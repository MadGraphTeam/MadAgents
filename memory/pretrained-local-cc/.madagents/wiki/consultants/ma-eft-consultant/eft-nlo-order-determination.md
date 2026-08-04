---
description: aMC@NLO EFT coupling-order determination — unconstrained NP/DIM6 at NLO defaults to default_unset_couplings (99), NOT the LO expansion cap; == amplitude & == squared orders are both REJECTED at NLO; only <= allowed.
---

# EFT coupling-order determination at NLO (aMC@NLO path)

The LO order machinery (expansion-order cap, squared-order diagram filter) does NOT govern NLO.
At NLO the order constraints flow through `amcatnlo_interface.py` with materially different
defaulting and a hard `<=`-only restriction. v3.7.1, all probe-verified on SMEFTatNLO-NLO.

## `==` constraints are REJECTED at NLO (both amplitude and squared)
Two separate gates forbid `==` (and `>`) constraints once a perturbation `[...]` is present:
- **Squared `NP^2==4`**: `$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_interface.py:540-542`
  (`if` at 540-541, `raise` at 542):
  `if myprocdef['sqorders_types'] and any([v != '<=' ...]): raise MadGraph5Error('The squared-order
  constraints passed are not '<='. Other kind of squared-order constraints are not supported at NLO')`.
  Probe (v3.7.1) `SMEFTatNLO-NLO; generate p p > t t~ NP^2==4 [QCD]` → that exact error.
- **Amplitude `NP==2`**: `madgraph_interface.py:4982-4985` (in extract_process; comment at 4982,
  `if` at 4983, `raise` at 4984-4985):
  `if constrained_orders and LoopOption != 'tree': raise InvalidCmd("Amplitude order constraints
  (for not LO processes) can only be of type <=, not '%s'")`. Probe (v3.7.1)
  `generate p p > t t~ NP==2 [QCD]`
  → `InvalidCmd: Amplitude order constraints (for not LO processes) can only be of type <=, not '=='.`
  Note `constrained_orders` is populated ONLY by amplitude `==` (4955-4956) and `>` (4962-4963) —
  `<=`/`=` never enter it, so only `==`/`>` trip this NLO gate.
- **CONSEQUENCE for the slice**: the LO recipes `NP==k` (linear interference) and `NP^2==2k`
  (quadratic) do NOT transfer to NLO. At NLO you write `NP<=k` / `NP^2<=2k`. The linear-vs-quadratic
  *selection* of contributions at NLO is done via the bound values + the per-order ME split
  (split_orders / amp_split, nlo-export slice), not via an `==` diagram filter.

