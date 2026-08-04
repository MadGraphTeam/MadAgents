---
description: RunCardNLO (banner.py) — NLO run_card defaults, ickkw allowed values (0/3/4/-1), FxFx auto-corrections, matching auto-detection, and check_validity guards.
---

# `RunCardNLO` — NLO run-card section

`$MADGRAPH_INSTALL/madgraph/various/banner.py`, `class RunCardNLO(RunCard)` (line 5594). `LO=False`. `default_run_card = internal/default_run_card_nlo.dat`. `blocks = [heavy_ion_block, running_block_nlo]`.

## `input/default_run_card_nlo.dat`
Contains ONLY commented-out override examples (no active params). All real defaults come from `default_setup`. The convention is `value = name` lines; uncommenting overrides the default when `output` generates the per-process run_card. (Verified: file has zero non-comment lines.)

## Selected params (`default_setup`, params span ~banner.py:5615-5759 — read each default fresh at its line)
Active NLO defaults live in `RunCardNLO.default_setup` (class at 5594). Cache the inventory + coordinate, NOT the numbers — they drift across versions; a stale value reads exactly as valid as the current one. Read the default at its `add_param` line when it is load-bearing.
- Integration/normalization: `nevents`, `req_acc`, `req_acc_fo`, `event_norm` (~5615-5626; the FO-vs-event `req_acc` split — different params, different defaults — is [[integration-driver-mint-loop]]).
- Beams: `lpp1/lpp2` (shortcuts p/p~/e-/e+/mu-/mu+ → 1/-1/3/-3/4/-4, a version-stable enum), `ebeam1/ebeam2`, `pdlabel`, `lhaid`.
- Shower/scale: `parton_shower` (fortran_name `shower_mc`, class default is a mode label — [[parton-shower-param-and-mcatnlo-linkage]]), `shower_scale_factor`, `mcatnlo_delta` (bool), `dynamical_scale_choice` (default list; allowed enum `[-2,-1,0,1,2,3,10]`, shortcuts ht/2→3, ht→2, et→1 — [[nlo-scale-params]]), `fixed_ren_scale/fixed_fac_scale` (bool), `fixed_extra_scale` (system).
- Cuts (5715-5759): `maxjetflavor` (hidden), `jetalgo/jetradius/ptj/ptl/mll_sf/ptgmin`, `gamma_is_j`, `lepphreco/quarkphreco` — full cut inventory + IR-safety in [[nlo-cut-block-and-ir-safety]].
- `bwcutoff`; `folding` (must be exactly 3 ints, each in the allowed set {1,2,4,8}).

## Systematics / uncertainty defaults (NLO ≠ LO — non-obvious)
- **`systematics_program 'none'`** (line 5702, include=False, hidden) — at NLO this defaults to `'none'`, whereas the LO `RunCard` defaults it to `'systematics'` (line 4427). Consequence: the `systematics <run>` step in `run_generate_events` (gated on `systematics_program=='systematics'`, run_generate_events:1860) does **NOT fire by default at NLO**. The comment even narrows the choices to "none, systematics" (no syscalc).
- The NLO scale/PDF uncertainty path is instead the **built-in reweighting**: `rw_rscale=[1.0,2.0,0.5]` (scalevarR), `rw_fscale=[1.0,2.0,0.5]` (scalevarF), `reweight_pdf=[False]` (lpdfvar), `store_rwgt_info False`, `pdf_set_min 244601`/`pdf_set_max 244700` (hidden) (lines 5696-5703). Whether the reweight branch in `reweight_and_collect_events` runs is gated by `reweight_scale`/`reweight_PDF`/multi-scale/multi-lhaid/`store_rwgt_info` (see [[print-summary-and-event-assembly]]) — NOT by `systematics_program`.

## ickkw (merging) — line 5712
`add_param('ickkw', 0, allowed=[-1,0,3,4], ...)`:
- `0` = no merging.
- `3` = FxFx merging (amcatnlo.cern.ch/FxFx_merging.htm).
- `4` = UNLOPS (NO interface within MG5aMC).
- `-1` = NNLL+NLO jet-veto (arXiv:1412.8408).

