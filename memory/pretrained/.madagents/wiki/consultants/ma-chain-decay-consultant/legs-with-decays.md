---
description: Process.get_legs_with_decays — the flattened full-depth leaf-leg final state of a decay chain (the EXTERNAL counterpart to the internal s-channel-mother onshell story); recursive leaf substitution, decay-to-core sort+assert, 1..N renumber, cached with invalidation; drives IDUP/leshouche.inc, subprocess naming, identical_particle_factor, IdentifyMETag.
---

# legs_with_decays — the flattened final state of a decay chain

Source: MG5_aMC v3.7.1. My other pages trace the INTERNAL story (onshell s-channel mothers → decayBW.inc). This page is the EXTERNAL counterpart: how a decay chain's *leaf* final-state legs are computed and where they are consumed. None of the onshell-* / comma-parser / combine pages cover it.

## The field and its builder
`Process` carries two leg lists (base_objects.py):
- `self['legs']` — the CORE process legs (e.g. `g g > t t~`, final state `t t~`).
- `self['legs_with_decays']` — the FLATTENED final state after substituting every decay chain's leaves (default empty `LegList()`, base_objects.py:2972).

`Process.get_legs_with_decays` (base_objects.py:3667-3702) builds the second from the first:
1. **Cache hit** (3670-3671): if already populated, return it.
2. **Sort decay chains to core leg order** (3676-3684): walk core final-state legs in order; for each, pop the decay chain whose incoming id (`l.get('legs')[0].get('id')`) matches. `assert not org_decay_chains` (3684) — **every** decay chain MUST correspond to a core final-state leg, else assertion error.
3. **Substitute leaves, full depth** (3686-3692): for each sorted decay, find the matching core leg index and splice `decay_legs[1:]` in place of it — where `decay_legs = decay.get_legs_with_decays()` (3690) **recurses**, so a subdecay's leaves are themselves flattened. `[1:]` drops the decaying particle itself (index 0 = the incoming leg), keeping only its products.
4. **Copy + renumber 1..N** (3694-3698): `leg.set('number', ileg+1)` — the flattened legs are renumbered contiguously from 1.
5. **Cache and return** (3700-3702).

So `legs_with_decays` is the recursive leaf set of the decay tree, in core-leg order, renumbered 1..N. The decaying particles (t, w+, t~) do NOT appear; only the leaves do.

## Cache invalidation
The cache is cleared whenever the leg structure is reset: `set('legs', ...)` runs `del self['legs_with_decays']` (base_objects.py:3838, in the legs-setter reset path). The special `get` at base_objects.py:3131-3134 lazily computes it on first access. So it is a memoized derived quantity, recomputed if `legs` change.

## Why the assert (3684) holds at output time — cross-link
The `assert not org_decay_chains` would fire if a decay chain had no corresponding core leg. But by the time output runs, any "decay without corresponding particle" chain has ALREADY been DISCARDED in `DecayChainAmplitude.__init__` (diagram_generation.py:1399-1424, see onshell-flag-and-decayBW.md case 1) — the offending amplitude/chain is removed with a RED warning. So the discard upstream is what GUARANTEES the assert downstream. The flat-vs-nested parenthesization trap (cautions.md §2) thus has a second consequence: a mis-nested subdecay is dropped *before* legs_with_decays, so the leaf list reflects only ATTACHED decays.

## Consumers (all in-slice-adjacent — this is what the leaf list feeds)
- **IDUP / leshouche.inc external particle list** (export_v4.py:955): `legs = proc.get_legs_with_decays()` → `DATA (IDUP(i,...))/<leaf ids>/`. The per-event external PDG list is the LEAF set, not the core final state.
- **identical_particle_factor** (base_objects.py:3746): the symmetry denominator counts identical particles among `get_legs_with_decays()` final legs — i.e. the DECAYED final state, not the core.
- **IdentifyMETag** (helas_objects.py:140): `legs = [l.get('id') for l in sorted(process.get_legs_with_decays())]` — the combined-process identity tag (used by the combine layer's identity merge, combine-decay-chain-layer.md step 8) is keyed on leaf ids.
- **Subprocess directory naming**: the `P1_..._t_bwp_wp_lvl_tx_bxwm` style dir name encodes the full decay tree (the leaves), via the same flattened structure.

## Probe verification (MG5_aMC v3.7.1)
Correct nesting `generate p p > t t~, (t > b w+, w+ > e+ ve), t~ > b~ w-; output`:
- No "corresponding particle" warning. Subprocess dir `P1_gg_ttx_t_bwp_wp_lvl_tx_bxwm`.
- `leshouche.inc`: `DATA (IDUP(I,1,1),I=1,7)/21,21,5,-11,12,-5,-24/` = `g g > b e+ ve b~ w-` — **7 external** (2 gluons + 5 leaves). The w+ recursively flattened to `e+ ve`, confirming full-depth recursion at :3690. (t, w+, t~ absent — only leaves.)

Mis-nested `t > b w+, (w+ > e+ ve), t~ > b~ w-` (the `(w+...)` is a SIBLING decay, not nested under t):
- RED "Decay without corresponding particle" warning; the `w+ > e+ ve` is DISCARDED.
- `IDUP(I,1,1),I=1,6 = 21,21,5,24,-5,-24` = `g g > b w+ b~ w-` — **6 external**, w+ (24) survives as a LEAF (its subdecay dropped). Subprocess dir `P1_gg_ttx_t_bwp_tx_bxwm` (no `wp_lvl`). Confirms: discarded decay → its parent stays a leaf in legs_with_decays.

## Why this matters for answering questions
- "What final state does my decay-chain process actually produce / what's in the LHE event?" → `legs_with_decays`, the leaf set — NOT the core `>` final state. The number of external particles (nexternal) is the leaf count.
- "Why is my subprocess directory named with all the decay products?" → the dir name encodes legs_with_decays (full decay tree), not the core process.
- This is the EXTERNAL-leg sibling of the onshell story: onshell-* pages answer "what gForceBW does an internal s-channel mother get"; this page answers "what external leaves does the chain produce". A complete decay-chain answer often needs both.
- The assert at :3684 is a structural invariant guaranteed by the upstream discard (case 1) — a mis-nested decay never reaches here; it's dropped first.
