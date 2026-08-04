---
name: mg-deep-verify
description: Heavy adversarial verification of an assembled MadGraph simulation-spec — an independent, slice-routed claim panel plus a runtime probe that checks the setup by running it, with bounded revision. Use ONLY when the user explicitly asks for deep verification ("verify deeply", "go deep", "check carefully"). Do not auto-invoke.
---

# `/mg-deep-verify`

Seven stages. Stages 1-5 run per invocation; Stage 6 (re-verify) fires only on a revision and is **capped** (below); Stage 7 (failure-mode extraction) is **off the answer path** — after the answer is composed, on a non-clean cascade only, never blocking.

**Verification prefers acting over reasoning** — where a claim is checkable by running, it goes to the probe (Stage 4); a reasoning-only check confirms "looks right," not "runs right." The probe is the load-bearing lens the reasoning stages scope and aggregate around.

## Dispatch discipline

Every Agent dispatch you make within this skill — Stage 1 (the regime-review dispatch), Stage 2 (the per-claim verifier dispatches), Stage 3, Stage 6, Stage 7, the synthesis-verification step in Stage 5, and any other dispatch the cascade triggers — must include this line **verbatim** in the dispatch prompt:

> **Deep-verify dispatch: wiki and Recent lessons as orientation only; walk source adversarially for THIS input even when a wiki page's scope matches or your MEMORY.md's Recent lessons say you've seen this before.**

This overrides the adopt-a-cached-page discipline on the dispatched agent's own card. The cascade is doing the verification; the dispatched agent must not shortcut via cached wiki content or cached lessons. Each stage's dispatch instructions below repeat the cue at the point of action — do not omit it.

**You apply the same self-discipline.** When you are running this cascade, your own lead-memory's Recent lessons and playbook references are orientation only — usable to route and prioritise, not citable as verified evidence in the synthesis. Source-walk via consultant dispatches (carrying the line above) for THIS input.

When Stage 4 invokes `/mg-probe`, attach the same line to the `ma-probe` dispatch the skill makes on your behalf. The `/mg-probe` skill is callable outside the cascade (where this discipline does not apply); the mg-deep-verify line is your channel for opting that dispatch into adversarial mode.

## Stage 1 — Regime classification and review

Carry forward the regime classification the lead produced when routing this task (per *Classify the regime before routing* in lead-discipline). If none was recorded, dispatch `ma-physics-consultant` to classify fresh.

Then review it adversarially: dispatch `ma-physics-reviewer` to challenge the classification for THIS input — is the regime right, are the implicated slices the correct ones, are the named approximations valid here? The dispatch prompt ends with the **mg-deep-verify line**. A NEEDS REVISION corrects the classification before any later stage builds on it; a WARNING flows into Stage 5 reconcile. The review comes first because every later stage depends on the regime: Stage 2 uses it to focus adoption review, Stage 3 to focus the blind-spot scan, and Stage 4's probe expectations are derived from it. The regime is the foundation the cascade builds on and has no downstream backstop, so under explicit deep-verify the challenge always fires — difficulty-gating the verification belongs to the lighter tiers, not the maximum-certainty tool.

The classification names which slices the input's physics implicates (off-shell propagator → `bw-window`; NLO process spec → `nlo-syntax`; EFT regime → `ma-eft-consultant`; …).

## Stage 2 — Per-claim verification (adversarial)

Consultant Implications bullets are already atomic, originate from a single slice, carry the support-chain label (DIRECT / INFERRED / HYPOTHESIS), and often cite file:line — so they hand you the claim list, owning-slice routing, and source-quoted status with no separate atomization pass. Route each claim directly. When a return is unlabeled monolithic prose or its labels look wrong, re-dispatch the owning consultant for the properly-labeled return its card mandates, or atomize it inline yourself before routing — do not treat unlabeled prose as a labeled claim list.

Route each claim to its verifier by `kind`:

