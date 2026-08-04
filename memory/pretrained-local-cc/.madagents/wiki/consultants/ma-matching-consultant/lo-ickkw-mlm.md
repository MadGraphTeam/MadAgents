---
description: LO matching (RunCardLO) — ickkw param, MLM-block params, xqcut, drjj/drjl auto-zeroing, ktscheme Fortran clustering-measure semantics (Durham vs Pythia), auto_ptj_mjj Fortran side, and the LO auto-detect that turns matching on.
---

# LO matching block (RunCardLO)

All cites `$MADGRAPH_INSTALL/madgraph/various/banner.py`, class `RunCardLO` (def @4187).

## Parameter registrations (default_setup, @4282-4291, @4423-4432)
Numeric defaults are drift-prone — read each fresh at its cited line in `RunCardLO.default_setup`/`add_param` (banner.py); the coordinate + role below is the cached knowledge, not the value.
- `ickkw` @4284: default `0` (off), `allowed=[0,1]`, hidden. Comment: "'0' for standard fixed order computation. '1' for MLM merging activates alphas and pdf re-weighting according to a kt clustering of the QCD radiation." Template comment @3986: "0 no matching, 1 MLM".
- `scalefact` @4283: NOT hidden; read default @4283.
- `highestmult` @4285: `fortran_name="nhmult"`, hidden; read default @4285.
- `ktscheme` @4286: hidden; read default @4286. (Only registration; no validity branch references it.)
- `alpsfact` @4287: hidden; read default @4287.
- `chcluster` @4288: default `False`, hidden.
- `pdfwgt` @4289: default `True`, hidden.
- `asrwgtflavor` @4290: hidden; read default @4290. Comment "highest quark flavor for a_s reweighting in MLM".
- `clusinfo` @4291: default `True`, hidden.
- `xqcut` @4425: default `0.0` (off), `cut=True`. Template comment @3992 "minimum kt jet measure between partons".
- `maxjetflavor` @4424: read default @4424.
- `pdgs_for_merging_cut` @4423: hidden; read default list @4423 (gluon + light quarks).
- `use_syst` @4426: default `True`.
- `sys_matchscale` @4432: default `"auto"`, include=False, hidden. Written into SYSCALC block @3923 "variation of merging scale".
- `auto_ptj_mjj` @4304: default `True`. Auto-sets ptj/mjj from xqcut when xqcut>0.
- `drjj` @4344: `cut='jj'`; `drjl` @4350: `cut='jl'`; read defaults @4344/@4350.

## check_validity matching logic (@4544-4577)
- `ickkw>0` branch @4544:
  - `ickkw != 1` @4545: logger.critical "ickkw >1 is pure alpha and only partly implemented"; interactive y/n prompt; raises `InvalidRunCard('ickkw>1 is still in alpha')` unless 'y'.
  - if `use_syst` and `alpsfact != 1.0` @4553: warns, forces `alpsfact = 1.0`.
  - `maxjetflavor == 6` @4556: raises `InvalidRunCard('maxjetflavor at 6 is NOT supported for matching!')`.
  - `ickkw == 2` @4558: pulls defaults for `highestmult` and `issgridfile`.
- `xqcut>0` branch @4562:
  - `ickkw == 0` @4563: logger.error "xqcut>0 but ickkw=0. Potentially not fully consistent setup. Be careful" + `time.sleep(5)`.
  - `drjj != 0` @4566: forces `drjj = 0` (warns only if user-set). Same for `drjl` @4570.
  - if not auto_ptj_mjj and `mmjj > xqcut` @4575: warns, sets `mmjj = 0.0`.
- `maxjetflavor > 6` @4507: raises (general, not matching-gated). Note comment says "should be lower than 5! (6 is partly supported)".

## LO auto-detect: matching turned ON automatically (create_default_for_process @4767)
- @4782: `pdgs_for_merging_cut` overwritten with `proc_characteristic['colored_pdgs']`.
- @4807-4810: pp/jet beams → `maxjetflavor`/`asrwgtflavor` set to max beam jet flavor.
- Multi-multiplicity jet detection @4940-4954: if min- and max-leg processes differ only by jets (pdg in {1..5,21}), `matching=True`.
- When matching @4956-4966: `ickkw=1`, `xqcut` set to a default merging scale, `drjj=0`, `drjl=0`, `sys_alpsfact`/`--alps` set to the auto variation set, displays mlm+ckkw blocks, `dynamical_scale_choice=-1`. (Read the forced literals fresh @4956-4966 — they are input-specific, not physics recommendations.)
- Model-limitation overrides @5048-5066: if `'MLM' in proc_characteristic['limitations']` OR `'fix_scale' in limitations`, force `ickkw=0` (critical log if it was 1: "MLM matching/merging not compatible with the model!"). HEFT/hgg-vertex models hit this path (see heft-merging-jetflag page).

