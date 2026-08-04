---
description: extended_cmd.py command-loop machinery — class stack (OriginalCmd/BasicCmd/Cmd), onecmd error-wrapping + exception taxonomy (InvalidCmd/ConfigurationError alias trap, crash_on_error, nice_*_error), precmd line splitting/comments/continuation, do_history/do_quit/do_help, exec_cmd vs onecmd_orig.
---

# Command-loop machinery (`extended_cmd.py`)

All MG5/madevent REPLs descend from `Cmd` here. File: `$MADGRAPH_INSTALL/madgraph/interface/extended_cmd.py`.

## Class stack
- `OriginalCmd` (84) — verbatim copy of stdlib `cmd.Cmd` (line-oriented loop, `parseline`, `onecmd`, `complete`). Pure base, no MG features.
- `BasicCmd(OriginalCmd)` (486) — readline layer: category-aware completion (`deal_multiple_categories` 502, `print_suggestions` 546, `getTerminalSize` 590), the real `complete` (614) with `;`/`-`/`=`/`:`/`\ ` split handling, static helpers `split_arg` (687), `list_completion` (709), `path_completion` (724).
- `CheckCmd` (773) / `HelpCmd` (810) / `CompleteCmd` (841) — mixins for `check_*` / `help_*` / `complete_*`.
- `Cmd(CheckCmd, HelpCmd, CompleteCmd, BasicCmd)` (883) — the combination class; base for every interface. Defines `InvalidCmd`/`ConfigurationError` exceptions (896-900), plugin_path (911-927), history, line-splitting.
- `CmdShell(Cmd)` (2086) — interactive shell variant (adds `do_shell`).

## Dispatch / error wrapping
- `parseline` (206, inherited) splits `cmd`+`arg`; `?`→help, `!`→shell.
- `onecmd` (1566): wraps `onecmd_orig` in `try/except BaseException` → `error_handling`. This is the catch-all.
- `onecmd_orig` (1491): the real dispatch — expands `~/` and `$VARS`, strips `#` comments, `getattr(self,'do_'+cmd)`, falls to `default` if missing. Passes `**opt` (internal calls).
- `error_handling` (1521): re-raises and re-catches by type. `InvalidCmd`→`nice_error_handling`(debug)/`nice_user_error`; `ConfigurationError`→`nice_config_error`; generic `Exception`→`nice_error_handling` AND `do_quit('')` if `self.mother` set (child interfaces die on unexpected error); `KeyboardInterrupt`→`stop_on_keyboard_stop`+msg. Returns `stop`; if stop truthy → `do_quit('all')`. Note `InvalidCmd` pops the offending line off history (1534, only in `__debug__`).

## Exception classes + the InvalidCmd/ConfigurationError alias trap
- `TimeOutError(Exception)` (58); `NotValidInput(Exception)` (2121, used by ControlSwitch); base `Cmd.InvalidCmd(Exception)` nested at 896.
- KEY: in the BASE `Cmd`, `ConfigurationError = InvalidCmd` (900) — the SAME class. So in the base class the `except self.ConfigurationError` clause (1542) is dead: `except self.InvalidCmd` (1531) catches first. The `nice_config_error` branch only fires because EVERY real interface OVERRIDES both names to distinct classes: `madgraph_interface` (158-159) sets `InvalidCmd = madgraph.InvalidCmd`, `ConfigurationError = MadGraph5Error`; same in `madevent_interface` (127-128) and `madweight_interface` (104); `amcatnlo_run_interface` (224) uses `aMCatNLOError`. `MadGraph5Error(Exception)` (`madgraph/__init__.py:16`) is independent of `InvalidCmd`. NET: in the running interfaces the two branches genuinely diverge — a `MadGraph5Error`/`aMCatNLOError` routes to `nice_config_error` (writes debug file), an `InvalidCmd` routes to user/debug handling.
- `nice_user_error` (1398) / `nice_config_error` (1435): both chdir to `__initpos`, recurse into `self.child` first. `nice_config_error` is the heavy one — it writes the debug file via `super().onecmd('history <debug_output>')` (full history) + `traceback.print_exc` (1447-1449).
- `crash_on_error` option gates the return in ALL THREE handlers — and the `True` ACTION differs by handler (verified this input):
  - `nice_error_handling` (1375-1381, the generic-`Exception`/`__debug__`-InvalidCmd handler): `True` → `raise` (RE-RAISES the current exception; the `sys.exit(str(error))` on 1379 is DEAD — after `raise`). Uncaught re-raise → Python exits non-zero (traceback). `'never'` → `return False`. Note: no `history.pop()` in the 'never' branch here (unlike the other two).
  - `nice_user_error` (1413-1419, the non-`__debug__` InvalidCmd handler): `True` → `sys.exit(str(error))` (string arg → exit code 1). `'never'` → `self.history.pop()`; `return False`.
  - `nice_config_error` (1465-1472, the `ConfigurationError`/`MadGraph5Error` handler): `True` → `sys.exit(str(error))`. `'never'` → `history.pop()` if history; `return False`.
  - NET: `crash_on_error=True` → HARD non-zero exit on ANY caught error (via `raise` or `sys.exit(str)`), ignores interactive/script state. `'never'` → swallow + continue (return False) in EVERY mode incl. script/`-f` — genuinely "never crash, never stop". Setter docstring (madgraph_interface 8673): "if crash_on_error is True, the code will stop with a non zero exit code."
  - WHICH handler an InvalidCmd hits is `__debug__`-gated (error_handling 1531-1536): release run under `python -O` (`__debug__`==False) → `nice_user_error` (True→sys.exit(str)); dev checkout / `--debug` (`__debug__`==True) → `nice_error_handling` (True→raise, + history.pop at 1534). Both non-zero, different mechanism. (See optimize-mode-debug-divergence.md.)
