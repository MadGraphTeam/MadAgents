---
description: FxFx / jet-veto execution-side enforcement in the aMC@NLO interface — the ickkw mode-vs-shower validity gates, the Pythia8 JetMatching.h plugin check, the FxFx merged cross-section extraction from the shower log, and the ICKKW/PTJCUT/DELTA shower-control write.
---

# FxFx / jet-veto: aMC@NLO interface execution side

The nlo-ickkw-fxfx page is the run-card auto-corrections (banner.py `check_validity`);
fxfx-unlops-fortran-cut is the generation-time Fortran cut. THIS page is the THIRD
layer: how `ickkw` (3=FxFx, -1=jet-veto) is enforced and consumed at **run/launch
time** by the aMC@NLO interface — the ickkw-gated validity gates inside the launch
flow, the Pythia8 plugin requirement, and the merged-cross-section reporting. The
generic AskRunNLO dialog flow is the amcatnlo slice; the **ickkw-specific branches
within it are matching's**.

All cites `$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`.

## Mode-vs-ickkw validity gates (in the launch path, @5894-5915)
Fired after `set_run_name`, gating the chosen run `mode` against `ickkw`:
- @5894-5895: `ickkw==3 and mode in ['LO','aMC@LO','noshowerLO']` → `raise InvalidCmd("FxFx merging (ickkw=3) not allowed at LO")`. **FxFx is NLO-only; the LO modes abort.**
- @5896-5911: `ickkw==3 and ((mode=='aMC@NLO' and parton_shower != PYTHIA8) or mode=='noshower')` → warn (the "remove events by hand" FxFx caveat), THEN:
  - `parton_shower=='PYTHIA6Q'` → `raise InvalidCmd("FxFx merging does not work with Pythia6's Q-squared ordered showers")`.
  - shower not in {HERWIG6, PYTHIA8, HERWIGPP} → interactive `ask` prompt "FxFx merging not tested for %s shower" default 'n'; 'n' re-asks run configuration.
- @5913-5915: `ickkw==-1 and mode in ['aMC@NLO','noshower']` → `raise InvalidCmd("NNLL+NLO jet veto runs (ickkw=-1) only possible for fNLO or LO")`. **Jet-veto is fNLO/LO-only — the opposite restriction to FxFx.**

A near-duplicate FxFx caveat warning fires earlier @1879-1882 (`ickkw==3` + noshower or non-PY8 aMC@NLO).

## Pythia8 JetMatching.h plugin check (@4017-4026)
When `shower=='PYTHIA8' and ickkw==3`:
- Reads `me_dir/MCatNLO/Scripts/JetMatching.h` (f1) and `pythia8_path/include/Pythia8Plugins/JetMatching.h` (f2).
- @4022-4023: plugin file absent (`if not os.path.exists` @4022) → `raise Exception("FxFx requires a dedicated plugin to be installed in Pythia8")` @4023.
- @4026: `f1 != f2` (byte-mismatch) → `raise Exception("...Incorrect plugin detected")`.
So FxFx+PYTHIA8 demands the exact MadGraph-shipped JetMatching.h be installed in the user's Pythia8 — a content-equality check, not just existence. This is the FxFx analogue of the MLM driver setup; absence/mismatch aborts at launch.

## FxFx merged cross-section extraction (@4394-4425)
After the shower, when `ickkw>0`:
- @4395-4396: `ickkw != 3 or shower != PYTHIA8` → `logger.warning("Merged cross-section not retrieved by MadGraph. Please check the parton-shower log...")`. So the auto-extraction only works for **FxFx + PYTHIA8**; MLM-at-NLO or non-PY8 FxFx leaves the merged xsec un-retrieved (user reads the shower log).
- @4398-4425 (FxFx+PY8): regex-scrapes `mcatnlo_run.log` for the Les Houches `9999` process line, parses `generated/tried/accepted` and `xsec/xerr` (Pythia mb → pb via `*1e9`), stores `cross_pythia`, `nb_event_pythia`, `error_pythia`, `shower_dir` in results, and logs "FxFx Cross-Section: ... %f pb. Number of events after merging: %s". So the **post-merging cross-section and event count come from the Pythia8 log, scraped by MadGraph** — not from the matrix-element integration.

## Shower-control write (ICKKW / PTJCUT / DELTA, @4778-4790)
Into the aMC@NLO shower run-control content:
- @4782: `ICKKW=%s` from `run_card['ickkw']`.
- @4783-4786: `DELTA=ON` if `mcatnlo_delta` else `DELTA=OFF` (see mcatnlo-delta).
- @4787: `PTJCUT=%s` from `run_card['ptj']`. **So `ptj` is propagated to the shower driver as PTJCUT** — the generation-side FxFx merging cut (fxfx-unlops-fortran-cut: ptj is the generation cut) is also handed to the shower control. (The Pythia8-side merging scale itself is the shower-card `Qcut`, see shower-card-qcut.)

## Scale-reporting difference by ickkw (@3342-3349)
In the scale-uncertainty summary: `ickkw != -1` reports "Dynamical_scale_choice <label> (envelope of <size> values)"; `ickkw == -1` (jet-veto) instead reports "Soft and hard scale dependence (added in quadrature)" using `max_q/min_q`. So the jet-veto run gets a quadrature-combined soft/hard scale uncertainty rather than an envelope — consistent with the NNLL+NLO veto computation (arxiv:1412.8408).

## Cautions
- FxFx and jet-veto have OPPOSITE mode restrictions: FxFx is NLO-only (aborts at LO modes @5894), jet-veto is fNLO/LO-only (aborts at aMC@NLO/noshower @5913). Don't conflate.
- FxFx+PYTHIA8 requires the EXACT shipped `JetMatching.h` plugin (content-equality @4026); a Pythia8 with a different-version plugin aborts at launch with "Incorrect plugin detected".
- The merged cross-section is auto-extracted ONLY for FxFx+PYTHIA8; every other ickkw>0 NLO combo logs "not retrieved" and the user must read the shower log.
- All static-source. The regex actually matching the live `mcatnlo_run.log`, the plugin equality holding for a given Pythia8 install, and the verbatim runtime abort/warning text are launch-time — probe-candidates, not asserted here.
