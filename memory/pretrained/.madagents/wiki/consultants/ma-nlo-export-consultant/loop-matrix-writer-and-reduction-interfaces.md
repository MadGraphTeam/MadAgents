---
description: write_loop_matrix_element_v4 (base vs optimized) — the V-dir loop_matrix.f writer family and the per-reduction-library interface emission (CT/TIR/COLLIER/GOLEM_interface.f), looplibs_av ordering.
---

# Loop-matrix writer + reduction-library interfaces (v3.7.1)

`generate_virt_directory` (export_fks.py base `:2429` / optimised `:4908`) writes the V-dir's `loop_matrix.f` by calling `write_loop_matrix_element_v4(None, matrix_element, fortran_model)` — base call `export_fks.py:2464`, optimised call `:4943`. The exporter's loop SA base (`loop_exporters.py`) owns the writer; `export_fks` only calls it. p-directory-layout.md notes the call; THIS page details the per-library interface files it emits.

## The `writer=None` invariant (both versions)
Both writers start with `if writer: raise MadGraph5Error('Matrix output mode no longer supported.')` (base `:1104`, optimised `:2070`). Every real call passes `writer=None` (export_fks `:2464`/`:4943`) — the writer opens its own per-file `FortranWriter` for each emitted file in the V-dir cwd. So the single-file "matrix" output mode is dead; the raise is unreachable on the real path but guards against re-enabling it.

## Base `write_loop_matrix_element_v4` (loop_exporters.py:1050, UNOPTIMISED loop path)
`template_dir = iolibs/template_files/loop` (`:233`). Files written into the V-dir:
- `loop_matrix.f` (via `write_loopmatrix`, `:1107`), `proc_prefix.txt`, `check_sa.f`, `CT_interface.f` (`write_CT_interface`, `:1120`), `improve_ps.f`, `loop_num.f`, `mp_born_amps_and_wfs.f`, `nexternal.inc`, `process_info.inc`.
- **CutTools is the ONLY reduction interface** — no TIR/GOLEM/COLLIER. Confirmed: `template_files/loop/` has only `CT_interface.inc`, `loop_matrix_standalone.inc`, `loop_num.inc` (no TIR/GOLEM/COLLIER `.inc`).
- Raises if `config_map` given (`:1060`) — base loop output cannot do MadEvent multi-channel AMP2.

## Optimised `write_loop_matrix_element_v4` (loop_exporters.py:2060, DEFAULT NLO path)
`template_dir = iolibs/template_files/loop_optimized` (`:1752`, has all four interface `.inc`). Adds beyond the base set:
- `set_group_loops` (`:2094`), `set_optimized_output_specific_replace_dict_entries` (`:2103`).
- `loop_matrix.f`, `check_sa.f`, `polynomial.f` (`write_polynomial_subroutines`, `:2119` — also writes `loop_max_coefs.inc`), `improve_ps.f`.
- `CT_interface.f` (`:2128`), `TIR_interface.f` (ALWAYS, `:2132`).
- `GOLEM_interface.f` ONLY if `self.tir_available_dict['golem']` (`:2135`).
- `COLLIER_interface.f` ONLY if `self.tir_available_dict['collier']` (`:2140`).
- `loop_num.f`, `mp_compute_loop_coefs.f`.
- `compute_color_flows.f` only if `get_context()['ComputeColorFlows']` (`:2154`).
- `tir_cache_size.inc` only if `get_context()['TIRCaching']` (`:2170`).

So the gating is asymmetric: CT and TIR interface files are unconditional on the optimised path; GOLEM/COLLIER are conditional on availability; pjfry/iregi/samurai/ninja get NO standalone `.f` (their mapping is folded into `TIR_interface.f`, see below).

