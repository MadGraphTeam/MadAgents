---
description: The cut_bw on-shell test in myamp.f — bwcutoff×Γ_eff window, Γ/M narrow gate, gForceBW flag, lbw require/exclude encoding, dual onshell definitions, zero-vs-tiny-width consumption gate
---

# cut_bw on-shell test (myamp.f)

Cite `$MADGRAPH_INSTALL/Template/LO/SubProcesses/myamp.f`, `logical function cut_bw(p)`
lines 2-204, v3.7.1. Returns `.true.` => event is CUT (fails); default `.false.` (passes,
line 76).

## Inputs consumed (this slice's read-only artefacts)
- `lbw(0:nexternal)` in `common/to_BW/` (myamp.f:50-51) — per-resonance BW requirement
  encoding: **1 = require on-shell (BW)**, **2 = exclude/require off-shell**, else = no cut
  (myamp.f:88-94 print, 196-198 enforce). NOT from decayBW.inc — set at RUNTIME by
  `DeCode(jconfig,lbw(1),3,nexternal)` (base-3) in madevent_driver.f from the requested
  config's fractional BW sub-code; per-channel, not per-topology (bw-gforcebw-lbw-provenance.md).
- `gForceBW(-max_branch:-1,lmaxconfigs)` via `include 'decayBW.inc'` (myamp.f:64-65) —
  per-leg forced-BW flag: **1 = forced on-shell**, **2 = on-shell-forbidden s-channel**,
  **0 = no force**. Static `data` array, from the decay-chain leg `onshell` flag
  (True/False/None → 1/2/0; base_objects.py:2111, export_v4.py:5884). gForceBW is the ONLY
  array decayBW.inc carries; `lbw` is NOT in it (runtime DeCode — bw-gforcebw-lbw-provenance.md).
  Writing is out of slice; consumed here.
- `prmass`/`prwidth(-nexternal:0,lmaxconfigs)` from `props.inc` (myamp.f:28-29,80), from
  the operative param-card via coupl.inc.

## Effective width floor
- myamp.f:131-135: `prwidth_tmp = max(prwidth, prmass*small_width_treatment)` when
  `prwidth>0`, else 0. This is Γ_eff used everywhere below.

## Zero width vs tiny width (runtime consumption of the width value)
The width value enters the BW machinery only through `prwidth(i,iconfig)` (real width from
the operative param-card via coupl.inc). Two distinct sub-floor regimes — do NOT conflate:
- **Tiny but positive width** (`0 < prwidth < prmass*small_width_treatment`): the leg DOES
  enter the BW loop (gate `prwidth .gt. 0d0`, myamp.f:123, increments `nbw`), gets an `lbw`
  index, and is tested with the FLOORED Γ_eff = `prmass*small_width_treatment` (default
  registered at banner.py:4452, bw-runcard-knobs.md). Window is finite, sampling uses the floor + NWA σ-reweight
  (bw-transpole-nwa-jacobian.md). This is the small_width_treatment regime.
- **Exactly zero (or negative) width** (`prwidth <= 0`): the leg is NEVER BW-treated.
  - In `cut_bw`: the `if (prwidth .gt. 0d0)` gate at myamp.f:123 is FALSE → `nbw` not
    incremented, leg skipped entirely, no `lbw` index, no window test. `prwidth_tmp` is
    set to 0d0 (myamp.f:134) but that branch is unreached for a zero-width leg here.
  - In `set_peaks` (same file): gates at myamp.f:329/399/417/429 all require
    `prwidth(_tmp) .gt. 0`; a zero-width pole gets `spole=0`/`swidth=0` (myamp.f:358-359)
    and falls to the non-BW grid — the radiation grid (`swidth==0`, myamp.f:451-457) or the
    `1/x^pow` else-branch (myamp.f:462). NEVER a BW grid.
  - Consequence: a width of exactly 0 makes the propagator a fixed-mass / non-resonant pole
    for sampling and removes it from all on/off-shell enforcement. `small_width_treatment`
    does NOT rescue a zero width — the floor only fires inside the `prwidth>0` branch, so
    the floor is `max(0,...)` only conceptually; the code never reaches it for `prwidth==0`.
