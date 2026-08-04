---
description: Cut-variable identity in the LO cuts — the generic eta cut + generic DR cut use TRUE LAB-FRAME RAPIDITY (rap), not pseudorapidity (only photon-iso uses pseudorap); the ptX cut enforces transverse MOMENTUM pt despite the "Et"/etmin label. The enforced variable differs from the run_card name/printed label; moot for massless cut classes.
---

# Cut-variable identity: rapidity vs pseudorapidity, and pt vs Et

Source: `$MADGRAPH_INSTALL/Template/LO/SubProcesses/cuts.f`,
`$MADGRAPH_INSTALL/Template/LO/Source/kin_functions.f`,
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/genps.f`. MG5_aMC v3.7.1.
This is the variable-and-frame subtlety none of the per-filter pages state. Pretraining
intuition that the run_card "eta" cut is pseudorapidity is WRONG for the generic cuts.

## The generic eta cut is TRUE RAPIDITY y, evaluated in the LAB frame
- cuts.f:424-433 (rapidity min/max filter, cuts-f-filter.md step 10): rejects on
  `abs(rap(p(0,i)))` vs `etamin(i)`/`etamax(i)`. The function called is `rap`, NOT a
  pseudorapidity function.
- `rap(p)` is defined at kin_functions.f:95-136:
  `pm = p(0)` (the ENERGY, not |p|); `rap = 0.5d0*dlog((pm+p(3))/(pm-p(3))) + cm_rap`.
  That is the true rapidity `y = 0.5 ln((E+pz)/(E-pz))`, plus a frame-boost term `cm_rap`.
  (The commented-out line :128 `pm=dsqrt(p1²+p2²+p3²)` would have made it PSEUDOrapidity;
   it is disabled — confirming the active path is rapidity, by deliberate choice.)
- `cm_rap` is the parton-CM-to-LAB boost. PASSCUTS receives momenta in the parton CM rest
  frame (cuts.f:30), but the cut is applied in the LAB frame: `set_cm_rap` must be true or
  `rap` does `print *,'Need to set cm_rap before calling rap'; stop` (:124-127).
  cm_rap is set in genps.f (:258-259, also :285-286, :345-346, :360-...):
  `cm_rap = 0.5d0*dlog(xbk(1)*ebeam(1)/(xbk(2)*ebeam(2)))` — the per-event longitudinal
  boost from Bjorken-x and the two beam energies. So the `etaj` cut is a LAB-frame |y| cut,
  not a CM-frame nor a pseudorapidity cut.
- For ASYMMETRIC beams (ebeam1 != ebeam2) cm_rap != 0 even at xbk1==xbk2: the rapidity
  window is centred on the boosted lab frame, not the CM. For symmetric pp it averages to 0
  per the x's.

## The generic DR cut is also RAPIDITY-based (Δy, φ), not Δη
- The ΔR distance is `R2(p1,p2)` at kin_functions.f:25-44:
  `R2 = (DELTA_PHI(P1,P2))**2 + (rap(p1)-rap(p2))**2`. So `drXY` (drjj/drbb/draa/drll/draj/
  drjl/drab/drbl/dral + maxes) compare `√(Δφ² + Δy²)` — the FastJet / hadron-collider
  rapidity-φ ΔR convention, NOT the Δη convention. (cuts.f:437-452 calls `r2(p(0,i),p(0,j))`
  which is this R2; the value is then compared to the pre-squared r2min/r2max — see
  cuts-f-filter.md step 11.)
- kin_functions.f header (:5) even mislabels it "distance in eta,phi" — the code uses `rap`.
  Trust the code, not the comment.

## Photon isolation is the ONE place pseudorapidity is used
- The Frixione cone separation `iso_getdr` (cuts.f:1273-1283) builds
  `deta = iso_getpseudorap(p1) - iso_getpseudorap(p2)`, `dphi = iso_getdelphi(...)`,
  `iso_getdr = sqrt(dphi² + deta²)`.
- `iso_getpseudorap` (cuts.f:1286-1300): `th=atan2(pt,pl); eta = -log(tan(th/2))` — true
  PSEUDOrapidity η, computed from the momentum only (no energy, no cm_rap boost).
- So the photon-isolation cone radius R0gamma is measured in (Δη, Δφ) IN THE CM FRAME
  (no cm_rap added), while the generic `draj`/`draa` are in (Δy, Δφ) IN THE LAB FRAME.
  Two different metrics AND two different frames for "ΔR" depending on which cut you set.
- Standalone `eta(p)` (pseudorapidity) exists at kin_functions.f:656 but is NOT in the
  generic eta/DR cut path; the cut path uses `rap`.

## The ptX cut enforces transverse MOMENTUM pt, despite the "Et"/etmin label
- The per-particle pt filter (cuts.f:330-340) rejects on `pt(p(0,i))` vs `etmin(i)`/`etmax(i)`.
  The compared quantity is the function `pt`, the array is named `etmin`/`etmax`, and the
  PASSCUTS cut-table header prints `Et >` (cuts.f:216, cuts-f-filter.md). The LABEL and the
  ARRAY NAME say "Et"; the ENFORCED quantity is pt.
- `pt(p)` (kin_functions.f:212-228): `√(px²+py²)` — transverse momentum.
- `et(p)` (kin_functions.f:188-210): `et = p(0)*pt/√(pt²+pz²)` = E·sinθ — transverse ENERGY,
  a DIFFERENT quantity. et == pt only for a massless particle (E=|p|).
- So `ptj`/`ptb`/`pta`/`ptl`/`misset` (+ their max counterparts) are transverse-MOMENTUM cuts.
  The "Et >" line in the cut table is a cosmetic misnomer; do not read it as a transverse-energy
  cut. (Same massless caveat as rapidity: the cut classes are massless, so pt==et in the common
  case; the label only misleads for a massive object reaching the filter, e.g. via a PDG cut.)
- misset (missing-Et) is likewise a vector-pt sum: cuts.f:343 comment "missing Et defined as
  the vector sum over the neutrino's pt" — it sums neutrino 4-momenta and takes pt of the sum
  (cuts-f-filter.md step 6), not a per-neutrino transverse-energy sum.

## Why it usually doesn't bite — and when it does
- The cut classes are MASSLESS objects (light jets/b/photons/leptons; >20 GeV resonances
  have do_cuts=.false. and never reach the eta/DR filter — see cuts-f-filter.md /
  pdg-cuts-and-smin.md). For a massless particle y == η, so the rapidity-vs-pseudorapidity
  distinction is numerically moot for the etaX cuts and the generic DR cuts in the common case.
- It DOES matter when:
  - A massive object survives to the filter via a PDG-specific cut (pt/eta_*_pdg bypass
    do_cuts, pdg-cuts-and-smin.md): its `eta_min_pdg`/`eta_max_pdg` is a true-rapidity cut,
    so for a heavy state |y| != |η| and a "|η|<2.5" intent set via eta_max_pdg is actually |y|<2.5.
  - Beams are asymmetric (different ebeam1/ebeam2, e.g. some ep / fixed-target-style setups):
    cm_rap != 0 shifts the whole rapidity window into the lab frame.
  - A user compares MadGraph parton-level "eta" cuts against a detector pseudorapidity
    acceptance: the generic etaX is rapidity, the photon-iso cone is pseudorapidity — they are
    not the same variable, and only one carries the lab boost.

## Cautions
- Run_card `etaj`/`etab`/`etaa`/`etal` (+mins) are LAB-FRAME TRUE-RAPIDITY cuts, not
  pseudorapidity. Numerically identical to η only for massless objects.
- Generic `drXY` cuts use Δy (rapidity), the photon-iso cone (R0gamma) uses Δη
  (pseudorapidity) — different metric AND different frame (lab vs CM). Don't assume one
  R0gamma-style number transfers to a draj-style number for a massive or boosted object.
- `ptj`/`ptb`/`pta`/`ptl`/`misset` are transverse-MOMENTUM cuts, not transverse-energy,
  despite the `etmin`/`etmax` array names and the printed `Et >` cut-table label. pt==Et only
  for massless objects.
- `rap` hard-`stop`s if `set_cm_rap` is false (kin_functions.f:124-127); genps.f sets it
  per-event before cuts run, so in the normal survey/refine path it is always set. A custom
  driver that calls PASSCUTS without going through genps would crash here.
- This is the LO path (Template/LO). NLO rapidity handling is amcatnlo slice.
