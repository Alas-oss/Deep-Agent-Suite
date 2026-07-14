# Deep Agent Suite

A supervisor/subagent "deep agent" that reads, writes, and edits Office documents (`.pptx`, `.docx`, `.xlsx`) by delegating skill-governed work to isolated subagents, each guided by a personally written `SKILL.md` blueprint rather than built-in prompts. The orchestration includes the supervisor loop, subagent delegation, filesystem sandboxing, and retries which are built on LangChain's `deepagents` library rather than a hand-written ReAct loop.

## What it does
Given a plain-language task, either one of the built-in example scenarios, a one-shot custom prompt, or free-form text types in an interactive session, the supervisor agent plans which skill(s) are relevant, delegates the actual file work to subagents scoped to those skills, and returns a final summary. All generated files land in `outputs/`.

Some example tasks that it can handle include:
- "Read sales.pptx and summarize the projected revenue."
- "Build a spreadsheet with a formula-driven total row."
- "Write a Word report with headed sections, then append audit notes to it."
- "Add a summary slide to a PowerPoint deck."
- "Make a docx file based on the findings from an xlsx file"

## Architecture
```
main.py                    → entrypoint: scenario index, one-shot prompt, or interactive session
run_all_scenarios.py       → regression harness across the 5 example scenarios (streams live, no output buffering)
debug_subagents.py         → zero-cost local check that all skill subagents build correctly, no LLM call
skills/                    → one folder per skill, each with a SKILL.md blueprint
  docx/SKILL.md
  pptx/{SKILL.md, editing.md, pptxgenjs.md}
  xlsx/SKILL.md
outputs/                   → every generated file lands here (gitignored)
tests/
  test_tools.py            → pytest unit tests for tools.py, no LLM/API calls
src/
  agent.py                 → DeepAgent: builds the deepagents graph, provider fallback loop
  tools.py                 → tool implementations (office file read/write) as typed @tool functions
  memory.py                → simple JSON-backed long-term memory per user
  scenarios.py              → the 5 example scenario definitions
  tui.py                    → rich-based colored terminal output, streamed live from agent.stream()
  .env                       → provider keys + Langfuse keys (not committed)
```

`sandbox.py` from earlier iterations has been removed, its only two jobs being: validating tool names, and resolving relative paths into `outputs/` - are now handled by LangChain's native tool-call validation and a `_resolve()` helper in `tools.py` respectively.

## How the task follows through the system

1. **Supervisor** `DeepAgent.execute_react_loop` receives the objective and sees a list of available subagents - one per skill, built from each `SKILL.md`'s frontmatter - and delegates via `deepagents`' native `task` tool. The supervisor is instructed to never touch `.pptx/.docx/.xlsx` files directly and to always route to the exact matching subagent.
2. **Delegation**: each subagent is declared up front (not spawned ad hoc) via `create_deep_agent(subagents=[...])`, with its `system_prompt` built from that skill's `SKILL.md` body and restricted to only the tools its frontmatter lists. Subagents do not share the supervisor's context, since each starts from a blank slate and only sees what's written into its `task` description.
3. **Large-content handoffs go through files, not inline text**: if a subagent's output would be large where it could include: spreadsheet findings and/or extracted document text - it writes the full detail to a temporary file via `write_file` and reports back a short 2-4 sentence confirmation with the file path - the next subagent reads that file directly rather than the supervisor pasting large blocks of text between each delegation. This keeps the individual model requests small, which matters a lot on free-tier providers with tight per-request token ceilings.
4. **Tools** (`tools.py`) do the actual file work - reading office files via MarkItDown, writing `.xlsx/.docx/.pptx` via openpyxl/python-docx/python-pptx. Every tool resolves its `filepath` argument through a `_resolve()` helper that strips any path the model supplies (real, virtual, or Windows-style) down to just the filename and forces it into outputs/`.
5. **Filesystem permissions** (`FilesystemPermission`, which is native to `deepagents`) enforce two hard rules regardless of what any prompt says: reading or writing `.pptx/.docx/.xlsx` through the generic filesystem tools (as opposed to the dedicated office-file tools) is denied outright, and any write into `outputs/` triggers a human-in-the-loop interruption for confirmation before it happens.
6. **Content quality is enforced in code, not just prompts**: `create_word_document` rejects content that's more than 35% bullet-point lines, returning a clear rejection message that tells the subagent to rewrite a written-out evaluation (or summary) and retry, this proved necessary because prompt-level instructions alone weren't reliably followed by the models tested. 
7. **Provider fallback**: the supervisor tries Cerebras, then Groq, then Gemini in order, rebuilding the graph fresh for each attempt. A failure on one provider such as: quota exhaustion, a too-large request, a malformed/unparseable response, a deprecated model - logs the reason and falls through to the next provider automatically, rather than the whole run failing. 

## Setup
`uv sync`
Add to src/.env:
```
CEREBRAS_API_KEY=...
GROQ_API_KEY=...
GOOGLE_API_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=...        # e.g. https://cloud.langfuse.com
```
All three model provider keys are optional individually, but the fallback chain (Cerebras → Groq → Gemini) is only as resilient as the keys that you actually provide, a missing key just means that link in the chain fails immediately and moves to the next one.

## Usage 
To run one of the 5 example scenarios by index (0-4 inclusive) - `uv run python main.py 0`

To run all of the 5 example scenarios - `uv run python run_all_scenarios.py`

To run a one-shot custom prompt - `uv run python main.py "Your relevant prompt here"`

To have an interactive session that keeps taking prompts until you type `quit` or `exit` - `uv run python main.py`

## Testing 

Fast and no LLM calls - unit tests for the deterministic parts of the system (including path resolution, xlsx formula handling, the bullet-vs-text content gate) - `uv run pytest tests/`

For structural checks on the agent's construction (e.g. confirming that all 3 skill subagents can actually build, catching bugs), `debug_subagents.py` constructs a `DeepAgent` without invoking it - `uv run python debug_subagents.py`

## Observability

Every run is traced to Langfuse, with nested spans per subagent delegation and per model call, each trace is tagged with the objective text and user id. This is the most reliable way to see what is actually happening during the run, as terminal output only shows the supervisor's top-level view, while a subagent's internal tool-calling loop only shows up in the full trace.

## Known limitations and the roadmap

- **Model choice affects tool-calling reliability**, not just speed - some hosted models have shown malformed tool-call syntax.
- **Document content quality is enforced where it matters most**, as a mentioned example the bullet point vs written text ratio in .docx files, or real formulas instead of hardcoded fallback values in spreadsheets. This is an ongoing area that will be updated as more features are included in each type of the documents.
- **Missing-file handling is still being hardened** - a request naming a file that doesn't exist under that exact name can cause a subagent to search broadly rather than reporting clearly that the file wasn't found; a system_prompt instructions addresses this but doesn't yet have a code-level backstop the way content quality does.
- **`memory.py`'s long-term store grown unbounded** across sessions and gets injected into every supervisor system prompt - worth capping before it becomes its own source of the same token-budget problems that motivated the file-based handoff design in the first place.