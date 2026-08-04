---
description: Runtime beam-mass and partonic sqrt(s) (stot) computation in genps.f — how lpp/mass_ion set m1/m2, the ebeam<m floor auto-correction, and the full-mass invariant stot formula.
---

# Beam masses and stot (sqrt(s)) at runtime

Source: `$MADGRAPH_INSTALL/Template/LO/SubProcesses/genps.f`, block at :654-679 (common `/to_stot/stot,m1,m2`, :643). Complements beam-pdf-params.md (parser side) — this is where lpp/mass_ion turn into the actual collision energy.

## Beam mass assignment (:660-669)
Starts from `m1=m(1)`, `m2=m(2)` (the external pmass), then overrides by beam type:
- `|lpp|==1 .or. |lpp|==2` (hadron / elastic-photon-from-proton) -> `m = 0.938d0` (proton mass) (:662-663).
- `|lpp|==3` (e-/e+) -> `m = 0.000511d0` (:664-665).
- `|lpp|==4` (mu-/mu+) -> `m = 0.105658d0` (:666-667).
- `mass_ion(i) >= 0d0` -> `m = mass_ion(i)` — **overrides the lpp-derived mass** (:668-669). For a lead beam (`mass_ion = 207.9766521*0.938 ~ 195.1 GeV`) the FULL ion mass becomes the kinematic beam mass.

Note: the per-nucleon proton mass 0.938 is hardcoded for `|lpp|∈{1,2}` regardless of `nb_proton/nb_neutron` — the nucleon count does NOT change the kinematic mass here; it only enters PDF x-scaling (`nb_hadron`) in pdg2pdf.f (runtime-pdf-dispatch.md). The two ion mechanisms are decoupled: `mass_ion` sets kinematic √s; `nb_proton+nb_neutron` sets per-nucleon Bjorken-x. A heavy-ion setup needs BOTH set coherently.

## ebeam floor auto-correction (:670-671)
```
if(ebeam(1).lt.m1 .and. lpp(1).ne.9) ebeam(1)=m1
if(ebeam(2).lt.m2 .and. lpp(2).ne.9) ebeam(2)=m2
```
If a beam energy was set below the beam mass it is silently bumped UP to the mass (so the beam is at rest), unless `lpp=9` (PLUGIN). A trap for low-energy / heavy-ion setups: ebeam set below the ion mass is silently raised, no error.

## stot formula (:657-676)
- `nincoming==1` (decay / 1->N): `stot = m(1)**2` (:657-658) — the decaying particle mass².
- `nincoming==2` (collision): beam 4-momenta `pi1=(ebeam1,0,0,+pz1)`, `pi2=(ebeam2,0,0,-pz2)` with `pz=sqrt(max(ebeam^2-m^2,0))` (:672-675); then
  `stot = m1**2 + m2**2 + 2*(pi1(0)*pi2(0) - pi1(3)*pi2(3))` (:676).
  This is the FULL invariant √s including beam masses — NOT the massless `4*E1*E2` approximation. For lepton/ion beams the beam mass term is non-negligible.
- Prints `Set CM energy to <sqrt(stot)>` (:678) — visible in the survey/refine log, a quick runtime check of the effective collision energy.

## Caution
- `stot` is the *hadronic/beam* √s; the partonic ŝ is `x1*x2*stot`. dynamical_scale_choice=4 ("shat", setscales.f) uses the partonic sumdot, not this stot.
- For asymmetric beams (different ebeam1/ebeam2, or beam+fixed-target) the formula correctly accounts for the boost via the pz1*pz2 term; don't assume √s = 2*sqrt(E1*E2).
- mass_ion overriding the lpp mass is the only place the ion mass enters kinematics — if mass_ion left at default -1 for an ion run, the beam is treated as a single proton (0.938) kinematically while PDFs still per-nucleon-scale: an inconsistent setup that does NOT error. Verify mass_ion is set for ion runs.
