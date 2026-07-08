import os
import json
import sys
import time
from dotenv import load_dotenv
from pathlib import Path
from groq import Groq
from langfuse import observe, get_client, propagate_attributes

from tools import TOOL_REGISTRY, TOOLS_SCHEMA
from memory import LongTermMemoryStore
from sandbox import AgentSandbox
from tui import (
    print_round, print_thought, print_tool_output, print_tool_call,
    print_subagent_start, print_subagent_tool, print_rate_limit
)

root_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=root_dir / ".env")
langfuse = get_client()

sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

groq_key = os.getenv("GROQ_API_KEY")

if groq_key and groq_key.strip():
    client = Groq(api_key=groq_key)
    MODEL_NAME = "openai/gpt-oss-120b"
else:
    print("Critical System Error: GROQ_API_KEY was not detected in your workspace .env file.")
    sys.exit(1)

DELEGATE_TOOL_SCHEMA = {"type": "function", "function": {
    "name": "delegate_subagent",
    "description": "Delegate a skill-governed subtask to an isolated subagent that has the skill's full blueprint and matching tool access.",
    "parameters": {"type": "object", "properties": {
        "skill": {"type": "string", "description": "Skill folder name, e.g. 'xlsx', 'docx', 'pptx'."},
        "prompt": {"type": "string", "description": "Task instructions for the subagent."}
    }, "required": ["skill", "prompt"]}
}}

