---
description: How loop diagram generation consumes the CT predicates - set_Born_CT (UVtree) vs set_LoopCT_vertices (R2/UVmass/UVloop) in loop_diagram_generation.py.
---

# CT-vertex consumers in loop diagram generation

`$MADGRAPH_INSTALL/madgraph/loop/loop_diagram_generation.py` (v3.7.1). Two methods split
the CT vertices by how they attach to the amplitude.

## set_Born_CT (1207) — UVtree counterterms
Adds, per Born diagram, the UV counterterms that *factorize with the Born* (coupling/field
renormalization), one `LoopUVCTDiagram` per Born diagram and per coupling-order set
(so QCD and QED wavefunction corrections stay in separate diagrams).
Selection loop (1224-1233) iterates `model['interactions'].get_UV()` and keeps `inter` iff:
- `inter.is_UVtree()` AND `len(particles)>1`, AND
- `inter.is_perturbating(process['perturbation_couplings'])`, AND
- `inter['orders'].keys() ∩ process['perturbation_couplings'] != {}`, AND
- some loop_particles element avoids `forbidden_particles` (or `loop_particles==[[]]`).
Selected interactions are temporarily tagged with the synthetic order
`'UVCT_SPECIAL'` (order_hierarchy set at 1236) — that is what `is_UVCT()` later detects.
NB: set_Born_CT ALSO does a SECOND job not about CTVertices — it consumes the
**particle-attached** wave-function CTs (`particle.counterterm`, per external leg, 1301-1310)
into LoopUVCTDiagrams. See particle-attached-wavefunction-CT.

## set_LoopCT_vertices (1333) — R2 / UVmass / UVloop
Recognizes the R2/UVmass CTs associated to each *loop* diagram (the non-factorizing ones,
incl. UV mass renormalization). Builds a dict keyed by
(external-PDG tuple, loop-particle PDG tuple) → interaction IDs.
Selection (1346): `inter.is_UVmass() or inter.is_UVloop() or inter.is_R2() and len>1 and is_perturbating(...)`.
- UVloop branch (1355-1362): leaves the loop-particle key empty but skips the CT if any of
  its loop_particles is in `forbidden_particles`.

## CAUTION — operator precedence at 1346
The condition is `is_UVmass() OR is_UVloop() OR is_R2() AND <guard>`. Python `and` binds
tighter than `or`, so the `len(particles)>1 and is_perturbating(...)` guard applies ONLY to
the `is_R2()` term. UVmass / UVloop interactions enter regardless of that guard. This is a
source-visible asymmetry; treat as the intended behavior unless a probe shows otherwise.

## Division of labor
- UVtree (coupling/field renorm, factorizes w/ Born) → set_Born_CT → LoopUVCTDiagram.
- R2 (rational) + UVmass (mass renorm) + UVloop → set_LoopCT_vertices, attached to loops.
- The set_Born_CT pass these predicates feed runs the ordinary Born generator over a
  temporarily-widened model dict (UVCT_SPECIAL synthetic order) and reverts it; that
  mutate→reuse→revert design is generalized in
  ct-generation-reuses-tree-machinery-via-revertible-mutation.
