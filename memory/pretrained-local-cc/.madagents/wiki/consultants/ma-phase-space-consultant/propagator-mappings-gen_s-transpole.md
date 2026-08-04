---
description: The s/t-channel change-of-variable mappings (BW, t-channel 1/sqrt, 1/x, 1/x^n) encoded by gen_s + transpole, driven by the spole/swidth tables set in myamp set_peaks.
---

# Propagator mappings: gen_s, transpole, and the spole/swidth tables

Phase-space variables are remapped per channel so the integrand peaks become flat. The peak
descriptors are the `spole(maxinvar)` / `swidth(maxinvar)` arrays in common `/to_brietwigner/`,
filled by `set_peaks` (myamp.f) and consumed by `gen_s` (genps.f) -> `transpole`
(`$MADGRAPH_INSTALL/Template/LO/Source/transpole.f`).

## props.inc — where prmass/prwidth come from (read at first_time)
Generated per-process include filling `PRMASS(-i,c)`, `PRWIDTH(-i,c)`, `POW(-i,c)`.
Example DY `q q~ > z > z > l+ l-` (`<PROC_DIR>/.../P1_qq_z_z_ll/props.inc`):
`PRMASS(-1,1)=ABS(MDL_MZ)`, `PRWIDTH(-1,1)=ABS(MDL_WZ)`, `POW(-1,1)=2` — the s-channel Z takes its
mass/width straight from the model params. set_peaks reads props.inc (myamp.f:325) into the prmass/
prwidth arrays that drive every mapping decision below. (gen_mom and cut_bw also `include 'props.inc'`.)

## set_peaks decides which mapping each branch gets (myamp.f:207)
Per propagator `-i` of `this_config`:
- **s-channel with width** (`prwidth_tmp(i)>0` and `lbw(nbw)<=1`): set Breit-Wigner pole.
  `spole(-i)=prmass^2/stot`, `swidth(-i)=prwidth*prmass/stot` (myamp.f:447-448). The real width is
  kept in swidth (matters for the jacobian). Only set if the resonance can fit
  (`prmass+bwcut_for_PS*width >= xm(i)` and not identical-particle, or BW required) — myamp.f:443.
- **PDF/s-hat branch** (`i == -(nexternal-(nincoming+1))`): the BW is mapped onto the s-hat
  integration variable `j=3*(nexternal-2)-4+1` instead (myamp.f:430-442, "Setting PDF BW").
- **No-width s-channel / radiation** (`swidth==0`): falls to `setgrid(-i,xo,a,1)` — a
  collinear/soft 1/(x-a) grid preset, no analytic pole (myamp.f:451-457, 462-490).
- **t-channel** (tsgn=-1): always `setgrid(-i,xo,a,1)` with offset `a=-prmass^2/stot` (myamp.f:532-537);
  xo is the t-min cutoff from external pt/etmin/xqcut, floored at a hardwired minimum (read myamp.f:532-537).
- **s-hat final transform** (myamp.f:540-582): if no BW claimed s-hat, `spole(i)=-2` (1/s pole)
  with `swidth(i)=xo`. Emits the runtime line "Transforming s_hat 1/s" or "Transforming s_hat BW".

