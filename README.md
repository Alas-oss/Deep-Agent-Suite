# Lightweight Multi-Model Deep Agent Suite

This is an autonomous ReAct (Reason-Act) agent loop framework built from scratch to orchestrate multi-model office tasks, document parsing, and formula audits. Operating via the Groq API, this agent supervisor coordinates tasks across `.pptx` and `.xlsx` file structures, runs commands inside a sanitized local sandbox, and delegates validation checks to specialized sub-agents.

## Key Structural Features

This project maps production patters from well-established agent repositories into an independent execution harness:

1. Anthropic Office Skills Alignment
- Lightweight Office Parsing (`pptx` & `docx`): Completely strips out multi-gigabyte background program dependencies. It achieves cross-model document reading by integrating Microsoft's `markitdown` engine to natively extract unstructured text and layout fields into pure Markdown.
- Strict formula Guardrails (`xlsx`): Fully enforces Anthropic's rule of "formulas should be used, and not hardcoded values." The agent parses structural statistics and dynamically generates live Excel formula strings (`=SUM(B2:B4)`) instead of using Python scalar math or hardcoding text totals.

2. LangChain DeepAgents Execution Boundaries
- Iteration Caps: The main controler is strictly locked to a maximum of **3 execution rounds** to eliminate recursive context window leakage and prevent infinite loops.
- Context Isolation via Workers: When running an audit or checking data layouts, the orchestrator forks execution to an isolated sub-agent module (`spawn_worker_subagent`). This guarantees that specialist instructions (e.g., the `xlsx` schema check rubric) never clutter or confuse the main supervisor's historical context window.

## Setup and Execution

### 1. Prerequisites
Ensure you have Python 3.11+ and the **`uv` package manager** installed on your Windows machine.

### 2. Synchronize Your Local Virtual Environment
Run this command in your PowerShell terminal to automatically configure your isolated dependencies inside `.venv/`:
```powershell
uv sync
```

### 3. Configure Your Secret Tokens
Create a `.env` file directly in the project root directory and add your free developer tier key string:
```text
GROQ_API_KEY="your_groq_api_key"
```

### 4. Run the Automated Architecture Pipeline
Trigger the complete agent cluster harness routine:
```powershell
uv run python src/agent.py
```

---

## Verification & Validation

Once the processing cycle completes, you can verify compliance by checking two outputs:
1. **Console Traces**: Review the terminal log stream. It will explicitly show the model calling `read_office_file`, computing data rows, and outputting a highly detailed spreadsheet auditing checklist via the `xlsx` sub-agent.
2. **Spreadsheet Formulas**: Open the generated `data/ledger.xlsx` workbook using an extension or reader application. Click on the **Total** row and confirm that cell `B5` contains a dynamic Excel formula (`=SUM(B2:B4)`) rather than a hardcoded scalar number.
