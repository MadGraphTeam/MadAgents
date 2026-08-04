---
description: Non-interactive / script-mode answer-resolution as one mechanism — the do_import command entry (master vs base do_import MRO split), entry flags (use_rawinput/inputfile/haspiping), the import_command_file feed engine + stored_line re-feed loop, and the check_answer_in_input_file family. Generalizes the script-mode notes scattered on ask-question-widgets / controlswitch-widget / command-loop-machinery / config-system pages.
---

# Script-mode answer resolution (the unifying principle)

When MG5/madevent runs non-interactively, ONE mechanism resolves both commands and
question-answers from a line source. The instance pages document fragments; this page
names the whole. File: `$MADGRAPH_INSTALL/madgraph/interface/extended_cmd.py` unless noted.

## The switch: `use_rawinput=False` OR `self.inputfile` set
Two independent signals put the loop in non-interactive mode:
- `bin/mg5_aMC -f file` / `bin/mg5_aMC file`: sets `use_rawinput=False`, `haspiping=False`, then `run_cmd('import '+file)` (`bin/mg5_aMC:214-216`; `--web` branch is the same at 209-211).
- `import_command_file(filepath)` (1691): sets `self.inputfile = (l for l in commandline)` (a *generator*, deliberately not a list — file may be overwritten mid-run, 1709-1711) and `self.use_rawinput=False` (1707-1708), restoring both afterward (1728-1729).
- `haspiping = not sys.stdin.isatty()` (940) — set when stdin is a pipe even without `-f`.
Child question instances inherit it: `ask` propagates `inputfile`/`haspiping` onto the created widget (1077-1081, 1145-1147). So ANY widget reached in this mode — not only the `ask`/SmartQuestion/ControlSwitch instances the other pages name — resolves the same way.

## Layer 0 — the `do_import command` entry (which `do_import` you hit)
`import command <script>` reaches `import_command_file` through DIFFERENT `do_import` methods
depending on interface — a non-obvious MRO split:
- **MG5 (madgraph)**: master `do_import` (master_interface 280) → `self.cmd.do_import` →
  `MadGraphCmd.do_import` (madgraph 5753). Its `command` branch (5853-5862) checks the path,
  calls `check_for_export_dir(args[1])` (so a script can find an implicit export dir), then
  `import_command_file`. `_import_formats` (madgraph 3001) = `['model_v4','model','proc_v4',
  'command','banner']` — `import` here is overloaded (model-loader is out-of-slice; the
  `command`/`banner` branches are in-slice script entry).
- **madevent**: has NO `do_import` override, so `import command` falls through to the
  BASE-class `extended_cmd.do_import` (1195): `check_import(args)` then `import_command_file(args[1])`.
  `check_import` resolves by MRO to madevent's `CheckValidForCmd.check_import` (madevent 1652),
  NOT the base `check_import` (extended_cmd 1206) — which matters because the base one has a
  latent `raise '<string>'` bug (1217) and a `args.set(0,...)` call that would fail; madevent's
  override (`args.insert(0,'command')`, 1659) is the path actually taken. So the base
  `do_import`+`check_import` pair is reachable but its `check_import` is shadowed in every real
  interface.

## Layer 1 — command feed (`import_command_file`, 1691)
The engine driving an `import command <script>`. Reads all lines, iterates the generator,
runs each non-empty line via `exec_cmd(line, precmd=True)` (1718). After each command it
DRAINS stored lines (1719-1723): `while get_stored_line(): exec_cmd(stored, precmd=True)`.
Closes any open child with `exec_cmd('quit')` at end (1726-1727).

## Layer 2 — answer matching (`check_answer_in_input_file`, 1220)
Active only when `self.inputfile` set (1224). Pulls the next line, strips comments, matches
against `question_instance.allow_arg` (exact / `line;` / case-insensitive). A `do_X` line is
executed and the method recurses to the next line (1249/1261). Path mode accepts existing
file / URL. ControlSwitch overrides via `special_check_answer_in_input_file` (2518) — allows
`key=value` even when `check_value` is False (backing tool missing), stores a bare `set ...`
line for the mother.