| Claim kind | Verifier | Why |
|---|---|---|
| `slice-internal-fact` | The `owning_slice` consultant — re-dispatched in verify-mode with the specific claims to confirm against source | Slice experts know their MadGraph mechanics; layer reviewers do not |
| `cross-claim-synthesis` | The layer-reviewer matching the synthesis layer (numerics / math / physics) | The synthesis quality (does the conclusion follow from the cited facts) is a layer-check, not a slice-check |
| `numerical` | `ma-numerics-reviewer` — recomputes via `python` | |
| `mathematical` | `ma-math-reviewer` — symbolic; sympy when non-trivial | |
| `physics` (regime / framework / approximation soundness) | `ma-physics-reviewer` — first-principles + literature | |
| `runtime` | Defer to Stage 4 (`ma-probe`) — runtime claims are what the probe is for. Stage 2 records them and Stage 4 verifies. | |

`source_quoted: true` slice-internal-fact claims skip Stage 2 verification (the consultant cited file:line; the citation is the evidence). All other claims go through Stage 2.

When a claim has more than one plausible owning slice — you cannot name a single slice that clearly owns it — dispatch all the plausible owners, not just your best guess. The owner you would have skipped is exactly the one whose answer you are missing. Agreement among the returns confirms the claim; disagreement is a finding for Stage 5.

**Batch by verifier, not by layer.** One dispatch per verifier covers all claims routed to it. Consultants typically receive 1-5 claims; reviewers typically receive 0-3 claims (most spec content is slice-internal). Verifiers fire in parallel.

**Verifier dispatch shape:**

- **Consultants** (verify-mode): dispatch with the per-claim list and instruction *"Verify each of these claims against MadGraph source for THIS input. For each claim: APPROVED (source citation matches) / NEEDS REVISION (claim is wrong, or its premise is incorrect so the derived conclusion does not stand; cite the correct content) / WARNING (you cannot adjudicate from source — the claim turns on a convention or an input you cannot verify here; name what must resolve it)."* The consultant remains the slice expert; this is the same kind of source walk it does on its primary dispatch, applied adversarially. Dispatch **clean** (fresh context), never continuing the authoring dispatch — the verify pass must carry none of the authoring run's self-persuasion; for a same-card check, the fresh context is its only independence.
- **Reviewers** (numerics / math / physics): dispatch with the per-claim list of cross-claim-synthesis or layer-specific claims. *"Mark out-of-slice content as premises in the dispatch prompt"* — slice-boundary discipline applies.

Each verifier returns **APPROVED / NEEDS REVISION / WARNING** per claim.

Every verifier dispatch in Stage 2 ends with the **mg-deep-verify line** verbatim.

## Stage 3 — Blind-spot scan + dispatched walks

Dispatch `ma-blind-spot-auditor` with: the assembled artefact, the question, Stage 1's regime classification, and a per-consultant summary of returns (one paragraph each: what was walked, what was concluded). Dispatch prompt ends with the **mg-deep-verify line**.

The auditor is a **triage scanner, not a walker.** It returns a structured list — each item names an unwalked region, the recommended consultant, and a one-sentence rationale. No source walks, no facts, no judgement.

For each flagged blind spot, dispatch the recommended consultant with the auditor's pointer and the question. The consultant walks source for this input per its card discipline, returns facts + implications, and updates its wiki if durable.

The auditor pass is **unconditional** — always dispatch it. Empty flag-list is a valid outcome.

Findings from dispatched consultants enter Stage 5 alongside the original trail. They are not re-routed through Stage 2; Stage 5's synthesis verification and Stage 6's re-verify cycle catch problems that emerge during reconcile.

## Stage 4 — MadGraph probe (adversarial, expectation-driven)

Invoke the `/mg-probe` skill with the assembled commands, the question, the consultant returns, and an expectation list. The list must carry at least one **target-derived** expectation — what a correct setup for the question produces (expected signal topology / diagram count, order-of-magnitude σ, non-zero-ness in the allowed region), taken from Stage 1's physics regime classification and computed independently of the assembled spec — alongside any spec-derived expectations. A spec-derived-only list lets a wrong-but-runnable spec pass; the target-derived expectation is what makes it deviate. The skill carries the expectation discipline, the dispatch shape, and the boundary rules (probe ≠ source overrule; absence ≠ correctness).

