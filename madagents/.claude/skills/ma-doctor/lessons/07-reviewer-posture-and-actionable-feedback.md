# 07 — Reviewer posture and actionable feedback

> The reviewer's default stance is doubt; it checks behavior not intent; and every finding carries its fix.

A reviewer earns its keep through three properties. (1) **Doubt by default** — "assume this code
is broken until proven otherwise"; if the evaluator is polite too, the loop is just an agent
nodding at itself. (2) **Behavior, not intent** — an evaluator that only reads judges "does this
*look* right"; one that acts checks "does it *run* right" against the real artifact. (3) **A
finding carries its fix** — a flag comes with its remedy or route and a source pointer, ordered
by severity (fatal issues before cosmetic ones), so the doer self-repairs instead of
re-diagnosing a bare complaint.

## In a harness like this

Reviewer cards default to "the claim is wrong until the source proves it" — the skeptical posture
made explicit. Reviewers verify against the actual source (file:line, not the consultant's prose)
and a real probe, not a plausible-sounding claim. Their findings are actionable — the correction or
the right specialist to route to — and ordered so a wrong observable is never buried under a style
nit. When auditing a harness, check each reviewer card for all three properties: a doubting default
stance, a check on behavior against the real artifact, and findings that carry their fix and a
source pointer in severity order.

## Where the books say it

- **Loop** — §05. The evaluator's default stance should be doubt rather than trust, and an evaluator that acts examines behaviour rather than intent (hooked to a real tool to click and screenshot, not to read JSX).
- **Skills** — ch9. Fatal issues first, since factual errors matter an order of magnitude more than word choice; and a finding carries its fix — do not merely observe that something reads as AI-generated, supply the rewrite.
- **Harness** — §06/§15. Feedback carries the fix — a reviewer return states what is wrong AND how to fix it, plus a source pointer, so the doer self-repairs.
