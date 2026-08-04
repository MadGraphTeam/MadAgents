---
description: Leg/MultiLeg polarization value whitelist (list_of_allowed_polarizations) enforced in base_objects filter, the canonical allowed helicity-code set, and the value->shorthand reverse render
---

# Polarization value whitelist + reverse render (`base_objects.py`)

A second validation layer, downstream of the `extract_process` letter loop: every
value placed into a leg's `'polarization'` list is checked against a hard whitelist
when the dict is set. This is independent of the letter-mapping and placement layers.

## The whitelist (`Leg.list_of_allowed_polarizations`)
`$MADGRAPH_INSTALL/madgraph/core/base_objects.py:2098` (v3.7.1):
```
list_of_allowed_polarizations = [-1, 1, 2,-2, 3,-3, 0, 4, 5, 6, 7, 9, 99]
```
Comment (2095-2097): "List of allowed helicity polarizations for a fermion or vector
boson. See [arXiv:1912.01725] for definitions (fermions,vectors) and
[arXiv:2512.10015] for extensions (vectors)".

### Enforcement
- `Leg.filter` (2143-2150): `polarization` must be a `list`; each element `i` must be
  in `list_of_allowed_polarizations` else
  `PhysicsObjectError("%s is not a valid polarization" % str(value))`.
- `MultiLeg.filter` (2330-2337): identical check referencing `Leg.list_of_allowed_polarizations`.
- `fks_tag.MultiTagLeg.filter` / `fks_tag.TagLeg.filter` (`madgraph/fks/fks_tag.py:42-49`,
  `71-78`): only special-case the `is_tagged` key, then **delegate to
  `super().filter()`** — i.e. `MultiLeg.filter` / `Leg.filter`. So the polarization
  whitelist is enforced **identically on the tagged/FKS leg classes** too; gate 4 has
  the same reach on every leg construction path.
- This fires when the leg dict is constructed/set in `extract_process` (the
  `MultiLeg`/`MultiTagLeg({'polarization': polarization})` build at
  madgraph_interface.py:5233-5240), so it is effectively parse-time — AND **again at
  generation time** when `ProcessDefinition` is expanded into concrete
  `Leg`/`TagLeg`s (`diagram_generation.py:1744-1782`, see
  `pol-generation-expansion.md`); each expanded leg re-runs `filter`. The value
  already passed at parse, so this re-check never fires in practice — it is a second
  copy of the same backstop.

### Mapping the whitelist back to the letters (cross-ref pol-letter-mapping.md)
- `1`,`-1` — R / L / T-components / explicit ±1
- `0` — longitudinal (`0`)
- `2,-2, 3,-3` — only reachable via explicit numeric `+2`/`-2`/`+3`/`-3` (the letters
  never emit these; spin-2+ helicities). `abs > 3` is already rejected earlier in the
  letter loop, so 2/3 are the only multi-unit values that survive.
- `4` G (metric), `5` H (Theta), `6` Q (qq), `7` W (Ward), `9` S (scalar=aux+width),
  `99` A (auxiliary) — the spin-3-only exotic codes.
- So the whitelist is the union of {everything the letter loop can emit} ∪ {explicit
  ±2,±3}. Anything outside it is a hard `PhysicsObjectError`, distinct from the
  letter-loop's `InvalidCmd('Invalid Polarization')`.

## Reverse render (display only)
Multiple `get_*` string builders render a polarization list back to shorthand for
process display (e.g. base_objects.py:3187-3195, 3322-3330, 3417-3425, 3471-3479,
3533+). The canonical reverse map used:
- `[-1,1]` or `[1,-1]` → `{T}`
- `[-1]` → `{L}`
- `[1]` → `{R}`
- anything else → `{%s}` with comma-joined raw codes (e.g. `{4}`, `{99}`, `{0}`),
  or in some builders `m`-prefixed negatives (3479: `str(p).replace('-','m')`).
- Display-only; does not affect physics. Note the round-trip is lossy in spirit:
  `{L}` on a spin-1 leg renders back as `{L}` even though it meant left (-1), and a
  raw `[-1]` from any spin also renders `{L}`.

## Caution
- The whitelist is the authoritative set of helicity codes the rest of MadGraph will
  accept on a leg. If a future letter or numeric path produced a value not in this
  list, it would fail here even after passing the letter loop — the two lists must
  stay in sync. Currently they do (letter loop caps at abs≤3 and the exotic codes
  4/5/6/7/9/99 are all present).
