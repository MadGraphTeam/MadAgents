---
description: How extract_process parses EFT power-counting order constraints (NP/DIM6 etc.); amplitude vs squared orders, the == auto-squared-order rule, = reinterpretation, and EW/aEW aliasing.
---

# EFT power-counting order parsing in extract_process

All in `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `extract_process` (def at line 4822).

## Order regex + valid operator types
- Regex `order_pattern` (def line 4883) matches `<name><type><value>`, where `name` may end in `^2`,
  `type` ∈ `(=|<=|==|===|!=|>=|<|>)`, value `-?\d+`.
- `_valid_amp_so_types = ['=','<=','==','>']` (line 3037) — amplitude-level constraints.
- `_valid_sqso_types  = ['==','<=','=','>']` (line 3036) — squared-order constraints (name ends in `^2`).
- Order name not in `model_orders` → `InvalidCmd: model order <X> not valid` (lines 4929-4931, 4942-4944).
  `model_orders = self._curr_model.get('coupling_orders')` (line 4893). Validity is gated against
  surviving interactions, not declared orders — see coupling-order-validity-from-surviving-interactions.md
  and smeftatnlo-default-restriction-trap.md.

## Amplitude-level `==` auto-generates a squared order (KEY)
For `NP==value` (amplitude, name has no `^2`), lines 4955-4960:
- adds `constrained_orders[NP] = (value,'==')`,
- if not `avoid_squared_orders` and NP not already in squared_orders: **`squared_orders[NP] = (2*value,'==')`**,
- and sets `orders[NP] = value`.
So `NP==2` ⟹ both an amplitude `NP==2` and an auto squared `NP^2==4` constraint. (Verified by probe: `SMEFTatNLO-LO`, `p p > t t~ NP==2` generates diagrams.)
`>` behaves analogously (lines 4962-4965): `squared_orders[name]=(2*value,'>')`.

## `=` is reinterpreted (warns)
- Amplitude `NAME=value` with value!=0 → warns "Interpreting NAME=value as NAME<=value", stored in `orders` (lines 4950-4954).
- Squared `NAME^2=value` → warns, treated as `<=` (lines 4936-4939).
So `NP=2` is NOT "exactly one insertion squared"; it is a `<=` bound on the amplitude order.

## EW / aEW / aS aliasing (lines 4892-4907)
If model has `EW` but not `QED`: `QED`→`EW`, `aEW`→`EW^2=2*` (value doubled). If model has `QED` not `EW`:
`EW`→`QED`, `aEW`→`QED^2=2*`, `aS`→`QCD^2=2*`. The `=2*` suffix doubles the value (line 4922-4924).
EFT models commonly carry QED (SMEFTatNLO does) — so `EW` maps to `QED`.

## Squared-order-only ⟹ amplitude order inferred (LO-only; lines 4994-5000)
If the user gives ONLY a squared order (`NP^2==2`, no amplitude `NP=`) and no perturbation `[...]`:
`if orders=={} and squared_orders!={} and not perturbation_couplings:` for each squared order,
`orders[order] = squared_orders[order][0]` when the value ≥0 and the type isn't `>`; **else
`orders[order] = 99`** (negative or `>` → amplitude can't be known at gen time, so uncapped).
Probe `dim6top_LO_UFO; generate p p > t t~ DIM6^2==2` → 15 gg / 6 uu~ diagrams (same as the
explicit-amplitude `DIM6^2==2` row in eft-squared-order-diagram-filtering.md) — the reinterpretation
set `orders[DIM6]=2` from the squared value. So `NP^2==2k` *alone* IS a usable quadratic constraint
at LO; the amplitude order is inferred. (This block is gated `not perturbation_couplings` → LO-only;
the NLO path is eft-nlo-order-determination.md.)

## Perturbation `[...]` parsing + LoopOption (lines 4851-4877)
`perturbation_couplings_pattern` (4852-4853) splits `proc [ option= pertOrders ] rest`. `LoopOption`
defaults `'tree'`; an `[opt=...]` sets it from `_valid_nlo_modes = ['all','real','virt','sqrvirt',
'tree','noborn','LOonly','only']` (line 3035). Bare `[QCD]` (no `opt=`) → `LoopOption='all'`. The
special `[tree= NP]` keeps LoopOption='tree' (LO) but routes NP into split_orders only — see
eft-squared-order-diagram-filtering.md for the LO split mechanism. `split_orders` is then built as
`make_unique(perturbation_couplings_list + squared_orders.keys())` (line 5264).

## Truncation shapes (k = per-insertion value from the model's coupling_orders.py)
- `NP=0` SM-only · `NP=k` linear (SM×EFT interference) · `NP^2==2k` quadratic (full squared incl EFT×EFT)
- `NP<=2k`, `NP^2<=2k` bounds. Whether to truncate linear vs squared is ma-physics-consultant's call.
- amp vs squared parse to different amp_split accounting (nlo-export slice owns amp_split).
- **These `==` shapes are LO-only.** At NLO both `NP==k` and `NP^2==2k` are REJECTED — only `<=`
  allowed (eft-nlo-order-determination.md). Translate to `NP<=k` / `NP^2<=2k` for `[QCD]` processes.