class DeepAgent:
    def __init__(self, objective: str, user_id: str):
        self.objective = objective
        self.max_execution_rounds = 4
        self.subagent_max_rounds = 3
        self.user_namespace = user_id

        self.sandbox = AgentSandbox(scope="assistant", identifier="global")
        self.memory_store = LongTermMemoryStore(filename=self.sandbox.output_dir / "long_term_store.json")

        self.available_skills_index = self._discover_available_skills()

    def _build_system_prompt(self) -> str:
        tool_list = "\n".join(f"  - {name}" for name in TOOL_REGISTRY.keys())

        if self.available_skills_index:
            skills_list = "\n".join(
                f"  - {name}: {meta.get('description', 'No description provided.')} "
                f"(relevant tools: {meta.get('tools', 'unspecified')})"
                for name, meta in self.available_skills_index.items()
            )
        else:
            skills_list = "  (no skills discovered under ./skills — proceeding with raw tools only)"
        prior_context = self.memory_store.get_all_context(self.user_namespace)
        return f"""You are a master deep agent cluster supervisor orchestration loop engine.
PRIOR SESSION CONTEXT:
{prior_context}

AVAILABLE SKILLS (each is a folder under ./skills with detailed instructions):
{skills_list}

To use a skill's full instructions before delegating work on it, call the 'load_skill_blueprint'
tool with the skill's folder name. To delegate the actual execution of a skill's task to an
isolated subagent, use the 'delegate_subagent' action with a "skill" field set to that skill's
folder name.

AVAILABLE RAW TOOLS (call directly when no skill applies, or as instructed by a skill):
{tool_list}

CRITICAL ARCHITECTURAL CONSTRAINTS:
- Prefer delegating skill-governed work (xlsx/docx/pptx tasks) to a subagent via 'delegate_subagent' with the
  matching "skill" name, rather than calling tools directly yourself, so the skill's constraints are enforced.
- If the user's request has nothing to do with reading, creating, or editing .pptx/.docx/.xlsx
   files, say so plainly in your final response rather than attempting an unrelated task.
"""

    def _discover_available_skills(self) -> dict:
        skills_map = {}
        repo_root = Path(__file__).resolve().parent.parent
        skill_root = repo_root / "skills"

        if not skill_root.exists():
            return {}
        
        for folder in skill_root.iterdir():
            if not folder.is_dir():
                continue

            skill_file = folder / "SKILL.md"
            if not skill_file.exists():
                continue
            
            try:
                with open(skill_file, "r", encoding="utf-8") as f:
                    text = f.read()

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
    
    @observe
    def spawn_worker_subagent(self, skill_name: str, worker_prompt: str) -> str:
        print_subagent_start(skill_name)
        
        skill_blueprint = self.sandbox.run_sandbox_tool("load_skill_blueprint", skill_name=skill_name)

        skill_meta = self.available_skills_index.get(skill_name.split("/")[0], {})
        allowed_names = [t.strip() for t in skill_meta.get("tools", "").split(",") if t.strip()]
        subagent_tools = [t for t in TOOLS_SCHEMA if t["function"]["name"] in allowed_names] or TOOLS_SCHEMA

        subagent_system_prompt = (
            "You are a specialized document engineering subagent.\n"
            "Follow this skill blueprint exactly:\n\n"
            f"{skill_blueprint}\n\n"
            "Use the provided tools to actually create/modify files. Once the task is fully done, "
            "respond with a short plain-text summary and make no further tool calls."
        )


        messages = [
            {"role": "system", "content": subagent_system_prompt},
            {"role": "user", "content": worker_prompt}
        ]

        findings = "Subagent did not produce a final summary within its round budget."

        for round_idx in range(1, self.subagent_max_rounds + 1):
            res = self._call_model(messages, tools=subagent_tools)
            msg = res.choices[0].message

            if msg.tool_calls:
                messages.append(msg.model_dump(exclude_none=True))
                for tc in msg.tool_calls:
                    name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}
                    result = self.sandbox.run_sandbox_tool(name, **args)
                    print_subagent_tool(skill_name, name, result)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
            else:
                findings = msg.content or findings
                break

        return findings

    @observe()
    def execute_react_loop(self):
        with propagate_attributes(user_id=self.user_namespace, tags=[self.objective[:60]]):
            base_system_prompt = self._build_system_prompt()

            messages = [
                {"role": "system", "content": base_system_prompt},
                {"role": "user", "content": self.objective}
            ]

            all_tools = TOOLS_SCHEMA + [DELEGATE_TOOL_SCHEMA]

            for loop_idx in range(1, self.max_execution_rounds + 1):
                print_round(loop_idx, self.max_execution_rounds)
                res = self._call_model(messages, tools=all_tools)
                msg = res.choices[0].message

                if msg.tool_calls:
                    messages.append(msg.model_dump(exclude_none=True))
                    for tc in msg.tool_calls:
                        name = tc.function.name
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}

                        if name == "delegate_subagent": 
                            result = self.spawn_worker_subagent(args.get("skill", ""), args.get("prompt", ""))
                        else:
                            print_tool_call(name, args)
                            result = self.sandbox.run_sandbox_tool(name, **args)
                        
                        print_tool_output(name, result)
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
                else:
                    print_thought(msg.content)
                    messages.append({"role": "assistant", "content": msg.content or ""})
                    break

            self.memory_store.save_memory(
                self.user_namespace,
                "last_executed_summary",
                {"objective_status": "Success", "objective": self.objective}
            )
            self.sandbox.close_and_cleanup()

    def _call_model(self, messages, tools=None):
        wait = 15
        for attempt in range(1, 7):
            try:
                if tools:
                    return client.chat.completions.create(
                        model=MODEL_NAME, messages=messages, tools=tools,
                        tool_choice="auto", temperature=0.2
                    )
                return client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.2)
            except Exception as e:
                err_text = str(e).lower()
                if "rate_limit" in err_text or "429" in err_text:
                    print_rate_limit(wait, attempt, 6, detail=str(e))
                    time.sleep(wait)
                    wait = min(wait * 2, 90)
                    continue
                if "tool_use_failed" in err_text and attempt < 3:
                    print_rate_limit(0, attempt, 6, detail=f"Malformed too call, retrying: {e}")
                    continue
                raise
        raise RuntimeError("Exceeded retry attempts due to rate limiting.")