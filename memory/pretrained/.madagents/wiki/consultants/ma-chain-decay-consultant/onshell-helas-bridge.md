---
description: How onshell=True reaches the s-channel mother leg write_decayBW_file reads — the operative write is insert_decay:4386 on the decay sub-element's mother wf (NOT a copy of trim_diagrams' core-leg flag); then DiagramTag vertex_id round-trip, get_s_and_t_channels onshell-copy + min() renumber, is_decay_chain forcing parent-last clustering, __init__ guards, decay_ids provenance.
---

# The onshell → s-channel-mother bridge (helas / diagram-tag layer)

Source: MG5_aMC v3.7.1. My other pages establish two endpoints: `DecayChainAmplitude.trim_diagrams` sets `onshell=True` on a *core final-state external* leg (diagram_generation.py:1284-1299), and `write_decayBW_file` reads `vertex.get('legs')[-1].get('onshell')` of each *s-channel vertex* (export_v4.py:5892). This page is the missing middle. **The onshell=True that write_decayBW_file ultimately reads is NOT a copy of the trim_diagrams core-leg flag threaded down** — for comma-decay it is set *afresh* during the helas combination, at `insert_decay` (helas_objects.py:4385-4386), on the decay sub-element's decaying-particle wavefunction that physically *replaces* the core external one. See "THE OPERATIVE comma-decay write" below. The DiagramTag round-trip then preserves that combined-ME value; trim_diagrams' core-leg flag is upstream bookkeeping (diagram identity + the `decay` field) on pre-combination leg objects.

## THE OPERATIVE comma-decay onshell=True write — insert_decay:4385-4386
`HelasMatrixElement.insert_decay` (helas_objects.py:4087, called per decayed leg from `insert_decay_chains` :3980) is where the decay sub-diagrams are spliced onto the core. The decaying particle's own wavefunction in the decay sub-element is:
```python
final_decay_wfs = [amp.get('mothers')[1] for amp in decay_diag.get('amplitudes')]   # :4267 (Majorana branch) / :4357 (no-Majorana branch)
```
This `final_decay_wfs` definition appears in BOTH branches of an `if ... got_majoranas` split (4267 Majorana / 4357 simpler no-Majorana); the two branches converge before the onshell write, so the flag is set on whichever set was built. These `final_decay_wfs` directly **replace** the old core external wavefunction (diagram_wfs spliced at :4377-4380, then `replace_single_wavefunction`/`replace_wavefunctions` :4388-4398). Immediately after the diagram_wfs splice and BEFORE the wavefunction-replace:
```python
# Set the decay flag for final_decay_wfs, to
# indicate that these correspond to decayed particles
for wf in final_decay_wfs:
    wf.set('onshell', True)                                                          # :4385-4386
```
So the wavefunction that BECOMES the s-channel mother propagator in the *combined* ME gets onshell=True set HERE, in the combine layer — not copied from the core leg. This is the true source for the gForceBW=1 line.

### Why trim_diagrams' core-leg onshell=True does NOT ride leg→wf
The HelasWavefunction-from-Leg constructor copies onshell from a leg ONLY when it is False:
```python
if leg.get('onshell') == False:        # helas_objects.py:675-677
    self.set('onshell', leg.get('onshell'))   # Denotes forbidden s-channel
```
There is NO `== True` branch. Instead, a core final-state leg whose id ∈ decay_ids gets a separate `decay=True` field (helas_objects.py:683-684: `if self['state']=='final' and self.get('pdg_code') in decay_ids: self.set('decay', True)`) — used so MultiProcess does not merge processes that differ only in which legs will be decayed. So the two non-default onshell values reach the wavefunction layer by DIFFERENT routes:
- **onshell=False (`$`-forbidden):** copied leg→wf at construction (:675-677). The diagram-filter slice's flag rides in directly.
- **onshell=True (comma-decay):** NOT copied at construction; set explicitly at insert_decay:4386 on the decay sub-element's mother wf. (trim_diagrams' core-leg True feeds diagram identity + the `decay` field, not the combined-ME wf onshell.)
This asymmetry is the corrected core of this page.

## The flow feeding write_decayBW_file
`write_configs_file_from_diagrams` (export_v4.py:4037-4095, `ProcessExporterFortranME`) calls, per Helas diagram:
```python
stchannels = ...amplitudes[0].get_s_and_t_channels(ninitial, model, new_pdg)   # export_v4.py:4085-4086
...
s_and_t_channels.append([[s for s,t in stchannels if t != None][0], ...])      # :4094
```
That `s_and_t_channels` list is the exact object handed to `write_decayBW_file` (export_v4.py:4453 build, 4474-4476 emit). So the onshell write_decayBW_file reads is whatever `get_s_and_t_channels` put on the resulting (mother) leg.

## get_s_and_t_channels copies onshell from the helas wavefunction
`helas_objects.py:1926-2040` (`HelasWavefunction.get_s_and_t_channels`):
- `mother_leg = copy.copy(mother_leg)` (:1937) — the resulting s-channel leg is a copy of the mother_leg threaded down the recursion, carrying its `onshell`.
- Each contributing-mother leg is built copying the wavefunction's onshell: `'onshell': mother.get('onshell')` (:1966 for the 1-init-mother s/t case; :2034 for the 2-init t-junction case).
- **min() renumbering**: `legs[-1].set('number', min([l.get('number') for l in legs[:-1]]))` (:1983, :2039). The resulting s-channel mother leg is renumbered to the MINIMUM leg number among its contributors. This — not "internal ⇒ negative" by fiat — is the actual reason decayBW.inc mother leg numbers come out low/negative. (Supersedes the looser "internal s-channel mothers are negative" phrasing on decayBW-artefact.md / cautions.md §5: they ARE low-numbered, but because of this min() renumber.)

