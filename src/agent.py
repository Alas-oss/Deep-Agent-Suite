import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI
from pptx import Presentation
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=root_dir / ".env")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools import TOOL_REGISTRY

groq_key = os.getenv("GROQ_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
if groq_key and groq_key.strip():
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_key
    )
    MODEL_NAME = "openai/gpt-oss-120b"
elif openai_key and openai_key.strip():
    client = OpenAI(
        api_key=openai_key
    )
    MODEL_NAME = "gpt-4o"
else:
    print("Critical System Error: Neither GROQ_API_KEY nor OPENAI_API_KEY was found in your .env file.")
    sys.exit(1)



class LightweightDeepAgent:
    def __init__(self, objective: str):
        self.objective = objective
        self.max_parallel_workers = 3
        self.max_execution_rounds = 3

        self.skills_rubric = {
            "docx": "Exclusively for .docx targets. Extract text contents via 'read_office_file'. To view layout details or tracked changes, unzip the file container using 'unpack_raw_xml'.",
            "pptx": "Triggers on decks/slides. Pull slide outlines using 'read_office_file'. For visual QA, use subagent verification states.",
            "xlsx": "Handles tabular formats. CRITICAL CONSTRAINT: Enforce formula injection! Never hardcode mathematical summaries or averages using scalar numbers. Write active Excel formulas (e.g., =SUM(B1:B10))."
        }
    def spawn_worker_subagent(self, context_key: str, worker_prompt: str) -> str:
        print(f"Skill Context Doain: {context_key}")
        messages = [
            {"role": "system", "content": f"You are a specialized sub-agent. Guidelines for this domain are: \n{self.skills_rubric.get(context_key)}"},
            {"role": "user", "content": worker_prompt}
        ]
        res = client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.1)
        return res.choices[0].message.content

    
    def execute_react_loop(self):
        orchestrator_prompt = f"""You are a master deep agent cluster supervisor. You orchestrate file mutations and guide subagents.
To run a Python file tool or delegate a worker task, respond with exactly one clean JSON dictionary block matching this markdown layout:

To read the text/table data structure inside a docx/pptx/xlsx document:
{{
    "action": "call_tool",
    "tool_name": "read_office_file",
    "args": {{"filepath": "data/summary.pptx"}}
}}

To review formula guidelines, formatting rules, or run audit checks via an isolated subagent (Max 3 concurrent spans):
{{
    "action": "delegate_subagent",
    "skill_context_key": "xlsx",
    "prompt": "Verify that no sum totals are hardcoded text values and everything utilizes Excel formula strings."
}}

To create an Excel spreadsheet workbook data layout with proper formulas:
{{
    "action": "call_tool",
    "tool_name": "create_xlsx_with_formulas",
    "args": {{
        "filepath": "data/ledger.xlsx",
        "json_data_matrix": [
            ["Item", "Amount"],
            ["Expected License Sales", 50000],
            ["Projected Cloud Revenue", 120000],
            ["Total", "=SUM(B2:B3)"]
        ]
    }}
}}

Active Skills Blueprint Reference:
{json.dumps(self.skills_rubric, indent=2)}
"""
        messages = [
            {"role": "system", "content": orchestrator_prompt},
            {"role": "user", "content": self.objective}
        ]

        for loop_idx in range(1, self.max_execution_rounds + 1):
            print(f"\n Loop Round {loop_idx} out of {self.max_execution_rounds}")
            res = client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.1)
            
            thought = res.choices[0].message.content
            print(f"Agent Thought Process: \n {thought}")
            messages.append({"role": "assistant", "content": thought})

            try:
                start, end = thought.find("{"), thought.rfind("}") + 1
                if start != -1 and end != -1:
                    payload = json.loads(thought[start:end])

                    if payload["action"] == "call_tool":
                        tool_name = payload["tool_name"]

                        if tool_name == "write_excel_file":
                            tool_name = "create_xlsx_with_formulas"
                            if "sheets" in payload["args"]:
                                sheet_info = payload["args"]["sheets"][0]
                                payload["args"] = {
                                    "filepath": payload["args"]["filepath"],
                                    "json_data_matrix": [sheet_info["headers"]] + sheet_info["rows"]
                                }

                        tool_args = payload["args"]
                        tool_return = TOOL_REGISTRY[tool_name](**tool_args)
                        print(f"Tool Response: {tool_return[:300]}")
                        messages.append({"role": "user", "content": f"Tool Execution Output: {tool_return}"})
                        continue

                    elif payload["action"] == "delegate_subagent":
                        sub_return = self.spawn_worker_subagent(payload["skill_context_key"], payload["prompt"])
                        print(f"Subagent Response: \n {sub_return}")
                        messages.append({"role": "user", "content": f"Subagent Worker Response: {sub_return}"})
                        continue
            except Exception as e:
                print(f"JSON parsing skipped or completed: {str(e)}")

            print("\n The lightweight framework has completed the file execution layout.")
            break

if __name__ == "__main__":
    test_instruction = (
        "Read the text layout from the presentation 'data/sales.pptx', use those findings to create a clean "
        "financial spreadsheet workbook named 'data/ledger.xlsx' enforcing strict Excel formulas for summary cells, "
        "and delegate a subagent to run an audit on the formula architecture variables."
    )
    
    os.makedirs("data", exist_ok=True)
    from pptx import Presentation 
    if not os.path.exists("data/sales.pptx"):
        Presentation().save("data/sales.pptx")
    
    harness = LightweightDeepAgent(test_instruction)
    harness.execute_react_loop()