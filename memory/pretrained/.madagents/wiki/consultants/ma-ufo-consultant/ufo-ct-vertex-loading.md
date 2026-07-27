---
description: Loader-side parsing of the NLO files into Model counterterms — add_CTinteraction (CT_vertices — type gate R2/UV/UVloop/UVtree/UVmass, bare-UV auto-classification, add_NLO() in except-pass, laurent-pole unfold _1eps/_2eps, double-pole InvalidModel, 3-axis split order x loop_particles x pole) PLUS two sibling paths — treat_couplings CTParameter->dict substitution (_FIN_/_1EPS_ UPPER), and add_particle wavefunction-CT consumption (synthesizes UVWfct_* couplings). Authored grammar = ufo-ct-file-object-grammar.md; MadLoop consumption = nlo-model/madloop slice.
---

# UFO CT vertex loading — add_CTinteraction (import_ufo.py, v3.7.1)

Refs in `$MADGRAPH_INSTALL/models/import_ufo.py`. Complements `ufo-vertex-to-interaction-conversion.md` (the BASE-vertex `add_interaction`) and `ufo-expression-shortening-and-event-dependence.md` (CT *parameter* pole-split `get_additional_CTparameters`). This page is the CT *vertex* path. SCOPE: how the loader turns `CT_vertices.py` into Model counterterm interactions. What MadLoop does with the resulting R2/UV interactions is **nlo-model / madloop slice** — not here.

