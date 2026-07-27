---
description: How aloha.unitary_gauge controls the UFO->MG5 conversion at load — Goldstone drop/keep, gauge-keyed propagator element selection, massive-vector propagator=0, FD merge_all_goldstone; plus the gauge/prefix-keyed pickle cache + reload guard.
---

# Gauge-dependent model loading (the converter interior) (v3.7.1)

`$MADGRAPH_INSTALL/models/import_ufo.py`. This is the *loading-side* effect of the
gauge choice — distinct from `gauge-selection-and-loopmodel-autoswitch.md` (which owns
the do_import selection/auto-switch). Here the already-chosen `aloha.unitary_gauge`
reaches into `UFOMG5Converter` and `import_full_model` and changes WHICH particles enter
the model and WHAT propagator they get. This is the mechanism behind "Goldstones appear
under Feynman" that the gauge page and `import-time-model-rewrites.md` flag at the
behavior level.

`aloha.unitary_gauge` encoding (module-level, set by `set2_gauge`):
`True`/`1`=unitary, `2`=axial, `3`=FD, `False`=Feynman. (See gauge page for the
do_set mapping.)

### The truthiness trap (read before claiming any gauge-dependent behavior here)
Every site below tests `aloha.unitary_gauge`, but with **four different predicates** — and
axial(`2`)/FD(`3`) classify differently under each. Pick the wrong predicate and you invert
the answer for axial/FD (this is exactly the error that previously bit the massive-vector and
FD-merge sections of this page). The map:
| predicate | unitary(True/1) | axial(2) | FD(3) | Feynman(False) | site |
|-----------|-----------------|----------|-------|----------------|------|
| `unitary_gauge in [1,2]` (+`0 in gauge`) | drop | drop | keep* | keep | goldstone drop :1245 |
| `if aloha.unitary_gauge` (truthy) | value[0] | value[0] | value[0] | value[1] | propagator-list pick :1298 |
| `not aloha.unitary_gauge` | no | no | no | **yes** | massive-vector prop=0 :1325 |
| `== 1` / `== 3` / else | model.pkl | Feynman.pkl | FDG.pkl | Feynman.pkl | pickle name :355 |
| `== 3` | no | no | **yes** | no | FD goldstone-merge :608 |
\*FD keeps at :1245 but then merges-away at :608, so its net particle set matches unitary.
**Rule:** axial(2) and FD(3) are TRUTHY, so any `if unitary_gauge` / `not unitary_gauge`
branch treats them as unitary-like; only the explicit `in [1,2]` / `==N` checks single them
out. Never say "non-unitary" when the code says `not aloha.unitary_gauge` — that means
**Feynman only**.

