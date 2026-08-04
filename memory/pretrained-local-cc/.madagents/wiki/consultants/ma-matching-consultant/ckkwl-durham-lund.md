---
description: CKKW-L for Pythia8 — the LO-card ktdurham/ptlund/dparameter cuts, the positivity CKKW-run marker, and the full setup_Pythia8RunAndCard CKKW branch (Merging:TMS=cut 1:1, nQuarksMerge, nJetMax, tmsList variation, shower pTmaxMatch/applyVeto, both-on abort).
---

# CKKW-L merging (LO+PS, Pythia8 side)

MadGraph's role: write the CKKW-L merging-scale cut into the LHE generation cuts and mark the run as CKKW; the merging itself is executed by Pythia8 (pythia8-interface slice).

## Run-card params (RunCardLO, `$MADGRAPH_INSTALL/madgraph/various/banner.py`)
- `ktdurham` @4420: default `-1.0` (off sentinel — a positive value activates CKKW-L), `fortran_name="kt_durham"`, `cut='j'`.
- `dparameter` @4421: `fortran_name="d_parameter"`, `cut='j'`; read default @4421 (drift-prone).
- `ptlund` @4422: default `-1.0` (off sentinel), `fortran_name="pt_lund"`, `cut='j'`.
- These are written in the `ckkw_block` template @3998-4007 (`ckkw_block = RunBlock('ckkw', ...)` @4009), header "Turn on either the ktdurham or ptlund cut to activate CKKW(L) merging with Pythia8 [arXiv:1410.3012, arXiv:1109.4829]". `pdgs_for_merging_cut` is written in the same block.
- No special check_validity branch for these (just generation cuts).

## Run-type marker (`$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py`)
`run_type` decision @4671-4677:
- `ickkw==1` → `'MLM'`.
- `ickkw==2` OR `ktdurham>0.0` OR `ptlund>0.0` → `'CKKW'`.
- else `'default'`.
Comment @4472: "We use the positivity of 'ktdurham' cut as a CKKWl marker."

## Full CKKW branch in `setup_Pythia8RunAndCard` (madevent_interface.py @4473-4567)
The run-card → PY8-card derivation MadGraph performs for a CKKW run (the value derivation is my slice; the PY8 card write/execution is pythia8-interface):
- @4476: if `Merging:Process == '<set_by_user>'` → `raise InvalidCmd` "the user must specifiy the option 'Merging:Process' in pythia8_card.dat" (links Pythia8 CKKWLMerging docs).
- @4485-4487: vetoes write-out of `JetMatching:qCut`, `JetMatching:doShowerKt`, `JetMatching:nJetMax` (avoid clashing with MLM driver).
- **Cut selection (@4490-4503):** `ptlund<=0 and ktdurham>0` → `Merging:doKTMerging=True`, `Merging:Dparameter=dparameter`, `CKKW_cut='ktdurham'`. `ptlund>0 and ktdurham<=0` → `Merging:doPTLundMerging=True`, `CKKW_cut='ptlund'`. **else (both on OR both off) → `raise InvalidCmd("*Either* the 'ptlund' or 'ktdurham' cut ... but *both* cuts cannot be turned on at the same time")`** — see "Both-on is an abort" below.
- @4507-4508: `SysCalc:qWeed` auto-set to `run_card[CKKW_cut]` if -1 (force=True).
- **`Merging:TMS` (@4512-4522)** — the CKKW merging scale on the PY8 side: if user left `Merging:TMS==-1.0`, MadGraphSet to `run_card[CKKW_cut]` (force=True) when that cut >0, else `raise InvalidCmd` "select a '<cut>' cut larger than 0.0 in the run_card". If user set `Merging:TMS < run_card[CKKW_cut]` → `logger.error` "It is incorrect to use a smaller CKKWl scale than the generation-level <cut> cut!" (warn-only; proceeds). So **TMS defaults to the generation cut (ktdurham/ptlund), 1:1 — NOT 1.5× like the MLM qCut** (contrast mlm-py8-bridge).
- @4524-4526: shower settings forced — `TimeShower:pTmaxMatch=1`, `SpaceShower:pTmaxMatch=1`, `SpaceShower:rapidityOrder=False`.
- @4528-4533: under `use_mg5amc_py8_interface and use_syst` → `Merging:applyVeto=False`, `Merging:includeWeightInXsection=False` (the MG5aMC driver does the veto, not PY8). MadGraphSet (system mode), not forced — user can override.
- @4536: `Merging:nQuarksMerge = run_card['maxjetflavor']` (analogue of MLM's `JetMatching:nQmatch`).
- @4538-4543: `Merging:nJetMax` auto-set from `proc_characteristic['max_n_matched_jets']` if user left -1 (logger.info).
- **`SysCalc:tmsList` merging-scale variation (@4544-4565):** if `=='auto'` and `use_syst`: `sys_matchscale=='auto'` → `[factor*TMS for factor in [0.5,0.75,1.0,1.5,2.0] if factor*TMS > run_card[CKKW_cut]]`; else parse `sys_matchscale` space-split + append central TMS. If tmsList scale `< run_card[CKKW_cut]` → logger.error (warn). Mirror of the MLM `qCutList` logic (mlm-py8-bridge) but for TMS/CKKW. (See sys-matchscale-variation page for the run-card `sys_matchscale` knob this consumes.)

## No-merging else-branch (madevent_interface.py @4567-4575)
When `run_type=='default'` (no merging): vetoes write-out of `Merging:TMS`, `Merging:Process`, `Merging:nJetMax`, `JetMatching:qCut`, `JetMatching:doShowerKt`, `JetMatching:nJetMax` — "can trigger undesired vetos in an unmerged simulation". So a non-merged PY8 run strips ALL merging/matching params.

## Both-on is an abort, not a silent kT-pick
- The run_type marker (@4675-4677) does mark both-on (`ktdurham>0 AND ptlund>0`) as `'CKKW'`, but `setup_Pythia8RunAndCard` then **ABORTS** in the cut-selection else-branch (@4500-4503): both-on raises `InvalidCmd("*both* cuts cannot be turned on at the same time")`. So both-on is an abort, not a silent kT-pick. (This is an abort-tier instance the matching-abort-vs-warn page should also carry.)

## Cautions
- ktdurham and ptlund are mutually-exclusive activation knobs (template header "either"). **Both-on ABORTS** (InvalidCmd @4500); exactly one must be >0.
- `Merging:Process` is a hard requirement for CKKW — absence aborts the PY8 step (InvalidCmd @4476), unlike MLM which auto-derives most settings.
- `Merging:TMS` defaults to the generation cut value 1:1 (not 1.5× like MLM qCut). TMS < cut only warns; both-zero-cut and unset-TMS abort.
- The PY8-card write-out / merging execution is the pythia8-interface slice. This page covers the MadGraph-side cut params, run-type marker, and the run-card→PY8 value DERIVATION (not the card write or PY8 run).
