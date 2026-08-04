# 27 — Capture a lesson from every mistake

> One real mistake, one durable rule. Record successes too. And user frustration is a first-class correction to encode.

Every correction becomes durable state — compound-interest engineering: hit a pitfall once,
record it so you never hit it twice; add one rule at a time, each corresponding to a real pitfall
you actually hit (not a hypothetical). Record validations too, not only corrections, or the agent
turns overly conservative. A self-improving agent should bias *toward* capturing — a session that
yielded a genuine durable lesson and recorded nothing is a miss, not a neutral non-event. And user
displeasure ("too verbose", "just give me the answer", "stop doing X") is a first-class learning
signal — the interactive equivalent of a caught mistake.

## In a harness like this

This is the self-improvement loop: a wrong outcome becomes a durable lesson the next dispatch
loads, and confirmations are recorded too (the record-confirmations discipline). Frustration is the
high-value, interactive-only trigger — the lead treats expressed dissatisfaction as a mistake to
persist, not just a one-turn adjustment. It is most load-bearing while the memory and wiki are
filling in, where active-but-braked capture (lesson 28 is the brake) populates the learned state
the system then ships with. When auditing, the question is whether the harness has a standing path
for a caught mistake (and a confirmed success, and a frustration signal) to land as durable state,
or whether corrections evaporate at end of session.

## Where the books say it

- **Src-Analysis** — ch6. Record successes too, not only corrections (else the agent turns overly conservative).
- **Harness** — §03/§07/§12/§14. Mistake-driven growth — one mistake, one rule; every correction becomes durable state.
- **Skills** — ch6/ch9. Hit a pitfall once, record it in the skill, and let nobody hit it twice.
- **Obsidian** — §04.2/§04.5. The author added a rule to CLAUDE.md after each mistake, and it grew from a few lines into a routing system.
- **Codex** — §05. Every rule should answer a pitfall actually hit rather than a hypothetical, and rules should be added one at a time.
- **CC-Guide** — §05/§10/App G. The start-small, grow-on-mistakes flywheel; keep the file lean, prune periodically.
- **Hermes** — §04. Frustration is a learning signal — a user's displeasure is a first-class correction, encoded immediately; most sessions should yield at least one skill update.
- **OpenClaw** — §09. Self-extension is the self-improvement loop — agents write, reload and test their own extensions at runtime, improving their toolchain continuously; the same gap-to-capability loop the memory, wiki, and promoted skills run.
