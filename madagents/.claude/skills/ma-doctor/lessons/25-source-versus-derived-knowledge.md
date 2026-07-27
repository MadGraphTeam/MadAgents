# 25 — Source versus derived knowledge

> Separate the immutable source (and the agent's identity core) from the mutable learned memory. They get different trust and different handling — and a wrong write to the always-loaded layer propagates silently.

The raw source is the ground truth: append-only, never modified, cited. AI-derived knowledge can
hallucinate, go stale, or misread intent, so it is handled more boldly (it can always be
regenerated) but trusted less (it must trace back to source). Mix them and over time you can't
tell originals from artifacts. The same split applies to the agent itself: an identity/values
core is frozen, while only a separate learned layer accumulates. And the cost of a *wrong* write
to the always-loaded learned layer is high — it hardens into every later turn, rides every
inheriting copy, silently and confidently, because the reader never sees the moment it went wrong.
So a recalled memory is a *lead to verify*, not truth; persist slow-changing facts, retrieve
fast-changing ones.

## In a harness like this

The MadGraph source is the only ground truth (read-only, cited); the wiki / memory is AI-derived
(can be wrong, must trace to source, verified before it hardens). The trust asymmetry *is*
verify-before-harden on the derived layer. The same frozen-vs-mutable split appears as the
lead-immutable card body vs. the lead-writable description, and as the mutable memory/wiki. Because
the learned state is inherited by every system seeded from it, a wrong artifact propagates to all
of them — which is exactly why a memory/wiki write is load-bearing and must be verified. When
auditing, the structural check is whether source and derived knowledge are kept distinguishable
(cited source vs. flagged derivation), and whether anything writes to the always-loaded layer
without a verification step in front of it.

## Where the books say it

- **Obsidian** — §05 P6/§06. Separate human-input/source from AI-output: the raw tier is the source of truth, append-only and never modified; different trust (artifacts can hallucinate) and different handling (derived data can be regenerated).
- **OpenClaw** — §06/§07 (an immutable identity core `SOUL.md` separate from mutable `MEMORY.md`/`USER.md`), §23 (a bad write to always-loaded memory went on to drive malicious operations in every subsequent interaction — the silent, confident, inheritance-riding propagation).
- **Src-Analysis** — ch6. Treat memory as a lead rather than as truth; remember slow-changing facts, retrieve fast-changing ones.
- **Harness** — §10. Persist *discovered* environment facts (discover once, cache) rather than pre-injecting them.
- **Hermes** — §07. Separate user-profile (`USER.md`) from domain notes (`MEMORY.md`) — two files, two budgets.
- **Skills** — ch9 (Integration). Keys and paths come from the environment, never hardcoded, because that is what keeps skills portable (an independent arrival at the same portable-paths discipline this harness already holds).
