---
description: MadGraph-side MLM->Pythia8 bridge — JetMatching:qCut auto-set to 1.5*xqcut, qCut<1.5*xqcut warnings, scheme=1 forced, nJetMax auto from proc_characteristic, template-card defaults (qCut/nJetMax=-1, doShowerKt=off is kt-MLM not scheme), SysCalc qCutList, Weight_MERGING LHE weight name.
---

# MLM -> Pythia8 bridge (MadGraph side)

Cites `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (setup_Pythia8RunAndCard) and `banner.py`. MadGraph fills PY8-card values from run-card; PY8 executes the matching (pythia8-interface slice owns the PY8 execution/card-write).

## MLM branch (run_type=='MLM', @4399-4471)
- @4403-4405: vetoes write-out of `Merging:TMS`, `Merging:Process`, `Merging:nJetMax` (avoid clashing with MLM driver).
- @4408-4409: if PY8 `JetMatching:qCut == -1.0` → MadGraphSet to `1.5*run_card['xqcut']` (force=True). So default qCut = 1.5*xqcut.
- @4411-4415: if `JetMatching:qCut < 1.5*xqcut` → logger.error "MLM merging qCut parameter you chose (...) is less than 1.5*xqcut ... better/safer to use a larger qCut or a smaller xqcut." (warning only, not abort).
- @4419: `Beams:setProductionScalesFromLHEF=True` (system) — use LHE shower starting scales.
- @4422-4423: `SysCalc:qWeed` auto-set to `xqcut` if -1 (only with mg5amc_py8_interface).
- @4425-4436: `SysCalc:qCutList=='auto'` + use_syst: if `sys_matchscale=='auto'`, list = `[factor*qcut for factor in [0.5,0.75,1.0,1.5,2.0] if factor*qcut > 1.5*xqcut]`; else parse `sys_matchscale` (space-split) and append the central qCut. (The `sys_matchscale` run-card knob and its three consumers are on sys-matchscale-variation.)
- @4439-4444: any qCutList scale < 1.5*xqcut → logger.error.
- @4452-4455: under `use_mg5amc_py8_interface and use_syst` → `JetMatching:doVeto=False` (MadGraphSet, not forced). The MLM analogue of CKKW's `Merging:applyVeto=False` — with systematics on, PY8 does NOT veto; the MG5aMC driver reweights instead (this is the mechanism behind the unchanged event count + reweight-mode in matched-xsec-banner-output's use_syst notice).
- @4456-4471: `JetMatching:merge=True`, `JetMatching:scheme=1`, `JetMatching:nQmatch=maxjetflavor`, `JetMatching:coneRadius=1.0`; `JetMatching:nJetMax` auto-set from `proc_characteristic['max_n_matched_jets']` if user left -1.

## Template-card defaults + scheme-vs-doShowerKt (doc-myth corrections)
`Template/LO/Cards/pythia8_card_default.dat` @43-49:
- `JetMatching:qCut = -1.0` (@43) — the TEMPLATE default is `-1.0` ("not set"), NOT a fixed number. MG derives it to `1.5*xqcut` (@4409). Any claim of a fixed default like `qCut=30` is fabricated — 30 is nowhere in source.
- `JetMatching:nJetMax = -1` (@49) — template default `-1` ("auto-guess"); MG auto-sets from `proc_characteristic['max_n_matched_jets']` (@4467-4471). NOT a fixed `2`.
- `JetMatching:doShowerKt = off` (@46). The template comment "Use default kt-MLM to match ... other Shower-kt scheme available too" (@44-45) attaches to `doShowerKt` (off = kt-MLM, on = shower-kt), **NOT** to `JetMatching:scheme`. `JetMatching:scheme` is absent from the template card entirely; it is system-forced to `1` (@4457). So "scheme=1 means the kT-MLM scheme" conflates two distinct knobs: `scheme=1` selects the MadGraph jet-matching scheme (Pythia8-side semantics; the exact value meaning is pythia8-interface's), and it is `doShowerKt=off` (default) that makes the clustering measure kt-MLM rather than shower-kt.

## Weight name convention (banner.py @1696-1706)
`RivetCard.setWeightName(runcard, py8card)` (class `RivetCard` @1563, method @1696; called from `madgraph/interface/common_run_interface.py:3005`): if `weight_name=="default"` (@1703): `ickkw==0` → `"None"` (@1704); else `weight_name = "Weight_MERGING={qCut}"` (@1706) with `round(py8card['JetMatching:qCut'],3)`. Used for Rivet weight selection. Histogram selector regex `madgraph/various/histograms.py:773` `r'^Weight_MERGING=[\d]*[.]?\d*$'`.

## Cautions
- `JetMatching:qCut` default is derived as 1.5*xqcut — NOT equal to xqcut. The matching (PY8) scale is 1.5x the generation (run-card) scale by default.
- qCut < 1.5*xqcut only errors in the log; the run proceeds. Physics can be wrong (matching scale below generation cut).
- `JetMatching:nQmatch` is tied to run-card `maxjetflavor`; changing maxjetflavor changes how many quark flavours are matched.
- All of the above are values MadGraph WRITES into the PY8 card. The card write-out mechanics and PY8 execution are the pythia8-interface slice; this page is the run-card->PY8 value derivation only.
