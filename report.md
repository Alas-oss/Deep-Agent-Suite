# System Evaluation Report: Lightweight Deep Agent Harness

## 1. Executive Summary and the Infrastructure Layer

This project successfully implements an automated multi-agent cluster pipeline optimized for enterprise document parsing and structural file generation. 

- Main Supervisor Loop Model: `openai/gpt-oss-120b` (via Groq Client API)
- Sub-Agent Worker Model: `openai/gpt-oss-120b` (via Groq Client API)
- Telemetry State Integration: 4-Round Iterative ReAct Framework

## 2. Real-World Execution Trace Analysis

The system was evaluated against a multi-step financial objective: extract revenue metrics from a presentation slide deck (`sales.pptx`), generate an accounting spreadsheet (`ledger.xlsx`), and audit the formula architecture for hardcoded values.

## The Trace Pipeline Log Details:
1. Loop Round 1 - Document Extraction: The orchestrator invoked the `read_office_file` tool wrapper. It leverages Microsoft's `MarkItDown` engine to parse the text layers out of the target slide container, extracting three core variabels:
    * Expected License Sales: 50,000
    * Project Cloud Revenue: 120,000
    * Estimated Consulting Fees: 30,000
2. Loop Round 2 - Structural Synthesis & Constraint Compliance: The main supervisor analyzed the extracted metrics and calles `create_xlsx_with_formulas`. It adheres to the given constraint rubric by mapping the rows as a matrix array and passing an active Excel formula string (`=SUM(B2:B4)`) directly into the summary cell.
3. Loop round 3 - Multi-Agent Task Delegation: The supervisor identifies that an expert validation review is needed. It invokes the `"action": "delegate_subagent"` command block and created an isolated sub-agent. The sub-agent uses the specialized `xlsx` domain instructions to evaluate the generated file schema.
4. Loop Round 4 - State Persistence & Teardown: The agent reviews the sub-agent validation response, terminates the runtime loop, writes execution metadata (`objective_status: Success`) to the `LongTermMemoryStore`, and prints the final workspace lifecycle logs.

## 3. Engineering Insights & Architectural Takeaways

By designing this lightweight agent core around the specifications of the Anthropic and LangChain frameworks, several technical insights were observed:

1. **Markdown Extraction (Zero-Dependency parsing)**: Traditional agent frameworks rely on massive software packages like LibreOffice or headless window layers to scrape data. By deploying Microsoft's `markitdown` library inside our `tools.py` file, it successfully transformed complex OpenXML file structures into light markdown text blocks, reducing latency and avoiding heavy downloads.
2. **Context Isolation vs. Tool Hallucination**: During earlier development phases, the agent tended to hallucinate general tool names (like `write_excel_file`). By implementing a robust **Tool Alias Route Safety Patch** directly inside the JSON interpreter block, the orchestrator now catches naming deviations on the fly and translates them to functional Python tool calls seamlessly.
3. **Workspace Input Sanitizer**: To mitigate path-traversal vulnerabilities common in automated tool-use scripts, `AgentSandbox` intercepts incoming keyword arguments. If a `"filepath"` key is present, the sandbox isolates and forces a flat filename extraction:
```python
if "filepath" in kwargs:
    filename = Path(kwargs["filepath"]).name
    kwargs["filepath"] = str(filename)
```
This forces all operations to resolve explicitly inside the localized root execution workspace (`Path(".").resolve()`).



# 4. Architectural Evaluation: Trade-offs and Limitations

| Architectural Choice | Structural Advantages | Strategic Disadvantages / Risks |
| :--- | :--- | :--- |
| **Assistant-Scoped Sandbox** | • Fast execution across consecutive turns.<br>• Retains working files across the entire session. | • Accumulates unmanaged files if loop fails.<br>• Risk of cross-thread state pollution. |
| **Character-Level JSON Extraction** | • Parses conversational thoughts and tool payloads simultaneously.<br>• Flexible model formatting. | • Breaks if JSON arguments contain unbalanced raw brackets.<br>• High sensitivity to syntax variations. |
| **File-Backed JSON Memory Store** | • Human-readable flat log configuration.<br>• Zero external infrastructure dependencies. | • Lacks thread-safe atomic lock writing operations.<br>• Suboptimal for large storage contexts. |