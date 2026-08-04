# 16 — Agree "done" up front

> Before a consultant executes, agree on testable success criteria and the return shape. Then the reviewer checks against an agreed target, and the merge is cheap.

A task without a stop condition cycles indefinitely; a fan-out whose pieces don't agree on a
return shape pays for the mismatch twice. The fix is to settle "done" before work starts — a
Sprint Contract of testable acceptance criteria the generator and evaluator both hold, and a
pre-specified return shape so parallel outputs assemble without a costly reconciliation. "Ten
minutes spent agreeing saves an hour later."

**In a harness like this.** A dispatch can carry explicit acceptance criteria, so the reviewer
checks against an agreed target rather than a vague "looks fine" (ties to lesson 06). When the
lead fans out consultants whose results it must combine, pre-specifying what each returns is what
makes the merge cheap (the mechanism behind lesson 12's "merge-cheap"). A misaligned fan-out pays
for itself twice in re-dispatch.

## Where the books say it

- **Harness Engineering** — §08/§17. Agree "done" up front — a Sprint Contract: generator and evaluator agree the definition of "done" before coding.
- **Claude Code: The Complete Guide** — §10/§09b. Define 'done' — a vague goal makes the agent cycle; clear success criteria ("stop when X holds") converge it (supplying the loop's stop condition is the surface that matters here).
- **Codex Complete Guide** — §09. Agree interfaces first, build separately, integrate at the end — the top fan-out failure is interfaces that do not line up, and ten minutes spent agreeing saves an hour.
