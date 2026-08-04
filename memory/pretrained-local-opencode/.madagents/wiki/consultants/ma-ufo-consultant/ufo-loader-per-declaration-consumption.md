---
description: The loader applies one of five fixed rules to each UFO declaration type — copy-raw / transform / read-into-derived-dict / conditional-attach / never-consume(defer) — so "the loaded Model doesn't reflect UFO file/declaration X" has a different answer per declaration. Routing page over the consumption locus, distinct from count/name divergence.
---

# What the loader does with each UFO declaration — the consumption-rule taxonomy (import_ufo.py, v3.7.1)

Generalization page. The instance pages each answer ONE declaration's fate: `ufo-coupling-orders-and-propagators.md` (orders read, propagators never read), `ufo-expression-shortening-and-event-dependence.md` (params/couplings transformed), `ufo-model-file-structure.md` (functions copied raw, decays conditional). None answers the cross-cutting question a reader actually has: **"the loaded Model doesn't reflect UFO declaration X — why, and is that a bug?"** The answer depends on which of FIVE fixed consumption rules the loader applies to that declaration type. This page is the routing index over the consumption *locus/timing*; the magnitude of count/name change is `ufo-loaded-model-diverges-from-files.md`'s axis (a sibling, not a parent).

## The complete `self.model.set(...)` / `model.set(...)` map (source backbone)
Every place the loader writes a UFO-derived value onto the Model (`grep "model.set(" import_ufo.py`, loader scope):

| Line | set key | UFO source | Rule |
|---|---|---|---|
| 419 | parameters | (built by OrganizeModelExpression) | **TRANSFORM** |
| 420 | couplings | (built by OrganizeModelExpression) | **TRANSFORM** |
| 421 | functions | `ufo_model.all_functions` | **COPY-RAW** |
| 511 | particles | `self.particles` (post add_particle drops) | **TRANSFORM** (drop) |
| 512 | interactions | `self.interactions` (post add_interaction split) | **TRANSFORM** (split/drop) |
| 515-519 | startfromalpha0 | `model.startfromalpha0` if present (bool-cast via `ConfigFile.format_variable`), else False | **CONDITIONAL** (read-or-default) |
| 525 | running_elements | `all_running_elements` (only if present) | **CONDITIONAL** |
| 559 | gauge | `ufomodel.gauge` (only if present) | **CONDITIONAL** |
| 585 | lorentz | `list(all_lorentz)` (+ LMER merges) | **COPY-RAW** (modulo merge) |
| 636 | conserved_charge | `self.conservecharge` (accumulated) | **DERIVED** |
| 660 | order_hierarchy | `coupling_orders.py` hierarchy | **READ-INTO-DICT** |
| 676/677 | expansion_order | `coupling_orders.py` expansion_order | **READ-INTO-DICT** |
| 426-438 | particles[].partial_widths | `decays.py` (only if `decay=True`) | **CONDITIONAL** |

NOT in this map (the fifth rule): `all_propagators` — `grep -c all_propagators import_ufo.py` = **0**. The loader NEVER consumes it.

## The five rules

1. **COPY-RAW** — set verbatim, no transform, no dependency-classification.
   - `functions` (l.421): `model.set('functions', ufo_model.all_functions)`. NOT shortened/classified like params/couplings.
   - `lorentz` (l.585): `list(all_lorentz)`, modulo `add_merge_lorentz` (LMER) additions — model-dependent, sm adds none (see vertex page).
   - `gauge` (l.559, conditional).

2. **TRANSFORM** — the UFO value is rewritten before it lands on the Model.
   - `parameters`/`couplings` (l.419-420): built by `OrganizeModelExpression` — shortened (`complexi`/`__exp__`/`conjg__`), dependency-classified, prefixed. NEW params appear; see `ufo-expression-shortening-and-event-dependence.md`.
   - `particles`/`interactions` (l.511-512): Goldstone/ghost drop, order-tuple split. See `ufo-loader-gauge-and-pickle.md` + `ufo-vertex-to-interaction-conversion.md`.

