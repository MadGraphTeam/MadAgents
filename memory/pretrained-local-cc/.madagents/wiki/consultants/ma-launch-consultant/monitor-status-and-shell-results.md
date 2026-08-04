---
description: The run-monitoring / status-reporting layer every launch stage calls — monitor(), update_status() (HTML-write rate-limit throttle), add_error_log_in_html, keep_cards (dot-hide), print_results_in_shell, store_result, GridPackCmd silent update_status override.
---

# Monitor, status, and shell-results layer

The cross-cutting layer that survey/refine/combine/store all call to report progress, write HTML status, manage cards, and print the final cross-section. Cites: `madevent_interface.py` (ME) and `common_run_interface.py` (CR), v3.7.1.

## monitor (ME 6011-6045) — the cluster-wait wrapper
`monitor(run_type='monitor', mode=None, html=False)`. `mode` defaults to `self.cluster_mode` (the run_mode int from `configure_run_mode`).
- **mode == 0** (single/`MultiCore(1)`): does nothing past setup — no wait loop entered (the `if mode > 0` guard, 6018). Local serial jobs are already blocking.
- **mode > 0**: builds `update_status`/`update_first` lambdas (force=False vs True) that call `self.update_status((idle,run,finish,run_type), ...)` only if `html`; then `self.cluster.wait(self.me_dir, update_status, update_first=...)` (6030) — this is the polling loop owned by the Cluster backend (see cluster-submission-backends page).
- **Cluster-error handling** (6031-6045): on any exception from `wait`, if not forced asks `'Cluster Error detected. Do you want to clean the queue? ("c"=continue)'` (default 'y'); `'y'` -> `cluster.remove()` then re-raise; `'c'` -> recurse into `monitor` (retry the wait); KeyboardInterrupt -> `cluster.remove()` + re-raise. Forced runs auto-answer 'y' (clean + raise).

So `monitor(..., html=True)` is what every stage (survey 3561, refine 3714, restart_gridpack) uses to block on submitted jobs and stream the Idle/Running/Completed line.

## update_status (CR 3963-3994) — the index/HTML status writer
`update_status(status, level, makehtml=True, force=True, error=False, starttime=None, update_results=True, print_log=True)`.
- **Rate-limit throttle** (3968-3972): when `makehtml and not force`, returns early if `time.time() < self.next_update`; else sets `next_update = now + <interval>`. So non-forced HTML status updates are rate-limited to one per throttle interval (interval literal at 3968-3972 — read fresh). Forced calls (e.g. `update_first`) bypass.
- **Log line** (3974-3983): str status -> `logger.info` (unless it contains `<br>`); tuple status with `starttime` -> ` Idle: %s, Running: %s, Completed: %s [ <timer> ]`; tuple without starttime -> same minus timer. This is the live progress line during a cluster wait.
- Strips ANSI color prefixes (3985-3986) and trailing arXiv citation text (3987-3991) before storing.
- `update_results` -> `self.results.update(status, level, makehtml, error)` (3994) — writes the HTML index entry (gen_crossxhtml). `level` tags the pipeline stage ('parton','pythia',...).

## GridPackCmd.update_status (ME 7009-7010) — SILENT override
`GridPackCmd` (ME 6980, the class used inside a running gridpack) overrides `update_status` to a bare `return`. So a **gridpack run produces no status logging / no HTML index updates** — it runs silently. `GridPackCmd.__init__` also forces `self.cluster_mode = 0` (ME 7145, "force single machine"): a gridpack always runs single-core locally regardless of run_mode. Pairs with the gridpack-create page's note that gridpack integration quality is hardcoded.

## add_error_log_in_html (CR 3898-3923) — the debug-log hook
On a ME error, if a run is current, sets `self.debug_output = <me_dir>/<name>_<tag>_debug.log` and records it on `results.current.debug` (3906-3912) so the HTML shows a debug link; symlinks `ME5_debug` -> that path (3917-3923). Deliberately catches all internal errors (comment: "Be very careful to not raise any error here"). This is why a failed run leaves a `<run>_<tag>_debug.log` and an `ME5_debug` symlink at me_dir root.

