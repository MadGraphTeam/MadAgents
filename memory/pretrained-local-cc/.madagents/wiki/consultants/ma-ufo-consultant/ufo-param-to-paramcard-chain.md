---
description: The UFO-declaration -> param_card membership chain — which Parameter attributes (nature/value/lhablock/lhacode/scale) decide param_card inclusion and how the loader (import_ufo.OrganizeModelExpression.analyze_parameters) carries them into a base_objects.ParamCardVariable that the writer consumes. The 'external' membership predicate, the ('external',) parameters-dict key, texname/type dropped at the boundary, scale 5th attr, mdl_ prefix in card comment. Boundary to ma-param-card-consultant (the writer) cited, not walked.
---

# UFO Parameter -> param_card membership chain (v3.7.1)

Topic: how a `parameters.py` `Parameter` *declaration* becomes (or fails to become) a `param_card` entry — the IN-SLICE part of the chain (declaration + loader read). Complements `ufo-declaration-object-grammar.md` (the static `Parameter` attribute semantics) and `ufo-smeft-eft-representation.md` (WCs as external params in EFT LHA blocks). The actual card-text writer is `ma-param-card-consultant` territory — cited as the boundary below, not walked. Refs: `$MADGRAPH_INSTALL/models/import_ufo.py`, `madgraph/core/base_objects.py`, `models/object_library.py`. `coupling_orders.py` is covered at the end (it carries NOTHING to the card).

## 1. The Parameter attributes that matter for the card (object_library.py:146-164)

