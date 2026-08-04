# 11 — Match orchestration to complexity

> Orchestration complexity should match task complexity. Don't fire the full cascade on an easy ask; scale effort to difficulty.

If the lead or one consultant can handle it, don't go multi-agent. Start with the simplest
approach and upgrade only when you actually need to. The mature form is a system that runs a
cheap-fast path for easy asks (answer fast, one consultant, no full cascade) and the deep-slow
path only for hard ones — auto-scaled to difficulty, not a user toggle.

## In a harness like this

A direct caution for a lead plus a full consultant roster: the rich machinery must not fire on
easy asks. This is the orchestration face of token-frugality and the fast-where-it-can /
accuracy-always rule — the cheap path answers the easy thing, the deep path (cascade, deep-verify)
is reserved for the hard one. (Lesson 33 covers the related but distinct question of gating
*consequential* actions; this lesson is about allocating *effort*.)

## Where the books say it

- **Harness** — §17. Orchestration complexity should match task complexity: if one agent can handle it, do not go multi-agent; start with the simplest approach and upgrade only when the need is real.
- **Src-Analysis** — ch5. The system auto-scales effort: a two-stage cheap-then-deep classifier runs a fast path for easy asks and the deep path only for hard ones.
- **Polymarket** — §07. Mature bots run a four-tier intensity system (Normal → Warning → Critical → Max) — graduated effort matched to the situation.
- **Src-Analysis** — coordinator prompt. Orchestrator answers directly, avoid over-delegation — the lead handles what it can (routing, clarification, consultant-choice, synthesis) without delegating; what it can answer excludes domain claims, which route to specialists.
