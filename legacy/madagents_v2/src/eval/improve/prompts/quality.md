Review the following documentation changes for quality and appropriateness.

## Changed Files

The documentation working copy is at `{docs_dir}`. The following files were modified:

{changed_files}

## Documentation Layout & Design

The documentation uses a flat layout:
- **Overview file**: High-level summary with a table linking to all topic files. Under 100 lines.
- **Topic files** (`*.md`): One file per topic, self-contained. 200-500 lines each.

New topic files must be referenced in the overview file.

Design principles:
- **The reader is an expert LLM agent.** No textbook physics. Focus on MadGraph-specific syntax, parameters, and behavior.
- **Operational, not pedagogical.** Every line should help the agent correctly use MadGraph.
- **Self-contained files.** Each file useful without reading others.
- **No search noise.** Each topic in one place — no duplicate content across files.

## Checks

Read each changed file in the context of the full documentation set at `{docs_dir}` and check for:

1. **Right file**: Is the change in the most appropriate file for its topic?
2. **Detail level**: Is the change at the right level of detail for this document?
3. **Duplication**: Does the change duplicate information already present in another file? No duplicate content across files.
4. **Scope**: Does the change stay focused on its purpose, or does it introduce tangential content? Physics content is only justified if it maps to an MG5 parameter/syntax choice, provides numerical benchmarks for sanity-checking, or prevents a common MG5-specific error.
5. **Generality**: Is the change general enough to prevent a class of similar errors, or is it too narrowly focused on one specific value or scenario? Documentation should teach principles and methodology (e.g., "always verify defaults by inspecting the generated card") rather than patch individual symptoms (e.g., "the top mass default is 174.3 GeV"). A note about one specific parameter is acceptable only if it also teaches the general approach.
6. **Coherence**: Does the surrounding content still flow naturally with the change inserted?

Do NOT assess factual correctness — that is the fact verifier's job. Only assess structure, placement, and appropriateness.

Only report issues that are serious enough to warrant a revision. Minor style preferences, cosmetic suggestions, and pre-existing issues in unchanged content should be ignored.

Write your assessment to `{output_path}`:

```
{
  "passed": true or false,
  "issues": [
    "Description of each serious quality issue found"
  ]
}
```

Set `passed: false` only if there are issues that must be fixed. If the change is structurally sound, set `passed: true` and `issues: []`.
