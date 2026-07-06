# Lightweight Multi-Model Deep Agent Suite

This is an autonomous ReAct (Reason-Act) agent loop framework built from scratch to orchestrate complex office pipelines, document text parsing, spreadsheet data rendering, and programmatic compliance audits. Operating via the Groq API, this agent supervisor coordinates tasks across `.pptx`, `.xlsx`, and `.docx` formats entirely within a localized, safe sandbox environment.

## Key Structural Features

* Dynamic Office Parsing (`.pptx` & `.docx`): Avoids heavy text processor platform dependencies by integrating the `markitdown` engine to natively extract text and layout structures into pure Markdown.
* Formula Guardrails (`.xlsx`): Enforces dynamic formula injection over dead text metrics, or hardcoded values. The agent writes structured data matrix arrays containing active Excel formulas directly into `openpyxl`.
* Flexible Parameter Wrapping: Includes adaptive tool wrappers to handle natural variation in model-generated argument structures, preventing missing parameter runtime crashes.
* Iteration Caps: The main control loop is locked to a maximum of `4 execution rounds` to eliminate context leakage, control inference billing, and prevent infinite loop hangs.
* Context Isolation via Workers: Forks execution to an isolated sub-agent module (`spawn_worker_subagent`). This guarantees that specialist instructions (i.e., the `xlsx` audit schema) never clutter the main supervisor's history window.


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

Once the processing cycle completes, you can verify compliance by checking three outputs:
1. **Console Traces**: Review the terminal log stream. It will track the supervisor batching tool calls, extracting a custom Python verification layout checklist via its worker sub-agent.
2. **Spreadsheet Formulas:** Open the generated `ledger.xlsx` file in Excel. Click on the summary row and verify that the total cells contain active, calculating `=SUM(...)` formulas rather than hardcoded numeric values.
3. **Word Documentation Report**: Open `executive_report.docx` in Word. Confirm that all structured headings text blocks have rendered successfully, and that sub-agent's verified audit footer is appended to the bottom page.