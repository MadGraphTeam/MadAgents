---
description: UFOMG5Converter interior (models/import_ufo.py) — how UFO particle/vertex objects become base_objects.Particle/Interaction; attribute mapping, nb_property==10 check, incoming/outcoming UFO-pair dedup, self_antipart + antiparticle deep-copy, color 3/3bar rep detection, fermion-flow sign, particle_dict/interaction_dict lazy build, parameters/couplings via OrganizeModelExpression.
---

# UFO objects → internal `base_objects.Particle`/`Interaction` (v3.7.1)

Conversion lives in `class UFOMG5Converter` at `$MADGRAPH_INSTALL/models/import_ufo.py:461`
(NOT `madgraph/iolibs/import_ufo.py` — the module is `models/import_ufo.py`). Driven from
`import_full_model` (`:408-420`): `ufomodels.load_model(path)` → `UFOMG5Converter(ufo_model)`
→ `.load_model()` returns the `Model`; then `OrganizeModelExpression(ufo_model).main()` fills
parameters/couplings (`:415`). The pickle cache then saves the assembled `Model` [pickle = ufo slice].

## Converter `__init__` (`:464`) — Model-class choice + perturbation detection
- Empty `ParticleList`/`InteractionList` (`:487-488`).
- **LoopModel-vs-Model decision** (`:498-510`): collects `self.perturbation_couplings = {order.name: order.perturbative_expansion}` for every `order in model.all_orders` with `order.perturbative_expansion>0` (consumer's-own test `>0` at `:501`, NOT a literal `==1`). Non-empty → `loop_base_objects.LoopModel(...)`; empty → plain `base_objects.Model()`. [perturbation predicate detailed on gauge-selection-and-loopmodel-autoswitch.md.]
- `self.model.set('particles', self.particles)` / `set('interactions', self.interactions)` (`:511-512`) — the Model holds the SAME list objects the converter appends to (live aliasing).

## `load_model` (`:530`) — order of conversion
1. Validate parameters: external `lhablock` single-word, no duplicate param names (`:536-545`); CTparameter name-collision check (`:549-556`).
2. `self.model.set('gauge', self.ufomodel.gauge)` if UFO defines `gauge` (`:558-559`) — this is where the model's gauge bits (`[0,1]` etc.) are copied in.
3. **`case_sensitive` decision** (`:563-567`): if lowercasing all names+antinames causes NO collision → `model['case_sensitive']=False` (names later lowercased in `add_particle`).
4. `self.detect_incoming_fermion()` (`:571`) — see below.
5. `for particle_info in all_particles: self.add_particle(...)` (`:573-574`).
6. `color_info = self.find_color_anti_color_rep()` (`:582`) — 3 vs 3bar assignment.
7. `self.model.set('lorentz', list(all_lorentz))` (`:585`).
8. `for interaction_info in all_vertices: self.add_interaction(...)` (`:604-606`).
9. If `aloha.unitary_gauge == 3` (FD gauge): `merge_all_goldstone_with_vector()` (`:608-609`) — drops goldstones from the particle list and folds their vertices into the vector. [FD detail on gauge-dependent-model-loading.md.]
10. If perturbation: `ufomodel.add_NLO()` then `add_CTinteraction` for `all_CTvertices` (`:620-627`).
11. `optimise_interaction` over every interaction; drop any whose `couplings` emptied (`:630-633`).
12. order_hierarchy / expansion_order from `all_orders` (loop models REQUIRE these or `MadGraph5Error`, `:641-677`).
13. `check_model_all()` → `check_model_aS` (`:682`, `:884-905`): enforces that `aS` is SMINPUTS#3 and SMINPUTS#3 is named aS/alphas, else `UFOImportError`.

## `add_particle` (`:1229`) — UFO Particle → `base_objects.Particle`
- **UFO-pair dedup** (`:1237-1239`): UFO has two entries (particle + antiparticle); MG5 keeps ONE. `if pdg in self.incoming or (pdg not in self.outcoming and pdg<0): return` — the antiparticle half is skipped using the incoming/outcoming sets from `detect_incoming_fermion` (negative pdgs not flagged incoming are dropped).
- **Tree-model ghost drop** (`:1242-1243`): `if not self.perturbation_couplings and particle_info.spin < 0: return` (UFO encodes ghosts as negative spin; tree models do physical polarization sums, no ghosts).
- **Goldstone drop** (`:1245-1254`): in unitary/axial gauge with bit-0 allowed, or when bit-1 (Feynman) absent, goldstones return early (not added). [gauge predicate on gauge-dependent-model-loading.md.]
- **Attribute-mapping loop** (`:1268-1318`): iterates `particle_info.__dict__`. A key counts toward `nb_property` only if `key in Particle.sorted_keys and key != 'counterterm'`. Special handling:
  - `name`/`antiname`: lowercased iff `not case_sensitive` (`:1272-1276`).
  - `charge`: `float(value)` (`:1277-1278`).
  - `mass`/`width`: `str(value)` — stored as the PARAMETER NAME string (e.g. `'MT'`), not a number (`:1279-1280`).
  - `spin`: `abs(value)`; if UFO spin `<0` → `type='ghost'` (`:1281-1286`).
  - `propagating` False → `line=None` (non-propagating) (`:1287-1289`).
  - `propagator` (if UFO provides it as list/dict): index `[0]` if `aloha.unitary_gauge` truthy, else `[1]` (Feynman) (`:1295-1305`).
  - Any key NOT in sorted_keys and not in the ignore-set (ghostnumber, selfconjugate, goldstone*, partial_widths, texname, antitexname, propagating, ghost) → `self.conservecharge.add(key)` + `particle.set(key, value, force=True)` (`:1312-1318`). This is how `LeptonNumber`, custom `Y`, etc. become candidate conserved charges.
- **`nb_property == 10` assert** (`:1328`): basic completeness check. A key counts toward `nb_property` ONLY if `key in Particle.sorted_keys and key != 'counterterm'` (`:1270-1271`). `Particle.sorted_keys` = {antiname, charge, color, counterterm, is_part, line, mass, name, pdg_code, propagator, self_antipart, spin, type, width} (re-read the set at its definition, don't rely on a memorized length). For a standard UFO particle exactly **9** of its `__dict__` keys land in that set; the 10th comes from the **propagator-absence branch** (`:1320-1326`): if UFO has NO `propagator` attr, `nb_property+=1` and a massless spin≥3 gets `propagator=0`, or a massive spin-3 in Feynman gets `propagator=0` (`:1322-1326`). VERIFIED (probe, `import_full_model('sm')` → UFO top pdg 6): its `__dict__` sorted-keys hits are exactly {antiname, charge, color, **line**, mass, name, pdg_code, spin, width} = 9, and it has NO `propagator` attr → +1 = 10. NOTE: `line` is a DIRECT sorted-keys hit (every UFO Particle carries a `line` attr, computed by `find_line_type()` if not passed — `object_library.py:89-91`), NOT "line via propagating"; `propagating`, `selfconjugate`, `goldstoneboson`, `texname`/`antitexname`, `GhostNumber`/`LeptonNumber`/`Y` are NOT in sorted_keys (custom charges go to `conservecharge`, the rest are ignored).
- **colored-scalar flag** (`:1331-1333`): spin-1 + color≠1 + massless + non-ghost → `colored_scalar=True` (later: `limitations.append('fix_scale')`, alpha_s running unsupported).
- **self-conjugate** (`:1337-1338`): `if particle_info.name == particle_info.antiname: self_antipart=True`.
- **counterterm** (loop models only, `:1342-1380`): wavefunction-renormalization counterterms become `UVWfct_*` couplings + a `particle['counterterm']` dict keyed `(order, (loop-particle-PDGs)) : {laurent: CTcouplingname}`.

## `detect_incoming_fermion` (`:1752`) — which of F/F~ is "incoming"
Scans `all_vertices` for fermion pairs (spin 2 or 4). For each `F F~` pair with `pdg[i]==-pdg[i+1]`, the FIRST-seen positive member goes to `self.incoming`, its conjugate to `self.outcoming` (`:1763-1771`). Odd fermion count in a vertex → `InvalidModel`. Inconsistent incoming/outcoming across vertices → `InvalidModel`. This set drives the UFO-pair dedup in `add_particle` (which antiparticle entry to skip).

## `find_color_anti_color_rep` (`:1651`) — 3 vs 3bar assignment
Looks at 3-particle vertices with two color-3 legs and a `T(...)`/`Identity(...)` color structure. From the index order in `T(3,2,1)` etc. it assigns one leg `output[pdg]=3` (color) and the other `-3` (anticolor) (`:1740`, `:1748`). A particle forced into BOTH → `InvalidModel('sometimes in the 3 and sometimes in the 3bar')`. Result `color_info` is passed into `add_interaction`→`treat_color`.

## `add_interaction` (`:1773`) — UFO Vertex → `base_objects.Interaction`
- Resolve UFO particles to internal via `model.get_particle(pdg)` (`:1777-1778`); if ANY is `None` (a ghost/goldstone that was dropped) → `return` (vertex skipped) (`:1779-1781`).
- **Fermion-flow check** (`:1788-1804`): 2-fermion uses UFO's flow (validated by `aloha_fct.check_flow_validity`); >2 fermion computes a permutation sign via `get_sign_flow` (`:1824-1827`, `:1878`), and a `-` sign is prepended to the coupling name when the permutation is odd. Majorana in a 4+-fermion vertex → `InvalidModel`.
- **One Interaction per distinct coupling-order tuple** (`:1816-1860`): couplings with the same `order` tuple merge into one `Interaction`; a new order tuple makes a new `Interaction({'id': len(self.interactions)+1})` with particles, lorentz (names only, `:1810`), couplings dict keyed `(color_idx, lorentz_idx)`, orders, color, type, loop_particles. A `'1'`-order coupling → `InvalidModel` (MG forbids order name `1`).
- **Non-QCD gluon-emission counter** (`:1838-1842`): a gluon (pdg 21) in a vertex whose coupling order lacks `'QCD'`, with all legs colored, increments `non_qcd_gluon_emission` → later `allow_pickle=False` + MLM limitation (`:612-618`).
- **Charge-conservation pruning** (`:1865-1874`): for each candidate conserved charge, if any vertex violates it (`|sum|>1e-12`), that charge is discarded from `conservecharge` (logged "interaction violating the charge"). Survivors become `model['conserved_charge']` (`:636`).

## Antiparticle generation is LAZY, at `particle_dict` build (not in add_particle)
`add_particle` appends only ONE entry per particle. The antiparticle is synthesized only when
`particle_dict` is first requested: `ParticleList.generate_dict` (`madgraph/core/base_objects.py:591-605`)
keys each particle by its pdg, and `if not self_antipart: antipart = copy.deepcopy(particle); antipart.set('is_part', False); particle_dict[anti_pdg]=antipart`. So the in-memory `Model['particles']` list is HALF the dict size. `Model.get('particle_dict')` (`base_objects.py:1181-1186`) builds it lazily on first access AND calls `synchronize_interactions_with_particles`. `interaction_dict` similarly lazy (`:1215-1217`, keyed by interaction `id`). VERIFIED (probe, `import_full_model('sm')` = the converter's full/unrestricted output, unitary gauge): 17 list entries → 30 dict keys (4 self-conjugate a/z/g/h not doubled: 17×2−4=30); a/z/g/h `self_antipart=True`, w+/t/b not; massless a & g (spin 3, ZERO) get `propagator=0`, massive z/w+ keep `propagator=''`. (SM restriction drops no particles, so `import model sm` reaches the same 17/30; a restricted model that prunes particles would have fewer — the list/dict 2:1 relation holds per-particle regardless.)

## Parameters/couplings → `OrganizeModelExpression(ufo_model).main()` (`:415`, class `:2040`)
Not built in the converter — `import_full_model` calls `OrganizeModelExpression(ufo_model).main(additional_couplings=wavefunction_CT_couplings if perturbation else [])` (`:415-417`) and does `model.set('parameters', parameters)` / `set('couplings', couplings)` / `set('functions', all_functions)` (`:419-421`). `main` (`:2082`) runs `analyze_parameters` + `analyze_couplings`, returning dicts keyed by the parameter dependency tuple (e.g. `()` for constants, `('external',)`, `('aS',)` for aS-dependent — VERIFIED on SM). The keys group params/couplings by what they depend on, so the generated Fortran recomputes only aS-dependent quantities per-event. [Expression-detail interior is shared with ufo slice; the SET into the Model is this slice's boundary.]

## "Drop unreachable" optimization at load time
The only load-time pruning in the converter: `optimise_interaction` removes interactions whose coupling dict emptied after identical-coupling collapse + ZERO removal (`:630-633`, `:686-708`), and `add_interaction`/`add_particle` early-returns for dropped ghosts/goldstones. There is NO "drop particles not reachable from a process" step here — that is restriction's job (restriction slice) and runs LATER on the assembled model.

## Cautions (source-visible)
- `mass`/`width` are stored as PARAMETER-NAME STRINGS (`str(value)`), never numbers — the numeric value comes from the param_card at runtime. A page reasoning about "the b mass" must read the parameter, not the particle field.
- The particle LIST is half the `particle_dict`: code iterating `model['particles']` sees one entry per pair; code wanting antiparticles must go through `particle_dict`/`get_particle`.
- `propagator` field is gauge-dependent at conversion (index 0 unitary / 1 Feynman, or `0` for massless spin≥3 / Feynman massive spin-3) — see gauge-dependent-model-loading.md; the converter bakes the gauge choice into the particle at load.
- `conservecharge` starts as `{'charge'}` plus every non-standard UFO particle attribute; it is PRUNED down by any interaction that violates a charge — so the final conserved-charge set is interaction-dependent, decided during `add_interaction`.
