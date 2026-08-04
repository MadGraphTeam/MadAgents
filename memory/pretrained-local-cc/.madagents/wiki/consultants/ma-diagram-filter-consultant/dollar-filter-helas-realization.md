---
description: The $-filter's onshell=False flows from the base Leg onto the HelasWavefunction, emitting a P1D ("DOLLAR") propagator routine + extra BWCUTOFF arg in the ME code, and zeroing s_pdg in the ME-identity hash — distinct from the gForceBW=2 phase-space cut. Probe-confirmed.
---

# `$`-filter realization at the HELAS / matrix-element-code level

File: `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (v3.7.1). This page
covers what happens to the `$`-filter's `onshell=False` leg flag AFTER
diagram_generation marks it (see diagram-filter-enforcement) and BEFORE/besides
the `gForceBW=2` decayBW.inc emission (see diagram-filter-enforcement §gForceBW).
There is a SECOND, independent realization of the `$` filter: it changes the
generated matrix-element Fortran itself.

## Step 1 — the flag is copied Leg -> HelasWavefunction (675-677)
`HelasWavefunction.__init__` (from a base Leg) copies the mark:
```
675   if leg.get('onshell') == False:
676       # Denotes forbidden s-channel
677       self.set('onshell', leg.get('onshell'))
```
Note the asymmetry: only `False` is copied here in the constructor (True/None
left at the wavefunction default `None`, 643). So the `$`-filter's `False`
survives into HELAS; chain-decay's `True` is set on the wavefunction by a
different path (4386 `wf.set('onshell', True)` — chain-decay slice). Class doc
70-71: the onshell flag exists "since we want the right propagator written" for
onshell s-channel propagators.

## Step 2a — the propagator ROUTINE name gets a `P1D` tag (1898-1899)
In the lorentz/propagator-tag builder:
```
1898   if self.get('onshell') is False:
1899       tags.append('P1D') # D is for DOLLAR
```
So a `$`-marked s-channel propagator is routed to a DISTINCT aloha/helas
routine whose name carries `P1D`. `P1D` sits in the same tag family as the
polarization/propagator tags `P1L/P1T/P1A/P1LS/P1G/P1H/P1Q/P1W/P1S` (1611-1643)
and the custom-propagator `P%s` (1602-1604). `P1D` is the off-shell-projected
("dollar") propagator.

## Step 2b — an extra `BWCUTOFF` argument is passed (1597-1600)
In the propagator-call output dict:
```
1597   if self.get('onshell') is False:
1598       output['bwcutoff'] = 'BWCUTOFF,'
1599   else:
1600       output['bwcutoff'] = ''
```
(Lines 1593-1595 are a commented-out alternative that would instead multiply the
width by BWCUTOFF; the LIVE behavior is the extra trailing argument, not a
width-scaling.) This `output['bwcutoff']` is consumed by the HELAS call writer
`$MADGRAPH_INSTALL/madgraph/iolibs/helas_call_writers.py:1244`
(`arg['extra'] = '%(bwcutoff)s'`) and 1716/1718 (C++), so the generated
propagator call for a `$`-marked leg gets a trailing `BWCUTOFF` argument the
ordinary propagator call does not.

## Step 3 — `s_pdg` zeroed in the ME-IDENTITY hash (vertex_id_from_vertex, 212-215)
```
212   s_pdg = vertex.get_s_channel_id(model, ninitial)
213   if s_pdg and (part.get('width').lower() == 'zero' or \
214      vertex.get('legs')[-1].get('onshell') == False):
215       s_pdg = 0
```
A `$`-marked propagator is treated like a ZERO-WIDTH (non-resonant) propagator
for matrix-element IDENTITY: its PDG is dropped from the vertex hash, so the
`$`-filtered process is NOT split into separate ME groups by the would-be
resonance PDG. (`link_from_leg` 172-178 also folds `onshell` into the ME hash —
`id=0` when not onshell, and `onshell` itself is a hash component "since this
specifies forbidden s-channel".) IMPORTANT: this is ME-identity only; it does
NOT change the `sprop` PDG written to `configs.inc` — see SPROP trap below.

## SPROP is NOT zeroed by `$` (export_v4.py:2252-2261)
The `sprop(i,...)` array in `configs.inc` is written from the RAW signed leg id
`v.get('legs')[-1].get('id')` (2256), with no onshell test. So a `$`-marked
s-channel STILL carries its real PDG in `sprop`; what marks it for runtime
rejection is the SEPARATE `gForceBW=2` value in `decayBW.inc`. Do not expect
`$` to zero the sprop entry — the s_pdg=0 zeroing (step 3) lives only in the ME
grouping hash, a different array.

## How the two realizations divide labor
- **ME-code level (this page):** `P1D` routine + `BWCUTOFF` arg = the propagator
  is evaluated with the off-shell projection in the amplitude itself.
- **Phase-space level (diagram-filter-enforcement):** `gForceBW=2` in
  decayBW.inc -> `cut_bw=.true.` at myamp.f when the propagator goes on-shell.
Both fire for the same `$`; they are complementary, not alternatives.

## Probe-confirmed (v3.7.1, sm)
`generate u u~ > e+ e- $ z ; output` yields:
- `decayBW.inc`: `DATA GFORCEBW(-1,2)/2/` (config 2 = the Z channel; config 1 =
  the photon channel has `/0/`).
- `matrix1_orig.f:433-434`: the HELAS call is
  `CALL FFV2_5P1D_3(W(1,1),W(1,2),-GC_50,GC_58,MDL_MZ, FK_MDL_WZ ,BWCUTOFF,W(1,5))`
  — the routine name carries `P1D` and the extra `BWCUTOFF` argument is present.
  Contrast the photon-channel call (no P1D, no BWCUTOFF).

## Cautions
- The `P1D`/`BWCUTOFF` ME-code change is invisible if you only inspect
  decayBW.inc; conversely gForceBW=2 is invisible if you only read the matrix
  file. A reader auditing whether `$` "took effect" should check BOTH artifacts.
- s_pdg=0 (step 3) affecting ME GROUPING means two processes differing only in a
  `$` can land in the same or different ME group than intuition suggests — pair
  with diagram-filter-enforcement §"filters are NOT part of process identity".
- The off-shell projection lives in the ALOHA-generated `*P1D*` routine; the
  detail of what that routine computes (the propagator numerator/denominator
  form) is the aloha/helas-routine slice, not this one. We own that the `$`
  filter ROUTES to it.
