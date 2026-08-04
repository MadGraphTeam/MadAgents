---
description: BW phase-space sampling transform (transpole/untranspole, LO Source/transpole.f) — small_width_treatment floor AND the NWA σ-correction jac *= width/width1; floor protects tiny-NONZERO widths only (swidth>0 dsample.f:1393 gate), exactly-zero → setgrid fallback no warning; width NOT replaced in ME propagator (coupl.inc), only sampling+window. v3.7.1
---

# BW sampling transform + NWA jacobian correction (transpole.f)

Cite `$MADGRAPH_INSTALL/Template/LO/Source/transpole.f`, v3.7.1. This is where the BW
phase-space sampling actually happens, and — importantly — where the NWA σ-correction the
banner comment promises is concretely applied. Earlier pages (bw-runcard-knobs.md,
bw-setpeaks-psgrid.md) recorded the `small_width_treatment` *floor* of Γ_eff but not that
the σ-correction lives in the jacobian here.

## The two subroutines
- `Subroutine transpole(pole1,width1,x1,y,jac)` (line 1): maps a flat x∈[0,1] to a
  BW-distributed y with the BW jacobian. Forward inverse-CDF sampling. Header comment
  (lines 2-10): "transfers evenly spaced x values ... to y values with a pole at y=pole
  with width". `pole<0` branches handle 1/sqrt(x²+a²) (t-channel) and 1/x poles instead.
- `Subroutine untranspole(pole1,width1,x,y1,jac)` (line 171): the inverse (y→x with
  jacobian). Symmetric small-width handling.

## Where it's driven (closes the set_peaks → sampling loop)
- `$MADGRAPH_INSTALL/Template/LO/Source/dsample.f:1396`:
  `call transpole(spole(ij),swidth(ij),y,x,wgt)` — guarded by `if (swidth(ij).gt.0d0)`
  (dsample.f:1393). `untranspole` called at dsample.f:1906.
- `spole`/`swidth` are exactly the per-pole arrays set by `set_peaks` in myamp.f
  (bw-setpeaks-psgrid.md, lines 429-449). Recall set_peaks keeps `swidth = prwidth` (the
  REAL width, not Γ_eff) — so the small-width floor below is applied HERE at sampling time,
  not baked into swidth upstream.

## small_width floor + NWA σ-correction (the non-obvious part)
Both subroutines, BW branch (`pole .gt. 0d0`):
- transpole.f:44-47:
  ```
  if (width.lt.pole*small_width_treatment)then
     width = pole * small_width_treatment
     jac = jac * width/width1
  endif
  ```
- untranspole.f:209-211: identical floor and `jac = jac * width/width1`.

`width1` is the input (real) width; `width` is the floored value
(`pole*small_width_treatment`). When the real width is below the floor:
1. The BW transform is performed with the WIDER floored width (so the sampling grid covers
   a finite, numerically tractable peak instead of a delta-like spike).
2. The jacobian is multiplied by `width/width1 = floored/real > 1`. This ratio is the
   **NWA correction factor**: it rescales the integration weight so the cross-section
   integrated over the artificially-widened resonance reproduces the NWA result for the
   true narrow width. This is the concrete implementation of banner.py's
   small_width_treatment comment ("cross-section will be corrected assuming NWA").
- `common/narrow_width/small_width_treatment` (transpole.f:34-35, 192-193) — same common
  block as myamp.f and run.inc (bw-runcard-knobs.md).

## Cautions
- The σ-correction is a single multiplicative jacobian ratio applied per BW pole at
  sampling time; it is the ONLY place the "correct σ assuming NWA" promise is honored in
  LO phase space. If you reason about a sub-floor width's cross-section, the literal width
  is NOT used — the floored width + `width/width1` reweight is. Source-visible; the σ
  outcome itself is a runtime quantity (not probed here).
- `bwcutoff` does NOT appear in transpole.f (`grep bwcutoff` = 0 hits). The window/cutoff
  decisions are upstream (myamp.f set_peaks / cut_bw); transpole only does the sampling
  transform on the spole/swidth it's handed. So "changing bwcutoff" never touches this
  jacobian directly.
- Floor comparison is `width .lt. pole*small_width_treatment` (strict <); a width exactly
  at the floor is left untouched (no jacobian rescale).
- transpole.f also encodes the t-channel (1/sqrt) and 1/x (pole==-15d0) transforms in the
  `pole<=0` branches — those are phase-space-slice territory, recorded here only for
  completeness; this slice owns the BW (`pole>0`) branch and its small-width handling.

## Zero-width vs tiny-nonzero-width: the floor protects only NONZERO widths (v3.7.1)
Critical distinction, verified myamp.f + dsample.f. `small_width_treatment` does NOT rescue
a *literally zero* s-channel width — it only helps tiny *nonzero* widths:
- `dsample.f:1393` gates the transform: `if (swidth(ij) .gt. 0d0) then call transpole(...)`.
  `swidth` is the REAL width (set_peaks keeps `swidth = prwidth*prmass/stot`, myamp.f:411,
  417 — "keep the real width here (important for the jacobian)"). So when `prwidth==0`
  exactly → `swidth==0` → **transpole is never called** → the small_width floor + NWA
  `jac*=width/width1` at transpole.f:44-47 never fires. The floor rescues a tiny nonzero
  width; it does nothing for an exactly-zero one.
- Zero-width fallback: `myamp.f:450-456` `if (swidth(-i) .eq. 0d0 ...) call setgrid(-i,xo,a,1)`
  (comment: "Set grid in case there is no BW (radiation process)") — a plain power-law grid
  around M²/stot, NOT a BW importance-sampling peak. No NWA σ-correction, **no error, no
  warning** for a zero-width s-channel that can go on-shell (the 1/(s−M²) integrand is then a
  genuine unregulated pole → wildly-fluctuating σ / huge MC uncertainty, silently). This
  matches the hand-doc's "delta-function / never samples the pole / no clear error" claim in
  practical outcome; the precise mechanism is "swidth>0 guard skips transpole → setgrid."
- Note the window/classification layer floors independently: `prwidth_tmp = max(prwidth,
  prmass*small_width_treatment)` (myamp.f:132, 330, 398) IS >0 even for zero real width, so
  the on-shell test / window uses a floored width — but that floor never reaches the
  *sampling* jacobian, which sees the raw `swidth`.

## Where the width is / isn't replaced (location precision for the "ME evaluation" claim)
The hand-doc says the width is "replaced ... for the ME evaluation." Imprecise: the
replacement (`pole*small_width_treatment`) lives in the phase-space **sampling** transform
(transpole.f) and the **window** floor (`prwidth_tmp`, myamp.f) — NOT in the matrix-element
BW propagator denominator. The amplitude's propagator width comes from `coupl.inc` (the
operative param-card width, fixed Γ) and is untouched by small_width_treatment; the NWA
`jac*=width/width1` at sampling time is what reconciles σ. So "replaced for the ME
evaluation" → read as "floored for sampling + window, σ NWA-corrected at sampling."
