# 08 — The evaluator is the floor

> The generator decides what a system *can* produce; the evaluator decides what it *won't*. Investing in the evaluator is investing in the floor.

Without a real check, the more cheerfully a loop runs the more bad code it stacks up. The
reviewer caps the downside — it is the thing that keeps a wrong result from shipping — and that
cap, not raw generation, is what an independent-verification loop buys (a measured 2-3× quality
gain). The harness amplifies whatever method sits under it: a fast, elaborate, ungrounded
cascade loses faster than one careful answer, so the verification layer is load-bearing, not
decoration.

## In a harness like this

The reviewer roster caps what the system *won't* ship — a wrong observable — and that cap is
exactly what an unreviewed single pass lacks. The reviewers' token cost is what buys the accuracy
edge over a bare loop; thinning it removes the brakes that justify the scaffold. Re-weight any
"thin the harness" instinct toward *keep the brakes*.

## Where the books say it

- **Loop** — §05. The generator's level sets what a loop can produce; the evaluator's level sets what it will not produce. A loop's floor is its evaluator.
- **Polymarket** — §07. The risk-control layer is what decides whether a bot makes or loses money; automation is not a money printer, and a flawed underlying strategy only loses faster once automated.
- **Harness** — §04/§08. An independent verification loop improves output quality 2-3× (Boris's #1 tip) — quantified backing for the reviewer cascade.
