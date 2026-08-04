---
description: A gForceBW=1 forced s-channel resonance scales sigma as 1/Gamma_total — the param-card DECAY width feeds BOTH the BW sampling and the propagator iMGamma; no BR<=1 reconciliation, so a stale total width silently rescales sigma.
---

# BW-resonance rate normalization: sigma ∝ 1/Gamma_total, width = param-card DECAY

Grounded against the case `generate b b~ > h, (h > w+ w-)`, heavy 400-GeV SM-like Higgs,
forced-BW s-channel H (gForceBW=1). Built dir `<PROC_DIR>/SubProcesses/P1_bbx_h_h_wpwm`.

## The finding
For a decay-chain `>` resonance the chain cross-section scales as `Gamma_partial/Gamma_total = BR`
with **no explicit BR multiplication anywhere**. The 1/Gamma_total comes purely from the on-resonance
phase-space integral of |BW|² (∝ 1/(M·Gamma)) in the propagator denominator; the H→WW vertex coupling
supplies the partial-width-like numerator. Both use the SAME runtime width = the param-card `DECAY`
value. A stale `DECAY` therefore silently rescales sigma by the width ratio (example: stale
`DECAY 25 = 6.382339e-03` → 66.095 pb; correct `2.720001e+01` → 0.015143 pb; ratio ≈ 4365× vs bare
width ratio 4262× — see "the ~2% residual" below). No warning at any stage.

## (a) The H BW is sampled with the model width, AND the denominator uses the SAME width
**Sampling side (mine).** For this 2→2-with-one-s-channel topology the H propagator IS the s-hat
propagator: index `-(nexternal-(nincoming+1)) = -(4-3) = -1` (`nexternal.inc`: NEXTERNAL=4,
NINCOMING=2). So set_peaks routes it through the **"Setting PDF BW"** branch (myamp.f:430-442), not a
separate branch mass:
- `spole(j) = prmass²/stot`, `swidth(j) = prwidth*prmass/stot` with `j=3*(nexternal-2)-4+1=3`
  (myamp.f:441-442; comment: "keep the real width here (important for the jacobian)").
- `prmass`/`prwidth` come ONLY from `props.inc` (`include 'props.inc'` myamp.f:325, after a
  zero-init loop myamp.f:321-324). For THIS case `props.inc` is:
  `PRMASS(-1,1)=ABS(MDL_MH)`, `PRWIDTH(-1,1)=ABS(MDL_WH)`, `POW(-1,1)=2`.
- gForceBW=1 (`decayBW.inc`: `DATA GFORCEBW(-1,1)/1/` → `lbw(nbw).eq.1`) forces the BW map regardless
  of energy concerns (the `.or. lbw(nbw).eq.1` clause, myamp.f:438).
- The map is applied live in `sample_get_x` (Source/dsample.f:1393-1396): `if (swidth(ij).gt.0d0) call
  transpole(spole(ij),swidth(ij),...)` — the spole/swidth in common `/to_brietwigner/` are exactly the
  set_peaks values. (`sample_get_x` body is numerical/VEGAS slice; the map object + its swidth arg are
  mine.) The one_tree s-channel branch reaches the sampler via `sample_get_x(wgt,x(-ibranch),...)`
  (genps.f:836).

**Denominator side (HELAS/ALOHA — boundary named).** Generated ME `matrix1_orig.f`:
`CALL VVS1_3(W(1,4),W(1,3),GC_72,MDL_MH, FK_MDL_WH,W(1,5))` (matrix1_orig.f:461) builds the off-shell
H wavefunction from the two W's with mass `MDL_MH`, width `FK_MDL_WH`. `FK_MDL_WH` is `MDL_WH`
floored by small_width_treatment (matrix1_orig.f:436-440). `CALL FFS4_0(W(1,1),W(1,2),W(1,5),
GC_83,AMP(1))` (463) contracts with b-b̄. JAMP(1,1)=AMP(1) (470); **no explicit BR factor** in
MATRIX1/ANS. The construction of the VVS1_3 propagator-denominator wavefunction itself is HELAS/ALOHA
territory — I confirm only that it reads `MDL_WH`, the SAME value my sampling side uses.

