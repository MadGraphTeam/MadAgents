---
name: verify-claims
description: "Extract factual claims from text and verify each one using execution, source inspection, or physics reasoning."
---

# Verify Claims

Extract verifiable claims from a text and verify each one.

## Input

$ARGUMENTS

If a file path was given, read it. If text was given, use it directly. If nothing was given, ask the user what to verify.

If the text references user-facing written artifacts (answer files, scripts, code, reports), read those artifacts and extract claims from them too — not just from the conversational response.

## Step 1: Extract claims

Split the text into individual, self-contained factual claims. Write them to `/workspace/verify/claims.json`.

Rules:
- Each claim should be a single, specific, verifiable statement.
- Claims must be self-contained — understandable without reading the full source text.
- Include claims about commands, parameter values, file paths, physics reasoning, expected outputs, and any other factual assertions.
- Preserve qualifying language ("roughly", "approximately") — do not rephrase approximate guidance as hard facts.
- Do NOT include subjective opinions or meta-commentary.

Output format — a JSON array, each object with a `claim` key:
```json
[
  {"claim": "The MadGraph command to generate Drell-Yan at LO is: generate p p > e+ e-"},
  {"claim": "The default number of events in run_card.dat is 10000"}
]
```

## Step 2: Verify each claim

For each claim, determine whether it is correct.

### Environment

You may install any software needed for verification (e.g. MadGraph5_aMC@NLO, Pythia8, Delphes).

### Evidence rules

Only the following count as evidence, and only when the result is unambiguous:
- **Execution output**: Run a MG5 script or command that tests the claim. Observe the output.
- **Source code inspection**: Read the relevant Python source files in the MadGraph installation directory.
- **Physics reasoning**: Explicit derivation from established principles (conservation laws, symmetries, kinematics, coupling structure) showing every step of the proof. MadGraph's implementation may differ from textbook physics in conventions, approximations, and defaults — for any claim about how MadGraph actually behaves, use execution or source inspection instead.

Reason very carefully about what the evidence actually proves. If the result is ambiguous, could be interpreted multiple ways, or has a loophole that does not fully rule in or rule out the claim — it is not conclusive. Investigate further. Only mark the claim as inconclusive if you are confident that verification is not possible.

The following are NOT evidence — they may help you find the correct answer, but never count as proof:
- Curated documentation files at `/madgraph_docs/`
- Web sources (arXiv, Launchpad, forums, blogs, Stack Overflow)

If you delegate verification to subagents, instruct them that these same evidence rules apply. Subagents must not cite curated documentation or web sources as proof.

## Output

For each claim, record:
- `claim`: the claim text
- `correct`: true, false, or null (inconclusive)
- `method`: execution, inspection, source_inspection, physics_reasoning, or null
- `evidence`: list of raw evidence items
- `explanation`: auditable justification

## Self-Validation

After writing results, verify:
- Each claim has all required fields
- `correct` is true, false, or null
- `method` is null only when `correct` is null
- `explanation` is non-empty
