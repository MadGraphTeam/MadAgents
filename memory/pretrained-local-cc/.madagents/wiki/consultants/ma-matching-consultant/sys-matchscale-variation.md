---
description: sys_matchscale — the run-card merging-scale variation knob (matching systematics). Its 'auto' meaning across three consumers (MLM qCutList, CKKW tmsList, legacy SysCalc matchscale field), the '30 50' SysCalc auto-restore, and the SysCalcError aborts when a variation scale is below the generation cut. ALSO: sys_alpsfact/--alps (alpha_s emission-scale variation, MLM-specific — reweights clustering-node scales) and the fact that no on-the-fly matching-SCALE (xqcut/qCut) reweighting exists (needs regeneration).
---

# sys_matchscale: merging-scale variation (matching systematics)

`sys_matchscale` varies the MATCHING/MERGING scale for systematics — distinct
from `sys_scalefact` (μR/μF) and `sys_pdf` (PDF), which are the systematics
slice's. The merging-scale variation is matching's. This page maps the run-card
knob and its three consumers.

## Registration (RunCardLO, banner.py)
- `banner.py:4432`: `self.add_param("sys_matchscale", "auto", include=False, hidden=True)`. Default `"auto"`, string, not written to the Fortran include.
- SYSCALC block template `banner.py:3923`: `%(sys_matchscale)s = sys_matchscale # variation of merging scale`.

## Consumer 1 — MLM qCutList (madevent_interface.py @4425-4448)
In `setup_Pythia8RunAndCard` MLM branch (see mlm-py8-bridge): `SysCalc:qCutList=='auto'` + use_syst:
- `sys_matchscale=='auto'` → `[factor*qCut for factor in [0.5,0.75,1.0,1.5,2.0] if factor*qCut > 1.5*xqcut]` (drop factors below the 1.5×xqcut floor).
- else → `sys_matchscale`.split() parsed as the list, central qCut appended.
- @4439-4448: any qCutList scale `< 1.5*xqcut` → `logger.error` (warn, proceeds).

## Consumer 2 — CKKW tmsList (madevent_interface.py @4544-4565)
In the CKKW branch (see ckkwl-durham-lund): `SysCalc:tmsList=='auto'` + use_syst, same shape but against `Merging:TMS` and the generation `CKKW_cut` (ktdurham/ptlund):
- `sys_matchscale=='auto'` → `[factor*TMS for factor in [0.5,0.75,1.0,1.5,2.0] if factor*TMS > run_card[CKKW_cut]]`.
- else → parsed list + central TMS appended.
- @4560-4565: tmsList scale `< run_card[CKKW_cut]` → `logger.error` (warn).

## Consumer 3 — legacy SysCalc card (madevent_interface.py @6622-6706)
The standalone `run_syscalc` path (legacy SysCalc external tool, PY6-era), distinct from the PY8-driver bridge:
- @6622-6623: **`sys_matchscale=='auto'` → restored to the hard-coded string `"30 50"`** ("Restore the old default for SysCalc+PY6"). So for legacy SysCalc, `auto` means the two scales 30 and 50 GeV — NOT a factor sweep. Non-obvious: the same `'auto'` value means different things to the PY8 bridge (factor sweep) vs legacy SysCalc (fixed "30 50").
- @6645: passed into `to_syscalc` dict → fills the `matchscale:` field of `syscalc_card.dat` via `syscalc_template.dat` (`Template/LO/bin/internal/syscalc_template.dat`, `# matching scales\nmatchscale:\n%(sys_matchscale)s`).
- @6700-6706 (mode=='Pythia', legacy): if the banner's `mgpythiacard` carries a `qcut=`, scrapes it and for each `sys_matchscale` value → `raise SysCalcError('qcut value for sys_matchscale lower than qcut in pythia_card. Bypass syscalc')` if value < qcut, and `raise SysCalcError(... lower than xqcut in run_card ...)` if value < `abs(xqcut)`. **These are SysCalcErrors that BYPASS syscalc (the run is not aborted — systematics are skipped).**

