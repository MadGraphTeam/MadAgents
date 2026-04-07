Split the following agent answer into a list of individual, self-contained factual claims that can each be independently verified.

## Question
{question}

## Agent's Answer
{agent_response}

If the agent produced user-facing written artifacts (answer files, scripts, code, reports) — e.g., files under `/output/` or `/workspace/` — also extract claims from those artifacts. The answer above may reference or summarize them; extract claims from the actual artifact content, not just the summary.

{known_claims_section}

## Instructions

- Each claim should be a single, specific, verifiable statement.
- Claims should be self-contained — understandable without reading the full answer.
- Include claims about commands, parameter values, file paths, physics reasoning, expected outputs, and any other factual assertions.
- Preserve qualifying language faithfully. If the answer says "roughly", "approximately", "expect around", or "as a sanity check", include that in the claim. Do not rephrase approximate guidance as hard facts.
- Do NOT include subjective opinions or meta-commentary (e.g. "the answer is comprehensive").
- Aim for completeness — cover all verifiable facts in the answer.

## Output

Write the claims as a JSON array to `{output_path}`. Each object must have a `claim` key:

```
[
  {"claim": "The MadGraph command to generate Drell-Yan at LO is: generate p p > e+ e-"},
  {"claim": "The agent suggests users should expect roughly 500 pb as a sanity check for LO tt̄ at 13 TeV"}
]
```
