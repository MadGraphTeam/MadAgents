---
description: What CT files a loop UFO declares (CT_vertices/CT_couplings/CT_parameters), the R2/UV/UVmass vertex types, and the UV->UVtree/UVloop/UVmass split in the importer.
---

# Counterterm files and vertex types

A loop-capable UFO carries three extra files beyond a tree UFO. (loop_sm, v3.7.1.)

## The three CT files (`$MADGRAPH_INSTALL/models/loop_sm/`)
- `CT_vertices.py` — `CTVertex(...)` objects appended to `all_CTvertices`. These hold the
  R2/UV interactions. NOTE: the ordinary `vertices.py` has NO `type=`/R2/UV content;
  CT content lives only in `CT_vertices.py`.
- `CT_couplings.py` — ordinary `Coupling(...)` objects (R2_*, UV_*), each with a
  `value` and `order` dict. (Not a distinct class — uses `Coupling`, `all_couplings`.)
- `CT_parameters.py` — `CTParameter(...)` → `all_CTparameters`. Holds the Laurent-series
  renormalization constants. `value` is a dict keyed by Laurent order:
  `{0: finite}`, `{-1: single-pole}` (e.g. `G_UVg value={-1:'...11.0*CA'}`).

## Vertex `type` distribution in loop_sm CT_vertices.py
Read fresh: `grep -oE "type = '[^']*'" $MADGRAPH_INSTALL/models/loop_sm/CT_vertices.py | sort | uniq -c`
— the raw literals are `R2`, `UV`, `UVmass` only (drift-prone multiplicities; do not cache the
counts). No literal `UVtree`/`UVloop` in the UFO file — those are derived by the importer (below).

## CTVertex / CTParameter UFO classes (`object_library.py`)
- `class CTVertex` (217): `require_args=['name','particles','color','lorentz','couplings','type','loop_particles']`.
  `loop_particles` lists the particle content circulating in the loop the CT corrects.
- `class CTParameter` (169): `require_args_all=['name','value','order','loop_particles','counterterm']`.
- `Coupling.pole(x)` (250-261): if `value` is a dict, returns `value[-x]` for pole order
  x (x=0 finite, 1 single, 2 double); else returns `value` as the finite part.

## UV -> UVtree/UVloop/UVmass split (`import_ufo.py:1568-1579`)
Accepted types: `['UV','UVloop','UVtree','UVmass','R2']` (else MadGraph5Error).
If `type=='UV'` (unspecified), the importer guesses:
- exactly 2 particles with identical names → `UVmass`;
- otherwise → `UVloop`.
So the bare `UV` in the UFO is auto-classified; a model may also specify UVtree/UVloop
explicitly. The `UV` entries in loop_sm become UVloop/UVmass at import.

## CTVertex couplings triple-key (color, lorentz, loop_particle) and loop_particles
A CTVertex's `couplings` dict is keyed by a **3-tuple** `(color_idx, lorentz_idx,
loop_particle_idx)` — **color FIRST**, one MORE index than an ordinary Vertex (which keys
`(color,lorentz)`). The element order is authoritative from the importer, NOT the symmetric
`(0,0,N)` loop_sm examples: `add_CTinteraction` repacks the key as
`new_couplings[key[2]][poleOrder][(key[0],key[1])]` (`import_ufo.py:1635`), handing
`(key[0],key[1])` to `add_interaction`, which reads `interaction_info.lorentz[key[1]]`
(`import_ufo.py` add_interaction, the `if interaction_info.lorentz[key[1]].name not in
lorentz` test) — so **`key[1]` indexes lorentz and `key[0]` indexes color**. The asymmetric
2HDMtypeII keys (e.g. `(2,1,0)`, `(11,0,0)`) confirm key[0] ranges over the 12 color
structures while key[1] ranges over the 4 lorentz structures. `key[2]` is the loop_particle
index. (Matches the ufo consultant's CT-object-grammar page: `(color, lorentz, loop_group#)`.)
The third index selects which entry of the nested `loop_particles` list the coupling belongs
to. `loop_particles` is a nested list: top level indexed by `key[2]`, each element a list of
particle-lists (the alternative loop-content sets that share that coupling structure).
Worked example (loop_sm CT_vertices.py:21-29, `V_R23G`, ggg R2):
```
loop_particles = [ [[P.u],[P.d],[P.c],[P.s],[P.b],[P.t]],   # key[2]==0: quark loop
                   [[P.G]] ]                                  # key[2]==1: gluon loop
couplings = {(0,0,0):C.R2_3Gq, (0,0,1):C.R2_3Gg}
```
So `(0,0,0)` (loop idx 0) carries the six-quark-loop R2 coupling, `(0,0,1)` (loop idx 1) the
gluon-loop R2 coupling. The importer emits ONE interaction PER loop_particles element, so this
single CTVertex unfolds into a quark-loop R2 interaction and a gluon-loop R2 interaction, each
with its own `loop_particles` pdg list (import_ufo.py:1640-1643: `loop_particles=[[part.pdg_code
...] for loop_parts in interaction_info.loop_particles[i]]`). An EMPTY `loop_particles` defaults
to `[[]]` (one interaction, no specified loop content) — import_ufo.py:1640.

## Laurent unfolding (`import_ufo.py:1598-1649`)
`add_CTinteraction` unfolds ONE CTVertex into multiple `add_interaction` calls along THREE
dimensions: (a) per coupling-order key, (b) per loop_particles element (`key[2]`, above),
(c) per Laurent pole order. The per-coupling-order split is via `order_to_interactions` (1592, 1602-1609):
couplings with distinct `coupling.order` dicts (e.g. a QCD vs QED renorm piece) become
SEPARATE interactions so they never mix. Pole couplings get name suffix `_<poleOrder>eps`
(e.g. `_1eps`) and the interaction type gets the `<n>eps` suffix (1644-1649). A non-zero
DOUBLE pole (poleOrder==2) raises InvalidModel (1611-1620) — CT couplings may only carry
finite + single-pole (UV renormalization is at most 1/eps in dim-reg here). NB: the
double-pole rejection is for the *coupling*; a CTParameter itself may have a -2 pole
(see ctparameter-eps-fin-expansion).

## Interaction CT predicates (`$MADGRAPH_INSTALL/madgraph/core/base_objects.py`)
On the Interaction class (NOT loop_base_objects — card drift):
- `is_R2` (784): `type[:2]=='R2'`.
- `is_UV` (794): `type[:2]=='UV'`.
- `is_UVmass`(804)/`is_UVloop`(814)/`is_UVtree`(824): `type[:6]==` the literal.
- `is_UVCT` (834): interaction has `'UVCT_SPECIAL'` order key (tagged during generation).
- `get_epsilon_order` (847): 1 if `'1eps'` in type, 2 if `'2eps'`, else 0.
- `is_perturbating(orders)` (775): True if `perturbation_type` is None or in `orders`.
InteractionList getters `get_UV/get_UVmass/get_UVtree/get_UVloop` at base_objects.py:1039-1053.
