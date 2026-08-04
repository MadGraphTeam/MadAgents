---
description: bin/mg5_aMC entry-point launcher — optparse flags (-f/-m/--web/--debug/-s/--logging), the -O optimize re-exec, readline/mg5history persistence, logging fileConfig, and how it builds + drives the MasterCmd/plugin cmd object.
---

# Launcher entry point (`bin/mg5_aMC`)

File: `$MADGRAPH_INSTALL/bin/mg5_aMC`. Thin wrapper that builds the cmd object and drives it.
Plugin-LOADING internals (from_plugin_import, output plugin) are on master-multiplexer-plugins.md;
this page is the launcher's own flag/process/IO layer.

## optparse flags (62-67)
- `-f/--file FILE` — run a script file (`run_cmd('import FILE')`). Bare positional arg works too (`args[0]`).
- `-d/--mgme_dir DIR` — legacy MG_ME dir, passed to the cmd constructor.
- `--web` — secure web mode → builds `MasterCmdWeb()` (189); locks down installs/saves, forces timeout=1.
- `--debug` — force debug mode (skips the `-O` re-exec, raises logging to DEBUG).
- `-m/--mode NAME` — load PLUGIN `NAME` as the principal interface (see below).
- `-s/--nocaffeinate` — macOS: don't spawn `caffeinate` during a scripted run (default IS to caffeinate, 198-201).
- `--logging LEVEL` — DEBUG|INFO|...|CRITICAL or a digit; under `__debug__` an `INFO` request is bumped to DEBUG (143-144).

## The `-O` optimize re-exec (75-82) — non-obvious
If `__debug__` is true (i.e. NOT already running under `python -O`) AND `--debug` not given AND
this is not a dev checkout (`bin/create_release.py` absent) OR `--web`: the script RE-LAUNCHES
ITSELF as `python -O -W ignore::DeprecationWarning -W ignore::SyntaxWarning <argv>` and exits with
that child's return code. CONSEQUENCE: a normal install runs under `-O`, so `__debug__==False`
inside the real session — which is exactly the flag `error_handling`/`nice_user_error` branch on
(debug vs user error text, history.pop). A dev tree (has `create_release.py`) stays in `__debug__`
mode and prints "Running MG5 in debug mode" (137-138). This is why behavior differs between an
installed release and a git checkout.

## readline + persistent history (94-129, 232-239)
- Tries `readline` then `pyreadline`; binds tab-completion (`tab: complete`, or `bind ^I rl_complete`
  on libedit/old-mac).
- History file `mg5history` lives in `state_dir`: legacy `~/.mg5` if it exists, else
  `$XDG_STATE_HOME` else `~/.local/state` (119-126). Read at startup, and on exit
  `set_history_length(<cap>)` + `write_history_file` (234-236). So the up-arrow shell history is
  capped (limit read at bin/mg5_aMC:234-236) and survives across sessions — distinct from `self.history` (the in-session
  command list `do_history` writes, command-loop-machinery.md).

## logging (150-153)
`logging.config.fileConfig($MADGRAPH_INSTALL/madgraph/interface/.mg5_logging.conf)`, then sets the
`madgraph` and `madevent` logger levels. The `.mg5_logging.conf` file defines the per-logger
handlers/formatters; `do_set stdout_level` and `do_tutorial` adjust levels at runtime on top of this.

## cmd object construction (169-191)
- `-m NAME`: looks for `$MADGRAPH_INSTALL/PLUGIN/NAME` on disk; if absent tries
  `import MG5aMC_PLUGIN.NAME` (else "ERROR: ... not present in the PLUGIN directory" + exit). Requires
  `plugin.new_interface` truthy (else warn "should be used without the --mode options" + exit). Gated by
  `misc.is_plugin_supported(plugin)`. Builds `cmd_line = plugin.new_interface(mgme_dir=...)`,
  `cmd_line.plugin = NAME`.
- `--web`: `MasterCmdWeb()`.
- default: `MasterCmd(mgme_dir=...)`.

## drive (196-227)
- File/script mode (`options.file or args`): sets `use_rawinput=False`, `haspiping=False`, then
  `run_cmd('import '+input_file)` + `run_cmd('quit')`. (macOS spawns `caffeinate -i -w <pid>` unless `-s`.)
  This is the entry of the script-mode-answer-resolution chain. `--web` additionally sets
  `cmd_line.debug_output` next to the input file.
- Interactive: `cmd_line.cmdloop()` (web mode seeds MADGRAPH_DATA/BASE/REMOTE_USER env first).
- `EasterEgg('loading')` (164) at startup; `EasterEgg('error')` fires inside `error_handling` (extended_cmd 1527). `EasterEgg` (`various/misc.py:1913`) is COSMETIC-ONLY and date-gated: prints jokes on Apr 1 / special ASCII banners on May 4 + Oct 14, and is wrapped in a bare `try/except: pass` so it can never alter control flow. ONE non-cosmetic side effect — on Apr 1 (`date==(1,4)`) it sets `EpsDiagramDrawer.april_fool=True`, a global that flips the EPS diagram drawing (consequence is out of this slice). No-ops entirely when `MADEVENT` (standalone run-dir mode).

CAUTION: the `-O` re-exec means almost everything you reason about for an installed MG5 runs with
`__debug__==False`. Any source branch guarded by `if __debug__:` (history.pop on InvalidCmd, the
debug-mode error traceback, the slow-load warning) is INACTIVE in a normal release run and ACTIVE only
in a dev checkout or under `--debug`.
