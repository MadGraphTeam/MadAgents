---
description: How MG5_aMC invokes MadAnalysis5 (parton & hadron) — entry points, the shared run_madanalysis5 driver, and the generate_events dispatch chain.
---

# MG -> MA5 invocation flow (v3.7.1)

## Entry points (both delegate to one shared driver)
- `do_madanalysis5_parton(self, line)` — `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py:4226`; body is `return self.run_madanalysis5(line, mode='parton')`.
- `do_madanalysis5_hadron(self, line)` — `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py:3096`; body is `return self.run_madanalysis5(line, mode='hadron')`.
- The single implementation `run_madanalysis5(self, line, mode='parton')` lives ONLY in `common_run_interface.py:3102`. There is no parton-specific copy; `mode` is the only difference. (The card-card comment "launch ... at the parton level" on the parton entry is stale wording.)

## Dispatch from generate_events
`madevent_interface.py:2666-2669` runs, in order, inside the generate_events finalisation:
```
self.exec_cmd('madanalysis5_parton --no_default', ...)
self.exec_cmd('shower --no_default', ...)           # pgs/delphes
self.exec_cmd('madanalysis5_hadron --no_default', ...)
self.exec_cmd('rivet --no_default', ...)
```
So parton MA5 runs on the LHE BEFORE the shower; hadron MA5 runs AFTER shower/detector. `--no_default` = "MG triggered me, not the user."

## `--no_default` semantics (run_madanalysis5, common_run_interface.py:3108-3134)
- `--no_default` present -> `no_default=True`. If the matching `Cards/madanalysis5_<mode>_card.dat` is absent, returns silently (3116-3121). Used by generate_events so a missing card is a silent skip, not an error.
- `--no_default` absent (user-issued) -> calls `ask_madanalysis5_run_configuration(runtype=mode)` (3125) to let the user edit the card, then runs.
- If `madanalysis5_path` unset OR neither MA5 card present: silent return under no_default; otherwise raises `InvalidCmd("You must have MadAnalysis5 available ...")` (3133).

## MELauncher (launch_ext_program.py) does NOT call MA5 directly
`MELauncher.launch_program` (`launch_ext_program.py:614`) only issues `generate_events <name>` to a child MadEventCmd (`:671,:699`). The MA5 step fires inside that child's generate_events (above), not in the launcher. The launcher has zero MA5 references.

## After the card is loaded (run_madanalysis5 continued)
- `check_madanalysis5(args, mode)` resolves inputs and run/tag (see input-resolution-and-cmds page).
- `MA5_card = MadAnalysis5Card(Cards/madanalysis5_<mode>_card.dat, mode=mode)` (3156).
- If `MA5_card._skip_analysis`: logs "skipped following user request" and returns (3159-3164).
- Else `MA5_card.get_MA5_cmds(...)` builds `[(runtag,[cmds])]`; an MA5 interpreter is obtained via `get_MadAnalysis5_interpreter` (3203) and each runtag executed via `runMA5` (3251).

## get_MadAnalysis5_interpreter (common_run_interface.py:2651-2706)
TWO callers: (1) run_madanalysis5 at RUN time (3203); (2) `create_default_madanalysis5_cards` at OUTPUT/export time (export_v4.py:455) to write the per-process default cards — see output-time-card-creation page. Both pass NO `mg5_interface`.
- Builds `MA5path = normpath(mg5_path/ma5_path)`; returns None immediately if `<MA5path>/bin/ma5` missing (2658). Inserts MA5path into `sys.path` (2660).
- READLINE BACKUP (2662-2670): saves `readline` completer / delims / history BEFORE import, because MA5 importing ROOT supersedes MG5 autocompletion; the `finally` block (2691-2706) restores them. Caution: side-effecting MG5's readline state is a real coupling, restored only via finally.
- READLINE DISPLAY-HOOK restore is CONDITIONAL on `mg5_interface` being passed (2705-2706): `if not mg5_interface is None and any(... [old_completer,old_delims,old_history]): mg5_interface.set_readline_completion_display_matches_hook()`. That method lives at `extended_cmd.py:489` (`BasicCmd.set_readline_completion_display_matches_hook`), refactored there "so that it can be called when another program called by MG5 (such as MadAnalysis5) changes this attribute of readline" (extended_cmd.py:490-491) — the OTHER side of this coupling.
- BUT the run-time caller `run_madanalysis5` (3203) does NOT pass `mg5_interface` (only positional `mg5_path`, `madanalysis5_path`, then kwargs), so `mg5_interface=None` -> the display-hook restore branch is SKIPPED during a normal generate_events MA5 run. Completer/delims/history ARE restored; the completion_display_matches_hook is not. (The output-time caller export_v4.py:455 also passes no mg5_interface.) Caution: the hook-restore exists in the helper but is dead on both actual call paths in this version.
- Imports `madanalysis.interpreter.ma5_interpreter.MA5Interpreter` and constructs it under stdout+stderr -> /dev/null (2672-2678).
- FAILURE BRANCH (2679-2691) is `__debug__`-gated: in optimised mode (`python -O`, `__debug__` False) it logs INFO "MadAnalysis5 instalation not python3 compatible" and returns None; in normal debug mode it logs WARNING "MadAnalysis5 failed to start so that MA5 analysis will be skipped." plus a DEBUG traceback. Either way -> None -> analysis skipped. All MA5-internal from here.

## Per-runtag execution + runMA5 wrapper
Once the interpreter is obtained, run_madanalysis5 loops the runtags, re-initialising the interpreter each time and calling the `runMA5` controlled-environment wrapper; a failing runtag aborts the rest. See the driver-execution-mechanics page for the full loop body, stdout-lvl precedence, and the user-side `ask_madanalysis5_run_configuration` card-edit flow.
