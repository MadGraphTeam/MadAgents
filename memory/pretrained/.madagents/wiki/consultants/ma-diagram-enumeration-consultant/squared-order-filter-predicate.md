---
description: Squared-order post-filter predicate-level mechanics — pass_squared_order_constraints per-pair keep/drop, positive/negative drivers, negative-target arithmetic, filter_constrained_orders, check_expansion_orders ceiling (base_objects.py)
---

# Squared-order filter — the predicate level (base_objects.py)

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` and `.../base_objects.py` (v3.7.1).

`generate-diagrams-algorithm.md` describes the ORCHESTRATION of `apply_squared_order_constraints` (diagram_generation.py:856) — it cites the helpers by name only. This page walks the actual keep/drop DECISION, which lives on `DiagramList`/`Diagram` in `base_objects.py`. The squared-order filter is a post-generation diagram filter inside `generate_diagrams` (my slice: the recursion's post-filters); the squared-order *syntax/policy* (`QED^2<=N`, `==`, what users mean) is the coupling-orders slice — boundary noted at the end.

## The central fact: squared orders are a property of diagram PAIRS, not single diagrams
`apply_positive_sq_orders` (base_objects.py:2882) is a DOUBLE loop: for each `tested_diag` in `self`, for each `ref_diag` in `ref_diag_list`, keep `tested_diag` the moment it passes against ANY ref (`break` :2894). The amplitude is squared with itself, so `self` and `ref_diag_list` are the same list (called as `res.apply_positive_sq_orders(res, ...)` at diagram_generation.py:871). A diagram survives if AT LEAST ONE interference term (itself × some ref diagram) satisfies the constraint. This is why a squared order is fundamentally a statement about |M|², not about individual diagrams.

## The predicate: pass_squared_order_constraints (base_objects.py:2659)
Per (tested_diag, diag_multiplier) pair, for each `(order, value)` in `squared_orders`:
- `value < 0` → `continue` (negative handled separately, see below) (:2668-2669).
- `combined_order = self.get_order(order) + diag_multiplier.get_order(order)` (:2670-2671) — the coupling power of the INTERFERENCE term (sum of the two diagrams' orders for that coupling).
- Reject (return False) if any of (:2672-2674):
  - type `'=='` and `combined_order != value`
  - type in `['=', '<=']` and `combined_order > value`
  - type `'>'` and `combined_order <= value`
- Pass only if no order rejects (:2676).
`get_order` (:2678) returns `self['orders'][order]` or 0 if absent — a coupling not appearing in a diagram counts as order 0.

`Diagram.calculate_orders` (base_objects.py:2638) is what populated `self['orders']`: sums each vertex interaction's `orders` (loop vertices id==-2 use `loop_orders`; id in [0,-1] skipped), and sets the special `'WEIGHTED'` = Σ `order_hierarchy[c]*n` (:2654-2656). Called per diagram at diagram_generation.py:797 before the squared-order filter runs.

## Driver: apply_squared_order_constraints (diagram_generation.py:856) — three stages
1. **constrained_orders** (`==`/`>` forms, the `constrained_orders` dict e.g. `{QED:(4,'>')}`) applied FIRST via `filter_constrained_orders` (:864-865), once, no iteration needed.
2. **positive squared_orders** in a `while True` loop (:870-881): re-run `apply_positive_sq_orders` until `len(res)` stops shrinking. Iterated because filtering one coupling's `==` constraint changes which interference partners exist for another coupling. A count INCREASE → `MadGraph5Error('Inconsistency in function apply_squared_order_constraints().')` (:877-879) — can never legitimately grow.
3. **negative squared_orders** (at most one) via `apply_negative_sq_order` (:885-900); see arithmetic below. `>1` negative → `InvalidCmd('At most one negative squared order constraint can be specified, not %s.')` (:898-900).

## filter_constrained_orders (base_objects.py:2897) — single-diagram, MUTATING
Distinct from the squared path: operates on each diagram's OWN `['orders'][order]` (not a pair), keeps if `== value` or `> value` per operator, and assigns `self[:] = new` IN PLACE (:2909). Only `'=='` and `'>'` operators handled — these are the `constrained_orders` forms (amplitude-level `QED==N` / `QED>N`), not squared.

## Negative-target arithmetic: apply_negative_sq_order (base_objects.py:2863)
A negative squared-order constraint (e.g. `QED^2<=-2`, "up to NLO in QED") is resolved to a positive target then applied as positive:
```
target_order = min(ref_diag_list.get_order_values(order))
             + min(self.get_order_values(order))
             + 2*(-value - 1)                                  (:2874-2875)
