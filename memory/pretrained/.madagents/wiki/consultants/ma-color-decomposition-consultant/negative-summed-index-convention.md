---
description: Cross-cutting convention in color decomposition — negative integers are summed (internal/contracted) color indices, positive are external leg numbers; string-combining routines each allocate from a disjoint negative band to avoid accidental contraction, and a paired (count==2) negative index IS a contraction.
---

# Negative integers = summed color indices (cross-cutting convention)

The whole color-decomposition machinery uses one index-namespace convention:

- **Positive index** = external leg number (or a real PDG-derived label).
- **Negative index** = a *summed* (internal / contracted) color index.
- **An index appearing exactly twice = a contraction** over that index. A
  negative index that appears twice is a summed pair to be contracted; the
  `__debug__` assert in `ColorMatrix.create_new_entry`
  (`$MADGRAPH_INSTALL/madgraph/core/color_amp.py:648-656`) enforces that after a
  product no index appears more than twice — i.e. the pairing invariant.

## Why it recurs: routines that COMBINE strings must rename to disjoint bands
When two color strings are multiplied/concatenated, their internal summed
indices must NOT collide, or two unrelated contractions fuse into one wrong
contraction. Each combining routine therefore draws fresh summed indices from
its own disjoint negative band, counting *downward* (more negative):

- `colorize`/`add_vertex` — new summed indices count down from **-1000**
  (`color_amp.py:68`); when multiplying a vertex color string onto existing
  chains, its internal negatives are remapped to fresh `min_index` values
  (`color_amp.py:209-218`).
- `ColorString.order_summation` — renames summation indices starting at
  **-10000**, counting down (`color_algebra.py:996,1007`), and only touches
  indices `<= -10000` (`color_algebra.py:1002`) — so the -10000 band is its own
  namespace, disjoint from the -1000 band above.
- `ColorMatrix.fix_summed_indices` (`color_amp.py:713-748`) — before forming
  `struct1 + struct2`, detects struct2's summed indices as those that are
  negative AND appear exactly twice (`list2.count(i) == 2`, `:732-733`) and
  renames them below `min(struct1)` so the squared/interference product does not
  accidentally contract struct1's indices against struct2's. Docstring states
  the assumption explicitly: "internal summed indices are negative."

## Boundary: the per-PAIR simplify rules do NOT allocate new negatives
The collision-avoidance lives at the *combination / canonicalization* layer
above. The per-pair contraction rules in `color_algebra.py` operate on whatever
index names they are handed and preserve the pairing — they do not mint new
negative indices:

- `T.pair_simplify` (`color_algebra.py:247-287`): the `T...T` join and the Fierz
  identity reuse the existing shared index `x`; no fresh negative is allocated.
- `complex_conjugate` (e.g. `T(a,b,c,i,j)* = T(c,b,a,j,i)`,
  `color_algebra.py:289-298`) only reorders indices.

So when reasoning about an index collision, look at the routine that *combined*
the strings (colorize, order_summation, fix_summed_indices), not at the
per-object algebra rules.

## Cases this catches beyond the instance pages
- Predicts the disjoint-band *design* (why -1000 vs -10000 vs `min(struct1)-1`)
  rather than treating each offset as an isolated magic number.
- Explains *why* `fix_summed_indices` keys on "negative AND doubled" and why
  ColorMatrix asserts "no index > twice."
- Tells you where an accidental-contraction bug would live (combination layer),
  and that any *future* string-combining routine must follow the same band
  discipline.

Instance detail lives on: colorize-and-add-vertex (the -1000 band, per-vertex
remap), canonical-dict-and-simplification (order_summation -10000), colormatrix
(fix_summed_indices, the assert).
