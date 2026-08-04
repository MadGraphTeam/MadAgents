---
description: Physics validity of MadWidth tree-level (LO) automatic partial widths. When the tree-level auto-width is adequate vs when an external width MUST be supplied (Higgs, loop-induced channels, heavy-quark/hadronic decays). b-Yukawa pole-vs-running overestimate, missing loop-induced channels, differential QCD K-factors, NWA cancellation logic. Literature-cited.
---

# Tree-level (MadWidth) auto-width: physics validity and failure modes

SCOPE. MadWidth computes ONLY tree-level (LO) partial widths, enumerating tree/effective vertices in the loaded model (source premise: `decay_objects.py:1591`; NWA/tree-level warning fires every call). Loop-induced channels with no tree vertex are ABSENT from the sum (in `sm`: H→gg, H→γγ, H→Zγ). This page is the first-principles verdict on when that LO sum is physically trustworthy. Derived, not recalled.

## Fact 1 — b-Yukawa pole-vs-running: Γ(H→bb̄) overestimated ~2.4–2.9×

Tree-level: Γ(H→bb̄) = (3 G_F m_H m_b²)/(4√2 π)·β³, β=√(1−4m_b²/m_H²). At m_H=125, m_b=4.78: β³=0.991 (negligible) → **Γ ∝ m_b²** to <1%. So the width scales with the SQUARE of whatever b-mass feeds the Yukawa.

- MadWidth in `sm` uses the b **pole** mass (default `MB` external ≈ 4.7 GeV; PDG pole m_b=4.78±0.06, PDG 2024 b-quark listings).
- State-of-the-art predictions use the MSbar **running** mass at μ≈m_H: m_b(125)≈2.8 GeV (interpolated; Djouadi Anatomy I Table 1.1 gives m_b(100 GeV)=2.95, arXiv:hep-ph/0503172; APARISI 2022 quotes m_b(m_H)=2.60 → band 2.6–2.9).
- **Mass-choice overestimate:** (m_pole/m_run)² ≈ (4.78/2.8)² ≈ **2.9×** (2.9–3.4 over the 2.6–2.9 band). Direction: OVERESTIMATE.
- **Net vs the physical value:** physical Γ(bb̄) = Γ_LO,run·(1+Δ_QCD) with Δ_QCD≈+0.20 (below). So Γ_MadWidth/Γ_phys = 2.9/1.20 ≈ **2.4×**. The omitted +20% QCD correction would have raised the true value, partially offsetting the mass-choice inflation — still a ~2.4× overestimate of the true channel.

Because H→bb̄ is the DOMINANT channel (BR=0.581, LHCHXSWG YR4 at 125.09 GeV), inflating it ~2.4–2.9× inflates the TOTAL width substantially.

## Fact 2 — physical SM Higgs total width = 4.100 MeV; MadWidth output ≈ 6–8 MeV

- **LHCHXSWG YR4 (CERN Yellow Report 4, arXiv:1610.07922; CERNYellowReportPageBR), m_H=125.09:** Γ_H = **4.100 MeV = 4.100×10⁻³ GeV**, ±0.73%. This is the physical SM Higgs total width to use.
- BRs (LHCHXSWG YR4): bb̄ 0.5809, WW* 0.2152, gg 0.0818, ττ 0.0626, cc̄ 0.0288, ZZ* 0.0264, γγ 0.00227, Zγ 0.00154.
- **A tree-level pole-mass MadWidth output (~6.5 MeV) overestimates Γ_H by ≈1.58×** relative to the physical 4.100 MeV — it is NOT the LHCHXSWG value. The inflation is consistent with the tree-level pole-mass MadWidth sum (bb̄ inflated ~2.4×, cc̄ inflated ~6× from pole vs running charm, gg/γγ/Zγ missing → rough tree total 6–8 MeV). Never quote a MadWidth number of this size as the physical width. Physical-width floor to hand to a param_card: **4.1×10⁻³ GeV**.

