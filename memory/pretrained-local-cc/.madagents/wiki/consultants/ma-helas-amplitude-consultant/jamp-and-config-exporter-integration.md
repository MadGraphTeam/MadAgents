---
description: HelasMatrixElement→exporter integration — get_color_amplitudes assembles stored color_basis into JAMP (coeff, amp#) lists (coeff tuple → coeff() Fortran prefix), and get_s_and_t_channels/get_num_configs/get_nb_t_channel reconstruct integration channels for configs.inc/multichannel.
---

# JAMP color-amplitude assembly and config/channel reconstruction (exporter integration)

Cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` and `.../iolibs/export_v4.py` (v3.7.1). These are the HELAS-layer methods the iolibs exporters CALL to turn a `HelasMatrixElement` into the JAMP sums and channel data in `matrix_*.f` / `configs.inc`. This is the "storage + integration with the helicity calls" part of my slice; the color *algebra* (what's IN color_basis) is the color-decomposition slice, diagram *enumeration* is the diagram-generation slice.

## JAMP assembly — get_color_amplitudes / generate_color_amplitudes @4978 / @4933
`get_color_amplitudes()` @4978 = `generate_color_amplitudes(self['color_basis'], self['diagrams'])`. Returns **one list per JAMP** (per color-basis element), each a list of `(coefficient, amplitude_number)` pairs. The coefficient tuple is `(fermionfactor, colorcoeff-as-Fraction, imaginary-bool, Nc-power)` (docstring @4936).
- **No color basis** @4939-4948: returns a SINGLE JAMP containing every amplitude with coeff `(fermionfactor, 1, False, 0)`. So a colorless ME has exactly one color amplitude.
- **With color basis** @4953-4974: iterates `sorted(color_basis.keys())` (sorted → deterministic JAMP order). For each color-basis element, each `diag_tuple = (diag_index, color_index_chain, frac, imaginary, Nc_power)` selects the amplitudes in `diagrams[diag_tuple[0]]` whose `tuple(color_indices) == diag_tuple[1]` @4959. **Raises** `PhysicsObjectError "No amplitude found for color structure..."` @4960-4965 if the color basis references a (diagram, color-index-chain) with no matching amplitude — a HELAS/color-basis desync surfaces here, not silently.
- Each surviving amp contributes `((res_amp.fermionfactor, diag_tuple[2], diag_tuple[3], diag_tuple[4]), res_amp.number)` @4968-4972 — i.e. the amp's OWN fermionfactor times the color-basis-element's (frac, imaginary, Nc_power).

### The coefficient tuple → Fortran prefix: coeff() @export_v4 2285
`get_JAMP_lines` (export_v4 @1575, @3341 — dispatches `col_amps.get_color_amplitudes()` when handed a HelasMatrixElement @3340-3341) formats each `(coeff_tuple, amp#)` into a `JAMP(i) = ...±coeff*AMP(amp#)...` line. The tuple is collapsed by `coeff(ff_number, frac, is_imaginary, Nc_power, Nc_value=3)` @2285:
- `total_coeff = ff_number * frac * Fraction(Nc_value)**Nc_power` @2288 — the four-element tuple becomes ONE rational number (Nc=3 substituted at output time).
- `+1`→`'+'`, `-1`→`'-'` (with `imag1*` if imaginary) @2290-2299; otherwise `'%+iD0[/%iD0]*[imag1*]'` Fortran double-precision literal @2301-2310.
So **Nc is numerically substituted (Nc=3) at emission** — the JAMP coefficients in `matrix_*.f` are concrete rationals, not symbolic in Nc. (export_python/export_cpp have their own `coeff` @390/@1331/@1534 with the same signature.)

### Consumers (the integration surface)
`get_color_amplitudes()` is read by EVERY exporter: export_v4 `get_JAMP_lines`/`get_JAMP_lines_split_order` @1513/@1587/@3341, export_python @230, export_cpp @827/@893/@2051, and the GPU writer's interleaved jamp accumulation (helas_call_writers GPU path @2034-2036, see helas-call-writers page). `get_JAMP_coefs` @1451 turns them into DATA statements when JAMP init is moved to a coef table. `get_icolamp_matrix` @1296 derives which JAMPs each diagram touches (ICOLAMP) from the same color_basis.

## Base-diagram reconstruction — get_base_amplitude / get_base_diagram (the inverse map)
`get_base_amplitude` @4675 rebuilds a `diagram_generation.Amplitude` FROM the HelasMatrixElement — the inverse of `generate_helas_diagrams`. Used to feed BOTH `get_color_amplitudes` (color algebra needs the diagram structure) AND diagram drawing AND `get_num_configs`/`get_s_and_t_channels` (via `base_amplitude`).
- Infers `optimization` from the current numbering: `optimization=0` iff >1 live wf has `number==1` @4684 (the no-recycle layout signal — see helas-me-mutation-lifecycle page; this is stage-sensitive).
- Per diagram, calls `diag.amplitudes[0].get_base_diagram(wf_dict, vx_list, optimization)` @4693 → `HelasAmplitude.get_base_diagram` @3060 → recursive `HelasWavefunction.get_base_vertices` @1750 walking mothers depth-first, each wf → `get_base_vertex` @1779 producing a `base_objects.Vertex{'id': interaction_id, 'legs': [...]}`.
- **`wf_dict` memoization** keyed `(wf.number, wf.onshell)` for the lastleg and `(mother.number, False)` for mother legs (@1793/@1804/@1811/@1822): a Leg built once per wf-number is REUSED across diagrams, so shared wfs map to the same Leg object. **Skipped entirely for loop wfs** (`is_loop` → `raise KeyError` forces a fresh Leg every time @1790-1792/@1808-1810) and when `optimization==0` (no caching @1803/@1821). The Vertex carries the wf's ORIGINAL `interaction_id` (@1828) — so the base diagram recovers the true vertex id even though `to_array`/recycling folded wfs together.
- `getmothers` @4705 is the forward counterpart used IN generate_helas_diagrams: resolves each leg-number to an existing wf via `number_to_wavefunctions`, else pulls the external wf and registers it.

## Config / integration-channel reconstruction
The HELAS layer reconstructs the s-/t-channel structure used for phase-space multichanneling (`configs.inc`, channel maps). All route through `CanonicalConfigTag` (see identify-me-tag-dedup page) for canonical propagator ordering.

### get_s_and_t_channels — two entry points
- `HelasAmplitude.get_s_and_t_channels(ninitial, model, new_pdg, reverse_t_ch=False)` @3105: builds `CanonicalConfigTag(self.get_base_diagram(...).get_contracted_loop_diagram(model), model)` @3120 then delegates to `tag.get_s_and_t_channels(...)` @3123. `reverse_t_ch` flips the toward-leg from 2 (`max_final_leg=2`) to 1. This is the production path exporters use (export_v4 @2209/@4086/@5463 write `configs.inc` from it; export_fks @1540/@1646/@3927 use `new_pdg=990`).
- `HelasWavefunction.get_s_and_t_channels(ninitial, mother_leg, reverse_t_ch=False)` @1926: the recursive worker. Splits mothers into final-state (`number_external > ninitial`, become s-channel sub-vertices @1942-1946) and initial-state (≤ ninitial). **Asserts ≤2 initial-state mothers** @1951-1952. Single init-mother → recurse down toward external leg `startleg` (1, or 2 if reverse) building t-channels; the resulting propagator leg is renumbered to `min` of its mothers' numbers @1983 (the canonical "lowest final-state leg number" convention named in the @1931 docstring).

### get_num_configs @4729 / get_nb_t_channel @3405 / get_vertex_leg_numbers @3394
- `get_num_configs()` @4729: `sum(d.get_num_configs(model, nini) for d in base_amplitude.diagrams)` — "always more than number of configs" (docstring @4730). Drives `maxconfigs` in export_v4 @5284-5287 (sizes the config arrays) and group_subprocs @312.
- `HelasDiagram.get_nb_t_channel()` @3405 → amplitude's `get_nb_t_channel`. group_subprocs @370 vetoes a diagram as a multichannel config when `get_nb_t_channel() > max_tpropa`.
- `get_vertex_leg_numbers(veto_inter_id=Vertex.ID_to_veto_for_multichanneling, max_n_loop=0)` @3394-3396: leg-counts per vertex, with default vetoes for which interactions/loop-orders may seed a multichannel config. **`max_n_loop` signature default is `0`** (NOT `Vertex.max_n_loop_for_multichanneling`); `0` is resolved in-body to `Vertex.max_n_loop_for_multichanneling` @3401-3402. Only `veto_inter_id` defaults straight to the Vertex attribute.

## Cautions
- `generate_color_amplitudes` will **raise** (not skip) on a color_basis ↔ amplitude desync @4960 — a genuine error surface, e.g. if color_indices drifted after a mutation (decay insert / Majorana flip) without color_basis rebuild. `get_color_amplitudes` reads the CURRENT `diagrams`/`color_basis`, so call ordering matters (cf. get_used_lorentz caution, split-orders page).
- Nc=3 is hard-substituted at emission via `coeff()` @2288 — the emitted JAMP coefficients are not symbolic in Nc; an Nc≠3 study cannot just re-read the Fortran. (The symbolic Nc lives in the color-decomposition slice's ColorMatrix, before this substitution.)
- `get_base_amplitude` @4675 (which feeds `get_num_configs` via `base_amplitude`) infers `optimization=0` when >1 wf has `number==1` @4684 — a decay-chain ME warns it needs diagram-numbering care before this is valid (@4680-4681 comment). So `get_num_configs` on a not-yet-finalized decay-chain ME can be wrong.
