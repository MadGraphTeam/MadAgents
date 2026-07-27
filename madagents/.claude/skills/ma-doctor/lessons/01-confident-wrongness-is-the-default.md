# 01 — Confident wrongness is the default

> The model will not say "I don't know." It returns a plausible, often-stale answer with full confidence.

A general model's default failure is not silence but a confident, well-formed, wrong answer.
It does not flag its own doubt; AI-generated output always *sounds* reasonable. A user who
trusts the surface ships the error. This is the single observation the whole system is built
around — the reason a lead must not answer domain claims from recall.

## In a harness like this

This is the system's entire reason to exist. The lead is forbidden from answering domain claims
because pretrained recall is unreliable, and routes to source-grounded specialists instead. The
stable-source lens sharpens it: the *model's recall* is the unreliable thing, while the released,
versioned, byte-static source it grounds against is not — so the fix (lesson 02) is reliable in a
way the books' fast-changing-application-code setting is not. When auditing a harness, treat any
agent or rule that lets recall stand in for a source-checkable fact as the first thing to flag.

## Where the books say it

- **CC-Guide** — §09b (on confident wrongness), App E glossary. Its central principle: the model does not volunteer uncertainty, and instead returns a plausible, often-stale answer with full confidence.
- **Codex** — §09. Generated code always reads as reasonable and never flags its own doubt, so the skill that matters is judging the output, not writing the prompt.
- **Src-Analysis** — ch3/ch11. The #1 failure is confident guessing; the fix is to patch known model weaknesses with targeted rules (the internal stricter prompt reveals the ideal).
- **Hermes** — §08. Wrapping a deterministic task in a probabilistic model buys cost, latency and hallucination rather than intelligence. The engineering face: a model asked to recite drifts.
