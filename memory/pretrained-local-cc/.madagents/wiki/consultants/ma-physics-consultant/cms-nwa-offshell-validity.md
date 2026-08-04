---
description: First-principles verdict on (1) complex-mass scheme vs naive fixed/running width and gauge invariance, (2) NWA validity conditions and what it drops, (3) the Gamma/M per-particle finite-width estimation rule (compute per particle+scheme; ~Gamma/M inclusive; ~0.05 breakdown floor; Higgs off-shell illustrative), (4) near-threshold breakdown (lightest-decomposition boundary — the off-shell-threshold-check slate lesson). Companion to tree-level-auto-width-validity (width source). Literature citations flagged for verification.
---

# CMS, NWA validity, off-shell / near-threshold: first-principles verdict

These four questions are all physics-spec (regime classification + approximation validity). The MadGraph *mechanisms* referenced (CMS activation at `import model ... --modelname`/`complex_mass_scheme`; `bwcutoff`/off-shell window enforcement) are model-loader and bw-window slices respectively — this page gives the physics, not the source path.

## CMS vs naive width & gauge invariance

Inserting Γ into the propagator (fixed-width) can violate gauge invariance because the width is a higher-order effect while the matrix element is fixed-order, and the violation grows with energy; the complex-mass scheme (M²→M²−iMΓ, all derived quantities complex) preserves gauge invariance. The precise statements:

- **Mechanism of the violation (correct as stated).** Γ = Im Σ(M²)/M is O(g²) (one-loop self-energy imaginary part). A tree amplitude's gauge cancellations hold *among terms of the same order*. Dressing ONLY the resonant propagator with a partial higher-order piece (the width), without the corresponding higher-order terms elsewhere, spoils the Ward/Slavnov–Taylor identity that enforced the cancellation. So the violation is an ORDER-MIXING artifact.
- **What is actually violated — be precise.** Not "gauge invariance" loosely but (a) gauge-PARAMETER independence (Rξ result ≠ unitary-gauge result once a naive width is inserted) and (b) the Ward identities that tie longitudinal-gauge-boson amplitudes together. State it as gauge-parameter dependence + broken Ward identities.
- **Where the pathology actually bites (process-dependent).** Near a single resonance peak the gauge-violating terms are numerically tiny (suppressed by Γ/M). They are DANGEROUS in amplitudes with delicate high-energy cancellations: t-channel gauge-boson exchange, and longitudinal-gauge-boson final states where the equivalence theorem/unitarity demand cancellations that grow like s/M². Classic breakdowns: single-W / single-resonance production such as eγ→νW, and e⁺e⁻→4f (WW with one leg off-shell) — there the naive fixed width leaves terms ∝ s/M_W² that violate unitarity at high √s. So "grows with energy" is right, but only for these gauge-cancellation-sensitive topologies, not universally.
- **Fixed-width vs running-width.** Both naive schemes break gauge invariance; the running width (Γ(p²)=Γ p²/M² for p²>0) is not a fix. Neither is gauge-safe.
- **Why CMS works — sharpen "order-by-order" to "exactly".** CMS analytically continues the mass to a complex value μ²=M²−iMΓ *in the Lagrangian* — so it propagates into the couplings and derived quantities too: the weak mixing angle becomes complex, cos²θ_W = μ_W²/μ_Z². Because the substitution is consistent everywhere, the Ward/Slavnov–Taylor identities are preserved EXACTLY (to all orders), not merely order-by-order. Cost: complex couplings/counterterms; the scheme is built so perturbative bookkeeping stays consistent. It is the standard NLO EW scheme (and usable at LO).
- **Gauge invariance ≠ unitarity (distinct requirements).** A scheme can be gauge-invariant yet still need care with unitarity; CMS respects both to the order worked. Alternative gauge-invariant schemes exist: pole scheme (expand around the complex pole), fermion-loop scheme (insert the full O(g²) fermionic corrections — gauge-invariant AND unitary by construction). CMS is preferred for its simplicity and NLO-readiness.

Reference (verify against the primary source): complex-mass scheme — Denner, Dittmaier, Roth, Wieders, Nucl. Phys. B724 (2005) 247 and the Denner–Dittmaier review "The Complex-Mass Scheme...". Gauge-violation-at-high-energy examples — Argyres et al. / Beenakker et al. on WW and single-W production.

## NWA validity conditions and what it drops

NWA is valid when Γ/M ≪ 1 and the observable is insensitive to off-shell tails; it drops off-shell tails, non-resonant diagrams, and inter-channel interference.

