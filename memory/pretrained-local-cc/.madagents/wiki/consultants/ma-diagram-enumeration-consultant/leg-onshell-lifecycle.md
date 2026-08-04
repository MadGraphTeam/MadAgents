---
description: Leg.onshell tri-state lifecycle — the three set-sites (None default / False forbidden-onsh / True decaying) plus the glue reset-site that no instance page covers
---

# `Leg.onshell` tri-state lifecycle (diagram_generation.py + base_objects.py)

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` and `.../base_objects.py` (v3.7.1).

## The field
`Leg.onshell` is a **tri-state** with three distinct meanings, set by three different mechanisms in two different code regions, plus one reset that can silently flip one value back. Canonical definition `base_objects.py:2111` comment: "onshell: decaying leg (True), forbidden s-channel (False), none (None)"; default `self['onshell'] = None` (`base_objects.py:2112`). It is a member of `get_sorted_keys` (`base_objects.py:2157`) so it persists on the Leg downstream.

This page is the generalization of the local pieces scattered across `generate-diagrams-algorithm.md` (the False site), `decay-chain-amplitude.md` (the True site + base comment) and `reduce-leglist-recursion.md` (the trim mechanism). It assembles the full set-and-reset site-set, **including the reset site no instance page covers**, so the gate "where does this leg's onshell come from / why did it change?" catches more than any one page.

## The four sites (three SET, one RESET)

SET — `None` (default):
1. Every Leg is born `onshell = None` (`base_objects.py:2112`). An ordinary, non-decaying, non-forbidden leg keeps None through generation.

SET — `False` (forbidden on-shell s-channel), during CORE `generate_diagrams`:
2. The `forbidden_onsh_s_channels` post-filter (`diagram_generation.py:781-794`) walks each diagram's non-last vertices, and for any s-channel propagator whose id is in `process['forbidden_onsh_s_channels']`, `copy.copy`s the propagator leg and sets `onshell = False` (:793). This does NOT drop the diagram — it marks the propagator so downstream forbids generating it on-shell. Mechanism detail is in `generate-diagrams-algorithm.md`.

SET — `True` (decaying leg), at DECAY-CHAIN construction (NOT core generation):
3. `trim_diagrams(decay_ids)` (`diagram_generation.py:1270`) called from `DecayChainAmplitude.__init__` (:1397) sets `onshell = True` on external **final-state** legs whose id ∈ `decay_ids`, at two physical sites: process legs (:1284-1286) and diagram legs (:1294-1299, with a `copy.copy` at :1298 before the index-dedup so the flagged leg doesn't alias an unflagged twin). Mechanism detail in `reduce-leglist-recursion.md` (trim_diagrams "Job 2") and `decay-chain-amplitude.md`.

RESET — `False` → `None`, during the final id=0 vertex glue (THE SITE NO INSTANCE PAGE COVERS):
4. The final-id=0-vertex glue (`diagram_generation.py:813-835`, runs only when `not process.get('is_decay_chain')`) pulls the outgoing leg out of the trailing n→0 vertex to replace the next-to-last vertex's incoming leg. If that pulled leg carries `onshell == False` (a forbidden-onsh marker from site 2), it is reset to `None` (:828-830): "Reset onshell in case we have forbidden s-channels". After gluing it is no longer the s-channel-propagator position the filter targeted, so the False marker is removed. This is why a forbidden-onsh flag set in site 2 can disappear from the final diagram — and it only happens on non-decay-chain procs (the glue is skipped for decay chains).

## Why a generalization, not a list
The three set-sites use the SAME field with INCOMPATIBLE meanings, set in different regions (core generation vs chain construction), and the glue step at site 4 can undo a site-2 False **silently** (no log). Anyone reading a downstream Leg's `onshell` must know which of the three meanings applies AND that a False may have been reset to None by the glue. Enumerating "set True here, set False there" misses the reset interaction; the lifecycle framing catches it, plus any FUTURE site that reads or mutates `onshell` must reckon with all three meanings and the reset.

## Boundaries / don't conflate
- `onshell` (decay/forbidden flag) is a DIFFERENT field from `from_group` (clustering-order tri-state); see `decay-proc-from-group-invariant.md`. Separate fields, separate lifecycles.
- The True (decaying) flag is set at CHAIN construction, not during core `generate_diagrams` — core `trim_diagrams` runs with empty `decay_ids` (:841) and sets nothing.
- What downstream HELAS / group_subprocs / export_v4 DO with the flag (force on-shell kinematics for True, forbid on-shell for False) is the helas-amplitude / output slices, not mine. I own only where the field is set and reset during enumeration.

## Cautions
- A leg can be `onshell == False` mid-generation and `None` in the final diagram (site 4 reset) — do not assume the forbidden-onsh marker survives to output on non-decay-chain procs.
- The reset guard is `if lastleg.get('onshell') == False:` (:829) — an explicit `== False` identity check against the tri-state, NOT truthiness; a True (decaying) leg is never reset here (and decay-chain procs skip the whole glue block anyway via the `is_decay_chain` guard at :814).
- True is set only on `state == True` (final-state) legs (:1285/:1295 check `leg.get('state')`); incoming legs never get the decay flag even if their id is in decay_ids.