**Same value, both sides.** `MDL_WH` is the runtime width loaded from the param-card `DECAY 25` block
(`coupl.inc:29,31` COMMON/WIDTHS/MDL_WH...; param_card.dat:60 `DECAY  25 6.382339e-03 # WH`; the
DECAY-block→MDL_WH parsing is lha_read.f:243-246 + the generated param_card.inc — that key→variable
map is param-card/model-loader slice). Sampling width and denominator width are NOT independently
recomputed; both are `MDL_WH`. There is **no summed-partials / recomputed total** anywhere — the
width is whatever the card says.

## (b) Nothing reconciles Gamma_total against partial widths; BR>1 is silently accepted
Grep of the whole phase-space path (myamp.f, genps.f) for `branching|partial.width|sum.*width|BR|
exceed|>1` finds NO reconciliation. The ONLY width-driven abort is set_peaks `write_null_results()`
+ `stop` (myamp.f:417-428), and it is purely **kinematic**: it fires when the forced-BW window
`[m ± bwcutoff*Gamma_eff]` cannot fit inside `[xm(i), sqrt(stot)]`. With Γ stale-narrow (6.4e-3 at
m=400), the window `[400 ± 15·6.4e-3] ≈ [399.9, 400.1]` sits well inside the kinematic range → the
abort does NOT fire, run proceeds clean. There is no check that the implied
`BR = Gamma_partial/Gamma_total` ≤ 1 (here ≈ 16.50/6.4e-3 ≈ 2585 ≫ 1, silently accepted). MadGraph
trusts the card width as the total; a too-small total just makes the |BW|² integral too large.

## (c) The ~2% residual (ratio 4365× vs bare 4262×)
Sampling width and denominator width are the same `DECAY 25` value, BUT both pass through
`small_width_treatment` floors that bite differently from a pure 1/Γ scaling:
- Denominator: `FK_MDL_WH = sign(max(|MDL_WH|, |MDL_MH*small_width_treatment|), MDL_WH)`
  (matrix1_orig.f:436-440).
- Sampling/jacobian: transpole floors `width` at `pole*small_width_treatment` (transpole.f:44-46).
The dominant residual cause the chain-decay consultant attributed (production-side Higgs BW being
sharper with the narrower stale width — the BW lineshape, not a pure normalization) is consistent
with this: the on-resonance |BW|² integral is not exactly 1/Γ once the finite-width lineshape and
the smin/smax integration limits are folded in. So the ~2% is expected lineshape/floor curvature, not
a separate BR factor. (The exact integration arithmetic is numerical/VEGAS slice; I establish only
that the SAME width drives both and that no independent normalization exists to explain the gap.)

## Cautions / boundaries
- The 1/Gamma_total scaling is a consequence of the BW map (mine) + propagator denominator
  (HELAS/ALOHA) sharing one width. I own the sampling-side width identity and the no-reconciliation
  fact; the VVS1_3 denominator construction is HELAS/ALOHA, the integration arithmetic is numerical.
- Deriving the CORRECT total width (here ≈27.2 GeV at m_H=400) is madwidth's slice; whether a stale
  width survives to the run is param-card/launch.
- This is the s-hat-routed BW (single s-channel = s-hat index). A resonance that is NOT the s-hat
  propagator (deeper in a multi-resonance chain) takes the `else if` branch (myamp.f:445-449,
  `spole(-i)`, `swidth(-i)`) — same width source (props.inc/MDL_W<X>), different invariant slot.
- See propagator-mappings-gen_s-transpole.md (the gen_s/transpole map mechanics) and
  gforcebw-cut_bw-onshell.md (the gForceBW=1 forced-BW gate). This page is the RATE consequence those
  two mechanics produce.