## When it runs (l.620-627)
Only when `self.perturbation_couplings` is non-empty (a loop model — set by some order's `perturbative_expansion > 0`, see `ufo-coupling-orders-and-propagators.md`). Then:
```python
if self.perturbation_couplings:
    try:
        self.ufomodel.add_NLO()
    except Exception as error:
        pass
    for interaction_info in self.ufomodel.all_CTvertices:
        self.add_CTinteraction(interaction_info, color_info)
```
**Non-obvious #1**: `add_NLO()` (the UFO model's own hook that generates/expands NLO vertices) is wrapped in a **bare `except Exception: pass`** — if it raises, the failure is swallowed and the loader proceeds to read whatever `all_CTvertices` already contains. A model whose `add_NLO` silently fails loses NLO vertices with no error at this point.

## add_CTinteraction (l.1556-1648)

### Type gate (l.1568-1579)
`interaction_info.type` MUST be in `['UV','UVloop','UVtree','UVmass','R2']`, else `MadGraph5Error` ("MG5 only supports the following types of vertices, R2, UV and UVmass"). **Non-obvious #2 — bare `'UV'` auto-classification** (l.1573-1579): a vertex declared simply `type='UV'` is reclassified:
- exactly 2 particles with the SAME name -> `UVmass` (a mass-renormalization counterterm).
- otherwise -> `UVloop`.
So `UVloop`/`UVtree`/`UVmass`/`R2` are explicit; a plain `UV` is resolved by particle content.

### Laurent-pole unfolding (l.1611-1637)
Each CT coupling carries a Laurent series in 1/eps. For each `poleOrder` in `range(0,3)` (finite=0, single=1, double=2), `expression = coupling.pole(poleOrder)`:
- `'ZERO'` -> skipped (that pole order contributes nothing).
- `poleOrder == 2` and non-`ZERO` -> **`InvalidModel`** raised ("CT coupling ... found with a contribution to the double pole. This is either an error in the model or a parsing error in 'is_value_zero'"). So the loader ASSERTS no genuine double pole survives in a CT coupling — a real double pole is treated as a model/parse error, not loaded.
- Otherwise a `copy.copy` of the coupling is made (deliberately NOT a reference to the UFO coupling — comment l.1622-1624), `.value` set to the pole expression, and for `poleOrder != 0` the name gets a `"_<poleOrder>eps"` suffix (`_1eps`). The `copy.copy` matters: mutating the new coupling won't corrupt the shared UFO coupling object.

### 3-axis split -> add_interaction (l.1597-1648)
One CT vertex fans out along THREE axes into base interactions:
1. **coupling-order tuple** `tuple(coupling.order.items())` (l.1601) — `order_to_interactions` dict, same order-tuple-grouping idea as the base `add_interaction` (see vertex page).
2. **loop_particles element** — `new_couplings[loop_particles_index][poleOrder]`; `new_couplings = [[{} for j in range(3)] for i in range(max(1,len(loop_particles)))]` (l.1605-1606). `key[2]` of the coupling dict key selects the loop_particles slot (l.1637).
3. **laurent pole order** 0/1/2.

Then (l.1638-1648) for each (order, loop_particles-slot, pole) cell that is non-empty, `self.add_interaction(interaction_info, color_info, label, loop_particles)` is called — routing back through the SAME base `add_interaction` (vertex page) but with a **type label**:
```
label = intType  if poleOrder==0  else  intType + str(poleOrder) + 'eps'
```
i.e. `R2`, `UVloop`, `UVmass`, `UVtree` for finite; `UVloop1eps`, `R21eps`, etc. for the single-pole piece. `loop_particles` is passed as a list of pdg-code lists (`[part.pdg_code for part in loop_parts]`, l.1642-1643) and stored on the interaction (`interaction.set('loop_particles', ...)`, l.1857 in add_interaction).

## What this means at the Model level
A single `CT_vertices.py` entry can become MANY base interactions — (distinct coupling-order signatures) × (loop_particles combinations) × (non-zero pole orders) — each a `base_objects.Interaction` carrying a CT type tag and a `loop_particles` list. These live alongside the tree interactions in `self.interactions`. The base-vertex order-tuple split (vertex page) and this CT split share `add_interaction`; the CT path adds the pole and loop_particles axes on top.

## Two OTHER CT consumption paths (not add_CTinteraction)
The CTVertex path above is only one of THREE ways the loader turns NLO file content into Model objects. The other two run earlier in `load_model` and are easy to miss (authored grammar of their inputs: `ufo-ct-file-object-grammar.md`):

### (a) CTParameter substitution into CT-coupling strings — `treat_couplings` (call l.598, def l.1383)
A CT coupling whose `value` is a STRING that references a `CTParameter` (e.g. loop_sm `GC_4GR2_Gluon_delta5 value='-4.0*complex(0,1)*RGR2*(2.0*lhv+5.0)'`, where `RGR2` is a CTParameter) is rewritten into a Laurent DICT by substituting the CTParameter's poles (comment l.587-594): `value='2*RGR2'` → `{-1:'2*RGR2_1EPS_', 0:'2*RGR2_FIN_'}`. The `_FIN_`/`_1EPS_`/`_2EPS_` UPPERCASE suffixes come from `pole_dict={-2:'2EPS',-1:'1EPS',0:'FIN'}` (l.60) — the SAME UPPER convention as the CTParameter pole-split (expression page), distinct from the coupling-path lowercase `_1eps`. **Non-obvious**: this mutation is applied DIRECTLY to the UFO model object and is REVERTED only inside `OrganizeModelExpression.main()` (comment l.592-594: "must be run on the UFO to have this change reverted") — a path that loads the model but never runs `OrganizeModelExpression.main` would leave the UFO model in the substituted state. A name-collision between a `<CTparam>_<FIN/1EPS/2EPS>_` synthesized name and an existing param raises `InvalidModel` (l.549-556). Runs only `if hasattr(self.ufomodel,'all_CTparameters')` — so a model with no `CT_parameters.py` skips it entirely (SMEFTatNLO is such a model — verify against `models/SMEFTatNLO/` when present, else the test fixture, since it is an oscillating EFT model); loop_sm (reliably shipped) runs it.

### (b) Particle-attached wavefunction-renormalization counterterm — in `add_particle` (l.1342-1379)
A particle carrying a `counterterm` dict (loop_sm `particles.py:318-329`, e.g. `b.counterterm={(1,0,0):CTParam.bWcft_UV.value}`) is consumed in `add_particle`, GATED on `self.perturbation_couplings and counterterms!={}` (l.1342 — else the particle is appended unchanged and returns). For each key (a tuple `(order1,...,orderN,loop_group#)`):
- **one-loop check** (l.1354-1355): exactly one order index ==1 AND none >1, else the key is skipped (only one-loop wavefunction CTs survive).
- **synthesizes a NEW Coupling** `UVWfct_<particlename>_<loop#>` with `value=counterterm` (the Laurent dict) and `order={ordername:2}` (l.1373-1376), popped onto `self.wavefunction_CT_couplings` (l.1377) — a coupling present in NO `.py` file, created at load.
- **rewrites** the particle's `counterterm` attr to `('ORDERNAME',((pdg_tuple),)):{laurent_order:UVWfctCouplingName(+'_<n>eps')}` form (l.1356-1370) and `particle.set('counterterm', particle_counterterms)` (l.1379).

So loop_sm's `b`/`c`/`t`/`G` end up with a synthesized `UVWfct_*` coupling each (b,c,t one; G three for c/b/t loops), invisible in the source files. This is the loop-UFO analogue of the CTVertex path but for self-energy/wavefunction CTs declared on the particle, not as a vertex.

PROBE-CONFIRMED (`import_full_model('$MADGRAPH_INSTALL/models/loop_sm')`, this install): loads as `LoopModel`. Synthesized `UVWfct_*` finite couplings = {`UVWfct_b_0`,`UVWfct_c_0`,`UVWfct_t_0`,`UVWfct_G_0`,`UVWfct_G_1`,`UVWfct_G_2`} (b/c/t one each, G three for c/b/t loops) each with a `_1eps` single-pole sibling — present in NO `.py` file. The c-quark's particle `counterterm` attr is reshaped to key `('QCD', ((4,21),))` (order QCD, loop content c=4 + gluon=21) — the `('ORDERNAME',((pdg_tuple),))` form (l.1368-1370). CT interaction-type KEYS present on the loaded Model: `R2`, `UVloop`, `UVloop1eps`, `UVmass`, `UVmass1eps` (+`base` tree) — confirms the bare-`UV`→`UVloop`/`UVmass` auto-classify (#2) and the `1eps` single-pole laurent siblings. (Re-probe for per-key counts; they drift with model version.)

## Boundary (out of slice)
- HOW MadLoop reads these R2/UV/UVmass interactions, the CTParameter EPS/FIN expansion at code-gen, the R2 vs UV diagram bookkeeping — **nlo-model / madloop slice**. This page stops at "the loader produced these counterterm interactions on the Model."
- `coupling.pole(...)` and `add_NLO()` are methods on the UFO model's own `object_library` Coupling / model — the loader CALLS them; their internal definition is UFO-author territory.

## Caution
- A model with a genuine non-zero **double pole** in a CT coupling will HARD-FAIL at load (`InvalidModel`), not warn — the loader's contract is that CT double poles are always ZERO after `is_value_zero` parsing.
- `add_NLO()` failing is SILENT (`except: pass`) — a loop model that loads "fine" but is missing expected CT vertices may have had `add_NLO` throw. There's no log at l.622-625; the symptom is missing counterterm interactions downstream.
- The CT path only runs for `perturbation_couplings` models; for a tree model `all_CTvertices` is never read even if the file exists.
