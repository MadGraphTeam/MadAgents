---
description: LoopHelas layer — LoopHelasAmplitude/Diagram/MatrixElement/Process, loop denominators+rank+spin sizing for reduction, split-order mapping, loop-group denominator grouping, HELAS-level color (loop_helas_objects.py, MG5_aMC v3.7.1)
---

# Loop HELAS objects

`$MADGRAPH_INSTALL/madgraph/loop/loop_helas_objects.py`. Turns the abstract `LoopDiagram`/`LoopUVCTDiagram` (from loop_diagram_generation) into concrete HELAS wavefunction/amplitude call chains, and computes the analytic metadata (denominators, ranks, spins, split orders) the exporters need to size the reduction. This is the layer between diagram generation and Fortran emission.

## Class map
- `:49 LoopHelasUVCTAmplitude(helas_objects.HelasAmplitude)` — HELAS form of a UVtree/wavefunction-renorm CT (carries `UVCT_couplings`, `get_UVCT_couplings` :122).
- `:170 LoopHelasAmplitude(helas_objects.HelasAmplitude)` — "an amplitude that also contains loop wavefunctions closed on themselves" (docstring :171-173). Holds `wavefunctions` (the loop line, all `is_loop`), a single `amplitudes` entry (the closing amp; comment :238-240 notes one is always enough), `pairing`, `type` (L-cut PDG), `loop_group_id`, `loopsymmetryfactor`, `multiplier` (:236-261).
- `:555 LoopHelasDiagram(helas_objects.HelasDiagram)` — accessor splits: `get_regular_amplitudes`/`get_ct_amplitudes`/`get_loop_amplitudes`/`get_loop_UVCTamplitudes` (:561-585).
- `:594 LoopHelasMatrixElement(helas_objects.HelasMatrixElement)` — one subprocess; `generate_helas_diagrams` (:770) is the big builder; carries `loop_groups`.
- `:2573 LoopHelasProcess(helas_objects.HelasMultiProcess)` — "always treating only one loop amplitude … one single subprocess without multiparticle labels" (:2574-2577). `matrix_element_class = LoopHelasMatrixElement` (:2580).

## LoopHelasAmplitude — the closed loop
- `is_equivalent` (:186-229): output-level dedup, NOT `__eq__` (deliberately, :189-190). Compares #wfs/#amps, coupling-list lengths, a fixed list of wf args (`fermionflow,lorentz,state,onshell,spin,is_part,self_antipart,color` :200-201), amp lorentz, outgoing numbers, and the is_loop pattern of mothers. Feeds `relabel_loop_amplitudes` (:2048) which assigns the same `number` to equivalent loop amps (default-mode optimization).
- `get_final_loop_wavefunction` (:319-329): the non-external loop mother of the closing amp — the "deepest" loop wf; exactly one expected (else MadGraph5Error). `get_starting_loop_wavefunction` (:308-317) walks `get_loop_mother()` up to the L-cut leg one.
- `get_lcut_size` (:301-306): wavefunction size from L-cut particle spin (`spin_to_size`).
- `get_denominators` (:401-419): returns the loop propagator structure as a tuple of `((external_part_ids), mass)`, one per `D_i=(q+Sum p_j)^2 - m^2` (docstring :402-406). This tuple is THE key by which loops are grouped (see loop_groups).
- `get_masses` (:421-435): loop masses ordered "as they should appear for cuttools (L-cut particles specified last)" (:422-423). Under `aloha.complex_mass` non-zero masses become `CMASS_<m>`.
- `get_orders` (:490-506): coupling orders of the loop chain only (excludes struct wfs), cached.
- `calculate_loopsymmetryfactor` (:534-553): "always 2 for bubble with identical particles and tadpoles with self-conjugated particles and 1 otherwise" (docstring :535-537). Lazily computed on first `get('loopsymmetryfactor')` (:267-268).
- `multiplier` (:256-261): copies of numerically-identical loops (e.g. closed massless quark loops) are merged at generation; the count rides here and into the Fortran call (`LoopMultiplier`, :478).

## Rank / spin metadata — sizes the reduction
The reduction library (CutTools/Ninja/Collier/...) must know the max loop-momentum power and spins. These getters on `LoopHelasMatrixElement` are read by `$MADGRAPH_INSTALL/madgraph/loop/loop_exporters.py` (:1160, :2180-2190, :2409-2419, :2690) to size the loop Fortran:
- `get_max_loop_rank` (:2018-2025): max `wavefunction_rank` (max power of loop momentum in the numerator) over all loop amplitudes.
- `get_max_loop_vertex_rank` (:2011-2016): max `interaction_rank` brought by a single loop interaction — docstring notes "For renormalizable theories, it should be no more than one" (:2013-2014).
- `get_max_spin_connected_to_loop` (:2027-2040): max spin of any particle in or attached to a loop.
- `get_max_loop_particle_spin` (:2042-2046): max spin of a particle running IN the loop.
- `find_max_loop_coupling` (:2003-2009): max #couplings on any loop amplitude.
- The per-amp analytic info (`wavefunction_rank`, `interaction_rank`) is delegated to the final loop wf (`get_analytic_info` :508-515; `LoopRank` flows into the HELAS call :463). `compute_all_analytic_information` (:2310) precomputes & caches so an alohaModel isn't needed later.

