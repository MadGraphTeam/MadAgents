---
description: NLO matching (RunCardNLO) — ickkw allowed values, FxFx (ickkw=3) and jet-veto (ickkw=-1) auto-corrections, and the NLO auto-detect that turns FxFx on.
---

# NLO matching block (RunCardNLO)

All cites `$MADGRAPH_INSTALL/madgraph/various/banner.py`, class `RunCardNLO` (def @5594).

## ickkw registration (@5712)
`self.add_param('ickkw', 0, allowed=[-1,0,3,4], comment=...)`. Comment enumerates:
- `0`: No merging.
- `3`: FxFx Merging (http://amcatnlo.cern.ch/FxFx_merging.htm).
- `4`: UNLOPS merging — "No interface within MG5aMC" (user does matching outside MadGraph).
- `-1`: NNLL+NLO jet-veto computation, arxiv:1412.8408.

NOTE: NLO card has NO `xqcut`. Confirmed: no `xqcut` registration anywhere in RunCardNLO (5594+). FxFx merging scale is the shower-card `Qcut` (see shower-card-qcut page), not a run-card param.

Related NLO params (read defaults fresh at each cited line in `RunCardNLO`, banner.py — drift-prone): `jetalgo` @5715; `jetradius` @5716; `ptj` @5717; `maxjetflavor` @5736 (hidden).

## FxFx auto-corrections (check_validity, ickkw==3 @5798-5819)
When `ickkw==3`, these run-card choices are OVERRIDDEN (user values silently changed):
- `fixed_ren_scale`, `fixed_fac_scale`, `fixed_QES_scale` @5800-5805: any True → forced `False` with warning "For consistency in FxFx merging, '%s' has been set to false".
- `dynamical_scale_choice` @5807: if not `[-1]` → forced `[-1]`, `reweight_scale` truncated to first element. Warning "...set to -1 (default)".
- `jetradius`, `jetalgo` @5814-5819: if != 1.0 → set to `1.0` (kT algorithm, R=1.0). Info-level log.

## Jet-veto auto-correction (ickkw==-1 @5820-5825)
If `ickkw==-1` and `dynamical_scale_choice` not `[-1]`: forced to `[-1]`, `reweight_scale` truncated. Warning "For consistency with the jet veto, the scale which will be used is ptj. dynamical_scale_choice will be set at -1."

## NLO auto-detect: FxFx turned ON automatically (create_default_for_process @6029)
- @6046-6048: pp/jet beams → `maxjetflavor` set to max beam jet flavor.
- Multi-multiplicity jet detection @6089-6114: same algorithm as LO (min/max-leg differ only by jets in {1..5,21}) → `matching=True`.
- When matching @6116-6123: `ickkw=3`, `fixed_ren_scale=False`, `fixed_fac_scale=False`, `fixed_QES_scale=False`, `jetalgo=1`, `jetradius=1`, `parton_shower="PYTHIA8"`.
- @6127-6128: `self.default_run_card` is read LAST if present, `consistency=False` (can override the above). The path is resolved @5608 to `$MADGRAPH_INSTALL/internal/default_run_card_nlo.dat` — the in-source comment @6125 says "input/..." but the actual `pjoin(MG5DIR,"internal",...)` is `internal/`.

## Cautions
- FxFx (ickkw=3) silently overrides the user's scale choices and jet algorithm. A user who set fixed scales or a non-(-1) dynamical scale will have them changed without an abort — only warnings.
- UNLOPS (ickkw=4) is accepted by `allowed=[-1,0,3,4]` but has no Python merging *driver* (no FxFx-style auto-config, no showered-UNLOPS aMC@NLO flow); the final merging is done outside MadGraph by the user. BUT a generation-side Fortran cut DOES exist (`passcuts_unlops_jv`→`pythia_UNLOPS`, ickkw=4) — see fxfx-unlops-fortran-cut. Don't say "ickkw=4 does nothing in MadGraph".
- FxFx requires post-shower event cleanup (handled downstream / Pythia8 side), not visible in this block.
