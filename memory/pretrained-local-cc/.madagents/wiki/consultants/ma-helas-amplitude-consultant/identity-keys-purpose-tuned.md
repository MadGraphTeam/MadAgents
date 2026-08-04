---
description: Cross-cutting principle — every identity/comparison key in the HELAS layer is purpose-tuned to its consumer's equivalence notion with a DIFFERENT property subset, so never assume one key's inclusion-set governs another; plus the four independent sharing axes (within-diagram recycle, cross-diagram recycle, call-lambda dedup, ME-dedup) and a fourth color-matrix recycling axis (process_color, probe-verified distinct from ME-dedup).
---

# Identity keys are purpose-tuned (never assume one governs another)

Cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (v3.7.1).

## The principle
The HELAS layer compares wavefunctions / diagrams / matrix-elements at several distinct points, each for a different question ("can I reuse this wf within a diagram?", "across diagrams?", "can two wfs share one emitted CALL lambda?", "are two whole processes the same ME?"). **Each comparison defines its own identity key, and each key deliberately includes a different subset of properties.** A property that is *irrelevant* to one key can be *load-bearing* in another. The recurring trap is reasoning about reuse/dedup behavior by carrying one key's inclusion-set over to another.

This generalizes the "two dedup keys are NOT the same property set" caution on the wavefunction-recycling page from a 2-key observation to the rule across **all four** identity keys in the slice — and it predicts the same caution for any future key added in this layer.

## The four keys and their inclusion/exclusion sets

| Key | Site | Question | Includes | Notably excludes |
|-----|------|----------|----------|------------------|
| `HelasWavefunction.__eq__` @2201 | within-diagram recycle (`diagram_wavefunctions.index(wf)`) | same physics wf already in THIS diagram? | number_external, fermionflow, color_key, lorentz, coupling, state, onshell, spin, self_antipart, mass, width, color, decay, sorted mother **numbers** | own `number`, `pdg_code`, `interaction_id` (docstring @2204-2206) |
| `HelasWavefunction.to_array` @1053 | cross-diagram recycle (`wf_mother_arrays.index(wf.to_array())`) | same wf already built in a PRIOR diagram of this process? | **interaction_id**, color_key, is_loop, mother **numbers** | everything `__eq__` checks beyond those (interaction_id+color_key+mothers ⇒ same physics within a process) |
| `HelasWavefunction.get_call_key` @1719 | emit-call lambda dedup (`self["wavefunctions"][key]` in call writers) | can two wfs share ONE emitted Fortran CALL lambda? | mother **spin-states** (`get_spin_state_number`, NOT numbers), own spin-state, outgoing#, [loop index/is_part], polarization, onshell, [conjugate_indices if hermitian], lorentz | mother numbers, color_key, mass/width — only the call-shape matters |
| `IdentifyMETag.create_tag` @79 | whole-ME dedup at multiprocess (`amplitude_tags.index`) | are two PROCESSES the same matrix element? | has_mirror_process, process.id, is_decay_chain, identical_particle_factor, dc (decay-chain counter), perms (relative leg permutations), sorted per-diagram physics-content tags | concrete pdg of non-resonant props (s_pdg zeroed when width=='zero'/onshell==False @213-215) |

(`CanonicalConfigTag` @274 is a fifth DiagramTag key, but for config canonicalization rather than dedup — leg number/mass/width/color only; see identify-me-tag-dedup page.)

## The three contrasts that bite
1. **interaction_id**: irrelevant to `__eq__`, load-bearing in `to_array`. Same interaction+color_key+mothers within a process is taken as sufficient for "same physics" by the cross-diagram key.
2. **mother numbers vs mother spin-states**: both recycle keys (`__eq__`, `to_array`) key on mother *numbers* (a specific wf instance); `get_call_key` keys on mother *spin-states* (a structural class), because two structurally-identical CALLs reuse one lambda even with different mother wfs.
3. **PDG of propagators**: a genuine resonant s-channel splits MEs in `IdentifyMETag`, but a zero-width/off-shell propagator's pdg is zeroed (@213-215) so it does NOT split — and `IdentifyMETagMadSpin` randomizes the slot entirely @256.

## Where this catches MORE than the instances
- The wavefunction-recycling page documents contrast (1) for two keys. This page extends the discipline to `get_call_key` (contrast 2) and to ME-level tags (contrast 3) — keys living on different pages.
- It predicts the trap for any *new* identity key added to this layer: read the constructor, don't assume it mirrors a neighboring key.

## A fourth axis: color-matrix recycling (independent of ME-dedup)
Beyond the four *comparison keys* above, the slice runs a separate sharing pass at the color/storage boundary: `HelasMultiProcess.process_color` @5749 recycles a `color_basis`+`color_matrix` across MEs via `list_colorize.index(colorize_obj)` @5786 — keyed on the **colorize object**, NOT on `IdentifyMETag`. So two MEs that are NOT the same ME (distinct IdentifyMETag, never combined) can still SHARE one color matrix when their colorize objects match. This is a genuinely independent equivalence relation, not a restatement of any comparison key.

**Probe-verified** (non-grouped standalone export, `u u~ > d d~` + `c c~ > s s~`, `group_subprocesses False`): the first logs `Processing color information for process: u u~ > d d~`, the second logs `Reusing existing color information for process: c c~ > s s~`. Two distinct MEs (different external pdg ⇒ different IdentifyMETag, never combined) share one color matrix. NOTE: the madevent default **subprocess-grouping** path uses a different color handler and logs `Processing` for both — the `HelasMultiProcess.process_color` recycle fires on the non-grouped / standalone export path, so to observe the reuse you must take that path. (Color algebra is the color-decomposition slice; this is the storage/recycling-axis integration only — see split-orders-and-exporter-helpers page.)

## Caution
Do not collapse "recycled together" (recycle keys) with "shares an emitted CALL" (call key) with "same ME" (IdentifyMETag) with "shares a color matrix" (`process_color` colorize index) — **four** independent equivalence relations. A wf can be a distinct recycle-slot yet share a CALL lambda with another wf; two processes can be distinct MEs yet share one color matrix. Sharing on one axis never implies sharing on another.
