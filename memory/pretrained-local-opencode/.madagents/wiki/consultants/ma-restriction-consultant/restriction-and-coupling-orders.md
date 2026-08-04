---
description: How restriction treats coupling orders (NP/QED/QCD) — order-aware merge grouping, vertex-order survival, and the "order dropped when no coupling survives" warning chain (import_ufo.py + base_objects.py v3.7.1)
---

# Restriction × coupling orders (NP / QED / QCD)

What restriction does to coupling-ORDER labels specifically — distinct from operator selection (see smeft-restrict-operator-selection.md, which decides which operators EXIST). This page answers: do NP/QED/QCD order labels survive pruning and merging, and can an entire order disappear?

## 1. Vertex `orders` dicts are never rewritten by restriction
A UFO interaction carries `orders = {'NP':2,'QED':1}` etc. (from `couplings.py`, e.g. SMEFTatNLO `order = {'NP':2,'QED':1}`). Through the whole `RestrictModel` pipeline:
- `remove_interactions` (import_ufo.py:2876) trims/removes vertices but NEVER edits `vertex['orders']` — a trimmed (partially-pruned) vertex keeps its original order dict (see remove-interactions.md).
- `merge_iden_couplings` (2780-2816) substitutes coupling NAMES inside `vertex['couplings']` but never touches `vertex['orders']`.

So a surviving vertex's coupling-order signature is exactly what the UFO declared. The operative model's per-vertex orders = declared orders, minus whole vertices that were removed.

## 2. Coupling merging is ORDER-AWARE (the load-bearing fact)
`detect_identical_couplings` (import_ufo.py:2525) groups couplings by numeric value, then **regroups each value-group by coupling order before merging** (2579-2589):
```
ords = [self.get_coupling_order(k) for k,c in tmp]     # 2580
coup_by_ord = collections.defaultdict(list)
for o,t in zip(ords, tmp): coup_by_ord[str(o)].append(t)   # 2582-2583
for tmp3 in coup_by_ord.values():
    if len(tmp3) > 1: iden_coupling.append(tmp3)            # 2585-2589
```
`get_coupling_order(cname)` (2596-2611) returns `v['orders']` — the FULL order dict of an interaction the coupling appears in (cached at 2604). The grouping key is `str(o)` = the stringified full order dict.

Consequence: two couplings with the IDENTICAL numeric value are merged ONLY if their host interactions carry the SAME `orders` dict. A coupling at `{'NP':2,'QED':1}` and one at `{'QED':3}` with equal value are NOT merged — they land in different `coup_by_ord` buckets. **This is the safeguard that stops restriction from collapsing an NP (EFT) coupling into an SM coupling that happens to share a numeric value.** Without it, the random-fraction Wilson values in the restrict cards could accidentally equal an SM coupling and merge across orders.

### Caching subtlety (benign in SMEFTatNLO, watch elsewhere)
`get_coupling_order` caches name→orders from the LAST interaction that uses the coupling (2602-2604, dict overwrite). If one coupling appeared in two interactions with DIFFERENT order dicts, the cached order would be whichever was iterated last — making the merge grouping order-ambiguous. Probed SMEFTatNLO `vertices.py`: **zero couplings appear under more than one distinct order dict** (each GC_* has a unique order signature), so the cache is well-defined there. A model that reused a coupling across orders would expose this ambiguity.

## 3. An entire coupling ORDER can be DROPPED — the warning chain
After all pruning/merging, restriction recomputes the model's order set (import_ufo.py:2477-2489; warnings+wipe at 2482-2486, re-init at 2487-2489):
```
old_order = self['coupling_orders']
self['coupling_orders'] = None                              # invalidate cache
if old_order and old_order != self.get('coupling_orders'):
    removed = set(old_order).difference(set(self.get('coupling_orders')))
    logger.warning("Some coupling order do not have any coupling associated to them: %s", list(removed))
    logger.warning("Those coupling order will not be valid anymore for this model")
    self['order_hierarchy'] = {}
    self['expansion_order'] = None
```
`get('coupling_orders')` recomputes via `get_coupling_orders()` (base_objects.py:1374-1377) = **union of `orders.keys()` over all SURVIVING interactions**. So an order vanishes iff EVERY interaction carrying it was removed by `remove_interactions`.

