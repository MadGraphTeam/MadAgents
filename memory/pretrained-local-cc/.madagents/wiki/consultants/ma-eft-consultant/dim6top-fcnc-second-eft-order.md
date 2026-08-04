---
description: dim6top_LO_UFO declares TWO disjoint EFT power-counting orders — DIM6 (flavour-conserving) and FCNC (flavour-changing), both per-insertion +1, both expansion_order=99 — plus a config-flag-conditional QCD order (norm_chromo_gs).
---

# dim6top has TWO EFT orders (DIM6 + FCNC), not one

The rest of my wiki treats `DIM6` as "the" EFT power-counting order for `dim6top_LO_UFO`.
That is incomplete: the model declares a **second, fully independent EFT-flavoured order**, `FCNC`,
which is a separate truncation knob. A user asking for EFT contributions in dim6top can constrain
`DIM6` and `FCNC` independently on the same process line.

## Both orders are declared in coupling_orders.py (v3.7.1, verified)
`$MADGRAPH_INSTALL/models/dim6top_LO_UFO/coupling_orders.py` declares four orders:
- `QCD` — expansion_order=99, hierarchy=1
- `QED` — expansion_order=99, hierarchy=2
- `DIM6` — expansion_order=99, hierarchy=1
- `FCNC` — expansion_order=99, hierarchy=1

So **both EFT orders have expansion_order=99 (no auto-cap)** and **hierarchy=1**. Neither is silently
capped (contrast SMEFTatNLO NP expansion_order=2; see eft-expansion-order-and-weighted-default-cap.md).

## DIM6 and FCNC are DISJOINT in the couplings (verified)
`$MADGRAPH_INSTALL/models/dim6top_LO_UFO/couplings.py`: **no single coupling carries both DIM6 and FCNC.**
- DIM6-carrying couplings: all `'DIM6':1` (flavour-conserving dim-6 operators).
- FCNC-carrying couplings: all `'FCNC':1` (flavour-changing dim-6 operators). FCNC is the larger set — count off couplings.py if needed.
- A grep for an order dict containing both `'DIM6'` and `'FCNC'` returns **zero** matches.
The full distinct order-dicts (grep `order = {...'DIM6'...}` / `...'FCNC'...}`):
- DIM6 pairs only with QED (and config-conditional QCD): `{'DIM6':1}`, `{'DIM6':1,'QED':1}`,
  `{'DIM6':1,'QED':2}`, `{'DIM6':1,'QED':3}`.
- FCNC pairs only with QED (and config-conditional QCD): `{'FCNC':1}`, `{'FCNC':1,'QED':1}`,
  `{'FCNC':1,'QED':2}`, `{'FCNC':1,'QED':3}`.
**Per-insertion increment for BOTH is +1** (every DIM6 entry =1, every FCNC entry =1). So
the `k` for an FCNC truncation is the same +1 as for DIM6 — but they count different operators.

## FCNC is a working, validatable order constraint (probe-verified)
- `dim6top_LO_UFO; generate t > u z FCNC==1` → `Trying process: t > u z FCNC==1 @1`, **2 diagrams**.
  (FCNC operators contribute to the flavour-changing top decay `t → u Z`.)
- The `==` auto-squared rewrite fires for FCNC exactly as for DIM6/NP: the NoDiagramException on a
  process with no FCNC contribution (`p p > t t~ FCNC==1`) prints the rewritten process
  `... FCNC=1 FCNC==1 FCNC^2==2 @1` — confirming `FCNC==1` auto-generated the squared `FCNC^2==2`
  (madgraph_interface.py:4955-4960, the same `==`→auto-squared rule in eft-power-counting-parser.md).
  So all the order-token-rewriting mechanics (eft-order-token-rewriting.md) apply to FCNC verbatim.
- **DIM6 and FCNC co-constrainable on one line** (probe): `generate t > u z DIM6<=1 FCNC<=1` →
  `Trying process: t > u z DIM6<=1 FCNC<=1 @1`, 2 diagrams. Two independent EFT bounds, one process.

## Caution — `p p > t t~` has NO FCNC contribution at this order
`generate p p > t t~ FCNC==1` raises `NoDiagramException` (probe-verified): FCNC operators don't
contribute to flavour-diagonal top-pair production at order FCNC=1. The order is *accepted* (parser
validates it) but no diagram survives. Do not assume "dim6top EFT = DIM6"; for FCNC processes
(single-top FCNC, `t → q V` decays) FCNC is the relevant order and DIM6 may be the empty one.

## Config-flag-conditional QCD order (norm_chromo_gs) — a coupling-order value that flips on a setting
A subset of couplings in `dim6top_LO_UFO/couplings.py` (the chromomagnetic-type ones) carry a **QCD order
that depends on a model config flag**: `order = {... 'QCD':1 if configuration.norm_chromo_gs else 0}`
(and `'QCD':2 if ... else 1`).
- `$MADGRAPH_INSTALL/models/dim6top_LO_UFO/configuration.py:6`: `norm_chromo_gs = False` (the default).
- So **by default those chromomagnetic-type couplings carry QCD:0** (the `else` branch); editing
  `configuration.py` to `norm_chromo_gs = True` bumps them to QCD:1 / QCD:2.
- `parameters.py:3809` uses the same flag: `value = 'G' if configuration.norm_chromo_gs else '1.'` —
  the flag also rescales the chromomagnetic coupling normalization by the strong coupling G.
- **Coupling-order hazard**: the QCD power assigned to chromomagnetic operators is config-dependent, so
  the WEIGHTED order and any `QCD<=n` truncation interact with these operators differently depending on
  `norm_chromo_gs`. The default (False) keeps them at QCD:0 (pure-EFT, no extra strong-coupling power).
  If a user reports unexpected QCD-order behaviour on chromo operators, check `configuration.py`.

## Boundary
- Whether DIM6 vs FCNC (or both) is the physically-wanted EFT contribution for a given process is
  ma-physics-consultant's call; this page records only that both are independent, validatable orders.
- The flavour-structure / operator content of the FCNC vs DIM6 couplings is ufo-slice territory; this
  page covers only the coupling-order axis (the orders exist, are disjoint, per-insertion +1, no cap).
