---
description: A coupling a signal needs can be ZERO at a benchmark chosen only for its masses — the mixing matrix / coupling structure is implicitly fixed by the input parameters, never set directly. Two derived instances (MSSM neutralino higgsino-decoupling Z-coupling; HVT fermiophobic no-production-channel) + regime boundaries.
---

# Coupling viability from spectrum: a needed coupling can vanish at a mass-chosen benchmark

CENTRAL PRINCIPLE (physics, derived). Choosing benchmark *input parameters* (masses, mixing inputs, coupling coefficients) implicitly fixes the *derived* couplings — diagonalized mixing-matrix entries, products of mixing angles. A coupling the requested SIGNAL depends on can be ~0 at that point even though it was never set to zero directly. "The spectrum is right" is NOT "the signal exists." Always check the signal coupling separately from the mass spectrum. Sibling in spirit to the lead's derived-quantity-staleness (a value MG5 won't refresh) — here it's a value the *user* never set, the model derived it.

## Instance (a): MSSM neutralino, higgsino-decoupling limit. VERDICT: APPROVED.
The Z–χ̃⁰ᵢ–χ̃⁰ⱼ coupling lives **exclusively in higgsino columns** (NNx3, NNx4) — pure gauginos have zero Z coupling by gauge quantum numbers — so it scales as (m_Z/μ)² and a decoupled μ kills a Z-mediated electroweakino signal. **FIX:** choose |μ| ≈ 2–3× M₁ (gaugino-dominated eigenstates, ~10% higgsino admixture), not |μ| ≫ M₁.
**Canonical treatment — source-walk (GC_422/GC_444), the gauge-quantum-number derivation, and the μ-scan numerical table — is `gaugino-limit-mu-not-decoupled.md`.** Retained here only as an example of the central principle.

## Instance (b): HVT fermiophobic (cF=cq=cl=0). VERDICT: APPROVED.
HVT phenomenological Lagrangian (Pappadopulo-Thamm-Torre-Wells, arXiv:1402.4431): four params M_V, cF (V–fermion, drives DY + fermionic decays), cH (V–Higgs / longitudinal-SM-gauge couplings, sets V-W-W & V-Z-h), gV (new-vector strength).
- cF=0 kills tree DY (qq̄→V⁰) — the dominant LHC channel for a 2 TeV neutral vector.
- Survivors VBF (pp→V⁰jj) and associated (V⁰h, V⁰W) proceed only via cH and the small V–SM-gauge mixing (θ ~ m_W²/M_V² × coupling ~ few×10⁻³ at 2 TeV) — amplitudes ~θ × SM-strength, rates ~θ² below an SM-strength TGC. Equivalence-theorem (m_W/M_V) factors compound the penalty.
- Anchored at M_V=2 TeV: DY(cq=1)=0.0242 pb; DY(cq=0)=7.1e-6; VBF(cq=0)=2.8e-5 (864× below DY-cq1); V+h(cq=0)=5e-7 (48400× below). VBF/DY-cq1 ≈ 1.2e-3, consistent with θ²×PDF/lumi.
- Observability: even the largest survivor (VBF, 2.8e-5 pb) needs ~3.5e4 fb⁻¹ for ~10 events at ~1% effective acceptance — an order of magnitude beyond HL-LHC's 3000 fb⁻¹. No observable channel.
- FIX: keep cF≠0 (drop fermiophobic); switching production mode does NOT rescue it.

CAVEAT: **A large cH does NOT rescue it.** σ(VBF)~cH²; reaching DY(cF=1) from VBF(cq=0) needs cH²↑~860× → cH ~29× its anchored value → non-perturbative / EWPT-excluded. No allowed cH closes the 3-orders gap at 2 TeV. (At much lower M_V the θ~m_W²/M_V² suppression weakens and VBF/Vh become relatively less hopeless, but the fermiophobic-no-channel conclusion holds for a multi-TeV resonance.)
