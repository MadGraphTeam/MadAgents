---
description: The pre-channel decay-vertex stage (find_vertexlist) — atomic 2-/3-body decay vertices from model interactions, the type!='base' LO-only filter, self-radiation exclusion, vertex-build-time on-shell flag, goldstone-final-state drop, and keep_Npoint contact-vertex handling.
---

# Decay-vertex enumeration — the stage BEFORE channels (v3.7.1)

All citations `mg5decay/decay_objects.py` unless noted. This is the foundation the channel-enumeration page (`channel-enumeration-bodydecay`) builds ON but does not document: where the atomic decay vertices come from. `find_channels` seeds itself from `decay_vertexlist`; this page owns how that vertexlist is built.

## Two find_vertexlist functions

### DecayParticle.find_vertexlist (542) — per-particle
- Builds `self['decay_vertexlist']`, a dict keyed `(partnum, onshell)` for ONLY 2- and 3-body vertices. The dict is pre-seeded with the four keys `{(2,False),(2,True),(3,False),(3,True)}` (566-569).
- **partnum > 3 skipped** (`partnum = len(partlist)-1` at 585; `if partnum > 3: continue` at 587-588). Direct 4+-body vertices are NOT entered here (they are handled later by `keep_Npoint`, see below).
- **Self-radiation exclusion** (membership guard `if model.get_particle(self.get_anti_pdg_code()) in partlist:` at 591; the count skip at 594-595): if the mother pid appears more than once among the interaction's particles (`part_id_list.count(self.get('pdg_code')) > 1`), the vertex is skipped — excludes vertices where the mother is also a decay product.
- **On-shell flag set at vertex-build time** (627-631): the `(partnum, onshell)` key uses `ini_mass > (total_mass - ini_mass)`, i.e. mother mass > sum of final masses. (`Channel.get_onshell`, 3615, recomputes the same thing at channel level using the ANTIPARTICLE mother mass — see decay-model-setup-stable-particles page.)
- **Caching**: `vertexlist_found` flag (560-562); `option=True` forces a rewrite (542-563). Stable/massless particle → empty vertexlist + early return (574-577, gated on `get('stable_particles')`).

### DecayModel.find_vertexlist (1562) — model-wide driver
- Iterates `self['interactions']`, sets each particle's `decay_vertexlist`. Skips stable particles (no decay vertices). Builds `ini_list` of all non-stable pids first (1581-1585).
- **`type != 'base'` LO-only filter** (1591-1592): `if 'type' in inter and inter['type'] != 'base': continue  # need only the LO interactions.` Interaction `'type'` defaults to `'base'` (madgraph/core/base_objects.py:691); UFO loop import sets non-base types via `add_interaction(..., type=...)` / `interaction.set('type', type)` (models/import_ufo.py:1773,1856) from the UFO-supported set `'UV','UVloop','UVtree','UVmass','R2'` (import_ufo.py:1568). All such non-base (loop / counterterm / R2) interactions are EXCLUDED from width-vertex enumeration. So the LO auto-width engine never sees loop interactions even when a loop-UFO is loaded. (This is the vertex-stage twin of the `--nlo`→SMWidth routing on nlo-smwidth-width-path: at LO the engine simply filters non-base vertices out.)
  - **Probe-confirmed (loop_sm, v3.7.1):** a loop-UFO carries many non-base interactions the filter drops, leaving only its base (LO) vertices to seed width enumeration. The durable fact is the non-base type STRINGS present — `R2`/`UVloop`/`UVloop1eps`/`UVmass`/`UVmass1eps` (not a literal `'loop'`); the per-type counts are per-model + version-drift-prone, so re-tally fresh if a number is load-bearing (`import_full_model('models/loop_sm')`, count `interaction['type']` by value — non-base far outnumber base). Default `models/sm` (tree) has only `{base}` so the filter is a no-op there.
- Fixes antiparticle vertices via `conj_int_dict` (docstring 1568-1569) so only particle-as-mother vertices are constructed explicitly.

## find_channels seeds from the vertexlist (740)
`DecayParticle.find_channels` (740): if `not model['vertexlist_found']` it calls `model.find_vertexlist()` first (check at 774, call at 776). Algorithm (docstring 744-760): a channel is EITHER a single vertex OR an existing channel + one vertex; built incrementally 2..partnum. **Off-shell sub-channels are extended; on-shell sub-channels are NOT** ("any further decay of an on-shell sub-level channel is not a new channel", docstring 752-754) — a channel-construction-level double-count guard that complements `check_gauge_dependence` (decay-model page).