## Layer 3 — the store-and-re-feed fallback (the missing half)
An UNMATCHED answer is NOT consumed. `check_answer_in_input_file` calls `store_line(line)`
and returns either `None` (piping: 1294-1295, falls through to print question + read pipe) or
`str(default)` (logs "Keep it for next question and use here default", 1298-1303).
`store_line`/`get_stored_line` (1304-1319) hold one line; `get_stored_line` walks up to
`self.mother` first (1315-1316) so a child interface's leftover bubbles to the parent loop.
That parent loop is `import_command_file`'s drain (1719-1723) — which re-feeds the stored
line as the NEXT command. So: a script line that fails to answer question N becomes a command
attempted after the command that posed N. This couples Layer 1 and Layer 2; documenting either
alone misses why a "wrong answer" can later surface as a "Command not recognized".

## Probe-confirmed runtime facts
- Script `display options` BEFORE any `import model` → `InvalidCmd: No model currently active` (preloop auto-import is skipped under `run_cmd('import file')`).
- A stray non-command line mid-script is fed to the command loop (`default` → "Command \"X\" not recognized, please try again") and execution continues to the next line.
- The Layer-3 store→next-question re-feed is SOURCE-grounded (1300-1303 store, 1719-1723 drain) but not independently probe-confirmed here (needs an under-answered launch question; launch is out-of-slice to drive).

## `.mg5` script file mechanics (comments, EOF-as-done, CmdFile-is-dead)
Verified for the "what is a `.mg5` script / how is it read" question class:
- **File read**: `import_command_file` (1702) does `commandline = open(filepath).readlines()`, wraps in the `self.inputfile` generator, feeds each line via `exec_cmd(line, precmd=True)`. Plain text, one command per line.
- **Comment stripping**: NOT in a file class — in `precmd` (extended_cmd.py:1028-1030): `if '#' in line: line = line.split('#')[0]`. Strips from the FIRST `#` onward, so a `#`-leading line becomes empty (skipped: `if line:` guard at 1717) AND inline `cmd # note` works. `precmd` also does `\`-continuation (1024-1026) and `;`-splitting (1033-1041). So `#` comments are ignored, but the mechanism is `precmd`, not a script-reader class.
- **CmdFile is DEAD**: `class CmdFile(file)` (extended_cmd.py:3334) subclasses `file`, which is NOT a Python-3 builtin (`NameError` on instantiation). `grep CmdFile` finds it referenced NOWHERE but its own def — a Py2 relic. CmdFile does NOT read/execute the script; the reader is `open().readlines()` + the inputfile generator.
- **EOF-as-done**: when the inputfile generator is exhausted the `import_command_file` loop ends; then `if self.child: self.child.exec_cmd('quit')` (1725-1727) closes any still-open child interface (e.g. a launch dialogue). So reaching EOF implicitly closes/`done`s open sub-dialogues rather than hanging. Interactive mode (`use_rawinput=True`, no `-f`) reads stdin via `timed_input`/`raw_input`, so an un-`done`d dialogue keeps prompting.

## Boundary
Applies only when `use_rawinput==False` or `self.inputfile` is truthy. Interactive mode
(`timed_input`/SIGALRM, raw `raw_input`) and the force-default path (`force=True` in `ask`)
are governed by the widget timeout machinery, not this resolution chain.

See also (plain refs): ask-question-widgets.md (widget internals, check_answer detail),
controlswitch-widget.md (special_check_answer_in_input_file), command-loop-machinery.md
(exec_cmd/run_cmd/CmdFile), config-system.md (display-options CAUTION),
interface-stack-chain.md (the store_line/get_stored_line mother-walk as one face of the
parent<->child chain invariant).