- Mechanism: BW propagator 1/[(p²−M²)²+M²Γ²] → (π/MΓ)δ(p²−M²) as Γ/M→0, so σ_prod×decay → σ_prod × BR. **Leading correction is O(Γ/M).**
- What it drops (all correct): off-shell tails (delta replaces the propagator), non-doubly-resonant diagrams feeding the same final state, signal×background interference and overlapping-resonance interference. Also **spin correlations** between production and decay unless explicitly restored (e.g. MadSpin `spinmode=madspin`).
- Load-bearing qualifier "insensitive to off-shell tails" is the real gate. The O(Γ/M) error estimate holds for inclusive rates AWAY from kinematic edges. Near a phase-space boundary or when the observable selects the tail (high-mass window, off-shell region) the error EXCEEDS Γ/M — see Higgs caveat below.

## Γ/M finite-width estimation rule (derive per particle + scheme, not a constant)

Γ/M is NOT a universal constant — compute it per particle from *that particle's* width and mass, and note both are scheme-dependent (pole vs complex-pole mass; on-shell vs running/NLO width). The rule:

- **NWA leading finite-width error ~ Γ/M** for inclusive rates away from kinematic edges (near an edge or when the observable selects the tail, the error EXCEEDS Γ/M — see the Higgs caveat and near-threshold below).
- **Breakdown heuristic Γ/M ≳ 0.05** (soft floor): above it, off-shell/interference stop being a small correction and NWA/BW-factorization degrade; broad BSM states (Γ ~ M) are firmly outside NWA.
- SM narrow states — compute each from its PDG width/mass per case (order-of-magnitude arithmetic; a precise ratio is a numerics-candidate): top comes out sub-percent (excellent), the EW bosons W/Z at the few-percent level (good for inclusive rates; percent-level finite-width corrections matter for precision).

**Illustrative for ONE regime (Higgs — derive per process): a tiny Γ/M does NOT imply NWA is adequate.** Γ_H/M_H ~ 3×10⁻⁵ makes NWA superb for the RESONANCE NORMALIZATION, but NWA is famously INADEQUATE for off-shell-sensitive Higgs observables regardless of the tiny ratio: gg→H*→ZZ/WW above threshold, and its interference with the gg→VV continuum, carry O(10%) of the on-shell rate and are the basis of the off-shell Higgs-width bound. So "tiny Γ/M ⟹ NWA always fine" is FALSE — Γ/M small guarantees the peak is narrow, NOT that the tail is negligible for the chosen observable. This is precisely where near-threshold/off-shell (below) applies.

## Near-threshold breakdown

When the sum of daughter masses approaches or exceeds the parent mass, the decay is off-shell-dominated, NWA/on-shell factorization fails, and the full final state is required. Example: in a 2HDM with m(h2) < m(h1)+M_Z, the decay h2→h1 Z is on-shell-forbidden.

- **Distinguish two sub-regimes.** (i) JUST ABOVE the on-shell threshold (Σm_pole ≲ m_parent): the 2-body decay is ALLOWED but phase-space-suppressed (velocity β→0; β³ for a scalar S-wave two-body). (ii) AT/BELOW threshold (Σm_pole ≳ m_parent): the on-shell mode is forbidden; the decay proceeds only through an off-shell daughter, i.e. the physical final state is the daughter's own decay products. Both need the full multi-body ME, not factorized production×BR; regime (ii) mandatorily so.
- **True kinematic boundary is the lightest decomposition, not the pole sum** — the near-threshold rule below (also carried as the `off-shell-threshold-check` slate lesson). h2→h1 Z with m(h2)<m(h1)+M_Z is on-shell-forbidden, but h2→h1 Z*→h1 f f̄ PROCEEDS whenever m(h2) > m(h1)+(m_f+m_f̄). So "forbidden" is only the on-shell statement; the off-shell tail of the daughter BW gives a finite (small) rate below the pole threshold.
- **MadGraph mechanism is bw-window's slice.** Whether the off-shell tail is actually sampled depends on `bwcutoff` / the off-shell window — a default `bwcutoff=15` clips the tail and can silently zero or bias the sub-threshold rate. The value must be DERIVED from the virtuality range per process. Route that to ma-bw-window-consultant; I only certify the physics that the rate is nonzero and off-shell-dominated.

## Cross-links
- `off-shell-threshold-check` (slate lesson, no separate page — content is the near-threshold section above) — lightest-decomposition kinematic boundary; the "don't call it forbidden" rule.
- `tree-level-auto-width-validity.md` — where the width Γ itself comes from (MadWidth LO) and its NWA-cancellation logic.
