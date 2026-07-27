---
description: PhotonFlux.f algorithm layer — epa_lepton(IWW)/epa_proton(EPA) flux formulas with HARDCODED Thomson alpha (not model alpha), ion coherent-Z enhancement, and get_ion_pdf isospin rotation + double-normalization. The physics runtime-pdf-dispatch.md only names.
---

# Photon-flux + ion-PDF algorithm (PhotonFlux.f)

Source: `$MADGRAPH_INSTALL/Template/LO/Source/PDF/PhotonFlux.f`.
runtime-pdf-dispatch.md names the call sites (`epa_lepton(x,q2max,|ih|)` at pdg2pdf.f :259; `epa_proton(x,q2max,beamid)` at :261; `get_ion_pdf` at :182,:277-294). This page walks what those functions actually compute.

## epa_lepton — IWW photon-from-lepton (:14-48)
Improved Weizsäcker-Williams (Frixione et al. PLB319 1993), elastic-limit, NO DGLAP evolution. Reached for `pdlabel=='iww'`/photon-from-lepton (`|ih|∈{3,4}`).
- `mode` = ±3 (electron) / ±4 (muon); `imode=abs(mode)`. Lepton mass table `xin(3:4) = (0.511d-3, 0.105658d0)` (:25) — **electron and muon ONLY; NO tau slot** (array bounds 3:4). A tau-beam IWW would index out of range.
- `q2min = m_f^2 * x^2/(1-x)` (:32) — the kinematic lower cutoff set by the lepton mass; `q2max` passed in = μF^2 (xmu^2, the factorization scale).
- Flux (:34-36): `f = alpha/(2π) * [ 2 m_f^2 x (1/q2max − 1/q2min) + (2−2x+x^2)/x · ln(q2max/q2min) ]`, gated `q2min<q2max` else `f=0`; also `f<0 → 0` and `x≥1 → 0`.

## epa_proton — EPA photon-from-proton / -ion (:50-89)
Budnev EPA (Phys.Rep. 15C 1975). Reached for `|ih|==2` (elastic photon from proton).
- Proton mass `xin=0.938` (:66); dipole scale `qz=0.71` GeV² (:69).
- **Heavy-ion override (:71-74)**: if `nb_proton(beamid)≠1 .or. nb_neutron(beamid)≠0`:
  - `xin = mass_ion(beamid)` — the ION mass replaces the proton mass in the form-factor cutoff `qmi = xin^2 x^2/(1-x)`.
  - `alpha = alpha * nb_proton(beamid)` — **coherent Z·α enhancement** (the photon couples to the whole nuclear charge Z=nb_proton). This is the ONLY place the ion charge enters the photon flux normalization.
- Flux (:80): `f = alpha/π · (phi_f(x,q2max/qz) − phi_f(x,qmi/qz)) · (1−x)/x`.
- `phi_f(x,qq)` (:91-107): the Budnev structure-function integral with fixed coefficients a=7.16, b=−3.96, c=0.028.

## HARDCODED Thomson alpha (caution — both EPA functions)
`alpha = .0072992701` (:27, :68); `1/.0072992701 = 137.000` (NOT 137.036 — the literal is 1/137 exactly, Thomson/on-shell-regime α, ≈1/137 not the running α(MZ)≈1/128). **PhotonFlux.f imports NO alpha common block** (grep: no `aewm1`/`common` for alpha) — the photon-flux normalization is INDEPENDENT of the param_card `aewm1`/α(MZ) and of `dynamical_scale_choice`. Changing the model's electroweak α does NOT change the EPA/IWW photon flux normalization. (Contrast: the EVA Z/W flux EW constants are MODEL-derived — written into a GENERATED `ElectroweakFlux.inc` at output and read by the driver — so EVA flux IS model-dependent, unlike this hardcoded EPA/IWW α. See eva-flux-driver-internals.md.)

## get_ion_pdf — isospin rotation + double normalization (:109-144)
Combines proton PDF into a (heavy-)ion PDF for hadron beams. `get_ion_pdf(pdf(-7:7), pdg, nb_proton, nb_neutron)`.
- **Identity short-circuit** (:120-123): `nb_proton==1 .and. nb_neutron==0` → returns `pdf(pdg)` unchanged (plain pp/single-proton).
- **Light-quark isospin rotation** (:125-136): for `pdg∈{1,2}` (d,u) and `{−1,−2}` (d̄,ū), mixes the proton's u↔d densities by neutron count:
  - `tmppdf(1) = nb_proton·pdf(1) + nb_neutron·pdf(2)` (d-slot gets proton-d's plus neutron-d's = proton-u by isospin)
  - `tmppdf(2) = nb_proton·pdf(2) + nb_neutron·pdf(1)` (u-slot symmetric). Antiquarks symmetric.
- **Other flavors** (:137-139): `pdf(pdg)*(nb_proton+nb_neutron)` — flavor-blind nucleon-count scaling (g, s, c, b same in p and n).
- **DOUBLE normalization (trap)**: the else-branch already multiplies by `(nb_proton+nb_neutron)` (:138), then line :142 multiplies the result AGAIN by `(nb_proton+nb_neutron)` UNCONDITIONALLY. So heavy-flavor/gluon ion densities get `(nb_p+nb_n)^2` while the light-quark isospin branch (which did NOT pre-scale) gets `(nb_p+nb_n)^1`. The per-nucleon Bjorken-x (`x*nb_hadron`) is applied separately in pdg2pdf.f (runtime-pdf-dispatch.md). Reading :142 alone misses that the else-branch pre-scales — the two paths reach different powers of A.

## Cross-refs / cautions
- The DEAD epa tail in `pdf.f` :303,:308 (parser-vs-fortran-mismatch Flavor 3) calls `epa_proton(x,q2max)` with only TWO args — the real def needs three (`x,q2max,beamid`); further confirmation that tail is dead (the live 3-arg calls are in pdg2pdf.f). Don't read the 2-arg call as a real signature.
- `epa_lepton`/`epa_proton` are the ONLY IWW/EPA flux entries; edff/chff (gamma-UPC) go through photonpdfsquare.f (generated-pdf-assembly.md), a SEPARATE flux family — don't conflate IWW with edff/chff.
- RUNTIME flux values not probe-verified here; formulas + the hardcoded-alpha / double-norm facts are statically read from source.
