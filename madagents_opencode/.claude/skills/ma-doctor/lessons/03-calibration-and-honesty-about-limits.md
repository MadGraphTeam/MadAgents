# 03 — Calibration and honesty about limits

> A well-calibrated, honestly-hedged answer beats a uniformly confident one. State what you can't do.

Calibration — stating a confidence and being right that fraction of the time — is a distinct and
more valuable quality than point accuracy. A confident point prediction that is occasionally,
catastrophically wrong scores worse than a calibrated probability the user can weigh. The
corollary is honesty about limits: every card/skill states what it *cannot* do, and a return
marks when it is not source-grounded. Declaring the limit is what makes the output trustworthy —
it is a product feature, not a hedge to be trimmed.

## In a harness like this

This is the rationale for the confidence labels (DIRECT / INFERRED / HYPOTHESIS) and for hedge
preservation: the value the on-the-loop user extracts is a *calibrated* claim they can act on, not
a uniformly confident assertion. A hedge the labels preserve is exactly the calibration signal a
user acts on but an automated one-shot answer would drop. Honesty about the edge of a consultant's
competence is what lets the lead and the user calibrate. When auditing a harness, check that every
agent's card states its limits and that the lead's final voice carries the hedges through rather
than flattening them into false confidence.

## Where the books say it

- **Polymarket** — §09/§03 (calibration: prediction markets beat polls on Brier score even when occasionally less accurate on individual events), §06/§08 (confidence is not correctness — a near-certain share still carries the full downside when the unlikely outcome hits).
- **Src-Analysis** — ch3/ch11. Explicit honesty / anti-false-claims: report failures faithfully, don't imply an unrun verification passed, don't sugarcoat.
- **Hermes** — §11 (bake the question of whether a real source exists into the return — x_search's `degraded=true`), §05/§21 (trust comes from honesty about limits, not from layers of protection).
- **Skills** — ch9/ch10. A skill that hides its limitations is not worth trusting — every distillation skill carries an explicit what-this-cannot-do section.
