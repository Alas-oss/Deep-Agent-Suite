---
description: Build or edit spreadsheets that require live calculations rather than static numbers.
tools: create_xlsx_with_formulas, read_office_file
triggers: spreadsheet, xlsx, ledger, totals, sum, formula
---

# xlsx skill

## When to use this skill
Use this whenever the task involves producing or updating a `.xlsx` file that contains any
calculated value (totals, sums, averages, running balances).

## Constraints (must follow exactly)
- Never hardcode a calculated number as a literal value. Any cell that is a sum, total, average, or derived figure MUST be written as a formula string starting with `=`, e.g. `=SUM(B2:B4)`.
- Row 1 must always be a header row (column labels), never data.
- When calling `create_xlsx_with_formulas`, pass `json_data_matrix` as a list of lists, where acalculated cell is written directly as the formula string (e.g. `"=SUM(B2:B4)"`), not as a dict or a pre-computed number.
- If asked to summarize source data (e.g. from a `.pptx` or `.docx`), first extract the raw numbers using `read_office_file`, then build the matrix yourself before calling `create_xlsx_with_formulas` — do not ask the tool to do the extraction.
- Column widths and cell formatting are not currently supported by `create_xlsx_with_formulas`. 
- Do not attempt to pass style/formatting arguments — they will be silently ignored.
- Do not check whether an output file already exists before creating it — just create or overwrite it directly unless the task explicitly says to check first.
- Never call a file-writing tool with placeholder, generic, or one-line content. Write out the full, specific content requested in the task (multiple sentences/rows/bullets as appropriate) before calling the tool — the tool call's arguments must contain the actual finished content, not a summary of what you plan to write.

## Example call

```
{"filepath": "ledger.xlsx", "json_data_matrix": [
["Metric", "Value"],
["License Sales", 50000],
["Cloud Revenue", 120000],
["Consulting", 30000],
["Total", "=SUM(B2:B4)"]
]}
```
## Common mistakes to avoid
- Writing `"Total", 200000` instead of `"Total", "=SUM(B2:B4)"` — this defeats the entire
  purpose of this skill and will be treated as a constraint violation.
- Forgetting the header row, which makes the resulting spreadsheet ambiguous to a human reader.
- Wrapping the formula string in extra quotes or escaping the `=` — pass it as a plain string
  cell value exactly as shown above.