- Caveat (probe-candidate): the param-card path that produces a literal 0d0 vs a tiny
  nonzero width (auto-width, hardcoded 0, decay-product width) is madwidth/param-card
  territory; this slice only consumes the resulting `prwidth` value.

## "On-shell for Les Houches" test (first definition, lines 136-139)
```
onshell = (abs(xmass - prmass) .lt. bwcutoff*prwidth_tmp
          .and. (prwidth_tmp/prmass .lt. 0.1d0 .or. gForceBW.eq.1))
```
Two combined conditions:
1. Mass within `bwcutoff*Γ_eff` of pole (the window).
2. **Narrow-resonance gate**: Γ_eff/M < 0.1, UNLESS the leg is forced on-shell
   (gForceBW=1). So a broad resonance (Γ/M ≥ 0.1) is NOT treated as on-shell unless forced.

### When onshell (lines 140-178)
- gForceBW=2 AND sde_strat=1 (myamp.f:142-145): on-shell forbidden => `cut_bw=.true.`, return.
- else `OnBW(i)=.true.` set, then cleared if decay to identical particle (idenpart logic,
  146-178): identical FS daughter always clears; otherwise the resonance closer to its
  pole keeps OnBW.

### When NOT onshell but forced (lines 179-184)
- gForceBW=1 and not on-shell => `cut_bw=.true.`, return (forced BW failed the window).

## Phase-space on-shell test (second definition, lines 188-200)
Re-computes `onshell` with a DIFFERENT window:
- gForceBW=1 (decay-chain syntax): window = `bwcutoff*Γ_eff` (myamp.f:189-190).
- else: window = **5d0*Γ_eff** (hardcoded 5σ, NOT bwcutoff) (myamp.f:192-193).

Then the lbw enforcement (myamp.f:196-198):
```
if (onshell .and. lbw(nbw).eq.2 .or. .not.onshell .and. lbw(nbw).eq.1) cut_bw=.true.
```
=> require-on-shell (lbw=1) fails if off-shell; exclude (lbw=2) fails if on-shell.

## Key source-visible facts / cautions
- TWO distinct windows live in this function: `bwcutoff*Γ_eff` (Les-Houches tag + forced
  legs) vs hardcoded `5*Γ_eff` (non-forced lbw enforcement + set_peaks grid). bwcutoff
  does NOT control the 5σ enforcement window for non-decay-chain resonances. NOTE: the
  Les-Houches tag (line 137) is bwcutoff-scaled for ALL legs, not just forced ones — only
  the enforcement onshell (190/193) is forced-only. Full taxonomy across all 6 bwcutoff
  sites: bw-bwcutoff-scaling-regimes.md.
- **bwcutoff is NEVER inert regardless of gForceBW (0, 1, or 2).**
  Prior mistake: "gForceBW=0 makes bwcutoff inert." Correction via Regime A: the
  Les Houches tag at myamp.f:136-139 uses `bwcutoff*prwidth_tmp` for ALL legs unconditionally;
  the s-hat transform gate at myamp.f:575 also uses bwcutoff for ALL legs. gForceBW
  does NOT gate the Regime A sites. Even for Regime B (enforcement/guard), gForceBW=1
  makes bwcutoff MANDATORY (not optional) — the 5σ fallback for gForceBW≠1 is a narrower
  window, not an inert bwcutoff.
- The Γ/M<0.1 narrow gate only affects the FIRST (Les Houches) onshell; the second
  (enforcement) onshell has no narrow gate.
- gForceBW=2 hard-cut is gated on sde_strat=1; with sde_strat=2 the forbidden-s-channel
  cut does not fire here.
- Loop counter `nbw` indexes lbw; it increments only for legs with prwidth>0 and skips
  t-channel/initial legs (myamp.f:115-124) — lbw indexing is by BW-eligible s-channel order.