## find_channels_nextlevel vertex consumption (810)
For a clevel with direct vertices (842-845), it deep-copies each vert, renumbers legs (final mother leg → number 1 at 860, state False at 861, anti-pid at 862), runs `initial_setups` (866), then:
- **>3-leg vertices gated by keep_Npoint** (test `if len(vert.get('legs')) >3:` at 847, `if not model.keep_Npoint(vert, self): continue` at 848-849).
- **Goldstone-final-state drop** (875, also 942, 999): `if temp_channel.get_onshell(model): if temp_channel.has_goldstone(model): continue` — an on-shell channel with a goldstone final leg is dropped from the width sum and NOT added as a channel.

## has_goldstone (3631)
`return any(model.get_particle(l.get('id'))['type'] == 'goldstone' for l in self.get_final_legs())`. Keys on the particle's `type` attribute == `'goldstone'` (the SM UFO declares `goldstoneboson = True`, models/sm/particles.py:315,330; UFO import sets `type='goldstone'`). Physics: a goldstone in the final state is the would-be-eaten longitudinal mode of a massive vector; counting an explicit goldstone-final channel would double-count the vector's longitudinal width. Dropped.
- **Model-state caveat**: `merge_all_goldstone_with_vector` (models/import_ufo.py:609,776) can REMOVE goldstones from the model entirely during import — whether any goldstone-final channel even exists to drop depends on the loaded model's gauge/merge state. That merge is the import/restriction slice's; the `has_goldstone` DROP in the decay engine is ours.

## keep_Npoint (1760) — 4+-point contact-vertex handling
For vertices with >3 legs (contact interactions), decides whether the N-point vertex is a genuine irreducible contact term or decomposes into substructure already counted at lower multiplicity.
- **Cache of rejects**: `if vertex['id'] in self['invalid_Npoint']: return False` (1765-1766).
- **Self-decay guard** (1772-1774): if the mother pid appears >1 time in the contact interaction's particles, cache as invalid + return False.
- Builds a `ProcessDefinition` with the interaction's coupling `orders` (other orders forced to 0, 1779-1782), runs `diagram_generation.MultiProcess(..., optimize=False)` (1800), and inspects whether the amplitude has substructure (multi-vertex sub-diagrams) — keeping the contact vertex only if it is irreducible. So a 4-point contact decay vertex that is really two 3-point vertices in disguise is rejected to avoid double-counting.

## Cautions
- **LO-only at the vertex stage.** The `type != 'base'` filter (1591) silently drops all non-base (loop/counterterm) interactions from width-vertex enumeration. A loop-UFO loaded for compute_widths still computes LO widths only — consistent with the always-fired NWA/tree-level warning (compute-widths-flow page). NLO widths require the separate `--nlo`/SMWidth path.
- **Only 2- and 3-body DIRECT vertices** are enumerated in `find_vertexlist`; higher contact vertices reach channels only through `find_channels_nextlevel`'s `keep_Npoint` gate. A 4-point contact decay that `keep_Npoint` rejects contributes no channel.
- **Goldstone-final channels are dropped** — but only if goldstones survive into the loaded model (the import-side merge may have removed them). Don't expect explicit goldstone decay modes in an auto-width card.
- The on-shell flag is computed twice with slightly different mother-mass sources: at vertex-build (`self.get('mass')`, 627-631) and at channel level (`get_anti_initial_id` antiparticle mass, 3615). For self-conjugate / real-mass particles these agree; for entries with a sign/complex mass they could differ — channel-level `get_onshell` is authoritative for amplitude selection (channel-to-amplitude-bridge page).

## Boundaries
- Channel enumeration loop / body_decay precision gate: channel-enumeration-bodydecay.
- Stable-particle determination (which particles get ANY vertexlist), scale running, gauge-dependence channel drop: decay-model-setup-stable-particles.
- Goldstone-vector MERGE at model import: import/restriction slice (we own only the `has_goldstone` enumeration drop).
- NLO interaction handling: not here — the LO engine filters them out; NLO widths go via nlo-smwidth-width-path.
