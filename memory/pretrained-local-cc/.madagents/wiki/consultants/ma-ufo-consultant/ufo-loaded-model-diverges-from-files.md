---
description: The loaded MG5 Model is a transformed image of the UFO files, not a copy — the loader drops, adds, renames, and splits, so loaded counts/names diverge from the .py files BEFORE restriction runs.
---

# The loaded Model is NOT a 1:1 image of the UFO files (v3.7.1)

Synthesis page. The single most common UFO confusion — "the loaded model has a different particle/vertex/parameter count (or a parameter name) than the `.py` files declare" — is not a bug. The loader is a **transformation pipeline**, and the loaded `Model` diverges from the literal UFO in FOUR independent directions, all BEFORE restriction touches anything:

| Direction | Where | Effect |
|---|---|---|
| **DROP** | Stage-1 add_particle / add_interaction | particles and vertices vanish |
| **ADD** | Stage-2 shorten_expr | NEW parameters appear that are in no `.py` file |
| **RENAME** | prefix stamp / LMER merge / conjg__ etc. | loaded names ≠ UFO names |
| **SPLIT** | add_interaction order-tuple loop | one Vertex → several Interactions |

This page is the index of the divergence; the per-mechanism deep-dives own the details.

## Probe-grounded inventory (sm, this install)
Raw UFO (`ufomodels.load_model` of `models/sm`) vs loaded Model, **loader stage only** (sm-full, restriction suppressed) vs further restriction:

Re-probe recipe: `ufomodels.load_model('models/sm')` (raw) vs the loaded Model, comparing `len(...)` for each quantity, loader-stage-only (restriction suppressed) vs after restriction. The DIRECTION of change per quantity is the durable fact; the exact integers are this-install probe data that drift — re-count, don't cache the number.

| Quantity | Raw → loader stage | loader stage → restriction |
|---|---|---|
| particles | DROPS (gauge Goldstones/ghosts) | unchanged by restriction |
| vertices→interactions | DROPS | shrinks further |
| parameters | **INCREASES** (loader ADDS) | shrinks |
| couplings | **UNCHANGED** (loader drops none) | shrinks |
| lorentz | unchanged | unchanged |

