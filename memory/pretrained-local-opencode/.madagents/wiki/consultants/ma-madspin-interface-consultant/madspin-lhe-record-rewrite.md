---
description: LHE event-record rewrite MadSpin performs at the handoff — status=2 for decayed particle, SPINUP(=helicity col 13) semantics per spinmode; the ±1 values are decay.py-internal (GAP)
---

# MadSpin LHE record rewrite — status codes + SPINUP at the handoff

Scope: what MadSpin changes about the LHE event record (status codes, the SPINUP/helicity column) at the interface/handoff. The ±1 helicity VALUES assigned to final states come from decay.py's helicity sampling — INTERNAL, marked GAP below.

## SPINUP == the `helicity` attribute == LHE column 13 (lhe_parser.py)
`madgraph/various/lhe_parser.py` `class Particle`:
- `:117` `self.helicity = 9` — default ONLY when a `Particle` is constructed with no line (`:74`). Same 9-default on the hepmc-import path (`:94`).
- `:133-137` when parsing a real LHE line, `helicity` is read as `float(args[12])` (13th column) — the file's value, NOT 9.
- `:147-162` `__str__` emits `helicity` as the last (13th) column; vtim (col 12) is written by the base writer.
So the `9` is purely a Python fallback for an unparsed/synthetic particle. Consistent with the premise: the base LO writer puts the MC-selected `nhel` into SPINUP, not 9.

## The rewrite primitive: add_decay_to_particle (`lhe_parser.py:1691`)
Turns a status=1 final particle into an intermediate + appends its decay products.
- `:1696` `this_particle.status = 2` — the decayed particle becomes an intermediate record.
- `:1697` `this_particle.helicity = 0` — decayed particle SPINUP set to **0**.
- `:1716-1720` decay products (`decay_event[1:]`) appended as copied `Particle`s → their `helicity` is carried **verbatim** from the decay event; momenta boosted into the parent frame (`:1724`), mothers re-pointed to the decayed particle (`:1727-1748`), colors remapped (`:1749-1773`).
Reached two ways: `Particle.add_decay(decay)` (`:191-194`, forwards to `add_decay_to_particle`), and `Event.add_decays()` below.

## add_decays wraps the primitive and OVERRIDES the decayed SPINUP to 9 (`lhe_parser.py:1775`)
`:1780-1787` recursion over `pdg_to_decay`: for each matching status==1 particle it calls `add_decay_to_particle(i, one_decay)` (which just set helicity=0), then **`:1786 particle.helicity = 9`** — overriding 0 → **9**. So the two entry points give the decayed particle a DIFFERENT SPINUP:
- `.add_decay(decay)` (singular)  → decayed particle SPINUP = **0**.
- `.add_decays(pdg_to_decay)` (recursive) → decayed particle SPINUP = **9**.

## spinmode selects which path does the rewrite (interface_madspin.py)
`spinmode` is the MadSpinOption that routes the rewrite (see madspin-launch-and-decay do_launch dispatch `:617`). The rewrite fires when a decay branch exists for that pdg; `onlyhelicity=True` suppresses it (see below).

- **`spinmode='none'` (run_bridge):** `:1149 particle.add_decay(decay)` (lhe branch) / `:1161 decayed_particle.add_decay(decay)` (hepmc branch) → decayed particle **status=2, SPINUP=0**. No helicity-matching filter for none (`:1138-1139` accepts any decay event). Decay-product SPINUP = whatever the decay-event file carried.
- **`spinmode='onshell'` (run_onshell → get_onshell_evt_and_wgt):** `:1722 full_event = full_event.add_decays(decays)` (also NLO counter-events `:1554`) → decayed particle **status=2, SPINUP=9**.
- **`spinmode='full'/'madspin'` (decay_all_events → decay.py OWN writer):** does NOT use lhe_parser's add_decay. decay.py emits events via `get_particle_line` (`decay.py:200-208`): col 13 = `float(leg["helicity"])`, col 12 (vtim) = `0.0`. Resonance (decayed) record → **status=2** (`decay.py:493 index2mom[-1]["status"]=2`; daughters status 1/2 at `:599-605`) and **helicity=9** (`decay.py:2566`). Final-state helicities come from a sampled `helicities` array (`decay.py:2562`, `:3933`) — the ±1 VALUES are decay.py sampling, **GAP**.

## onlyhelicity mode — helicity reassignment WITHOUT a record rewrite
`onlyhelicity=True` (MadSpinOption): no decay, no status=2, event structure unchanged. `adding_only_helicity` (`decay.py:2468`) + `reset_helicityonly_in_prod_event` (`decay.py:2551`) only overwrite the SPINUP column of the production event: finals → sampled `helicities[...]` (`:2562`), resonances → `9` (`:2566`). So this mode ONLY rewrites SPINUP, never status.

## What the interface writes: decayed → status=2, SPINUP=9; finals → SPINUP=±1
- decayed → status=2: TRUE for all three decay paths (interface-visible).
- decayed SPINUP=9: TRUE for onshell + full/madspin; **FALSE for none (SPINUP=0)**. Spinmode-dependent — interface-visible fact.
- finals get SPINUP=±1: the ±1 magnitude is decay-ME helicity sampling — **decay.py internal, GAP**. Interface-visible part: those sampled values are written verbatim into col 13, and undecayed finals keep their PRODUCTION SPINUP (add_decay_to_particle touches only the decayed particle + appended products; it does not reset other finals to 9).

## Cautions
- SPINUP of the decayed particle is NOT uniformly 9: none→0, onshell/full/madspin→9. A test that asserts "9" will fail under spinmode='none'.
- full/madspin and none/onshell use DIFFERENT writers (decay.py get_particle_line vs lhe_parser Particle.__str__); both are 13-column LHE but formatting widths differ (decay.py `%+18.11e` vs lhe_parser `%+13.10e`).
- lhe_parser add_decay_to_particle requires the decay event's first particle at rest (`:1704-1706` assert) — the decay LHE is in the parent rest frame, then boosted.

## Gaps (decay.py internals — redirect to MadSpin-internals, out of slice)
- The ±1 (and general) helicity VALUES assigned to final states: decay.py importance sampling / helicity selection math.
- The full/madspin decay-ME reweighting that picks those helicities.
