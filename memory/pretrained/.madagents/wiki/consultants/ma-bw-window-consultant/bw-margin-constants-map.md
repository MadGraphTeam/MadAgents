---
description: The four LO BW window/threshold constants (bwcutoff / 5σ / 3σ / 0.1d0 narrow-gate) and which (stage × leg-class) cell each governs — the cross-stage margin taxonomy, v3.7.1
---

# LO BW margin constants — the (stage × leg-class) map

Cites `$MADGRAPH_INSTALL/Template/LO/SubProcesses/myamp.f` and
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_symmetry.f`, v3.7.1. Lifts a
deeper rule out of the per-stage pages (bw-onshell-test-cutbw.md, bw-setpeaks-psgrid.md,
bw-bwcutoff-scaling-regimes.md, bw-symmetry-failconfig.md): the LO BW machinery does NOT
use one window — it uses **four distinct constants**, and the one that applies depends on
the **(stage, leg-class)** cell, not on any global rule. To answer "what is the on/off-shell
window for resonance Y at stage Z?", look up the cell.

## The four constants
- **`bwcutoff`** — run-card param, default registered at banner.py:4305 (bw-runcard-knobs.md).
  A *window multiple* (M ± bwcutoff·width).
- **`5d0`** (5σ) — hardcoded window multiple, the non-forced fallback.
- **`3d0`** (3σ) — hardcoded, **unique to one site** (symmetry BW_Conflict mass bound).
- **`0.1d0`** — hardcoded, a *ratio threshold* on Γ/M (the narrow-resonance gate), NOT a
  window multiple. Categorically different from the other three.

## The map (every grep-confirmed site, v3.7.1)

| Stage / site | leg-class | constant | source line | effect |
|---|---|---|---|---|
| Les-Houches onshell tag | ALL legs (unconditional) | **bwcutoff** | myamp.f:137 | sets OnBW for LHE/idenpart |
| Narrow gate (within LH tag) | non-forced only | **0.1d0** (Γ/M) | myamp.f:138 | broad (Γ/M≥0.1) not onshell unless gForceBW=1 |
| cut_bw enforcement onshell | gForceBW=1 | **bwcutoff** | myamp.f:190 | window for the event cut |
| cut_bw enforcement onshell | non-forced | **5d0** | myamp.f:193 | window for the event cut |
| set_peaks PS-grid lower bound | gForceBW=1 | **bwcutoff** | myamp.f:404 (`bwcut_for_PS=bwcutoff`) | grid window |
| set_peaks PS-grid lower bound | non-forced | **5d0** | myamp.f:406-409 (`bwcut_for_PS=5d0`) | grid window |
| set_peaks impossible-onshell guard | gForceBW=1 | **bwcutoff** | myamp.f:422 | write_null_results+stop |
| set_peaks impossible-onshell guard | lbw=1 non-forced | **bwcut_for_PS** (=5d0) | myamp.f:419-421 | write_null_results+stop |
| s-hat 1/s-vs-BW transform gate | ALL poles (unconditional) | **bwcutoff** | myamp.f:575 | choose 1/s over BW (combines w/ small_width_treatment) |
| symmetry BW_Conflict mass bound | non-iden legs | **3d0** | madevent_symmetry.f:381 (`+3d0*prwidth`) | conflict mass floor |
| symmetry failConfig | gForceBW=1 | **bwcutoff** | madevent_symmetry.f:525 | DROP config (failConfig=.true.) |
| symmetry failConfig | iarray=1 (conflicted non-forced) | **5d0** | madevent_symmetry.f:533 | DROP config (failConfig=.true.) |

## The rule that no single per-stage page gives you
1. **bwcutoff is the forced-leg window everywhere it bites EXCEPT the two unconditional
   Regime-A myamp sites** (LH tag :137, s-hat gate :575), where it scales ALL legs/poles.
   (Regime A/B detail: bw-bwcutoff-scaling-regimes.md.) The symmetry-program bwcutoff
   (:525) is forced-only — no Regime A there.
2. **5σ is the non-forced fallback** at three different stages (cut_bw enforcement :193,
   set_peaks grid :406, symmetry failConfig conflicted :533) — but with DIFFERENT leg-class
   gates: enforcement/grid use lbw/default; failConfig uses iarray=1 (conflicted). Same
   number, different selection logic.
3. **3σ exists at exactly one site** (madevent_symmetry.f:381) and is a *conflict mass
   bound*, not an on/off-shell window. Do not generalize it to any other stage.
4. **0.1d0 is a ratio, not a window** — it gates whether a broad resonance is even eligible
   for onshell treatment in the FIRST (LH) onshell definition only. The second (enforcement)
   onshell has no narrow gate.

## Cross-stage cases this catches (the generalization payoff)
- "Is the symmetry-time window the same as the integration-time window for a non-forced
  conflicted leg?" → BOTH 5σ, but the symmetry one (failConfig :533) **drops the config**
  at symfact.dat time; the integration one (set_peaks :419) **zeroes the channel** at
  integration. Same number, different lifecycle stage, different failure mode.
  (failConfig is EARLIER — bw-symmetry-failconfig.md.)
- "Does lowering bwcutoff narrow a non-forced resonance's window anywhere?" → NO at any 5σ
  cell (enforcement/grid/failConfig-conflicted), NO at the 3σ cell, YES at the two
  unconditional Regime-A cells (:137, :575). The answer is per-cell, not global.
- "Which constant floors a near-zero width?" → NONE of these four; that is
  `small_width_treatment` (Γ_eff floor / NWA reweight, a separate axis —
  bw-param-layer-map.md). The four margin constants multiply an ALREADY-floored Γ_eff
  (myamp.f:132/:330) — except the symmetry program, which is NOT Γ_eff-floored (uses real
  prwidth; grep small_width_treatment madevent_symmetry.f = 0).

## Boundary
- LO only. NLO uses a single unconditional `bwcutoff*real_width` with NO 5σ/3σ/0.1d0 and no
  Γ_eff floor (bw-nlo-window-sites.md). Sampling-layer transpole.f has NO margin constant —
  it floors the width and reweights the jacobian, never windows (bw-transpole-nwa-jacobian.md).
- This is a static source map (which constant at which line, grep/sed-confirmed across both
  files); the per-process effect of any cell firing is a runtime quantity, not
  probed here.
