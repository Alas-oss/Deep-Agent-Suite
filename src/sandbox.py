from pathlib import Path
from tools import TOOL_REGISTRY

class AgentSandbox:
    def __init__(self, scope: str = "assistant", identifier: str = "global"):
        self.scope = scope
        self.identifier = identifier
        repo_root = Path(__file__).resolve().parent.parent
        self.output_dir = repo_root / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_sandbox_tool(self, tool_name: str, **kwargs) -> str:
        if tool_name not in TOOL_REGISTRY:
            return f"Error: Tool '{tool_name}' is not supported."

        if "filepath" in kwargs:
            filename = Path(kwargs["filepath"]).name
            kwargs["filepath"] = str(self.output_dir / filename)

        return TOOL_REGISTRY[tool_name](**kwargs)

    def close_and_cleanup(self):
        print(f"Local root workspace active. Files saved directly to {self.output_dir}")
