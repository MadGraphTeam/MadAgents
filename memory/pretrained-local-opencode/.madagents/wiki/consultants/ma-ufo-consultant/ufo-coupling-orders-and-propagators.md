---
description: How import_ufo reads coupling_orders.py (the CouplingOrder object = name/expansion_order/hierarchy/perturbative_expansion; order_hierarchy/expansion_order onto the Model, set for tree models too) with base_objects fallback when absent; the tree-vs-loop object_library ASYMMETRY (sm's CouplingOrder.__init__ accepts but never STORES perturbative_expansion -> the loader's except-AttributeError is load-bearing); the Vertex->Coupling.order chain; and the fact that propagators.py / all_propagators is NEVER consumed by the loader — ALOHA reads Propagator objects, the loader only sets the per-particle propagator integer index.
---

# UFO coupling_orders + propagators: what the loader reads (and doesn't) (v3.7.1)

Refs in `$MADGRAPH_INSTALL/models/import_ufo.py` and `madgraph/core/base_objects.py` unless noted. Complements `ufo-model-file-structure.md` (which declares the `CouplingOrder`/`Propagator` classes) by walking what the LOADER does with them.

## coupling_orders.py — what gets read onto the Model (l.638-677)

`coupling_orders.py` declares `CouplingOrder(name, expansion_order, hierarchy, perturbative_expansion=0)` instances into `all_orders`. sm's (`models/sm/coupling_orders.py`): `QCD(expansion_order=99, hierarchy=1)`, `QED(expansion_order=99, hierarchy=2)` — no `perturbative_expansion` (defaults 0).

`UFOMG5Converter.load_model` reads them in a `try/except AttributeError/else` block (l.638-677):
- `all_orders = self.ufomodel.all_orders` (l.643); if the attribute is missing AND `self.perturbation_couplings` is non-empty -> `MadGraph5Error`; else `pass` (tree model with no orders file is fine).
- Builds `hierarchy[order.name] = order.hierarchy` and, in the `else` clause, `self.model.set('order_hierarchy', hierarchy)` (l.660).
- Builds `expansion_order[order.name] = order.expansion_order` (also `coupling_order_counterterms`), and `self.model.set('expansion_order', expansion_order)` (l.676 — **written twice**, l.676-677, a harmless source duplicate).

**Non-obvious #1 — this fires for TREE models too.** The `else` clause runs whenever NO `AttributeError` was raised, not only for loop models. sm is a tree model with a `coupling_orders.py`, so the loader DOES set `order_hierarchy`/`expansion_order` from the UFO. The `MadGraph5Error` only fires when `perturbation_couplings != {}` AND an order lacks the attribute. PROBE-CONFIRMED (`import_ufo.import_model('sm')`): loaded sm Model carries `order_hierarchy = {'QCD':1,'QED':2}`, `expansion_order = {'QCD':99,'QED':99}`, `coupling_orders = {'QED','QCD'}`.

**`expansion_order = 99` semantics**: 99 is the UFO's "no per-process cap" sentinel (effectively unbounded coupling order). The Model uses `expansion_order` as the max coupling order per process (`base_objects.py:3757 check_expansion_orders`). Per-process constraints set via the parser are coupling-order slice; the loader's job is only to load the model-wide caps.

## The CouplingOrder object itself (object_library.py) — and the tree/loop ASYMMETRY

A `CouplingOrder` is declared in `coupling_orders.py` as `CouplingOrder(name, expansion_order, hierarchy, perturbative_expansion=0)` and self-appends to the module-global `all_orders` list (sm `object_library.py:234-243`). sm's `coupling_orders.py` (full file): only `QCD(expansion_order=99, hierarchy=1)` and `QED(expansion_order=99, hierarchy=2)` — no `perturbative_expansion` argument given.

