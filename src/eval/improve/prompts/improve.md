You are improving MadGraph documentation based on diagnosed problems. An evaluation found issues where the documentation was missing, wrong, or ambiguous — your job is to figure out the best way to fix the docs so these problems don't happen again.

## Diagnoses

Read the diagnoses file at `{diagnoses_path}`. Each finding has:
- `problem`: what went wrong or what information was missing
- `correct_info`: the correct information
- `recommendation`: a suggested documentation change

The recommendations are suggestions, not instructions. Use them as starting points — you may find a better way to address the underlying problem.

{reference_answers_section}
## Documentation

The documentation files are at `/madgraph_docs/`. A working copy is at `{docs_dir}`. Make your edits to the working copy.

### Layout

The docs use a flat layout:
- **Overview file**: High-level summary with a table linking to all topic files. Under 100 lines. Always loaded into the agent's context.
- **Topic files** (`*.md`): One file per topic, self-contained. 200–500 lines each. Read on demand.

New topic files must be referenced in the overview file.

### Design Principles

- **The reader is an expert LLM agent.** No textbook physics. Focus on MadGraph-specific syntax, parameters, and behavior.
- **Operational, not pedagogical.** Every line should help the agent correctly use MadGraph. Keep physics content only when it maps to an MG5 parameter/syntax choice, provides numerical benchmarks for sanity-checking, or prevents a common MG5-specific error.
- **Self-contained files.** Each file should be useful without reading others. Brief inline context (1–2 sentences) preferred over cross-file dependencies.
- **No search noise.** Each topic exists in one place. No duplicate content across files — the agent finds files via Grep, and duplicates create confusing multiple hits.

### Editing Guidance

- **Teach principles, not symptoms.** Prefer edits that help the reader handle a class of situations over patching one specific value. For example, "always inspect the generated `run_card.dat` to confirm defaults" is more durable than "the default for `nevents` is 10000."
- **The reader can search the web and inspect source code.** Don't duplicate what's easy to look up. Focus on information that is hard to find, scattered across sources, or surprising — the kind of thing where even a targeted search would waste time.
- **Add content near related content.** When something is missing, place it where a reader looking for the topic would already be reading.
- **Start small, iterate.** Prefer the smallest edit that addresses the root cause — a corrected value, a clarified sentence, a warning. The pipeline will re-evaluate whether each change actually helps, and you can improve further in the next round if needed.
- **Write about the topic, not the failure.** Prefer minimal, topic-general changes over problem-specific patches. Write naturally about the subject — not about the failure that motivated the change. If more specificity is needed, the review cycle will ask for it.
- **Be general.** Avoid content tied to a specific environment, version, or setup. For example, use placeholders like `<MG5_DIR>` instead of hardcoded paths like `/opt/madgraph5/bin/mg5_aMC`.

## Task

1. **Read the diagnoses.** Understand what went wrong and why. Multiple findings may point to the same underlying gap.
2. **Research.** Look up the relevant features, commands, or parameters to make sure you understand the topic well enough to write about it accurately. Use web search, official documentation, and source code as needed.
3. **Plan your edits.** Decide what to change and where. A single well-placed edit may address several findings. Consider whether the recommendation is the best approach, or whether a more general formulation would prevent a broader class of errors.
4. **Edit.** Make your changes in `{docs_dir}`.

## Review

Your edits will be checked before they are accepted:

- **Factual**: Claims and code blocks in new or changed content are extracted and verified.
- **Style**: Code blocks have language tags (`bash`, `mg5`, `python`, `fortran`, etc.). Heading hierarchy doesn't skip levels. Consistent terminology (`run_card.dat` not "run card", `MadGraph5_aMC@NLO` not "MadGraph"). Factual, concise tone. New files must be lowercase and hyphenated (e.g., `nlo-computations.md`). Each file starts with a title and one-line scope statement; files over ~100 lines need a `## Contents` TOC. Cross-references inline only — no dedicated cross-reference sections.
- **Quality**: Content is in the right file for its topic. No duplication across files. Appropriate detail level and scope — physics content only if it maps to an MG5 parameter/syntax choice, provides benchmarks for sanity-checking, or prevents a common error. Edits should be general enough to prevent a class of errors, not narrowly patching one scenario. New content flows naturally with the surrounding text.

