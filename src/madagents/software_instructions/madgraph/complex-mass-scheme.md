# 23 — Width Treatment and the Complex Mass Scheme

Width treatment in propagators: complex mass scheme, `bwcutoff`, NWA, and off-shell effects.

## Contents

- [The Problem: Widths and Gauge Invariance](#the-problem-widths-and-gauge-invariance)
- [The Complex Mass Scheme (CMS)](#the-complex-mass-scheme-cms)
- [The `bwcutoff` Parameter](#the-bwcutoff-parameter)
- [The `small_width_treatment` Parameter](#the-small_width_treatment-parameter)
- [Off-Shell Effects](#off-shell-effects)
- [The Narrow-Width Approximation in Practice](#the-narrow-width-approximation-in-practice)
- [Near-Threshold and Kinematically Forbidden Decays](#near-threshold-and-kinematically-forbidden-decays)
- [Zero Width Warning](#zero-width-warning)
- [Width Consistency with `compute_widths`](#width-consistency-with-compute_widths)

## The Problem: Widths and Gauge Invariance

The simplest treatment is the narrow-width approximation (NWA), which treats the particle as on-shell and factorizes production and decay:

```
sigma(pp -> tt-bar -> WbWb-bar) ~ sigma(pp -> tt-bar) * BR(t -> Wb)^2
```

The NWA is valid when the width is much smaller than the mass (Gamma/M << 1). For the top quark (Gamma_t/m_t ~ 0.8%), the NWA works well for inclusive observables. For the W and Z bosons (Gamma_W/M_W ~ 2.6%, Gamma_Z/M_Z ~ 2.7%), finite-width effects can be more significant.

When finite widths are included by inserting Gamma into the propagator (the "fixed-width scheme"), gauge invariance can be violated because the width arises from higher-order corrections while the matrix element is computed at a fixed order. This violation grows with energy and can produce unphysical results.

## The Complex Mass Scheme (CMS)

The Complex Mass Scheme solves this by promoting the mass of unstable particles to a complex number:

```
M^2 -> mu^2 = M^2 - i*M*Gamma
```

All derived quantities (weak mixing angle, couplings) are consistently computed using complex masses. This preserves gauge invariance order by order in perturbation theory.

MG5 uses the CMS for NLO computations. For NLO processes, the CMS is controlled by the run card parameter:

```
False  = complex_mass_scheme   ! (NLO run card, hidden)
```

When set to `True`, the CMS is activated. This parameter appears in the NLO run card.

At LO, MadGraph uses a fixed-width Breit-Wigner propagator by default, which is a simpler but less rigorous treatment. For most LO computations, the difference is negligible.

## The `bwcutoff` Parameter

The `bwcutoff` parameter controls the phase-space window around resonances:

```
15.0  = bwcutoff    ! (M +/- bwcutoff * Gamma)
```

When using the `$` (on-shell) syntax or decay chain syntax in the `generate` command, MG5 restricts the invariant mass of the resonance to within `bwcutoff` widths of the pole mass:

```
M - bwcutoff * Gamma  <  m_invariant  <  M + bwcutoff * Gamma
```

The default value of 15 corresponds to a very wide window (essentially all of phase space for narrow resonances). Reducing `bwcutoff` can speed up generation by focusing on the resonance region, but values below ~5 may miss relevant off-shell contributions.

## The `small_width_treatment` Parameter

```
1e-6  = small_width_treatment   ! (hidden)
```

Particles with very small widths (Gamma/M < `small_width_treatment`) can cause numerical instabilities in s-channel propagators. When this condition is met, MG5 replaces the width with `small_width_treatment * M` for the matrix element evaluation and corrects the cross-section assuming the NWA.

This parameter is hidden by default. Adjusting it is rarely needed — it mainly protects against numerical issues with nearly stable particles.

## Off-Shell Effects

For processes where off-shell effects matter (e.g., near kinematic thresholds, for precision measurements, or when non-resonant diagrams contribute), the full off-shell computation is preferred:

```
import model sm
generate p p > e+ ve mu- vm~ b b~    ! full 2->6 process
```

This includes all diagrams — doubly resonant (through tt-bar), singly resonant, and non-resonant — and naturally accounts for finite-width effects via the complex mass scheme.

The trade-off is computational cost: the full off-shell computation has many more diagrams than the factorized (production x decay) approach.

## The Narrow-Width Approximation in Practice

The decay chain syntax and MadSpin both keep only resonant diagrams, which is an approximation valid in the narrow-width regime. Note that MadGraph does not use the textbook NWA factorization ($\sigma \times \text{BR}$) — it performs full phase-space integration with Breit-Wigner propagators, retaining off-shell effects within the `bwcutoff` window. Example:

```
generate p p > t t~                    ! on-shell tops
# then decay with MadSpin
```

The NWA is a good approximation when:
- The particle is narrow (Gamma/M < few percent)
- You are not looking at observables sensitive to the off-shell tails (e.g., invariant mass distributions near the resonance)
- Non-resonant diagrams are negligible

Quantitative guidance for SM particles:

| Particle | Gamma/M | NWA quality |
|----------|---------|-------------|
| Top quark | ~0.8% | Excellent (~1% precision) |
| W boson | ~2.6% | Good for inclusive, finite-width effects at percent level |
| Z boson | ~2.7% | Good for inclusive, finite-width effects at percent level |
| Higgs (SM) | ~0.003% | Excellent |

For broad BSM resonances (Gamma/M > 5-10%), the NWA breaks down completely. Use the full matrix element for the final state instead of decay chain syntax.

## Near-Threshold and Kinematically Forbidden Decays

The NWA also breaks down near **kinematic thresholds**. When the sum of daughter masses approaches or exceeds the parent mass (m_parent ≈ m_1 + m_2 or m_parent < m_1 + m_2), the decay is dominated by off-shell effects.

This situation arises commonly in BSM models with compressed mass spectra. For example, in a Two-Higgs-Doublet Model where m(h2) < m(h1) + m(Z), the decay h2 → h1 Z is kinematically forbidden on-shell. Using the comma syntax (`generate p p > h2, h2 > h1 z`) forces h2 on-shell and produces zero or negligible cross-sections because the on-shell h2 cannot decay to on-shell h1 + Z.

**Recommended approach**: Generate the **full final state** without requiring specific intermediate resonances:

```
generate p p > l+ l- b b~     # all diagrams, no intermediate-particle requirement
```

This includes all contributing topologies — doubly resonant, singly resonant, and non-resonant — and naturally handles off-shell effects. The trade-off is computational cost (more diagrams), but the result is physically complete.

When using diagram filtering (`/`, `$`, `$$`) to select specific topologies in this context, verify gauge invariance with `check gauge`, since filtering can break gauge invariance especially when off-shell effects are important.

## Zero Width Warning

Setting the width to zero for a particle that appears as an s-channel resonance makes the Breit-Wigner propagator a delta function. The numerical phase-space integrator effectively never samples the exact pole mass, resulting in a zero or wildly fluctuating cross-section with enormous integration uncertainties. MadGraph may not produce a clear error message in this case.

**Fix**: Always set the physical width for s-channel resonances, or use `compute_widths` to calculate it automatically. See [MadWidth](decays-and-madspin.md).

## Width Consistency with `compute_widths`

When modifying particle masses in the param_card, the widths must be recomputed to be consistent with the new parameters. Use [MadWidth](decays-and-madspin.md):

```
compute_widths t w+ w- z h
```

Inconsistent widths (e.g., width computed at one mass but used at a different mass) can lead to:
- Branching ratios > 1 in MadSpin (causing errors)
- Incorrect Breit-Wigner line shapes
- Incorrect Breit-Wigner normalization
