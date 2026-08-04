---
description: NLO FKS exporter class hierarchy in export_fks.py + loop_exporters.py — base/optimized/EW-Sudakov/MatchBox/loop-induced, MRO, and which finalize fires.
---

# NLO-export exporter class hierarchy (v3.7.1)

Two files, one inheritance web. `export_fks.py` defines the FKS (NLO real+virtual) exporters; `loop_exporters.py` defines the loop/MadLoop standalone base they extend.

## loop_exporters.py classes
- `LoopExporterFortran(object)` — `$MADGRAPH_INSTALL/madgraph/loop/loop_exporters.py:71`. Pure helper mix-in (NOT a ProcessExporterFortran subclass — avoids MRO ambiguity). Carries `default_opt` (`:81`, incl `output_dependencies:'external'`, `SubProc_prefix:'P'`, `vector_size:0`), `include_names` map for TIR `.mod` files (`:92`), `link_CutTools` (`:115`), `write_mp_files` (`:212`).
- `LoopProcessExporterFortranSA(LoopExporterFortran, export_v4.ProcessExporterFortranSA)` — `:227`. Unoptimised standalone loop exporter. `loop_additional_template_setup` (`:370`) lays MadLoop scaffolding into the dir.
- `LoopProcessOptimizedExporterFortranSA(LoopProcessExporterFortranSA)` — `:1747`. Optimised (default) loop path. Adds `link_TIR` (`:1910`), `write_TIR_interface` (`:2219`), `loop_optimized_additional_template_setup` (`:1817`), `tir_available_dict`.
- `LoopProcessExporterFortranMatchBox(LoopProcessOptimizedExporterFortranSA, export_v4.ProcessExporterFortranMatchBox)` — `:3017`. MatchBox format (color-string output). Sets `export_format='madloop_matchbox'`, `sa_symmetry=True` (`:3023`-3024). Overrides `get_color_string_lines`/`get_JAMP_lines` to delegate to the MatchBox base (leading-color color-flow strings, `:3029`-3039), `get_ME_identifier` → `'MG5_<id>_'` (`:3041`). Its `finalize` (`:3046`) calls `super().finalize` then `misc.compile(Source/MODEL)` (`:3048`) — compiles the model right at output.
- `LoopInducedExporterME(LoopProcessOptimizedExporterFortranSA)` — `:3054`. Common base for loop-induced; sets `proc_characteristic['loop_induced']=True`, forces `vector_size=1` (`:3072`).
  - `LoopInducedExporterMEGroup(LoopInducedExporterME, ...)` — `:3254` (subprocess-grouped).
  - `LoopInducedExporterMENoGroup(LoopInducedExporterME, ...)` — `:3435` (ungrouped).

## export_fks.py classes
- `ProcessExporterFortranFKS(loop_exporters.LoopProcessExporterFortranSA)` — `:91`. Base FKS exporter (unoptimised loop path). Owns `copy_fkstemplate` (`:98`), `generate_directories_fks` (`:472`), `finalize` (`:842`), `write_orders_file` (`:1239`), `generate_virt_directory` (`:2429`), the EW-Sudakov ME writers (`write_sudakov_*`, `:2886`+).
- `ProcessOptimizedExporterFortranFKS(LoopProcessOptimizedExporterFortranSA, ProcessExporterFortranFKS)` — `:4693`. The DEFAULT NLO exporter. `jamp_optim=True` (`:4698`). Overrides `copy_fkstemplate` (`:4707`, adds TIR linking) and `generate_virt_directory` (`:4908`). Its `finalize` (`:4700`) just delegates to `ProcessExporterFortranFKS.finalize`.
- `ProcessExporterEWSudakovSA(ProcessOptimizedExporterFortranFKS)` — `:5056`. EW-Sudakov standalone. Overrides `generate_directories_fks` (`:5104`, only writes Sudakov-relevant files) and `finalize` (`:5061`, then `write_python_wrapper` (def `:5068`, call `:5066`) → `bin/internal/ewsud_pydispatcher.py`).

## Loop-induced exporters — ME / Group / NoGroup divergence (loop_exporters.py)
`LoopInducedExporterME(LoopProcessOptimizedExporterFortranSA)` — `:3054`. Common base for loop-induced (a loop ME integrated like a tree ME). Non-obvious details:
- `__init__` (`:3062`): sets `proc_characteristic['loop_induced']=True`, reads optional `output_options['t_strategy']` (channel t-strategy), forces `self.opt['vector_size']=1` (`:3072`).
- `get_context` (`:3075`): sets `context['MadEventOutput']=True` — flips the loop ME templates into MadEvent-integration mode (vs pure standalone).
- `get_source_libraries_list` (`:3095`): if `dependencies=='internal'`, appends `libcts` + `libiregi` to the SOURCE compile list (loop-reduction libs must build with the rest).
- `link_files_in_SubProcess` (`:3109`): adds `ln('../MadLoop5_resources')` into each P-dir.
- `copy_template` (`:3116`): calls BOTH `LoopProcessExporterFortranSA.loop_additional_template_setup` (Source-makefile off) AND `LoopProcessOptimizedExporterFortranSA.loop_optimized_additional_template_setup` — the "mixed" MadEvent+MadLoop-standalone template layout.
- `finalize` (`:3131`): just `write_global_specs` (+ a commented-out MadLoopInitializer.init_MadLoop). MadLoop init is deferred to `initMadLoop` / first run, NOT done at output time.
- `write_tir_cache_size_include` (`:3147`): hardcodes a smaller `TIR_CACHE_SIZE` than the standalone path (`:3147`, read the literal) — gains speed since MadLoop is called once per helicity here.

The two leaf classes pick a different MadEvent base and stitch it to `LoopInducedExporterME`:
- `LoopInducedExporterMEGroup(LoopInducedExporterME, export_v4.ProcessExporterFortranMEGroup)` — `:3254`. Subprocess-grouped. `copy_template`/`finalize`/`generate_subprocess_directory` call the **MEGroup** base explicitly (to dodge MRO). Its `finalize` (`:3286`) additionally **removes the duplicate `DDILOG` routine from `Source/setrun.f`** via `FortranWriter.remove_routine` (loop material and MadEvent both ship DDILOG).
- `LoopInducedExporterMENoGroup(LoopInducedExporterME, export_v4.ProcessExporterFortranME)` — `:3435`. Ungrouped; calls the plain **ME** base. No DDILOG removal.

So Group↔NoGroup differ only in which MadEvent exporter they bolt on (grouped vs ungrouped subprocess dirs) and the Group-only DDILOG dedup.

## Cautions
- MRO for the optimised FKS exporter: `ProcessOptimizedExporterFortranFKS` lists `LoopProcessOptimizedExporterFortranSA` FIRST, then `ProcessExporterFortranFKS`. So optimised-loop methods win unless `ProcessExporterFortranFKS` overrides; `copy_fkstemplate` is explicitly re-defined on the optimised class to be unambiguous.
- Loop-induced leaf classes call mother methods by explicit class name (`export_v4.ProcessExporterFortranMEGroup.finalize(self,...)`), NOT `super()` — a deliberate MRO bypass so the right MadEvent finalize runs alongside `LoopInducedExporterME.finalize`. Don't reason about their behavior from the linearised MRO.
- `ProcessExporterFortranFKS` extends the UNOPTIMISED loop SA class; the optimised FKS exporter pulls the optimised loop SA in via the first base. Don't assume the base FKS class has TIR support — TIR linking lives on the optimised side.
