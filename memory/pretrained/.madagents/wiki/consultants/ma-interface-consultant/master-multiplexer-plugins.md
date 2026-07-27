---
description: master_interface.py multiplexer (Switcher/MasterCmd) — interface switching on generate/add/import, change_principal_cmd; plugin loading (-m mode, output plugin, from_plugin_import); plugin registration API (new_interface/new_output/version-metadata) + install-generated bin/<name>.py launcher that wraps mg5_aMC --mode (grounds MadDM bin/maddm REPL).
---

# Master multiplexer + plugin loading

## master_interface.py
`$MADGRAPH_INSTALL/madgraph/interface/master_interface.py`. The entry-point object `bin/mg5_aMC` instantiates (`MasterCmd`, line 191).

### Switcher (56) / MasterCmd (655)
- `interface_names` (65-67): each value is a `(prompt_name, cmd_class)` tuple — `MadGraph`→`('MG5_aMC', MGcmd.MadGraphCmd)`, `MadLoop`→`('MG5_aMC', LoopCmd.LoopInterface)`, `aMC@NLO`→`('MG5_aMC', amcatnloCmd.aMCatNLOInterface)`. Only these three are switchable principal interfaces. The interactive prompt is `tuple[0]+'>'` (`__init__` 661, `change_principal_cmd` 694) → literally **`MG5_aMC>`** for ALL three (the display name is identical; only the underlying `self.cmd` class differs on LO↔MadLoop↔NLO switch — the prompt never visibly changes).
- `MasterCmd(Switcher, LoopCmd.LoopInterface, amcatnloCmd.aMCatNLOInterface, cmd.CmdShell)` (655) — multiple inheritance over all sub-interfaces; `self.cmd` points at the *current* class and methods delegate via `self.cmd.do_X(self,...)`.
- `change_principal_cmd(name, allow_switch=True)` (684): swaps `self.prompt`, `self.cmd`, `self.current_interface`. `allow_switch=False` → raises InvalidCmd "Can not combine LO/NLO feature." Calls `self.cmd.setup(self)` only when the *display name* (`MG5_aMC`) changes (it never does among the three) — so setup is effectively not re-run on LO↔NLO switch here.
- `debug_link_to_command` (81): in `__debug__`, audits that every `do_/check_/help_/complete_` is wired in the Switcher; writes missing wrappers to `additional_command` file and raises if any subclass method is ambiguous.

### Switch triggers (which command picks the interface)
- `extract_process_type` (162, `@staticmethod` at 161): parses `[...]` in a process line → `('tree'|'NLO', option, orders)`. `[QCD]`→NLO all; `[virt=...]`→virt; bare `[...]`→all; `LOonly`→NLO LOonly.
- `do_generate` (260) / `do_add` (200) / `do_check` (239): NLO `all/real/LOonly`→`aMC@NLO`; `virt/sqrvirt`→`MadLoop`; tree→`MadGraph`. `noborn`→loop-induced path. `NoBornException` on add → auto-switch to loop-induced (232).
- `do_import` (280): after import, if model is a `LoopModel` with `perturbation_couplings` and not already NLO/loop → switch to `aMC@NLO`; non-loop model while in MadLoop → back to MadGraph.
- `do_output` (294): `output aloha` forced through `MadGraphCmd.do_output`; else delegates.

### MasterCmdWeb (711) — secure web mode (`--web`), timeout forced to 1, installs/saves locked down.

## Plugin loading
- `Cmd.plugin_path` (extended_cmd.py 911): `[MG5DIR/PLUGIN]` for MG5 (`[]` in MADEVENT mode). Also scans `$PYTHONPATH` for any `MG5aMC_PLUGIN` dir (915-927). `$MADGRAPH_INSTALL/PLUGIN/` ships with only `__init__.py`.
- `bin/mg5_aMC -m/--mode NAME` (169-187): imports `PLUGIN.NAME` (or `MG5aMC_PLUGIN.NAME`), requires `plugin.new_interface`; if absent → warns and exits. `misc.is_plugin_supported` gate. Builds `plugin.new_interface(mgme_dir=...)` as the cmd object.
- `output <name>` plugin path: `check_output` (madgraph_interface 1707) calls `misc.from_plugin_import(self.plugin_path,'new_output',name,...)` → if a plugin defines `new_output[name]`, sets `_export_format='plugin'`, `_export_plugin=cls` (1714-1722).
- `misc.from_plugin_import` (various/misc.py 2227): iterates plugin dirs, imports each subdir with `__init__.py`, returns `getattr(plugin,target_type)[keyname]`; `keyname=None` returns all keys. Honors `is_plugin_supported`.

CAUTION: a plugin used with `-m` MUST define `new_interface` or mg5 exits; a plugin providing only `new_output` is used via `output <name>`, not `-m`.

## Plugin registration API (the module-level attributes a `PLUGIN/<name>/__init__.py` exposes)
Read by both `-m` launch and `install <name>` validation:
- `new_interface` — a Cmd subclass (its own REPL) or None. Non-None → `mg5_aMC -m <name>` builds `new_interface(mgme_dir=...)` as the cmd object (bin/mg5_aMC 180-187); its `do_*` methods ARE the plugin's new REPL commands (`MadDM>` prompt, `define darkmatter`, `generate relic_density` etc. = plugin-internal do_* = GAP, needs plugin source; the *class-as-interface* extension is core).
- `new_output` — dict {format_name: exporter_cls} consumed by `output <name>` via `from_plugin_import` (madgraph_interface 1714/2590); None/empty for interface-only plugins.
- `latest_validated_version`, `minimal_mg5amcnlo_version`, `maximal_mg5amcnlo_version` — version-compat metadata read by `install <name>` (madgraph_interface 6814-6818) and `misc.is_plugin_supported`.

## install-generated launcher (grounds MadDM's `bin/maddm`)
`do_install` (installation slice owns the command) at madgraph_interface 6835-6858: when the installed plugin defines `new_interface`, it WRITES an executable `bin/<name>.py` (chmod S_IRWXU) whose entire body re-invokes `mg5_aMC ... --mode=<name>`. Release build (`__debug__` False) bakes in `-O -W ignore::DeprecationWarning`; dev bakes `-tt`. So `python bin/maddm.py` is a thin wrapper → `mg5_aMC --mode=maddm` → the `-m` plugin path above builds the MadDM REPL. The dedicated REPL is NOT a separate mechanism; it IS the `--mode` plugin-interface path wrapped in a generated launcher.
- `install_plugin = ['maddm', 'maddump', 'MadSTR', 'cudacpp']` (madgraph_interface 6484): maddm is a recognized `install maddm` target (name-registry only; the download/build is installation slice).
