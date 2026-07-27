---
description: aMCatNLOCmd runtime shell — do_launch/generate_events/calculate_xsect/shower/compile/banner_run/treatcards, the run_generate_events pipeline, run() folder mapping, and shower invocation.
---

# `aMCatNLOCmd` runtime shell (the `<PROC_DIR>` command processor)

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`, `class aMCatNLOCmd(CmdExtended, HelpToCmd, CompleteForCmd, CommonRunCmd)` (line 1474). `aMCatNLOCmdShell` (5929) adds CmdShell. `aMCatNLOError` (102), `aMCatNLOAlreadyRunning(InvalidCmd)` (919).

## Command entry points (do_*)
- `do_generate_events` (1705): thin wrapper → `do_launch(line)`.
- `do_calculate_xsect` (1652): sets `options['parton']=True`, `reweightonly=False`, then `do_launch`. Fixed-order cross-section only.
- `do_launch` (1739): the main chain. Resolves cluster_mode (multicore→2, cluster→1), calls `ask_run_configuration(mode|'auto', options, switch)` to get the resolved `mode`, assigns/auto-generates `run_name` (`run_%02i`, `_LO` suffix for LO), then `run_generate_events`.
- `do_shower` (1529): shower an existing `events.lhe` — `ask_run_configuration('onlyshower', options)` then `run_mcatnlo`.
- `do_banner_run` (1667): re-run from a banner; removes shower/madspin cards, splits banner, builds `mode_status` dict from banner `run_settings`, calls `do_launch(..., switch=mode_status)`. When forced (no card-edit), `mode_status` starts from a hardcoded base `{'order':'NLO','fixed_order':False,'madspin':False,'shower':True}` (1691) then overlays the banner's `run_settings` `k = v` lines (loop 1693-1696) (which `ask_run_configuration` emitted at 5880). If interactively choosing to edit, `mode_status={}` (re-asks the dialog). The base default is aMC@NLO — a banner lacking a `run_settings` block re-runs as aMC@NLO regardless of the original mode.
- `do_compile` (1888): `argss[0]` ∈ `{FO→NLO, MC→aMC@NLO}` (line 1898), asks config, compiles only.
- `do_treatcards` (1712): builds run_card.inc; for LO/NLO propagates FO_analyse_card `fo_lhe_weight_ratio` / `fo_lhe_postprocessing` (system-only run_card vars) before delegating to super.
- `do_plot` (1544): parton-level plots from `MADatNLO.top` via the `plot`/`plot_page-pl` scripts (uses `madanalysis_path`, `td_path`).

`__init__:1524`: if `[real=QCD]` NOT in proc_card → `check_compiler(block=True)` (gfortran ≥4.6 required for virtuals).

## run_generate_events pipeline (line 1838, @scanparamcardhandling)
Order: `compile(mode)` → `evt_file = run(mode)` → if not LO/NLO: systematics (if `systematics_program=='systematics'`), `reweight -from_cards`, `decay_events -from_cards`, optional `add_time_of_flight` → if not noshower/parton: `run_mcatnlo` (shower) + `madanalysis5_hadron`.
- Post-`run()` step exec_cmds (verified 1838-1888): `systematics <run_name> <systematics_arguments...>` (only if `systematics_program=='systematics'`; args from run_card `systematics_arguments`); `reweight -from_cards`; `decay_events -from_cards`; then `add_time_of_flight --threshold=<time_of_flight>` **only when `run_card['time_of_flight']>=0`** (a `>=0` gate, not truthy — `0` triggers it, the default-off sentinel is negative). After these, `evt_file` is reset to the (now-unzipped) `Events/<run>/events.lhe`.
- Shower+MA5 gate (1875): `run_mcatnlo` + `madanalysis5_hadron --no_default` fire only when `mode not in {LO,NLO,noshower,noshowerLO}` AND `not options['parton']`. MA5 is invoked with `--no_default` (silently no-ops on a missing/default madanalysis5_hadron_card — the card-existence gate is the MA5 slice's; this is the invocation site).
- `nevents==0` and not LO/NLO (line 1852): grids set up only, no event file, returns.
- `mode=='noshower'` (1874): warns "NLO events without showering are NOT physical".
- FxFx post-shower warning (1879): `ickkw==3` and (noshower or (parton_shower≠PYTHIA8 and aMC@NLO)) → warns to remove events by hand (FxFx_merging.htm).

## run() — integration + folder mapping (line 1923)
- `folder_names` (1934): `LO→born_G*`, `NLO→all_G*`, `aMC@LO→GB*`, `aMC@NLO→GF*`; noshower→GF*, noshowerLO→GB*.
- LO/NLO (1951): `mode_dict={'NLO':'all','LO':'born'}`, `req_acc=req_acc_FO`, integration loop until accuracy met → `finalise_run_FO` → returns (no event file; produces `MADatNLO.HwU`).
- aMC@NLO/aMC@LO/noshower/noshowerLO (1981): `ninitial==1` → `aMCatNLOError('Decay processes can only be run at fixed order.')`; reads `parton_shower` from run_card; `shower_list=['HERWIG6','HERWIGPP','PYTHIA6Q','PYTHIA6PT','PYTHIA8']` validated at line 2003; `PYTHIA6PT` + `has_fsr` → error (2011). 3 MINT steps (mcatnlo_status, line 1943).
- `nevents==0 and req_acc<0` (1989): error (cannot determine accuracy). `req_acc` valid is `0 < req_acc <= 1` or `-1` (line 1994 raises only on `req_acc>1 or req_acc==0`, so 1.0 IS allowed); `req_acc<0 and nevents>1M` auto-sets req_acc=0.001 (2000-2001).

## run_mcatnlo — shower invocation (line 3911)
- Reads `parton_shower` from the **banner** (3921). nsplit_jobs sanity vs nevents (3925).
- `HERWIGPP`/`PYTHIA8` need path_dict checks (3992): HERWIGPP→hepmc_path+thepeg_path+hwpp_path; PYTHIA8→pythia8_path.
- PYTHIA8 + `ickkw==3` (4018): needs `Pythia8Plugins/JetMatching.h` for FxFx.
- FastJet linking via shower_card `extralibs` (3947); falls back to fjcore if fastjet-config missing.
- StdHEP path used for HERWIG6/PYTHIA6* (hep_format == 'StdHEP', line 4220). MCatNLO scaffolding lives in `<PROC_DIR>/MCatNLO/` (linked from `$MADGRAPH_INSTALL/Template/NLO/MCatNLO/`). Verified template contents: source dirs `srcCommon, srcHerwig, srcPythia, srcPythia8`; analyzers `HWAnalyzer, HWPPAnalyzer, PYAnalyzer, PY8Analyzer`; plus `include, lib, objects, Scripts, shower_template.sh, Makefile_MadFKS, MCatNLO_MadFKS.inputs, README.shower`.

## Artefacts
- fNLO (LO/NLO): `Events/<run>/MADatNLO.HwU` histograms; parton `events.lhe.gz` for aMC modes.
- aMC@NLO: shower-ready `events.lhe.gz` (MC@NLO subtractions); showered `<run>_pythia8_events.hepmc.gz`.

## Cautions
- The shower name validated in `run()` (line 2003 list) differs from what `AskRunNLO.get_allowed_shower` may *offer* — `run()` reads from the run_card `parton_shower`, so a manually-edited run_card shower not gated by module availability still reaches `run()` and is checked against the fixed 5-name list.
- `do_calculate_xsect`/LO/NLO set `parton=True` → run_generate_events skips shower/madspin/reweight entirely; produces HwU not LHE-with-shower.
