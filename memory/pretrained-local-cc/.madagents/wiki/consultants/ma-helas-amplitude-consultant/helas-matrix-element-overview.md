---
description: HelasMatrixElement construction pipeline — constructor steps, generate_helas_diagrams flow, the central classes (HelasWavefunction/Amplitude/Diagram) and their stored properties.
---

# HelasMatrixElement construction overview

All cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (v3.7.1).

## Class hierarchy / entry points
- `HelasWavefunction(base_objects.PhysicsObject)` @547 — one helicity wavefunction. Key props (default_setup @569): `interaction_id`, `pdg_codes`, `inter_color`, `lorentz`(list), `coupling`(list), `color_key`, `state` (initial/final/intermediate/incoming/outgoing), `leg_state`, `mothers`(HelasWavefunctionList), `number_external`, `number`, `me_id`, `fermionflow`(+/-1; -1 only on Majorana flow clash @612-614), `decay`, `onshell`, `conjugate_indices`, `polarization`.
- `HelasAmplitude` @2585 — the last-vertex object producing a JAMP term; holds `fermionfactor`, `coupling`, `lorentz`, `color_indices`, `mothers`, `number`.
- `HelasDiagram` @3338 — list of `wavefunctions` + `amplitudes`.
- `HelasMatrixElement` @3431 — central. default_setup @3452: `processes`(ProcessList), `diagrams`(HelasDiagramList), `identical_particle_factor`(int, default 0), `color_basis`, `color_matrix`, `base_amplitude`, `has_mirror_process`(bool).

## Constructor `__init__(amplitude=None, optimization=1, decay_ids=[], gen_color=True)` @3512
Sequence when given an `Amplitude` (@3519-3529):
1. append `amplitude.process` to `processes`; set `has_mirror_process`.
2. `generate_helas_diagrams(amplitude, optimization, decay_ids)` @3580.
3. `calculate_fermionfactors()` @4661 (forces each amp's fermionfactor).
4. `calculate_identical_particle_factor()` @4668 — delegates to `process.identical_particle_factor()`.
5. if `gen_color` and no color_basis yet: `process_color()` @3570 → builds color_basis + color_matrix.
If `amplitude` is a dict, treated as PhysicsObject init (@3530-3532).

## `spin_to_size` @559
`sizes = {1:1, 2:4, 3:4, 4:16, 5:16}` (@563) keyed on abs(spin) (2s+1). Wavefunction element count.

## Helicity / averaging
- `get_helicity_matrix(allow_reverse=True)` @4834 — `itertools.product` over each external wf's `polarization` (if set) else `model.particle.get_helicity_states(allow_reverse)`. (get_helicity_states itself is model/base_objects, out of slice.)
- `get_helicity_combinations` @4818 — product of per-particle hel counts.
- `get_denominator_factor` @4910 — spin_factor * color_factor (initial-state) * `identical_particle_factor`. color_factor from initial-leg particle 'color'; spin_factor uses polarization length if partial-pol else helicity-state count.
- `get_hel_avg_factor`/`get_beams_hel_avg_factor` @4851/@4894 — initial-state spin-average denominators (beams separate for partial polarization).

## Equality `__eq__` @3539
Two MEs equal iff: both have processes, same `has_mirror_process`, same process `id`, NEITHER is_decay_chain, same `identical_particle_factor`, and `diagrams` equal. Decay-chain MEs are never equal (always split).

## Caution
- `identical_particle_factor` default is 0 (not 1) until `calculate_identical_particle_factor` runs; a freshly dict-constructed ME without the Amplitude path will carry 0.
