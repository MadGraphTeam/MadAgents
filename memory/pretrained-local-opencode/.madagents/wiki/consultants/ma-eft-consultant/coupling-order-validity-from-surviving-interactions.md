---
description: A coupling order is valid for a process iff a surviving interaction carries it; extract_process validates against orders-of-present-interactions, not the model's declared coupling_orders.py. Catches any order (EFT or not), any restriction.
---

# Coupling-order validity = orders carried by surviving interactions

## Principle
`extract_process` accepts an order constraint (`NAME==v`, `NAME^2<=v`, ...) only if `NAME`
is in `model_orders`. `model_orders` is **not** the model's declared `coupling_orders.py` list —
it is `get_coupling_orders()`, derived from the orders of the interactions that survived restriction.
So an order is valid iff at least one surviving interaction carries it; absence (restriction-zeroed
or never-present) removes it from validity. True for **any** order — EFT (`NP`,`DIM6`) or SM (`QED`,`QCD`).

## Source chain (v3.7.1, verified)
- `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:4893`:
  `model_orders = self._curr_model.get('coupling_orders')`.
- Rejection branches gate on `model_orders` for ANY name:
  - squared order (`NAME^2`): line 4929 — `if basename not in list(model_orders)+['WEIGHTED']: raise InvalidCmd("model order %s not valid ...")`.
  - amplitude order: line 4942 gate `if name not in model_orders and name!='WEIGHTED':` → raise at 4944.
  Both emit the identical "model order X not valid for this model (valid one are: ...)" message.
- `$MADGRAPH_INSTALL/madgraph/core/base_objects.py:1374-1377` `get_coupling_orders()`:
  `set(sum([list(i.get('orders').keys()) for i in self.get('interactions')], []))`
  — built from interactions present, after restriction stripping.

## Why `display coupling_order` can disagree with `generate`
`display coupling_order` reads the model's **declared** order objects, so it lists an order even
when no surviving interaction carries it. `generate` validates against the surviving-interaction
set. A declared-but-unvalidatable order is the diagnostic signature of this principle: the order
shows in `display` yet `generate ... NAME==v` raises "not valid".

## Cases this catches (beyond the two instances)
- **SMEFTatNLO bare** — `restrict_default.dat` zeroes every DIM6* Wilson coefficient (only Lambda,
  `DIM6` code 1, left nonzero) → no NP interaction survives → `NP` rejected. Probe-verified: bare
  `p p > t t~ NP==2` raises `model order NP not valid (valid one are: QED, QCD, EW, EW^2, aEW, aS)`;
  `SMEFTatNLO-LO` gives 7 diagrams (gg) / 10 (uu~). See smeftatnlo-default-restriction-trap.md.
- **dim6top_LO_UFO** — no restrict file → full interaction set → `DIM6` always validatable even
  though parameters.py defaults the coefficients to 0. See bundled-eft-models.md.
- **Generalizes to**: any non-EFT order whose carrying interactions are all zeroed by a restriction;
  any UFO where an order is declared but never used in a vertex; the inverse — unrestricted load
  keeps an order regardless of zero parameter defaults (zero-stripping is restriction-only behaviour).

## Boundary
This governs order *validity* (is `NAME` an accepted constraint name). It does not govern whether
diagrams survive the *value* of the constraint, nor amp_split accounting (nlo-export slice).
The restriction algorithm's zero-coupling stripping itself is restriction-slice territory; this page
only uses its observable consequence on the order set.
