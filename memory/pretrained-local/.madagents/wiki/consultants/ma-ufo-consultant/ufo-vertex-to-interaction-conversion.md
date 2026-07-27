---
description: How UFOMG5Converter.add_interaction turns one UFO Vertex into MG5 Interaction(s) — ghost/Goldstone-ref drop, fermion-flow checks, order-tuple splitting, '1'-order ban, non-QCD-gluon counter.
---

# UFO Vertex -> MG5 Interaction (import_ufo.py, v3.7.1)

`UFOMG5Converter.add_interaction` (`$MADGRAPH_INSTALL/models/import_ufo.py:1773`), called once per `all_vertices` entry (l.605-606). Complements `ufo-model-file-structure.md` (Vertex class) and `ufo-loader-pipeline.md` (Stage 1 summary). The non-obvious part: one UFO Vertex can become several MG5 `Interaction`s, and several silent drops/hard errors happen here.

## Silent drop: vertex touching a removed particle (l.1779-1781)
`particles = [self.model.get_particle(p.pdg_code) for p in interaction_info.particles]`; then `if None in particles: return`. A vertex referencing a particle that `add_particle` dropped (a Goldstone in unitary gauge, a ghost in a tree model — see `ufo-loader-gauge-and-pickle.md`) is silently skipped. This is WHY the unitary-gauge sm keeps no Goldstone/ghost vertices, distinct from the later empty-coupling pruning.

## Fermion-flow validation (l.1789-1808)
- `nb_fermion == 2`: ALOHA `check_flow_validity` runs once per new Lorentz name (cached in `self.checked_lor`); a bad flow raises `InvalidModel`.
- `nb_fermion > 2` (4/6-fermion): a self-conjugate (Majorana) fermion in the vertex raises `InvalidModel("Majorana can not be dealt in 4/6/... fermion interactions")` (l.1798). For >2 fermions a per-coupling `coupling_sign` is computed from `get_fermion_flow`/`get_sign_flow` and prefixed onto the coupling name.

## One Vertex -> N Interactions, keyed by coupling-order (l.1816-1860)
Loops `interaction_info.couplings.items()` (key = `(color_idx, lorentz_idx)`). For each coupling, `order = tuple(coupling.order.items())` (l.1831). An `order_to_int` dict groups by that order tuple:
- same order tuple already seen -> just add `{key: signed_coupling_name}` to that interaction's couplings.
- new order tuple -> build a fresh `base_objects.Interaction` with a new sequential `id`, the particles, lorentz-name list, that one coupling, `orders`, color, `type`, `loop_particles`; append to `self.interactions`.

So a single UFO vertex carrying couplings of different coupling-order content splits into multiple MG5 interactions (one per distinct order signature).

## Hard error: coupling order '1' (l.1832-1835)
`if '1' in coupling.order: raise InvalidModel("Some couplings have '1' order. This is not allowed in MG. Please defines an additional coupling to your model")`. A UFO order literally named `'1'` is forbidden.

## non-QCD gluon emission counter (l.1838-1842)
If pdg 21 (gluon) is among the vertex particles AND the coupling has no `'QCD'` order AND no color-singlet (color 1) particle is present, `self.non_qcd_gluon_emission += 1`. Consequence after all vertices added (l.612-618):
```
logger.critical("Model with non QCD emission of gluon (found %i of those)...")
self.model['allow_pickle'] = False
self.model['limitations'].append('MLM')
```
Non-obvious: it's `logger.critical` (NOT warning), it DISABLES pickling for that model, and tags an `MLM` limitation (restricts LO dynamical scale + MLM matching/merging). [runtime critical-log text — confirm via probe before quoting as fired output]

## Post-pass pruning (l.630-633)
After all vertices (and CT vertices for loop models) are added, `optimise_interaction` runs on each, then any interaction with empty `couplings` is removed. This is the empty-coupling pruning my structure page references — separate from the ghost/Goldstone drop above.

