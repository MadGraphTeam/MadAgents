---
description: Decision procedure — the bwcutoff sites in LO myamp.f split into two regimes (unconditional vs gForceBW=1-only); when does changing bwcutoff affect X
---

# bwcutoff scaling regimes in LO myamp.f

Cite `$MADGRAPH_INSTALL/Template/LO/SubProcesses/myamp.f`, v3.7.1. `bwcutoff` (run-card
default registered at banner.py:4305; bw-runcard-knobs.md) appears at the sites enumerated
below in this file (count via `grep -c bwcutoff myamp.f`). They fall into TWO regimes. To
answer "does changing bwcutoff affect X?", classify X first.

## Regime A — UNCONDITIONAL (bwcutoff scales the window for ALL resonances/poles)
- **Les Houches on-shell tag**, myamp.f:136-139: window is `bwcutoff*Γ_eff` for every leg.
  gForceBW=1 only relaxes the `Γ_eff/M<0.1` narrow gate — it does NOT change the window
  scale. So bwcutoff widens this tag even for ordinary (non-decay-chain) s-channels.
- **s-hat 1/s-vs-BW transform gate**, myamp.f:575:
  `smin/stot > spole + bwcutoff*max(swidth, spole*small_width_treatment)` — bwcutoff
  applies to every pole, no gForceBW gate. (Also the one site where bwcutoff and
  small_width_treatment combine; see bw-setpeaks-psgrid.md.)

## Regime B — FORCED-ONLY (bwcutoff only when gForceBW=1, else hardcoded 5d0*Γ_eff)
- **cut_bw enforcement onshell**, myamp.f:188-193: gForceBW=1 → `bwcutoff*Γ_eff`;
  else → `5d0*Γ_eff` (bw-onshell-test-cutbw.md).
- **set_peaks grid lower bound**, myamp.f:402-409: gForceBW=1 → `bwcut_for_PS=bwcutoff`;
  else (lbw=1 or default) → `bwcut_for_PS=5d0` (bw-setpeaks-psgrid.md).
- **set_peaks impossible-onshell guard**, myamp.f:419-422: lbw=1 branch uses
  `bwcut_for_PS(i)` (= bwcutoff only if forced, else 5d0); the gForceBW=1 branch uses
  `bwcutoff` directly. BW-pole setting (443, 461) likewise via `bwcut_for_PS(i)`.

## Why the generalization matters (corrects an incomplete per-page caution)
- Both bw-onshell-test-cutbw.md and bw-setpeaks-psgrid.md carry the caution "bwcutoff only
  widens forced (gForceBW=1) legs; ordinary s-channel resonances use a hardcoded 5σ."
  That caution is **true for Regime B but omits Regime A.** Adopting it in isolation would
  give the WRONG answer "changing bwcutoff has no effect on non-decay-chain resonances" —
  false for the Les Houches event tag (137) and for the s-hat transform choice (575).
- Decision procedure for an arbitrary "bwcutoff affects X?" question:
  1. Is X the Les Houches on-shell tag or the s-hat transform gate? → Regime A: YES,
     bwcutoff scales it for all legs.
  2. Is X the cut_bw enforcement / set_peaks grid window / impossible-onshell guard?
     → Regime B: only if the leg is gForceBW=1 (decay-chain syntax); else the window is a
     fixed 5σ and bwcutoff is irrelevant.

## Why the registered default is a sensible default (tail quantity)
A `bwcutoff` of `n` widths excludes only the BW tail *below* `1/(4n²+1)` of peak height
(≈ 1/900 at n=15; NOT 1/226 = 1/(n²+1), the wrong full-Γ convention). For a narrow
resonance sampled at its pole the discarded fraction is negligible — so the Regime-B window
(gForceBW=1 → bwcutoff·Γ_eff, else 5σ) only needs enlarging when the physics lives in that
tail (sub-threshold / forced-off-shell daughter). Derivation + sizing: bw-cutoff-sizing-derivation.md.

## Boundary
- LO `myamp.f` only. NLO/FKS BW windows → amcatnlo/fks slices. MadSpin `BW_cut` → MadSpin
  slice. This page is about which Fortran expression scales which window — a static source
  fact (read off the code), not a runtime prediction; source-walk grounding suffices.
- Γ_eff throughout = `max(prwidth, prmass*small_width_treatment)` (bw-onshell-test-cutbw.md).
