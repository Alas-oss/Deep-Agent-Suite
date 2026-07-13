---
name: pptx
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
- Aim for real depth: a docx report section should be several sentences, a spreadsheet
  should have multiple meaningful rows (not just one), and a slide should have several
  bullet points, unless the task explicitly asks for something brief.
- Do not check whether the TARGET FILE already exists before creating it — just create or
  overwrite it directly unless the task explicitly says to check first. This does NOT mean
  skip planning your slides.
- Before your first `modify_presentation_metadata` call, decide your complete slide list —
  how many slides, and each one's title and content — in your own reasoning. Then call the
  tool exactly once per planned slide, in order. Never call it speculatively, to "try again,"
  or to redo a slide you're unsure about — there is no edit/delete capability, so getting it
  right the first time matters. If you find yourself calling this tool more than once for
  what should be the same slide, stop and use the total_slides count in the tool's response
  to figure out what's already there before continuing.

## Example call
```
{"filepath": "outline.pptx", "action_type": "add_slide",
"raw_text_content": "Q3 revenue grew 12% year over year, driven by cloud subscriptions."}
```
## Additional reference material
This skill has supplementary reference files in this same folder:
- `editing.md` — detailed procedures for reading and modifying existing multi-slide decks
- `pptxgenjs.md` — reference notes on slide layout/placeholder indices for generation

These are not loaded automatically. If your task needs that level of detail, use `read_file`
on `skills/pptx/editing.md` or `skills/pptx/pptxgenjs.md` directly.