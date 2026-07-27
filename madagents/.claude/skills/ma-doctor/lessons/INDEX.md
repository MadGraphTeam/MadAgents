# Lessons — cross-cutting index

One file per distilled principle, each collecting the books that arrived at it. A principle that
several independent books reach is stronger than any single statement of it, so each lesson
consolidates the principle plus all its sources in one place. Each lesson file carries: the
generalized principle, how it applies in an orchestrator-plus-consultants harness, and the backing
books with section references.

**Book tags:** **Src-Analysis** (Claude-Code-Source-Code-Analysis), **Harness**
(Harness-Engineering), **Hermes** (Hermes-Agent), **Skills** (Agent-Skills), **Loop**
(Loop-Engineering), **CC-Guide** (Claude-Code-The-Complete-Guide), **Codex**, **OpenClaw**,
**Obsidian** (Obsidian-AI), **Polymarket**.

---

## Grounding & honesty
- **[01] Confident wrongness is the default** — the model returns plausible, stale answers with full confidence and won't say "I don't know". · CC-Guide, Codex, Src-Analysis, Hermes
- **[02] Ground every claim in the source** — answer from the source, not from recall; the source is the only ground truth. · Src-Analysis, Harness, CC-Guide, Codex, Hermes, Obsidian, Polymarket
- **[03] Calibration and honesty about limits** — a calibrated, honestly-hedged answer beats a uniformly confident one; state what you can't do. · Polymarket, Src-Analysis, Hermes, Skills
- **[04] Reserve the model for judgment** — decide with a rule or a check what a rule can decide; spend the model only on real judgment. · Hermes, Loop

## Verification & the independent reviewer
- **[05] The maker cannot check itself** — the author can't grade its own work; verification needs a separate, independent agent. · Loop, Harness, Src-Analysis, CC-Guide, Polymarket
- **[06] Running is not being right** — "it ran" is not "it's right"; verify functional correctness against the user's actual ask. · Loop, Harness, CC-Guide, Codex, Src-Analysis
- **[07] Reviewer posture and actionable feedback** — default to doubt, check behavior not intent, and make every finding carry its fix. · Loop, Skills, Harness
- **[08] The evaluator is the floor** — the reviewer decides what the system won't ship; investing in it is what the scaffold buys. · Loop, Polymarket, Harness

## Multi-agent structure
- **[09] Independence makes pooling work** — pooled judgments cancel error only when independent; correlated agents share blind spots. · Polymarket, Loop, Hermes
- **[10] Consensus before high-stakes claims** — a lone claim is a hypothesis; require independent convergence before acting on a high-stakes one. · Polymarket, Hermes
- **[11] Match orchestration to complexity** — don't fire the full cascade on an easy ask; scale effort to difficulty. · Harness, Src-Analysis, Polymarket
- **[12] Do not over-fan-out** — a few clean, independent slices beat a large noisy crowd; over-fanning dilutes the answer. · Skills, CC-Guide, Polymarket, Loop, Hermes
- **[13] Subagents are independent context** — a subagent's real value is its own clean context window, not just specialization. · CC-Guide, OpenClaw, Hermes
- **[39] Narrow specialists beat generalists** — a narrow specialist that owns one slice beats a generalist; domain edge does not transfer. · Polymarket
- **[40] Weight a judge by its track record** — weight a contributor by demonstrated correct outcomes per category, not by activity or volume. · Polymarket

## Dispatch craft
- **[14] Self-contained dispatch** — a consultant sees only what you hand it; carry the full question, the verbatim ask, and paths. · Src-Analysis, Harness, Codex, CC-Guide
- **[15] Dispatch the what, not the how** — give the goal and context, not the method; a presupposed diagnosis is the confident-recall trap. · Harness, CC-Guide, Codex
- **[16] Agree "done" up front** — carry testable acceptance criteria and the return shape into the brief. · Harness, CC-Guide, Codex
- **[17] The lead owns the final voice** — consultants return concise, labeled signal; the lead synthesizes its own answer, never relays raw text. · Src-Analysis, Harness, OpenClaw, Hermes

