---
description: Runtime error "failed to reduce to color indices" — where it lives (addmothers.f mother-color reconstruction at LHE-write time), what it reduces (external ICOLUP → intermediate/resonance colors up the diagram forest), the is_LC leading-color gate, and the slice boundary (my slice owns only the upstream color_flow_decomposition; the error routine is output/runtime Fortran).
---

# "Error: failed to reduce to color indices" (addmothers.f)

## Where the string lives
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/addmothers.f:451-452` — emitted by
`subroutine write_error(ida1,ida2,imo)` on the `ida1.eq.1001` branch, after `stop`.
It is a RUNTIME Fortran template (copied into each `SubProcesses/P*/`), fired during
LHE event writing, NOT in the Python color-decomposition core.

## What "reduce to color indices" means
`addmothers.f` reconstructs the color (ICOLUP) of INTERMEDIATE particles
(s-/t-channel propagators, resonances = "mothers") by combining the daughter
external color indices up the chosen diagram's forest. The external ICOLUP flow
is ALREADY selected upstream (color matrix / `select_color`); this routine
propagates it inward to fill mother color tags for the `<event>` record.
The 1001 error = the daughter color indices of a vertex could not be reduced to
a single consistent mother color index.

`write_error(1001,...)` call sites (all "should not happen" color combinations in
the reduction helpers): `:728` (mincol/maxcol epsilon-gluon case fell through),
`:888`, `:1000`, `:1100`, `:1266`. Helpers doing the reduction:
`set_colmp` (`:465`), `elim_indices` (called `:307-317`), `fix_tchannel_color`
(`:241`). `write_error(1000,...)` is a different error (too many legs in a
multiparticle vertex → raise `maxcolmp`).

## The is_LC leading-color gate (confirms the "leading-color" framing)
`is_LC` declared `:84` with comment: "for not leading color bypass the writing of
intermediate particle since the diagram is a very good candidate (and that it
leads to issue)". Set `.true.` at `:117`; set `.false.` at `:130` when the passed
`icol < 0` (signal that the selected flow is NOT leading-color). The mother-color
reconstruction (the `elim_indices`/`set_colmp` block, `:195,199,301`) runs only
under `is_LC`. So the reduction that can 1001-fail is the LEADING-COLOR
mother-reconstruction path — when is_LC is false, intermediate-particle writing
is bypassed entirely (no reduction, no 1001).

## Slice boundary (important)
- MY slice owns the UPSTREAM producer: `color_flow_decomposition` /
  `get_color_flow_string` (`color_amp.py:379-529`, leading-N flow tags) — see
  color-flow-decomposition.md. Those tags reach Fortran via `leshouche.inc`.
- The `addmothers.f` reduction routine, the LHE `<event>` mother/ICOLUP emission,
  and the per-event color-flow SELECTION are OUTPUT-slice + mc-integration/runtime
  territory, not this slice. I can confirm the string's location, the
  leading-color gate, and what is being reduced; I cannot author the runtime
  trigger conditions.

## CAUTIONS / GAPS (not source-settleable here)
- Version-bug claims (color-flow assignment bugs fixed across releases): NOT
  verifiable from a single source tree — leave as caution.
- `group_subprocesses` as a trigger: NO connection visible in addmothers.f; the
  reduction is per-event/per-config. Unverified — gap for output/mc-integration.
- MLM matching (`ickkw>0`): `ickkw` DOES appear in addmothers.f (`:253-267,:411`)
  and changes which propagators are flagged as preserved resonances (`nres`,
  `jpart(6,i)`), hence the mother set walked. This is a PLAUSIBLE but unconfirmed
  interaction; the is_LC reduction branch itself is not ickkw-gated. Gap.