## FxFx auto-corrections (check_validity, line 5798) — stage 2 of [[fxfx-ickkw3-lifecycle]]
When `ickkw==3` (probe-verified: see lifecycle page):
1. `fixed_ren_scale`, `fixed_fac_scale`, `fixed_QES_scale` forced to False (warn "$MG:BOLD").
2. `dynamical_scale_choice` forced to `[-1]` if not already (and `reweight_scale` truncated to first element).
3. `jetradius` and `jetalgo` forced to `1.0` (kT algorithm, R=1.0; info "$MG:BOLD").

When `ickkw==-1` (jet veto): `dynamical_scale_choice` forced to `[-1]` (scale = ptj), reweight_scale truncated.

## Matching auto-detection (create_default_for_process, line 6029)
- maxjetflavor auto-set from beam ids (line 6047, `max(4, |beam quark ids|)`).
- e+e-/mu+mu- beams → `lpp1=lpp2=0`, `ebeam=500` (line 6050).
- tagged photon → `gamma_is_j=False`; no QED splitting → `gamma_is_j=False`, lepphreco=quarkphreco=False (6084).
- **Multi-multiplicity all-jet difference → matching=True (line 6116): sets `ickkw=3`, all fixed scales False, `jetalgo=jetradius=1`, AND `parton_shower='PYTHIA8'`.** This silently switches the default shower from HERWIG6 to PYTHIA8 for FxFx-eligible processes.
- `default_run_card_nlo.dat` is `read()` LAST (line 6127), overriding the above with any uncommented user defaults.

## Other check_validity guards (line 5761)
- DIS (one lepton + one hadron beam) "not supported at NLO" (5777).
- lepton-lepton: ignores pdlabel/lhaid (forces nn23nlo) unless dressed-lepton (lpp=±3/±4).
- `pineappl` requires lhapdf + reweight_scale (5828).
- `reweight_pdf` requires pdlabel=='lhapdf' (5862).
- `mcatnlo_delta` (bool default at 5670) requires parton_shower=='pythia8' (case-insensitive), else `InvalidRunCard("MC@NLO-DELTA only possible with matching to Pythia8")` (5934-5935). **The ONLY source-enforced guard is the pythia8 requirement** — there is NO Pythia8-version check anywhere in MG5 source (grep of madgraph/+Template = only 5670/5934 + run-interface consumers 4783/5242, no version literal). A minimum-Pythia8-version requirement for MC@NLO-Δ is an external/physics constraint, NOT something MG5 validates. Card display name is `MCatNLO_DELTA` (Template/NLO/Cards/run_card.dat:97, cites arXiv:2002.12716).
- `folding` (include=False, 5706; read default in default_setup) must be exactly 3 integers, each in the allowed set {1,2,4,8} (5928-5932). **The three entries are source-documented (run_card template comment, Template/NLO/Cards/run_card.dat:220) as "folding in xi_i, y_ij, and phi_i"** — the FKS integration variables; higher values reduce the negative-weight fraction at linear CPU cost. Caps: lhaid, dynamical_scale_choice length, rw_rscale/rw_fscale length (all bounded at 5900 — read the cap literals). `1.0` must be in rw_rscale/rw_fscale (auto-inserted, 5909).
- ebeam<0.938 for proton beams → at-rest (0.938) if 0, else error (5954).

## Runtime ickkw guards (NOT this slice's layer — see [[fxfx-ickkw3-lifecycle]])
The FxFx/jet-veto guards that fire at run-launch live in the run interface (`ask_run_configuration:5894-5915`), not banner.py. They are stage 3 of the FxFx lifecycle and are documented in full in [[ask-run-configuration-mode-resolution]] and the [[fxfx-ickkw3-lifecycle]] routing map. This page (banner.py) owns the card-write-time effects only: the `check_validity` auto-corrections (above, stage 2) and `create_default_for_process` auto-detect (stage 1). Do not cite this page for run-launch guards.

## Cautions
- FxFx auto-corrections OVERWRITE user-set fixed-scale / jet params silently (warning only). A user setting `fixed_ren_scale=True` with `ickkw=3` will have it reverted.
- The matching auto-detect (6116) flips the default `parton_shower` to PYTHIA8 only when min/max multiplicities differ AND all extra legs are jets — single-multiplicity NLO keeps HERWIG6 default. Verify the actual run_card, not the class default, before claiming the shower.
