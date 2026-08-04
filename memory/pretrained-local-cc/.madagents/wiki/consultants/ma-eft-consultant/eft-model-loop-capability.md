---
description: What makes an EFT UFO loop-capable (perturbative_expansion>0 → LoopModel), SMEFTatNLO's QCD-only perturbation set, the user-visible [QED]/[QCD QED] rejection gate (loop_interface.py:356), no CT_parameters.py, dim6top tree-only despite CT_couplings.py.
---

# EFT model loop-capability and the QCD-only NLO restriction (v3.7.1)

The BSM/EFT path TO NLO process generation. What lets `import model X; generate ... [QCD]` work,
why `[QED]`/`[QCD QED]` is rejected for SMEFTatNLO, and where the user-visible error actually fires.

## What makes a UFO model loop-capable: `perturbative_expansion > 0`
`$MADGRAPH_INSTALL/models/import_ufo.py:498-508`:
```
self.perturbation_couplings = {}
for order in model.all_orders:
    if(order.perturbative_expansion>0):            # line 501
        self.perturbation_couplings[order.name]=order.perturbative_expansion   # line 502
...
if self.perturbation_couplings!={}:               # line 506
    self.model = loop_base_objects.LoopModel({'perturbation_couplings':
                                        list(self.perturbation_couplings.keys())})   # line 507-508
```
- The model becomes a `LoopModel` (loop-capable AT ALL) **iff at least one coupling order declares
  `perturbative_expansion > 0`** in its `coupling_orders.py`. The set of perturbable orders =
  `{order.name : order.perturbative_expansion>0}`. `perturbative_expansion` defaults to 0
  (`object_library.py:303` `CouplingOrder.__init__(... perturbative_expansion = 0)`).
- **SMEFTatNLO** (`coupling_orders.py`): ONLY `QCD` carries `perturbative_expansion = 1` (line 16).
  `NP` (expansion_order=2, hierarchy=1) and `QED` (expansion_order=99, hierarchy=4) have NO
  perturbative_expansion → default 0. So `perturbation_couplings = {'QCD': 1}` → LoopModel with
  `perturbation_couplings = ['QCD']`. **Loop-capable for QCD ONLY.**
- **dim6top_LO_UFO** (`coupling_orders.py`): QCD/QED/DIM6/FCNC, NONE declare perturbative_expansion
  (grep count 0) → `perturbation_couplings = {}` → the model stays a plain `Model`, **NOT a LoopModel**
  → tree-only. (Its name `_LO_UFO` advertises this.)

## TRAP — CT_couplings.py present ≠ loop-capable
`dim6top_LO_UFO/` ships a `CT_couplings.py` (verified `ls`), yet the model is tree-only (no
`perturbative_expansion` anywhere → never a LoopModel). The presence of a CT_* file does NOT make a
model loop-capable; only `perturbative_expansion > 0` on some order does. The CT machinery is inert
for a model that never becomes a LoopModel. (dim6top has NO CT_vertices.py / CT_parameters.py either,
but the principle holds even if it did.)

## TRAP — SMEFTatNLO has NO CT_parameters.py; NP rides in CT-coupling order dicts
`$MADGRAPH_INSTALL/models/SMEFTatNLO/` (verified `ls`): has `CT_couplings.py` (1.0 MB) and
`CT_vertices.py` (546 KB) but **NO `CT_parameters.py`** (contrast `loop_sm/CT_parameters.py` which
DOES exist). The EFT power-counting order `NP` is carried on the **CT couplings' order dicts**, not on
any CTParameter:
- `CT_couplings.py` — entries tagged `order = {'NP':2, 'QCD':2, 'QED':1}` etc. (CT couplings carry `'NP'`;
  same +2 NP increment as tree couplings.py). See eft-nlo-specifics.md for the CT NP-order detail.
So `NP==2`/`NP^2==4` (LO) and `NP<=2`/`NP^2<=4` (NLO) truncation applies uniformly to the R2/UV
counterterm pieces via the CT-coupling order, with no CT_parameters.py needed. (R2/UV declaration
mechanics themselves = nlo-model slice.)

