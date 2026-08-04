---
description: Probe-confirmed runtime behavior of polarization syntax in MG5_aMC 3.7.1 — L-warning, scalar-0 reject, ambiguous-mix abort, disjoint-pol pass, generation-time massless-0 drop (NoDiagramException)
---

# Polarization parse-time probes (v3.7.1, probe-confirmed)

All run via `python3 $MADGRAPH_INSTALL/bin/mg5_aMC <file>` at `generate` time (parse
stage, no `output`/`launch` needed). These are runtime-observed, not reading-only.

## `Z{L}` → left-handed warning, parses (probe)
`import model sm; generate e+ e- > Z{L} Z{L}` →
- emits (once per `{L}` leg): `"L" polarization is interpreted as left (-1); for
  longitudinal (0) please use "0".`
- proceeds normally: "Process has 2 diagrams". So `L` on spin-1 is a WARNING not an
  error; the value is left-handed -1. Confirms `pol-letter-mapping.md` L row.

## `h{0}` (scalar) → hard reject (probe)
`generate e+ e- > h{0} z` → `InvalidCmd : "0" (longitudinal) polarizations are not
supported for scalars/fermions.` Higgs spin==1 (scalar in 2s+1) so `0` is rejected
at parse. Confirms the spin-in-[1,2] branch (madgraph_interface.py:5176-5177).

## `z{T} z` → ambiguous-mix critical + default-abort (probe)
`generate e+ e- > z{T} z` →
- `logger.critical`: "Not Supported syntax: ... Syntax like p p  > Z{T} Z are
  ambiguious ... symmetry factor ... We suggest you to abort this computation".
- prompt `Do you want to continue [no, yes]` — default shown as `no`.
- non-interactive run takes default → `InvalidCmd : Not supported syntax of type
  p p  > Z{T} Z`. Confirms check-polarization.md caller behavior; the False return
  here is the per-PID polarized(23)+unpolarized(23) overlap.

## `p p > z{T} z{A}, z > e+ e-` → disjoint-pol same-PID PASSES (probe)
The documented help example. `z{T}`=[1,-1] and `z{A}`=[99] are both PID 23 but their
helicity values are **disjoint** → `check_polarization` finds no overlap → NO
ambiguous-mix prompt, NO critical. Generates: "Process has 2 diagrams" per subprocess.
Confirms `check-polarization.md` disjoint-allowance and that the documented
multiple-polarized-copies form works. Display renders the leg as `z{99}` (the `{A}`
code 99 has no T/L/R shorthand, so the reverse-render falls back to the raw code —
confirms `pol-allowed-values.md` reverse-render).

## `e+ e- > a{0} z` → massless-boson sole-0 dropped at GENERATION → NoDiagramException (probe)
Parse emits `logger.info '"0" (longitudinal) polarization detected for massless
boson.'` but generation strips the photon's only pol (`0`, mass attr ZERO) → empty →
process dropped → `NoDiagramException : No amplitudes generated ... Please enter a
valid process`. NOT a polarization error. Contrast `e+ e- > a{0R} z` which survives
(R remains after 0 stripped): "Process has 2 diagrams". Confirms
`pol-generation-expansion.md` — the 0-bypass site is diagram_generation, not numerical.

## Note
- The `do_add` ambiguous-mix path is a runtime `ask()`; in a script it aborts by
  default. To force-through requires answering `yes`. (Probe used a 2-line script
  with no answer → abort.)