## Fact 3 — "sub-percent QCD mismatch" is WRONG for hadronic/heavy-quark channels

A common over-optimistic claim holds that because LO-summed partials differ only mildly from the NLO total, the BW-normalization/BR bias is "sub-percent for most processes." That is wrong for hadronic/heavy-quark channels: the bias equals the SPREAD of differential K-factors across channels:
- **Γ(H→bb̄): +≈20%** QCD (running-mass scheme; Δ=5.67(α_s/π)+…, Djouadi Anatomy I §2.1.2 "≈20%"). NOT sub-percent.
- **Γ(t→Wb): −≈9%** O(α_s) (PDG 2024 Top review Eq.61.4, Jezabek-Kühn; Bernreuther arXiv:0805.1333 combined QCD ≈−11%). NOT sub-percent.
- Purely leptonic/EW decays (Z→ℓℓ, W→ℓν, slepton→ℓχ) genuinely ARE sub-percent-to-few-percent — no strong-final-state, no mass running.

So "sub-percent for most" holds ONLY for decays with no strongly-interacting final state and no large mass-running. For any competition between a QCD-sensitive channel (heavy quarks, jets) and an EW channel, the BR SPLIT shifts by O(10–20%).

**Key NWA subtlety (the physics of when it actually hurts):** in pure narrow-width production×BR, a globally-wrong TOTAL width CANCELS between the BW-propagator normalization and the branching fraction when the SAME width is used consistently. A uniform K-factor on all channels therefore does NOT bias σ×BR. What DOES bias results: (a) a MISSING channel → wrong BR numerator; (b) DIFFERENTIAL K-factors → wrong BR splits; (c) off-shell / interference regions where the absolute BW tail shape matters. This is why the Higgs (missing gg/γγ + big differential bb̄ K-factor) fails, while a leptonically-decaying Z' is fine.

## Fact 4 — validity condition: tree-dominance + no differential distortion + NWA

Tree-level auto-width is ADEQUATE when ALL hold:
1. **No loop-induced channel carries non-negligible BR** (else the total AND the BRs are wrong — the channel is simply absent from the sum).
2. **Differential QCD/EW K-factors across channels are small** (else BR splits are wrong).
3. **You are in the NWA regime** (production×decay factorizes; the total-width normalization largely cancels in σ×BR).

Adequate FOR: heavy resonances decaying dominantly to tree-level 2-body with a single dominant color structure — Z'/W', most SUSY cascades (squark→qχ, χ→χℓℓ), heavy scalars/vectors with tree fermionic/bosonic decays. There a ~10–20% total-width error is harmless in NWA.

MUST supply an EXTERNAL width when:
- **Loop-induced channels have significant BR** — the **Higgs** above all (gg 8.2%, γγ 0.23%, Zγ 0.15% all missing in `sm`; use LHCHXSWG **4.1×10⁻³ GeV**). Any state whose dominant/significant decay is loop-induced (a scalar decaying only via loops).
- **Large / differential QCD corrections distort the width** — Higgs (bb̄ +20% vs EW ~0), and any precision application.
- **The physical width is measured better than tree-level** — Z (2.4952 GeV), W (2.085 GeV), top (Γ_NLO≈1.32 GeV at m_t=172.5, PDG). Prefer the measured/NLO value over the LO auto-width.

In `heft` an effective Hgg vertex EXISTS (premise), so MadWidth there DOES include H→gg at tree level — but still misses γγ/Zγ and still carries the pole-mass bb̄ inflation, so the total is still not the physical 4.1 MeV. Supplying the LHCHXSWG width remains the right move for Higgs phenomenology.

## Operative guidance
- Higgs (any model): set Γ_H = 4.1×10⁻³ GeV externally; do NOT trust the auto-width.
- Top: prefer Γ_t ≈ 1.32 GeV (NLO) over LO auto-width (LO ≈ +10% high).
- Z/W: prefer measured widths.
- Generic BSM tree-decayer used in NWA: auto-width is fine; the ~10–20% is absorbed in the σ×BR cancellation.
