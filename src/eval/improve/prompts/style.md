Review the following documentation changes for style and formatting consistency.

## Changed Files

The documentation working copy is at `{docs_dir}`. The following files were modified:

{changed_files}

Focus ONLY on the new or modified content — do NOT flag pre-existing style issues in unchanged parts of the file.

Check for:

1. **Markdown formatting**: Proper heading hierarchy (no skipped levels), consistent list formatting, correct code fence language tags.
2. **Terminology**: Consistent use of MadGraph terminology (e.g., "run_card.dat" not "run card", "MadGraph5_aMC@NLO" not "MadGraph").
3. **Tone**: Matches the rest of the documentation — factual, concise, no unnecessary hedging.
4. **No hardcoded paths**: Environment-specific absolute paths (e.g., `/opt/madgraph5/bin/mg5_aMC`) must use placeholders like `<MG5_DIR>` instead. Hardcoded paths break across installations.
5. **File naming**: Lowercase, hyphenated, descriptive (e.g., `nlo-computations.md`). No numeric prefixes, no underscores.
6. **Structure**: Title followed by a one-line scope statement. Files over ~100 lines should have a `## Contents` TOC.
7. **Cross-references**: Inline only, where contextually relevant. No dedicated cross-reference sections at the end of files.

Do NOT assess factual correctness — that is the fact verifier's job.

Only report issues that are serious enough to warrant a revision. Minor cosmetic preferences should be ignored.

Write your assessment to `{output_path}`:

```
{
  "passed": true or false,
  "issues": [
    "Description of each serious style issue found"
  ]
}
```

Set `passed: false` only if there are issues that must be fixed. If the style is acceptable, set `passed: true` and `issues: []`.