## do_quit (CR 3926-3947) — RunWeb cleanup + final store
`quit`/`exit`/`EOF` alias. Removes `RunWeb` (unless `force_run`), calls `store_result()` (final archive), `update_status('', level=None)`, `gen_card_html()` (refresh index.html), then the cmd-superclass quit. `__del__` (3953-3960) also tries to remove `RunWeb`. So the per-run-directory lock file `RunWeb` is the "a run is in progress" marker, cleaned at quit.

## keep_cards (CR 3997-4020) — dot-prefix card hiding
Given the `need_card` list `ask_run_configuration` built from the switch, for each known optional card (pythia/pgs/delphes/madspin/reweight/shower/madanalysis/plot/rivet): if NOT needed, `mv card -> .card` (hide with dot prefix); if needed and absent, restore from `.card` or copy `<card>_default.dat`. So toggling off a downstream tool **hides** its card (renames to dotfile), it is not deleted — re-enabling restores it. `do_banner_run` instead deletes these cards outright before re-splitting the banner (launch-entrypoints page).

## print_results_in_shell (ME 2811-2881) — the "=== Results Summary ===" block
Takes a `gen_crossxhtml.OneTagResults`.
- **Per-channel run statistics** (2818-2834): aggregates each G-dir's `RunStatistics`, logs each at level 5 (debug) or 10 (warning if `has_warning()`), then a combined warning text. This is where channel-level integration warnings surface to the user.
- **The headline** (2843-2847): `ninitial==1` -> `Width : %.4g +- %.4g GeV`; else `Cross-section : %.4g +- %.4g pb`. Then `Nb of events`. So a 1->N (decay) launch prints a **width**, an N->M launch prints a **cross-section**, from the same code path.
- **Pythia-merged** (2849-2879): if `cross_pythia` set, prints matched width/xsec or, for `cross_pythia == -1`, reads `<tag>_merged_xsecs.txt` and prints per-merging-scale cross-sections; notes the use_syst-modifies-weights caveat for matched samples.
- `print_results_in_file` (2883+) is the file-writing twin.
- User-facing reprint command is `do_print_results` (CR 2532-2579, run-management-commands page): dispatches here per stored OneTagResults; no-arg dumps every run/tag.

## store_result (ME 5783-5840) — the to_store archiver
Distinct from `do_store_events` (parton-level, combine-store page). Driven by the `self.to_store` list: gzips `unweighted_events.lhe` if not already, removes stray `reweight.lhe`, tars `pythia_events.hep`/`pythia8` hepmc into the run dir (with optional remove/compress/move HEPMC sub-flags), then `results.save()` and clears `to_store`. `do_combine_events` appends `'event'` to `to_store`; `do_quit` calls `store_result` at exit. So final LHE gzip + pythia archiving is lazy, flushed at store_result/quit.

## Cautions
- A gridpack run is **silent by design** (GridPackCmd.update_status no-op) and **always single-core** (cluster_mode=0 forced) — do not expect HTML/status output or cluster parallelism from inside gridpack event generation.
- `update_status`'s throttle (interval at CR 3968-3972) means non-forced HTML updates can lag actual job state by up to one interval; the Idle/Running/Completed line is not real-time.
- `keep_cards` hides (not deletes) deselected cards as `.card` dotfiles; a "missing" pythia/delphes card after a parton-only run is hidden, recoverable by re-selecting the tool. (Contrast `do_banner_run`, which deletes them.)
- The shell headline says "Width ... GeV" for `ninitial==1` and "Cross-section ... pb" otherwise — same OneTagResults, branch on ninitial. A decay-process launch reporting "Width" is expected, not a mislabel.
