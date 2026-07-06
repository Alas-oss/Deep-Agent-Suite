# System Evaluation Report: Lightweight Deep Agent Harness

## 1. Executive Summary and the Infrastructure Layer

This project successfully implements an automated multi-agent cluster pipeline optimized for enterprise document parsing and structural file generation. 

- Main Supervisor Loop Model: `openai/gpt-oss-120b` (via Groq Client API)
- Sub-Agent Worker Model: `openai/gpt-oss-120b` (via Groq Client API)
- Telemetry State Integration: 4-Round Iterative ReAct Framework
- Target Document Footprint: PowerPoint (`.pptx`), Excel (`.xlsx`), Word (`.docx`)

## 2. Real-World Execution Trace Analysis

The framework was evaluated against a multi-step cross-functional objective: extract revenue metrics from a presentation slide deck (`sales.pptx`), generate an interactive accounting spreadsheet (`ledger.xlsx`), compile an executive text narrative (`executive_report.docx`), and deploy a specialized sub-agent to audit the formula layout and append its verification footprint.

## The Trace Pipeline Log Details:
1. Loop Round 1 - Document Extraction: The orchestrator discovered a missing source file, automatically seeded a mock presentation via `python-pptx`, and called the `read_office_file` tool wrapper. It leverages Microsoft's `MarkItDown` engine to parse the text layers out of the target slide container, extracting three core variabels:
    * Expected License Sales: 50,000
    * Project Cloud Revenue: 120,000
    * Estimated Consulting Fees: 30,000
2. Loop Round 2 - Parallel Synthesis & Worker Delegation: The main supervisor bundled three complex operations into a single execution turn:
    - It passed the extracted figures to `create_xlsx_with_formulas`, right after it built `ledger.xlsx` with active math formula strings.
    - It invoked the parameter-matched `create_word_document` tool, and generated `executive_report.docx`.
    - It spawned the specialized `.xlsx` sub-agent worker, handing it a layout audit checklist.
3. Loop round 3 - Sub-Agent QA Verification: The sub-agent compiled its own evaluation matrix script using the `openpyxl` to programmatically crosscheck data types and column configurations. It onfirmed that all cells were numeric, no hidden columns existed, and harcoded numbers were replaced with live formula tracking. It then appended the official audit note: *“Spreadsheet audit passed: all formulas dynamic, no hard‑coded totals.”* directly to the bottom of the Word report.
4. Loop Round 4 - Workspace Teardown: The supervisor verifiedthe sub-agent's success response. Finding its objectives completely fulfilled, it exited the execution state machine early, saved the metadata logging variables down to the `LongTermMemoryStore`, and executed the sandbox's `close_and_cleanup()` sequence.

## 3. Engineering Insights & Architectural Takeaways

By designing this lightweight agent core around the specifications of the Anthropic and LangChain frameworks, several technical insights were observed:

1. **Markdown Extraction (Zero-Dependency parsing)**: Traditional agent frameworks rely on massive software packages like LibreOffice or headless browser containers to scrape data. By deploying Microsoft's `markitdown` library inside the `tools.py` file, the system converts binary XML files into Markdown text streams, thus cutting down latency.
2. **Context Isolation vs. Prompt Bloat**: Feeding exhaustive spreadsheet formatting rubrics and programmatic checklist checks directly into the main supervisor prompt window results in token bloat and dilutes attention. Forcing the supervisor to delegate validation loops to an isolated sub-agent via structured JSON commands keeps the primary planner highly efficient, while ensuring the validation report is detailed, informative, and secure.
3. **Dynamic Parameter Adaptability**: AI models frequently vary keyword parameters when interfacing with custom tool definitions. By designing adaptive argument wrappers inside `tools.py` (e.g., matching the model's choice of `content` across both `Word` and `log` generation), the supervisor successfully routes multi-tool payloads without throwing missing positional argument exceptions.


# 4. Architectural Evaluation: Trade-offs and Limitations

| Architectural Choice | Structural Advantages | Strategic Disadvantages / Risks |
| :--- | :--- | :--- |
| **Assistant-Scoped Sandbox** | • Fast execution across consecutive turns.<br>• Retains working files across the entire session. | • Accumulates unmanaged files if loop fails.<br>• Risk of cross-thread state pollution. |
| **Character-Level JSON Extraction** | • Parses conversational thoughts and tool payloads simultaneously.<br>• Flexible model formatting. | • Breaks if JSON arguments contain unbalanced raw brackets.<br>• High sensitivity to syntax variations. |
| **File-Backed JSON Memory Store** | • Human-readable flat log configuration.<br>• Zero external infrastructure dependencies. | • Lacks thread-safe atomic lock writing operations.<br>• Suboptimal for large storage contexts. |