## Goldstones are dropped at conversion time (`add_particle`, :1245-1254)
Inside `UFOMG5Converter.add_particle`, BEFORE the Particle object is built:
```python
if (aloha.unitary_gauge in [1,2] and 0 in self.model['gauge']) \
                    or (1 not in self.model['gauge']):
    # MG5 doesn't use goldstone boson
    if ... GoldstoneBoson ...: return
    if ... goldstoneboson ...: return
    elif ... goldstone ...: return
```
So a particle flagged Goldstone in the UFO is **not loaded at all** when:
- gauge is unitary/axial (`unitary_gauge in [1,2]`) AND the model permits unitary (`0 in gauge`), OR
- the model forbids Feynman entirely (`1 not in gauge`).
Under Feynman (`unitary_gauge==False`) with `1 in gauge`, the condition is false → Goldstones ARE loaded.
- **Probe-confirmed** (`/tmp` parse-time import of `sm`): under `aloha.unitary_gauge=True`,
  SM loads **17 particles, zero goldstones**; under `aloha.unitary_gauge=False`, **19
  particles incl. `g0`,`g+`** (`g-` is g+'s antiparticle, hence 2 extra Particle objects).
  `gauge` bits were `[0,1]` in both. This is exactly the `:1245` branch firing.

NB the goldstone is still TAGGED `type='goldstone'` lower down (`:1259-1264`) — that
tagging happens only for the particles that survived the early `return`, i.e. only in
Feynman/FD.

## Gauge-keyed propagator selection (`add_particle`, :1295-1303)
If the UFO particle carries a `propagator` attribute that is a list/dict:
```python
if aloha.unitary_gauge:  particle.set('propagator', str(value[0]))   # unitary -> element 0
else:                    particle.set('propagator', str(value[1]))   # Feynman -> element 1
```
So a UFO that ships two propagator forms gets the unitary form chosen under any non-False
`unitary_gauge` (1/2/3 all truthy), the Feynman form only under `unitary_gauge==False`.
**Caution:** axial(2)/FD(3) are truthy → they take `value[0]` (the unitary propagator
slot) here, NOT a dedicated axial/FD slot. A model intending a distinct FD propagator via
the list would not get it from this branch.

## Massive vector default propagator: Feynman ONLY, not "non-unitary" (`add_particle`, :1320-1326)
When the UFO particle has NO `propagator` attribute and `spin>=3` (vector or higher):
- `mass=='zero'` → `propagator=0` (default photon/gluon prop).
- `spin==3 and not aloha.unitary_gauge` → `propagator=0` too.
**CORRECTION (probe + truthiness):** `not aloha.unitary_gauge` is True ONLY when
`unitary_gauge==False` (Feynman). axial(`2`) and FD(`3`) are TRUTHY → `not 2`/`not 3` is
False → this branch does NOT fire for them. So a massive spin-1 (W/Z) gets `propagator=0`
**under Feynman gauge specifically**, NOT under "non-unitary" broadly. Under unitary AND
under axial AND under FD it keeps the default `''` (the unitary massive-vector propagator).
This is the SAME truthiness rule as the propagator-list pick at :1298 (axial/FD truthy →
unitary slot) — the two sections must agree.
- **Probe-confirmed** (parse-time `import_full_model('models/sm')` per gauge): W+ and Z
  `propagator` = `''` under unitary/axial/FD, `0` under Feynman; photon = `0` in all four.
  Particle counts: 17 (unitary/axial/FD), 19 incl. `g0`,`g+` (Feynman).
- `propagator=0` is NOT the empty default: helas_objects.py:1868 checks `propagator not in
  ['', None]` (and `0 not in ['','None']` is True) → `0` adds a `P0` HELAS tag, selecting the
  explicit (Feynman-style) massive-vector propagator; `''` selects the built-in unitary one.
This is the per-particle counterpart to the Goldstone keep — together they make Feynman
gauge use the (vector_Feynman + Goldstone) representation and unitary use (vector_unitary,
no Goldstone).

## FD gauge merges Goldstones into vectors (`load_model`, :608-609)
After all vertices are added, if `aloha.unitary_gauge == 3` (FD only — `3` is FD, the
docstring at :777 says "For Feynman Diagram gauge"; axial is `2` and does NOT trigger this):
`self.merge_all_goldstone_with_vector()` (def at `:776`). So FD gauge loads Goldstones
(they survive `:1245` because `unitary_gauge==3` is not in `[1,2]`) and then folds them
into the vector (`:783` removes the goldstone Particle from `self.particles`) — a third
representation distinct from both plain unitary and plain Feynman. **Net effect probe-
confirmed:** under FD the SM ends at 17 particles / 0 goldstones (same COUNT as unitary,
but reached by load-then-merge, not by the :1245 drop). (merge interior not walked here;
the trigger is the in-slice fact.)

## Pickle cache is gauge-keyed AND prefix-checked (`import_full_model`, :355-405)
The pickle filename is selected from `aloha.unitary_gauge` (`:355-360`):
`1`→`model.pkl`, `3`→`model_FDG.pkl`, else→`model_Feynman.pkl`; then `dec_` prefix if
`decay` (`:361-362`), then ALWAYS a `py3_` prefix (`:363`). So the on-disk names are
`py3_model.pkl` (unitary), `py3_model_Feynman.pkl` (Feynman/axial), `py3_model_FDG.pkl`
(FD), with `py3_dec_*` variants for the decay-loaded model. **Axial (2) and Feynman
(False) share `model_Feynman.pkl`** — only unitary(1) and FD(3) get distinct files; axial
reuses the Feynman pickle. This is the cache-side reason a gauge switch re-imports under a
different pickle (the behavior `import-time-model-rewrites.md` knob #3 flags).

**Prefix mismatch forces a `.py` reload** (`:378-402`): even with an up-to-date pickle and
matching `version_tag`, the loader scans the cached params: if `prefix` is set but a param
name does NOT start with the prefix (or `--noprefix` was given but a name DOES start with
`mdl_`), it logs `'reload from .py file'` and falls through to re-parse the UFO. So a
session that loaded a model with one prefix and then re-imports it with the other
(`--noprefix`) invalidates the pickle reuse and re-parses — the prefix is part of the cache
key in practice, even though it's not in the filename.

**`_import_once` "modified on disk" guard** (`:327`, `:386/396/404-405`): a module-level
list keyed `(model_path, aloha.unitary_gauge, prefix, decay)`. A successful pickle-reuse
appends the key (`:386`/`:396`). On a LATER import of the same key where the pickle is now
stale (`not allow_reload`, i.e. `is_uptodate` failed because a model file changed mid-
session): `raise MadGraph5Error('This model %s is modified on disk. To reload it you need
to quit/relaunch MG5_aMC')`. So editing a UFO file after it was loaded once forces a
restart rather than a silent re-parse. (This is the load-orchestration boundary; the
pickle save/load primitives themselves are ufo slice.)

## non-QCD gluon emission disables pickling (`load_model`, :612-618)
If the model has non-QCD gluon emission vertices: `logger.critical(...)` about MLM/dynamic-
scale restrictions, `self.model['allow_pickle']=False` (`:617`) and
`limitations.append('MLM')`. So such a model is NEVER cached (the `:450` save is gated on
`model['allow_pickle']`) and re-parses every import — a load-orchestration consequence of
model content.

## Boundary
- The do_import-level gauge SELECTION and auto-switch live in
  `gauge-selection-and-loopmodel-autoswitch.md`. This page is the import_ufo.py interior
  that the chosen gauge drives.
- `merge_all_goldstone_with_vector` interior, the UFO particle-attribute semantics, and the
  pickle save/load primitives are ufo slice; this page owns only how the GAUGE/PREFIX
  selection changes the loaded particle set, propagators, and cache key.
