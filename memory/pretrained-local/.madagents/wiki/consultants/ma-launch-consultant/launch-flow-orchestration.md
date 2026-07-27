---
description: LO launch end-to-end flow — do_launch -> do_generate_events -> run_generate_events stage sequence (survey/refine/combine/store/decay/shower), gridpack-warmup branch, zero-xsec handling.
---

# LO launch orchestration (madevent_interface.py)

All file:line cites are `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (v3.7.1) unless noted.

## Entry chain
- `do_launch` (2754): for `ninitial==1` prints a note that since 2.3 `launch` of 1>N goes through event generation (the `calculate_decay_widths` path is commented out). Then unconditionally calls `do_generate_events(line,...)` (2762). So `launch` == `generate_events` for LO; width path requires explicit `calculate_decay_widths` (madwidth slice).
- `do_generate_events` (2383): resets `self.banner=None`, `self.Gdirs=None`; `check_generate_events(args)` -> mode; `ask_run_configuration(mode,args)` -> `switch_mode`; loads a throwaway `RunCard(consistency=False)` with `allow_scan=True` (2393-2394) only to test `run_card.scan_set`. If NOT a scan, assigns/sets run name (2395-2401). Then `run_generate_events(switch_mode,args)` (2404) and `postprocessing()` (2406).
- `postprocessing` (2411): only Rivet/Contur postprocessing after all generation (incl. scan loop). Not the core xsec path.

## run_generate_events (2565-2677) — `@scanparamcardhandling(run_card_scan=True)` decorated (handles scan loop)
- Loop-induced + `run_mode==0`: forces `run_mode 2` / `nb_core 1` with a warning — single-core unsupported for loop-induced (2567-2574).
- **Gridpack-warmup branch** (`run_card['gridpack'] in self.true`, 2576-2592):
  - Gridpack survey opts are **hardcoded** at 2578-2581 (accuracy / points / iterations, plus `gridpack='.true.'`) — read the literals there; they override the `_survey_options` defaults registered at line 2053. (Values are drift-prone; the fact that gridpack warmup uses a fixed hardcoded set, not run_card survey settings, is the stable point.)
  - Sequence: `survey <run> --accuracy=.. --points=.. --iterations=.. --gridpack=.true.` -> `combine_events` -> `store_events` -> `decay_events -from_cards` -> `create_gridpack`. NO refine in this branch.
- **Regular branch** (2593-2671):
  1. `survey <run> <args>` (2597).
  2. `refine <nevents>` (2601).
  3. Zero-xsec check: if `float(self.results.current['cross'])` is 0 -> critical text listing typical causes (zero-width s-channel, zero PDF / maxjetflavor=4 for initial b, too-strong cuts) (2604-2611). If not in a param scan, raises `ZeroResult`; if scanning, sets `bypass_run=True` (2612-2615).
  4. Second refine `refine <nevents> --treshold=<second_refine_treshold>` (2619) — gated by `do_refine` threshold logic (see survey-refine-and-thresholds page).
  5. `combine_events` (2622), then `print_results_in_shell` (2623).
  6. Systematics (2625-2647): chooses `systematics` vs `syscalc` vs `none` from `use_syst`/`systematics_program`. (systematics slice owns internals.)
  7. `create_plot('parton')` (2650), `store_events` (2651), then `boost_events()` if `run_card['boost_event'].strip() and != 'False'` (2652-2653) — the call-site guard, NOT just truthiness; see event-postprocessing-stages page.
  8. `reweight -from_cards` (2656), `decay_events -from_cards` (2657), then `add_time_of_flight --threshold=<time_of_flight>` if `run_card['time_of_flight']>=0` (2658-2659) — runs AFTER decay so it stamps decayed daughters; see event-postprocessing-stages page.
  9. ExRoot root file if `switch_mode['analysis']=='ExRoot'` (2661-2664).
  10. `madanalysis5_parton`, `shower` (shower launches pgs/delphes), `madanalysis5_hadron`, `rivet` — all `--no_default` (2666-2670); `store_result()` (2671).
- system_notify at end if enabled (2673-2677).

## Stage commands (each a do_*)
- `do_survey` (3484): see survey-refine-and-thresholds page.
- `do_refine` (3605): see survey-refine-and-thresholds page.
- `do_multi_run` (3084-3171): `check_multi_run` converts arg[0] to int (1266), so `nb_run` is a true int; `nb_run==1` warns "not optimal, use generate_events" (3091). One `ask_run_configuration` for the whole batch. Loop `i in range(nb_run)`: `exec_cmd('generate_events <main>_<i> -f', postcmd=False)` (3108), then accumulates:
  - `nb_event += results[run][-1]['nb_event']` (3110-3111);
  - **inverse-variance weighting** (3113-3117): `crossoversig += cross/error**2`, `inv_sq_err += 1/error**2`, then `main['cross'] = crossoversig/inv_sq_err`, `main['error'] = sqrt(1/inv_sq_err)`. So the combined xsec is the error-weighted mean across sub-runs, NOT a simple average. `error += 1e-99` guards div-by-zero (3113).
  - tracks `madspin` if any sub-run name contains 'decayed' (3118-3119).
  - Merges all sub-run LHE via `bin/merge.pl <name>_*[_decayed_*]/unweighted_events.lhe.gz -> <name>/unweighted_events.lhe.gz` + a `<name>_banner.txt` (3128-3132); the `_decayed_*` glob is injected only when madspin ran. Then ExRoot/create_plot/gzip, `print_results_in_shell`.
  - **param scan** (3158-3171): if a `param_card_iterator` exists, stores the current xsec, then for each scan card writes param_card and recursively `exec_cmd("multi_run <nb_run> -f")`; finally writes `Events/scan_<name>.txt` summary via `param_card_iterator.write_summary`. So a scanned multi_run produces one scan summary file across all points.

## Run-dir naming + inline-set timing (install smoke-test)
- Run name: `find_available_run_name` (`common_run_interface.py:4158-4166`) = `run_%02d` over `max(existing_ints+[0])+1`. First run in a fresh `output` dir -> `run_01`; events land in `<PROC_DIR>/Events/run_01/`. Assigned at do_generate_events 2398/2400 (unnamed -> find_available_run_name; named arg -> set_run_name(args[0])).
- Inline `set run_card ebeam1 45.6 / lpp1 0 / nevents 100 / done` in the launch dialog: handled by `AskforEditCard.do_set` (`common_run_interface.py:5868`) which mutates the in-memory RunCard and tracks `modified_card`; on `done`/`0`/empty the question ends (`postcmd` 6793-6799) and every modified card is flushed via `write_card` (6783). run_card.dat is thus rewritten BEFORE the run proceeds; the subsequent survey's treatcards reads the edited run_card.dat -> run.inc. So inline edits are applied before survey/refine. `done` (equiv `0`/empty) is the dialog terminator.
- Entry points: top-level `$MADGRAPH_INSTALL/bin/mg5_aMC` is the REPL frontend only (verified: sole file in top-level `bin/`). `madevent`/`generate_events` are per-process, copied from `Template/LO/bin/` into `<PROC_DIR>/bin/` at output time (see launch-entrypoints-and-html). No top-level `bin/madevent`.

## Cautions
- The gridpack branch silently uses different (tighter) integration opts than a normal run and skips refine; a gridpack's accuracy is governed by the hardcoded 0.01, not the run_card.
- Zero survey cross-section raises hard (ZeroResult) outside a scan but is silently bypassed inside a scan — a scan can complete with zero-xsec points.
