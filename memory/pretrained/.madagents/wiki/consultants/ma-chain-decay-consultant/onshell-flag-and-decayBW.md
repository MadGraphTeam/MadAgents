---
description: The onshell leg tri-state (None/True/False) set by DecayChainAmplitude.trim_diagrams, write_decayBW_file's booldict to gForceBW 0/1/2, and the post-trim validation (discard missing-core-parent decays; warn on self-decay).
---

# onshell leg-flag → gForceBW mapping

Source: MG5_aMC v3.7.1.

## The Leg onshell field — tri-state
`$MADGRAPH_INSTALL/madgraph/core/base_objects.py`:
- Default `self['onshell'] = None` (base_objects.py:2112).
- Canonical semantics comment (base_objects.py:2111): `# onshell: decaying leg (True), forbidden s-channel (False), none (None)`.
- Validity filter (base_objects.py:2138-2141): must be `bool` or `None`.
- In `get_sorted_keys` (base_objects.py:2157).

So three values only: `None` (plain cascade, no comma-decay, no `$`), `True` (comma-decay flags the leg as decaying/forced-onshell), `False` (forbidden s-channel — set by the `$` diagram filter; that filter is the diagram-filter slice's, but it writes the same field).

## Where True is set — DecayChainAmplitude
`$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py`:
- `DecayChainAmplitude.__init__` builds the amplitude tree, then collects `decay_ids` = the set of PDG ids of every decay sub-chain's incoming particle (diagram_generation.py:1391-1395).
- For each core amplitude it calls `amp.trim_diagrams(decay_ids)` (:1396-1397).
- `trim_diagrams` (:1270-1312):
  - First flags the process's external legs: `if leg.get('state') and leg.get('id') in decay_ids: leg.set('onshell', True)` (:1284-1286). `state` True = final-state.
  - Then, walking diagram vertices, copies and flags each matching external leg `onshell=True` (:1294-1299), guarding (`leg.get('number') not in leg_external`) so only genuine external legs get the decay flag.

This is the source-of-truth for the comma-syntax `gForceBW=1` outcome: a leg gets `onshell=True` only when its PDG id is among the decay-chain incoming-particle ids AND it is a final-state external leg of the core. A comma-decay whose parent never appears as a core final-state leg sets nothing → that leg stays `None`.

Also note diagram_generation.py:779-830: forbidden-s-channel marking sets `onshell=False` (and resets to `None` at :829-830 in a specific case) — this is the `$`/diagram-filter path sharing the field.

## Post-flag validation in DecayChainAmplitude.__init__ (after trim_diagrams)
Two checks run right after `trim_diagrams(decay_ids)` (diagram_generation.py:1396-1397) — both directly in the comma-decay path:

1. **Decay-without-corresponding-particle → discard** (diagram_generation.py:1399-1424). After flagging, it re-checks every core amplitude leg and removes from `decay_ids` any id that IS present. Any id left in `decay_ids` corresponds to a decay whose parent never appears as a core leg. It then:
   - emits a RED `logger.warning`: `"Decay without corresponding particle in core process found.\nDecay information for particle(s) <names> is discarded.\n...This warning usually means that you forgot parentheses in presence of subdecay.\nExample of correct syntax: p p > t t~, ( t > w+ b, w+ > l+ vl)"` (:1409-1414).
   - **actively removes** the offending amplitude(s) from the decay chain, and removes the decay chain entirely if no amplitudes remain (:1416-1424).
   So a flat (un-parenthesised) nested subdecay like `t > b w+, w+ > e+ ve` after a `p p > t t~` core: the `w+ > e+ ve` is a SIBLING decay of the core (it would decay a core `w+`), the core has no `w+` leg → the `w+` subdecay is discarded, not silently flagged-or-not. Confirmed by probe (see decayBW-artefact.md).

2. **Particle-decaying-to-itself → warning only** (diagram_generation.py:1426-1443). For each decay amplitude, if the decaying (initial) particle's `abs(id)` is also among its own final-state `abs(id)`s (e.g. `t > t g`), it appends to `bad_procs` and emits a RED `logger.warning` `"Decay(s) with particle decaying to itself:\n<procs>\nPlease check your process definition carefully."` (:1440-1443). This is warning-ONLY — no discard; the process still generates. Confirmed by probe (`g g > t t~, t > t g`).

These are the runtime manifestation of "parser-acceptance ≠ amplitude-attachment": a syntactically accepted decay can be discarded (case 1) or flagged-with-warning (case 2) at amplitude-build time.

## write_decayBW_file — the integer mapping
`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:5879-5899` (in `ProcessExporterFortranME`):
```python
booldict = {None: "0", True: "1", False: "2"}
for iconf, config in enumerate(s_and_t_channels):
    schannels = config[0]
    for vertex in schannels:
        leg = vertex.get('legs')[-1]          # the resulting (mother) leg of the s-channel vertex
        lines.append("data gForceBW(%d,%d)/%s/" % (leg.get('number'), iconf + 1, booldict[leg.get('onshell')]))
```
The mapping is exactly:
| onshell | gForceBW | meaning |
|---------|----------|---------|
| None    | 0        | default cascade — no forced BW |
| True    | 1        | comma-decay — force Breit-Wigner |
| False   | 2        | `$`-forbidden s-channel |

Read directly each time — the dict is small and could drift across versions.

## How the leg reaches write_decayBW_file
`s_and_t_channels` is built in `write_configs_file` (ProcessExporterFortranME, export_v4.py:~5431-5481) from `h.get('amplitudes')[0].get_s_and_t_channels(...)` on each Helas diagram. The s-channel vertex list's last leg is the decaying mother, which carries the `onshell` flag.

**Mechanism nuance — the operative write is NOT a thread-down of trim_diagrams' core-leg flag.** It is tempting to say "the flag flows: parser → trim_diagrams (onshell=True) → Helas diagram → get_s_and_t_channels". That is the right *value* but the WRONG *provenance*: trim_diagrams' onshell=True is upstream bookkeeping on pre-combination core legs (diagram identity + the `decay` field); the onshell=True that the s-channel mother write_decayBW_file reads actually carries is set **afresh during the helas combination**, at `insert_decay` (helas_objects.py:4386, called per decayed leg from `insert_decay_chains:3980`), on the decay sub-element's decaying-particle wavefunction that physically replaces the core external one. The DiagramTag vertex_id round-trip then preserves that combined-ME value through `get_s_and_t_channels`. So the operative chain is: comma parser → DecayChainAmplitude (core+decays built separately) → helas combine `insert_decay:4386` sets onshell=True on the replacement mother wf → DiagramTag round-trip → get_s_and_t_channels → write_decayBW_file booldict → gForceBW in decayBW.inc. See onshell-helas-bridge.md for the full bridge and why the leg→wf ctor does NOT copy True.

## Emission call site
export_v4.py:4474-4476:
```python
filename = pjoin(Ppath, 'decayBW.inc')
self.write_decayBW_file(writers.FortranWriter(filename), s_and_t_channels)
```
Written once per subprocess directory `<P_n>` at output time, immediately after `write_configs_file` produces `s_and_t_channels` (:4453).

There are **two** `write_decayBW_file` call sites — the ungrouped ME path here (4474-4476) and the **subprocess-group** path (export_v4.py:6408-6410, fed by `write_configs_file` at :6398). Both call the single `write_decayBW_file` (:5879) with the same booldict and the same `s_and_t_channels` object, so the mapping is identical regardless of which fires. Probe-confirmed (MG5_aMC v3.7.1): a standard `output` for `p p > ...` produces grouped `P1_qq_*` / `P1_gg_*` dirs (the 6408 path), and the decayBW.inc values match the booldict exactly — grouping does not change gForceBW emission.
