---
description: split_orders assembly (perturbation couplings + squared-order keys), WEIGHTED auto-detection and the order_hierarchy sort, and the loop-optimized-output caveat.
---

# `split_orders` and `WEIGHTED` in `extract_process`

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`.

## split_orders composition (`5259-5273`)
```python
perturbation_couplings_list = perturbation_couplings.split()  # from [...] brackets
split_orders = misc.make_unique(perturbation_couplings_list + list(squared_orders.keys()))
split_orders.sort(key=lambda elem: 0 if elem=='WEIGHTED' else
                       self._curr_model.get('order_hierarchy')
                       [elem if not elem.endswith('.sqrt') else elem[:-5]])
```
- `split_orders` = union of the perturbation orders (the `[QCD]`/`[QED]`
  bracket contents — owned by nlo-syntax slice) AND every key in
  `squared_orders`. These are the orders needing separate matrix-element
  evaluations (NLO `amp_split` machinery — nlo-export slice consumes this).
- Sort key: `WEIGHTED` sorts first (key 0); everything else sorts by the
  model's `order_hierarchy[order]`. A `.sqrt` suffix is stripped before lookup.
- KeyError on the hierarchy lookup -> `InvalidCmd` naming the couplings the
  model has no hierarchy for (`5269-5273`). i.e. a squared order on a coupling
  the model doesn't rank cannot be split.

## tree-syntax-only split_orders (`5278-5279`)
`[tree= Orders]` sets split_orders but then empties
`perturbation_couplings_list` (the brackets were only used to declare split
orders, not to request loops).

## loop-optimized-output caveat (`5290-5296`)
If `loop_optimized_output` is False AND LoopOption is a real loop mode AND
`split_orders != []`: warns that default MadLoop output cannot provide
per-coupling-order evaluations, and **silently sets `split_orders = []`**.
CAUTION: squared-order splitting is dropped without error in non-optimized
loop output.

## WEIGHTED — what this slice owns vs. the boundary
This slice owns: `WEIGHTED` as a constraint NAME accepted by the parser.
- `WEIGHTED` is whitelisted alongside `model_orders` in both the squared-order
  basename check (`4929`) and the amplitude-order name check (`4942`), so
  `WEIGHTED=N` and `WEIGHTED^2=N` parse.
- `WEIGHTED` sorts first in split_orders (`5266`).

BOUNDARY (model side, NOT this slice): the *value* of WEIGHTED per interaction
is computed in `$MADGRAPH_INSTALL/madgraph/core/base_objects.py`:
- `Interaction.get_WEIGHTED_order(model)` (`893-899`): NOT a bare sum. It is
  ```python
  float(sum(order_hierarchy[key]*orders[key] for key in orders))
        / max(len(particles)-2, 1)
  ```
  i.e. the hierarchy-weighted coupling sum NORMALIZED to an "equivalent
  3-particle vertex" by dividing by `max(n_particles-2, 1)`. The docstring notes
  it "can be fractional" — the return is `float`, not int.
- `Model.get_max_WEIGHTED()` (`1481-1485`): `max(inter.get_WEIGHTED_order(self)
  for inter in interactions)`.
- `order_hierarchy` default: `get_order_hierarchy` (`1379-1386`) gives every
  order weight 1, EXCEPT when the order set is EXACTLY `{QCD, QED}`, in which
  case `hierarchy['QED'] = 2` (`1384-1385`). This QED=2 weight is what makes a
  QED vertex "cost" twice a QCD vertex in the WEIGHTED ordering — and it feeds
  the `split_orders` sort key above (`5266-5268`).
- `Model.get_minimum_WEIGHTED()` (`3910`): the auto-detection starting guess for
  the WEIGHTED bound (combines leg + 2*s-channel WEIGHTED orders).
The auto-detection of the dominant WEIGHTED bound from the process's
interactions is model/diagram territory; route WEIGHTED-value questions there.

## WEIGHTED auto-detection BYPASS — the `QED=99` idiom (SEAM to diagram-enum)
The WEIGHTED auto-scan lives in `diagram_generation.py`
(`find_optimal_process_orders`, docstring `1929-1962`). Its first guard
(`1971-1975`):
```python
# If there are already couplings defined, return
if process_definition.get('orders') or \
        process_definition.get('overall_orders') or \
        process_definition.get('NLO_mode')=='virt':
    return process_definition.get('orders')