`Parameter(name, nature, type, value, texname, lhablock=None, lhacode=None)` (sm `object_library.py:146`). The card-relevant subset:
- `nature` ∈ {'external','internal'} — THE membership gate (see #2). external -> card; internal -> never.
- `value` — for external, a NUMERIC LITERAL (the param_card DEFAULT). For internal, an expression STRING (excluded).
- `lhablock` — the param_card block name (e.g. `'SMINPUTS'`, `'MASS'`, `'DECAY'`, EFT `'DIM6'`/`'DIM62F'`/`'FCNC'`).
- `lhacode` — a LIST (e.g. `[1]`, `[3]`, `[23]`) = the code(s) within the block.
- **REQUIRED-for-external invariant** (`object_library.py:161-162`): `if (lhablock is None or lhacode is None) and nature == 'external': raise Exception('Need LHA information for external parameter "%s".')`. So an external param ALWAYS has both lhablock+lhacode — there is no such thing as a card-less external param (it would fail to import). An internal param has neither.
- `texname`, `type` — NOT used for the card (see Cautions). `texname` is read only for CTparam pole-piece naming (`import_ufo.py:2128`) and particle display, never the param_card.
- `scale` — NOT a positional arg; an optional kwarg an author may pass (caught by `UFOBaseClass **options`). See #4.

### sm concrete anchor — MASS vs YUKAWA are independent externals (parameters.py, v3.7.1)
The b-quark carries TWO independent external params, same lhacode [5], DIFFERENT block + DIFFERENT default value:
- `MB` = Parameter external, `lhablock='MASS'`, `lhacode=[5]`, value **4.7** (`parameters.py:149-155`) — pole mass, feeds propagator + kinematics.
- `ymb` = Parameter external, `lhablock='YUKAWA'`, `lhacode=[5]`, value **4.2** (`parameters.py:85-91`) — Hbb coupling strength. Different number proves they are decoupled inputs, not the same slot.

The full sm YUKAWA block = exactly SIX members (`parameters.py:77-123`): `ymc`[4]=1.27, `ymb`[5]=4.2, `ymt`[6]=164.5, `yme`[11]=0.000511, `ymm`[13]=0.10566, `ymtau`[15]=1.777. **NO first-gen QUARK Yukawa exists** — there is no ymu/ymd/yms Parameter at all, so u/d/s have NO Higgs coupling in sm by construction (not "small" — absent). All six external Yukawas feed an INTERNAL derived `y*` param `= (ym*·√2)/vev` (`parameters.py:349-384`: yb/yc/ye/ym/yt/ytau), which is what the couplings.py GC_* reference.

Hbb vertex chain (for a "does ymb=0 remove Hbb" probe): external `ymb` → internal `yb=(ymb·√2)/vev` (`parameters.py:352`) → `GC_83 = -i·yb/√2`, order {QED:1} (`couplings.py`) → `V_78 = Vertex(particles=[b~,b,H], lorentz=[FFS4], couplings={(0,0):GC_83})` (`vertices.py:474-478`). So zeroing external YUKAWA[5] zeroes GC_83; the restriction-time removal of V_78 (evaluated coupling → 0) is `ma-restriction-consultant`'s call, but the coupling→vertex wiring is as cited here.

## 2. The membership predicate: nature=='external' -> ParamCardVariable (import_ufo.py:2155-2166)

The carry happens in `OrganizeModelExpression.analyze_parameters` (`import_ufo.py:2155`):
```python
for param in self.model.all_parameters+additional_params:
    if param.nature == 'external':
        parameter = base_objects.ParamCardVariable(param.name, param.value,
                                       param.lhablock, param.lhacode,
                                       param.scale if hasattr(param,'scale') else None)
    else:
        expr = self.shorten_expr(param.value)
        depend_on = self.find_dependencies(expr)
        parameter = base_objects.ModelVariable(param.name, expr, param.type, depend_on)
    self.add_parameter(parameter)
```
- external -> `base_objects.ParamCardVariable(name, value, lhablock, lhacode, scale)` (`base_objects.py:2062-2080`). This class is literally "the parameter which should be defined in the param_card.dat" (its docstring). It carries ONLY `name`, `value`, `lhablock`, `lhacode`, `scale` — `texname`/`type` are dropped here.
- internal -> `base_objects.ModelVariable(name, shortened-expr, type, depend_on)` — no lhablock/lhacode; it is a computed quantity, never a card line.

**`ParamCardVariable.depend = ('external',)`** is a CLASS attribute (`base_objects.py:2066`), and `add_parameter` (`import_ufo.py:2169`) keys `self.params[parameter.depend].append(parameter)` at `:2180` (NOT `:2178`, which is the `all_expr[name]=parameter` line). So EVERY ParamCardVariable lands under the `('external',)` key; ModelVariables land under their actual dependency tuple (`()`, `('aEW',)`, etc.). This is set onto the Model as `model['parameters'][('external',)]`.

**So the param_card-membership predicate at the UFO/loader level is exactly: `Parameter.nature == 'external'`.** That and only that puts a parameter into `model['parameters'][('external',)]`, the list the writer iterates.

## 3. The boundary — the writer consumes model['parameters'][('external',)] (ma-param-card-consultant)

`models/write_param_card.py` `ParamCardWriter` (`:43`) is the WRITER and is param-card slice. For provenance of WHERE the chain hands off (do not re-walk):
- `write_param_card.py:81`: `self.external = self.model['parameters'][('external',)]` — it reads exactly the `('external',)` list the loader built.
- It uses per-param: `lhablock` (block grouping + sort, `:153/205/209`), `lhacode` (`:167/265`), `value` (`:249/253/271` — written as the default `%e`), `scale` (`:216` -> `Block <name> Q= <scale>`), optional `info`/`name` (the `# comment`).
- It does NOT read `texname` or `type`. The Fortran-vs-Python type split is handled elsewhere.
- `mdl_` prefix: the writer STRIPS `mdl_` from the comment text in `write_param` (`write_param_card.py:246-247`: `if info.startswith('mdl_'): info = info[4:]`), but the LHA block/code are unaffected (the prefix is on the param `name`, not lhablock/lhacode). So a prefixed param `mdl_cpDC` still writes under `Block dim6 ... 2 ... # cpDC`. (Two OTHER `mdl_`-strips exist for dependent-param comment expressions at `:298` and `:313` via `.replace('mdl_','')` — those are the derived-param formula comments, not the external-block comment.) RECONCILED with ma-model-loader-consultant, which also cites `:246-247`; an earlier `:243-244` here was off by 3 lines (`:243` is `info = param.info`).

That is the full in-slice chain: UFO declaration (#1) -> loader external-gate into ParamCardVariable (#2) -> writer reads the `('external',)` list (#3, param-card slice).

## 4. scale — the optional 5th attribute (a Q= block-scale, rarely exercised)

`ParamCardVariable.__init__(name, value, lhablock, lhacode, scale=None)` (`base_objects.py:2069`). The loader passes `param.scale if hasattr(param,'scale') else None`. The base `Parameter` signature has NO `scale`, so it is set ONLY if a model author passes `scale=` as a kwarg.
- PROBE (`grep -l "scale=" models/*/parameters.py` = 0): NO bundled model (sm, SMEFTatNLO, dim6top, ...) declares a `Parameter(... scale=...)`. So in practice every ParamCardVariable has `scale=None`.
- When non-None it surfaces as `Block <name> Q= <scale>` (the renormalization-scale-stamped block, `write_param_card.py:216,231` — boundary). Relevant to running/loop-input blocks (the `lhablock=='loop'` family) but not authored via `scale=` in the bundled set.

## 5. coupling_orders.py carries NOTHING to the param_card

`CouplingOrder(name, expansion_order, hierarchy, perturbative_expansion=0)` (`coupling_orders.py`). The loader reads these into the Model's `order_hierarchy` / `expansion_order` DICTS (`import_ufo.py:638-677`, see `ufo-coupling-orders-and-propagators.md`) — these are per-process coupling-order CAPS and WEIGHTED-ranking, NOT param_card content. There is NO param_card block for QCD/QED/NP/DIM6 ORDERS. (EFT Wilson-coefficient *values* are `Parameter`s in LHA blocks named after the EFT order — e.g. block `DIM6` — but that is a parameters.py Parameter, #1-#3, not the CouplingOrder object. Don't conflate the order NAME used as an LHA block name with the CouplingOrder declaration.)

## Gaps (other slices)
- The actual card TEXT, block ordering, dependent-param comment blocks, `# (Note: not used if you use a PDF set)` for SMINPUTS#3, operative-priority of an edited card vs default — `ma-param-card-consultant` (the writer + the param-card lineage).
- Which external params `restrict_*.dat` ZEROES/prunes (and the 9.999999e-1 / 0.000001e-99 restriction sentinels the writer special-cases at `:253-256`) — `ma-restriction-consultant`.
- What physical VALUE a WC/mass/width should take — physics slice.
- Fortran param_card.inc / MG5_param.dat generation from the card — output/export slice.

## Cautions (source-visible)
- **`texname` and `type` never reach the param_card.** They are dropped at the ParamCardVariable boundary (`import_ufo.py:2157` passes only name/value/lhablock/lhacode/scale). Don't expect a UFO param's `type='complex'` or its `texname` to influence the card; the writer even rejects a non-real external value (`write_param_card.py:249-250`).
- **An internal parameter is excluded by the `nature` gate, NOT by missing lhablock.** It is impossible for an external to lack lhablock (import raises). So "won't appear in the card" is decided purely by `nature=='internal'` -> ModelVariable. A WC that the author wrote as internal (a formula) is NOT a card entry, even if it looks like a coupling you'd want to dial — only the external inputs it derives from are.
- **`scale=` is a real but bundled-unused author feature.** Treat ParamCardVariable.scale as None unless a specific model declares it; don't assume a Q= block-scale exists.
- **The `('external',)` dict key is the single source of param_card membership.** A parameter visible in `model['parameters'][()]` (or any non-`('external',)` key) is internal/derived and will NOT be written. Don't infer card membership from the param existing on the Model; check its depend-key / nature.
- **aS/SMINPUTS#3 is a hard contract** (`import_ufo.py:888-905 check_model_aS`): the external param at SMINPUTS lhacode [3] MUST be named aS/alphaS (else `UFOImportError`), and aS MUST be SMINPUTS#3. So that one card slot is name-locked at import — covered in `ufo-loader-validation-gates.md`.

## Probe-candidates
- (cheap, candidate) Load sm and dump `model['parameters'].keys()` + `[(p.name,p.lhablock,p.lhacode,p.value) for p in model['parameters'][('external',)]]` to confirm the external list == the param_card blocks (SMINPUTS/MASS/YUKAWA/DECAY) and that internals are absent. Pairs with the `ufo-loaded-model-diverges-from-files.md` count probe.
- (cheap, candidate) Load SMEFTatNLO (raw import_full_model) and confirm the EFT WC blocks (DIM6/DIM62F/DIM64F*/FCNC) appear in `model['parameters'][('external',)]` with their lhacodes — verifies the EFT-WC -> card chain end to end at the loader level (writer is boundary).
