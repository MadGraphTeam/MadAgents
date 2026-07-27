---
description: The topology-fingerprint diagnostic principle — answer "what did enumeration actually build / why isn't it what I expected" by per-channel diagram count + a characteristic vertex-call grep in matrix1_orig.f, never by "it ran clean"; the Trying/Process-has log pair is the count's runtime shadow
---

# Enumeration topology fingerprint — count + vertex-grep, never "it ran"

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` + `base_objects.py` (v3.7.1). This page names the diagnostic METHOD; the source INVARIANT under it (enumeration keys off vertex PRESENCE not coupling VALUE, leg-counting applicability, the gg/WWWW zero-diagram cases) is `vertex-presence-not-value-enumeration.md`. One worked example (inclusive-vs-chain FFV1 fingerprint) is retained inline below — derive per process for any other topology; do NOT read it as a per-process count table.

## The principle
For any "the enumeration did something other than I expected" question — wrong subprocess set, wrong cross section, a process that gives nothing, a coupling I zeroed that changed nothing — the discriminator is a **topology fingerprint**:
1. **per-channel diagram COUNT** (`INFO: Process has N diagrams`, and the `Total: M processes with K diagrams` roll-up), and
2. a **characteristic vertex-call GREP** in the generated `SubProcesses/P*/matrix1_orig.f` (`grep -cE 'CALL <VVV>'`).

A clean exit-0 `generate`/`output` is SILENT across the entire family of enumeration surprises — it is never the evidence. The count tells you HOW MANY graphs were built; the vertex-grep tells you WHICH graphs. Together they fingerprint the actual enumeration intent/cause.

## Why the count is the discriminator (source spine)
Enumeration keys off vertex PRESENCE (ref-dict PDG-tuples), never coupling VALUE — `InteractionList.generate_ref_dict` (`base_objects.py:983-999`) → `generate_dict_entries` (`:861-891`) keys `ref_dict_to0/to1` purely from `tuple(sorted(pdg_codes))` + interaction id, reading neither `couplings` nor a param card. So the count is fixed by the model's *interaction topology*, independent of any numerical coupling value or card edit. That is exactly why the count separates the failure families a clean run conflates (full detail: `vertex-presence-not-value-enumeration.md`).

## The count's runtime shadow: the Trying / Process-has log pair
- `generate_diagrams` logs `INFO: Trying %s` (`diagram_generation.py:636`) for EVERY crossing that passes the conservation pre-checks and reaches the recursion.
- `INFO: Process has %d diagrams` is GUARDED `if res and not returndiag:` (`:837-838`) — emitted ONLY when the recursion returned a non-empty `res`.
- So a member that enumerates to ZERO prints `Trying ...` but NO `Process has ...` line, and is silently absent from the `Total:` roll-up (the silent zero-diagram-member drop, `multiprocess-crossing-mirror.md:44-50`). Reading the two log lines as a PAIR is the count fingerprint without opening the matrix: `Trying` present + `Process has` absent = an empty member.

## The discrimination table (what the fingerprint separates)
The same clean exit-0 surface hides at least these distinct enumeration outcomes; only the count + grep tell them apart:

| Cause | Diagram count | matrix vertex-grep | log signature |
|---|---|---|---|
| restriction REMOVED the vertex (restrict_default zero) | DROPS (member empty / NoDiagramException) | the vertex's call absent | `Trying` w/o `Process has` (or NoDiagramException) |
| coupling VALUE zeroed (param-card cq=0, decoupled-μ) | UNCHANGED | call still present | identical to baseline; only σ collapses at launch |
| present vertex, no matching leg cluster (leg-counting; WWWW with 2 W legs; gg→colorless) | that vertex contributes 0 / member empty | that call's count 0 | `Trying` w/o `Process has` for the empty member |
| INCLUSIVE ME vs RESONANT chain, same final state | inclusive ≫ chain (per-channel, 4-lepton) | photon FFV1 present (nonzero) vs absent (0) | inclusive shows all channels; chain shows production×decays |

### The one retained worked example — inclusive-vs-chain FFV1 fingerprint (example for THIS one topology; derive per process for anything else)
PROBE-anchored (MG5_aMC v3.7.1, `sm`), the 4-lepton `e+ e- mu+ mu-` final state written two ways:
- Inclusive `generate p p > e+ e- mu+ mu-` → `Amplitude.generate_diagrams` enumerates the FULL tree set per partonic channel (doubly-resonant ZZ + single-resonant Zγ* + γ*γ* + non-resonant): LARGE per-channel count + **nonzero `CALL FFV1`** in `SubProcesses/P1_qq_llll/matrix1_orig.f`.
- Chain `generate p p > z z, (z>e+e-), (z>mu+mu-)` → PRODUCTION graphs (`p p > z z`) × the specified decays; leptons FORCED onto Z legs, no photon graph possible: SMALL production per-channel count + **0 `CALL FFV1`** (a STRUCTURAL absence, not a drift-prone count) / nonzero `CALL FFV2` in `P1_qq_zz_z_ll_z_ll`.
- **Why FFV1 == photon (grounds the fingerprint, in-slice):** the inclusive `CALL FFV1*` lines carry mass `ZERO` and couplings `GC_2`/`GC_3`; `$MADGRAPH_INSTALL/models/sm/couplings.py:12-22` gives `GC_1=-(ee*i)/3.`, `GC_2=(2*ee*i)/3.`, `GC_3=-(ee*i)`, all `order={'QED':1}` = `±ee×(charge fraction)`, the electric-charge photon-fermion coupling. A massless FFV1 propagator with an `ee`-proportional coupling IS the photon; the Z vertex appears as FFV2/FFV5 with a massive propagator. So nonzero FFV1 (inclusive) vs 0 FFV1 (chain) = the inclusive form really enumerates the Zγ*/γ*γ* graphs the chain excludes. CONFIRMED, not inferred.

Read the exact counts fresh per process (`Process has N diagrams` + `grep -cE 'CALL FFV1'`) — DERIVE from the requested final state and topology, never cache the integers.

## How to apply
When a user reports an enumeration surprise — "fewer/more diagrams than I expected," "I zeroed X and σ didn't move / moved to 0," "I asked for ZZ→4l but got a different σ," "this process gives nothing":
- **Get the count first** (`Process has` lines + `Total:` roll-up), or the `Trying`/`Process has` pair if no matrix yet.
- **Then grep the discriminating vertex** in `matrix1_orig.f` (FFV1=photon, the operator's `GC_*`, the BSM vertex).
- **Never accept "it ran clean" as scope evidence** — exit-0 is degenerate across the whole table above.

The retained inclusive-vs-chain example above is the last table row; `vertex-presence-not-value-enumeration.md` grounds the first three rows (removal vs value-zero vs leg-topology). The principle catches columns neither individually names (e.g. removal-vs-leg-topology both giving an empty member, separated by whether the vertex's `GC_*` survives in OTHER subprocesses' matrices).

## Boundaries (out of this slice)
- The vertex-grep IDENTITY (which `CALL` / `GC_*` is which physical vertex) is grounded in-slice from the generated code, but the COUPLING physics behind it (electric charge → FFV1, EFT operator → its `GC_*`) is ufo/eft slices.
- WHY physically a graph should/shouldn't be present (signal-vs-continuum, γ* interference, NWA) is the physics slice; the chain-SYNTAX that forces the resonant topology is chain-decay. The count/grep fact is mine; the physical interpretation is not.
- Lead-side this principle is consumed by `process-line-scope-traps` (topology check, not "it ran") and `coupling-vertex-viability` (count-unchanged vs count-changed discriminator) — both already route the σ-vs-count distinction through it.
