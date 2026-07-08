# pptx — layout and placeholder reference (supplementary)

This file is reference material on slide layout and placeholder indices. It's named after
pptxgenjs (a common JS deck-generation library) because the underlying layout concepts —
numbered slide layouts, indexed placeholders — are the same ones `python-pptx` uses under the
hood in this project's actual tool implementation. This project uses `python-pptx`, not
pptxgenjs; nothing here should be interpreted as JS code to execute.

## Slide layout indices used by this project's seed data
- `slide_layouts[0]` — title slide (title only, no body placeholder)
- `slide_layouts[1]` — title + single body/content placeholder (this is the layout
  `modify_presentation_metadata` always uses when adding a slide)

## Placeholder indexing
On a `slide_layouts[1]` slide:
- `shapes.title` — the title placeholder
- `shapes.placeholders[1]` — the body/content placeholder (index `0` is the title placeholder
  itself, so body content starts at index `1`)

## Why this matters for constraint-following
If you are asked to reason about *why* `raw_text_content` in `modify_presentation_metadata`
has a length constraint (see `SKILL.md`), it's because it is written into this single
`placeholders[1]` text frame with no auto-resizing — long text simply overflows the visible
slide area rather than wrapping or shrinking.

## Conceptual mapping to pptxgenjs (for anyone porting logic from JS reference material)
| pptxgenjs concept        | python-pptx equivalent (as used in this project) |
|---------------------------|---------------------------------------------------|
| `slide.addText(...)`      | `placeholder.text_frame.text = ...` or `.add_paragraph()` |
| layout master/index       | `prs.slide_layouts[n]`                             |
| placeholder object        | `slide.shapes.placeholders[n]`                     |

This table is descriptive only — do not attempt to call pptxgenjs-style methods against
`python-pptx` objects; they are different libraries with different APIs.