**Non-obvious #0 — the sm `CouplingOrder.__init__` ACCEPTS `perturbative_expansion` but NEVER STORES it.** sm `object_library.py:236-243`: the `__init__` signature has the `perturbative_expansion=0` default, but the body only sets `self.name`, `self.expansion_order`, `self.hierarchy` — there is NO `self.perturbative_expansion = perturbative_expansion` line. Loop-capable model object_libraries DO add that line: `SMEFTatNLO/object_library.py:301` and `loop_sm/object_library.py` both end the `__init__` with `self.perturbative_expansion = perturbative_expansion`. So the attribute's existence on an order instance is itself a tree-vs-loop fingerprint, decided by which object_library the model ships. PROBE-CONFIRMED (`models/sm`): `hasattr(QCD,'perturbative_expansion') == False`, `hasattr(QED,'perturbative_expansion') == False`.

This is WHY the loader wraps the perturbative scan in `try/except AttributeError: pass` (below): for a tree model the very first `order.perturbative_expansion` access raises `AttributeError` (the attr is genuinely absent, not just 0), the loop is abandoned, and the model loads as a plain `Model`. The except is load-bearing — without it, importing sm would crash on a missing attribute. A would-be `perturbative_expansion=N` passed to sm's CouplingOrder would be silently swallowed (accepted by the signature, dropped by the body) — so you cannot turn sm into a loop model just by editing `coupling_orders.py`; the object_library must also store the attr.

Coupling/Vertex order chain (explore-phase anchor): a `Vertex` carries `couplings = {(color_i, lorentz_i): C.GC_n}` and references `Coupling` objects, NOT orders directly (sm `vertices.py`, e.g. `V_1 ... couplings = {(0,0):C.GC_33}`). Each `Coupling(name, value, order)` carries its own `order` dict, e.g. sm `couplings.py:13 GC_1 ... order = {'QED':1}`, `GC_5 ... order = {'QED':2}`. So a vertex's coupling-order weight is transitive through its couplings; the loader collects `coupling.order` into the interaction's `orders` (l.1854) — see `ufo-vertex-to-interaction-conversion.md` for the order-tuple split.

## perturbation_couplings detection (l.498-508, mirrored l.2063-2065)

BEFORE the orders are read, the converter scans `model.all_orders` for any `order.perturbative_expansion > 0` -> `self.perturbation_couplings[name] = perturbative_expansion` (l.500-502). If non-empty, the Model object built is a `loop_base_objects.LoopModel` (l.506-507); else a plain `base_objects.Model` (l.509). So `perturbative_expansion > 0` on ANY order is what flips the model into loop mode at load — and what makes the missing-`all_orders` / missing-`hierarchy` / missing-`expansion_order` checks fatal instead of skipped. The `except AttributeError: pass` (l.503-504) is precisely the tree-model escape hatch described in #0 — a tree object_library never stores `perturbative_expansion`, so the scan aborts harmlessly on the first order.

## base_objects fallback when the UFO doesn't set them (lazy getters)

