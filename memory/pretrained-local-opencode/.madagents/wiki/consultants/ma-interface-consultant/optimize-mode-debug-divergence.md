---
description: Installed releases run under python -O so __debug__==False — the cross-cutting principle — error/traceback/history/error-swallowing/menu behavior across extended_cmd.py diverges between a normal release run and a dev checkout / --debug.
---

# The `__debug__` / optimize-mode divergence (cross-cutting principle)

## Principle
A NORMAL installed MG5_aMC session runs under `python -O`, so the Python literal
`__debug__` is `False`. The launcher forces this: `bin/mg5_aMC:75-82` re-execs itself as
`python -O -W ignore... <argv>` and `sys.exit`s with the child's code UNLESS `--debug` is
given OR it is a dev checkout (`bin/create_release.py` present) and not `--web`. A dev tree
stays `__debug__==True` and prints "Running MG5 in debug mode" (`bin/mg5_aMC:137-138`).

CONSEQUENCE: every source branch guarded by `if __debug__:` is INACTIVE in a normal release
run and ACTIVE only in a dev checkout or under `--debug`. Reason about installed behavior as
`__debug__==False`. This principle predicts the divergence at ANY `__debug__` site, including
ones not enumerated here.

## The `__debug__` sites in `extended_cmd.py` (enumerate via grep `__debug__`)
1. **`debug()` decorator** (61-66): when `debug_only and not __debug__` the decorator returns
   `f` UNWRAPPED — `@debug` instrumentation is a no-op in release runs.
2. **BasicCmd completion redraw** (586-588): an exception while redrawing the prompt during
   completion is `logger.error`-logged only in debug; silent under `-O`.
3. **`nice_error_handling` traceback-to-screen** (1342-1343): the full `traceback.print_exc()`
   goes to SCREEN only in debug. Under `-O` the traceback is written ONLY to the debug file
   (1340) — the user sees just the one-line `"<cmd>" with error: InvalidCmd : ...`.
4. **`error_handling` InvalidCmd routing** (1532-1536): debug → `nice_error_handling` +
   `self.history.pop()` (the offending line is removed from history); release →
   `nice_user_error` (no pop). So the history-pop-on-InvalidCmd is a DEBUG-ONLY behavior.
5. **`error_handling` KeyboardInterrupt** (1556-1557): `nice_config_error` (writes a debug
   file) fires on Ctrl-C only in debug; release just logs the stop message.
6. **`SmartQuestion.onecmd`** (2222-2225): an exception raised by a command typed AT A QUESTION
   is `raise`d (propagates) in debug, but under `-O` is SWALLOWED with a bare `logger.warning`
   and the question continues. So a broken `do_X` inside a question widget fails LOUD in a dev
   tree and SILENT in a release.
7. **`ControlSwitch.create_question` hide_line** (3247-3263): a switch key in `self.hide_line`
   is SKIPPED entirely from the menu under `-O` (`if key in self.hide_line and not __debug__:
   continue`); in debug it is shown highlighted green. Hidden axes (e.g. dev/internal switches)
   appear in the AskRun menu only in a dev tree.

(Note `master_interface.debug_link_to_command` at 81 is also `__debug__`-gated — the
do_/check_/help_/complete_ wiring audit runs only in dev trees. Same principle, different file.)

## Probe-verified runtime divergence
Script `import model sm` then bare `generate` (raises `InvalidCmd: "add" requires at least two
arguments`):
- `bin/mg5_aMC -f` (release, `-O`): prints only `"generate" with error: InvalidCmd : ...` — NO
  Python traceback to screen.
- `bin/mg5_aMC --debug -f` (dev/debug): prints "Running MG5 in debug mode" + full
  `Traceback (most recent call last): ... madgraph.InvalidCmd: ...` to screen, THEN the user
  error. Confirms sites 3+4.

## Boundary
This is about Python's `__debug__` literal (toggled by `-O`), NOT runtime verbosity.
`--logging LEVEL` / `do_set stdout_level` / `do_tutorial` set logger levels at runtime and are
ORTHOGONAL to `__debug__`. (One coupling: under `__debug__`, an `INFO` `--logging` request is
bumped to `DEBUG` at `bin/mg5_aMC:143-144` — but that is the launcher reading `__debug__`, not
`__debug__` reading the log level.) Also out of scope: `--web` forces the re-exec ON even in a
dev checkout (76), so web mode always runs `-O`.

See also: launcher-entrypoint.md (the re-exec cause + CAUTION), command-loop-machinery.md
(sites 3-4 in the error-handling narrative).
