# pptx — editing existing decks (reference)

This file is a deeper reference for tasks that involve modifying a deck that already has
content, rather than creating a fresh single slide.

## Reading before editing
Always call `read_office_file` on the target `.pptx` first, even if you already have the raw
data elsewhere. The Markdown-converted output tells you the actual slide order and any existing
titles, which matters because `modify_presentation_metadata` appends slides at the end — it
does not let you insert at a specific position or edit an existing slide's text.

## What `modify_presentation_metadata` can and cannot do
- It can only **append** a new slide using `slide_layouts[1]` (title + single content
  placeholder). It cannot:
  - Edit the text of an existing slide
  - Reorder slides
  - Change the layout of an existing slide
  - Insert images, charts, or tables
- If a task requires any of the above, say so explicitly in your findings back to the
  supervisor rather than attempting a workaround — do not fall back to manual XML manipulation.

## Multi-slide additions
If a task calls for more than one new slide (e.g. "add a summary slide and a next-steps
slide"), call `modify_presentation_metadata` once per slide, in the order you want them to
appear. Each call re-opens and re-saves the file, so always pass the same `filepath` across
calls in the same task.

## Content formatting inside `raw_text_content`
The tool passes this string directly into a single text frame — it does not parse Markdown,
bullet syntax, or line breaks specially. If you want multiple bullet-like lines, separate them
with `\n` in the string; each line will appear as a separate paragraph in the placeholder, but
none will be auto-formatted as a bulleted list.

## Verification after editing
After appending a slide, call `read_office_file` again on the same file to confirm the new
slide's title and body text landed as expected before reporting success back to the supervisor.