```
`get_order_values` (:2926) = set of distinct order values across the list (absent → 0). So target = (lowest order in ref) + (lowest order in self) + 2*(|value|-1). For `u u~ > d d~ QED^2<=-2`: the list contains a pure-QCD diagram (QED=0), so the lowest QED order value is 0 in both `self` and `ref` → target = 0+0+2*(2-1) = **2** → keeps interference terms up to combined QED=2 (NLO). It then calls `apply_positive_sq_orders` with `{order: target_order}` (:2877-2878) and returns `(new_list, target_order)`. **Probe-confirmed (v3.7.1, `u u~ > d d~ QED^2<=-2`): `process['squared_orders']` resolves to `{'QED': 2}` (the kept-diagram count is readable via `display diagrams` — drift-prone, not cached here).** WATCH: the source docstring (`base_objects.py:2870`) claims `target_order=4` for this same example — that is the source docstring being WRONG/self-inconsistent (it ignores the pure-QCD QED=0 minimum); the operative resolved value is 2, not 4. Don't transcribe the docstring's 4.

**Side effect (already noted in generate-diagrams-algorithm.md, restated for the predicate context):** the driver writes `self['process']['squared_orders'][neg_order] = target_order` (diagram_generation.py:897) — after generation the process carries the RESOLVED POSITIVE value, never the user's negative. Downstream/output read the positive.

## check_expansion_orders (base_objects.py:3757) — the MODEL ceiling, separate filter
Called in `generate_multi_amplitudes` at diagram_generation.py:1688 (and inside the order search at :2089), BEFORE diagrams are generated — it clamps the process's `orders`, it does not drop diagrams. Mechanics:
- `expansion_orders = model.get('expansion_order')` (:3762).
- Acts only on entries with `0 < v < 99` (:3766). For each such `(k, v)`:
  - if `k in orders` and `v < orders[k]` (user asked for more than the model allows): set `orders[k] = v` (:3783) and warn. Two warning variants — one if `k` has a squared-order with `sq_orders[k]>v or sq_orders[k]<0` ("...can potentially receive contributions with powers... larger than the maximal value... sets the amplitude order to this maximal one") (:3772-3777), else the plain "The coupling order (%s=%s) specified is larger than the one allowed by the model builder..." (:3779-3782).
  - if `k not in orders`: just set `orders[k] = v` (:3785).

### Non-obvious default: the ceiling is a NO-OP for ordinary models
`Model.expansion_order` defaults (base_objects.py:1231-1234, lazy-filled on first `get` when interactions exist) to `dict([(order, -1) for order in coupling_orders])` — i.e. `-1` for EVERY coupling. Since `check_expansion_orders` only fires on `0 < v < 99` (:3766), a `-1` default is skipped entirely. **The expansion-order clamp only bites when a model file (UFO / restriction) explicitly sets a finite positive `expansion_order` for a coupling** (e.g. some EFT/BSM models cap a coupling's max power). For the default SM and most models it does nothing. Do not assume the clamp ran.

## Cautions
- The squared-order filter survival test is "passes against ANY ref diagram" (`break` on first pass, :2894) — a diagram is NOT required to satisfy the constraint against every interference partner, only one. A diagram kept by this filter can still have individual interference terms that violate the squared order; they are simply not what the constraint tests.
- WEIGHTED enters `pass_squared_order_constraints` like any other order if a `WEIGHTED^2` constraint is set; `calculate_orders` always populates it (:2656). Don't assume only named couplings can be squared-constrained.
- `check_expansion_orders` MUTATES `process['orders']` in place and only WARNS — a user who over-specifies a coupling order silently gets the model's ceiling instead, with the requested diagrams above the ceiling never generated. The warning is the only signal.
- The squared-order filter is SKIPPED on the loop/returndiag path (`not returndiag` guard at diagram_generation.py:807) — see generate-diagrams-algorithm.md. The predicate here only runs for tree amplitudes; NLO interference spans diagrams beyond this single amplitude's list.

## Boundary (out of this slice)
- What the squared-order/coupling-order SYNTAX means and how the parser builds `squared_orders`/`constrained_orders`/`sqorders_types` from `QED^2<=N` etc. → coupling-orders / diagram-filter (stage-2) slices. I own the predicate mechanics (how a diagram is kept/dropped given the parsed constraint dicts), not the parsing or the physics policy of choosing the constraint.
- Loop/NLO squared-order handling (interference across the full set, FKS) → madloop slice.