The chain end-to-end: zero a Wilson coefficient → its coupling(s) → 0 → `detect_identical_couplings` flags them zero → `remove_interactions` deletes vertices carrying ONLY those couplings → if those were the only interactions bearing a given order, the order disappears from the recomputed set → the 2480 diff fires TWO warnings AND wipes `order_hierarchy={}` + `expansion_order=None`.

This is precisely how a restrict card that zeroes EVERY operator of a given NP order eliminates that order from the operative model — silently except for the two warnings, which appear at WARNING level (not the model-modification log level that hides vertex-prune lines).

### It is an order-WIPE, not a weight-decrement (framing correction)
A common mis-framing: "zeroing all WCs takes `NP : weight = 2` down to `weight = 1` in MG5's order optimiser." **This is wrong.** The vertex `orders` dicts are never edited (§1), and the model's per-order *weight* (the `order_hierarchy` value) is not decremented either — the whole order NAME is REMOVED from the recomputed `coupling_orders` set (`get_coupling_orders` is a pure set-union of surviving interactions' `orders.keys()`, base_objects.py:1374-1377, v3.7.1), and `order_hierarchy`/`expansion_order` are wiped to `{}`/`None` wholesale (import_ufo.py:2485-2486). Nothing goes "2→1"; the order simply ceases to exist in the model. `restrict_default.dat` for SMEFTatNLO is the clean demonstration — every Wilson coefficient is `0.` (only Lambda nonzero), so bare `import model SMEFTatNLO` drops NP entirely.

### Why `NP^2==N` then fails at parse (the consumer site, restriction-driven)
The generate-time rejection lives in `madgraph_interface.py` (coupling-order/process-syntax slice) but is DRIVEN by restriction having removed the order. `model_orders = self._curr_model.get('coupling_orders')` (madgraph_interface.py:4893). For a squared constraint `NP^2==N`, the parser strips the `^2` to `basename='NP'` (4926-4927) and tests `if basename not in list(model_orders) + ['WEIGHTED']` (4928); on failure it raises `InvalidCmd("model order NP^2 not valid for this model (valid one are: ...). Please correct")` at **4931**. (The non-squared `NP=N` form hits the parallel check at 4942-4944.) So the squared order `NP^2` is invalid *because the basename `NP` is absent from the post-restriction `coupling_orders`* — a direct consequence of the order-wipe, not of any weight value. The "NP^2 not valid" message is the squared-form branch (4931); same root cause as the bare-`NP` branch (4944).

## Probe confirmation (SMEFTatNLO-NLO, v3.7.1)
- `import model SMEFTatNLO-NLO` then `display coupling_order` →
  ```
   NP : weight = 1
   QCD : weight = 2
   QED : weight = 4
  ```
  All three orders survive restriction even though NLO zeroes cG/cpG/ctlS3/ctlT3/cblS3 — those operators are not the SOLE carriers of any order, so no order is dropped. No "coupling order do not have any coupling" warning fires.
- `generate u u~ > t t~ NP=2` after the NLO restriction → "Interpreting 'NP=2' as 'NP<=2'", 13 diagrams. NP-order-2 vertices survived and NP is a usable generation constraint post-restriction.

## Cautions
- **Order-drop is the real EFT hazard, not value-merge.** Within the shipped SMEFT cards no order is fully de-populated, so the 2480 warning stays dormant. But a custom restrict card (or a more aggressive operator set) that zeroes every operator of an order WILL drop the order, blank `order_hierarchy`/`expansion_order`, and then any later `generate ... NP=N` referencing the dropped order fails — the order is "not valid anymore for this model". Watch for the two WARNING lines at import.
- **`order_hierarchy` and `expansion_order` are wiped wholesale (={}/None), not just the dropped key.** A single dropped order resets the ENTIRE hierarchy, so even surviving orders lose their UFO-declared hierarchy/expansion settings. Downstream coupling-order weighting (`WEIGHTED`, base_objects.py:2643-2657) then runs against the defaulted hierarchy.
- **Merge grouping depends on the stringified full order dict**, not on a single order name. `{'NP':2,'QED':1}` and `{'NP':2,'QED':3}` are DIFFERENT buckets — same NP order, different QED, so not merged. This is finer-grained than "same NP order"; it is "same complete orders dict".
- The linear-vs-quadratic / `NP^2` interference choice is a generate-time interaction-order matter, NOT a restriction concern (restriction only decides which order-carrying vertices EXIST). See smeft-restrict-operator-selection.md line on this.
