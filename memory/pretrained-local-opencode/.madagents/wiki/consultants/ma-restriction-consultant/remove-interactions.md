---
description: remove_interactions — how zero-coupling vertices/counterterms are pruned, the partial-trim vs full-remove distinction, loop counterterm handling, and lorentz reindexing (import_ufo.py v3.7.1)
---

# remove_interactions — vertex pruning

`remove_interactions(self, zero_couplings)` at `$MADGRAPH_INSTALL/models/import_ufo.py:2876-2970`. Called at pipeline step 7 (2425) with the zero-coupling set from `detect_identical_couplings`. Uses `self.coupling_pos` (built by `locate_coupling`) to find where each zero coupling appears.

## Trim vs remove (the load-bearing distinction)
For each vertex touching a zero coupling, delete just the dict entries whose coupling is zero (2894-2902) — including sign-prefixed `-GC_X` forms (2898-2902). Then (2920-2930):
- vertex `couplings` dict now EMPTY → `self['interactions'].remove(vertex)` and log `"remove interactions: ..."`.
- vertex still has surviving couplings → kept, log `"modify interactions: ..."`.

So a multi-coupling vertex that loses ONLY SOME couplings is TRIMMED, not removed. A vertex is removed only when every one of its couplings was zero. This is why pruning a single coupling order can shrink a vertex's lorentz/coupling content without deleting the interaction.

## Counterterm pruning (loop models)
Particle counterterms are stored as `coupling_pos` entries that are tuples `(particle, ct_key)` (2908-2909). Same trim logic on `particle['counterterm'][ct_key]` (2910-2917); empty → `del` the counterterm and log `"remove counterterm of particle ..."`, else log `"Modify counterterm ..."` (2933-2948). Relevant only to NLO/loop UFO models that carry counterterms; tree models have none.

## Lorentz reindexing (2950-2967)
After trimming, for every MODIFIED (not removed) vertex: recompute the set of lorentz indices still referenced by surviving coupling keys (`key[1]`), rebuild `vertex['lorentz']` to only those, and remap the coupling-dict keys to the new compacted lorentz indices. This keeps `vertex['lorentz']` and the `(color, lorentz)` coupling keys consistent after partial pruning. A vertex with no surviving lorentz refs is skipped (already handled by removal above).

## Orphaned particles survive — restriction prunes interactions, NEVER drops a particle
`remove_interactions` only removes/edits `Interaction` objects from `self['interactions']` (2927) and `particle['counterterm'][...]` entries — it NEVER touches `self['particles']` or `self['particle_dict']`. So a particle that loses ALL its vertices (e.g. a heavy state all of whose couplings went to zero, or a fermion whose only Yukawa was pruned) stays in the operative model's particle list with no interactions. Restriction does not delete particles.

Confirmed by enumeration: the ONLY `self.particles.remove(particle)` call in `import_ufo.py` is at `:783`, inside `merge_all_goldstone_with_vector` (class `UFOMG5Converter`, FD = Feynman Diagram gauge, conversion time — see goldstone-vector-merge.md), with the explicit code comment at `:780` "This routine also removes the goldstone from the list of particles of the model." So the goldstone-vector merge is the SINGLE particle-dropping operation in the whole UFO→operative-model path, and it is NOT param-card restriction — `RestrictModel.restrict_model` drops zero particles.

The `set('particles', self.get('particles'))` resync at `restrict_model:2403` is NOT a prune: `Model.set` for `'particles'` (`base_objects.py:1255-1287`) only `make_unique`s the list (dedup) and regenerates `particle_dict`/`ref_dict_to0` — it does not filter out orphaned particles. Restriction's effect on particle content is therefore entirely indirect: a particle's mass/width can be repointed to `'ZERO'` or a merged name (fix_parameter_values / merge_iden_parameters), and its vertices can vanish, but the particle entry itself persists.

