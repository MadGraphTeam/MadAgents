---
description: set_peaks phase-space grid use of bwcutoff/5σ windows, impossible-onshell stop, and the s-hat 1/s-vs-BW transform gate using small_width_treatment, myamp.f v3.7.1
---

# set_peaks / phase-space BW-window mechanics (myamp.f)

Cite `$MADGRAPH_INSTALL/Template/LO/SubProcesses/myamp.f`, `subroutine set_peaks` (from
line 207), v3.7.1. This is the phase-space grid setup; channel decomposition / BW
propagator mapping at integration time is the phase-space slice. We own the bwcutoff /
small_width_treatment usage visible here.

## Per-resonance lower-mass grid bound (lines 399-411)
For a resonance leg (`prwidth_tmp>0`), the grid lower bound xm(i) is widened by a window:
- gForceBW=1: `xm(i)=max(xm(i), prmass - bwcutoff*Γ_eff)`, `bwcut_for_PS(i)=bwcutoff`
  (myamp.f:402-404).
- else if lbw(nbw)=1 (require BW): `xm(i)=max(xm(i), prmass - 5d0*Γ_eff)`,
  `bwcut_for_PS=5d0` (myamp.f:405-407).
- else: `bwcut_for_PS=5d0` (myamp.f:408-409).
=> Same dual-window pattern as `cut_bw`: bwcutoff only for forced legs; otherwise 5σ.

## Impossible-onshell guard => write_null_results + stop (lines 413-428)
Stops the channel (writes null results) when:
- lbw=1 and `prmass + bwcut_for_PS*Γ_eff < xm(i)` (window above the kinematic min) OR
  `prmass - bwcut_for_PS*Γ_eff > sqrt(stot)` (window above CM energy); OR
- gForceBW=1 and `prmass + bwcutoff*Γ_eff < xm(i)`; OR
- lbw=2 and gForceBW=1 (require-off-shell conflicts with forced-on-shell).
This is where a require-BW that is kinematically impossible silently zeroes the channel.

## BW pole setting for integration (lines 429-449)
- For lbw<=1 resonances, sets spole/swidth (the BW peak for the phase-space transform).
- s-hat case (myamp.f:436-442): uses BW if `prmass>=xm(i)` and `prmass<sqrt(stot)` and not
  identical-particle, OR lbw=1. **swidth keeps the REAL width** (`prwidth`, not Γ_eff) for
  the jacobian (comment line 441,448).
- non-s-hat (myamp.f:443-449): BW if `prmass + bwcut_for_PS*Γ_eff >= xm(i)` and not
  identical, OR lbw=1.

## s-hat 1/s-vs-BW transform gate (lines 568-581)
- myamp.f:575: chooses 1/s transform over BW when
  `smin/stot > spole(i) + bwcutoff*max(swidth(i), spole(i)*small_width_treatment)`.
- This is the one place `bwcutoff` and `small_width_treatment` combine in the integration
  transform: small_width_treatment floors the per-pole width in the comparison so a
  near-zero-width pole still gets a finite window before falling back to 1/s.

## Cautions
- bwcutoff controls the PS grid window ONLY for forced (decay-chain, gForceBW=1) legs; all
  other resonances use a hardcoded 5σ. Changing bwcutoff in the run_card does not widen the
  PS grid for ordinary s-channel resonances. CAVEAT: this forced-only rule is the
  set_peaks-grid behavior; the s-hat transform gate (line 575) below applies bwcutoff
  UNCONDITIONALLY to every pole. Full taxonomy: bw-bwcutoff-scaling-regimes.md.
- The impossible-onshell branch calls `stop` after `write_null_results()` — a mis-specified
  require-BW (lbw=1) or a forced BW above CM energy yields a zero channel, not an error
  message in the usual log. Source-visible; runtime symptom not probed here.
