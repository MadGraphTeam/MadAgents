Verify each claim in the file `{verdicts_path}`.

This file contains a JSON array of claims extracted from an agent's answer. For each claim, determine whether it is correct by adding verdict fields to the existing object.

## Question Context
{question}

## Previously Verified Claims

A file of previously verified claims may be available at `{known_claims_path}`. These are claims that were verified in earlier runs with real evidence (execution output, source code inspection, etc.). Use them at your discretion to skip or expedite verification where applicable — but re-verify if you have any doubt.

IMPORTANT: Do NOT generalize from known claims. Only reuse a known claim when it covers exactly the same fact. For example, a known claim about a parameter value in one context does not verify the same parameter in a different context. When in doubt, verify from scratch.

## Instructions

Read `{verdicts_path}`, verify each claim, and edit the file in place. For each object, add the following fields:

- `correct`: true (claim is correct), false (claim is incorrect), or null (inconclusive after exhausting all applicable methods)
- `method`: the method that provided conclusive evidence — `execution`, `inspection`, or `physics_reasoning`. Set to null only when `correct` is null.
- `evidence`: a list of raw evidence items — verbatim script output, source code excerpts, computed values. Factual and uninterpreted.
- `explanation`: a self-contained, auditable justification. State what was expected, what was found, and why. Do NOT write vague justifications like "Correct" or "Matches documentation".

## Environment

You may install any software needed for verification (e.g. MadGraph5_aMC@NLO, Pythia8, Delphes).

## Evidence Rules

Only the following count as evidence, and only when the result is unambiguous:
- **Execution output**: Run a MG5 script or command that tests the claim. Observe the output.
- **Source code inspection**: Read the relevant Python source files in the MadGraph installation directory.
- **Physics reasoning**: Explicit derivation from established principles (conservation laws, symmetries, kinematics, coupling structure) showing every step of the proof. MadGraph's implementation may differ from textbook physics in conventions, approximations, and defaults — for any claim about how MadGraph actually behaves, use execution or source inspection instead.

Reason very carefully about what the evidence actually proves. If the result is ambiguous, could be interpreted multiple ways, or has a loophole that does not fully rule in or rule out the claim — it is not conclusive. Investigate further. Only mark the claim as inconclusive if you are confident that verification is not possible.

The following are NOT evidence — they may help you find the correct answer, but never count as proof:
- Curated documentation files at `/madgraph_docs/`
- Web sources (arXiv, Launchpad, forums, blogs, Stack Overflow)

If you delegate verification to subagents, instruct them that these same evidence rules apply. Subagents must not cite curated documentation or web sources as proof.
