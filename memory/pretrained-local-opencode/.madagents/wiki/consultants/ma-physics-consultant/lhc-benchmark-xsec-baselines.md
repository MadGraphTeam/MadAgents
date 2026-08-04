---
description: Rule for judging an LO cross-section against a "known" (usually NNLO/N3LO) reference in pp @ 13 TeV troubleshooting — estimate the K-factor regime from process class (ggF large K~3, VBF K≈1, DY/tt̄/diboson moderate, loop-induced absent at tree LO, inclusive bb̄ IR/cut-dominated); ggH heft K≈3 trap illustrated; plus W+/W- valence asymmetry, √s scaling, light-final-state IR regulator. Absolute σ are per-case literature lookups (verify vs primary source), not cached; MadGraph-LO figures are cluster probe-candidates.
---

# LHC benchmark cross-sections as "σ too small/large" sanity baselines (pp, √s=13 TeV)

Order-of-magnitude checks on MadGraph runs. The physics here (regime, LO-vs-higher-order K-factors, asymmetry mechanism, IR divergence) is the physics slice; the *number MadGraph-LO actually emits* for a given process is a runtime quantity → probe-candidate (cluster LO run), not source-walkable. **The reference σ below are literature values not yet re-verified against a primary source; confirm against PDG / LHCHXSWG / top++ before shipping as authoritative.**

## Judging an LO σ against a "known" reference (derivation rule, not a σ lookup)

A `generate p p > … ; launch` at tree level gives the **LO** number; most quoted "known" σ are **NNLO / N3LO**. So a low LO number is not a bug — it is LO. Do NOT adopt a cached σ per process; instead estimate the expected **K-factor regime from the process class**, then judge:

- **gg-initiated, higher-order-rich (ggF / ggH):** large K (order ~2–3). The sharpest trap.
- **EW t-channel (VBF):** K≈1 — the clean LO≈reference check.
- **Drell–Yan (W/Z), tt̄, diboson (WW):** moderate K ~1.2–1.8; LO sits below the NNLO reference by that factor, expected.
- **Loop-induced admixtures** (gg→WW box, gg→ZH, gg→H) are physically real but **absent from a tree-level `generate`** — a LO run is expected to miss them, so it also undershoots a reference that includes them.
- **IR / cut-dominated (inclusive bb̄, low-pT jets):** NOT a fixed number at all — order O(few hundred μb) but cut/scale/PDF-dominated and IR-divergent as pT→0; useful only as "O(right magnitude), and it blows up without pT cuts."

**Illustrative for ONE regime (ggH — derive per process): a `heft` LO run ~15–20 pb vs the ~48.6 pb N3LO reference (K≈3)** is CORRECT LO, not "too small." Never flag it as a bug against the 48 pb number.

**Absolute σ are per-process literature lookups, not cached constants.** For the actual number, look up per case against the primary source at the ORDER you need — LHCHXSWG YR4 (ggH / VBF / ZH / Higgs BRs), top++ (tt̄), PDG (W/Z), the relevant measurement (inclusive bb̄). Do not ship a recalled absolute σ as authoritative. The MadGraph-LO number itself is a runtime quantity → cluster probe-candidate, not source-walkable.

## W⁺/W⁻ ratio ≈ 1.29 (pp valence effect) — CONFIRMED

- Sign and magnitude correct. Measured W⁺/W⁻ at 13 TeV ≈ **1.29–1.30** (ATLAS/CMS; verify exact value). Doc's "1.3–1.4" is slightly high at the top end — the central value is ~1.29; 1.4 is the outer edge.
- Mechanism correct: dominant Drell–Yan channels are u d̄ → W⁺ and d ū → W⁻. The proton valence content is **uud** (2 valence u, 1 valence d), so the u-PDF exceeds the d-PDF at the relevant x → more W⁺. (The d̄/ū sea is nearly symmetric and dilutes but does not reverse the asymmetry.)
- It IS a pp effect. At the Tevatron (p p̄): the p̄ carries the CP-mirror valence content (2 valence ū, 1 valence d̄), so σ(W⁺)=σ(W⁻) **exactly by CP invariance** → ratio = 1. Correct.
- Related: the ratio rises toward central rapidity and with √s (sea grows, valence fraction shrinks) — so the number is mildly rapidity/energy dependent, not a universal constant.

## √s scaling 13 → 13.6 → 14 TeV (qualitative) — CORRECT

Energy steps: 13→13.6 ≈ +4.6%, 13→14 ≈ +7.7%. Cross-sections grow because parton luminosities rise; **the growth is steeper for heavier final states / gg-initiated processes** (they sit at larger x·√ŝ where PDFs — especially the gluon — rise faster with √s).

Rough 13→14 TeV growth (verify with a PDF-luminosity calc if load-bearing):
- EW / low-mass (W, Z, DY): **~+9–10%** (mild).
- WW, ZH: ~+12–15%.
- tt̄ (gg-dominated, M~350 GeV threshold): **~+20–25%** (steeper).
- ggH: ~+18–20%.
- High-mass BSM (TeV-scale): steeper still, tens of %.
13→13.6 TeV ≈ roughly 55–60% of the 13→14 step. Doc's "mild for EW, steeper for high-mass/tt̄" is correct.

## Light final-state (m→0) → IR divergence; generation cut is the regulator — CORRECT

If a final-state particle is (nearly) massless and couples via a t-channel exchange or is radiated as a massless gauge boson/parton, the cross-section **diverges as m→0** absent a cut. Two intertwined mechanisms:
- **Collinear**: t-channel propagator ~1/t with t = (p_i − p_out)² → 0 in the collinear limit; the mass m and the emission angle both regulate it. As m→0 the integral develops a log (or power) divergence ∫dt/t. For a radiated massless parton this is the collinear singularity of QCD/QED.
- **Soft**: a radiated massless gauge boson of energy E→0 gives a 1/E enhancement (soft singularity).
- A light **s-channel resonance** is a different regime (Breit-Wigner peak, width-regulated, → bw-window slice), NOT the m→0 IR divergence — keep the two apart.

Regulator at **generation level**: a `ptmin`-type cut (ptj/ptl/pta) removes the soft+collinear-transverse region; an invariant-mass cut (`mmjj`/`mmll`) or an angular ΔR cut removes the remaining collinear config; a `ptheavy`/`m_min` on the light particle removes the m→0 phase-space enhancement. **Any of these makes the LO cross-section finite.** The specific run_card knob is kinematic-cuts slice; the physics (which singularity each cut regulates) is mine.
- IR-safety caveat: the cut must be applied to the *singular* variable. A cut on the wrong variable leaves the divergence and the integral stays unstable (VEGAS won't converge / σ keeps climbing with statistics — that surfaces as an mc-integration symptom, but the root cause is this physics).

## Provenance / confidence
- **CONFIDENT (physics, robust across sources):** the LO-vs-higher-order *ordering* and the K-factor-by-process-class rule above; the W⁺/W⁻ mechanism & pp-vs-pp̄ CP argument; the √s-scaling qualitative pattern; the IR-divergence physics + regulator. These are physics, not lookups.
- **NEEDS VERIFICATION per case:** every absolute σ and exact K-factor is a literature lookup, regime-specific — verify against the primary source (PDG / LHCHXSWG YR4 / top++) at the order you need before shipping as authoritative.
- **PROBE-CANDIDATE:** the MadGraph-LO number itself (e.g. the ggH heft LO ~15–20 pb / K≈3 claim, load-bearing) → cluster LO run, not local, not source-walk. σ integrations → cluster, do NOT run locally.