## Unconstrained EFT order at NLO → default_unset_couplings (99), not the expansion cap
The auto-order path (`amcatnlo_interface.py`) defaults differently from LO. KEY surprise: an
unconstrained EFT order does NOT silently become quadratic-at-the-expansion-cap the way a bare LO
process does (contrast eft-expansion-order-and-weighted-default-cap.md). Sequence (probe-verified,
`SMEFTatNLO-NLO; generate p p > t t~ QED=2 QCD=2 [QCD]`, NP unconstrained):
1. **Missing amplitude order → `default_unset_couplings`** (`amcatnlo_interface.py:533-538`,
   warning text at 537; the loop is gated `if myprocdef['orders'] and not all(o in orders ...)` at
   533 — it fires only when the user gave SOME amplitude orders, as the probe does):
   `NP order is missing in the process definition. It will be set to "default unser couplings": 99`
   (verbatim, including MG's typo "unser").
   `default_unset_couplings` default = **99** ("99 means infinity", `madgraph_interface.py:3112`).
2. **Missing squared order → 2× the amplitude value** (`amcatnlo_interface.py:606-612`, warning at 612):
   `Order NP is not constrained as squared_orders. Using: NP^2=198` (= 2×99).
3. The expansion-order cap then clamps the **amplitude** to `NP<=2` (SMEFTatNLO expansion_order=2)
   but leaves the squared order huge → the "...can potentially recieve contributions with powers of
   the coupling NP larger than the maximal value..." warning fires; born processes are generated as
   `g g > t t~ NP<=2 QCD<=3 QED<=2 NP^2=198 QCD^2=6 QED^2=4`.
So at NLO an unconstrained EFT order is effectively **amplitude-capped but squared-unbounded** —
NOT a clean quadratic truncation. ALWAYS pass an explicit `NP<=k NP^2<=2k` at NLO; do not rely on
defaults to truncate the EFT.

## The full auto-order branch (`amcatnlo_interface.py:544-606`) — what each path does
Reached ONLY when `not myprocdef['squared_orders'] and not myprocdef['orders']` (line 545 gate — user
gave NO orders at all). After a `find_optimal_process_orders` weighted guess and
`get_qed_qcd_orders_from_weighted` → integers `qed,qcd`:
- **`nlo_mixed_expansion=True` (the DEFAULT, `madgraph_interface.py:3115`)** — branch at lines 562-579
  (`if` at 562):
  sets `squared_orders={'QED':2*qed,'QCD':2*qcd}` and for every OTHER model order `o`:
  `2*qcd` if `hierarchy[o]==hierarchy[QCD]`, `2*qed` if `hierarchy[o]==hierarchy[QED]`, **else 0**.
  EFT orders (SMEFTatNLO NP hierarchy=1; dim6top DIM6/FCNC hierarchy=1) match neither QCD(=2) nor
  QED(=4) → would be set to **0 (SM-only)** in this auto branch.
- **`nlo_mixed_expansion=False`** — `else` branch at lines 580-606: same hierarchy matching, but adds an
  EFT-specific path: `elif o in expansion_order and expansion_order[o] < 50:
  orders[o]=expansion_order[o]; sqorders[o]=2*expansion_order[o]` (lines 592-594) → NP(exp=2)<50 →
  auto `NP<=2 NP^2<=4` (quadratic). dim6top DIM6 expansion_order=99 (not <50) → 0.
- These two auto branches fire only when the user gave essentially no orders. When the user gives
  partial orders (as in the probe above), the missing-order→`default_unset_couplings` path (530-538)
  governs instead.

## split_orders is FORCED to all model orders at NLO
`amcatnlo_interface.py:625-626` (comment at 622): `myprocdef['split_orders'] += [o for o in
model.get('coupling_orders') if o not in split_orders]` — comment "split all orders in the model, for
the moment it's the simplest solution". So at NLO every model order (NP/DIM6 included) is ALWAYS in
split_orders regardless of what the user asked; matrix.f returns each order-power ME piece separately.
(Per-order ME evaluation = nlo-export slice; recorded here only as the NLO-forces-all-orders fact.)
`born_sq_orders` is then `copy.copy(squared_orders)` (line 621) — the squared constraint carried into
the FKS born subtraction. (Also between the 2× step and split_orders, lines 616-619 set ANY model order
still missing from squared_orders to 0 with warning `No squared order constraint for order %s. Setting
to 0` — a separate zeroing distinct from the 2× default.)

## LO companion trap: default_unset_couplings != 99 zeroes unmentioned EFT orders
`madgraph_interface.py:4970-4980` (LO, in extract_process): if `default_unset_couplings != 99` AND the
user gave some orders/squared_orders, every model order NOT mentioned is set to the default value.
Probe `dim6top_LO_UFO; set default_unset_couplings 0; generate p p > t t~ QED=2` →
`the following coupling will be allowed up to the maximal value of 0: QCD, FCNC, DIM6` and process line
`g g > t t~ DIM6=0 FCNC=0 QCD=0 QED<=2` (2 diagrams) — the EFT order is silently zeroed. With the
default 99 this branch is skipped (the expansion-order cap governs LO instead).

## Cautions / boundary
- Never reuse an LO `NP==k` / `NP^2==2k` recipe at NLO — both raise. Translate to `NP<=k` / `NP^2<=2k`.
- Never rely on NLO defaults to truncate EFT: an unconstrained order goes to default_unset_couplings
  (99), amplitude-capped but squared-unbounded. Pin both the amplitude and squared bounds.
- Whether linear or quadratic truncation is physically wanted = ma-physics-consultant. amp_split /
  per-order ME accounting that consumes split_orders/born_sq_orders = nlo-export slice. R2/UV
  counterterm order-carrying = nlo-model slice (see eft-nlo-specifics.md for the CT_couplings NP tag).
