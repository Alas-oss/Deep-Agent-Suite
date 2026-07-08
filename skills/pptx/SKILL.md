---
description: Read data out of slide decks, or append new slides summarizing agent findings.
tools: read_office_file, modify_presentation_metadata
triggers: pptx, slide deck, presentation, slides
reference_files: editing.md, pptxgenjs.md
---

# pptx skill

## When to use this skill
Use this when the task involves extracting text/data from an existing `.pptx`, or adding a new
slide to communicate a result (e.g. a summary slide appended after other work is done).

## Constraints (must follow exactly)
- Always use `read_office_file` for extraction — never attempt to parse `.pptx` XML manually, and never use `unpack_raw_xml` for this unless explicitly asked to inspect raw OpenXML.
- When adding a slide via `modify_presentation_metadata`, keep `raw_text_content` under 500 characters — this uses a fixed single-placeholder layout (`slide_layouts[1]`), not a full text box, so long content will visually overflow the slide.
- Only use `action_type: "add_slide"` — no other action types are currently implemented in the tool.
- If the target `.pptx` file does not exist yet `modify_presentation_metadata` will create a new, empty presentation before adding the slide — confirm this is the intended behavior for the task rather than assuming a source file should already exist.
- Do not check whether an output file already exists before creating it — just create or overwrite it directly unless the task explicitly says to check first.
- Never call a file-writing tool with placeholder, generic, or one-line content. Write out the full, specific content requested in the task (multiple sentences/rows/bullets as appropriate) before calling the tool — the tool call's arguments must contain the actual finished content, not a summary of what you plan to write.


## Example call
```
{"filepath": "outline.pptx", "action_type": "add_slide",
"raw_text_content": "Q3 revenue grew 12% year over year, driven by cloud subscriptions."}
```
## Additional reference material
This skill has supplementary reference files in this same folder:
- `editing.md` — detailed procedures for reading and modifying existing multi-slide decks
- `pptxgenjs.md` — reference notes on slide layout/placeholder indices for generation

These are not loaded automatically. If your task needs that level of detail, call
`load_skill_blueprint` again with `skill_name="pptx/editing"` or `skill_name="pptx/pptxgenjs"`
(folder/file-stem format).