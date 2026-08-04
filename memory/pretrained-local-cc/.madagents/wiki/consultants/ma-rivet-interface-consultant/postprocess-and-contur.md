---
description: Rivet postprocessing + Contur run path in madevent_interface.py — run_rivet_later deferral, cluster submission, single-yoda vs scan-tree Contur invocation, heatmap plotting.
---

# Postprocessing & Contur (madevent_interface.py)

## Entry: postprocessing() (2411-2420)
- Calls `common_run.CommonRunCmd.do_rivet(self, "--no_default", True)` (postprocess=True) (2414).
- If it returns (i.e. a rivet_card existed): unpacks `[rivet_config, postprocess_RIVET, postprocess_CONTUR]` (2415-2418).
- If `postprocess_RIVET or postprocess_CONTUR` -> `rivet_postprocessing(...)` (2419-2420).
- `do_rivet` with `--no_default` returns None when no rivet_card.dat -> postprocessing is a no-op then.

## rivet_postprocessing(rivet_config, postprocess_RIVET, postprocess_CONTUR) (2422-2561)
- `run_dirs` = one per name in `self.postprocessing_dirs` (populated by do_rivet when run_rivet_later=True) (2425-2426); `nb_rivet = len(run_dirs)`.

### postprocess_RIVET branch (2430-2445)
- Submits each `run_rivet.sh` via `self.cluster.submit2(..., argument=[str(i_rivet)])` (2433-2434).
- `self.cluster.wait(...)` with a monitoring callback logging Idle/Running/Done (2438-2443).
- This is the deferred (scan) path: all Rivet jobs run together after all parameter points showered.

### postprocess_CONTUR branch (2447-2561)
- Builds set_env with rivet/yoda PATH+LD_LIBRARY_PATH+PYTHONPATH (2452-2468), then contur PATH/PYTHONPATH (2470-2473), `source <contur_path>/contur/setupContur.sh` (2475).
- mkdir `Analysis/contur` (2477).
- nb_rivet==1 (single run) (2479-2485):
  - symlink the single `rivet_result.yoda` into `Analysis/contur/`.
  - `contur --wn "{weight_name}" <yoda>` if weight_name != "None", else `contur <yoda>` (2482-2485).
- nb_rivet>1 (scan) (2486-2550):
  - per point: mkdir `Analysis/contur/scan/<contur_ra>/<NNNN>/`, symlink `rivet_result.yoda` as `runpoint_<NNNN>.yoda` and `params.dat` (2488-2500).
  - if xaxis/yaxis relvar set -> `setRelevantParamCard` rewrites params.dat with derived columns (2502-2509). See its mechanism below.
  - `contur --nomultip -g scan [--wn "<weight_name><contur_add>"] >> contur.log` (2511-2518).
  - if `draw_contur_heatmap`: append `contur-plot ANALYSIS/contur.map <x> <y> [labels] [--xlog/--ylog]` (2520-2550).
- Writes `Analysis/contur/run_contur.sh`, `misc.call(["run_contur.sh"], cwd=Analysis/contur)` (2552-2558).
- Output -> `Analysis/contur/conturPlot` (2560).

## Deferral logic recap (set in do_rivet)
- `run_rivet_later=True` (default in shipped template) => defer to postprocessor; run_name appended to postprocessing_dirs.
- A manual `rivet` command (no `--no_default`) forces run_rivet_later=False -> runs immediately (common_run_interface.py:2974-2975).
- hepmc output containing "remove" or "fifo" forces run_rivet_later=False (can't defer) (common_run_interface.py:3071-3072).

## setRelevantParamCard(f_params, f_relparams) (banner.py:1708-1741) — derived heatmap axes via exec()
Used ONLY in the Contur scan-tree heatmap path (2502-2509) when `xaxis_relvar`/`yaxis_relvar` is set. Purpose (docstring 1711-1714): scan a BSM quantity NOT directly in the UFO — e.g. scan coupling^2 when the UFO only carries coupling.
- Reads each line of the point's `params.dat`, accumulates them into one Python `exec_line` prefixed `import math; ` (1716-1720), and copies each line verbatim into the relparams file.
- For x (1721-1730) and y (1732-1741): builds `exec_line + "xaxis_relvar = " + self['xaxis_relvar']` and runs `exec(xexec_line, locals(), xexec_dict)` — the param values become in-scope locals, then the user's relvar expression is EVALUATED. Result written as `<xaxis_label> = <value>` into relparams (1727 x / 1738 y).
- `xaxis_label==""` (i.e. card said "default", read() blanked it) -> label becomes the literal string `"xaxis_relvar"`/`"yaxis_relvar"` (1726 x / 1737 y); if no relvar, label falls back to `xaxis_var`/`yaxis_var` (1729-1730 x / 1740-1741 y).
- CAUTION (source-visible, not a runtime claim): `xaxis_relvar`/`yaxis_relvar` are USER strings from the rivet_card and are passed straight to `exec()` with `import math` in scope (template literally says "python library works!"). Arbitrary-Python evaluation surface; a malformed relvar raises at exec() during postprocessing. This is by design (it is how relative axes are computed), but it means the rivet_card is trusted-input.

## fast_rivet shortcut (common_run_interface.py:5345-5346)
Card-editor macro: sets `run_rivet_later True`, `draw_rivet_plots False`, `HEPMCoutput:file hepmc` (uncompressed), `partonlevel:mpi=off`. For fast multi-point scans; warns it does NOT compress HepMC (storage).
