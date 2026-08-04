---
description: ReweightInterface (reweight_interface.py) + do_reweight entry + reweight_card — change/launch/set commands, LO/NLO mode gating, OLP=MadLoop requirement, f2py reload, multicore safety.
---

# ReweightInterface and do_reweight

`$MADGRAPH_INSTALL/madgraph/interface/reweight_interface.py`, class `ReweightInterface(extended_cmd.Cmd)` at :65.
Alternate-parameter-card matrix-element reweighting on existing LHE events (arxiv:1607.00763). Distinct from `Systematics` (scale/PDF) — this changes model parameters/process.

## Default state (`__init__`, ri.py:74-130)
`rwgt_mode=''` (LO/NLO/NLO_tree, '' default), `output_type='default'`, `helicity_reweighting=True`, `keep_ordering=False`, `use_eventid=False`, `options['allow_missing_finalstate']=False`. Holds an `mg5cmd = master_interface.MasterCmd()`.

## do_import gates (ri.py:132-220)
Entry that reads the LHE banner and sets `rwgt_mode`. Hard gates: no `slha` block → InvalidCmd "does not contain model information"; no `mg5proccard` → "does not contain generation information"; **`madspin` in banner and not `allow_madspin` → InvalidCmd "Reweight should be done before running MadSpin"** (ri.py:189-190) — reweight must precede MadSpin. Mode gating below. Full import + ME-source-generation flow on `reweight-me-source-generation`.

## Mode gating — NLO needs MadLoop (ri.py:195-210, do_change :404-418)
On import of an NLO event file (process has `[...]` and RunCardNLO):
- `store_rwgt_info` False → warn, force `rwgt_mode='LO'` (approximate).
- **`mother.options['OLP'].lower() != 'madloop'` → warn "Accurate NLO mode only works for OLP=MadLoop", force LO.** GoSam (or any non-MadLoop OLP) cannot do NLO-accurate reweighting.
- lhapdf not installed → warn, force LO.
- LO event file → always `rwgt_mode='LO'` regardless of `change mode`.
`change mode XXX` re-checks the same three conditions before accepting NLO.

## do_change sub-options (`do_change`, ri.py:368-438)
- `model X` — `second_model`; bumps `nb_f2py_module`, terminates fortran execs.
- `process DEF [--add]` — `second_process` (list; `--add` appends); bumps `nb_f2py_module`.
- `keep_ordering`, `use_eventid` (bool), `allow_missing_finalstate` (bool, into options).
- `boost EXPR` — `eval`'d into `boost_event`.
- `virtual_path`/`tree_path` — into `dedicated_path` (abspath).
- `output [default|2.0|unweight]` — `output_type`. default = add weights to current file.
- `helicity True|False`.
- `mode LO|NLO|NLO_tree|LO+NLO`.
- `rwgt_dir PATH` — abspath, mkdir if absent.
- `systematics ...` — forces `output_type='2.0'` if currently default (warn).
- `soft_threshold FLOAT`, `multicore` (no-op pass).
- `identical_particle_in_prod_and_decay average|max|crash` (ri.py:441-444) — into `options`; rejects any other value with an Exception. Governs handling when an identical particle appears in both production and decay (ambiguous permutation).
- `include_sudakov True` (ri.py:445-448) — sets `inc_sudakov=True` AND forces `rwgt_mode='LO'`. Triggers the EW-Sudakov branch; see `ew-sudakov-reweight` page.
- Unknown option → `logger.critical("unknown option! ... Discard line.")` (ri.py:449-450), line silently dropped (not an error).

## f2py reload (`nb_f2py_module` global, ri.py:59)
Module-level counter incremented on every `change model`/`change process`; used to force the f2py-compiled matrix-element module to reload (avoids stale standalone dir).

## do_launch (ri.py:497-546)
Loads model, builds f2py interface (`setup_f2py_interface`), computes `type_rwgt` weight names (`get_weight_names`, ri.py:480-494: mode `LO`→`['']`, `NLO`→`['_nlo']`, `LO+NLO`→`['_lo','_nlo']`, `NLO_tree`→`['_tree']`, empty+NLO→`['_nlo']`), processes param_card (with scan-iterator support), then `launch_actual_reweighting`. Weight tags written under `<weightgroup name='mg_reweighting' weight_name_strategy='includeIdInWeightName'>`, individual `<weight id='rwgt_<id>'>` (ri.py:871-919). `rwgt_name`/`rwgt_info` from `launch --rwgt_name= --rwgt_info=`.
- **The per-event ME computation** (`calculate_weight`/`calculate_matrix_element`/`calculate_nlo_weight`, the `smatrixhel` f2py call) is on the `me-reweight-evaluation-core` page. Key facts that affect command choice: NLO-accurate reweight is **pure-QCD-Born only** (mixed QCD+QED → hard Exception); αs is always taken from the event, not the new param_card; `allow_missing_finalstate=False` (default) crashes on a final state absent from the new model.

## do_set / do_compute_widths / do_quit
- `do_set` (ri.py:1050): must be AFTER `launch`; if before, warns and auto-inserts launch.
- `do_compute_widths` (ri.py:1100).
- `do_quit` (ri.py:1697).

## do_reweight entry (common_run_interface.py:2045)
- `check_multicore` (cri.py:2054-2083): **any `change output` or `change rwgt_dir` (or `change process`/`change model`) AFTER the first `launch` → multicore disabled (returns False).** run_mode in {0,1} also disables. A `change output`/`multicore` BEFORE launch is also checked.
- `--multicore=create`/`=wait` flags; `--plugin=` plugin reweighting.
- MADEVENT needs `mg5_path` set or raises InvalidCmd.
- Reads `Cards/reweight_card.dat`; `-from_cards` mode skips card editing.

## reweight_card default (`Template/Common/Cards/reweight_card_default.dat`)
Default active line `change mode NLO`. Structure: optional `change ...` lines, then `launch`, then `set BLOCK ID VALUE` lines OR a path to a param_card per launch. `change mode` allowed values LO/NLO/LO+NLO; no effect on LO .lhe (always LO). NLO/LO+NLO need `store_rwgt_info=True`.
- v3.7.1 default file also ships commented hints for `change rwgt_dir /PATH` (avoid overwriting the Sudakov rw_me file) and `change include_sudakov True` (EW Sudakov reweight) — both off by default.
- Header notes: alpha_s is taken from the event (param_card value ignored); large parameter changes (e.g. mass shifts ≫ width) give inaccurate ME-reweight results — use separate generation runs instead.

## Cautions
- GoSam OLP → NLO reweight silently degrades to approximate LO with only a `logger.warning`.
- `change output`/`rwgt_dir`/`process`/`model` after `launch` silently disables multicore (slow serial run, no error).
- `do_set` before `launch` is auto-corrected with a warning, not an error.
