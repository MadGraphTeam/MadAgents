---
description: Polarization {} placement validation in check_process_format — the four parse-time rejections (required s-channel, forbidding particles, NLO, colored/massive gates) that run upstream of extract_process letter parsing
---

# Polarization `{}` placement restrictions (`check_process_format`)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `check_process_format`
(method opens at **1150**, v3.7.1). This runs **before** `extract_process` (5082+)
ever parses the letters inside `{}`. It validates *where* a polarization marker may
appear and *under what process mode* — so a `{}` in the wrong position is rejected
here with a placement error, never reaching the letter-mapping loop. All four
rejections below are **parse-time** (`generate`, no `output`/`launch`) and were
**probe-confirmed** in v3.7.1.

The block is gated by the comment at **1189**: "'{}' should only be used for onshell
particle (including initial/final state)".

## 1. Not in required s-channel (1191-1193)
When the process has two `>` (`nbsep == 2`, a required s-channel is named between
them), a `{` anywhere in that middle piece (`particles_parts[1]`) raises:
`InvalidCmd('Polarization restriction can not be used as required s-channel')`.
- Probe: `generate p p > Z{T} > e+ e-` → `InvalidCmd : Polarization restriction can
  not be used as required s-channel`.
- Note: `nbsep` counts `>\D` via regex (1167), not `process.count('>')`, to avoid
  miscounting things like `QCD^2>2`.

## 2. Not in forbidding particles (1194-1197)
`split = re.split(r'\D[$|/]', particles_parts[-1], 1)`; if the part after a `$` or `/`
(forbidden / excluded particles) contains `{` →
`InvalidCmd('Polarization restriction can not be used in forbidding particles')`.
- Probe: `generate e+ e- > e+ e- / Z{T}` → `InvalidCmd : Polarization restriction can
  not be used in forbidding particles`.

## 3. Not for NLO — unless noborn/sqrvirt (1199-1204)
`if '[' in process and '{' in process:` (any NLO bracket + any polarization):
- escape hatch: if `'noborn' in process or 'sqrvirt' in process` → `valid = True`
  (allowed, subject to the colored/massive gates below).
- else → `InvalidCmd('Polarization restriction can not be used for NLO processes')`.
- Probe: `generate p p > e+{R} e- [QCD]` → `InvalidCmd : Polarization restriction can
  not be used for NLO processes`.

## 4. NLO-pol escape gates: colorless AND massless (1206-1237)
When NLO+pol IS allowed (noborn/sqrvirt path), every polarized particle in the
external (initial+final) legs is checked by the inner `check(p)` (1213-1217):
- `p.get('color') != 1` → `InvalidCmd('Polarization restriction can not be used for
  color charged particles')`.
- `p.get('mass') != 'ZERO'` → `InvalidCmd('Polarization restriction can not be used
  for massive particles')`.
- The loop (1221-1237) only inspects tokens containing `{`; resolves the name (or each
  member of a multiparticle, 1229-1232; or `.lower()`, 1234) and applies `check`.
- The commented-out 1210-1211 shows an old restriction ("Polarization ... can not be
  used for generic NLO computations") that no longer fires — only color/mass gate now.
- Probe (colored): `generate p p > t{R} t~ [noborn=QCD]` → `InvalidCmd : Polarization
  restriction can not be used for color charged particles`.
- Probe (massive): `generate e+ e- > w+{R} w- [noborn=QCD]` → `InvalidCmd :
  Polarization restriction can not be used for massive particles` (W is colorless but
  mass attr is `mdl_MW`).

## Caution — mass gate keys on the mass *attribute string*, not a number
`check` tests `p.get('mass') != 'ZERO'` — the symbolic mass *name*, not its numeric
value. In the **default `sm` model (restrict_default)** light fermions carry mass
attribute literally `'ZERO'` (probe-inspected: `mu-`, `e-`, `ve` all
`mass='ZERO'`), so `generate e+ e- > mu+{R} mu- [noborn=QCD]` passes this gate (it
then dies later with `NoDiagramException` — a noborn/QCD structural issue, NOT a
polarization rejection). A full (non-restricted) model where the muon mass attr is
`'MMU'` would instead trip the massive gate. So whether a given fermion passes
depends on the model restriction, not on physics mass. Heavy quarks (`t`=`mdl_MT`,
`b`=`mdl_MB`) and W/Z always carry symbolic non-ZERO mass and are gated.

## Relation to the rest of the slice
- This is the **placement / process-mode** layer; `pol-letter-mapping.md` is the
  **letter→helicity** layer inside `extract_process`; `check-polarization.md` is the
  **ambiguous polarised/unpolarised mix** layer (post-construction, in `do_add`).
  A `{}` survives all three to be a valid polarized leg.
- These four errors fire before any letter is interpreted, so e.g. a *required
  s-channel* `{...}` is rejected for placement regardless of whether the letters
  inside are valid.
