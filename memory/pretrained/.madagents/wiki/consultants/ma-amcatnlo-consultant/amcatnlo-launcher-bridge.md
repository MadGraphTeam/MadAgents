---
description: aMCatNLOLauncher (launch_ext_program.py:487) — the bridge from the one-shot do_output/do_launch path into the persistent aMCatNLOCmd runtime shell; option-line round-trip, set-history replay, cluster/multicore core count, cards=[] means the launcher skips card editing.
---

# `aMCatNLOLauncher` — the output→launch → runtime-shell bridge

`$MADGRAPH_INSTALL/madgraph/interface/launch_ext_program.py`, `class aMCatNLOLauncher(ExtLauncher)` (line 487). This is the object the process-construction `do_launch` hands off to (`amcatnlo_interface.py:1045`: `launch_ext.aMCatNLOLauncher(argss[0], self, run_mode=argss[1], shell=isinstance(self, CmdShell), **options).run()`). [[do-output-and-launch-interface]] names it; this page documents what it does. It is the seam between the one-shot `mg5_aMC` script flow (`output DIR` → `launch DIR MODE`) and the persistent `aMCatNLOCmd` runtime shell that actually integrates.

## Construction (`__init__`, 490-514)
- `run_mode` = the launch MODE (`LO`/`NLO`/`aMC@NLO`/`aMC@LO`/`auto`), stored verbatim (503).
- cluster/multicore coercion (505-508): `cluster` option → `self.cluster=1`; `multicore` option → `self.cluster=2`. So `self.cluster` is a tri-state mode token (0 single / 1 cluster / 2 multicore), NOT a boolean.
- **`self.cards = []` (510)** — load-bearing. The base `ExtLauncher.run()` (line 63) only edits cards when `self.cards` is non-empty (`run():71` → `ask_edit_card_static`). An empty list means **the launcher does NO card editing**. Card editing for an aMC@NLO run happens later, inside `aMCatNLOCmd.ask_run_configuration` ([[ask-run-configuration-mode-resolution]]), not here. (Contrast `MadLoopLauncher` at line 147, which sets `cards=['param_card.dat','MadLoopParams.dat']` and DOES edit.)
- run-name default: `find_available_run_name(self.running_dir)` if `name==''` (513-514).

## `run()` (base `ExtLauncher.run`, 63-79)
`prepare_run()` (no-op for this launcher) → since `self.cards==[]`, the `ask_edit_card_static` block is skipped → `launch_program()`.

## `launch_program` (516-578) — the actual bridge work
1. **Multicore core-count (520-535)**: only when `self.cluster==2`. `multiprocessing.cpu_count()`; if 1 core → warn "Pass in single machine", set `cluster=0`, recurse `launch_program()` (so multicore silently degrades to single-machine on a 1-core box). 2 cores → `nb_node=2`. Else if not forced → interactive `ask('How many cores do you want to use?', max_node, range(2,max_node+1))`; if forced → `nb_node=max_node`.
2. **Instantiate the runtime shell (539-542)**: `run_int.aMCatNLOCmdShell(...)` if `self.shell` else `run_int.aMCatNLOCmd(...)`, with `me_dir=running_dir` and the parent's `options`. **This is where the persistent `<PROC_DIR>` command processor ([[runtime-shell-commands]]) is born.**
3. **`set`-history replay (544-556)**: scans `cmd_int.history` for lines starting `set`, keeps those whose first arg is a known option key (`options_configuration`/`options_madgraph`/`options_madevent`), and `usecmd.exec_cmd(line)`s each on the new shell — failures are caught and `misc.sprint`-warned, not fatal. So `set` commands issued in the parent mg5 session (e.g. `set lhapdf /path`) are carried into the runtime shell.
4. **`define_child_cmd_interface(usecmd, interface=False)` (557)** — wires the new shell as a child cmd of the parent.
5. **Option-line synthesis (560-566)**: rebuilds a `launch <run_mode> <flags>` command string. Every truthy option except `cluster/multicore/name/appl_start_grid/shell` becomes `--<opt>`; `name` → `--name X`; `appl_start_grid` → `--appl_start_grid X`. Then mode token appended: `cluster==1` → ` -c`; `cluster==2` → ` -m` (and `usecmd.nb_core=nb_node`, 572).
6. **Drive (573-578)**: removes stale `ME5_debug`, then `launch.run_cmd(command)` (re-enters `aMCatNLOCmd.do_launch` with the synthesized line) followed by `launch.run_cmd('quit')`.

## The round-trip that matters
The launcher takes the **structured `**options` dict** that `do_launch` built from `check_launch`'s parsed flags ([[do-output-and-launch-interface]]) and **re-serializes it into a command-line string** (560-566), which `aMCatNLOCmd.do_launch` ([[runtime-shell-commands]]) then **re-parses**. The `-c`/`-m` cluster flags are re-derived from `self.cluster`, NOT passed through as-is. So a flag set on the original `launch DIR MODE --flag` survives as `--flag` only if `do_launch`/`check_launch` retained it in `options` AND it isn't in the excluded set {cluster, multicore, name, appl_start_grid, shell} (the excluded ones are re-emitted in their canonical form).

## Cautions
- `self.cards=[]` is the reason the **first** card-edit prompt a user sees in an `output`→`launch` flow comes from `ask_run_configuration`, not from the launcher. A page claiming "the launcher asks you to edit cards" is wrong — it deliberately does not (only non-aMCatNLO launchers like `MadLoopLauncher`/`MELauncher` do).
- multicore on a 1-core machine **silently** degrades to single-machine (525-528) — no error, just a warning and `cluster=0`.
- The `-m`/`-c` mode is re-synthesized from `self.cluster` at 568-571, so even if the user typed `--multicore`, what reaches the inner `do_launch` is the canonical `-m` plus `usecmd.nb_core` set directly on the object. The core count is set on the object (572), not passed on the command line.
- `set`-history replay only carries lines whose first arg is a *recognized option key* (549); a `set` of an unknown key is silently dropped from the replay.