## ktscheme Fortran semantics (clustering measure: 1 vs 2)
`ktscheme` only registered in Python (no validity branch); its effect is entirely Fortran-side, in the MLM kt-clustering.
- run.inc common: `common/to_cluster/ktscheme,chcluster,pdfwgt` (`$MADGRAPH_INSTALL/Template/LO/Source/run.inc:46-48`).
- `cluster.f` final-state branch (`$MADGRAPH_INSTALL/Template/LO/SubProcesses/cluster.f:610-613`): `ktscheme==2` → measure = `pydj(...)`; else (==1) → `dj(...)`. Initial-state branch @621-622: `ickkw==2 .or. ktscheme==2` → `pyjb(...)`. (Same pair repeats in the second clustering loop @869-881.)
- Measure definitions in `$MADGRAPH_INSTALL/Template/LO/Source/kin_functions.f`:
  - `DJ` @230 (ktscheme=1): Durham kT — `y_{ij}=2·min[pT_i²,pT_j²]/S·(cosh Δη − cos Δφ)`.
  - `PYDJ` @313 (ktscheme=2): Pythia pTE-style — `p1(0)*p2(0)/(p1(0)+p2(0))**2 * SumDot(p1,p2,1)`.
  - `PYJB` @433 (beam, ktscheme=2 or ickkw=2): Pythia jet-vs-beam measure.
- Label confirmation: MadWeight run_card comment "ktscheme for xqcut: 1: pT/Durham kT; 2: pythia pTE/Durham kT" (`$MADGRAPH_INSTALL/Template/MadWeight/src/setrun.f:325`); MadWeight run_card.dat:80 "for ickkw=1, 1 Durham kT, 2 Pythia pTE".
- `myamp.f:341`: `if(ickkw.eq.2.or.ktscheme.eq.2) xqfact=0.3d0` — ktscheme=2 (or ickkw=2) scales xqcut by 0.3 for the matrix-element cut.

## auto_ptj_mjj — Fortran side (setcuts.f, depends on ktscheme)
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/setcuts.f:153-170`, runs when `xqcut>0`:
- `auto_ptj_mjj .and. ptj>=0 .and. ktscheme==1` → `ptj=xqcut` (warning "ptj set to xqcut to improve integration efficiency"; note warns it may affect non-radiated/decay jets — suggests `cut_decays=F`).
- else if `ptj>xqcut` → `ptj=0` (warning "ptj set to 0 since xqcut>0 and auto_ptj_mjj=F or ktscheme>1").
- `auto_ptj_mjj .and. mmjj>=0` → `mmjj=xqcut`.
So the Python-side `auto_ptj_mjj` default True (registration @4304) is enforced in Fortran, but the `ptj=xqcut` shortcut applies ONLY for `ktscheme==1`; with `ktscheme>1` ptj is instead zeroed.

## Hidden-block reveal: `update mlm` / `update ckkw`
The MLM and CKKW parameter blocks are HIDDEN in the default LO run_card; the placeholder text (template_off @3994) prints literally: `# To see MLM/CKKW merging options: type "update MLM" or "update CKKW"`.
- `mlm_block = RunBlock('mlm', ...)` @3995; `ckkw_block = RunBlock('ckkw', ...)` @4009. Block names are `mlm` / `ckkw` (NOT `ckkwl`; case-insensitive on input).
- MLM `template_on` @3982-3993 reveals: `ickkw, alpsfact, chcluster, asrwgtflavor, auto_ptj_mjj, xqcut`.
- CKKW `template_on` @3998-4007 reveals: `ktdurham, dparameter, ptlund, pdgs_for_merging_cut`.
- Reveal command: `do_update` in `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py:6833`; `elif args[0] in self.update_block` @6892 → `run_card.display_block.append(args[0].lower())` (writes the block into the card on next write). `update_block` populated from `run_card.blocks` names @5246. Auto-detect also reveals both blocks (`display_block.append('mlm')` @4964). The `do_update` command dispatch itself is interface-slice territory; the parameter *semantics* of what each block reveals are this slice.

## Cautions
- **MLM does NOT enforce xqcut>0.** The `ickkw>0` branch @4544-4561 checks alpsfact, maxjetflavor==6, ickkw==2 — but NEVER checks xqcut. So `ickkw=1 + xqcut=0` passes check_validity silently (no abort, no warning). The "xqcut must be nonzero for MLM" is a physics requirement, NOT a MadGraph-enforced one. (Only the reverse, `xqcut>0 + ickkw=0` @4563, warns.) A doc claiming MG5 enforces it is wrong.
- **maxjetflavor allowed values, not just 4/5.** General cap @4507: `>6` raises ("should be lower than 5! (6 is partly supported)"). With matching (ickkw>0) @4556: `==6` raises ("NOT supported for matching!"). So under matching 6 is forbidden and higher values partly-supported without matching; read the default @4424. Auto-set to max beam jet flavor for pp/jet beams @4808.
- `xqcut>0 + ickkw=0` only logs an error and sleeps (see @4563-4565) — it does NOT abort. A run with that combo proceeds.
- `drjj`/`drjl` are silently zeroed whenever xqcut>0 (warning only if user had set them). Phase-space jet separation is then handled by xqcut, not drjj.
- Auto-detect sets a default `xqcut` merging scale (read @4956-4966) — input-specific; not a recommended physics value.
- `ktscheme` has NO Python validity branch — an out-of-range value is not caught at card-parse; it changes the Fortran clustering measure and (for >1) the ptj/xqfact handling silently. Default 1 (Durham kT) is the standard MLM measure.
