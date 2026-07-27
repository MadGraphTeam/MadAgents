---
description: copy_fkstemplate template-tree copying + loop/MadLoop scaffolding into the NLO process dir — Template/NLO+Common copy, MadLoopParams, CutTools/TIR linking, FKS_params edit.
---

# copy_fkstemplate + loop scaffolding (v3.7.1)

`copy_fkstemplate(model)` builds the NLO process directory skeleton. Two versions: base `ProcessExporterFortranFKS.copy_fkstemplate` (`export_fks.py:98`) and optimised `ProcessOptimizedExporterFortranFKS.copy_fkstemplate` (`:4707`). The optimised one is the default path.

## Template trees copied (both versions)
- `misc.copytree(Template/NLO, dir_path, True)` — `:114` / `:4722`. The whole NLO tree (bin, Cards, Events, FixedOrderAnalysis, HTML, lib, MCatNLO, Source, SubProcesses, Utilities, makefile, index.html).
- `misc.copytree(Template/Common, dir_path)` — `:116` / `:4724`. Common files overlaid.
- `plot_card.dat` → `plot_card_default.dat` if present.
- `FO_analyse_card.dat` → `_default` (base only, `:171`).

## clean step
If `self.opt['clean']`: runs `bin/internal/clean_template` (with `--web` if `MADGRAPH_BASE` env set), writes `SubProcesses/MGVersion.txt` (`:137`/`:4746`).

## MadLoop material (from loop_material/StandAlone/)
`self.loop_dir` points at `Template/loop_material`. Copied via `cpfiles` (`:193`/`:4851`):
- `SubProcesses/MadLoopParamReader.f`, `SubProcesses/MadLoopParams.inc`, `Cards/MadLoopParams.dat`.
- `MadLoopParams.dat` → `Cards/MadLoopParams_default.dat`; re-parsed via `banner_mod.MadLoopParam` and re-written to `SubProcesses/MadLoopParams.dat` (`:204`/`:4864`).
- `MadLoopCommons.inc` → `SubProcesses/MadLoopCommons.f` with `%(print_banner_commands)s` substituted. Context `collier_available`: **False** in the base version (`:218`); in the optimised version it is `self.tir_available_dict['collier']` (`:4878`) — i.e. only the optimised path can emit COLLIER-aware MadLoopCommons.

## Reduction-library linking
- `self.link_CutTools(dir_path)` (both) — links `libcts.a`,`mpmodule.mod` into `lib/` per `output_dependencies` mode (external/internal/environment_paths). Defined `loop_exporters.py:115`.
- TIR (optimised only): loops over `self.all_tir`, calls `self.link_TIR` (`loop_exporters.py:1910`) per library. For pjfry/ninja/golem/samurai/collier links dynamically with `-L.../-l...`; ninja additionally needs `libavh_olo` or it raises (`export_fks.py:4786`). IREGI is self-contained (linked into `lib/`). Builds `link_tir_libs`/`tir_libs`/`tir_include` → fed to `write_makefile_TIR` (makefile_loop) and `write_make_opts`. The per-library DISABLE/compile semantics inside `link_TIR` (internal-mode disables all non-self-contained libs, IREGI is the only self-buildable, all TIR misses soft-fail) are detailed in output-dependencies-link-modes.md.
- DUPLICATED TIR loop (non-obvious): the `for tir in self.all_tir` linking loop — including the ninja `libavh_olo` raise — exists in TWO places: the FKS optimised `copy_fkstemplate` INLINES its own copy (`export_fks.py:4783`-4786, raise at `:4786`), while `loop_optimized_additional_template_setup` (`loop_exporters.py:1817`, raise at `:1843`) carries an identical copy used by the loop-SA/loop-induced (non-FKS) path. So a NLO FKS run hits the `export_fks.py:4786` raise; a pure loop-standalone/loop-induced run hits the `loop_exporters.py:1843` raise. Same message, different file:line — cite the one matching the exporter.

## Other files written
- `makefile_loop.inc` removed and regenerated via `write_makefile_TIR` (base `:258` reads `Template/NLO/SubProcesses/makefile_loop.inc`).
- `make_opts.inc` removed, regenerated via `write_make_opts`.
- `vendor/SudGen/sudakov.f` copied into SubProcesses (Pythia8 Sudakov tables for MC@NLO-DELTA) — `:189`/`:4847`.
- `cts_mprec.h`,`cts_mpc.h` written from CutTools (`write_mp_files`).
- `copy_python_files()`, `write_pdf_opendata()`.
- If `model["running_elements"]`: copies `Template/Running` → `Source/RUNNING` (base RAISES if not installed, `:247`; optimised just copytree, `:4901`).
- Optimised also links `mp_coupl.inc`/`mp_coupl_same_name.inc` from Source/MODEL into SubProcesses — absent for `[real=]` mode (`:4883`).

## FKS_params edit (base only, :227)
Regex-forces `#NHelForMCoverHels` → `-1` in `Cards/FKS_params.dat` (turns off MC-over-helicities by default). NOTE: this edit is in the BASE copy_fkstemplate only; the optimised override does NOT repeat it.

## loop_additional_template_setup (loop_exporters.py:370)
Called during `copy_template` for the loop-SA path. Copies StandAlone MadLoopParams files, copies StandAlone `SubProcesses/makefile` → `self.madloop_makefile_name`, writes `MadLoop_makefile_definitions`, creates empty `SubProcesses/MadLoop5_resources/`, links param_card/ident_card/MadLoopParams into it, removes generic `check_sa.f`.

## Cautions
- The base-vs-optimised `collier_available` divergence means MadLoopCommons.f differs by path; don't assume COLLIER banner logic from the base class.
- `FKS_params.dat` NHelForMCoverHels=-1 forcing is base-only in source text — verify on the optimised default path before asserting it for a given run (probe-candidate).
