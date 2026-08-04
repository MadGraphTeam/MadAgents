---
description: What the model actually contains (particles, vertices, interactions), or something you expected in it is missing.
---

# Model content — declare → convert → prune → augment lifecycle

"Models, particle content, and interactions" fans across the five model-load-stage slices along the lifecycle of a particle/vertex (declare → convert → prune → augment). Same shape as `decay-widths-lifecycle`, an instance of `config-value-lifecycle-layers`. Complements `pipeline-stage-map.md` stage 1 (flat owner map) with the *content-modification* view + the removal trap. Dispatch behaviour only; MadGraph facts live in `../consultants/<name>/` — confirm one cited file:line before adopting a page as evidence.

## Stages

- **DECLARE (UFO files)** → `ma-ufo-consultant` — object-level grammar of the *authored* declarations: `Particle`/`Parameter`/`Vertex`/`Lorentz`/color-string objects; the sparse vertex `couplings` dict keyed `(color_idx, lorentz_idx)`; the `structure`/color DSLs; `coupling_orders`. Page `ufo-declaration-object-grammar.md` (authored-structure sibling to the consumption pages `ufo-vertex-to-interaction-conversion`/`ufo-coupling-orders-and-propagators`). The ghost-vs-Goldstone two-mechanism distinction and mass/width-is-a-Parameter-reference live there.

- **CONVERT (UFO objects → internal base_objects)** → `ma-model-loader-consultant` — the `UFOMG5Converter` interior: `add_particle`/`add_interaction` build internal `base_objects.Particle`/`Interaction`; **lazy antiparticle synthesis** (`model['particles']` is HALF the `particle_dict`); NO process-reachability prune at load. Page `ufo-to-internal-object-conversion.md`. **This is the only stage that removes a particle** (gauge-driven goldstone handling, conversion time).

- **PRUNE (restriction)** → `ma-restriction-consultant` — `RestrictModel` removes zero-coupling interactions, collapses identical couplings (identifier-collapse, topology/count unchanged), sets masses/widths → ZERO. **Drops NO particle** — an orphaned particle (all its vertices pruned) stays in the model, appearing in no diagram. Pages `remove-interactions.md` / `detect-identical-couplings.md` / `goldstone-vector-merge.md` (the last marks the unique conversion-time removal site).

- **AUGMENT-loop (CT structure)** → `ma-nlo-model-consultant` — a loop model carries EXTRA content beyond a tree model: CTVertex objects (R2/UV; `couplings` keyed by a 3-tuple `(color, lorentz, loop_group#)` — color FIRST, same convention as the tree `Vertex` 2-tuple `(color, lorentz)`; proven `import_ufo.py:1635`+`:1821`) AND particle-attached wave-function CTs (`particle.counterterm`/`loop_particles` → synthesized `UVWfct_*`). Pages `ct-files-and-vertex-types.md` / `particle-attached-wavefunction-CT.md`. Bundled loop-model SET is build-volatile — live-scan with the consumer predicate (`perturbative_expansion > 0`), do NOT quote a count from this index.

- **AUGMENT-EFT (effective vertices)** → `ma-eft-consultant` — an EFT model adds dim-6/dim-8 effective vertices gated by external Wilson-coeff params and a new coupling-order (NP/DIM6/FCNC); the coupling value literally = coeff/Λ². Page `eft-model-content-wilson-coupling-vertex.md`. WHICH operators survive is restriction's `smeft-restrict-operator-selection.md`. Broader EFT routing → `eft-smeft-fanout.md`.

## Central routing trap — "a particle / vertex / coupling disappeared"

- **A particle vanished between the UFO files and the loaded model** → it is the CONVERT stage's gauge-driven goldstone handling (model-loader), NOT the restrict card. Route to model-loader `ufo-to-internal-object-conversion.md` + restriction `goldstone-vector-merge.md` (marks the unique removal site). The triggering gauge: read the goldstone-vector-merge page — do NOT quote a gauge from this index (correctable-claim).
- **A vertex/interaction disappeared** → restriction `remove-interactions.md` (zero-coupling prune), or coupling-order `default-unset-couplings.md` (silent `<=N` injection at process spec — see `coupling-order-nlo-bracket-seams.md`).
- **An orphaned particle (still listed, but in no diagram)** → expected: restriction pruned all its vertices but kept the particle; the absence bites at diagram generation, not load.
- **A coupling/parameter changed value** → restriction merge/fix (`parameter-fixing-and-merging.md`, `detect-identical-couplings.md`), then the card stage (`config-value-lifecycle-layers.md`).

## Dispatch ordering

- "What does model X actually CONTAIN" → ufo (declared) → model-loader (converted + lazy antiparticles) → restriction (pruned) → nlo-model/eft (augmented).
- "Why is X MISSING" → walk convert (gauge drop) then prune (interaction removal), asking at each stage which dropped it. Restriction is never the answer for a missing *particle*.
