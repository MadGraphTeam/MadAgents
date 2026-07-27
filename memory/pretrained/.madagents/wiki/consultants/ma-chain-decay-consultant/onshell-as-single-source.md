---
description: Unifying principle — every decayBW.inc value is one lookup of the s-channel mother leg's onshell tri-state; three writer paths across two slices, distinct structural targets (final-state external vs internal s-channel); never count commas.
---

# onshell is the single source of truth for every decayBW.inc value

Source: MG5_aMC v3.7.1. This page lifts the unifying rule out of `comma-parser.md`, `onshell-flag-and-decayBW.md`, `decayBW-artefact.md`, and `cautions.md` — each documents ONE writer of the `onshell` field; this page states the rule that answers ANY decayBW.inc value, including writer-collision cases the per-path pages don't individually reach.

This is the **VALUE-axis** generalization (given an s-channel mother already in the config, what gForceBW does it get). Its **BINDING-axis sibling** is `decay-binding-is-scope-times-match.md` — which legs become decay mothers at all / which subdecays attach-leak-drop. A binding question (does this clause bind? to which legs?) is answered THERE; this page assumes the mother is already present and asks only its value.

## The principle
`write_decayBW_file` (export_v4.py:5884-5894) reads exactly one thing per emitted line:
```python
leg = vertex.get('legs')[-1]   # the resulting (mother) leg of each s-channel vertex
booldict[leg.get('onshell')]   # {None:"0", True:"1", False:"2"}
```
So **the gForceBW integer for any leg is a pure function of that s-channel mother leg's `onshell` state at output time** — nothing else. To answer "what gForceBW will leg X get", you do NOT count commas, inspect syntax, or reason about resonances; you ask **which code path last wrote `onshell` on the s-channel mother leg X.** Then read decayBW.inc to confirm.

## The three writer paths (two slices) and their structural targets
`onshell` is a tri-state (`base_objects.py:2111-2112`, comment `# onshell: decaying leg (True), forbidden s-channel (False), none (None)`). Three paths write it:

| Path | Value | Set where | Structural target | gForceBW | Owning slice |
|------|-------|-----------|-------------------|----------|--------------|
| default | `None` | Leg ctor `base_objects.py:2112` | any leg, untouched | 0 | (none) |
| comma-decay | `True` | `DecayChainAmplitude.trim_diagrams` `diagram_generation.py:1284-1286` (core legs) + `1294-1299` (diagram-walk) | **final-state external leg** whose id ∈ `decay_ids` (`leg.get('state')` True) | 1 | mine (chain-decay) |
| `$`-forbidden | `False` | forbidden-s-channel marking `diagram_generation.py:781-793` | **internal s-channel propagator** (resulting leg of a non-final vertex) whose s-channel id ∈ `forbidden_onsh_s_channels` | 2 | diagram-filter |

The key non-obvious fact: **the two non-default writers target structurally different legs.** Comma-decay (`True`) flags a *final-state external* leg, which later becomes an s-channel *mother* in the config decomposition. `$`-forbidden (`False`) flags an *internal s-channel propagator* directly. This is why they almost never collide on the identical leg write_decayBW_file reads — and why a process can carry both a /1/ line and a /2/ line for different mothers without contradiction.

## Reset edge: `$` can clear False back to None
Only the `$`/diagram-filter path has a reset: when gluing the final id=0 vertex on a non-decay-chain process, `diagram_generation.py:828-830` resets `onshell False → None` for a forbidden s-channel in a specific glue case. comma-decay's `trim_diagrams` only ever *sets* `True`; it never clears. So precedence among writers is not a runtime race — each acts on its own structural class of leg, and the only reset is internal to the `$` path.

## Probe verification — all three values reachable end-to-end (MG5_aMC v3.7.1)
- **value 1** (comma-decay, True): `p p > t t~, (t > b w+, w+ > e+ ve), t~ > b~ w-; output` → `P1_..._t_bwp_wp_lvl_tx_bxwm/decayBW.inc` has `GFORCEBW(-1..-3,1)/1/` (t, w+, lepton-side mothers) and `GFORCEBW(-4,1)/0/` (undecayed mother). Properly-nested keeps the w+ forced-BW line.
- **value 0** (default, None): same file, `GFORCEBW(-4,1)/0/`; also `u u~ > e+ e- $ z` → `GFORCEBW(-1,1)/0/` for the unforbidden photon s-channel.
- **value 2** (`$`-forbidden, False): `u u~ > e+ e- $ z; output` → `P1_qq_ll/decayBW.inc`:
  ```
        DATA GFORCEBW(-1,1)/0/      ! photon s-channel — None
        DATA GFORCEBW(-1,2)/2/      ! Z s-channel — $-forbidden → False
  ```
- **no-collision check**: `p p > t t~ $ t, t > b w+; output` → t mother gets `/1/`, not `/2/`. The `$ t` targets internal s-channel t, but here t is a *final-state* leg (no internal t propagator to forbid), so the `$` marks nothing and comma-decay's True wins. Confirms the structural-target separation: `$` on a final-state particle is a no-op for decayBW.inc.

## Catches beyond the instances
- **Collision/precedence questions** ("leg both decayed and `$`-vetoed — which value?"): resolve by structural target, not by syntax order. No per-path page answers this; this page does.
- **"value 2 in my decayBW.inc" triage**: immediately a diagram-filter-slice concern (forbidden s-channel), never a comma artefact — even though it surfaces in my file.
- **Any future syntax that touches `onshell`**: the rule (trace the last writer of the mother leg's onshell) holds regardless of how the field gets written; new writers would just extend the table.

## Decision procedure (the operative takeaway)
1. Identify the s-channel mother leg (negative number) for the iconfig in question — from configs.inc / decayBW.inc, not from the command line.
2. Ask which writer last set its `onshell`: comma-decay (final-state external id ∈ decay_ids) → 1; `$`-forbidden (internal s-channel id ∈ forbidden_onsh_s_channels) → 2; neither → 0.
3. Confirm against decayBW.inc. Never infer gForceBW from comma count or syntax shape.
