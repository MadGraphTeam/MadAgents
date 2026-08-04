---
description: FxFx (ickkw==3) is enforced/repaired at five lifecycle stages across banner.py and the run interface, each with a different reaction (silent repair / hard reject / warn / y-n prompt).
---

# FxFx (`ickkw==3`) enforcement lifecycle — five stages

`ickkw=3` does NOT have one point of effect. MG5_aMC checks and repairs FxFx consistency at **five distinct lifecycle stages**, each owned by a different code layer and each reacting differently (silent auto-repair, hard reject, warn-and-continue, or interactive y/n). To answer "what does FxFx do to X" or "will my FxFx run", find the stage whose guard fires — the *same* condition (e.g. `ickkw==3` + non-PYTHIA8) produces a *different* effect at different stages.

This page is the routing map. The ickkw enumeration / defaults live in [[runcardnlo-defaults-and-ickkw]]; the launch-time guard detail in [[ask-run-configuration-mode-resolution]]; the run/shower invocation in [[runtime-shell-commands]]. Physics of FxFx merging itself is the **matching slice** (out of scope here).

## Stage 1 — card *creation* (auto-detect): `RunCardNLO.create_default_for_process`
`$MADGRAPH_INSTALL/madgraph/various/banner.py:6116-6123`. When `output` builds the per-process run_card and the process set is multi-multiplicity AND every extra leg is a jet (id ∈ ±{1,2,3,4,5},21 — loop 6090-6114), `matching=True` → sets `ickkw=3`, `fixed_ren/fixed_fac/fixed_QES_scale=False`, `jetalgo=jetradius=1`, **and `parton_shower="PYTHIA8"`** (6123). This is the ONLY stage that flips the shower default from HERWIG6 to PYTHIA8. Effect: silent default-setting. *(Source-confirmed structure; the end-to-end PYTHIA8-switch on a real multi-mult NLO output is probe-pending — not yet probe-verified.)*

## Stage 2 — card *validation/write*: `RunCardNLO.check_validity`
`banner.py:5798-5819`. Whenever `ickkw==3` at card-write: force `fixed_ren_scale/fixed_fac_scale/fixed_QES_scale=False` (5800-5805, warn `$MG:BOLD`); if `dynamical_scale_choice != [-1]` force `[-1]` + truncate `reweight_scale` (5807-5811); force `jetalgo` and `jetradius` to `1.0` (5814-5818, info). Effect: **silent auto-repair** of user-set values (warning only). Does NOT touch `parton_shower` (that is stage-1-only). **Probe-verified** (RunCardNLO with ickkw=3, fixed_ren=True, jetalgo=-1, R=0.4, dyn=[3] → after check_validity: fixed_ren=False, fixed_fac=False, jetalgo=1.0, jetradius=1.0, dyn=[-1]).

## Stage 3 — run *launch*: `aMCatNLOCmd.ask_run_configuration`
`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py:5894-5912`. After run_card is charged, before integration:
- `ickkw==3` + `mode ∈ {LO, aMC@LO, noshowerLO}` → `InvalidCmd("FxFx merging (ickkw=3) not allowed at LO")` (hard reject, 5894-5895).
- `ickkw==3` + ((`aMC@NLO` & parton_shower≠PYTHIA8) or `noshower`) → by-hand-removal warning (5897-5900), then: `PYTHIA6Q` → `InvalidCmd` (5903, hard reject); shower not in {HERWIG6,PYTHIA8,HERWIGPP} → **interactive y/n** "FxFx merging not tested for X shower" (5904-5911; `n` recurses ask_run_configuration, the raise is commented out).

## Stage 4 — event *generation* (post-warn): `aMCatNLOCmd.run_generate_events`
`amcatnlo_run_interface.py:1879-1882`. `ickkw==3` + (`noshower` or (parton_shower≠PYTHIA8 & `aMC@NLO`)) → SAME by-hand-removal warning as stage 3, but fired again later (after run() has started). Effect: warn-only, no reject. This duplicates stage 3's warning text at a different time — a question about *when* the warning appears must distinguish 5897 (launch) from 1879 (generation).

## Stage 5 — *shower*: `aMCatNLOCmd.run_mcatnlo`
`amcatnlo_run_interface.py:4017-4026`. `shower=='PYTHIA8'` & `ickkw==3` → reads `MCatNLO/Scripts/JetMatching.h` (f1) and `<pythia8_path>/include/Pythia8Plugins/JetMatching.h` (f2). If f2 missing → `Exception("FxFx requires a dedicated plugin... ")` (4023); if `f1 != f2` (byte mismatch) → `Exception("...Incorrect plugin detected")` (4026). Effect: **hard Exception at shower time**, and it is a *byte-for-byte file comparison*, not mere existence. (A leftover `misc.sprint(pythia8_path)` debug print sits at 4019.) *(Source-confirmed; not probe-verified end-to-end — needs an installed PY8 + FxFx output.)*

## Why this matters (routing symptoms → stage)
- "my `fixed_ren_scale=True` reverted" → stage 2.
- "default shower became PYTHIA8" → stage 1 (auto-detect only; single-mult NLO keeps HERWIG6).
- "FxFx won't launch at LO" → stage 3 (`InvalidCmd`).
- "Exception at shower: FxFx requires a dedicated plugin" → stage 5 (4018 byte-match).
- "by-hand-removal warning appeared twice" → stages 3 and 4 fire the same text at different times.

## No applicability guard (pure-QCD multijet)
There is **no code guard** anywhere in `amcatnlo_run_interface.py`/`banner.py` enforcing the physics rule "FxFx needs a non-QCD hard scale, so it is not applicable to pure-QCD multijet" (grep for `hard.scale`/`pure.qcd`/`non.qcd` → 0 relevant hits). The opposite: the stage-1 auto-detect (`create_default_for_process`, banner.py:6110-6123) triggers `matching=True` for *any* all-jet multi-multiplicity difference — so a pure-QCD `p p > j j [QCD] @0` + `add p p > j j j [QCD] @1` would silently get `ickkw=3`, `parton_shower=PYTHIA8`, fixed scales off. The methodological non-applicability is a **physics claim (route to physics / matching slice), not something MG5 rejects.**

## Sibling: `ickkw==-1` (NNLL+NLO jet veto)
Fewer stages: card-validation `banner.py:5820-5825` (force `dynamical_scale_choice=[-1]`, scale=ptj) + launch-guard `ask_run_configuration:5913-5915` (`InvalidCmd("NNLL+NLO jet veto runs (ickkw=-1) only possible for fNLO or LO")` for aMC@NLO/noshower). No auto-shower-switch, no shower-time plugin check.

## Caution
The condition `ickkw==3 and non-PYTHIA8` appears verbatim in stages 3 and 4 with DIFFERENT effects (launch-guard with possible reject vs. pure warning). Cite the stage that matches the question's timing; do not conflate "FxFx warns" (which stage?) with "FxFx rejects" (only stages 3 and 5).