## optimise_interaction — Stage-1 coupling collapse + Lorentz merge (l.686)
This is the Stage-1 `UFOMG5Converter.optimise_interaction` (l.686), distinct from `RestrictModel.optimise_interaction` (l.3102, restriction slice). Two transforms, both BEFORE any param_card is read — it keys purely on the raw UFO `Coupling.value` STRING:
1. **Identical-coupling collapse + ZERO deletion** (l.691-708): on first call it builds `self.iden_couplings`, a defaultdict over `str(coupling.value)`; couplings sharing an identical value-string are mapped to a single representative (the first), and `coups['0']` is seeded with `'ZERO'`. Per interaction, each coupling in `iden_couplings` is replaced by its representative, and any coupling that resolves to `'ZERO'` is `del`-eted from the interaction. NOTE: this is NOT the restriction-slice identical-coupling detection — that one (l.2525 `detect_identical_couplings`) keys on numerically-evaluated param_card values to 6 digits; THIS one keys on the literal source string before evaluation. A coupling literally `value='0'` is dropped here regardless of param_card. (The deeper string-vs-number principle this is an instance of: `ufo-loader-keys-on-value-strings-not-numbers.md`.)
2. **Same-coupling-across-Lorentz merge** (l.711-773): if one coupling appears for multiple Lorentz indices at the SAME color index, those Lorentz structures are summed into a NEW Lorentz via `add_merge_lorentz` (l.1187) -> `add_lorentz` (l.1920). New name = longest common prefix of the merged names + a counter (fallback base `'LMER'`); new structure = `' + '.join(structures)`; spins taken from the first; formfactors concatenated. The old `(color,lor)` coupling keys are deleted and one `(color, new_lor)` added. Skipped if spins differ (`logger.warning('not all same spins...')`) or if any merged Lorentz has `structure=='external'`.

PROBE-CONFIRMED (sm under restrict_default): produces ZERO merged-Lorentz names — the merge path is conditional and sm never triggers it (its raw UFO Lorentz survive one-to-one, no `LMER`/prefix-merged names in the loaded model). So merged-Lorentz artifacts are MODEL-DEPENDENT, not a universal load artifact; do not expect them unless a model genuinely shares one coupling across multiple Lorentz at one color.

## treat_color — color-string -> ColorString, with rep-dependent index order (l.1946)
Converts each UFO `Vertex.color` string into a `color.ColorString` object. Non-obvious per-term handling, driven by the particles' integer color charge:
- `Identity(i,j)` between two color-8 particles -> `color.Tr(i,j)` AND multiplies the color coefficient by 2 (`factor *= 2`, l.1988).
- `Identity(i,j)` between sextets (color ±6) -> `color.T6(i,j)` (index order flips for -6).
- `Identity(i,j)` between triplets (color ±3) -> `color.T(...)`, with index order chosen from the 3-vs-3bar assignment in `color_info` (from `find_color_anti_color_rep`); 3 -> `T(second,first)`, 3bar -> `T(first,second)` (l.2009-2012). If the rep is still unknown it retries `find_color_anti_color_rep` once, then falls back to the particle's own color sign.
- Summed-index convention: `'i<n>'` tokens -> `-<n>` (l.2021-2022); all indices then shifted by -1 (0-based) before eval.

NEW InvalidModel site (not previously cataloged): `Identity` between two particles in the SAME representation raises `InvalidModel('UFO model have inconsistency ... both fermion are in the same representation')` for color ±6 (l.1959-1963) and for color ±3 when `color_info` agrees they match (l.1964-1979). Also `MadGraph5Error("Unknown use of Identity ...")` (l.2014) for an unexpected color.

## Color-flow inference — find_color_anti_color_rep (l.1651)
Before color strings are converted, the loader infers which fermions sit in 3 vs 3bar by scanning EVERY 3-particle vertex's color string. For a vertex with two triplet particles it reads the `T(a,b,c)` / `Identity(i,j)` index pattern to decide which particle is color (3) and which is anticolor (3bar), accumulating into `output[pdg]= 3|-3`. A particle assigned BOTH 3 and 3bar across vertices raises `InvalidModel('Particles %s is sometimes in the 3 and sometimes in the 3bar representations')` (l.1737/1745) — the 3/3bar-inconsistency error my validation-gates page lists, now with its detection algorithm. `detect_incoming_fermion` (l.1752) is the parallel pass that infers fermion-flow direction from `F F~ X` vertices and raises the odd-fermion-count / incoherent-flow errors.

## Gauge-3 (FD) extra step (l.608-609)
`if aloha.unitary_gauge == 3: self.merge_all_goldstone_with_vector()` — only in FD gauge (gauge 3 = "Feynman Diagram gauge", pickle suffix `_FDG`; see `ufo-loader-gauge-and-pickle.md` for the naming). Tree/unitary/Feynman(0) do not call this.

## CORRECTION to ufo-loader-pipeline.md
That page said non-QCD-gluon-emission models "disable pickling and flag MLM limitation" via a generic note; the exact mechanism is the `logger.critical` + `allow_pickle=False` + `limitations.append('MLM')` block at l.612-618, driven by the per-coupling counter here. Both pages now agree.
