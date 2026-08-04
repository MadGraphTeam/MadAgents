---
description: Which NLO exporter methods amcatnlo_interface.py drives directly (SubProcesses-level output) vs the per-P-dir generate_directories_fks loop — pineappl/init_map, orderstag_file, procdef_mg5, coef_specs, OLP, pass_information_from_cmd.
---

# Interface-driven exporter methods (SubProcesses-level vs P-dir-level) (v3.7.1)

NLO output is split across TWO drivers. The per-born-ME **P-directory** content is written inside `generate_directories_fks` (export_fks.py:472). But several **SubProcesses-level** (one-per-output, not per-P-dir) files are written by the exporter only because `amcatnlo_interface.py` calls those methods directly. If you ask "which method writes file X" and X is a SubProcesses-level aggregate file, the answer may be a method NOT called from the dir loop at all.

## The exporter surface called from amcatnlo_interface.py
Complete list of `self._curr_exporter.<method>` calls (grep-confirmed) and their line in `madgraph/interface/amcatnlo_interface.py`:
- `pass_information_from_cmd` (`:765` and again `:794`) — passes `proc_defs`/`born_processes` from the cmd into the exporter (export_fks.py:831). Comment: "Please do not modify any object of the interface from the exporter." Sets `self.proc_defs`, `self.born_processes` (used later by `finalize` for MA5-card collection — see finalize-nlo-process-dir.md).
- `copy_fkstemplate` (`:785`) — builds the dir skeleton (copy-fkstemplate-and-scaffolding.md).
- `generate_virtuals_from_OLP` (`:801`) — BLHA/GoSam external virtuals (olp-blha-virtuals.md). Only when OLP != MadLoop.
- `generate_directories_fks` (`:913`) — the per-born-ME P-dir loop (p-directory-layout.md). Called once per ME in a loop.
- `write_coef_specs_file` (`:994`) — DHELAS `Source/DHELAS/coef_specs.inc` (MAXLWFSIZE/VERTEXMAXCOEFS), only if `loop_optimized_output and len(max_loop_vertex_ranks)>0` (`:992`-993). The base-class version (export_fks.py:463) RAISES; the optimized one (`:5035`) writes. So this DHELAS-level file is interface-gated on optimized output + nonzero loop-vertex ranks.
- `write_procdef_mg5` (`:996`) — `SubProcesses/procdef_mg5.dat` (the MG4-equivalent proc_card so MadEvent4 Perl scripts work). Only if `self._generate_info` (`:995`). Splits coupling-order tokens out of the process string into the `coupling` field (export_fks.py:363-397).
- `write_init_map` (`:1006`) — `SubProcesses/initial_states_map.dat`: each initial-state PDF combination gets a unique id; returns `nmaxpdf` (export_fks.py:424). For the fast-PDF NLO interface.
- `write_maxproc_files` (`:1008`) — `SubProcesses/pineappl_maxproc.inc` (Fortran `mxpdflumi`/`max_nproc`) + `pineappl_maxproc.h` (C `__max_nproc__`) from `nmaxpdf` (export_fks.py:403). The PineAPPL fast-interface max-pdf-pairs headers.
- `write_orderstag_file` (`:1011`) — `SubProcesses/orderstags_glob.dat`: one orderstag integer per splitorder combo (export_fks.py:1143, uses get_orderstag; its base is the `orderstag_base` module constant at export_fks.py:64 — read the literal, do not cache the number; amp-split-and-orderstag.md).

## The two output altitudes
- **P-dir level** (inside `generate_directories_fks`, once per born ME): born_*/real/virt files, orders.inc, linkfiles, V-dir. The dir-loop writes/symlinks these. The linkfiles list (`:675`) symlinks the SubProcesses-level aggregates (`initial_states_map.dat`, `pineappl_maxproc.inc/.h`, `orderstags_glob.f` AND `orderstags_glob.dat`) DOWN into each P-dir via `ln('../'+file,'.')` (`:778`) — but the aggregates themselves are written ONCE at SubProcesses level by the interface AFTER the dir loop. (NB: both `orderstags_glob.f` at `:711` and `orderstags_glob.dat` at `:764` are in linkfiles; `write_orderstag_file` writes the `.dat`.)
- **SubProcesses level** (interface-driven, once per output, after the dir loop): `procdef_mg5.dat`, `initial_states_map.dat`, `pineappl_maxproc.{inc,h}`, `orderstags_glob.dat`, `Source/DHELAS/coef_specs.inc`.

## Cautions
- "Which method writes orderstags_glob.dat / initial_states_map.dat / pineappl_maxproc.* / procdef_mg5.dat?" → NOT generate_directories_fks; they are written by interface-driven calls (`amcatnlo_interface.py:996`-1011). The dir loop only SYMLINKS them into P-dirs. Same enclosing-def trap as the born-vs-dir-loop one (which-def-writes-which-pdir-file.md), but one level up: the writer isn't even in export_fks's dir loop, it's in the interface.
- `write_init_map`/`write_maxproc_files` run unconditionally (`:1006`-1009) — the pineappl headers are emitted even when PineAPPL is not used; they are cheap parameter headers, not a PineAPPL dependency.
- `write_coef_specs_file` is the one with a base-class poison override that RAISES (export_fks.py:466) — on a non-optimized exporter the interface guard (`loop_optimized_output`, `:992`) is what prevents the raise. The optimized default is fine.
- `write_procdef_mg5` only fires if `self._generate_info` is truthy (`:995`); a path that doesn't set it skips procdef_mg5.dat. NOTE: LoopInducedExporterME overrides write_procdef_mg5 (loop_exporters.py:3086).
