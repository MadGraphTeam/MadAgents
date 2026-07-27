---
description: sudakov.py EW-Sudakov primitives — isospin-partner dicts, goldstone map, charge conservation, and the get_sudakov_amps amplitude enumeration (LSC/SSC terms).
---

# EW Sudakov amplitude generation

`sudakov.py` (`$MADGRAPH_INSTALL/madgraph/fks/sudakov.py`) builds the auxiliary
amplitudes needed for the high-energy EW Sudakov approximation. Activated by
`ewsudakov=True` in FKSMultiProcess options; `FKSProcess.__init__` calls
`get_sudakov_amps(self.born_amp)` when `ewsudakov` (`fks_base.py:646-648`).

## Hard-coded SM+goldstone dictionaries
These are SM-specific (comment: "should eventually become an attribute of the
model"):
- `get_isospin_partners_diffcharge` (`:39`): charge ±1 partners. Maps quarks
  d↔u etc, leptons e↔ν etc, gauge γ/Z↔W, Higgs/chi↔251 goldstone. Validates all
  ids exist in the model (`SudakovError` if not, `:57-59`).
- `get_isospin_partners_samecharge_cew` (`:65`): same-charge, enters LSC C_EW
  terms. SM: `{22:[23], 23:[22]}` (γ↔Z mixing) only.
- `get_isospin_partners_samecharge_iz` (`:81`): same-charge, SSC I_Z terms. SM:
  `{25:[250], 250:[25]}` (Higgs↔chi).
- `get_goldstone` (`:97`): longitudinal-polarisation goldstone. `{23:250, 24:251,
  -24:-251}`; returns None otherwise.
- `is_charge_conserved` (`:109`): total charge ≈ 0 (sign per state/particle).

## get_sudakov_amps (sudakov.py:126)
Returns a list of amplitude dicts `{type, legs, base_amp, amplitude, pdgs}`.
Stages:
- **0) goldstone** (`:143-173`): every nonempty combination of legs that have a
  goldstone is replaced by goldstones; amplitudes with diagrams kept (type
  `'goldstone'`). These also become base amps for later stages.
- **1) LSC / C_EW** (`:180-202`): single-leg same-charge swap (γ↔Z); type `'cew'`.
- **2) SSC / I_Z single** (`:209-231`): single-leg Higgs↔chi swap; type `'iz1'`.
- **3) SSC / I_Z x I_Z** (`:239-276`): two-leg same-charge swaps; type `'iz2'`.
- **4) SSC / I_pm x I_pm** (`:284-323`): two-leg charge-changing swaps, kept only
  if `is_charge_conserved`; type `'ipm2'`.

Stages 1–4 loop over `[born_amp] + goldstone_amplitudes` as base amps. Each kept
amp records old/new pdgs and the base_amp index.

## Cautions
- The isospin/goldstone dicts are **SM-only and literally coded** — a BSM model
  will either hit `SudakovError` (diffcharge validates ids) or silently get no
  partners (samecharge/goldstone return [] / None on KeyError). EW Sudakov mode is
  effectively SM-with-goldstones only as shipped.
- `MZ: NEVER deepcopy a process!!!` (`:151`) — the code deliberately
  copy.copy's the process and only deepcopies the leg list as a plain `MG.LegList`
  (not FKSLegList) to avoid leg reordering. Preserve this if editing.
- ewsudakov also disables ME combination in FKSHelasProcess.__eq__ (see
  helas-async-generation.md).