## Loop groups — denominator-based reduction grouping (optimized output)
- `identify_loop_groups` (:649-677): groups loop amplitudes by IDENTICAL `get_denominators()` tuple into `self['loop_groups']`. Within a group, amps are sorted by `wavefunction_rank` DESC so the reference (first) has the highest rank (:666-672); groups sorted by smallest reference amp number (:673-676). `loop_group_id` set on each amp (:665, refreshed by `update_loop_group_ids` :688-694).
- Physics: loops sharing the same set of propagators (same denominators) are reduced together — their numerators (open-loop coefficients / LOOPCOEF) are summed before the single reduction call, the core optimized-MadLoop speedup. The grouping is purely denominator-keyed, independent of numerator content.
- `relabel_loop_amplitudes_optimized` (:2066) numbers loop amps for the LOOPCOEF array; grouping by `loop_group_id` happens later (docstring :2067-2071).

## Split-order mapping (:1789+ get_split_orders_mapping)
Returns `(squared_orders, amps_orders)` driving the Fortran split-order indexing.
- `squared_orders`: list of `((OrderValue_i…),(max_contrib_ct_amp_number, max_contrib_uvct_amp_number, max_contrib_loop_amp_number, max_contrib_group_id))` (:1799-1804). The max-contrib numbers are an optimization: if the user wants only one squared-order contribution, all open-loop coefficients with amp number above the cutoff can be skipped (:1811-1822).
- `amps_orders` dict: `born_amp_orders`, `loop_amp_orders` — per-amplitude (un-squared) order values with the contributing amp-number tuples (:1824-1840). Empty if `process['split_orders']` empty; `born_amp_orders` is `()` when no born.
- Outer-list ordering is load-bearing — it dictates the order-index numbering in the exported Fortran (:1842-1844).

## Color at HELAS level
- `LoopHelasMatrixElement.process_color` (:696-712, single-ME path): `relabel_helas_objects()`, then `loop_color_basis.build_loop(base_amplitude)`; if `has_born`, also `build_born` and a born×loop `ColorMatrix`; else a loop-only `ColorMatrix` (:705-712). See ./loop-color-basis.md, ./loop-induced-and-has-born.md.
- `LoopHelasProcess.process_color` (classmethod :2595-2647+, multiprocess path): takes `compute_loop_nc` and constructs `LoopColorBasis(compute_loop_nc=...)` (:2627-2628); recycles an already-seen loop color config via `list_colorize.index` (:2635-2647). THIS is where the loop-induced+MadEvent `compute_loop_nc=True` reaches the color basis.
- Born-vs-loop color-amplitude accessors: `get_born_color_amplitudes` / `get_loop_color_amplitudes` (:2398-2477).

## Probe-confirmed (v3.7.1) — counts are PER-PROCESS, never reuse the integers
The emitted `NLOOPS`/`NLOOPGROUPS`/`NCTAMPS` scale with process content (# loop diagrams, # distinct denominator groups, # CT amplitudes) — re-derive per process from the generated `loop_matrix.f`; the values below are ONE illustration of the mechanism reaching Fortran, not a lookup for any other process. `import model loop_sm; generate g g > t t~ [virt=QCD]; output standalone` ⇒ `SubProcesses/P0_gg_ttx/loop_matrix.f` carries `NLOOPS`/`NLOOPGROUPS` with NLOOPGROUPS < NLOOPS (identify_loop_groups collapses loop amps into denominator-keyed groups — for this process 44 amps → 26 groups), plus `NCTAMPS`, `LOOPFILTERBUFF(NSQUAREDSO,NLOOPGROUPS)`. `global_specs.inc` has `OVERALLMAXRANK=3` (= get_max_loop_rank baked to Fortran), `coef_specs.inc` `MAXLWFSIZE=4` (L-cut wf size from max spin). Emitted loop files: `loop_CT_calls_1.f`, `helas_calls_uvct_1.f` (UVCT amps), `loop_num.f`, `improve_ps.f`, `CT_interface.f`/`COLLIER_interface.f` (reduction interfaces). Confirms loop-group grouping + rank/spin getters reach Fortran.

## Cautions
- `reuse_outdated_wavefunctions` (:679-686) is deliberately neutered for loops ("make sure never to use this optimization in the loop context") — sets `me_id=number`. A tree-level wf-reuse optimization is intentionally OFF in the loop layer.
- `get_max_loop_vertex_rank` >1 signals a non-renormalizable / higher-dim operator in the loop (EFT) — exporters use it to size the numerator update; a model that yields rank>1 is exercising a bigger reduction than the renormalizable default. (caution, not a runtime claim)
- The rank/spin getters are CONSUMED by loop_exporters.py (nlo-export-adjacent), but the metadata definitions and their physics meaning are this HELAS slice; cited consumer lines are the boundary.
