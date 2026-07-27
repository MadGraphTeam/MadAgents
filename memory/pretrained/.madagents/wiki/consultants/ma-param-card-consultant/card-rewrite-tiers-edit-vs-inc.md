---
description: Two tiers of operative-card rewrite — edit-time stages are entry-point-gated (skipped by launch -f / scan), inc-time stages fire on every path to integration; same hand-edit, different outcome by launch path.
---

# Card-rewrite tiers: edit-time (entry-point-gated) vs inc-time (always fires)

Generalizes the per-stage pages (override-stages-card-to-fortran, operative-source-chain,
card-editor-update-commands, scan-and-auto-detection, slha1-slha2-conversion,
param-card-validation-rule-engine). Each documents one place the
operative `Cards/param_card.dat` is silently rewritten. The deeper organizing axis they share — and
which none of them states as such — is **where in the run the rewrite lives**, because that determines
**whether the launch path can skip it**.

## The principle

A param-card rewrite belongs to exactly one of two tiers:

- **Edit-time tier — runs behind the interactive edit question, so it is ENTRY-POINT-GATED.**
  Lives in `AskforEditCard` (`common_run_interface.py`). Fires on the interactive `launch` /
  file-answer path; **skipped** when the edit question is bypassed: `launch -f` /
  `generate_events -f` route through `ask_edit_cards(..., mode='auto')` (madevent_interface.py L6804,
  gated `if mode == 'auto'` L6844; the interactive-only branch is `if not self.mode == 'auto'`
  common_run_interface.py L7721) and `scan` cards short-circuit it (`do_update` scan-return L6855-6864).
  Members: auto-`update dependent` at `postcmd` (L6793, call L6804); the dependent mass/width recompute
  (`ParamCard.update_dependent`, check_param_card.py L463); the aS↔PDF sync; the dependent-recompute
  KeyError on a deleted top mass.

- **Inc-time tier — runs inside `do_treatcards → write_inc_file`, so it fires on EVERY path to
  integration** (interactive, `-f`, scan-point, LO and NLO alike). `do_treatcards`
  (madevent_interface.py L3175; aMCatNLO delegates to the same parent, amcatnlo_run_interface.py
  L1712→L1730) always calls `param_card.write_inc_file` (L3265). Members: default-fill of missing
  params (check_param_card.py L678/684); `secure_slha2` slha1↔slha2 auto-conversion (L614/643, can
  overwrite the card on disk); MSSM `convert_to_mg5card → MG5_param.dat` (L3216); fresh-card sentinel
  rounding `9.999999e-1→1` / `0.000001e-99→0` (write_param_card.py L253-256); negative-mass→negative-
  width (check_param_card.py L691-695).

## Why it catches more than the instances

The per-stage pages answer "does stage S rewrite my value?" This page answers the cross-stage question
the instances can't: **"will *this launch command* exercise stage S at all?"** Tier membership predicts:

- A hand-edited dependent mass / aS persists in the card after `launch -f` (edit-tier skipped) but is
  corrected after an interactive `launch` (edit-tier fires). Probe-confirmed (card-editor page): three
  `madevent launch -f` runs on SM `p p > t t~` with `mass 24`=70.0 kept 70.0; no "For consistency …"
  message.
- The SAME deleted line is non-fatal via bare `treatcards param` (inc-tier only, default-fills) but
  fatal via interactive `launch` (edit-tier dependent-recompute KeyErrors first). Probe-confirmed
  (override-stages page): deleting `mass 6` → `KeyError: 'id (6,) is not in mass'` on the launch path,
  silent default-fill on the treatcards path (message `default value: <MT operative default>`, read the
  current MT default from the default card).
- A future consistency check added behind the interactive question inherits edit-tier gating
  automatically; a new check added to `write_inc_file` inherits inc-tier always-fires.

## Boundary — do NOT over-generalize

The inc-time tier is **not** entry-point-dependent. "All card rewrites depend on how you launched" is
the failure mode this page guards against: `secure_slha2`, default-fill, and sentinel rounding fire on
`-f` and scan paths too (they reach `write_inc_file` unconditionally). Only the **edit-time** tier is
gated. When diagnosing "set X, got Y": first classify X's governing stage by tier, THEN ask whether the
launch path was interactive or `-f`/scan — the launch path only matters if the stage is edit-time.

## Relation to the lead's config-value-lifecycle-layers playbook

Same structural family ("written card ≠ enforced value; latest stage governs") but the discriminating
axis here is the **launch entry point**, not just the lifecycle stage. The lead playbook routes across
slices; this page is the param-card-internal refinement: within this slice, the stages further split by
whether the entry point can skip them.