## The reduction-library interface writers (loop_exporters.py optimised class)
Each reads its `.inc` from `template_dir`, `%`-substitutes `matrix_element.rep_dict`, and (for several) APPENDS a `FortranPolynomialRoutines` (`q_polynomial`) mapping:
- `write_CT_interface` (optimised `:2214` → base `:1320` with `optimized_output=True`): `CT_interface.inc`.
- `write_TIR_interface` (`:2219`): `TIR_interface.inc`. Computes `HAS_AN_HEFT_VERTEX` per loop group (see amp-split-and-orderstag.md), then APPENDS `FPR.write_pjfry_mapping()` if `tir_available_dict['pjfry']` (`:2271`) and `FPR.write_iregi_mapping()` if `['iregi']` (`:2273`). So pjfry+iregi mappings live INSIDE `TIR_interface.f`, not in their own files.
- `write_COLLIER_interface` (`:2280`): `COLLIER_interface.inc` + builds `collier_coefmap` (the COEFMAP_ZERO/ONE/TWO/THREE DATA arrays, emitted in fixed-size chunks, from `FPR.get_COLLIER_mapping()`, `:2292`-2305, read the chunk size there).
- `write_GOLEM_interface` (`:2319`): `GOLEM_interface.inc` + APPENDS `FPR.write_golem95_mapping()` (`:2348`). Sets `loop_induced_sqsoindex=',SQSOINDEX'` when NOT `AmplitudeReduction`, else `''` (`:2330`/`:2332`) — finalises the TIR result differently for built-in-squaring-against-born vs loop-induced.
- Each substitutes `include_vector` = `include '../../Source/vector.inc'` iff `self.opt['vector_size']`, else `''`.

## `data_looplibs_av` ordering constraint (write_loopmatrix :2893-2899)
`loop_matrix.f` carries an availability array seeded `['.TRUE.']` (CutTools always first) then ONE entry per library in the FIXED order `['pjfry','iregi','golem','samurai','ninja','collier']` (`:2896`), each `.TRUE.` iff `tir_lib in self.all_tir and self.tir_available_dict[tir_lib]`. Source comment: "one should be careful about the order ... as it must match the ordering in MadLoopParamsCard." So this literal list order is load-bearing — it indexes into the MadLoopParams library-selection enum at runtime.

## Other write_loopmatrix outputs (:2858+)
- `nsquaredSO.inc` (`PARAMETER NSQUAREDSO=...`) written then `files.cp('nsquaredSO.inc','..')` into the P-dir (`:2858`-2861).
- Into `../MadLoop5_resources/`: `<proc_prefix>ColorNumFactors.dat`, `<proc_prefix>ColorDenomFactors.dat`, `<proc_prefix>HelConfigs.dat` (`:2927`-2947) — only if `write_auxiliary_files`.
- `hel_offset` hardcoded (`:2909`, read the literal); HELAS calls split via `split_HELASCALLS` into `helas_calls_split.inc` chunks with `*_REQ_SO_DONE` broadcasters and sequential `continue_label`s (`:2971`-2990, read the label values there).

## Cautions
- The base (unoptimised) loop V-dir has NO TIR/COLLIER/GOLEM interface — only CutTools. A question about a reduction library other than CutTools on the base FKS path (`ProcessExporterFortranFKS`, non-optimised) has the answer "not emitted." But the DEFAULT NLO exporter is optimised, so the default path DOES emit TIR (always) + conditional GOLEM/COLLIER.
- GOLEM/COLLIER `.f` files are conditional on `tir_available_dict` at OUTPUT time — a library installed later but absent at `output` time means no interface file. Runtime/install-dependent; verify `tir_available_dict` for THIS run before asserting a given interface file exists.
- The `looplibs_av` list order is a literal source array, not derived — if MadLoopParamsCard's enum order ever changes, this line must change in lockstep. Watch for drift across versions.
- pjfry/iregi/samurai/ninja have NO own interface `.f`; only CT, TIR, GOLEM, COLLIER do. pjfry+iregi mappings are appended into `TIR_interface.f`. Don't expect a `PJFRY_interface.f` or `NINJA_interface.f`.

## Verification
Adversarially re-walked loop_exporters.py for THIS version. ALL content claims hold: base writer (`:1050`) template_dir `:233` (`loop/` has ONLY `CT_interface.inc`); optimised writer (`:2060`) template_dir `:1752` (`loop_optimized/` has CT/TIR/GOLEM/COLLIER `.inc`); CT+TIR unconditional (`:2128`/`:2131`-2132), GOLEM gated `self.tir_available_dict['golem']` (`:2136`), COLLIER gated `['collier']` (`:2141`); BOTH real calls pass `writer=None` (`export_fks.py:2464`/`:4943`) so the raise IS unreachable on the real path; `data_looplibs_av` seeded `['.TRUE.']` (CutTools first, `:2892`) then the FIXED list `['pjfry','iregi','golem','samurai','ninja','collier']` (`:2896`) — NOTE this order ≠ `self.all_tir` (`:1763` = `['pjfry','iregi','ninja','golem','samurai','collier']`, ninja↔golem/samurai swapped); the `:2896` list is the MadLoopParamsCard-matching one.
