---
description: Amplitude / DecayChainAmplitude / MultiProcess data structures and the auto-generation entry points in diagram_generation.py
---

# Amplitude data structures (diagram_generation.py)

All citations: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` (v3.7.1, 2206 lines).

## Amplitude (class :433)
- "Amplitude: process + list of diagrams (ordered)" (:434).
- `default_setup` (:439): keys `'process'` (`base_objects.Process()`), `'diagrams'` (`None`), `'has_mirror_process'` (`False`). `get_sorted_keys` returns exactly these three (:487).
- `__init__` (:448): if `argument` is a `base_objects.Process`, it auto-calls `self.generate_diagrams()` (:453). Any other non-None argument goes to the mother routine without generation.
- `get('diagrams')` (:475): lazy — if `'diagrams'` is still `None` and a process is set, calls `generate_diagrams()` on access (:478-481).
- `has_mirror_process` doc (:444): "True if the same process but with the two incoming particles interchanged has been generated." It is a bool flag on the kept amplitude, set by `MultiProcess` (see `multiprocess-crossing-mirror.md`), NOT set inside `generate_diagrams`.
- `has_loop_process` (:515) returns `process.get('perturbation_couplings')` (truthy iff perturbed).

## AmplitudeList (class :1317)
- `has_any_loop_process` (:1321) — true if any contained amp `has_loop_process`.
- `is_valid_element` (:1329) requires `isinstance(obj, Amplitude)`.

## DecayChainAmplitude (class :1337, subclass of Amplitude)
- `default_setup` (:1342): keys `'amplitudes'` (`AmplitudeList`) and `'decay_chains'` (`DecayChainAmplitudeList`). Note: does NOT carry `'process'`/`'diagrams'`/`'has_mirror_process'` — different shape from Amplitude.
- Construction branch and prohibitions: see `decay-chain-amplitude.md`.
- `get_number_of_diagrams` (:1472) sums own amplitudes' diagram counts + recurses into decay_chains.
- `get_amplitudes` (:1526) recursively flattens core + all decay amplitudes into one AmplitudeList.
- `get_decay_ids` (:1508) returns unique initial-state ids across all decay-chain amplitudes (via `get_initial_ids()[0]`).
- `get_ninitial` (:1504) reads from `amplitudes[0]` (the core), not the decays.

## MultiProcess (class :1554)
- "list of process definitions / list of processes / list of amplitudes" (:1555).
- `default_setup` (:1560): `process_definitions`, `amplitudes`, `collect_mirror_procs` (False), `ignore_six_quark_processes` ([]), `use_numerical` (False). `__init__` also stashes `loop_filter` and `diagram_filter` (:1600-1601).
- `__init__` (:1577): accepts ProcessDefinition or ProcessDefinitionList; triggers generation eagerly by touching `self.get('amplitudes')` (:1606).
- `get('amplitudes')` (:1630): lazy build. Per process_def — if it has `decay_chains`, wrap in a `DecayChainAmplitude` (:1638); else call `generate_multi_amplitudes` (:1644). This is the routing fork between plain and chain-decay processes.
- `generate_multi_amplitudes` (classmethod, `def` :1664, decorator :1663) — the multiparticle-expansion + crossing/mirror entry (see `multiprocess-crossing-mirror.md`).
- `get_amplitude_from_proc` (classmethod :1919) returns `Amplitude({"process": proc})`. Overridden by `LoopMultiProcess`/`LoopInducedMultiProcess` (loop subclasses) to return loop amplitudes.

## Cautions
- `Amplitude(Process)` is eager — instantiating with a Process runs full diagram generation immediately (:453). Cheap to instantiate only with a dict argument.
- `get('diagrams')` mutates: first access triggers generation. Reading is not side-effect free.
- `DecayChainAmplitude` is an `Amplitude` subclass but has a different key set; do not assume `.get('diagrams')` works on it (it has none — diagrams live in nested `amplitudes`).