Findings flow into Stage 5 alongside the streams from Stages 2-3.

## Stage 5 — Reconcile

Findings from four streams:

- **Stage 1** — regime classification (which slices the physics implicates).
- **Stage 2** — per-atomic-claim verdicts (each claim labelled APPROVED / NEEDS REVISION / WARNING by its routed verifier).
- **Stage 3** — dispatched-consultant findings (from blind-spot follow-up walks).
- **Stage 4** — probe deviations (per supplied expectation, per probe-derived expectation).

Cross-reference regime classification against the consultant trail. Regime-implicated slices not in the trail are themselves findings (a routing failure caught in deep mode); engage the missing slice.

Walk every finding. Each gets one verdict:

- **revise** — change the spec value (re-engage the owning consultant in revise-mode). Default action on NEEDS REVISION.
- **re-engage** — dispatch a slice for resolution.
- **dismiss** — with an explicit one-sentence reason.

**A WARNING is never resolved by your own adjudication.** A reviewer's WARNING flags an open question it could not decide — a convention, an ambiguity, an uncheckable input. You may not settle it by applying the reviewer's suggested alternative, and you may not dismiss it as your own call. Route it: **re-engage** the slice that owns the question, or — when the WARNING concerns what the question asks for — re-read the user's request and resolve against that. Only the owning slice's resolution, or the user's explicit request, turns a WARNING into a revise or an APPROVED-equivalent.

No "noted-but-shipped" action. Caveats live in `mg-setup`'s reconciliation step. Every NEEDS REVISION not revised carries a written dismissal reason.

### Synthesis verification (before applying a substantive revision)

Discriminate:

- **Trivial** (skip verification): single reviewer's specific fix; arithmetic correction; parameter change a single consultant explicitly authored. The "synthesis" is verdict routing.
- **Substantive** (verify): revision combines findings from multiple streams; topology change; parameter change with non-trivial physics implications; the conclusion is your interpretation rather than any single stream's verdict.

For substantive syntheses, dispatch the layer-reviewer for the synthesis's layer (typically `ma-physics-reviewer`). The dispatch carries each underlying finding as a marked premise, the synthesis as the claim to verify, the explicit ask *"Verify the synthesis, or propose an alternative that preserves the original spec,"* and the **mg-deep-verify line** verbatim.

If APPROVED: apply the revision; proceed to Stage 6.
If NEEDS REVISION / WARNING / alternative proposed: do not apply; re-enter Stage 5 with the new finding; re-triage.

### Wiki updates

When during reconcile you notice a consultant's wiki claim is contradicted by a Stage 2 / 3 finding for this input, the only mechanism is **`Agent` dispatch to the owning consultant** with an update-mode prompt. The consultant invokes `ma-wiki-write` itself on its own subtree — you do not write or edit consultant pages directly — ever. For lead-side findings (a dispatch-level surprise), invoke `ma-wiki-write` on `.madagents/wiki/lead/` per your wiki discipline; Stage 7's failure-mode extraction is the structured channel for behavioural-mistake candidates.

## Stage 6 — Re-verify on revision (conditional)

**Fires whenever Stage 5 applied a revision.** A revised spec is unverified — the streams that produced findings verified a spec that no longer exists. Before composing the answer, re-enter the cascade with carry-forward:

| Stream | Re-run? | Reason |
|---|---|---|
| Stage 1 — regime | NO | Regime is a property of the input, not the spec. |
| Stage 2 — per-claim | PARTIAL | Re-read the revised spec's claims; verdicts on unchanged claims carry forward; new + changed claims route through Stage 2. |
| Stage 3 — blind-spot | YES | New spec → new code path; the auditor walks the actual artefact. |
| Stage 4 — probe | YES | New commands → new generated tree, cards, parser output; the re-probe **widens** its expectation list to the fix's blast radius — what passed before the revision and what depended on the changed value — not a re-test of the original deviation alone. |

