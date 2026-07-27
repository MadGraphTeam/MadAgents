---
description: Loop-UFO renormalization CTs attach to PARTICLE objects (particle.counterterm + loop_particles), not only to CTVertex; importer synthesizes UVWfct_* couplings and set_Born_CT consumes them per external leg into LoopUVCTDiagrams.
---

# Particle-attached wave-function / mass-renormalization counterterms

(v3.7.1, `$MADGRAPH_INSTALL`.) A loop UFO carries TWO kinds of renormalization counterterm,
on two different object types. My other pages (ct-files-and-vertex-types, ct-vertex-consumers,
ct-diagram-gen-pass-mechanics) cover the **CTVertex**-based CTs (R2/UVtree/UVmass/UVloop in
`CT_vertices.py`). This page covers the OTHER kind: CTs attached to **Particle** objects — the
external-leg wave-function / mass renormalization. This is the "loop model's particle content
differs from a tree model's" angle: loop-UFO particles carry extra `counterterm` and
`loop_particles` attributes a tree-model particle does not.

## Declaration: on the Particle, in particles.py
`$MADGRAPH_INSTALL/models/loop_sm/particles.py` (after the Particle constructors; marker
comment `# Wavefunction renormalization` at :317, declarations :319-329):
```python
b.loop_particles = [[[5,21]]]
b.counterterm    = {(1,0,0):CTParam.bWcft_UV.value}
c.loop_particles = [[[4,21]]]
c.counterterm    = {(1,0,0):CTParam.cWcft_UV.value}
t.loop_particles = [[[6,21]]]
t.counterterm    = {(1,0,0):CTParam.tWcft_UV.value}
G.loop_particles = [[[4]],[[5]],[[6]]]
G.counterterm    = {(1,0,0):CTParam.GWcft_UV_c.value,(1,0,1):CTParam.GWcft_UV_b.value,(1,0,2):CTParam.GWcft_UV_t.value}
```
- `particle.counterterm` is a dict keyed `(order1,...,orderN, loop_particle#)` → a CTParameter
  value (a Laurent dict). The key's leading entries are the power of each coupling order
  brought by the CT; the final entry indexes `particle.loop_particles`.
- In loop_sm only b/c/t (massive quarks) and `G` (the goldstone) carry these — they are the
  fields with non-trivial on-shell mass/wave-function renormalization. The object_library
  Particle class declares `loop_particles`, `counterterm`, `goldstoneboson` among
  `require_args_all` (object_library.py:74), defaulting to None — a tree particle leaves them
  unset.

## Import-time processing → synthesized UVWfct_* couplings (`import_ufo.py:1342-1377`)
In `add_particle`:
- **Tree-model / no-CT short-circuit (1342-1344):** `if not self.perturbation_couplings or
  counterterms=={}: self.particles.append(particle); return`. So a non-loop model NEVER
  processes particle counterterms — the same `perturbation_couplings` spine gates this path.
- **One-loop check (1353-1354):** keeps the CT only if exactly one order key is at power 1 and
  none is >1 (`len([1 for k in key[:-1] if k==1])==1 and not any(k>1 ...)`) — i.e. a genuine
  one-loop wave-function CT.
- **Synthesis (1366-1377):** for each surviving key the importer builds a NEW Coupling named
  `UVWfct_<particle.name>_<loop_particle#>`, `value = counterterm` (the Laurent dict),
  `order = {order_name: 2}`, and appends it to `self.wavefunction_CT_couplings`
  (init at import_ufo.py:493; appended at :1377). The particle's `counterterm` attr is rewritten
  into the form `('ORDER', ((pdg-tuple,))) : {laurent_order: UVWfct_name[+'_<n>eps']}`.
- The collected `wavefunction_CT_couplings` are merged into the model at import_ufo.py:416 via
  `additional_couplings = ufo2mg5_converter.wavefunction_CT_couplings`, so these synthesized
  couplings join the regular coupling set.

## Consumption: inside set_Born_CT, per external leg (`loop_diagram_generation.py:1301-1310`)
`set_Born_CT` (method at :1207) does TWO jobs — correct an incompleteness in my other pages
which describe it as ONLY the CTVertex/UVtree double-generate:
1. (documented elsewhere) the UVtree CTVertex factorizing CTs via the `UVCT_SPECIAL`
   synthetic-order second diagram-generation pass.
2. (THIS page) the particle-attached wave-function CTs: it loops over `process['legs']`, reads
   `model.get_particle(abs(leg['id'])).get('counterterm')`, and for each key whose order
   `key[0] in process['perturbation_couplings']` (spine list again) builds a `LoopUVCTDiagram`
   with `('EpsilonOrder', -laurentOrder)` in its order key — one per leg per Laurent order.
   The CTCoupling list is filtered: a loop_particles set intersecting
   `process['forbidden_particles']` is dropped (1308-1313).

## Why it matters / cautions
- A loop model's wave-function/mass renormalization is split across BOTH object types: CTVertex
  `UVmass` (mass renorm appearing as a 2-point CT vertex) AND particle `counterterm`
  (the leg wave-function factor). Don't assume all renormalization lives in `CT_vertices.py`.
- **Goldstone dependence:** loop_sm's particle CTs reference `P.G` (goldstone) for the G
  wave-function CT, and the b/c/t loop_particles include pdg 21 (gluon). The goldstone exists
  only in **Feynman gauge** — `import_ufo.py:1248-1255` DROPS goldstone particles entirely in
  unitary gauge (gate `(aloha.unitary_gauge in [1,2] and 0 in model['gauge']) or (1 not in
  model['gauge'])` → `return` before append) and tags them `type='goldstone'` in Feynman gauge
  (1260-1264). For a QED/EW-perturbed model (forced to Feynman gauge) the goldstone CT is live;
  a QCD-only loop process keeps Feynman gauge too (gauge `[0,1]`), so `G` is present.
- The per-leg `LoopUVCTDiagram` count for a given process is runtime/diagram-content
  (depends on which external legs carry a counterterm and survive forbidden_particles) —
  PROBE-CANDIDATE, not asserted here. The synthesis + selection MECHANISM above is source-confirmed.
- Boundary: the LoopUVCTDiagram object semantics at amplitude/MadLoop-evaluation time are
  madloop slice; this page is the model-side declaration + diagram-gen selection only.
