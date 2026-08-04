---
description: Goldstone-with-vector merging — triggers on aloha.unitary_gauge==3 (FD = Feynman Diagram gauge), lives in UFOMG5Converter not RestrictModel (import_ufo.py v3.7.1)
---

# Goldstone-vector merging

NOTE on ownership: `merge_all_goldstone_with_vector` / `merge_goldstone_with_vector` live in `class UFOMG5Converter` (`$MADGRAPH_INSTALL/models/import_ufo.py:461-2039`), NOT in `RestrictModel`. They fire during UFO→MG5 CONVERSION, before/independent of param-card restriction. The `do_set gauge` orchestration that sets the trigger is model-loader's slice; this page records only the merge mechanism and the value it reads.

## Trigger (608-609)
```
if aloha.unitary_gauge == 3:
    self.merge_all_goldstone_with_vector()
```
`aloha.unitary_gauge` defaults to `True` (boolean) but is overloaded as an int (`$MADGRAPH_INSTALL/aloha/__init__.py:2`). Value mapping from `do_set` (`madgraph_interface.py:8079-8118`):
- `unitary` → `True` (needs gauge 0 in model)
- `axial` → `2`
- `FD` → `3` (needs gauge 1 in model; warns "NOT ALL MODEL ARE SUPPORTING THIS GAUGE", cites 2203.10440 and 2405.01256)
- `Feynman` / else → `False`

So the merge fires ONLY in FD = Feynman Diagram gauge (value 3), NOT in ordinary unitary or Feynman gauge. (Corrects a common mis-framing of "unitary gauge absorbs Goldstones": the actual code trigger is FD gauge.)

NAME (verified v3.7.1): gauge 3 is the **Feynman Diagram gauge** in source — aloha/__init__.py:6 comment "3: Feynman Diagram gauge (5D aloha)", import_ufo.py:358 pickle name `model_FDG.pkl` (FDG = Feynman Diagram Gauge), and the merge_*_goldstone_with_vector docstrings (777/797) say "For Feynman Diagram gauge". "FD" expands to Feynman Diagram, NOT "Four-Dimensional".

## Mechanism
`merge_all_goldstone_with_vector` (776): for each particle with `type=='goldstone'`, remove it from the particle list, find the unique vector (`spin==3`) with the SAME mass (785: `len(vector)!=1 → raise Exception("Failed to idendity goldstone/boson relation")`), then `merge_goldstone_with_vector(goldstone, vector)`. For a non-self-conjugate particle it also merges the anti-particle copy (789-794).

THE UNIQUE PARTICLE-DROPPING SITE: `self.particles.remove(particle)` at `:783` (code comment `:780` "This routine also removes the goldstone from the list of particles of the model") is the ONLY place in `import_ufo.py` that deletes a particle from the model's particle list. By contrast `RestrictModel` (param-card restriction) drops ZERO particles — it only prunes interactions/couplings and repoints masses/widths (see remove-interactions.md). So if the operative model is missing a *particle* (not just a vertex), the cause is FD-gauge goldstone absorption at conversion time, never the restrict card.

`merge_goldstone_with_vector` (796): collects goldstone-containing vertices and vector-containing-but-not-goldstone vertices; builds a name-keyed `search_int` map; for each goldstone vertex either updates an existing equivalent vector vertex (`update_vertex_for_goldstone`) or converts the goldstone vertex into a vector vertex (`convert_goldstone_to_V`, 845). Goldstone is replaced by the vector particle in the vertex particle list.

## Caution
The goldstone↔vector pairing is by equal MASS + spin-3 uniqueness. A model where two vectors share a goldstone's mass would hit the `len(vector)!=1` exception. The merge mutates the interaction list at conversion time, so the OPERATIVE model in FD gauge has no goldstone particles and folded vertices.