## Related knob — sys_alpsfact / `--alps` (alpha_s emission-scale variation, MLM-specific)
Distinct from `sys_matchscale` (which varies the merging CUT). `sys_alpsfact`/`--alps` varies the scale at which alpha_s is evaluated for the CLUSTERING-node reweighting — the "emission scale variation" (systematics.py:546 writes `# emission scale variation:` into the summary). This is systematics-slice source; the MLM-specificity is this slice's physics:
- Path: run_card `sys_alpsfact` (systematics.py:1379-1383) → `opts['alps']` → `Systematics.alps` (default `[1]`, systematics.py:56); also the command-line `--alps=VALS` form. Auto-detect (banner.py:4956-4966) sets `sys_alpsfact="0.5 1 2"` and appends `--alps=0.5,1,2` when matching turns on.
- Mechanism (systematics.py get_lo_wgt @1024-1031): `Dalps` scales **`loinfo['asrwt']`** (the alpha_s clustering-node scales) and the intermediate **`pdf_q1/pdf_q2`** clustering scales. These come ONLY from the `<mgrwt>`/`<asrwt>`/`<pdfrwt>` block (lhe_parser.py parse_lo_weight @1578-1631), which reweight.f/unwgt.f write for matched samples (see mlm-reweight-lhe-write). In a plain fixed-order run `asrwt` is empty and `n_pdfrw==1`, so `Dalps` reweights nothing → the variation is a no-op. So `--alps`/`sys_alpsfact` is relevant only for MLM matching: alps varies the kt-clustering alpha_s+PDF reweighting scale, which only exists in matched output.
- Ties to run_card `alpsfact` (MLM-only, forced to 1.0 when use_syst under ickkw>0, banner.py:4553) — `alpsfact` is the CENTRAL clustering-scale factor; `sys_alpsfact`/`--alps` are its systematic variations.

## No on-the-fly matching-SCALE reweighting (xqcut/qCut need regeneration)
- The runtime `Systematics` class (systematics.py) reweights mur/muf/**alps**/dyn/pdf ONLY. There is NO xqcut/qcut/matchscale variable anywhere in it (grep-clean). So the merging CUT (xqcut/qCut) cannot be varied by on-the-fly LHE reweighting — it requires separate event generations.
- The only merging-scale variation MG offers (`sys_matchscale` → qCutList/tmsList, above) acts at the Pythia8/SysCalc shower stage and can only re-veto DOWNWARD toward the generation cut — the ME phase space below xqcut was never generated (reweight.f setclscales drops events with clustered pt < xqcut, see mlm-reweight-lhe-write). To LOWER the matching scale you must regenerate. So: qCut re-veto within [floor, ...] is cheap; changing xqcut is a fresh generation.
- Scope note: `--alps`/get_lo_wgt reweighting mechanism is systematics-slice source (I verified the MLM-connection, not the full Systematics weight algebra).

## Cautions
- `'auto'` is OVERLOADED: PY8-bridge MLM/CKKW interprets it as the factor sweep `[0.5,0.75,1.0,1.5,2.0]×central`; legacy SysCalc interprets it as the literal `"30 50"`. Which one fires depends on the systematics path (PY8 driver vs external SysCalc tool).
- A `sys_matchscale` value below the generation cut is handled differently per consumer: PY8 bridge only `logger.error`s (variation still attempted); legacy SysCalc `raise`s `SysCalcError` and bypasses syscalc entirely (systematics skipped, main run unaffected).
- The factor-sweep floor differs: MLM uses `1.5*xqcut`, CKKW uses `run_card[CKKW_cut]` (the raw ktdurham/ptlund) — because MLM's PY8 qCut is itself 1.5×xqcut while CKKW's TMS is the cut 1:1 (see mlm-py8-bridge vs ckkwl-durham-lund).
- This knob varies the MERGING scale only. μR/μF and PDF systematics (`sys_scalefact`, `sys_alpsfact`, `sys_pdf`) are the systematics slice's — the legacy SysCalc card carries all of them together, but only `matchscale` is matching's.
- All static-source (card-fill + validity). The actual systematics weights produced are runtime — probe-candidates, not asserted.
