import os
import sys
from dotenv import load_dotenv
from pathlib import Path
import groq
import openai
from langchain_cerebras import ChatCerebras
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemPermission

from tools import ALL_TOOLS, TOOLS_BY_NAME
from memory import LongTermMemoryStore
from tui import stream_and_print

import tempfile
import shutil

root_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=root_dir / ".env")
langfuse = get_client()
langfuse_handler = CallbackHandler()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

PROVIDER_CHAIN = ["cerebras", "groq", "gemini"]
MAX_GRAPH_STEPS = 50


def _build_model(provider: str):
    if provider == "cerebras":
        return ChatCerebras(model="gpt-oss-120b", api_key=os.getenv("CEREBRAS_API_KEY"), temperature=0.2, timeout=60, max_retries=2)
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(model="gemini-flash-latest", api_key=os.getenv("GOOGLE_API_KEY"), temperature=0.2, timeout=60, max_retries=2)
    else:
        return ChatGroq(model="openai/gpt-oss-120b", api_key=os.getenv("GROQ_API_KEY"), temperature=0.2, timeout=60, max_retries=2)


class DeepAgent:
    def __init__(self, objective: str, user_id: str):
        self.objective = objective
        self.user_namespace = user_id

        repo_root = Path(__file__).resolve().parent.parent
        self.skills_dir = repo_root / "skills"
        self.output_dir = repo_root / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.temp_dir = str(Path(repo_root) / "outputs" / ".tmp")
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)

        self.backend = FilesystemBackend(root_dir=str(repo_root), virtual_mode=True)
        self.memory_store = LongTermMemoryStore(filename=self.output_dir / "long_term_store.json")

        self.available_skills_index = self._discover_available_skills()
        self.subagents = self._build_skill_subagents()
        self.permissions = [
            FilesystemPermission(operations=["write"], paths=["/**/*.docx", "/**/*.pptx", "/**/*.xlsx"], mode="deny"),
            FilesystemPermission(operations=["write"], paths=["/outputs/**"], mode="interrupt"),
        ]
        self.agent = None

    def _discover_available_skills(self) -> dict:
        skills_map = {}
        if not self.skills_dir.exists():
            return {}
        for folder in self.skills_dir.iterdir():
            if not folder.is_dir():
                continue
            skill_file = folder / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                text = skill_file.read_text(encoding="utf-8")
                if not text.startswith("---"):
                    continue
                meta_section = text.split("---")[1]
                meta_data = {}
                for line in meta_section.strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta_data[k.strip()] = v.strip()
                skills_map[folder.name] = meta_data
            except Exception:
                continue
        return skills_map

    def _load_blueprint_body(self, skill_name: str) -> str:
        """Load SKILL.md body, trimmed to just the parts a dedicated subagent
        needs (when-to-use + constraints). Drops the 'Example call' and
        'Additional reference material' sections, which existed for a
        top-level agent still deciding which skill to use — a subagent
        already dedicated to this skill doesn't need them, and they were
        costing real tokens on every single delegation."""
        skill_file = self.skills_dir / skill_name / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        body = parts[2].strip() if len(parts) >= 3 else text.strip()

        for cutoff in ("## Example call", "## Additional reference material"):
            idx = body.find(cutoff)
            if idx != -1:
                body = body[:idx].strip()
        return body

    def _build_skill_subagents(self) -> list[dict]:
        subagents = []
        shared_reporting_rule = (
            "\n\nIMPORTANT — reporting back to the supervisor: your final response to the "
            "supervisor must be SHORT (2-4 sentences) — confirm what you did and the file "
            f"path, do not repeat the full content you extracted or wrote. If your task "
            f"involves large data (more than ~150 words), write the full detail to a file "
            f"under {self.temp_dir} first, and mention that file's path in your short summary "
            "instead of pasting the content into your response."
        )
        for skill_name, meta in self.available_skills_index.items():
            allowed = [t.strip() for t in meta.get("tools", "").split(",") if t.strip()]
            tools = [TOOLS_BY_NAME[t] for t in allowed if t in TOOLS_BY_NAME] or ALL_TOOLS
            subagents.append({
                "name": f"{skill_name}-agent",
                "description": meta.get("description", f"Handles {skill_name} tasks"),
                "system_prompt": (
                    "You are a specialized document engineering subagent.\n"
                    "Follow this skill blueprint exactly:\n\n"
                    f"{self._load_blueprint_body(skill_name)}"
                    f"{shared_reporting_rule}"
                ),
                "tools": tools,
            })
        return subagents

    def _build_system_prompt(self) -> str:
        if self.available_skills_index:
            skills_list = "\n".join(
                f"  - {name}-agent: {meta.get('description', 'No description provided.')}"
                for name, meta in self.available_skills_index.items()
            )
        else:
            skills_list = "  (no skills discovered under ./skills — proceeding with raw tools only)"
        prior_context = self.memory_store.get_all_context(self.user_namespace)
        return f"""You are a master deep agent cluster supervisor orchestration loop engine.
    PRIOR SESSION CONTEXT:
    {prior_context}

    AVAILABLE SUBAGENTS (delegate matching work to the exact named subagent via the task tool):
    {skills_list}

    CRITICAL ARCHITECTURAL CONSTRAINTS:
    - You MUST delegate any task touching a .pptx, .docx, or .xlsx file to the exact matching
    subagent by name — including verification, audit, or "check the file" steps. Never use
    'general-purpose' for any task that requires reading or writing an office file, since
    it does not have access to the office-file tools and will fail. If a step doesn't fit
    neatly into docx-agent/pptx-agent/xlsx-agent's stated purpose but still involves an
    office file, delegate to the subagent matching that file's extension anyway.
    - Do not explore the filesystem yourself before delegating — the subagent already knows
    where its target files live.
    - SUBAGENTS DO NOT SHARE YOUR CONTEXT. Each subagent starts with a blank slate and can
    only see what you put directly into its task description. Assume the subagent has
    amnesia about everything except what you just told it — never reference prior content
    vaguely (e.g. "the summary from before"). For SHORT content (a few sentences), paste it
    directly into the task description. For LARGE content, follow the file-based rule below
    instead of pasting it inline.
    - If a subagent returns a large or detailed result that a later subagent needs, do NOT
    paste the full text into the next task description. Instead, use write_file to save it
    to a path under {self.temp_dir} (e.g. {self.temp_dir}/findings.md), and reference that
    full path in the next subagent's task description, telling it to read_file that path
    first. This keeps individual model requests small and avoids provider request-size limits.
    - If the user's request has nothing to do with reading, creating, or editing .pptx/.docx/.xlsx
    files, say so plainly in your final response rather than attempting an unrelated task.
    - Before delegating a task that references a specific filename, if you're not certain
    it exists, have the relevant subagent check first (via glob). If the exact filename
    isn't found but a similarly-named file or a same-name-different-extension file exists,
    STOP and ask the user to confirm which file they meant in your final response — do not
    guess, and do not keep searching broadly. If truly nothing similar exists, report that
    clearly instead of attempting the task with fabricated or assumed content.
    - Your FIRST action in every run must be a write_todos call laying out your complete
    plan. Each todo item must explicitly name which subagent (docx-agent/pptx-agent/
    xlsx-agent) will handle it, e.g. "Extract data from sales.pptx via pptx-agent" —
    not just "read the file." Do not call any other tool — including ls, glob, or task —
    before this planning step is complete. Once written, follow the plan in order; do not
    re-delegate to the same subagent for a step already marked completed unless a later
    step's output reveals the earlier one needs correction.
    """

    def execute_react_loop(self):
        try:
            print(f"[agent] starting run — objective: {self.objective[:80]}", flush=True)
            print(f"[agent] subagents loaded: {[s['name'] for s in self.subagents]}", flush=True)
            errors = []
            for provider in PROVIDER_CHAIN:
                print(f"[agent] trying provider: {provider}", flush=True)
                try:
                    self.agent = create_deep_agent(
                        model=_build_model(provider),
                        backend=self.backend,
                        subagents=self.subagents,
                        system_prompt=self._build_system_prompt(),
                        permissions=self.permissions,
                    )
                    result = stream_and_print(
                        self.agent,
                        {"messages": [{"role": "user", "content": self.objective}]},
                        config={
                            "callbacks": [langfuse_handler],
                            "metadata": {"user_id": self.user_namespace, "tags": [self.objective[:60]]},
                            "recursion_limit": MAX_GRAPH_STEPS,
                        },
                    )
                    self.memory_store.save_memory(self.user_namespace, "last_executed_summary", {"objective_status": "Success", "objective": self.objective})
                    print(f"Local root workspace active. Files saved directly to {self.output_dir}")
                    return result
                except Exception as e:
                    status = getattr(e, "status_code", None)
                    reason = "capacity/quota" if status in (429, 413) else f"error ({type(e).__name__}, status {status})"
                    print(f"[agent] {provider} failed — {reason}, trying next provider...", flush=True)
                    errors.append(f"{provider}: {type(e).__name__}: {e}")
                    continue
            raise RuntimeError("All providers exhausted:\n" + "\n".join(errors))
        finally:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"[agent] cleaned up temp dir: {self.temp_dir}", flush=True)
