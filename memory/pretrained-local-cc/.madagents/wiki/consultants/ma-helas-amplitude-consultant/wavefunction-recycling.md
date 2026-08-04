---
description: Wavefunction recycling in generate_helas_diagrams — the optimization=1/0 toggle, within-diagram and cross-diagram dedup keys (__eq__, to_array, wf_mother_arrays), and the me_id memory-slot reuse feeding the Fortran W() indices.
---

# Wavefunction recycling

Cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` and `.../iolibs/helas_call_writers.py` (v3.7.1).

## generate_helas_diagrams @3580
Per-process arrays maintained across diagrams: `wavefunctions=[]` (all previously defined wfs), `wf_mother_arrays=[]` (each wf's `to_array()`, parallel list), `wf_number` counter (starts at `len(legs)` @3620).

External wfs built first @3614; initial-state bosons flip part/antipart (treated outgoing) @3624-3628; initial-state fermions flip PDG @3632-3636.

### Two-level dedup (per generated wf @3725-3741)
1. **Within current diagram**: `diagram_wavefunctions.index(wf)` (uses `HelasWavefunction.__eq__` @2201) → reuse existing diagram wf.
2. **Cross-diagram** (only meaningful with optimization): after assigning a new `number`, look up `wf_mother_arrays.index(wf.to_array())`; on hit, reuse the prior `wavefunctions[...]` object and decrement `wf_number` back (no new wf emitted).

`__eq__` @2201 compares number_external, fermionflow, color_key, lorentz, coupling, state, onshell, spin, self_antipart, mass, width, color, decay (+ particle if decay), and **sorted mother numbers**. The wf's own `number`, `pdg_code`, `interaction_id` are explicitly irrelevant (docstring @2204-2206).

**Key asymmetry — the two dedup keys are NOT the same property set.** `to_array()` @1053-1071 (the cross-diagram key) is `[interaction_id, color_key, int(is_loop), *mother_numbers]` — it keys ON `interaction_id`, which `__eq__` declares irrelevant. Note a second asymmetry in HOW mothers enter each key: `__eq__` sorts the mother-number lists at compare time (@2230-2231 `sorted([...])`), but `to_array` appends mother numbers in **stored order** (@1068, no sort). Cross-diagram dedup therefore relies on two physics-identical wfs having their mothers stored in the same deterministic (pdg-sorted at construction) order, not on a sort inside `to_array`. So within-diagram dedup (`.index(wf)` → `__eq__`) compares full physics content and ignores interaction_id, while cross-diagram dedup (`wf_mother_arrays.index(wf.to_array())`) uses interaction_id as a cheaper/stronger discriminator (same interaction+color_key+mothers within a process ⇒ same physics). Do not assume one principle governs both keys. (This is one instance of a slice-wide rule — see identity-keys-purpose-tuned page for all four HELAS identity keys and their differing inclusion-sets.)

### optimization toggle @3844-3849
- `optimization=1` (default): after each diagram, `wavefunctions.extend(diagram_wavefunctions)` and extend `wf_mother_arrays` — so later diagrams can recycle. Class docstring @3439 offers ~15% of #amplitudes as a rule-of-thumb for the optimized total wf count — a docstring approximation, NOT a per-process guarantee; the actual recycled count is process-specific (read `get_number_of_wavefunctions` after reuse, or the emitted `NWAVEFUNCS`).
- `optimization=0`: reset `wf_number = len(legs)` after each diagram; nothing carried over → each diagram self-contained (for restricted memory / GPU).

### Mother-before-daughter ordering @3823-3839
After per-diagram generation, sort diagram_wavefunctions by `number`, then bubble any wf appearing as a mother to before its daughter.

## me_id: memory-slot reuse — reuse_outdated_wavefunctions @3866
Called from `get_matrix_element_calls` @232 (call_writers) right before emitting (NOT for loop MEs @228).
- optimization=0 path @3871: `me_id = number` verbatim.
- optimization=1: computes first/last appearance line of each wf, then reassigns the smallest free slot — an `outdated` stack of freed slot-ids is popped when a new wf appears @3907-3917. Result stored in each wf's `me_id`.
- `restore_original_wavefunctions` @3926 resets `me_id = number`.

## me_id → Fortran
FortranHelasCallWriter wavefunction/amplitude templates use `wf.get('me_id')` for the W() array index and mother indices @386-430; amplitudes use `amp.get('number')` for the AMP() index. So me_id is the actual Fortran wavefunction-array slot, distinct from `number`.

## Cautions
- `get_number_of_wavefunctions` @4740 returns `max(me_id)` if reuse has run, else the raw count — the value depends on whether reuse_outdated_wavefunctions already executed.
- `get_base_amplitude` @4675 infers optimization=0 when >1 wf has number==1 (a signal of the no-recycle layout).