## The wavefunction's onshell originates from the vertex_id round-trip (DiagramTag)
The helas wavefunction's `onshell` is not free-standing — it is reconstructed from the diagram's *canonical config tag* (`CanonicalConfigTag`, a `DiagramTag` subclass in diagram_generation.py). Two halves:

1. **Encode** — `vertex_id_from_vertex` (helas_objects.py, the `last_vertex=False` branch, :476-482) packs the propagator leg's onshell into the vertex_id tuple:
   ```python
   return ((part.get('color'), part.get('mass'), part.get('width')),
           (vertex.get('id'), vertex.get('legs')[-1].get('onshell'),   # <-- onshell captured here (:480)
            vertex.get('legs')[-1].get('number')),
           loop_info)
   ```
2. **Decode** — `vertex_from_link` (helas_objects.py:517-535) writes it back onto the reconstructed resulting leg:
   ```python
   if len(vertex_id[1]) == 3:
       vertex.get('legs')[-1].set('onshell', vertex_id[1][1])          # :533-534
   ```
So `onshell` is part of the diagram's canonical identity: two diagrams that differ ONLY in a propagator's onshell are distinct config tags, and the flag survives the tag round-trip onto the s-channel mother leg. This is the precise mechanism behind "the comma-decay flag reaches write_decayBW_file" — the DiagramTag carries it.

Note the onshell is ALSO part of the leg-tag at helas_objects.py:172-178 (`if leg.get('onshell'): id = leg.get('id')` — an onshell leg is tagged by its specific PDG id, "since this specifies forbidden s-channel" per the :177 comment), and the module docstring (:70-71) notes the goal is "the right propagator written" for onshell s-channels (non-zero width and onshell True or None).

## get_base_vertex also carries onshell external→leg
`HelasWavefunction.get_base_vertex` (helas_objects.py:1780-1823) builds the resulting Leg with `'onshell': self.get('onshell')` (:1799) for the wavefunction's own leg, but forces `'onshell': None` (:1817-1819) for each *mother* leg it descends into. So onshell rides only on the resulting/propagator leg, never leaking onto the descent legs — consistent with write_decayBW_file reading `legs[-1]` (the resulting leg) only.

## DecayChainAmplitude.__init__ structural guards (diagram_generation.py:1377-1389)
Before any onshell flagging, each decay sub-process is wrapped as its own `DecayChainAmplitude(process, ...)` (:1386-1389) — the amplitude tree is self-recursive, mirroring the parser's comma/paren recursion. Three hard guards on each decay process:
- **No perturbation**: `if process.get('perturbation_couplings'): raise MadGraph5Error("Decay processes can not be perturbed")` (:1378-1379). (Distinct from, and in addition to, the parser-level comma+`[`/`]` block in cautions.md §1.)
- **is_decay_chain forced**: `process.set('is_decay_chain', True)` (:1381-1382).
- **Exactly one incoming**: `if not process.get_ninitial() == 1: raise InvalidCmd("Decay chain process must have exactly one incoming particle")` (:1383-1385). **Probe-confirmed** (MG5_aMC v3.7.1): `generate p p > t t~, t t~ > b b~ w+ w-` raises exactly `InvalidCmd : Decay chain process must have exactly one incoming particle`. A decay fragment must be a true 1→N decay; a 2→N fragment after a comma is rejected, not reinterpreted.

## Why a decay's diagrams can splice onto the core leg: is_decay_chain forces the parent last
Setting `is_decay_chain=True` (diagram_generation.py:1382) is not cosmetic — it changes diagram generation. For a decay leg `A > B C...`, `Amplitude.generate_diagrams` (docstring at diagram_generation.py:556-559) ensures "`BC...` combine first, giving `A=A` as a final vertex". The mechanism is `LegList.can_combine_to_0(..., is_decay_chain=True)` (base_objects.py:2258-2274): clustering to the null vertex is allowed ONLY when the initial leg (marked `from_group == None`) is still unclustered, "since we want this to stay until the very end" (:2269-2272; 2259-2266 is the method docstring). So the decaying particle's wavefunction is the LAST evaluated in the decay sub-amplitude — which is precisely what lets that wavefunction be glued onto the core's matching final-state (onshell=True) leg when the combined matrix element is built. The exactly-one-incoming guard guarantees there is a single such initial leg to hold back.

## decay_ids provenance
`decay_ids` (the set that gates onshell=True in trim_diagrams) is built from the FIRST leg of each decay sub-amplitude's process:
```python
decay_ids = sum([[a.get('process').get('legs')[0].get('id')      # diagram_generation.py:1392-1394
                  for a in dec.get('amplitudes')] for dec in self['decay_chains']], [])
decay_ids = set(decay_ids)
```
`legs[0]` is the single incoming particle (guaranteed by the exactly-one-incoming guard above). The convenience method `get_decay_ids` (diagram_generation.py:1508-1520) does the same via `get_initial_ids()[0]`. So "id ∈ decay_ids" in trim_diagrams means "this PDG is the incoming particle of some declared comma-decay" — that is what makes a matching core final-state leg get onshell=True.

## Why this matters for answering decayBW questions
- The onshell value in decayBW.inc is determined at *amplitude/helas build* time and frozen into the config tag — it is not re-derived at output time. write_decayBW_file is a pure read of `legs[-1].onshell`.
- The mother leg numbering (min of contributors) is a config-decomposition artefact, not a property of the decayed particle — don't try to map a decayBW leg number to a command-line particle; read configs.inc.
- A 2→N fragment after a comma never reaches onshell flagging at all — it errors at __init__ before trim_diagrams.
