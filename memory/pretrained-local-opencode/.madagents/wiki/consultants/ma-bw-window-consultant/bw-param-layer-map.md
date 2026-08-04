---
description: Two-layer routing principle — which BW parameter (bwcutoff vs small_width_treatment) reaches which LO stage (window/classification layer vs sampling/jacobian layer), v3.7.1
---

# BW parameter → LO-stage layer map

Cites `$MADGRAPH_INSTALL/madgraph/various/banner.py`, `Template/LO/SubProcesses/myamp.f`,
`Template/LO/Source/transpole.f`, `Template/LO/Source/dsample.f`, v3.7.1. Generalizes the
per-file pages (bw-onshell-test-cutbw.md, bw-setpeaks-psgrid.md,
bw-bwcutoff-scaling-regimes.md, bw-transpole-nwa-jacobian.md) into one routing axis.

## The principle: two layers, two parameters with different reach
The LO BW machinery splits into two stages. To answer "does parameter P affect stage S?",
first place S in one of the two layers — the parameter's reach is then determined.

**Layer 1 — window / classification** (`myamp.f` + `run.inc` declaration). Decides whether
a propagator counts as on-shell, where the PS-grid lower bound sits, whether a channel is
impossible, and 1/s-vs-BW transform choice. This is where on/off-shell *enforcement* lives.

**Layer 2 — sampling / jacobian** (`transpole.f`, driven by `dsample.f`). Maps flat x→BW-
distributed y and computes the integration weight. This is where the BW peak is actually
*sampled* and where σ is reweighted.

## bwcutoff: Layer 1 ONLY
- Appears in only two LO files: `myamp.f` (the sites enumerated in
  bw-bwcutoff-scaling-regimes.md; count via `grep -c bwcutoff myamp.f`) and
  `run.inc:36-37` (the common-block declaration). `grep -c bwcutoff` = **0** in both
  `transpole.f` and `dsample.f` (verified).
- **Consequence:** bwcutoff can never touch the integration jacobian or the sampling
  transform. A question of the form "can bwcutoff change the event weight / jacobian / the
  shape of the sampled BW peak?" answers **NO by layer** — bwcutoff only sets *which* poles
  get a BW transform and *how wide* the classification/grid window is, never the transform
  itself. (Within Layer 1, the Regime-A/B split governs which windows it scales:
  bw-bwcutoff-scaling-regimes.md.)

## small_width_treatment: BOTH layers, DIFFERENT roles
- Window layer (`myamp.f`): Γ_eff floor `max(prwidth, prmass*small_width_treatment)`
  at myamp.f:132 (cut_bw) and :330 (set_peaks), plus the s-hat 1/s-vs-BW gate comparison at
  :575. Role here = **floor + gate** (a classification threshold). No reweight.
- Sampling layer (`transpole.f`): the same floor `width = pole*small_width_treatment`
  at transpole.f:44-46 / untranspole 209-211, AND `jac = jac * width/width1`. Role here =
  **floor + NWA σ-reweight** (bw-transpole-nwa-jacobian.md). The `width/width1` ratio is the
  *only* place the banner.py "σ corrected assuming NWA" promise is concretely honored.
- `grep -c small_width_treatment` = 0 in `dsample.f` itself (the driver passes spole/swidth
  to transpole; the floor logic lives inside transpole, not the driver).

## Routing payoff (cases the per-file pages don't individually answer)
- "Does bwcutoff affect the integration jacobian / sampled-peak shape?" → **No** — Layer 2,
  bwcutoff absent there. (Per-file pages note the absence locally; this is the routing rule.)
- "Where is σ actually NWA-corrected vs merely floored?" → floored in **both** layers;
  σ-*corrected* only in Layer 2 (transpole jac ratio). The window-layer floor changes
  classification thresholds, not the cross-section weight.
- "Changing small_width_treatment — what moves?" → both the on/off-shell classification
  thresholds (Layer 1) AND the sub-floor-width σ reweight (Layer 2). The two effects are
  driven by the same run-card number but realized in different files/roles.

## Boundary
- LO only. NLO/FKS BW handling → amcatnlo/fks slices. MadSpin `BW_cut` → MadSpin slice.
- This is a static source fact (which file contains which symbol + the role each plays,
  grep-confirmed); not a runtime prediction — source-walk grounding suffices.
- Γ_eff throughout = `max(prwidth, prmass*small_width_treatment)`.
