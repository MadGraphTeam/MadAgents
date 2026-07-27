---
description: The polarization-to-SPINUP (LHE col 13) seam — polarization {…} restricts the NHEL helicity matrix; the LO/NLO writers write the definite per-event helicity nhel into SPINUP; SPINUP=0 on a vector = longitudinal (hel 0), NOT "no info". Corrects the "MG sets SPINUP=9 by default" misconception. Writing/selection itself is output/mc-integration, not this slice.
---

# Polarization ↔ SPINUP (LHE column 13) seam

**Slice boundary.** The SPINUP *field* — its LHE-format meaning, where it is
written, the per-event helicity MC selection that fills it — is **output /
mc-integration** territory, NOT polarization-syntax. What IS mine: the parsed
`{…}` polarization list restricts which helicity rows exist in the ME, and the
letter→helicity mapping fixes what SPINUP value a polarized leg can carry. This
page records the seam + the boundary facts I walked, so a future SPINUP question
gets the in-slice part answered and the rest routed.

## Boundary facts (walked, but out-of-slice owner)
- **LO madevent writer** writes the definite per-event helicity into SPINUP.
  `Template/LO/SubProcesses/unwgt.f:607-610`:
  `call get_helicities(iproc, ihel, nhel)` then
  `jpart(7,isym(i,jsym)) = nhel(i)`. `jpart(7,·)` is the 7th particle field =
  SPINUP (col 13) in the LHE `<event>` record. So the value written is the HELAS
  `nhel` integer of the MC-selected helicity row, **not** a blanket 9.
- **NLO writer** likewise: `Template/NLO/SubProcesses/write_event.f:262`
  `SPINUP(i)=dfloat(ic(7,i))` and `:368` `SPINUP_out(i)=dfloat(spin(i))` — again a
  definite per-leg helicity integer (0.0 used only as an init/placeholder at
  `:349,406`).
- **The `SPINUP=9` sentinel is NOT the primary writer's behavior.** `9` appears in
  the NLO *re-read/analysis utility* `Template/NLO/SubProcesses/analysis_lhe.f:182`
  (`SPINUP(i)=9`) and `montecarlocounter.f:1703` uses `-9` — utility defaults for
  events whose helicity is not being tracked, not the generation-time value.
- The `nhel` values come from the ME's **helicity matrix**
  (`export_v4.py:1138 get_helicity_lines` → `NHEL` table, rows from
  `matrix_element.get_helicity_matrix()`, helas-amplitude slice). The per-event
  pick over that table (`get_helicities`, generated per-process) is mc-integration.

## In-slice reconciliation (the SPINUP=9 misconception)

**Common misconception "MG sets SPINUP=9 by default because the ME is
summed/averaged over spins" — CONTRADICTED for the madevent LO/NLO writers.** MadGraph does a
**per-event Monte-Carlo helicity selection** and writes that definite helicity
into SPINUP (unwgt.f:609). Even for an *unpolarized* (helicity-summed) process,
the LHE carries a definite per-event helicity, not 9. (Whether that MC helicity
pick is always active vs a placeholder is mc-integration's call — I cite only that
the writer writes `nhel`, defeating a blanket-9 reading.)

**SPINUP value convention.** MG writes the raw HELAS helicity integer, not the
LHE-standard spin/momentum cosine: vectors → −1/0/+1, fermions → −1/+1 (±½ encoded
as ±1). So on a **vector**, `SPINUP = 0` means **helicity 0 = longitudinal**, NOT
"averaged / no info". Reading col-13 `0.0` on a W/Z as "no helicity info" is the
canonical misread — for a massive vector it is the *longitudinal* state, exactly
what `{0}` selects.

**Polarized generation writes the selected pol into SPINUP — DIRECT from the
letter map.** For `generate p p > w+{0} w-{T}`, the parsed polarization lists
(`pol-letter-mapping.md`) prune the helicity matrix to the selected rows, so the
per-event `nhel` — hence SPINUP — is confined to those:
- `{0}` (longitudinal) → SPINUP = **0** on the W+ (W is massive, so `0` survives;
  contrast a massless boson where `{0}` is stripped at generation, see below).
- `{T}` (transverse) → SPINUP ∈ **{+1, −1}** on the W− (T = `[1,-1]`).
- `{L}` (**the trap**) → SPINUP = **−1** (left helicity), NOT 0. `{L}` on a vector
  is left-handed with a warning; longitudinal needs `{0}`. So a leg written as
  "longitudinal" via `{L}` would wrongly show SPINUP=−1.
- `{R}` → SPINUP = **+1** (right helicity).
- `{A/G/H/Q/W/S}` → SPINUP would carry the exotic sentinel value `[99]/[4]/[5]/
  [6]/[7]/[9]` (the pol whitelist, `pol-allowed-values.md`) — these are internal
  ME-construction codes, not physical helicities; their appearance in a written
  SPINUP column is untested (probe-candidate).

**Massless-boson `{0}` caveat carries into SPINUP.** A massless boson's `{0}` is
stripped at diagram generation (`pol-generation-expansion.md`); if it was the sole
pol the process dies (`NoDiagramException`). So SPINUP=0 from `{0}` only ever
appears for **massive** bosons; a photon/gluon `{0}` never reaches the writer.

## Probe-candidate (expensive — needs a launch + LHE read)
- Generate `p p > w+{0} w-{T}` (or `e+ e- > w+{0} w-{L}`), launch, and read the
  LHE `<event>` col-13: confirm W+ rows carry SPINUP=0 and W− rows ±1, and that
  `{L}` yields −1 not 0. Confirms the letter→SPINUP mapping end-to-end and pins
  whether the exotic codes (99/4/5/…) surface literally in SPINUP. Not run here.