- Default (`False`, neither True nor 'never'): falls through the gate to the non-interactive check — if `use_rawinput==False or self.inputfile` (or a mother chain in that mode), the handler returns True → `stop` → `do_quit('all')` — a CLEAN stop of the loop (typically exit 0), NOT a crash. So in script/`-f` mode a default-False error ABORTS the run cleanly; interactively it pops history and continues at the prompt. This is the "may exit 0 / continue silently after a crash" default behavior. (Couples to script-mode-answer-resolution.md.)
- `exec_cmd` forces the wrapped path when `crash_on_error=='never'` (1594-1596): a third-party `exec_cmd` that would otherwise use raw `onecmd_orig` (errors propagate to caller) instead routes through `onecmd` (try/except swallow) — so 'never' guarantees even internal calls don't crash.

## do_history (1628), do_quit (1808)
- `do_history` (1628): no arg → log history; `clean` → empty it; `.` → write `$_export_dir/Cards/proc_card_mg5.dat`; else `<file>`. Prepends `get_history_header()`. `avoid_history_duplicate` (1667) prunes repeated trailing lines (used so re-running a command doesn't bloat history).
- `do_quit` (1808, aliased `do_EOF`/`do_exit`): cascade — if `self.child`, forward `quit <line>` to child and return; elif `self.mother`, detach (`mother.child=None`), `quit all` recurses up, numeric arg `N` climbs N levels; elif `self.inputfile`, drain + warn `command not executed: <line>` for each leftover script line. Returns True (stops the loop). (The child-first-then-unwind-up direction is the interface-stack-chain.md invariant; error handlers recurse the same way.)
- `default` (1614): logs "Command ... not recognized"; special-cases `q/.q/stop`→hint to type "exit".
- `cmdloop` (961, Cmd's own): wraps `precmd`+`onecmd` in `try/except BaseException`→`error_handling`; `postcmd` in `finally`.

## cmdloop / preloop / postloop lifecycle (961 / 946 / 1743)
The full loop body, beyond the error-wrapping noted above:
- `cmdloop` (961): calls `preloop()`, prints `intro` if set, then loops `while not stop`. Line source PRIORITY: `self.cmdqueue` (pre-seeded command list) FIRST (970-972), else interactive `input(self.prompt)` if `use_rawinput` (974-978), else `sys.stdin.readline()` (non-rawinput, 980-986) with `''`→`'EOF'` and a `\n` chop. So a parent can pre-load commands into `cmdqueue` to drive a child loop. Each iteration: `precmd`→`onecmd`, exceptions to `error_handling` (`KeyboardInterrupt` ALSO forces `stop=True`, 992-993), and `postcmd(stop,line)` in `finally` — postcmd's RETURN replaces `stop` (995). Ends with `postloop()`.
- `preloop` (946): saves `self.old_completer = readline.get_completer()` (951) THEN installs `self.complete` + binds `completekey: complete` + the `print_suggestions` display hook (libedit-guarded). So entering a loop swaps the readline completer IN.
- `postloop` (1743): RESTORES `readline.set_completer(self.old_completer)` and `del`s it (1746-1754) — the counterpart to preloop's save. So a nested child interface's cmdloop restores the PARENT's completer on exit (an interface-stack-chain.md coupling). THEN it reads `self.lastcmd`: if it was `quit/exit ... all`, or `quit N` with N not in `['0','1']`, returns True — propagating the stop UP the enclosing cmdloop chain (the loop-side of `do_quit`'s "climb N levels"). Returns False otherwise.
- `no_notification` (998): sets `allow_notification_center=False` and forces `automatic_html_opening`/`notification_center` options off — a hook used to silence a child run's HTML/notification side effects.
- `SmartQuestion.cmdloop` (2338) just runs the base loop and `return self.answer` — this is how `smart_input` (2343) extracts the answer from the loop.
- `emptyline` (1610): overridden to `pass` (stdlib default would REPEAT the previous command; MG5 deliberately does nothing on a blank line). `default` (1614) self-pops history if the faulty line equals the last history entry (1624-1625).

## madgraph `do_quit` override (madgraph_interface 3215) — auto-update-on-exit
The LO interface's `do_quit` wraps the base cascade: removes a stale `RunWeb` lock from the last export dir, calls `super().do_quit(line)` (the extended_cmd cascade above), THEN — gated by `madgraph.ReadWrite` (`madgraph/__init__.py:40` = `os.access(MG5DIR, os.W_OK)`, i.e. install dir writable) — fires `self.do_install('update --mode=mg5_end')` (3224), and `misc.EasterEgg('quit')`. This is SYMMETRIC with a startup `do_install('update --mode=mg5_start')` (3144). NET: quitting MG5 from a writable install triggers the auto-update timestamp check (consequence — whether it actually fetches, gated by `auto_update` interval — is do_install's, out-of-slice). On a read-only install the update call is skipped entirely. (Probe: trivial `import model sm` script quit emitted no visible update output — within-interval no-op, as expected.)

