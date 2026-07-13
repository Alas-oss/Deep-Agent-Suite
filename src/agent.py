import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from langchain_cerebras import ChatCerebras
from langchain_groq import ChatGroq
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemPermission

from tools import ALL_TOOLS, TOOLS_BY_NAME
from memory import LongTermMemoryStore
from tui import stream_and_print

root_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=root_dir / ".env")
langfuse = get_client()
langfuse_handler = CallbackHandler()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

provider = os.getenv("MODEL_PROVIDER", "cerebras")

if provider == "cerebras":
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    if not cerebras_key:
        print("Critical System Error: CEREBRAS_API_KEY was not detected in your .env file.")
        sys.exit(1)
    model = ChatCerebras(
        model="gpt-oss-120b",
        api_key=cerebras_key,
        temperature=0.2,
        timeout=60,
        max_retries=2,
    )
else:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("Critical System Error: GROQ_API_KEY was not detected in your .env file.")
        sys.exit(1)
    model = ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=groq_key,
        temperature=0.2,
        timeout=60,
        max_retries=2,
    )

MAX_GRAPH_STEPS = 40


class DeepAgent:
    def __init__(self, objective: str, user_id: str):
        self.objective = objective
        self.user_namespace = user_id

        repo_root = Path(__file__).resolve().parent.parent
        self.skills_dir = repo_root / "skills"
        self.output_dir = repo_root / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.backend = FilesystemBackend(root_dir=str(repo_root), virtual_mode=True)
        self.memory_store = LongTermMemoryStore(filename=self.output_dir / "long_term_store.json")

        self.available_skills_index = self._discover_available_skills()
        self.subagents = self._build_skill_subagents()

        self.agent = create_deep_agent(
            model=model,
            backend=self.backend,
            subagents=self.subagents,
            system_prompt=self._build_system_prompt(),
            permissions=[
                FilesystemPermission(
                    operations=["read", "write"],
                    paths=["/**/*.docx", "/**/*.pptx", "/**/*.xlsx"],
                    mode="deny",
                ),
            ],
        )

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
  subagent by name. Never use 'general-purpose' for these file types.
- Do not explore the filesystem yourself before delegating — the subagent already knows
  where its target files live.
- SUBAGENTS DO NOT SHARE YOUR CONTEXT. Each subagent starts with a blank slate and can
  only see what you put directly into its task description. If a later step needs content
  a previous subagent extracted or generated (e.g. summary text, extracted data, figures),
  you MUST paste that full content directly into the task description for the next
  delegation — never reference it vaguely (e.g. "the summary from before"). Assume the
  subagent has amnesia about everything except what you just told it.
- If the user's request has nothing to do with reading, creating, or editing .pptx/.docx/.xlsx
  files, say so plainly in your final response rather than attempting an unrelated task.
"""

    def execute_react_loop(self):
        print(f"[agent] starting run — objective: {self.objective[:80]}", flush=True)
        print(f"[agent] subagents loaded: {[s['name'] for s in self.subagents]}", flush=True)
        result = stream_and_print(
            self.agent,
            {"messages": [{"role": "user", "content": self.objective}]},
            config={
                "callbacks": [langfuse_handler],
                "metadata": {"user_id": self.user_namespace, "tags": [self.objective[:60]]},
                "recursion_limit": MAX_GRAPH_STEPS,
            },
        )
        self.memory_store.save_memory(
            self.user_namespace,
            "last_executed_summary",
            {"objective_status": "Success", "objective": self.objective},
        )
        print(f"Local root workspace active. Files saved directly to {self.output_dir}")
        return result