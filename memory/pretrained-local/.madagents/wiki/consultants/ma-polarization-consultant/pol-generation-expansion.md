---
description: Generation-time handling of the parsed polarization list in diagram_generation — massless-boson 0-strip, sole-0 process drop (NoDiagramException), polarization-aware FS dedup, the MultiLeg->Leg expansion fork
---

# Polarization at generation time (`diagram_generation.py`)

The parse/construction gates (see `pol-validation-pipeline.md`) stop after `do_add`.
But the parsed `polarization` list this slice produces is consumed once more at
**diagram-generation time** (pipeline stage 3), when `ProcessDefinition` (a list of
`MultiLeg`s) is expanded into concrete `Leg`-list `Process` objects. That expansion
**mutates and can drop** the polarization list — so a spec that parses cleanly can
still vanish here. Source: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py`
~1700-1800 (v3.7.1), inside the `ProcessDefinition`-expansion loop. All
probe-confirmed (v3.7.1).

## Where the polarization list is read (1706-1718)
- `islegs_orig` / `fslegs` split by `leg['state']` (1706-1709).
- `polids = [tuple(leg['polarization']) for leg in ... if state==True]` (1715-1716)
  — final-state polarization tuples, used for dedup below.
- `masses = {id: model.get_particle(id).get('mass') for leg ... for id in leg['ids']}`
  (1718) — the per-PID mass attribute *string* (`'ZERO'` or a symbolic name), reused
  for the 0-strip test. (Same mass-attribute-string semantics as the NLO placement
  gate, `pol-placement-restrictions.md` — numeric value is never consulted.)

## The MultiLeg -> Leg expansion fork (1735-1782)
For each `itertools.product` over the multiparticle ids, concrete legs are built —
and the leg **class** forks on whether tagging is active:
- no tags → `base_objects.Leg({'id':..,'state':..,'polarization': <leg>['polarization']})`
  (1744-1745 initial, 1776-1778 final).
- tags → `fks_tag.TagLeg({..., 'polarization':..., 'is_tagged': tag})`
  (1740-1742 initial, 1780-1782 final).
The polarization list is copied verbatim from the `MultiLeg`/`MultiTagLeg` onto each
expanded `Leg`/`TagLeg`. Both leg classes re-run `filter` on assignment, so the
value-whitelist (gate 4, `pol-allowed-values.md`) is re-enforced here too — but the
values came from the already-validated MultiLeg, so it never fires in practice.

## Massless-boson `0`-strip + sole-0 process DROP (1748-1755, 1788-1794)
Comment in source: "check for longitudinal photon". For every expanded leg:
```
if 0 in l['polarization'] and masses[l['id']] == "ZERO":
    l['polarization'] = [x for x in l['polarization'] if x != 0]   # strip the 0
    if len(l['polarization']) == 0:
        invalid = True; break                                       # whole combo dropped
if invalid: continue
```
- Initial-state legs: 1750-1755. Final-state legs: 1790-1794 (uses
  `.remove(0)` form, same effect).
- **`0` is silently removed** from any massless-boson leg's polarization list at
  generation. This realizes the parse-time `logger.info('"0" (longitudinal)
  polarization detected for massless boson.')` + comment "those mode will be bypass
  at generation time" (madgraph_interface.py:5179-5180, see `pol-letter-mapping.md`).
  The *bypass site* is HERE, not at parse and not at integration.
- If stripping `0` empties the list (i.e. `0` was the **only** requested
  polarization on a massless boson), `invalid=True` and the entire id-combination is
  **skipped** (`continue`). If every combination is skipped → no amplitudes →
  generation raises a generic **`NoDiagramException`**, NOT a polarization error.

### Probe matrix (v3.7.1, confirmed)
- `generate e+ e- > a{0} z` → parse-time `logger.info` longitudinal-massless, then
  generation **drops the a-leg's only pol** → `NoDiagramException : No amplitudes
  generated from process ... e+ e- > a{0} z ... Please enter a valid process`.
  (A `{0}`-only request on a massless boson dies as "no diagrams", not as an
  invalid-polarization error — a real trap: the error text points nowhere near
  polarization.)
- `generate e+ e- > a{0R} z` → photon pol `[0,1]`; the `0` is stripped (massless),
  `[1]` survives → "Process has 2 diagrams ... 1 processes". Same logger.info, but
  the process LIVES because R remained. Clean contrast to the sole-`0` case.
- `generate e+ e- > a{0} a` → never reaches generation: dies at gate 5
  (`check_polarization`) because `a{0}` (PID 22 polarized) + unpolarized `a` (PID 22)
  is the ambiguous mix → `InvalidCmd: Not supported syntax of type p p > Z{T} Z`.
  (Shows the parse gates still fire first; the 0-strip only matters for specs that
  survive to stage 3.)

## Polarization-aware final-state dedup (1762-1771)
Final-state multiparticle combinations are deduped on a **polarization-aware** key:
```
red_fsidlist = set()                       # 1762
for prod in itertools.product(*fsids):
    tag = sorted(zip(prod, polids))        # 1765-1766
    if tuple(tag) in red_fsidlist: continue  # 1768
    red_fsidlist.add(tuple(tag))           # 1771
```
The dedup tag pairs each final-state id with its polarization tuple, so two
combinations that differ ONLY in polarization are NOT collapsed. (Mirrors the
polarization-aware identity key in `identical_particle_factor`,
`pol-symmetry-factor.md` — both keep polarization in the identity, just at different
stages: this one for combinatorial dedup, that one for the 1/n! factor.)

## Cautions / boundary
- The 0-strip keys on the mass **attribute string** == `'ZERO'`, exactly like the
  NLO placement gate. A massless boson in a model where its mass attr is `'ZERO'`
  (e.g. photon, gluon) gets stripped; a massive boson keeps its `0`. Model
  restriction governs which attr a particle carries.
- The drop is **silent at the polarization level** — the only user-visible signal of
  a sole-`0` massless drop is `NoDiagramException`. Diagnosing it requires knowing
  this strip happened; the error text does not mention polarization.
- What the *surviving* polarization codes mean for the amplitude (how the helicity
  sum/selection is computed once the Leg carries `[1]`, `[4]`, etc.) is HELAS /
  numerical territory — out of slice. This page owns only: the parsed list is
  re-read at generation, `0` is conditionally stripped, and the process is dropped
  if that empties it.
- A `,` *inside* `{}` combined with a glued following name can die earlier at a
  process-format token-split gate (`a{0,R} z` → `InvalidCmd: wrong format for "R} z"
  this part requires one or two symbols '>'`) — the comma confuses process-string
  splitting before `extract_process`. The token-splitting is process-syntax-slice
  territory; noted here only because the symptom appears on a polarization spec.
  Glued `{0R}` (no comma) parses fine.
