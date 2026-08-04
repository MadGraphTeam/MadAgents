---
description: You are fixing a BSM benchmark point or spectrum, and the signal needs a coupling that point could silently zero.
---

# Benchmark Parameter Coupling Viability

When choosing benchmark parameters for a signal process, verify that the load-bearing coupling is non-zero at those parameters. A "standard" choice from pretraining can silently kill the process.

## Trap

A parameter choice that makes eigenstates pure (decoupled) can simultaneously kill the gauge-boson coupling to those eigenstates. "Gaugino limit" means gaugino-dominated eigenstates, not fully-decoupled higgsinos.

## Concrete instance

In MSSM_SLHA2, the Z–χ̃⁰ᵢ–χ̃⁰ⱼ coupling (`$MADGRAPH_INSTALL/models/MSSM_SLHA2/couplings.py`, GC_444, GC_422) depends exclusively on higgsino NMIX columns (NNx3, NNx4). Setting |μ| >> M₁, M₂ → zero higgsino admixture → zero coupling → zero cross-section. Correct: μ ≈ 2-3× M₁ retains ~10% higgsino mixing to sustain the coupling while eigenstates stay gaugino-dominated.

## Discipline

1. Identify load-bearing coupling(s) — the ones driving production and/or decay.
2. Walk the coupling formula in UFO source (e.g., `couplings.py`) to see which parameters it depends on.
3. Choose parameters so that coupling is non-zero at the chosen point.
4. If a physics label ("gaugino limit", "pure bino") could mean either pure-state or near-pure-state, choose near-pure with enough mixing to sustain the coupling.

## Fires on

Any task asking for benchmark parameters, SUSY/BSM model choices, or "what should I set X to for process Y".

## Related

`coupling-vertex-viability.md` — the general "is the physics realizable at THIS benchmark?" diagnostic. This page is the parameter-authoring variant.