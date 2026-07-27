---
description: PRINCIPLE — which photon/EW flux families read the model's α/EW constants vs use a hardcoded Thomson α. EPA/IWW + edff/chff gammaUPC = hardcoded 1/137 (model-INDEPENDENT); EVA = model-derived. Answers "does changing aewm1/α(MZ) change my flux rate?" per family.
---

# Flux normalization: model-α vs hardcoded-α (generalization)

## Principle
The non-DGLAP "PDFs" in this slice are flux functions, and they split cleanly on ONE question: does the flux normalization read the loaded model's electroweak coupling (α/α(MZ), MW, MZ, sw2), or a value baked into the Fortran? The answer is **per flux family**, and the partition is:

- **Hardcoded Thomson α (model-INDEPENDENT)** — all the ELASTIC photon fluxes. Changing the model's `aewm1`/α(MZ) does NOT change the flux rate.
- **Model-derived EW constants (model-DEPENDENT)** — only EVA's effective Z/W/γ flux. Changing the model's EW inputs DOES change the flux rate.

So when asked "does changing aewm1/α(MZ) change my photon-flux (or EW-boson-flux) rate?", answer by flux family, never globally.

## The three families (all source-walked, 3.7.1)

### 1. EPA / IWW (PhotonFlux.f) — hardcoded, model-independent
`epa_lepton` (IWW, photon-from-lepton) and `epa_proton` (EPA, photon-from-proton/-ion) use a literal `alpha = .0072992701` (`Template/LO/Source/PDF/PhotonFlux.f:27,:68`). PhotonFlux.f imports NO alpha common block (no `aewm1`). `1/.0072992701 = 137.0000` (Thomson/on-shell 1/137, NOT 1/137.036, NOT α(MZ)≈1/128). See photon-flux-ion-pdf.md.

### 2. edff / chff gammaUPC (ElasticPhotonPhotonFlux.f90) — hardcoded, model-independent
The gamma-UPC elastic-FF photon flux (edff = electric dipole FF, chff = charge FF; routed via PHOTONPDFSQUARE / generated-pdf-assembly.md) uses module-PUBLIC `alphaem_elasticphoton = 0.0072992700729927005d0` (`Template/Common/Source/PDF/gammaUPC/ElasticPhotonPhotonFlux.f90:7`; private fallback `aqedup` :8 same value). `1/0.0072992700729927005 = 137.0` EXACTLY (this literal is the exact double-precision 1/137; the EPA `.0072992701` is a 10-digit truncation of the same — diff 2.7e-11). VERIFIED: `alphaem_elasticphoton` is NEVER assigned from the model anywhere in `Template/` or `madgraph/iolibs/` (grep for `alphaem_elasticphoton =` outside the def finds nothing) — it keeps the module default. The `<0` sentinel branch (:1283-1290, would fall back to aqedup or literal 0.0072992701) is never triggered because nothing sets it negative. So edff/chff is hardcoded-α model-independent, same as EPA/IWW.

### 3. EVA (ElectroweakFlux.inc) — model-derived, model-DEPENDENT
The EVA effective-W/Z/photon flux EW constants (`eva_mz2,eva_mw2,eva_gw2,eva_gz2,eva_ee2,eva_sw2,...`) come from `ElectroweakFlux.inc`, which is NOT in the template — it is GENERATED into `<PROC>/Source/` at output time by `export_v4.py:707` from the LOADED MODEL (eva-flux-driver-internals.md). So EVA's MZ/MW/sw2/couplings flow from the model; changing the model's EW inputs changes the EVA flux. This is the OPPOSITE of families 1+2.

## The generalized diagnostic (catches more than the instances)
For ANY flux family — current or a future one added to the slice — read where its α / EW constants come from:
- a **literal in the .f/.f90** (or a module default never reassigned) → model-INDEPENDENT (Thomson 1/137 for every elastic-photon family seen so far).
- a **GENERATED include** written from the loaded model at output → model-DEPENDENT.

Do NOT generalize one family's answer to another (the MEMORY lesson `flux-alpha-hardcoded-vs-model` warned this for EPA-vs-EVA; this page extends it to a third family, edff/chff, on the hardcoded side). The boundary: this is about the flux NORMALIZATION's α/EW input. It does NOT govern the QED running α used INSIDE the matrix element (that is the standard model-α path), nor αs (alphas-paths.md).

## Cross-refs
- Family 1 detail: photon-flux-ion-pdf.md (epa_lepton/epa_proton formulas + the hardcoded-α + ion coherent-Z·α enhancement, which scales the hardcoded α by nb_proton — still no model α).
- Family 2 routing: generated-pdf-assembly.md (PHOTONPDFSQUARE joint-flux assembly, |lpp|=2 both-photon gate) + runtime-pdf-dispatch.md (edff/chff NOT in pdg2pdf.f, gammaUPC f90 path).
- Family 3 detail: eva-flux-driver-internals.md (the per-event EVA algorithm + the generated .inc).
- All three "RUNTIME flux VALUES not probe-verified" — the model-(in)dependence facts here are STATIC source reads (where the constant is defined / whether it is ever reassigned), not runtime σ checks.
