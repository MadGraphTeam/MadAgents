---
name: edit-docs
description: "Edit MadGraph documentation with parallel review: style, quality, and factual verification. Revises until all checks pass or max rounds reached."
---

# Edit MadGraph Documentation

Guided workflow for editing the MadGraph documentation with parallel review and revision.

## Task

$ARGUMENTS

If no task was given, ask the user what they want to change.

## Workspace Setup

If a draft already exists from a previous edit, skip setup — reuse it.

Otherwise, call the `get_doc_draft` MCP tool to create a writable copy:
```
get_doc_draft("/workspace/docs_draft")
```

## Workflow

### Round 1: Edit

Invoke the **doc-editor** agent with the task. It edits the draft files at `/workspace/docs_draft`.

After it finishes, generate a diff using the MCP tool (this correctly handles the overview file which lives outside `/madgraph_docs/`):

```
get_doc_diff("/workspace/docs_draft")
```

Save the diff output to `/workspace/docs_changes.diff`.

### Round 1: Parallel Review

Invoke ALL THREE reviews simultaneously — do not run them sequentially:

1. **doc-style-reviewer** agent — review the changed files for style and formatting
2. **doc-quality-reviewer** agent — review the changed files for structure, placement, duplication
3. **verifier** agent — extract and verify factual claims from the changed content. Dispatch with:

   > Extract and verify all factual claims from the documentation changes.
   >
   > - Diff of changes: `/workspace/docs_changes.diff`
   > - Updated docs: `/workspace/docs_draft/`
   >
   > Read the diff to understand what was changed, then read the relevant files for full context. Only extract claims from **new or changed content** — do not extract claims from unchanged parts of the documentation.
   >
   > **Doc-specific extraction rules:**
   > - Extract both factual claims AND executable code blocks.
   > - Any fenced code block tagged as `mg5`, `madgraph`, `mg5_amc`, `bash`, or `python` that involves MadGraph commands must be extracted. For each, include the source file and section for context, what the code block accomplishes, and the full code block content.
   >
   > **Doc-specific verification rules:**
   > - MG5 code blocks must be **executed** to confirm they run without errors.
   > - Default values must be verified by reading **source code** (e.g., `banner.py`, template card files) — not by trusting existing documentation.
   > - Check that claims do not contradict each other within the document.
   > - Do NOT verify: general physics concepts, high-level descriptions, cross-references, formatting, or style choices.
   > - If you discover **pre-existing errors** in the existing documentation (under `/madgraph_docs/`) while verifying, report them separately as incidental errors.
   >
   > Write verdicts to `/workspace/verify/verdicts.json`.

Wait for all three to complete.

### Decide

If all three checks pass (style: PASS, quality: PASS, no incorrect claims), proceed to step "Discuss with user."

If ANY check fails, collect all feedback and continue to "Revise."

### Revise (rounds 2+)

Send ALL feedback to the **doc-editor** agent in a single message:

> Your previous changes had issues. Please revise the files at `/workspace/docs_draft`.
>
> **Factual issues**: [list incorrect claims with evidence]
> **Style issues**: [list style problems]
> **Quality issues**: [list quality problems]
>
> Address ALL issues in this revision.

After revision, regenerate the diff (call `get_doc_diff("/workspace/docs_draft")` and save to `/workspace/docs_changes.diff`) and run the parallel review again (all three checks simultaneously).

Repeat up to 5 rounds total. If checks still fail after 5 rounds, proceed to "Discuss with user" anyway — note which issues remain unresolved.

### Discuss with user

Present the diff to the user (call `get_doc_diff("/workspace/docs_draft")` and show the output) and summarize:
- What was changed and why
- Any review findings that were fixed
- Any claims that could not be verified (mark as uncertain)
- Any remaining unresolved issues from the review

Wait for the user's feedback. If they request changes, go back to "Edit" with their instructions.

### Apply changes

Only apply changes if the user explicitly asks you to. If in doubt, ask.
Only apply changes where all factual claims have been verified.
```
apply_doc_changes("/workspace/docs_draft")
```
