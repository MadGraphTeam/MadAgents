---
name: mg-setup
description: '''Set up MG5_aMC for a physics request end-to-end — the default path for any task that builds or configures a MadGraph process or run. Use whenever the deliverable is an MG5 setup: the process line, model, parameters, cuts, scales, LO/NLO mode, decay chains, EFT orders, and so on. Frames the request, classifies the physics regime (which surface keywords routinely under-specify), builds the candidate via consultant dispatches, and reconciles against the physics-spec. Skip only for a pure source-mechanics lookup (dispatch the consultant directly) or a quick factual answer.'''
---

# `/mg-setup`

The setup workflow — the four-step sequence for building a MadGraph configuration. The orchestration disciplines it leans on are already in your context, not restated here: dual-spec, regime classification, slice-boundary premises, whole-spec reconciliation, revise-before-caveat, and "a clean run is not evidence" all live in `lead-discipline.md`. This skill is the setup-specific scaffold over them.

**Step 1 — Frame the physics-spec.** Capture the user's prompt verbatim (dual-spec discipline). If too vague to act, surface and ask.

**Step 2 — Classify the regime.** Classify the physics regime (regime-classification discipline) and route to the slices each regime implicates — sub-threshold parent → `ma-bw-window-consultant`; NLO bracket syntax → `ma-nlo-syntax-consultant`; EFT operators → `ma-eft-consultant`; and so on.

**Step 3 — Build the candidate.** Translate physics-spec + regime classification into a candidate MadGraph configuration. Dispatch the slices the regime named plus any others your reading requires; consultants author within slice, you conduct, iterate as returns reveal what's next.

The simulation-spec is what the configured artifacts *do*, not what you meant them to do, and this is exactly where the two silently diverge. A model name does not fix its vertices, a restriction card silently prunes couplings, a chain drops a sub-decay the parentheses never bound — each artifact is opaque until its owning slice reads it. So build every load-bearing choice on what the artifact actually carries, read by its owner, in **both directions**: a contribution the physics needs can be silently absent (a dead process, a removed coupling), and one you never intended silently present (a contaminating topology, an extra coupling). On a don't-run setup both are invisible until something is read.

The build is not done until each load-bearing choice is grounded in what its artifact does — never its name — and the candidate is coherent across stages.

**Step 4 — Reconcile and present.** Compare the assembled simulation-spec against the physics-spec, then ship.

- **Per-requirement.** Verify each physics-spec requirement is satisfied by the assembled simulation-spec, given everything else now in it. A DIRECT-cited value carries its own evidence; re-dispatch the owning slice only to *Establish* a load-bearing value that shipped non-DIRECT.
- **Whole-spec.** An assembly of individually-correct slice outputs can still be globally wrong — a dead process, a form that computes a different observable, a contaminating topology, a silently dropped coupling. Confirm the emergent cross-slice invariants with a lens that did not build them:
  - **Trivial invariants** (BR ≤ 1 arithmetic, a count, a sign) you check yourself — no dispatch.
  - **Runtime realization** — invoke `/mg-probe` on the assembled commands with a **target-derived** expectation list (per `/mg-probe`), drawn from Step 2's regime classification; re-dispatch `ma-physics-consultant` for the target-state only if that classification is not specific enough. The probe is the independent lens — it acts (reads the generated artifacts), where the build did not; its card carries the cheap-vs-launch discipline.
- **Reconcile.** A deviation from a target-derived expectation is a finding: revise via the owning slice (revise-before-caveat). A revision does not close the finding — re-verify a substantive fix (per *Re-verify a fix* in lead-discipline): re-probe **once** against the revised artifact, the expectation list widened to the fix's blast radius (the deviated expectation plus the ones that passed before the fix); a trivial source-cited fix clears by inspection. **Risk gate:** if after this a load-bearing part of the spec remains unestablished — a finding that will not settle, a substantive fix the re-probe could not clear, a non-DIRECT load-bearing claim you could not establish, or an invariant the source cannot settle — do not bury it in a caveat: surface it prominently and **recommend `/mg-deep-verify`**, leaving the call to the user. Do not loop here, and do not auto-invoke the cascade. The gate is tight — a clean build settles and never trips it.

This raises the default path to one independent lens; it is not full verification — a high-stakes result still wants `/mg-deep-verify`. Then ship per the revise-before-caveat discipline.
