---
name: ma-reflect
description: Harden the agent system against past mistakes — point it at evidence of a failure (`/ma-reflect <previous runs | good and bad example pairs | a recurring mistake you describe>`) and it tightens its own behaviour so the mistake does not recur. The lead reads the evidence as a whole, abstracts the failures to general mechanisms, and installs a behavioural discipline for each — on the lead, the owning consultants, the runtime probe, or a combination — in whatever form fits (a sharpened operating principle, a check, a routing refinement, a wiki page, a new skill, and so on). Every discipline must change behaviour rather than restate what the surface already carries, is scoped to the condition under which it fires, and is confirmed real before it is written. User-invoked, not auto-invoked.
---

# `/ma-reflect [evidence]`

`/ma-reflect` is a self-hardening skill: point it at evidence of a past mistake and it tightens the agent system's own behaviour so the same mistake does not recur. Invoke it deliberately, with a reference to the evidence — previous runs, good and bad example pairs, a documented trap, or a recurring mistake you describe. It is not auto-invoked.

## What it writes — a hardening, gated

For each failure the lead installs a **hardening** in whatever form fits: a sharpened operating principle, an explicit check, a routing refinement, a wiki page, a new skill, and so on. One gate governs all of them:

- **Change behaviour, don't restate.** A hardening that repeats a principle the surface already carries is inert — the agent already had it and the failure still happened. Before writing, confirm the surface does not already say it; if it does, the fix is to change *who owns it, when it fires, or what trace it leaves*, not to say it again. A hardening earns its place by being owned at the step where the failure happens and by leaving an artifact a later check can see.
- **Record what worked, not only what failed.** When the evidence includes an approach confirmed correct for THIS input — a good example, a path validated against source or probe — record the approved approach as a positive discipline or lesson, not only the failure it is paired against. A learned tier that holds only pitfalls pushes the system toward over-caution; the confirmations are what tell it which paths are safe to take again.

## Don't harden — durable disciplines only

A real, reproduced failure is not automatically a durable discipline. Three classes are surfaced to the user and **not** written as permanent disciplines, because the cause is not a durable property of the work:

- **Environment / instance state** — a missing binary, an unset path or credential, a transient tool error. The state of this machine or run, not a rule of the task.
- **A "tool/feature is broken" claim** — hardening it installs a standing refusal the system will cite against itself long after the real (often environmental) cause is fixed.
- **One-off specifics** — a single run's exact value, name, or error string; a one-time identifier. Re-derived when needed, not memorised.

Criterion: if the rule would only hold on this one run, machine, or input, it is not durable — flag it and move on. This gate is separate from *validate before writing*: a failure can be real and reproducible and still fail it.

## Orchestration — global abstraction, then fan-out

The dispatch shape: each owning consultant works its own subtree in parallel, the lead runs its own pass, then aggregate. One step comes before any of that — a **global pass first** — because the mechanisms that matter are cross-slice: one root mistake surfaces across several slices, so no single consultant sees the whole pattern. The lead reads the evidence as a whole before any fan-out.

1. **Ingest.** Read the referenced evidence.
2. **Abstract (lead).** Cluster the failures by mechanism, surface stripped: a model-specific name guessed from memory, a default left unexamined, an unparenthesised decay chain — each is one mechanism, however many times or ways it showed up. Pitch each at the level that changes behaviour and transfers across inputs; keep it as a general discipline only when the mechanism would fire on other models and regimes, judged on its nature, not on how often it appears in the evidence.
3. **Classify the owning layer** — lead, consultant(s), the probe (for a probe-method failure), or a combination — for each mechanism.
4. **Install.** Dispatch each owning agent (a consultant, or the probe) to harden its own MEMORY.md / wiki (single-writer); the lead hardens its own behaviour (lead-memory, a `lead/` routing page, a refined consultant `description`, a new skill). A mechanism touches only the layer(s) it belongs to.
5. **Validate** (below) before each write.
6. **Consolidate.** Installing adds; pair it with pruning so the learned tier does not only grow. As each owner writes (via `ma-wiki-write`), it supersedes any prior entry the new one replaces in-place, merges pages whose scope now overlaps, and demotes slate entries pushed past their budget. A hardening that supersedes an old one leaves one current entry, not two — proliferation and apoptosis run in the same pass.
7. **Verify placement.** A consultant slate is auto-loaded only from `.claude/agent-memory/<name>/MEMORY.md`, the lead's only from `.claude/lead-memory/MEMORY.md`; a slate written anywhere under `.madagents/wiki/` is never loaded and is silently inert. After writing, audit: `find .madagents/wiki -name MEMORY.md ! -empty` returns nothing, and each agent hardened this run has a non-empty slate at its auto-load path. Move any stranded slate to the auto-load path (or delete it if that copy is current) and re-dispatch the owning agent to write there.

## Validate before writing

Write a hardening only once the mistake behind it is confirmed real — take the cheapest sufficient path to that confidence:

- the evidence already demonstrates it (a reproduced error, a failure shown directly) → write;
- a quick reproduction would settle it → run a cheap `/mg-probe` (quick parse-time checks and small local launches run inline; a long launch waits for a go-ahead);
- it cannot be confirmed cheaply → ask, or flag it as a candidate and move on.

A behaviour-changing discipline is never written on a guess.

## Efficiency — scoped, not blanket

Every hardening names the **condition under which it fires**, so its cost is paid only then — "when the model is non-SM, confirm the particle labels", not "always run a label check". Prefer the cheapest sufficient check, and add one only where the mistake is likely or damaging enough to be worth it. An always-on, check-everything battery is the over-broad form the gate already rejects.

## Boundaries

- Behavioural disciplines, not facts (the specific names and values of one case are re-derived when the discipline runs, not memorised).
- Writes the learned tier — MEMORY.md, wiki, new skills, refined descriptions — not the card bodies or rules.
- Single-writer-per-page; gap-aware (read existing hardenings first; extend or correct, never duplicate); consolidates as it installs — supersede, merge, or demote what this run makes redundant, so the learned tier is pruned as it grows, not only appended.
- A hardening is scoped, validated, and durable, or it is flagged — never written on a guess, on environment / one-off state, or as an always-on check.
