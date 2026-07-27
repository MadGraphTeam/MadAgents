---
description: How particle widths reach the MadSpin interface — banner param_card ONLY, no compute_widths; where the total width is consumed for BR; zero-width division edge
---

# Width handoff to the MadSpin interface

How the decaying particle's **total width** reaches the MadSpin interface, and where it is
consumed. `$MADGRAPH_INSTALL/MadSpin/interface_madspin.py`.

## The interface NEVER computes widths
- Only decay-relevant import is `import MadSpin.decay as madspin` (:47). There is **no**
  `compute_widths` / width-computation module imported or called anywhere in `interface_madspin.py`
  (grep-confirmed). Width *computation* is upstream (madwidth slice / param-card `Auto`); by the time
  MadSpin runs, every total width is a concrete number baked into the **input LHE banner's
  param_card decay block**.
- So an `Auto` / `DECAY <pid> auto` in the param_card must already have been resolved to a number by
  the MadGraph launch flow *before* the events were written. MadSpin reads the resolved value off the
  banner; it does not re-resolve `Auto`. (Resolution-of-Auto itself is madwidth's slice — boundary.)

## Where the total width is READ (all from the banner)
Every width read is `banner.get('param'|'param_card', 'decay', abs(pdg)).value`:
- bridge (`spinmode='none'`) BR loop: `totwidth = float(self.banner.get('param','decay',abs(pdg)).value)` (:964).
- `new_wgt='BR'` single-decay site: `tot_width = float(self.banner.get('param','decay',abs(pdg)).value)` (:1108).
- onshell BR loop: `totwidth = self.banner.get('param_card','decay',abs(pdg)).value` (:1470).
- run_from_pickle re-exposes for the decay core: `generate_all.pid2width = lambda pid:
  generate_all.banner.get('param_card','decay',abs(pid)).value` and `pid2mass` likewise (:743-744).

## How the width is USED — BR = partial-cross / total-width
`generate_events(..., output_width=True)` returns the decay sub-process **partial cross-section** as
`width` (summed for cumul / multiplied otherwise — see madspin-generate-events-decay-me page). That
`pwidth` is divided by the banner's `totwidth` to form the branching ratio:
- bridge: `br *= pwidth / totwidth` (:970); multi-particle variants `(pwidth/totwidth)**nb_mult`
  (:987) and `* math.factorial(nb_mult)` (:982).
- onshell: `br *= pwidth / totwidth` (:1479), with `pwidth` capped: if `pwidth` exceeds `totwidth` by more
  than a small tolerance -> `logger.warning('partial width larger than total width --from param_card--')`, then
  `elif pwidth > totwidth: pwidth = totwidth` (:1475-1478 — read the tolerance fresh).
- `new_wgt='BR'` direct: `br = decay_file.cross / tot_width` (:1110).
- Final: `self.branching_ratio = br`; `self.cross = banner.get_cross() * br` (:1510-1514, onshell) —
  the BR-scaled cross-section the MadGraph caller reads off the interface.

Physics meaning: `pwidth` (partial cross-section of the decay sub-process) / `totwidth` (total width
from param_card) approximates the partial branching ratio Γ_partial/Γ_total under NWA. The param_card
total width is the **denominator of the BR** — a wrong total width directly mis-normalizes the
decayed-sample cross-section, even though the kinematics are unaffected.

## The decay sub-process gets the param_card verbatim
The per-PDG decay MadEvent dir's `param_card.dat` is written straight from the banner:
`param_card = self.banner['slha']; open(.../Cards/param_card.dat,"w").write(param_card)` — both
regimes (:1281-1282 gridpack, :1338-1339 inline). So the **same** widths/masses MadSpin uses for BR
normalization are the ones the decay ME is generated with — no independent width source. (In-card
`import model NAME CARD` can swap this param_card, but the strict diff guard forces it value-identical
to the banner unless `--bypass_check`; see madspin-import-resolution page.)

## Cautions / edges
- **Zero total width -> division.** The `new_wgt='BR'` site guards with `if tot_width:` (:1109) so a
  zero width there leaves `br` unchanged. But the bridge (:970) and onshell (:1479) BR sites divide
  by `totwidth` with **no zero-guard**. A decaying PDG whose param_card DECAY entry is `0.0` (e.g. a
  stable-declared particle, or an `Auto` that resolved to ~0) would hit `pwidth / 0.0`. *Runtime
  prediction (ZeroDivisionError at :970/:1479) — NOT probe-verified; listed as probe-candidate.*
- **BR > 1 symptom.** `pwidth` exceeding `totwidth` by more than a small tolerance logs `logger.critical("Branching ratio larger than
  one for %s")` (bridge :969/980/986) or a `logger.warning(... --from param_card--)` (onshell
  :1476 — tolerance read fresh). This is the canonical "total width in the param_card is too small / inconsistent with the
  decay sub-process" symptom — it points at the handed width, not the decay generation.
- **BW_cut is a separate width-related knob.** `BW_cut` (the Breit-Wigner sampling window, in units of
  the width) is resolved from the banner `bwcutoff` at do_import, NOT from the decay width here; see
  madspin-import-resolution. This page is about the *total width value* used for BR normalization.
- Width *value* is the handoff (in slice); how decay.py samples off-shellness within ±BW_cut*Γ is
  MadSpin-internal (out of slice).

## Gaps / boundary
- Resolving param_card `Auto` widths to numbers — madwidth slice (happens before MadSpin).
- decay.py's internal use of the width for BW sampling — MadSpin internals, out of slice.

## Probe-candidates (expensive)
- Decay a PDG whose param_card DECAY total width is `0.0` under `spinmode='none'` and `'onshell'`;
  confirm the unguarded `pwidth/totwidth` raises ZeroDivisionError (vs the guarded `new_wgt='BR'`
  path). Expected division crash at :970/:1479.
