---
name: verify-claims
description: "Extract factual claims from text and verify each one using execution, source inspection, or physics reasoning. Uses specialized subagents for extraction, triage, verification, and caching."
---

# Verify Claims

Extract verifiable claims from a text and verify each one. This workflow uses specialized subagents for each step — do not do the work yourself.

## Input

$ARGUMENTS

If a file path was given, read it. If text was given, use it directly. If nothing was given, ask the user what to verify.

If the text references user-facing written artifacts (answer files, scripts, code, reports), read those artifacts and extract claims from them too — not just from the conversational response.

## Workspace Setup

Create `/workspace/verify/` for all intermediate files.

If a claim database exists at `/output/.eval/claim_db.json`, copy it to `/workspace/verify/known_claims.json`. Otherwise, create an empty array: `[]`.

## Step 1: Extract claims

Invoke the **claim-extractor** agent (use model `haiku`). Tell it:
- The text to extract claims from (either the file path or inline text)
- Output path: `/workspace/verify/claims.json`
- If known claims exist, pass them so it can use consistent wording

After it finishes, read `/workspace/verify/claims.json` and verify it contains a valid JSON array. If it's empty or malformed, report this and stop.

## Step 2: Triage against known claims

Skip this step if the claim database is empty.

Invoke the **claim-triage** agent (use model `haiku`). Tell it:
- Claims file: `/workspace/verify/claims.json`
- Known claims file: `/workspace/verify/known_claims.json`
- Output path: `/workspace/verify/triage.json`

After it finishes, read `/workspace/verify/triage.json`. The result is a list of known-claim IDs that are relevant to the new claims.

## Step 3: Verify claims

Copy `/workspace/verify/claims.json` to `/workspace/verify/verdicts.json`. This file will be enriched in place with verdict fields.

Invoke the **madgraph-operator** agent for verification. Tell it:

> Verify each claim in `/workspace/verify/verdicts.json`.
>
> This file contains a JSON array of claims. For each claim, determine whether it is correct by adding verdict fields to the existing object.
>
> For each claim, add the following fields:
> - `correct`: true (claim is correct), false (claim is incorrect), or null (inconclusive after exhausting all applicable methods)
> - `method`: the method that provided conclusive evidence — `execution`, `inspection`, or `physics_reasoning`. Set to null only when `correct` is null.
> - `evidence`: a list of raw evidence items — verbatim script output, source code excerpts, computed values. Factual and uninterpreted.
> - `explanation`: a self-contained, auditable justification. State what was expected, what was found, and why. Do NOT write vague justifications like "Correct" or "Matches documentation".
>
> **Environment**: You may install any software needed for verification (e.g. MadGraph5_aMC@NLO, Pythia8, Delphes).
>
> **Evidence rules** — only the following count as evidence, and only when the result is unambiguous:
> - **Execution output**: Run a MG5 script or command that tests the claim. Observe the output.
> - **Source code inspection**: Read the relevant Python source files in the MadGraph installation directory.
> - **Physics reasoning**: Explicit derivation from established principles (conservation laws, symmetries, kinematics, coupling structure) showing every step of the proof. MadGraph's implementation may differ from textbook physics in conventions, approximations, and defaults — for any claim about how MadGraph actually behaves, use execution or source inspection instead.
>
> Reason very carefully about what the evidence actually proves. If the result is ambiguous, could be interpreted multiple ways, or has a loophole that does not fully rule in or rule out the claim — it is not conclusive. Investigate further. Only mark the claim as inconclusive if you are confident that verification is not possible.
>
> The following are NOT evidence — they may help you find the correct answer, but never count as proof:
> - Curated documentation files at `/madgraph_docs/`
> - Web sources (arXiv, Launchpad, forums, blogs, Stack Overflow)
>
> If you delegate verification to subagents, instruct them that these same evidence rules apply. Subagents must not cite curated documentation or web sources as proof.
>
> Previously verified claims are at `/workspace/verify/known_claims.json`. Use them at your discretion to skip or expedite verification where applicable — but re-verify if you have any doubt. IMPORTANT: Do NOT generalize from known claims. Only reuse a known claim when it covers exactly the same fact. A known claim about a parameter value in one context does not verify the same parameter in a different context. When in doubt, verify from scratch.

## Step 4: Select claims for database

Invoke the **claim-remember** agent (use model `haiku`). Tell it:
- Verdicts file: `/workspace/verify/verdicts.json`
- Known claims file: `/workspace/verify/known_claims.json`
- Output path: `/workspace/verify/remember.json`

## Step 5: Update claim database

Read `/workspace/verify/remember.json` (a list of indices). For each selected index, read the corresponding verdict from `/workspace/verify/verdicts.json`.

Load the claim database from `/output/.eval/claim_db.json` (or start with `[]`). For each selected claim:
- Assign an `id` (max existing id + 1, or 0 if empty)
- Add the claim with its `claim`, `correct`, `method`, `evidence`, and `explanation` fields
- Add `count: 1`

Write the updated database back to `/output/.eval/claim_db.json`.

## Output

Report to the user:
- Number of claims extracted
- Number of claims verified as correct, incorrect, inconclusive
- Number of new claims added to the database
- Any claims marked incorrect — list them with their explanations
