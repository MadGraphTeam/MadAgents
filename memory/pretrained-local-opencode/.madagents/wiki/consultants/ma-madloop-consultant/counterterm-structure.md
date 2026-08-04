---
description: R2/UV/UVmass/UVloop/UVtree + wavefunction-renorm counterterm assembly — set_Born_CT, set_LoopCT_vertices, CT-type predicates (loop_diagram_generation.py / base_objects.py, MG5_aMC v3.7.1)
---

# Counterterm structure

## CT-type predicates (`$MADGRAPH_INSTALL/madgraph/core/base_objects.py`)
Interaction `type` string prefix decides the CT class:
- `:784` `is_R2()`  → `type[:2]=='R2'`  (rational R2 term)
- `:794` `is_UV()`  → `type[:2]=='UV'`  (any UV)
- `:804` `is_UVmass()` → `type[:6]=='UVmass'`
- `:814` `is_UVloop()` → `type[:6]=='UVloop'`
- `:824` `is_UVtree()` → `type[:6]=='UVtree'`
- `:834` `is_UVCT()` → has `'UVCT_SPECIAL'` order key (set only transiently during set_Born_CT).
Model `interactions.get_UV()` at :1039 returns all UV interactions.

## set_Born_CT (loop_diagram_generation.py :1207-1331) — runs only if has_born
Handles the UV counterterms that FACTORIZE the born (UVtree) plus WAVEFUNCTION renormalization. UVmass/UVloop/R2 are NOT here — they go in set_LoopCT_vertices.

UVtree block (:1218-1281):
- `:1224-1233` collect UV interactions that `is_UVtree()`, have >1 particle, perturbate the requested orders, share an order with the perturbation, and whose `loop_particles` are not all forbidden.
- `:1235-1251` temporarily inject a fake order `UVCT_SPECIAL=1` into those interactions, refresh model dicts (`actualize_dictionaries(useUVCT=True)`), and re-run the tree generator to produce UVCT diagrams. Each diagram with `UVCT_SPECIAL==1` becomes a `LoopUVCTDiagram`.
- `:1262-1265` the UVCT coupling is counted once per allowed `loop_particles` list (forbidden-particle filtered).
- `:1270-1277` the fake order is removed and dicts restored afterward.

Wavefunction renormalization block (:1290-1329):
- For each born diagram and each external leg, read `model.get_particle(abs(id)).get('counterterm')`.
- `:1304-1325` for each counterterm whose order is in `perturbation_couplings`, and each Laurent ε order, build a `LoopUVCTDiagram` keyed by `((order,2),('EpsilonOrder',-laurentOrder))`. `type` = `'UV'` for laurentOrder 0 else `'UV<n>eps'` (e.g. `UV1eps`). `UVCT_orders={order:2}`.
- Different ε orders ⇒ different LoopUVCTDiagrams (one per Laurent order).

## set_LoopCT_vertices (:1333-1518) — R2 / UVmass / UVloop attached per loop diagram
- `:1344-1391` build `CT_interactions` dict keyed `(tuple(ext-PDGs), tuple(loop-particle-PDGs))` from interactions that `is_UVmass() or is_UVloop() or is_R2()`. For `is_UVloop()` the loop-particle key is forced EMPTY (only used to filter against forbidden particles), `:1355-1364`.
- `:1413-1518` for each loop diagram build a searching key (ext PDGs + loop-content PDGs) and a tracking key (struct IDs), look up matching CT interaction IDs, and add a `CTVertex` to `diag['CT_vertices']` IF not already added (CT_added dict prevents double counting across crossings) AND `diag.get_loop_orders(model) == interaction['orders']` (:1484-1486).
- `:1517` CT vertices sorted by `interaction.canonical_repr()` (stable for cross-process merging).

## Containers
- `LoopDiagram['CT_vertices']` holds R2/UVmass/UVloop vertices; `get_CT(model,'R2'|'UV')` (loop_base_objects.py :428) filters by `type` substring.
- `LoopUVCTDiagram` (loop_base_objects.py :1323): UVtree + wavefunction renorm. Carries `UVCT_couplings`, `UVCT_orders`, `type`; `calculate_orders` (:1379) sums vertex orders + UVCT_orders into coupling_orders + WEIGHTED.

## Final CT count (generate_diagrams :901-908)
`nCT['UV']`/`nCT['R2']` aggregated from both `loop_UVCT_diagrams` (split by `type[:2]`) and per-loop `get_CT(model,'UV'|'R2')`.
