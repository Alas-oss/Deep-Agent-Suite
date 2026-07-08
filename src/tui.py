from rich.console import Console
from rich.panel import Panel

console = Console()

def print_banner(text: str) -> None:
    console.print(Panel(text, style="bold white on purple", expand=False))

def print_round(loop_idx: int, max_rounds, label: str = "Supervisor") -> None:
    console.rule(f"[bold]{label} round {loop_idx} of {max_rounds}[/bold]")

def print_thought(text: str) -> None:
    console.print(Panel(text or "(no reasoning text returned)", title="thought", border_style="grey50", title_align="center"))

def print_tool_call(name: str, args: dict) -> None:
    console.print(Panel(str(args), title=f"tool call: {name}", border_style="blue", title_align="left"))
    
def print_tool_output(name: str, result: str) -> None:
    console.print(Panel(str(result), title=f"tool output: {name}", border_style="green", title_align="center"))

def print_subagent_start(skill_name: str) -> None:
    console.print(Panel(f"delegate to skill '{skill_name}'", title="subagent", border_style="magenta", title_align="center"))

def print_subagent_tool(skill_name: str, name:str, result: str) -> None:
    console.print(Panel(str(result), title=f"subagent: {skill_name} -> {name}", border_style="magenta", title_align="center"))

def print_rate_limit(wait: int, attempt: int, max_attempts: int, detail: str = "") -> None:
    body = f"Rate limited - waiting {wait}s (attempt {attempt}/{max_attempts})"
    if detail:
        body += f"\n\n{detail}"
    console.print(Panel(body, border_style="yellow"))