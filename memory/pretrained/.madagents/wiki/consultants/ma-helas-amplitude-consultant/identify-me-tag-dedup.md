---
description: IdentifyMETag matrix-element dedup — what create_tag compares, the FKS/MadSpin variants, CanonicalConfigTag for configs, and the HelasMultiProcess.generate_matrix_elements combine loop.
---

# IdentifyMETag dedup and CanonicalConfigTag

Cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (v3.7.1).

## IdentifyMETag(DiagramTag) @59
Identifies processes with identical matrix elements so they share one HelasMatrixElement. Compares (docstring @60-72): leg number, color, lorentz, coupling, state, spin, self_antipart, mass, width, color, decay, is_part — plus has_mirror_process, process id, identical_particle_factor. Never combines decay chains; never combines processes differing in possibly-onshell s-channel propagators (to write the right resonance in the LHE).

### create_tag(amplitude, identical_particle_factor=0) @79 returns a 7-element list:
`[has_mirror_process, process.id, is_decay_chain, identical_particle_factor, dc, perms, sorted_tags]` @123-129.
- `dc` = a monotonic `dec_number` (class var @77) when is_decay_chain, separating distinct decays so identical/non-identical factors stay right.
- `sorted_tags` = sorted per-diagram tags (FKS variant if perturbation & NLO_mode not in virt/loop/noborn @91-94; contracted-loop tag for loop-induced @95-101; else base `cls(d,...)` @102-104).
- `perms` @116-118 = relative external-leg permutations of diagrams 1.. vs diagram 0, via `prepare_comp_dict` @131 which makes identical particles symmetric (lists of positions). Not built for LoopAmplitude.

### link_from_leg @163 / vertex_id_from_vertex @183
- leg link encodes: number (0 for FS legs, real for IS), id (0 unless onshell decay leg), spin, onshell, is_part, self_antipart, mass, width, color, + leg number @178-181.
- vertex encodes: sorted couplings, color strings, lorentz, sorted orders; for non-last vertex adds propagator (spin,color,self_antipart,mass,width, s_pdg). `s_pdg` zeroed when width=='zero' or onshell==False @213-215 (so only genuinely-resonant props split processes).

## Variants
- `IdentifyMETagFKS` @237 — adds `flow_charge_diff` (charge diff along fermion flow for IS legs) to the comparison; `__eq__` @245 ANDs it.
- `IdentifyMETagMadSpin` @250 — `vertex_id_from_vertex` @256 replaces the s_pdg slot with `random.random()` for non-last vertices → effectively ignores onshell-s-channel PDG, so splittings combine the same with/without decay.

## CanonicalConfigTag(DiagramTag) @274
Canonical config ordering for integration channels. Compares leg number, mass, width, color. `get_s_and_t_channels` @283 reconstructs s-/t-channel vertex lists by walking the tag toward leg 2 (or 1). Docstring warning @278-280: sorting MUST match `IdentifySGConfigTag` in diagram_symmetry.py or symmetry breaks.

## generate_matrix_elements @5817 (HelasMultiProcess, classmethod)
For each amplitude: build `IdentifyMETag.create_tag(...)`; if tag already in `amplitude_tags` and combine → don't build a new ME, instead `reorder_process` the new process onto the matching ME's process list @5949-5960 (logs "Combined ... with ..."). Else build `cls.matrix_element_class(amplitude, decay_ids=, gen_color=False)` @5933.
- `combine = combine_matrix_elements` (default True via HelasMultiProcess @5683); forced False for MadSpin mode @5837-5839, and bypassed when `not combine` @5889.
- Color processed once per surviving ME via `process_color` @5978.
- DecayChainAmplitude path @5870 routes through `HelasDecayChainProcess.combine_decay_chain_processes` first.

## IdentifyMETag does NOT compute the identical-particle symmetry factor
Common conflation: that IdentifyMETag "groups identical-final-state permutations and applies the 1/n! symmetry factor." FALSE. Two separate mechanisms:
- **Symmetry factor computed elsewhere:** `Process.identical_particle_factor()` in `$MADGRAPH_INSTALL/madgraph/core/base_objects.py:3742` — counts final-state legs (incl. decays) keyed by `(id, polarization)`, returns `prod(factorial(count))`. For `p p > z z` → two identical Z → 2!=2. Stored on the ME by `calculate_identical_particle_factor` @4668 (reads `process[0].identical_particle_factor()`), consumed as the denominator by `get_denominator_factor` @4910-4931 (so |M|² is divided by it → σ ∝ 1/2 for zz). No manual user correction needed — but this is base_objects/HelasMatrixElement, NOT IdentifyMETag.
- **IdentifyMETag's role:** cross-*process* ME deduplication (merge distinct subprocesses that yield the identical squared ME into one HelasMatrixElement, e.g. `u u~ > ...` and `d d~ > ...`). It merely *includes* `identical_particle_factor` as one equality field @126 so processes with DIFFERENT symmetry factors are never merged. It neither computes nor applies the factor. The `perms`/`prepare_comp_dict` machinery @116-161 that "treats identical particles symmetrically" is about not falsely distinguishing two MEs that differ only by identical-leg relabeling — a comparison concern, not a symmetry-factor concern. It does not combine identical-FS *permutations within one process into a symmetry factor*; MG5 sums all helicity/leg amplitudes and divides by the separately-computed factor.

## Cautions
- `dec_number` is a mutating class variable @77 incremented per decay-chain tag — global state across create_tag calls within a session.
- IdentifyMETagMadSpin's random s_pdg means the tag is non-deterministic across runs by design (only used to suppress onshell-prop splitting).