If the loader left `order_hierarchy` / `expansion_order` unset (no `coupling_orders.py`, so `all_orders=[]` and the dicts stay empty), `Model.get()` lazily derives them (`base_objects.py:1223-1234`):
- `coupling_orders`: guard `== None` -> `get_coupling_orders()` (l.1374) = the union of every interaction's `orders` keys. So even with no orders file, the model knows its order NAMES from the vertices.
- `order_hierarchy`: guard **`not self[name]`** -> `get_order_hierarchy()` (l.1379): every order weight 1, EXCEPT the special case `set(coupling_orders)==set(['QCD','QED'])` sets `QED:2` (l.1384). So a bare QCD+QED model auto-gets the standard 1/2 hierarchy with no orders file.
- `expansion_order`: guard **`== None`** -> `dict([(order, -1) for order in coupling_orders])` (l.1233-1234) — `-1` is the "uncapped" default (distinct from the UFO's `99`).

**Non-obvious #2 — the two guards differ (a real desync hazard).** `order_hierarchy` re-derives when its value is *falsy* (empty `{}` triggers it); `expansion_order` re-derives only when *exactly None* (empty `{}` does NOT trigger it). If the loader sets BOTH to empty `{}` (e.g. `all_orders=[]` for some path that still entered the `else`), `order_hierarchy` auto-fills from interactions but `expansion_order` stays `{}` forever. These two attributes can therefore disagree on which orders they cover. [static code-path fact; the empty-`{}`-set path is loader-dependent — re-walk for a specific no-orders model before asserting the desync occurs at runtime.]

## WEIGHTED and the hierarchy's downstream use (boundary)

`order_hierarchy` feeds the `WEIGHTED` pseudo-order: `base_objects.py:2654-2656` computes `weight += sum(order_hierarchy[c]*n)` over each vertex's orders, stored as `orders['WEIGHTED']` (l.2656). This is how a process's WEIGHTED cap maps to physical coupling powers. The WEIGHTED computation and per-process `expansion_order` enforcement are process / coupling-order slice; the loader only supplies the `order_hierarchy` and `expansion_order` dicts they read.

## propagators.py — declared, but the LOADER never consumes it

`propagators.py` declares `Propagator(name, numerator, denominator)` (string DSL) into `all_propagators`. The ONLY shipped-core model carrying it is `taudecay_UFO` (`models/taudecay_UFO/propagators.py`: scalar `S` :13, fermion `F` :19, massive vectors `V1` :25 / `V2` :31 — re-resolve lines per build; other models declaring propagators are oscillating and may be absent). Most models (sm, loop_sm) have NO `propagators.py`.

**Non-obvious #3 — `import_ufo.py` NEVER reads `all_propagators`.** `grep -c all_propagators import_ufo.py` = **0**. `propagators.py` is in the optional-files list (l.340) and gets imported as a module (so `all_propagators` is populated on the ufo model package), but the loader attaches NOTHING from it to the MG5 Model. PROBE-CONFIRMED: loaded sm Model has no `all_propagators` attribute.

What the loader DOES do with the word "propagator" (l.1295-1326) is set the per-particle `propagator` attribute to an **integer index** (0/1), NOT a `Propagator` object:
- If the UFO particle's `propagator` attr is a list/dict: `aloha.unitary_gauge` truthiness picks `value[0]` (unitary/axial/FD) vs `value[1]` (Feynman), stored as `str(value[...])` (l.1297-1300). See `ufo-loader-gauge-and-pickle.md` for the gauge-pick detail.
- Default (no `propagator` attr): spin>=3 massless gets `propagator=0`; spin==3 in Feynman gauge gets `propagator=0` (l.1320-1326).

The `Propagator` OBJECTS (the numerator/denominator expressions) are consumed by **ALOHA**, not the loader: `aloha/create_aloha.py:463-465` does `getattr(self.model.propagators, propa); numerator = propagator.numerator; denominator = propagator.denominator`. The per-particle integer index the loader set is the KEY into that propagator table (plus ALOHA's built-in special propagators `'1L'/'1T'/'1A'/'1S'` for spin-projection cases, l.466+). So: the loader picks WHICH propagator (an index/gauge choice); ALOHA's create_aloha resolves the index to the actual numerator/denominator expression. The propagator-expression -> Fortran wavefunction-routine generation is ALOHA slice, not mine.

## Caution
- **Editing only `coupling_orders.py` to add `perturbative_expansion=N` does NOT make a tree model loop-capable** if the model's `object_library.py` `CouplingOrder.__init__` lacks the `self.perturbative_expansion = ...` store line (the sm/tree-model case). The value is accepted by the signature and silently dropped; the loader's scan then aborts on `AttributeError` and builds a plain `Model`. Both files (orders declaration AND object_library) must carry it. (Loop-capable models — SMEFTatNLO, loop_sm — ship the storing object_library already.)
- "My model has a propagators.py but the loaded Model ignores it" is EXPECTED at the loader stage — propagators surface only through ALOHA at aloha-routine-generation time. A loader-level inspection of the Model will never show propagator expressions.
- Don't conflate the per-particle `propagator` integer (a gauge/index choice the loader sets) with the `Propagator` named objects (numerator/denominator strings ALOHA reads). They're different things sharing the word.
- `expansion_order = 99` (UFO sentinel) vs `-1` (base_objects fallback default) both mean "uncapped" but are different literals — don't read a `99` as a real per-process cap of 99.
