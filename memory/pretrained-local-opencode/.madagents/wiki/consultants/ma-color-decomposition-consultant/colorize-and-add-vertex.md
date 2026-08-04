---
description: How colorize() walks a diagram's vertices into raw color strings, and how add_vertex builds per-vertex strings — flow-flipping for internal legs, the dead id=0 path vs the live id=-1 special-identity stitching, leg reordering, index summation.
---

# colorize() and add_vertex()

`$MADGRAPH_INSTALL/madgraph/core/color_amp.py`.

## Build lifecycle (entry point → basis)
`ColorBasis` is the entry point. Construction flow:
- `ColorBasis(amplitude)` — `__init__` (`color_amp.py:333-354`): asserts ≤1 arg,
  inits an empty dict + fresh per-instance `_canonical_dict`/`_list_color_dict`,
  then if an `Amplitude` is given calls `self.build(amplitude)` (`:354`).
- `build(amplitude)` (`:323-331`): if an amplitude is passed, calls
  `create_color_dict_list(amplitude)`; then loops `enumerate(self._list_color_dict)`
  calling `update_color_basis(color_dict, index)` per diagram. With NO amplitude
  it reuses the already-stored `_list_color_dict` (re-build from cached colorize).
- `create_color_dict_list(amplitude)` (`:308-321`): for each
  `amplitude.get('diagrams')` calls `colorize(diagram, model)`, collects the
  list, stores it on `self._list_color_dict`, returns it. So `colorize` runs
  once per diagram; the **diagram index used in the basis 6-tuple is this
  enumerate position** (build loop `:330`), not a diagram-internal id.

So: `__init__` → `build` → `create_color_dict_list` (per-diagram `colorize`/
`add_vertex` → raw strings) → `update_color_basis` (per diagram: simplify +
append to basis). The simplification/caching half is on the
canonical-dict-and-simplification page; this page covers the raw-string half.

## colorize(diagram, model) — `color_amp.py:62-85`
Walks `diagram.get('vertices')` in order, calling `add_vertex` on each,
threading `repl_dict` (index replacement bookkeeping), `res_dict` (the growing
product of color strings keyed by the per-vertex color-part index chain), and
`min_index` (counter for new summed indices, starts at **-1000**, `:68`).
Returns `res_dict`: keys = color-coefficient index tuples, values = unsimplified
`ColorString`s.

CAUTION — colorless-process fallback (`color_amp.py:79-83`): if every value is
an empty `ColorString()`, the whole dict is rebuilt with each value replaced by
`ColorString([ColorOne()])`. So a fully colorless process still yields a
1-element basis with a `ColorOne` structure, not an empty basis.

## add_vertex(...) — `color_amp.py:89-237`
Builds `(color, leg-number)` pairs for the vertex (color negative for anti).

Flow / index logic (the tricky part):
- **Last leg of a non-final vertex** (`:118-119`): color is flipped to
  `get_anti_color()` (the propagator continues as the conjugate rep), and the
  leg number is replaced by a new negative summed index `min_index`
  (`:125-126`), UNLESS the special id=-1 case below applies.
- **id=-1 (identity) penultimate special case** (`:123-130`): if the final
  vertex is id=-1 and the current vertex is the next-to-last, instead of a fresh
  summed index, the replacement reuses the **max leg number of the id=-1
  vertex's legs**. This stitches the identity vertex's legs together.
- **id0_rep — DEAD CODE at runtime (`:90,111-113,122`).** The parameter
  `id0_rep` defaults to `[]` (`:90`) and is **never populated anywhere in the
  codebase** (repo-wide grep for `id0_rep`: only the default + the three reads
  in `add_vertex`; `loop_color_amp.py` does NOT override `colorize`/`add_vertex`,
  so the loop variant inherits the same dead path). The ONLY caller is
  `colorize` at `:75`, which passes 6 positional args and never the 7th. So at
  runtime `id0_rep` is **always empty**, which means:
  - The next-to-last-before-id=0 pre-replacement (`:111-113`, guarded by
    `curr_num in id0_rep`) **never fires**.
  - The `if not id0_rep:` guard at `:122` is **always True**, so the flow-flip
    summed-index replacement (`:125-126`) always runs — modulated only by the
    id=-1 special case below, never by id=0.
  So although id=0 IS a real vertex id in MadGraph diagrams (the *identity
  vertex* — `diagram_generation.py:1063` "Don't check for identity vertex
  (id = 0)"), the color machinery's dedicated id=0 stitching path is vestigial.
  Do NOT describe `:111-113` as live behavior. Sole live special-identity path
  is id=-1 (below).
- **Leg reordering** (`:141-147`): for non-final vertices the last (resulting
  wavefunction) leg is moved to the front. Then legs are sorted to match the
  interaction's particle PDG order (`:150-168`); a leftover pair raises
  `PhysicsObjectError` (`:165-166`).

## id=-1 vertex → no color object (`color_amp.py:176-177`)
Returns `(min_index, res_dict)` unchanged: the identity vertex contributes no
color object, only the index stitching done above.

## Colorless vertex (`color_amp.py:185-195`)
If `interaction['color']` is empty, each existing chain key gets a `0` appended
(`:189-191`) and values are passed through unchanged; if res_dict empty, seed
`{(0,): ColorString()}`. This keeps the chain-index tuple aligned across all
vertices even when some vertices carry no color.

## Multi-color-structure vertices (`color_amp.py:197-237`)
A vertex's `interaction['color']` can be a LIST of `ColorString`s. Only those
whose index `i` appears in `inter_indices` (couplings keys, `:182-183`) are
kept (`:202-203`). For each kept color string: copy, remap its negative
(summed) indices to fresh `min_index` values (`:209-218`), remap positive
indices via `match_dict` (the leg-number map, `:221`), then either seed
new_res_dict (first vertex, `:226-227`) or multiply onto every existing chain
(`:230-235`), extending the chain key with `i`. This is the source of multiple
color-coefficient chains per diagram.