## `[QED]` / `[QCD QED]` rejection — the USER-VISIBLE gate is loop_interface.py:356, NOT mg_interface:5286
Two gates test "is this perturbation order allowed by the model"; the loop-interface one fires FIRST
on the live `generate ... [...]` path and shadows the deeper madgraph_interface one.

**Live path (probe-confirmed):**
- `amcatnlo_interface.py:513` `self.validate_model(proc_type[1], coupling_type=proc_type[2])` —
  `proc_type[2]` is the parsed `[...]` perturbation list (e.g. `['QED']`), `stop` defaults True.
- `loop_interface.py:297` `def validate_model(self, loop_type='virtual', coupling_type=['QCD'], stop=True)`.
- `loop_interface.py:310-313` the gate:
  `if not isinstance(self._curr_model, LoopModel) or self._curr_model['perturbation_couplings']==[]
   or any((coupl not in self._curr_model['perturbation_couplings']) for coupl in coupling_type):`
  → for `[QED]`: `'QED' not in ['QCD']` → True → enters block.
- `loop_type` is not `real`/`LOonly` → `else` at 323-326 logs "The current model SMEFTatNLO-NLO does
  not allow to generate loop corrections of type ['QED']."
- model_name is not sm/loop_sm (the SM-fallback at 329-353 that auto-loads `loop_qcd_qed_*` only fires
  for sm-family) → falls to `elif stop:` at 354 → **raises** `loop_interface.py:355-356`:
  `InvalidCmd("The model %s cannot handle loop processes" % model_name)`.

**Probe-verified (v3.7.1):** `import model SMEFTatNLO-NLO; generate p p > t t~ NP<=2 [QED]` →
`InvalidCmd : The model SMEFTatNLO-NLO cannot handle loop processes`. (Same for `[QCD QED]` —
`'QED' not in ['QCD']` still trips 312-313.)

**Deeper shadowed gate** (NOT the one users hit on this path): `madgraph_interface.py:5286-5289`
`if pert_order not in self._curr_model['perturbation_couplings']: raise InvalidCmd("Perturbation
order %s is not among the perturbation orders allowed for by the loop model.")`. This message exists
but the aMC@NLO `validate_model` gate at loop_interface.py:354-356 fires earlier for a real bracket,
so the user sees "cannot handle loop processes", NOT "not among the perturbation orders". Quote
loop_interface.py:356 as the user-visible message; mg_interface:5286 is the deeper/dead-on-this-path guard.

**Contrast `[QCD]` (works, probe-verified):** `SMEFTatNLO-NLO; generate p p > t t~ NP<=2 [QCD]` →
11 born FKS processes `g g > t t~ NP<=2 QCD<=100 QED<=99 NP^2=4 QCD^2=200 QED^2=198 (1/11)` etc.
`'QCD' in ['QCD']` → gate passes.

## Why this is the QCD-only-at-NLO restriction
"SMEFTatNLO is loop-capable for QCD only" is exactly `perturbation_couplings == ['QCD']` (the only
order with perturbative_expansion>0). QCD corrections to SMEFT operators have R2/UV CTs declared
(CT_couplings/CT_vertices with NP order); QED/EW corrections do not (no perturbative_expansion on QED,
no QED CT structure) → `[QED]`/`[QCD QED]` is rejected at the validate_model gate. This is a model-
content fact (which orders the UFO declares perturbable), not an MG5 limitation per se — a different
SMEFT UFO declaring `perturbative_expansion=1` on QED would lift it.

## Boundary
- FKS/MadLoop/R2-UV mechanics of the QCD loop itself = nlo-model / madloop / fks slices.
- The Switcher/interface-switch that routes a `[...]` process to aMC@NLO = nlo-syntax slice.
- WHETHER QCD-only NLO suffices for the user's physics (vs wanting EW corrections) = ma-physics.
- This page owns: the loop-capability CRITERION (perturbative_expansion>0), the EFT-model
  perturbation-order SET, and the user-visible EFT-bracket rejection path.