`bwcut_for_PS(i)` = `bwcutoff` if gForceBW=1, else a hardwired constant for the non-forced/lbw cases
(read the `5d0`-style literal at myamp.f:402-410).
Impossible on-shell configs (forced BW that can't fit) -> `write_null_results()` + `stop` (myamp.f:417-428).

## gen_s (genps.f:1363) — apply the mapping for one s-invariant
- `spole==0`: flat in s, `s=(smax-smin)*x+smin`, jac=`(smax-smin)`.
- `spole!=0` and `spole^2<smax`: `CALL TRANSPOLE(spole^2/smax, spole*swidth/smax, x, s, jac)`,
  then rescale by smax. Else fail (pole above kinematic max).
- `dsqrt_shatmax` (from run_card) caps smax (genps.f:1392-1394).

## transpole (transpole.f:1) — the actual change of variable, branch on `pole` sign
- `pole>0`  : **Breit-Wigner**. `y=pole+width*tan(width*z)`, z linear in x between
  atan limits; jac=`(width/cos(width*z))^2*(zmax-zmin)`. Linear fallback for x<del or x>1-del
  (del=1d-22) so the full range stays reachable (transpole.f:43-67).
- `-1<pole<0`: **t-channel** `1/sqrt(x^2+width^2)`, log-spaced for x<0.5, identity for x>0.5
  (transpole.f:68-80).
- `pole==-15` (width>0): **1/x** soft pole, `y=width^(1-z)` above cutoff xc (transpole.f:84-98).
- `pole>=-2` (width>0): **1/x^n** general power pole (incl. the 1/s s-hat case pole=-2),
  `y=a+b*z^(pole+1)` above cutoff (transpole.f:99-115).

`small_width_treatment` (common `/narrow_width/`) floors width at `pole*small_width_treatment` so
NWA-narrow resonances stay integrable (transpole.f:44-46).

## The inverse map (UNTRANSPOLE) — consumed at VEGAS grid-recording, not in genps
`transpole` has an inverse `untranspole` (recovers `x` from `y`). The LIVE callers are in
`$MADGRAPH_INSTALL/Template/LO/Source/dsample.f:1906,2591`: when VEGAS records a sampled point into
its grid, a BW-mapped variable (`swidth(j)>0`) is `untranspole`'d back to the FLAT variable so the
grid bins and `xmin/xmax` track the un-biased coordinate (dsample.f:1903-1913). So the spole/swidth
BW map I install is round-tripped: `transpole` forward at sampling (gen_s), `untranspole` back at
grid-recording. The grid-binning itself is the numerical/VEGAS slice; the *map object* being inverted
is mine.
- `genps.f` ALSO defines `ungen_s` (genps.f:1572, the gen_s inverse calling UNTRANSPOLE) — but it has
  NO caller in the LO template (dead twin of the live dsample.f path). Don't cite ungen_s as runtime.

## Width scheme at integration: FIXED real width, NOT running, NOT complex-mass
The phase-space BW map is a **constant-width** change of variables. `transpole` pole>0 branch is
`y = pole + width*tan(width*z)` (transpole.f:52-54) — a fixed-Γ (relativistic-BW-flavoured) tangent
substitution. `width` here is `swidth = prwidth*prmass/stot` with `prwidth` the **real, energy-
independent** model width from props.inc. There is no s-dependent (running) width and no complex mass
anywhere in the sampling map.
- `prmass`/`prwidth` are declared `double precision` (genps.f:1867-1868) — the arrays are structurally
  real; they cannot carry a complex mass.
- props.inc is written with `abs(mass)` / `abs(width)` of the *real* model parameter names
  (export_v4.py:2117-2125, e.g. `abs(MDL_MZ)`, `abs(MDL_WZ)`).

## Complex-mass scheme does NOT change the phase-space path (CMS is ME-side only)
`write_props_file` (export_v4.py:2097-2139) has **no `complex_mass` branch** — it emits the same real
`abs(...)` mass/width regardless of CMS. Grep of myamp.f, genps.f, transpole.f for
`complex|cmass|running.*width` returns **nothing**. So CMS changes only the matrix-element propagator
denominator (HELAS builds the wavefunction with the complex mass `CMASS_*` — that construction is
ALOHA/HELAS territory, see complex_mass handling export_v4.py:7317-7411 for the model include, not
props.inc). `gForceBW`, `set_peaks`, spole/swidth, the BW peak sampling, and channel/ICONFIG
construction are all **CMS-invariant**. The channel decomposition and importance-sampling map are
identical with or without `set complex_mass_scheme True`.

## Zero-width s-channel resonance (Γ=0): the BW map degenerates to a grid, no div-by-zero
The BW branch only fires when `swidth = prwidth*prmass/stot > 0`. If the resonant propagator has Γ=0
(prwidth=0), `swidth` stays 0, `spole/swidth` for that invariant is **never set** to a BW pole, and
set_peaks routes the invariant to `setgrid(-i,xo,a,1)` — a power-law/collinear grid centred at the pole
location `a=prmass²/stot` (myamp.f:452-458). So the map degrades from the analytic tangent-BW to a
1/x^pow grid: the sharp resonance peak is NOT importance-sampled as a Lorentzian, only as a power-law
bump around the pole. The `swidth>0` gate means `transpole`'s BW branch (and its `atan(.../width)`) is
never reached with width=0 → no division by zero. (A *tiny but nonzero* width instead reaches transpole
and is floored at `pole*small_width_treatment`, transpole.f:44-46 — a different path from exact Γ=0.)
The physical consequence of a genuinely zero-width resonance sitting on the integration domain (a
delta-function peak the grid cannot resolve) is a numerical/VEGAS-convergence concern, not a mapping-
construction one.

## Cautions
- The spole/swidth grids are *integration biasing only*; the on-shell accept/reject is a separate
  test in `cut_bw` (see gforcebw-cut_bw-onshell page). A BW mapped for sampling is not the same as a
  BW enforced on the event.
- `setgrid` lives in `dsample.f` (VEGAS slice territory) — I cite it as the downstream consumer of
  set_peaks' xo/a, not for its internal bin layout.
- A hardwired multiple of width (read the literal at myamp.f:406,443) is the phase-space BW window for
  non-forced resonances; the *event-level* on-shell window uses `bwcutoff` and is the bw-window slice's
  detail.
