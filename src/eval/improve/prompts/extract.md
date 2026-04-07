Extract all verifiable factual claims and executable code blocks from the documentation changes.

## Changes

A diff of all changes is at `{diff_path}`. The updated documentation files are at `{docs_dir}`.

Read the diff to understand what was changed, then read the relevant files for full context.

## Instructions

Extract two types of claims:

1. **Factual claims**: Specific, verifiable statements about MadGraph behavior, parameter names, default values, command syntax, file paths, physics behavior, etc. Each must be self-contained. Preserve qualifying language faithfully — if the text says "roughly", "approximately", or "typical", include that in the claim. Do not rephrase approximate guidance as hard facts.

2. **Code blocks**: Each fenced code block tagged as `mg5`, `madgraph`, `mg5_amc`, `bash`, or `python` that involves MadGraph commands. For each, create a claim that includes the source file and section (for context), what the code block is supposed to accomplish, and the full code block content. The verifier will read the source file to understand the setup context.

{known_claims_section}

Only extract claims from new or changed content — do not extract claims from unchanged parts of the documentation.

Aim for completeness — cover all verifiable facts in the changed content.

Do NOT include:
- General descriptions or explanations that aren't specific enough to verify
- Style or formatting observations
- Cross-references to other documents

## Output

Write the claims as a JSON array to `{output_path}`.

Each object must have a `claim` key:

```
[
  {"claim": "The LO dilepton mass cut parameter in run_card.dat is mmll"},
  {"claim": "Given the context in nlo-computations.md § Running NLO processes, the following generates an NLO Drell-Yan process:\ngenerate p p > e+ e- [QCD]\noutput DY_NLO\nlaunch DY_NLO"}
]
```
