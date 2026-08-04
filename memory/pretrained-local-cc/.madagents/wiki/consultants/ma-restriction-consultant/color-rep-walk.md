---
description: find_color_anti_color_rep — assigns 3/3bar color states by reading T(...)/Identity(...) tensors of 3-particle vertices, runs at conversion time (import_ufo.py v3.7.1)
---

# find_color_anti_color_rep — color flow assignment

`find_color_anti_color_rep(self, output=None)` at `$MADGRAPH_INSTALL/models/import_ufo.py:1651` (in `UFOMG5Converter`). Called at conversion (582) and again from add_interaction paths (1993, 2002). Returns/extends `output` = `{pdg_code: 3 or -3}`.

## Algorithm
Looks only at 3-particle vertices (1661-1662). Takes `colors = [abs(p.color) for p in particles]`. By which two of the three are triplets (`==[3,3]`, `[1:]==[3,3]`, or `count(3)==2`), reads the color tensor string to decide which triplet is color (3) vs anti-color (3bar):
- `T(3,2,1)` → particle1=color, particle2=anticolor. The unpacking at 1666 is literally `color, anticolor, other = particles`. NOTE: the source COMMENT at 1654-1656 ("set F1 to anticolor and F2 to color") is stale/backwards relative to the code — trust the unpacking, not the comment.
- The other tensors are split across three `colors`-pattern branches: `colors[:2]==[3,3]` handles `T(3,2,1)`/`T(3,1,2)` (1665-1668); `colors[1:]==[3,3]` handles `T(1,2,3)`/`T(1,3,2)` (1687-1690); `colors.count(3)==2` handles `T(2,3,1)`/`T(2,1,3)` (1710-1713). Each unpacks the 3-tuple so the 3-index particle binds `color` and the 3bar-index particle binds `anticolor`.
- `Identity(i,j)` cases: resolved by whichever of the two already has a known rep in `output`; if neither known yet, `continue` (deferred — that is why the function is re-invoked later to converge).
- After binding, assign `output[color.pdg]=3` / `output[anticolor.pdg]=-3` (1740,1748). A conflicting prior assignment raises `InvalidModel("...sometimes in the 3 and sometimes in the 3bar...")` (1737,1745).

## Purpose
Sets up the color flow (which leg carries 3 vs 3bar) for the restricted/converted model so diagram color factors and flow are correct. Output feeds `add_interaction(interaction_info, color_info)` (605-606).

## Caution
Identity-based assignment is order-dependent and may defer (`continue`) until a neighbouring particle's rep is fixed — hence the multiple call sites that re-pass `color_info` to converge. A model whose colored particles only ever appear in Identity vertices (never a T(...) anchor) would leave reps unassigned. This is conversion-time behaviour, upstream of param-card restriction.