Two facts this isolation makes sharp:
- The loader **ADDS** params: the additions are Stage-2 shortening intermediates (`mdl_complexi`, `mdl_MZ__exp__2`, `mdl_MZ__exp__4`, `mdl_cw__exp__2`, `mdl_sqrt__2`, `mdl_conjg__CKM1x1`, …) — stripped-unique names in the loaded model that are in NO `parameters.py` entry. They originate in `shorten_expr` (`import_ufo.py:2276`), not the UFO. See `ufo-expression-shortening-and-event-dependence.md`.
- The loader does **NOT** drop couplings (in-count == out-count at loader stage). The subsequent shrinkage is ENTIRELY the restriction stage (param-pruning/coupling-merging), which is **restriction slice, not mine** — do not attribute the coupling drop to the loader. (Within the loader, `optimise_interaction`'s ZERO/identical-collapse only reduces per-interaction coupling *references*, not the global coupling object set.)

## The four directions, with owning deep-dive

### DROP (loaded < files)
- **Particles** 43→17: Goldstones dropped in unitary/axial gauge, ghosts dropped in tree models — `add_particle` l.1242/1245. See `ufo-loader-gauge-and-pickle.md`.
- **Vertices** dropped two ways: (1) any vertex referencing a dropped particle is silently skipped — `add_interaction` l.1779-1781 (`if None in particles: return`); (2) any interaction whose `couplings` dict empties after order-splitting is pruned post-pass — l.630-633. See `ufo-vertex-to-interaction-conversion.md`.
- These are the **silent drops** the validation-gates page catalogs — no error, just fewer objects than declared.

### ADD (loaded > files)
- **Parameters**: Stage-2 `shorten_expr` (l.2276) factors repeated sub-expressions into NEW `ModelVariable`s — `complexi`, `X__exp__n`, `op__x` (cmath), `conjg__x`. These are loader artifacts, present in the loaded Model and emitted into generated Fortran/Python, absent from the UFO. See `ufo-expression-shortening-and-event-dependence.md`.

### RENAME (same object, different name)
- **Prefix**: `model.change_parameter_name_with_prefix()` (l.442 -> `base_objects.py:1627`) stamps `mdl_` onto parameter names when `prefix` is truthy (the restriction-default load passes `prefix='mdl_'`). NOT universal — a WHITELIST is exempt: `['as','mu_r','zero','aewm1','g']` (the list literal is at `base_objects.py:1658`; the function `change_parameter_name_with_prefix` is defined at l.1627) are NEVER prefixed. (Note: this 5-name list includes `g`; the PICKLE prefix-CHECK skip-list `['as','mu_r','zero','aewm1']` at `import_ufo.py:382` is the 4-name subset WITHOUT `g` — see `ufo-loader-gauge-and-pickle.md`. Two different lists for two different purposes; `g` is in the whitelist, which is why loaded `G` stays bare.) Params already starting with `prefix`, or empty, are also skipped. PROBE (loaded sm, this install): 48 of 52 param names carry `mdl_`; the 4 bare ones are exactly the present whitelist members `aS`, `aEWM1`, `G`, `ZERO` — THIS is why `all(...mdl_)` is False, not randomness.
- **Case-collision de-dup** (base_objects.py:1669, the `for value in duplicate` loop): `change_parameter_name_with_prefix` ALSO renames parameters identical up to case (e.g. `MW` vs `mw`) into `<prefix><lowername>__<n>` (1-based, suffix only for n>1). The guard `if prefix=='' and not duplicate: return` (l.1648) means this de-dup runs EVEN with `prefix=''` when a case-collision exists — so a no-prefix load can still rename colliding params. `as`/`mu_r`/`zero`/`aewm1`/`g` whitelist applies before the collision pass.
- **Merged Lorentz** (`LMER…`): when one coupling spans multiple Lorentz at the same color index, `add_merge_lorentz` (l.1187) sums them into a new Lorentz with a synthesized name. MODEL-DEPENDENT — sm produces ZERO (22→22). See `ufo-vertex-to-interaction-conversion.md`.

### SPLIT (one Vertex → N Interactions)
- `add_interaction` groups a vertex's couplings by their coupling-order tuple (l.1816-1860); each distinct order signature becomes its own `base_objects.Interaction` with a fresh sequential id. This is why "interactions" (71 for sm-full) is a different unit than "vertices" (153 raw) — both drops AND splits separate the two numbers. See `ufo-vertex-to-interaction-conversion.md`.

## Why this matters as a synthesis
No single deep-dive answers "why doesn't my loaded model match the files." The gauge page sees only particle drops; the vertex page only vertex transforms; the expression page only the param additions. A reader asking any of —
- "particle/vertex/param count differs from the `.py` files" → which direction, which stage?
- "where did `conjg__CKM1x1` / `MZ__exp__2` come from, it's not in parameters.py?" → ADD, Stage-2 shortening.
- "one line in vertices.py became three interactions?" → SPLIT, order-tuple loop.
- "coupling count unchanged at load but smaller after I import the restricted model?" → loader doesn't drop couplings; restriction does (out of slice).
— is routed from here to the owning mechanism, with the right stage attribution and the right slice boundary (loader vs restriction).

## Caution / boundary
- Loader-stage divergence is this slice. The FURTHER shrinkage under restriction (interactions, params, couplings all shrink again for sm) is **restriction slice**. The loader-stage column above is the clean loader-stage cut; use it, not the restricted column, when attributing divergence to the loader.
- Counts are model-dependent AND version-dependent. Any sm integers are this-install probe data, not universal — re-probe for a different model (a model with kept Goldstones in Feynman gauge, with LMER merges, or with no restriction default, diverges differently).
