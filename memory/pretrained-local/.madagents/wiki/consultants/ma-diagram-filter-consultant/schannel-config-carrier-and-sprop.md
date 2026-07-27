---
description: How onshell=False rides get_s_and_t_channels into write_decayBW_file (gForceBW), how sprop/iforest are written to configs.inc, and the full myamp.f cut_bw runtime logic for gForceBW=2 (gated on the onshell window AND sde_strat==1). Probe-confirmed.
---

# The s-channel config carrier and the SPROP/gForceBW runtime trap

Covers the path from a `$`-marked leg to the config-file arrays and the myamp.f
runtime classification. Complements diagram-filter-enforcement (which owns the
parser-field -> diagram constraint) and dollar-filter-helas-realization (the
ME-code P1D/BWCUTOFF side). Boundary: full runtime/phase-space behavior is the
bw-window / phase-space slices; we own that the `2` is produced by `$` and trace
how it reaches the arrays.

## The carrier: `get_s_and_t_channels` (helas_objects.py:1926+)
The decayBW.inc and configs.inc files iterate `s_and_t_channels`, a list of
`[schannels, tchannels]` built by `get_s_and_t_channels`. When it rebuilds the
config legs from the HELAS wavefunctions it COPIES the onshell flag:
```
1962   legs.append(base_objects.Leg({ ...
1966       'onshell': mother.get('onshell') }))      # (also at 2034)
```
So the `$`-filter's `onshell=False` (which rode onto the HelasWavefunction —
see dollar-filter-helas-realization) lands back on the config Leg here. This is
the leg that `write_decayBW_file` reads.

## decayBW.inc: `write_decayBW_file` (export_v4.py:5879-5899)
```
5884   booldict = {None: "0", True: "1", False: "2"}
5886   for iconf, config in enumerate(s_and_t_channels):
5887       schannels = config[0]
5888       for vertex in schannels:
5891           leg = vertex.get('legs')[-1]
5892           lines.append("data gForceBW(%d,%d)/%s/" % \
5893                        (leg.get('number'), iconf + 1,
5894                         booldict[leg.get('onshell')]))
```
So per s-channel leg per config: onshell None->`0`, True->`1` (chain-decay),
False->`2` (the `$` filter). SHARED emission point with chain-decay; this slice
owns the `False->2` row. Note it iterates ONLY `config[0]` (s-channels) — gForceBW
is an s-channel-only array, consistent with `$` being s-channel-only.

## configs.inc: sprop / iforest / tprid (export_v4.py:2242-2270)
For each s-channel vertex:
- `iforest(i,leg,conf)` = the daughter leg numbers (2249-2251).
- `sprop(i,leg,conf)` = the propagator PDG, written from the RAW signed leg id
  `v.get('legs')[-1].get('id')` (2256), padded with `0` for absent subprocesses.
  **No onshell test** — `$` does NOT zero sprop. The s_pdg=0 zeroing lives only
  in the ME-identity hash (dollar-filter-helas-realization step 3), a different
  array.
- t-channel branch (2264-2270): `tprid = abs(id)`, `sprop = all zeros`. This is
  why `$`/`$$`/`> >` cannot touch t-channels — they have sprop=0 and no gForceBW
  row (only s-channels are enumerated into config[0]).

## Runtime: `cut_bw` in myamp.f (Template/LO/SubProcesses/myamp.f:2-204)
The gForceBW array (read from a generated include, 64) drives `cut_bw`:
- **iproc selection (108-113):** loops `iproc=1..maxsproc`, picks the first with
  `sprop(iproc,-1,iconfig).ne.0`; if none, `iproc=1`. So sprop's nonzero-ness
  selects which subprocess column is read. (A `$`-marked s-channel still has
  nonzero sprop, so it participates normally in iproc selection.)
- **gForceBW=2 hard rejection (140-145):** only INSIDE the `if(onshell)` block
  (140), where `onshell` is the bwcutoff-window test (136-139). I.e. the channel
  is rejected ONLY when the propagator is within the BW window AND
  `gForceBW(i,iconfig).eq.2 .and. sde_strat.eq.1`:
  ```
  142   if(gForceBW(i,iconfig).eq.2.and.sde_strat.eq.1) then
  143      cut_bw = .true.
  144      return
  ```
  Off-shell points (outside the window) pass — exactly the "forbid the on-shell
  region, keep the off-shell tail" semantics of `$` (vs `$$` which removes the
  diagram entirely at generation).
- Contrast gForceBW=1 (chain-decay's "force on-shell"): rejected on the OPPOSITE
  branch (179-183) when the propagator is NOT on-shell. So `=1` and `=2` are
  mirror cuts; this slice owns the `=2` (from `$`).

## The SPROP trap (reader caution)
Two arrays carry different things and are easy to conflate:
- `sprop` = propagator PDG, set from the raw leg id, NEVER zeroed by `$`.
- `gForceBW` = the onshell-class code (0/1/2), the ONLY array that encodes the
  `$` filter at runtime.
Auditing "did `$` take effect at runtime?" means reading `gForceBW(...)/2/` in
decayBW.inc, NOT looking for a zeroed sprop. And the `s_pdg=0` you may recall
from the ME hash is a THIRD, unrelated zeroing (ME grouping only).

## Probe-confirmed (v3.7.1, sm)
`generate u u~ > e+ e- $ z ; output`:
- `decayBW.inc`: `DATA GFORCEBW(-1,1)/0/` (photon config), `DATA
  GFORCEBW(-1,2)/2/` (Z config) — the `$ z` config carries the 2.
- sprop for the Z config still carries the Z PDG (not zeroed).

## Cautions
- The `=2` rejection is gated on `sde_strat.eq.1` (142). Whether that single-
  diagram-enhanced strategy is active for a given config is a phase-space /
  integration question — bw-window/phase-space slices. We own that `$` sets the 2.
- The bwcutoff WINDOW that defines "onshell" at 136-139 is the bw-window slice's
  parameter; we own only that gForceBW=2 keys the rejection off it.