## The lean context surface
- **[18] Map, not manual** — the always-loaded surface is a thin map of the non-inferable, not an encyclopedia. · Harness, CC-Guide, Src-Analysis, Skills, Codex
- **[19] Guardrails by exclusion** — stating what does NOT exist / what NOT to do (with the escape route) steers cheaply. · Harness, CC-Guide, Hermes
- **[20] The description is the router** — a card's description is both the routing key and a standing token cost paid every request. · Skills, Codex, OpenClaw, Obsidian, Hermes, Src-Analysis
- **[21] Curate the dispatch payload** — more context isn't better; hand the slice, read the rest on demand. · CC-Guide, Codex, OpenClaw

## Memory & the wiki
- **[22] Plain files, not a database** — plain Markdown read directly; at bounded scale no vector DB or RAG is needed. · Src-Analysis, Harness, Obsidian, OpenClaw
- **[23] Memory is an index of pointers** — a description-only index; page bodies are fetched on demand (progressive disclosure). · Src-Analysis, Obsidian, Hermes, Skills, Loop, CC-Guide
- **[24] Compile, don't re-derive** — compile the source once into a kept wiki; later questions read the page, not the source. · Obsidian
- **[25] Source versus derived knowledge** — separate immutable source/identity from mutable learned memory; treat memory as a lead, verify before it hardens. · Obsidian, OpenClaw, Src-Analysis, Harness, Hermes, Skills
- **[26] A written schema, a shallow cross-linked tree** — a schema makes a general agent author consistently; keep the wiki flat and cross-linked. · Obsidian, Skills
- **[41] Record the thesis, not just the verdict** — a recorded answer without its reasoning and conditions is unusable downstream. · Polymarket

## Self-improvement
- **[27] Capture a lesson from every mistake** — one real mistake, one durable rule; record successes too; user frustration is a first-class signal. · Src-Analysis, Harness, Skills, Obsidian, Codex, CC-Guide, Hermes, OpenClaw
- **[28] Know what not to learn** — never harden a transient/env failure or a negative tool claim into durable memory; distill, don't transcribe. · Hermes, Src-Analysis
- **[29] Curate the learned store** — edit before create, name by class, consolidate and prune; the write is its own step, never mid-answer. · Hermes, Src-Analysis

## The human on the loop
- **[30] Keep the human on the loop** — execution can be outsourced, deciding can't; surface choices, keep the human the decider. · Loop, CC-Guide, Hermes, Skills, Polymarket
- **[31] Ask before guessing** — clarify scope and acceptance criteria before non-trivial work. · CC-Guide, Codex, Skills
- **[32] Surface a choice well** — give a reason not just a prompt; 3-4 materially-distinct options with honest weaknesses; aggregate, don't spam. · Skills, Src-Analysis
- **[33] Gate consequential actions** — default to dry-run, gate irreversible actions, skip work whose marginal gain doesn't clear its cost. · Polymarket, Src-Analysis
- **[34] Design degradation paths** — on repeated failure, degrade gracefully (ask the user; fresh agent) rather than spin. · Src-Analysis, Harness

## The scaffold earns its keep
- **[35] Constraints, not model size, are the edge** — reliability comes from the scaffold; pre-build the competence a weak model can't improvise. · Loop, Harness, Polymarket, OpenClaw, CC-Guide
- **[36] Don't add machinery that costs more than it saves** — every layer must save more than it costs; bound runaway spend. · Hermes, Skills, Loop
- **[37] Save as you go, and phase the work** — write durable output incrementally, phase long work, catch drift early; framing sets the ceiling. · Skills, CC-Guide, Codex, Loop, Harness
- **[38] Compose primitives, don't bolt on** — cover new cases by combining existing primitives; gate a card on its preconditions. · Hermes, Skills, Loop, CC-Guide

---

_41 lessons across 9 groups, distilled from ten books on agent engineering. Each is a principle to
keep in mind when auditing a harness; the "in a harness like this" note in each file applies it to an
orchestrator-plus-consultants system, read through an interactive-product and stable-source lens.
Lessons 39-41 trail the numbering but sit under their thematic groups above._

---

## About the sources

The tags above name third-party works consulted while designing this harness. Each lesson states
its principle, and what those works contribute to it, **in this project's own words** — no text
from any of them is reproduced here. The `§`/`ch` markers point back into the source's own
structure for anyone who has it; they are locators, not quotations. Where a lesson names a person
(Fowler, Boeckeler, Buffett) or a system (Ghostty, Metaculus, Stripe Minions), that attribution
belongs to the source that discussed it.

Principles are not owned by whoever wrote them down first. What is recorded here is our reading of
them and how they bind *this* harness; the value is in the convergence, not in any one phrasing.