## Removed ≠ small — the full external-zero → parameter → coupling → vertex chain
A restrict-card value of `0.0` for an external parameter does NOT set a tiny numerical value; the whole dependency chain is DELETED from the operative model. Grounded for `yme=0` (default `sm`, PDG 11 YUKAWA), traced through `restrict_model` (`import_ufo.py:2390`):
1. `detect_special_parameters` (`:2615-2624`) collects every name in `parameter_dict` whose value `== 0` (≠ 'ZERO') into `null_parameters` — so external `mdl_yme` AND every internal param that evaluated to 0 (here `mdl_ye = (yme*sqrt2)/vev → 0`) are flagged. (`==1` → `one_parameters`.)
2. `detect_identical_couplings` (`:2525`) flags couplings whose value is 0 — `GC_89 = -i*ye/sqrt2 → 0` (couplings.py:363-366, the `e+ e- H` coupling) lands in `zero_couplings`.
3. `remove_interactions(zero_couplings)` (`:2425`) deletes the `e+ e- H` FFS4 vertex (V_104, couplings={(0,0):GC_89}, vertices.py:631-634) → emits `remove interactions: e- e- h at order: QED=1`. The orphaned coupling is then dropped by `remove_couplings` (`:2433`).
4. `fix_parameter_values(*detect_special_parameters())` (`:2440-2442`) repoints zero MASS/WIDTH params to `'ZERO'` (`:2987-3001`) then, when `simplify=True` (rm_parameter default) and a param is no longer referenced by any surviving expression, REMOVES the parameter object from `self['parameters']` and emits `remove parameters: %s` (`:3091-3099`). Probe-confirmed emissions for `import model sm; generate h > e+ e-`: `remove parameters: mdl_yme`, `mdl_ye`, `mdl_Me`, `mdl_MM` (at DEBUG log level).

`keep_external=True` (or the param appearing in the running.py block) PROTECTS an external param — it logs `fix parameter value:` instead and keeps the param object (`:3093-3096`). Default restriction has `keep_external=False`, so the param is gone.

### User-facing consequences of "removed, not small"
- **`set <name>` is rejected at the MG5 prompt** — e.g. `set ye <val>` → `InvalidCmd : Possible options for set are [...]`; `ye` is absent because the parameter object was removed. A `param_card.dat` edit is equally moot: no `Block YUKAWA 11` line is written (param-card slice's symptom) and no GC_89 factor exists in any generated Fortran.
- **Zero diagrams / NoDiagramException**: a process whose ONLY amplitude needs the removed vertex generates nothing — `generate h > e+ e-` → `NoDiagramException : No amplitudes generated` (probe-confirmed). In a multi-subprocess generate (`h > l+ l-`, l=e/μ/τ) the e/μ subprocesses silently contribute zero diagrams; only τ survives.
- **Fix is model-load-time, not card-time**: re-load a restrict variant that keeps the value non-zero (`import model sm-lepton_masses` for yme — see sm-restrict-files.md), or author a custom restrict. You cannot resurrect a removed parameter by editing the card.

NOTE — engine vs card-generator: the runtime pruning engine is `RestrictModel.restrict_model` here, NOT `models/sm/build_restrict.py`. `build_restrict.py` exists but its docstring (`:15-16`) says it "defines how the restrict card can be build automatically" — it is the AUTHOR-side generator that PRODUCES `restrict_*.dat`; the loaded model is pruned by `import_ufo.py`.

## Caution
- Logging uses `logger_mod` at `self.log_level` — prune actions are visible only at the model-modification log level, so a surprised user ("my vertex vanished") may not see why without raising verbosity.
- Trim mutates the SAME interaction object in place; the lorentz reindex changes `key[1]` values, so any external cache of `(color,lorentz)` keys taken before restriction is stale afterward. This is the operative-model state; the declared UFO vertices.py is untouched.
- An orphaned particle (no surviving vertices) is still a valid external/internal leg in `_curr_model`; it simply cannot appear in any diagram because no interaction references it. Diagram generation, not restriction, is where its absence-of-couplings finally bites.
