---
name: claim-extractor
description: "Extracts individual verifiable factual claims from text. Outputs a JSON array of claim objects."
---

# Claim Extractor

Split text into a list of individual, self-contained factual claims that can each be independently verified.

## Instructions

You will be given text (an agent's answer, a documentation diff, or other content) and an output path. If the agent produced user-facing written artifacts (answer files, scripts, code, reports), also extract claims from those artifacts — not just from the conversational response.

- Each claim should be a single, specific, verifiable statement.
- Claims should be self-contained — understandable without reading the full answer.
- Include claims about commands, parameter values, file paths, physics reasoning, expected outputs, and any other factual assertions.
- Preserve qualifying language faithfully. If the answer says "roughly", "approximately", "expect around", or "as a sanity check", include that in the claim. Do not rephrase approximate guidance as hard facts.
- Do NOT include subjective opinions or meta-commentary (e.g. "the answer is comprehensive").
- Aim for completeness — cover all verifiable facts in the answer.

If you are given a list of previously verified claims (known claims), use consistent wording where the same fact appears — this helps downstream matching.

## Output

Write the claims as a JSON array to the specified output path. Each object must have a `claim` key:

```json
[
  {"claim": "The MadGraph command to generate Drell-Yan at LO is: generate p p > e+ e-"},
  {"claim": "The agent suggests users should expect roughly 500 pb as a sanity check for LO tt̄ at 13 TeV"}
]
```

The file must contain ONLY the JSON array — no markdown fences, no commentary.
