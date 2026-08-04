---
description: The loader as a validation gate — a UFO that imports as Python can still be hard-rejected at conversion (InvalidModel/UFOImportError/AssertionError) or have parts silently dropped. Enumerates the hard-reject contracts and the silent-drop cases, with the exception type each raises.
---

# UFO loader validation gates (import_ufo.py, v3.7.1)

Principle: **importing as Python is necessary but not sufficient.** A syntactically-valid UFO still passes through Stage-1 `UFOMG5Converter` (`$MADGRAPH_INSTALL/models/import_ufo.py`, class at l.461), which (a) HARD-REJECTS on broken contracts and (b) SILENTLY DROPS pieces that don't fit the loaded gauge/structure. "It imports but errors / it imports but loses particles" almost always lands here. This page is the catalog; the deep-dives (`ufo-vertex-to-interaction-conversion.md`, `ufo-loader-gauge-and-pickle.md`) cover individual mechanisms.

The exception TYPE matters for diagnosis: `InvalidModel` and `UFOImportError` give a readable message; a bare `assert` gives an opaque `AssertionError` with no guidance.

## Hard rejects — grouped by contract

### (a) Name / block hygiene — `load_model` (l.530-556)
- `InvalidModel('LHABlock should be single word ...')` (l.539): an external param's `lhablock` containing whitespace.
- `InvalidModel('name %s define multiple time ...')` (l.542): two parameters share a name.
- CTparameter name-clash check for loop models (l.534-556 region).

### (b) The aS <-> SMINPUTS#3 contract — `check_model_aS` (def l.891, body l.894-906)
BIDIRECTIONAL, both `UFOImportError`:
- A parameter literally named `aS` MUST have `lhablock` SMINPUTS and `lhacode == [3]`, else "aS parameter should be assigned to SMINPUTS#3" (l.897, l.900).
- Conversely, ANY external SMINPUTS#3 param whose name is not in `['AS','ALPHAS']` -> "SMINPUTS#3 parameter should be aS" (l.905).
So you cannot park something else in SMINPUTS#3, and you cannot name your strong coupling `aS` while putting it elsewhere. (Undocumented elsewhere in this subtree; commonly bites home-grown/edited UFOs.)

### (c) Particle-field completeness — `add_particle` (l.1266-1328)
`nb_property` counts the required particle fields as they are consumed; `assert(10 == nb_property)` (l.1328). A missing/extra recognized field trips a bare **AssertionError** (not InvalidModel) — opaque failure. This is the 10-required-fields check the structure page references.

### (d) Color / fermion structural consistency — `add_interaction` and color detection
- `InvalidModel('Particles %s is sometimes in the 3 and sometimes in the 3bar ...')` (l.1737, l.1745): a particle used inconsistently as 3 vs 3bar across vertices.
- `InvalidModel('Odd number of fermion in vertex: %s')` (l.1762): a vertex with an odd fermion count.
- `InvalidModel('%s has not coherent incoming/outcoming status ...')` (l.1766): inconsistent fermion flow across interactions.
- `InvalidModel("Majorana can not be dealt in 4/6/... fermion interactions")` (vertex page, l.1798): self-conjugate fermion in a >2-fermion vertex.
- `InvalidModel("Some couplings have '1' order ...")` (l.1832-1835): a coupling-order literally named `'1'`.
- ALOHA `check_flow_validity` on a 2-fermion Lorentz can raise `InvalidModel` (vertex page).

## Silent drops — no error, pieces just disappear
Distinct failure mode: the model loads "successfully" but with fewer particles/vertices than the files declare. Easy to misread as a bug.
- Ghosts (UFO spin<0) dropped for tree models; Goldstones dropped in unitary/axial gauge — `add_particle` l.1242 / l.1245-1246 (see `ufo-loader-gauge-and-pickle.md`).
- Any vertex referencing a dropped particle is silently skipped — `add_interaction` l.1779-1781 (`if None in particles: return`) (see `ufo-vertex-to-interaction-conversion.md`).
- Interactions whose `couplings` dict emptied after order-splitting are pruned post-pass (l.630-633).

## Soft signals (load proceeds, log only)
- `logger.critical` for scalar-colored models (l.577, sets `limitations.append('fix_scale')` l.579; flag set in `add_particle` l.1330-1333) and for non-QCD gluon emission (l.612-618, also sets `allow_pickle=False` + `limitations.append('MLM')`; see vertex page). [log text is runtime output — confirm via probe before quoting]
- `logger.warning('coupling ... has direct dependence in aS but ... QCD order set to 0 ...')` in Stage-2 (see `ufo-expression-shortening-and-event-dependence.md`).

## Diagnostic rule
- `AssertionError` from import -> almost always the l.1328 field-count check (a particle is missing/has an unexpected field).
- `UFOImportError` mentioning aS/SMINPUTS -> the l.890-906 contract.
- `InvalidModel` -> read the message; it names the contract (3/3bar, fermion count/flow, '1' order, lhablock, duplicate name).
- Loads but fewer particles than declared -> gauge drop (Goldstone/ghost), not an error.

The exception-type-to-line mapping above is a static code-path fact; the actual message string printed at runtime should be probe-confirmed before quoting verbatim.
