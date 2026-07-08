# Deep Agent Suite

A supervisor/subagent "deep agent" that reads, writes, and edits Office documents (`.pptx`, `.docx`, `.xlsx`) by declaring skill-governed work to isolated subagents, each guided by personally written `SKILL.md` blueprints rather than built-in prompts.

## What it does
Given a plain-language task, either one of the buil-in example scenarios or free-form text types into the interactive session, a supervisor agent plans which skills are relevant, delegates the actual file work to subagents scopedto those skills, and returns a final summary. All generated files are generated in `outputs/`.

Some exmaple tasks that it can handle include:
- "Read sales.pptx and summarize the projected revenue."
- "Build a spreadsheet with a formula-driven total row."
- "Write a Word report with headed sections, then append audit notes to it."
- "Add a summary slide to a PowerPoint deck."

## Architecture
main.py                   → entrypoint: scenario index, one-shot prompt, or interactive session
run_all_scenarios.py       → regression harness across the 5 example scenarios
skills/                    → one folder per skill, each with a SKILL.md blueprint
  docx/SKILL.md
  pptx/{SKILL.md, editing.md, pptxgenjs.md}
  xlsx/SKILL.md
outputs/                   → every generated file lands here (gitignored)
src/
  agent.py                 → DeepAgent: supervisor loop + subagent spawning
  tools.py                 → tool implementations + native tool-calling schema
  sandbox.py                → resolves all file I/O into outputs/
  memory.py                 → simple JSON-backed long-term memory per user
  scenarios.py               → the 5 example scenario definitions
  tui.py                     → rich-based colored terminal output
  .env                       → GROQ_API_KEY, LANGFUSE_* keys (not committed)

## How the task follows through the system

1. **Supervisor** `DeepAgent.execute_react_loop` receives the objective, sees a list of available skills: name + description, read from each `SKILL.md`'s frontmatter - and either calls tools directly or delegates to a subagent 
2. **Delegation** `spawn_worker_subagent` loads the full skill blueprint via the `load_skill_blueprint` tool, restricts the subagent to only the tools that skill's frontmatter lists, and runs its own bounded tool-calling loop
3. **Tools** `tool.py` do the actual file work, so reading office files via MarkItDown, writing `.xlsx`/`.docx`/`.pptx` via openpyxl/python-docx/python-ptx, and every call is routed through `AgentSandbox`, which resolves relative filenames into `outputs/` regardless of process working directory
4. **Native tool calling**: both the supervisor and every subagent use Groq's structured `tools=`/`tool_calls` API rather than parsing JSON out of plain text, which was a deliberate fix after early iterations hit reliability issues with models emitting native tool-call syntax even when prompted to just "output JSON"


## Setup
`uv sync`
add to src/.env:
```
GROQ_API_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=...        # or LANGFUSE_BASE_URL, per your Langfuse dashboard
```

## Usage 
To run one of the 5 example scenarios by index (0-4 inclusive) - `uv run python main.py 0`

To run a one-shot custom prompt - `uv run python main.py "Your relevant prompt here"`

To have an interactive session that keeps taking prompts until you type 'quit' or 'exit' - `uv run python main.py`

For a quick test just run - `uv run python run_all_scenarios.py`
This runs all 5 examples one after the other, and reports pass/fail based on wether each scenario's expected output files landed in `output/`

## Observability

Every run is traced to Langfuse (there are nested spans per subagent delegation and per model call), each trace is tagged with the objective text and user id, for reviewing wether the supervisor is actually routing to the right skill.

## Known limitations and the roadmap

- In it's current state, model choice matters a lot: smaller but faster Groq models have shown less reliable multi-step tool orchestrationin testing rather than larger ones, check `console.groq.com/docs/models` for current recommendations
- I am planning on a LagnChain `deepagents`-based orchestration swap in a separate branch, keeping this existing `skills` / `tools.py` layer intact
- Document output formatting (bullets, table support, styling is an ongoing area of improvement)