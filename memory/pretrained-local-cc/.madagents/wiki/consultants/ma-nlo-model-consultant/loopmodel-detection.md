---
description: How the UFO importer detects a loop-capable model and instantiates LoopModel via perturbative_expansion on coupling orders.
---

# LoopModel detection in the UFO importer

The trigger for loop capability is `perturbative_expansion` on a coupling order, NOT the
presence of CT files. (v3.7.1, `$MADGRAPH_INSTALL`.)

## Detection mechanism
`$MADGRAPH_INSTALL/models/import_ufo.py:498-510`:
```python
self.perturbation_couplings = {}
try:
    for order in model.all_orders:
        if(order.perturbative_expansion>0):
            self.perturbation_couplings[order.name]=order.perturbative_expansion
except AttributeError as error:
    pass
if self.perturbation_couplings!={}:
    self.model = loop_base_objects.LoopModel({'perturbation_couplings': list(...keys())})
else:
    self.model = base_objects.Model()
```
- Scans `coupling_orders.py` (`all_orders`). Any order with `perturbative_expansion>0`
  → that order name goes into `perturbation_couplings`.
- If the dict is non-empty → a `LoopModel` is built; else a plain `base_objects.Model`.
- A model lacking `perturbative_expansion` (AttributeError) silently falls back to tree-level Model — CT files alone do not make a loop model.

## loop_sm coupling_orders.py
`$MADGRAPH_INSTALL/models/loop_sm/coupling_orders.py`:
- `QCD`: `perturbative_expansion = 1`  → QCD is the perturbed order.
- `QED`: `perturbative_expansion = 0`  → not perturbed (NLO QCD only for loop_sm).
So loop_sm's `perturbation_couplings == ['QCD']`.

## LoopModel class
`$MADGRAPH_INSTALL/madgraph/loop/loop_base_objects.py:1415` `class LoopModel(base_objects.Model)`:
- `default_setup` adds `self['perturbation_couplings'] = []` (1433) and
  `self['coupling_orders_counterterms'] = {}` (1442).
- Non-dict attribute `self.map_CTcoup_CTparam = {}` (1448-1449): maps coupling name →
  list of CTParameter names entering its expression (filled in `treat_couplings`,
  import_ufo.py:1535).
- `get_sorted_keys` (1480) adds `'perturbation_couplings'` to the model keys.
- `change_electroweak_mode` (1486): would block EW-scheme change for models with
  'QED'/'EW' in perturbation_couplings — but is bypassed (`bypass_check=True` hardcoded).

## CouplingOrder UFO class
`$MADGRAPH_INSTALL/models/loop_sm/object_library.py:301-311` `class CouplingOrder`:
ctor `(name, expansion_order, hierarchy, perturbative_expansion=0)` — default 0,
so a tree model's orders are non-perturbed unless explicitly set.

## Caution
- Card pointer drift: the QED/EW perturbation *detection* is NOT inside LoopModel; it
  is in import_ufo.py:500-502. LoopModel only stores the result.