## precmd — the MG line preprocessing (1009)
Runs before dispatch on the interactive path:
- line continuation: trailing `\` stored in `self.save_line`, returns `''` (1024).
- comment removal: everything after `#` dropped (1029).
- `;` splitting (1033): each subline run via `onecmd_orig`+`postcmd` inline, then returns `''`. NOTE this path bypasses the `onecmd` error wrapper for sublines.
- appends line to `self.history` (skips `history`/`help`/`#*` lines).

## exec_cmd / run_cmd (third-party entry)
- `exec_cmd` (1579): the internal call API. `printcmd` logs the line; routes to `self.child` if a child interface exists. Honors `crash_on_error=='never'` → uses wrapped `onecmd`; else uses raw `Cmd.onecmd_orig` (so errors propagate to caller). `precmd`/`postcmd` toggleable.
- `run_cmd` (1604): `exec_cmd(line, errorhandling=True, precmd=True)` — used by `bin/mg5_aMC` script mode (`run_cmd('import file')`).

## CmdFile (3334)
`CmdFile(file)` — file-as-cmd-source for `import command`. Reads whole file at init, `readline` re-adds missing `\n`. CAUTION: subclasses the Py2 `file` builtin — only used where `file` is shimmed.

## post_<cmd> hooks
`postcmd` (1047) dispatches to `post_<cmd>(stop, subline)` if defined (e.g. `post_set`). This is how `do_set` persistence is triggered.

## Base meta-commands (extended_cmd, inherited by all interfaces)
- `do_help` (1833): with an arg → defers to stdlib `super().do_help`. With NO arg → builds the categorized command listing (tag = text before first `:` in each docstring, ordered by `self.helporder`), THEN appends **Contextual Help**: walks `self.history` backward to find the last action, looks it up in `self.next_possibility` dict, and prints "The following command(s) may be useful in order to continue". So `help` alone is history-aware. `next_possibility` is per-interface (defined in madgraph_interface/madevent_interface).
- `do_display` (1918, base): `options` → dumps `self.options` as `name : value`; `variable <expr>` → eval's expr as GLOBAL/LOCAL/EXTERNAL and pages via `pydoc.pager`. (madgraph_interface 3566 and madevent_interface 2212 override/extend this — `display options` on config-system.md, `display variable` on meta-commands-introspection.md.)
- `do_save` (1974, base): saves the configuration file. The richer per-interface `do_save options` tier logic lives in the overrides (config-system page).
