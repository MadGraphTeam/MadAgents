---
description: Cross-cutting principle — HelasMatrixElement query methods are stateless live-reads over a MUTABLE in-place ME; the ME is mutated/renumbered at well-defined lifecycle stages, so a query's answer depends on WHEN it is called relative to those mutations. Call ordering is load-bearing.
---

# HELAS-ME query methods are live-reads over a mutable ME (call ordering is load-bearing)

Cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (v3.7.1).

## The principle
A `HelasMatrixElement` is NOT immutable after construction. Its `diagrams` / per-diagram `wavefunctions` / `color_basis` are mutated **in place** — wfs and amps renumbered, slots remapped, lists rebuilt — at several well-defined lifecycle stages. The exporter-facing query methods (`get_number_of_wavefunctions`, `get_used_lorentz`, `get_color_amplitudes`, `get_base_amplitude`, …) are **stateless live-reads**: they recompute from whatever `self.get('diagrams')` holds at call time and cache nothing. **Therefore the same query returns different answers depending on WHEN in the lifecycle it runs.** Any code (or any consultant reasoning) that quotes a query's result without pinning the lifecycle stage is unsound.

This is the static (source-level) call-ordering analog of the lead's `config-value-lifecycle-layers` playbook ("latest stage governs; written value ≠ enforced value") — but at the in-memory HELAS-object level, not the on-disk card level. It is a method-semantics property, NOT a runtime prediction, so it is grounded by source-walk alone.

## The mutation stages (when the ME changes under you)
1. **`reuse_outdated_wavefunctions(helas_diagrams)` @3866** — assigns `me_id` memory slots (the Fortran W() index); reversible by `restore_original_wavefunctions` @3926 (resets `me_id = number`). Called from call-writers' `get_matrix_element_calls` right before emission.
2. **`insert_decay_chains` / `insert_decay` (@3940 / @4087)** — decay-chain stitching: deepcopies decay diagrams, multiplies production diagrams by Ndiag, offsets `number_external`, then renumbers EVERY wf and amp `number=i+1` and **recomputes** each amp's fermionfactor + color_indices (@4073-4080). See decay-chain-helas-assembly page.
3. **Majorana fermion-flow clash (`check_majorana_and_flip_flow` @1207)** — `copy.copy`s clashing wfs with new numbers, inserts respecting mother-before-daughter ordering, renumbers later wfs, rewrites `number_to_wavefunctions`. See fermion-flow-clash-majorana page.
4. **`process_color` @5749** — (re)builds/attaches `color_basis` + `color_matrix`; `get_color_amplitudes` reads the CURRENT pair.

## Why each query is stage-sensitive (the verified live-reads)
- **`get_number_of_wavefunctions` @4740**: `max(wf.me_id ...)` if that is non-zero, ELSE `sum(len(d.wavefunctions))`. So it returns the *recycled slot count* only AFTER `reuse_outdated_wavefunctions`; before reuse (or after `restore`) it returns the raw count. Same method, two answers, gated on stage 1.
- **`get_used_lorentz` @5092 / `get_used_couplings` @5104**: iterate `get_all_wavefunctions() + get_all_amplitudes()` live, skipping interaction_id ∈ {0,-1}. Reflects whatever wfs exist at call time — called before stage 2/3 (decay insert / Majorana flip) it misses the inserted/flipped wfs.
- **`get_color_amplitudes` @4978 → `generate_color_amplitudes` @4933**: reads CURRENT `diagrams` and `color_basis`. If `color_indices` drifted (stage 2/3 mutation) without a `color_basis` rebuild (stage 4), it **raises** `PhysicsObjectError "No amplitude found for color structure…"` @4960 — a desync surfaces here loudly, not silently.
- **`get_base_amplitude` @4675**: infers `optimization=0` when >1 live wf has `number==1` @4684 — a signal that depends on the current numbering. Its own docstring warns it needs decay-chain diagram-numbering care BEFORE it is valid (@4680-4681), so on a not-yet-finalized decay-chain ME it (and `get_num_configs`, which rides `base_amplitude`) can be wrong.

## Where this catches MORE than the instances
- Each instance page carries a single local caution ("cached numbers invalid after this mutation" / "called before reuse it reflects whatever exists"). This page names the ONE mechanism behind all of them and predicts the trap for **any** query method in the slice, including ones not yet documented: if a method recomputes from `self.get('diagrams')` and caches nothing, its answer is stage-dependent.
- It predicts the reverse direction too: `restore_original_wavefunctions` UN-does stage 1, so a query that was "correct" can become "raw" again after a restore — the dependency is not monotone.

## Caution
When quoting any HELAS-ME query result (wf count, used-lorentz set, JAMP list, num_configs), pin the lifecycle stage: pre/post reuse, pre/post decay-insert, pre/post Majorana-flip, pre/post color-build. "The ME has N wavefunctions" is incomplete without "at stage S". For a decay-chain or Majorana process this is the difference between a right and a wrong number.
