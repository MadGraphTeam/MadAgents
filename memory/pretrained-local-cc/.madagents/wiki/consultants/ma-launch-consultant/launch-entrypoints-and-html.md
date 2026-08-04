---
description: launch entry points (bin/generate_events, MELauncher in launch_ext_program) cluster/multicore flag mapping, and the launch-time HTML hooks (make_all_html_results, AllResults.add_detail prev_cross, results.html/index.html).
---

# Launch entry points and HTML hooks

## bin/generate_events (per-process script)
`$MADGRAPH_INSTALL/Template/LO/bin/generate_events` (v3.7.1) — copied into `<PROC_DIR>/bin/`.
- Re-execs itself with `-O` (optimize) unless a dev checkout (40-43).
- `treat_old_argument` (111-147): MG4-legacy numeric first arg. mode 0=serial -> `['-f', name, '--nb_core=1']`; mode 1=cluster -> `['-f', name, '--cluster']`; mode 2=multicore -> `['-f','--multicore', name, '--nb_core=opt']` (140-145).
- Main (159-189): picks `launch_plugin.MEINTERFACE` if `bin/internal/launch_plugin.py` exists, else `MadEventCmdShell`; runs `generate_events <args>` then `quit` (186-189).

## MELauncher (mg5_aMC `launch` -> generate_events bridge)
`$MADGRAPH_INSTALL/madgraph/interface/launch_ext_program.py:584` (MELauncher).
- `self.cluster=1` if cluster, `=2` if multicore (603-606).
- `launch_program` (614): mode=="2" asks core count (or uses max under `-f`) (618-633). Builds `generate_events <name>` and appends `--cluster` (mode 1) or `--nb_core=N` (mode 2), `-f` if force, `--laststep=`, `-R` (reweight), `-M` (madspin) (671-691). Then `launch.run_cmd(command)` + `quit` (699-700).
- After run, reads `SubProcesses/results.dat` first line for `cross error` and prints index.html pointer (706-715).

## do_banner_run (restart-from-banner entry point)
`madevent_interface.py:do_banner_run` (2182-2207). Re-runs a process from a saved banner.
- Removes any existing downstream cards (`delphes_trigger.dat`, `delphes_card.dat`, `pgs_card.dat`, `pythia_card.dat`, `madspin_card.dat`, `reweight_card.dat`) from `Cards/` (2190-2196), then `banner_mod.split_banner(args[0], me_dir, proc_card=False)` (2198) re-splits the banner into the run/param/etc. cards.
- If NOT forced: prompts "Do you want to modify the Cards?" default 'n'; answering 'n' sets `self.force=True` so the subsequent run is forced (2201-2204).
- Then `exec_cmd('generate_events <run> [-f]')` (2207) — i.e. banner_run is a thin wrapper that restores cards from a banner and re-enters the normal generate_events flow.

## Process-dir + run-name resolution (launch -> run_NN)
- **Bare `launch` -> last output dir.** `check_launch` (`madgraph_interface.py:1389-1400`): no positional arg -> uses `self._done_export[0]`, the directory set at `output` time (`_done_export = (self._export_dir, self._export_format)`, 9351; also re-set on explicit path launch, 1426). If `_done_export` is falsy it auto-runs `do_output('')` first (1402-1405). `launch <dir>` resolves the path via cwd / `MG5DIR` / `MG4DIR` (1412-1419).
- **Run subdir auto-increment `run_01, run_02, ...`.** `find_available_run_name` (`common_run_interface.py:4158-4165`): pattern `'run_%02d'`, scans `<me_dir>/Events/` for `run_<digits>` names, returns `max(existing+[0]) + 1`. So the counter is Events-dir-state-driven (a gap or a manually-named run does not reset it; only numeric `run_NN` dirs count). Zero-padded to 2 digits but `%02d` overflows past 99 (run_100).
- **Where the run dir lives.** `<PROC_DIR>/Events/<run_name>/` — e.g. `pjoin(me_dir,'Events',run_name)` (`madevent_interface.py:296`, `set_run_name` usage). `do_generate_events` (2396-2401): no arg -> `set_run_name(find_available_run_name(...))`; positional arg -> `set_run_name(args[0], ...)` then pops it (that arg is the explicit run name).
- **`-n`/`--name` custom run name (mg5 `launch` level).** `_launch_parser.add_option("-n","--name", ...)` (`madgraph_interface.py:10284`) — `-n` IS a valid short form. Flows to `MELauncher.name` (`launch_ext_program.py:611` assert; empty -> `find_available_run_name`, 612-613) and is emitted as `generate_events <name>` (671/677) -> `set_run_name(args[0])` (madevent 2400). Help example: `launch PROC_sm_1 --name=run2` (madgraph_interface.py:418). At the `generate_events` REPL level the equivalent is a positional run name, or `--name=X` (banner-run path, madevent 949-955).

## Launch-time HTML generation
- `sum_html.make_all_html_results(cmd, ...)` (`$MADGRAPH_INSTALL/madgraph/madevent/sum_html.py:771`): makes `HTML/<run>/`, `collect_result` over P-dirs, writes `HTML/<run>/results.html` (790-793) and `SubProcesses/results.dat` (788). Returns `(xsec, xerru)` or attrs via `get_attr`. Called from survey (make_make_all_html_results) and refine. Per-result aggregation (collect_result / Combine_results) is mc-integration slice; the launch-time invocation is here.
- `gen_crossxhtml.AllResults.add_detail` (`gen_crossxhtml.py:345`): stores cross/error/nb_event/etc. **prev_cross trick** (367-369): when `cross` is written and the existing value is nonzero, the old value is saved to `prev_cross` — this is what the second-refine threshold reads.
- `AllResults.output` (387): writes the top-level status/cross table for `HTML/index.html` (top-level index updated by `make_all_html_results` in madevent_interface, distinct from sum_html's per-run one).

## do_open (the `open` command — view results/cards)
`common_run_interface.py:do_open` (3525-3533): `open FILE` -> `check_open` resolves the path then `misc.open_file`. `check_open` (457-493) resolution order for a bare name: `me_dir/FILE`, then `me_dir/Cards/FILE`, then `me_dir/HTML/FILE`; a `*_card.dat` with no instance is auto-copied from its `_default.dat`. `index.html` lives at the process-dir root, so `open index.html` resolves to `<PROC_DIR>/index.html` — the top-level web results/graphical interface. `./`-prefixed paths are taken literally (must exist). The command name is `open`, not `do_open`; help_open (madevent_interface.py:355) documents index.html/param_card.dat/run_card.dat as special names. `misc.open_file` picks the viewer from `mg5_configuration.txt`.

## Cautions
- The `launch` 1>N path prints a "since 2.3 launch passes through event generation" note but still issues `generate_events` (MELauncher 671-677) — width-by-launch goes through generation, not the legacy width calc.
- MELauncher under `-f` multicore uses ALL cores (`nb_node=max_node`, 632) rather than prompting; a forced launch can saturate the machine.
- The shell cross-section printed at the end comes from `SubProcesses/results.dat`; "Generation failed (no results.dat file found)" (708) is the symptom of a survey that never produced results.
