---
paths:
  - "**/*.md"
---

# Documentation Editing Conventions

## Layout

The MadGraph docs use a flat layout:

- **Overview file**: High-level summary linking to all topic files. Under 100 lines.
- **Topic files** (`*.md`): One file per topic, self-contained. New files must be referenced in the overview.

## Editing workflow

Use the dedicated agents for documentation work:
- **doc-editor**: makes edits
- **doc-style-reviewer**: reviews style and formatting
- **doc-quality-reviewer**: reviews structure, placement, duplication

All factual claims in documentation changes must be verified (via the **verifier** agent) before applying.

## Applying changes

Never apply documentation changes (via `apply_doc_changes`) unless:
1. All factual claims have been verified.
2. The user explicitly requests it.

If in doubt, ask first.
