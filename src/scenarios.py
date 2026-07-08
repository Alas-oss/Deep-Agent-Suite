SCENARIOS = [
    {
        "name": "pptx_to_ledger_and_report",
        "prompt": (
            "1. Read the text layouts out of 'sales.pptx'.\n"
            "2. Synthesize that financial data to build a clean spreadsheet named 'ledger.xlsx' "
            "enforcing strict dynamic formula injection for totals.\n"
            "3. Generate a comprehensive project narrative file named 'executive_report.docx' "
            "outlining our findings.\n"
            "4. Deploy an isolated subagent worker to run a verification layout checklist on the "
            "spreadsheet, and append those final audit notes directly to the bottom of the Word "
            "document report."
        ),
        "expected_outputs": ["ledger.xlsx", "executive_report.docx"],
    },
    {
        "name": "pptx_summary",
        "prompt": "Read 'sales.pptx' and write a one-page summary of it to 'pptx_summary.docx'.",
        "expected_outputs": ["pptx_summary.docx"],
    },
    {
        "name": "docx_compliance_checklist",
        "prompt": (
            "Read 'executive_report.docx' if it exists, otherwise create a placeholder one, "
            "then produce a compliance checklist spreadsheet named 'compliance_checklist.xlsx' "
            "with formula-driven pass/fail totals."
        ),
        "expected_outputs": ["compliance_checklist.xlsx"],
    },
    {
        "name": "xlsx_to_docx_crossref",
        "prompt": (
            "Build 'metrics.xlsx' with sample quarterly figures and a SUM total, then write "
            "'metrics_report.docx' summarizing those figures in prose."
        ),
        "expected_outputs": ["metrics.xlsx", "metrics_report.docx"],
    },
    {
        "name": "docx_to_pptx_outline",
        "prompt": (
            "Read 'executive_report.docx' if it exists, otherwise create a placeholder one, "
            "then add a summary slide to a new 'outline.pptx' capturing its key points."
        ),
        "expected_outputs": ["outline.pptx"],
    },
]