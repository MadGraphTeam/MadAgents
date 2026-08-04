---
description: LoopOption (post-remap), not the surface option= keyword, is what every post-parse guard branches on; the keyword is consumed at the remap chokepoint and only HasBorn survives it.
---

# LoopOption is the post-remap discriminant

`extract_process`, `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`. v3.7.1.
This page lifts a single principle out of the per-guard instances on
`bracket-parse-and-loopoption-mapping.md` and `gauge-restriction-and-pert-order-validation.md`.

## The principle
The surface `option=` keyword from the bracket is read exactly ONCE, at the remap
chokepoint (interface:4862-4877). There it is collapsed into two variables —
`LoopOption` and `HasBorn` — and then never read again. After line 4877 the raw
`option` variable is dead (only reuse in the rest of `extract_process` is a comment
at interface:5372, not a use). Therefore **every post-parse guard branches on the
`LoopOption` value (or `HasBorn`), not on the keyword the user typed.**

The remap (interface:4864-4874) is non-identity in two places, so `LoopOption` is
NOT the same as the typed keyword:
- `sqrvirt` -> `LoopOption='virt'`, `HasBorn=False` (4865-4867).
- bare `[…]` (no `option=`) -> `LoopOption='all'` (4874).
- `noborn`/`real`/`virt`/`LOonly`/`only`/`tree` -> `LoopOption=option` (4864, identity).

## Every guard reads LoopOption (verified, interface)
| guard | line | predicate |
|---|---|---|
| gauge FD/axial | 4879 | `LoopOption != 'tree'` |
| constrained-orders `==`/`>` | 4983 | `LoopOption != 'tree'` |
| tagged-particle | 5227 | `LoopOption in ['virt','sqrvirt','tree','noborn']` |
| loop-model requirement | 5280 | `LoopOption not in ['real','LOonly']` |
| split_orders/loop_optimized | 5291 | `LoopOption not in ['tree','real']` |
| stored on ProcessDefinition | 5350 | `'NLO_mode':LoopOption` |

## Consequences the per-guard instances do not individually give
- **sqrvirt-vs-virt survives ONLY through HasBorn.** Because `sqrvirt` is remapped to
  `LoopOption='virt'` at 4866, no `LoopOption`-keyed guard can tell them apart; the
  sole difference downstream is `HasBorn` (False for sqrvirt, True for virt). The
  ProcessDefinition stores both as `NLO_mode='virt'` and distinguishes them only by
  `has_born` — rendered as `[ virt^2= … ]` vs `[ virt= … ]` (base_objects:3353-3354).
- **The `'sqrvirt'` entry in the tagged-guard set (5227) is dead code.** sqrvirt is
  already `LoopOption='virt'` by the time line 5227 runs, so the `'sqrvirt'` literal
  can never match; the tagged-particle case for sqrvirt is caught via the `'virt'`
  entry. Harmless but unreachable.
- **bare `[QCD]` is `'all'`, never `'tree'`.** The bare-bracket default is set in the
  else branch (4874), so a bare bracket trips every `!= 'tree'` guard — gauge,
  constrained-orders — exactly like an explicit NLO mode does.
- **Predicts future guards.** Any new validation added after 4877 will, by
  construction, see only `LoopOption`/`HasBorn`; it cannot recover the user's typed
  keyword. So sqrvirt and bare-bracket aliasing will hold for it too.

## Boundary
This principle covers guards INSIDE `extract_process` after the remap (line 4877
onward). What FKS / MadLoop / the Fortran exporter do with the stored `NLO_mode`
and `has_born` downstream is owned by the fks / madloop / nlo-export slices — this
page does not extend there.
