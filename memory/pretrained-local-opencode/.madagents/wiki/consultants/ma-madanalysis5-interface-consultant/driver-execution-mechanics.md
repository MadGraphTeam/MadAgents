---
description: run_madanalysis5 execution-loop internals — runMA5 controlled-env wrapper, per-runtag interpreter re-init, stdout-lvl precedence, error skip-vs-abort flow, ask_madanalysis5_run_configuration.
---

# MA5 driver execution mechanics (v3.7.1)

Covers the runtime layer of `run_madanalysis5` (common_run_interface.py:3102) that the invocation-flow page stops short of: the per-runtag loop body, the `runMA5` wrapper, and the user-side card-ask. All file:line refs are common_run_interface.py unless noted.

## stdout-level precedence chain (3193-3199)
`check_madanalysis5` seeds `MA5_options['MA5_stdout_lvl']='default'` (2713). Resolution at run time:
- If `MA5_opts['MA5_stdout_lvl']=='default'` (i.e. user gave no `--MA5_stdout_lvl=`):
  - if card's `stdout_lvl` is None -> `MA5_lvl = self.options['stdout_level']` (the global MG verbosity).
  - else `MA5_lvl = MA5_card['stdout_lvl']` (the card's `@MG5aMC stdout_lvl=...`).
- Else (user passed `--MA5_stdout_lvl=`) -> that value wins.
So precedence is: CLI flag > card stdout_lvl > global stdout_level.

## Interpreter acquisition guard (3202-3219)
`get_MadAnalysis5_interpreter(...)` called with `forced=True, compilation=True, loglevel=100`.
- `except SystemExit: return` and `except Exception: logger.warning("MA5 fails with: ..."); return` — interpreter-construction failure is a SILENT skip (just returns from run_madanalysis5), not a raise.
- `if MA5_interpreter is None: return` — same silent skip (get_MadAnalysis5_interpreter returns None on Py3-incompat / import failure; see invocation-flow page).

## Per-runtag loop re-initialisation (3224-3247)
For each `(MA5_runtag, MA5_cmds)` in the list, BEFORE running:
- `MA5_run_number` is hard-reset to 0 each iteration (comment: every run goes in a fresh folder, so it's always 0). Output-dir naming downstream relies on this `_0` suffix.
- `MA5_interpreter.setLogLevel(100)` — bypass the banner noise, then:
- hadron mode -> `MA5_interpreter.init_reco()`; parton mode -> `MA5_interpreter.init_parton()`. The interpreter is RE-INITIALISED on every runtag (the code comment notes they'd prefer one interpreter but lack a reset path).
- `MA5_interpreter.setLogLevel(MA5_lvl)` — restore the resolved level.
- runtag-specific INFO banner: `_reco_*` -> "running the reconstruction", `Recasting` -> "running the recasting", else "running the '<tag>' analysis"; `default` runtag stays silent.

## runMA5 controlled-environment wrapper (2607-2645, @staticmethod)
`runMA5(MA5_interpreter, MA5_cmds, MA5_runtag, logfile_path, advertise_log=True)`:
- Grabs `logging.getLogger('MA5')`, **backs up its handlers**, removes them all, attaches a fresh `FileHandler(logfile_path)` — so MA5's own logging is diverted to the per-runtag logfile while it runs.
- If `advertise_log`: prints "Follow Madanalysis5 run ... tail -f <logfile_path>".
- The actual call runs under nested `misc.stdchannel_redirected(sys.stdout, devnull)` and `(sys.stderr, devnull)` — BOTH stdout and stderr are silenced to /dev/null. Then `MA5_interpreter.print_banner()` + `MA5_interpreter.load(MA5_cmds)`.
- `except Exception`: logs WARNING "MadAnalysis5 failed to run the commands for task '<tag>'. ... will be skipped.", dumps the traceback at DEBUG level, sets `successfull_MA5_run=False`. Caught — does not propagate.
- `finally`: removes the FileHandler and **restores the backed-up handlers** (logger always left clean).
- Returns the success bool.

## Error skip-vs-abort flow (caller, 3251-3254)
`if not CommonRunCmd.runMA5(...): return` — a failed runtag ABORTS the whole MA5 step (returns from run_madanalysis5); remaining runtags in the list are NOT attempted. So one failing analysis/reco/recast stops the rest. Contrast: missing PDF (3310-3322) only `logger.error('MadAnalysis5 failed to create PDF output')` and continues (non-fatal); missing analysis dir (3332-3335) logs error + returns. BUT one post-success path hard-RAISES, not returns: in the `_reco_*` handler, if the reconstructed event file (`*.lhe.gz`/`*.root` under `<reco_output>/Output/SAF/_reco_events/...`) is absent, `raise MadGraph5Error("...failed to produce the reconstructed event file...")` (3281-3282) — propagates out of run_madanalysis5, unconditionally (no no_default guard). See failure-handling-two-layers for why this is the one Layer-2 exception to quiet degradation.

## Logfile path (3252)
`Events/<run_name>/<run_tag>_MA5_<runtag>.log` — one logfile per runtag, the file `tail -f` points at.

## ask_madanalysis5_run_configuration (2863-2887) — user-issued path only
Called by run_madanalysis5 (3124) only when `--no_default` ABSENT (user ran the command, not generate_events):
- `cards = ['madanalysis5_<runtype>_card.dat']`; `self.keep_cards(cards)`.
- `if self.force: return runtype` — `-f` / force mode skips the editor entirely.
- `mode=='auto'` (set by `auto=True`) -> `ask_edit_cards(cards, mode='auto', plot=False)`; else `ask_edit_cards(cards, plot=False)`. Structure deliberately mirrors `ask_pythia_configuration`.
- Returns the runtype (no further info passed back). Net effect: surfaces the MA5 card editor before the analysis runs.

## post-loop bookkeeping (3340-3357)
After all runtags: copies last sub-run's `nb_event`/`cross`/`error` from `results[run_name].get_current_info()` into the run details (comment: "maybe do something smarter later" — it just takes the LAST sub-run's numbers). Then `update_status('Finished MA5 analyses.')`, folds the card into the banner (`banner.add(... madanalysis5_<mode>_card.dat)`) and writes `<run>_<tag>_banner.txt`.

## Cautions
- A single failing runtag silently aborts every later runtag (3251-3254) — partial analyses possible with no hard error, only a WARNING in the log.
- MA5's stdout/stderr are fully redirected to /dev/null during `load`; the ONLY visible trace of an MA5-internal problem is the per-runtag logfile + the caught-exception WARNING. Runtime claim — not separately probed here.
- The cross-section/nb_event written back to results are the LAST sub-run's, not aggregated across runtags.