```
So if `orders` (the dict THIS slice fills) is non-empty for ANY coupling, the
whole increasing-WEIGHTED scan (`while max_order_now < max_WEIGHTED_order`,
`2013`) is SKIPPED and the user's orders are used verbatim. Console
confirms: `"Please specify coupling orders to bypass this step."` (`1983`).
- This is the mechanism behind the `QED=99` idiom: a single loose explicit
  order (`QED=99` -> `orders['QED']=99`, a cap so high it drops nothing) makes
  `orders` truthy, disabling the auto WEIGHTED threshold that would otherwise
  scan up from the minimal bound and can silently drop wanted higher-order
  diagrams. Any explicit order does this; `QED=99` is the conventional
  "don't-actually-constrain-me" choice.
- BOUNDARY: my slice OWNS filling `orders`; the bypass guard + the auto-scan
  are diagram-enumeration's. I describe the seam, not the scan internals.
- CAUTION — `QED=99` does NOT defeat an `expansion_order` model cap. See
  `effective-vertex-and-plugin-orders.md`: `check_expansion_orders`
  (`base_objects.py:3766-3785`) re-caps `orders[k]` to the model's
  `expansion_order[k]` when `0 < v < 99`, AFTER parsing. `QED=99` only bypasses
  the WEIGHTED heuristic, not the model-builder's per-order ceiling.
- Side effect: making `orders` non-empty also arms `default_unset_couplings`
  (see `default-unset-couplings.md`) when that option != 99.

## The WEIGHTED-scan-vs-explicit-order RULES (derive counts per process)
Read the sm hierarchy fresh — sm `coupling_orders.py` declares `QCD`/`QED`
hierarchies (both `expansion_order=99`); the fallback `get_order_hierarchy`
(base_objects.py:1379-1386) gives the SAME for the exact `{QCD,QED}` set
(QED-weighted-heavier special case). WEIGHTED = Σ hierarchy·order.

The auto-scan (`find_optimal_process_orders`) sets
`orders={'WEIGHTED': max_order_now}` and generates, scanning `max_order_now` UP
from `get_minimum_WEIGHTED` (diagram_generation.py:2013+) and STOPPING at the
FIRST value that yields diagrams — the ceiling = "lowest WEIGHTED giving
non-zero", never higher. Console: `Trying coupling order WEIGHTED<=N`.

Two version-stable RULES (the diagram counts they produce are PER-process — read
the process's order combinations off its topology, never reuse a cached integer):

- **RULE A — explicit order REPLACES the scan, it is not a no-op.** ANY explicit
  order makes `orders` truthy → the guard (1971-1975) returns BEFORE the
  increasing-WEIGHTED scan → the user's orders are used verbatim, the auto ceiling
  is gone. So `QED=99` ≠ "leave the default ceiling in place"; it can ADMIT
  diagrams the auto-scan would have dropped. Whether the count changes depends
  entirely on whether dropped-by-WEIGHTED diagrams exist for THIS process.
- **RULE B — the WEIGHTED drop only bites when a higher-WEIGHTED order
  combination coexists with a lower one.** Because the scan stops at the
  MINIMUM WEIGHTED giving nonzero, a final state with a SINGLE order-combination
  loses nothing to the ceiling → bypass and no-bypass give the identical count.
  The drop is real only when a cheaper combination shadows a more expensive one.

Example for ONE topology (sm, parse-time, derive per process for anything else):
`p p > t t~` — the QCD tree (WEIGHTED=2) shadows the EW q q~→Z/γ→t t~ piece
(QED=2 → WEIGHTED=4), so the default scan drops the EW diagrams while any explicit
order (`QED=99` / `QED=2 QCD=2` / `WEIGHTED<=99`) admits them → the two counts
DIFFER (RULE A + B both bite). Contrast a single-combination final state (e.g.
`p p > mu+ mu- a`, every diagram QED=3 QCD=0): the ceiling clips nothing, bypass
vs default give the SAME count (RULE B no-op). Both counts are for these
topologies only — derive fresh elsewhere.
