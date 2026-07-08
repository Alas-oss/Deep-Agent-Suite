---
description: Generate or append to Word documents that narrate findings, summaries, or audit notes.
tools: create_word_document, append_text_to_document, read_office_file
triggers: report, docx, word document, summary, narrative, audit notes
---

# docx skill

## When to use this skill
Use this whenever the task involves producing a `.docx` narrative document, or appending
additional findings/audit notes to an existing one.

## Constraints (must follow exactly)
- Use `create_word_document` only when the target file does not exist yet. If it already exists, use `append_text_to_document` instead — never overwrite an existing report unless explicitly told to.
- Structure content with `#` prefixes for section headings (the tool converts these to Word heading styles automatically) — do not use Markdown bold/italics, they are not supported.
- Keep each section under a heading to 3-6 sentences unless the task explicitly asks for exhaustive detail.
- When appending audit or verification notes (e.g. from a subagent double-checking another file), prefix the appended paragraph with a clear label like "Verification Notes:" so it's distinguishable from the original report body.
- Do not check whether an output file already exists before creating it — just create or overwrite it directly unless the task explicitly says to check first.
- Never call a file-writing tool with placeholder, generic, or one-line content. Write out the full, specific content requested in the task (multiple sentences/rows/bullets as appropriate) before calling the tool — the tool call's arguments must contain the actual finished content, not a summary of what you plan to write.


## Example call
{"filepath": "executive_report.docx", "title": "Q3 Executive Report",
 "content": "# Overview\nRevenue grew across all three streams.\n# Details\nLicense sales..."}