3. **READ-INTO-DERIVED-DICT** — a declaration file is read and reshaped into Model dicts.
   - `order_hierarchy`/`expansion_order` from `coupling_orders.py` (l.660/676). Fires for TREE models too (not just loop). If the file is ABSENT, the loader sets nothing and `base_objects` LAZILY derives both from the interactions' order keys at first `.get()` — with an ASYMMETRIC guard (`not self[name]` vs `== None`). See `ufo-coupling-orders-and-propagators.md`.
   - `conserved_charge` (l.636): accumulated from particle attributes during add_particle, not a UFO file.

4. **CONDITIONAL-ATTACH** — present on the loaded Model only if a precondition holds.
   - `decays.py` (l.426-438): attached ONLY when `import_full_model(decay=True)` AND `all_decays` non-empty. A plain `import model X` carries `partial_widths={}` on every particle even if `decays.py` exists. The pickle key includes `decay`, so decay and non-decay loads use different pickles.
   - `running_elements` (l.525), `gauge` (l.559): only if the UFO defines them.
   - `startfromalpha0` (l.515-519): READ from `model.startfromalpha0` (bool-cast) if the UFO sets it, else defaulted False. NO installed model here declares it (all default False). Consumed only by NLO/FKS photon-tagging export (`export_fks.py:1169`, out of slice) — the loader just reads-or-defaults the flag.

5. **NEVER-CONSUME (defer to a later stage)** — the loader imports the file as a Python module (so its `all_*` list is populated on the ufo package) but attaches NOTHING to the MG5 Model.
   - `all_propagators` (`propagators.py`): the loader sets only the per-particle `propagator` INTEGER index (a gauge/index choice, l.1295-1326); the `Propagator` numerator/denominator OBJECTS are read by ALOHA at routine-generation time (`aloha/create_aloha.py:463-465`), not the loader. See `ufo-coupling-orders-and-propagators.md`.

## Probe (loaded sm Model, this install)
`import_ufo.import_model('sm')` then inspect the Model:
- COPY-RAW: `len(functions)==7` (the 7 sm function_library functions verbatim).
- TRANSFORM: a parameter named with `complexi` exists (shortening intermediate, in no `.py`).
- READ-INTO-DICT: `order_hierarchy=={'QCD':1,'QED':2}`, `expansion_order=={'QCD':99,'QED':99}`.
- DERIVED: `conserved_charge=={'LeptonNumber','Y','charge'}`.
- NEVER-CONSUME: Model has NO `all_propagators` (`hasattr` False).
PROBE-CONFIRMED (this install, v3.7.1).

## Routing — the question this page answers
- "my `propagators.py` is ignored / the Model has no propagator expressions" → NEVER-CONSUME, expected; ALOHA surfaces them, not the loader.
- "my `decays.py` did nothing / `partial_widths` empty" → CONDITIONAL; needs `decay=True` (a `--with_decay`-style load), else not attached.
- "model has `order_hierarchy` though I shipped no `coupling_orders.py`" → READ-INTO-DICT absent path → base_objects lazy-derive from vertices (QCD+QED auto-gets 1/2).
- "where did `complexi`/`MZ__exp__2` come from, not in `parameters.py`?" → TRANSFORM (shortening); also a count-ADD on `ufo-loaded-model-diverges-from-files.md`.
- "functions show up verbatim, untransformed" → COPY-RAW, correct.

## Boundary
- This page indexes consumption LOCUS/TIMING. The count/name divergence MAGNITUDE (particles drop, params increase — re-probe for integers) is `ufo-loaded-model-diverges-from-files.md`. They are sibling axes over the same loader, not a hierarchy.
- TRANSFORM internals live on pages 5/6; this page only names that the rule IS transform and points there.
- Restriction (further pruning/merging), ALOHA propagator-expression→Fortran, MadLoop CT consumption are all out of slice — this page stops at "what rule the LOADER applied."
