---
description: aMCatNLOInterface do_display / do_output / check_output / do_launch / check_launch — NLO three-amplitude display, NLO export trigger, forbidden formats, handoff to the runtime shell.
---

# `do_output` / `do_launch` (process-construction interface)

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_interface.py`.

## do_display (line 384) — NLO three-amplitude display
NLO splits the amplitude into Born / real / loop. `get_amps_dict = {'real':get_real_amplitudes, 'born':get_born_amplitudes, 'loop':get_virt_amplitudes}` (391, off `self._fks_multi_proc`). Sub-commands:
- `display diagrams [born|real|loop] [args]` (394): draws via `self.draw(..., Dtype=...)`; with no type arg, loops all three non-empty sets. Requesting `loop` with zero virt amps → `InvalidCmd('No virtuals have been generated')` (400).
- `display diagrams_text [...]` (411): `nice_string()` text into `pydoc.pager`; with no type, prints Born+Real+Loop sections.
- `display processes [...]` (431): `nice_string_processes()` per amplitude; no type → Born/Real/Loop process lists.
- Any other first arg → falls through to `mg_interface.MadGraphCmd.do_display` (450).
- `check_display` (104): delegates to MadGraphCmd then restricts arg[1] to born/loop/virt/real, and renames `virt→loop` (116). `_fks_display_opts` (336) = real_diagrams/born_diagrams/virt_diagrams/... The `'virt'` alias is normalised to `'loop'` at check time.

## check_output (line 139) and do_output (line 740)
- `check_output:142`: first arg `ewsudakovsa` → `_export_format='ewsudsa'`; otherwise `_export_format='NLO'`.
- `check_output:148`: `forbidden_formats = ['madevent','standalone']` → passing them raises `InvalidCmd("You generated a NLO process, which cannot be exported in %s mode... use 'output DIR_NAME'")`. (NLO cannot use the LO `madevent`/`standalone` exporters.)
- `check_output:151`: no `_fks_multi_proc` → "No processes generated"; no model → "No model found".
- `do_output:757`: `group_processes = False` always (comment: "For NLO, the group_subprocesses is automatically set to false"). Grouping is rejected later in `export()` (line 827) with `MadGraph5Error("Cannot group subprocesses when exporting to NLO")`.
- `do_output:761`: exporter from `export_v4.ExportV4Factory` with `output_type` `'amcatnlo'` (NLO) or `'ewsudsa'`. Calls `copy_fkstemplate` (line 785), then `self.export(...)`, `self.finalize(...)`.
- `do_output:800`: if `OLP != 'MadLoop'`, calls `generate_virtuals_from_OLP`. (OLP/MadLoop internals are out of slice — madloop slice.)
- `do_output:768`: existing dir + not `-f`/`-noclean` → interactive `ask('Do you want to continue?')`; then `shutil.rmtree`.

The multi-directory Fortran emission / exporter internals invoked by `export()` are the **nlo-export slice**; `do_output` here is the command-level driver.

## check_launch (line 179) / do_launch (line 1016)
- `check_launch`: args are `[DIR, MODE]`. MODE ∈ `['LO','NLO','aMC@NLO','aMC@LO','auto']` (line 200); default appended is `'auto'`. Invalid mode raises. No args + prior `_done_export` → reuses it.
- `check_launch:230`: `-m`(multicore) + `-c`(cluster) together → InvalidCmd.
- `check_launch:233`: `mode=='NLO'` with `-r/--reweightonly` → InvalidCmd (reweightonly needs aMC@NLO/aMC@LO).
- `do_launch:1025`: **if `<DIR>/Events` does not exist, switches to ML5 (`do_switch('ML5')`) and defers to the LO `MadGraphCmd.do_launch`** — i.e. a non-NLO process dir falls through to the launch slice.
- `do_launch:1032`: `--interactive` → spins up `run_interface.aMCatNLOCmd(Shell)` and replays `set` history lines, then `define_child_cmd_interface` (drops into the runtime shell).
- `do_launch:1045`: normal path → `launch_ext.aMCatNLOLauncher(dir, self, run_mode=argss[1], ...).run()`.

## complete_launch options (line 315)
Tab-completion offers: `-f -c -m -i -x -r -p -o -n a --force --cluster --multicore --interactive --nocompile --reweightonly --parton --only_generation --name --appl_start_grid`, and `--laststep=` ∈ `parton/pythia/pgs/delphes/auto`.

## Cautions
- The `Events`-dir existence check (line 1025) is the silent LO/NLO fork: launching a directory that isn't an NLO output dir does NOT error — it reroutes to ML5. A caller expecting NLO behaviour on a non-NLO dir gets LO launch instead.