**The re-verify of a fix is independent of the fixer.** A *changed* claim re-routed through Stage 2 is a fix, so re-verify it through a lens that did not make it: the Stage-4 re-probe for a runtime-signature fix, the matching layer-reviewer for a synthesis/physics fix. Re-dispatch the owning slice (clean, adversarial) only for a pure source-mechanics fix no other lens is competent on, not as the default — re-dispatching the maker as the sole check is the fixer signing off on its own fix.

Re-enter Stage 5 with the merged findings (carried-forward verdicts + new findings); re-triage. Stage 6 is **capped at two re-verify cycles**: if a revision is still unsettled after the cap, do not loop again — escape upward (below). Two bounded passes catch a revision that introduces a new issue; a spec that keeps producing revisions past that is a framing problem the loop cannot fix. The carry-forward is what makes each re-verify affordable.

### When the cycle does not converge

When the two-cycle cap is reached, or a revised spec keeps producing new revisions without settling, the issue is not at the parameter level — it is a topology, framing, or physics-spec problem that `mg-deep-verify`'s internal cycle cannot fix. **Escape upward, not by accepting a caveat.** Hand back to `mg-setup` with: the persistent finding, the revisions tried, and an explicit ask to re-engage at the spec-construction level. The escape is structural, not a deadline.

## Stage 7 — Failure-mode extraction (off the answer path)

Failure-mode extraction is **learning, not answer verification** — so it runs **after the answer is composed and handed back** (see *After mg-deep-verify*), never before, never blocking it, and **only on a non-clean cascade** (a revision was applied, or a finding was flagged / dismissed-with-reason). A fully clean cascade skips Stage 7 — a run with no real mistake tends to manufacture junk lessons. It is best-effort: if it fails, the answer still shipped.

When it fires, dispatch `ma-failure-mode-extractor` with the cascade trail (regime, consultant trail summary, per-claim verdicts from Stage 2, blind-spot findings, probe deviations, Stage 5 reconcile decisions, Stage 6 cycles if any). Dispatch prompt ends with the **mg-deep-verify line**. The extractor returns a structured list of candidates — agent-system mistakes the cascade surfaced. One occurrence is enough; no recurrence gate.

For deliberate, fuller hardening from this run's evidence, the user can invoke **`/ma-reflect`** on the run. Stage 7 is the lightweight in-cascade capture; `/ma-reflect` is the deliberate channel.

A candidate names: the owner (a consultant, or `lead`), the behavioural mistake, the trigger condition, the correct behaviour, the cascade evidence, and a recommendation (ADD a new page / UPDATE an existing page / DEFER).

For each candidate:

- **Owner is a consultant** → dispatch the consultant in update-mode with the candidate fields; the consultant invokes `ma-wiki-write` to write a page in its own subtree with a description naming the recurring mistake (single-writer-per-page; the lead never writes the consultant's page).
- **Owner is the lead** → the lead invokes `ma-wiki-write` itself on `lead/` with a description naming the dispatch-level mistake.
- **DEFER** → record nothing; the candidate was not durable enough.

The extraction step does not change the simulation-spec and does not produce caveats. A non-clean cascade typically yields 0-2 candidates. Over-recording is the failure mode of this stage itself — the non-clean gate above is the first guard, and the discipline against it lives in the extractor's card.

This stage is the wiki-side counterpart to the spec-side reconciliation: Stage 5 fixes the answer; Stage 7 records the lesson so future sessions of the same agent do not need the same fix.

## After mg-deep-verify

Hand back to `mg-setup`'s reconciliation step (or to the user directly if `mg-deep-verify` was invoked post-shipping) with the simulation-spec, the verified findings, and any caveats from dismissed-with-reason findings. Caveats are surfaced; defects shipped without resolution are not.

On a non-clean cascade, Stage 7 runs **after** this handback — off the answer path, best-effort — so the answer is never delayed by lesson capture.
