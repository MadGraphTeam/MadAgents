---
description: PDF luminosity assembled at code-OUTPUT time in auto_dsig.f (export_v4.py get_pdf_lines), a layer above pdg2pdf.f — edff/chff joint photon flux (PHOTONPDFSQUARE) and dressed-lepton ee_comp_prod 4-component dot product bypass the per-beam g1*g2 product.
---

# Generated PDF-assembly layer (auto_dsig.f)

The per-event PDF *luminosity* (the product/convolution combined into the event weight) is written into the GENERATED `auto_dsig.f` at `output` time by `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py` `get_pdf_lines` (def :1832, UPC/dressed blocks :1942-2084). This is a layer ABOVE the template `pdg2pdf.f` (runtime-pdf-dispatch.md): pdg2pdf returns one parton density per beam, but how those are combined — and two cases that bypass the plain product — is decided at code-gen and frozen into the process directory. Reading only the template misses it.

Normal case: `PD(IPROC) = g1 * g2` (per-beam densities multiplied). Two special cases override this.

## Case 1 — edff/chff joint photon flux (gammaUPC), non-factorized
Gate (export_v4 :1942): emitted only when `22 in initial_states[0] AND 22 in initial_states[1]` — BOTH incoming legs are photons. Generated guard (:1945-1954):
```
IF (ABS(LPP(1)).EQ.2 .AND. ABS(LPP(2)).EQ.2 .AND. (PDLABEL(1:4).EQ.'edff'.OR.PDLABEL(1:4).EQ.'chff')) THEN
   G1 = PHOTONPDFSQUARE(XBK(1),XBK(2))
   G1 = DSQRT(G1)
   G2 = G1
ELSE  ... (normal per-beam path)
```
So the JOINT two-beam flux `photonpdfsquare(x1,x2)` is computed once, and each beam g-factor is its **square root**, so that the downstream `g1*g2` reproduces the joint flux exactly. This is a NON-factorized PDF — the two photon densities are NOT independent.

`photonpdfsquare` lives in `$MADGRAPH_INSTALL/Template/Common/Source/PDF/gammaUPC/photonpdfsquare.f` (def :1):
- `edff` (`pdlabel(1:3)=='edf'`, :135) → `USE_CHARGEFORMFACTOR4PHOTON=.FALSE.` (electric dipole FF); `chff` (`pdlabel(1:3)=='chf'`, :199) → `.TRUE.` (charge FF). The bare LO labels are `'edff'`/`'chff'` (banner.py valid_pdf :4251).
- **Forward-neutron-tagging variants** (`edff0n1n`, `chffXnYn`, ...) are parsed here from `pdlabel(4:7)` (neutron_tagging per beam, :135-262) but are NOT in the LO `valid_pdf` static list — only the bare `edff`/`chff` are user-typable at LO (parser-vs-fortran-mismatch Flavor 2 would revert a tagged form on file read). The tagging suffix is reachable from NLO / direct edit, not the LO run-card allowed list.
- Collision-mode dispatch by `nb_hadron` (:270-280): both=1 → `PhotonPhotonFlux_pp`; one>1 → `PhotonPhotonFlux_pA_WoodsSaxon`; both>1 → `PhotonPhotonFlux_AB_WoodsSaxon`. Final normalization `*nb_hadron(1)*nb_hadron(2)` (:282).
- LO `SubProcesses` never calls `photonpdfsquare` directly (grep: only NLO reweight_xsec_events.f does) — at LO it is invoked from the generated auto_dsig.f. The makefile (`Source/PDF/makefile` :31) compiles the real `libgammaUPC` only when `pdlabel1`/`pdlabel2` ∈ {edff,chff}; otherwise the `gammaUPC_dummy.f` stub returns `photonpdfsquare=1.0`.

## Case 2 — dressed-lepton ee-luminosity, 4-component dot product
When `dressed_lep` is true (lepton-ISR/`pdlabel=='dressed'`), the generated weight is overridden (export_v4 :2047-2050, :2079-2082):
```
if (pdlabel.eq.'dressed') PD(IPROC) = ee_comp_prod(g1_components, g2_components)
```
`pdg2pdf.f` (:121-124) fills `ee_components(1:n_ee)` via `compute_eepdf(x, omx_ee, xmu, i_ee, ipart, ih_local)` for the 4 components (`n_ee=4`, `eepdf.inc`), returning only component 1 as a placeholder. The real combination is `ee_comp_prod` (pdg2pdf.f :354-367): `Σ_{i=1..4} comp1(i)*comp2(i)` — a **dot product of the two beams' 4-component vectors**, NOT the scalar `g1*g2`. The `to_ee_components` common is "very quickly overwritten — do not use outside auto_dsig.f" (eepdf.inc) — the per-beam component arrays must be captured in the generated dsig before the next pdg2pdf call clobbers them.

## PDF-call scale (xmu) fallback for |lpp|≥1 beams
For ordinary hadron/lepton beams (`|lpp|≥1`), the generated dsig computes the scale `qscale` it passes to `PDG2PDF(...,qscale)` as the PDF evaluation scale (export_v4 :1964-1979):
- beam 1: `if DSQRT(Q2FACT(1))==0` then `qscale = (Σ_{i=3..nexternal} sqrt(max(0,(E_i+pz_i)(E_i-pz_i)))) / 2` (= HT/2, sum transverse mass / 2); else `qscale = DSQRT(Q2FACT(1))`.
- beam 2: if `DSQRT(Q2FACT(2))≠0`, `qscale = DSQRT(Q2FACT(2))` (else keeps beam-1's).

So when q2fact is still ZERO at the PDF call — the `dynamical_scale_choice=-1` (CKKW) case where setscales.f left q2factorization=0 *before* setclscales runs (scale-runtime-eval.md / ckkw-clustering-scale-resolution.md) — the PDF is evaluated at a HT/2-style fallback μF, NOT at the clustered q2fact that setclscales later assigns to the matrix-element/αs side. For fixed or dsc=1-4 scales q2fact is already positive, so qscale = `DSQRT(Q2FACT)` directly. Caution: the PDF-evaluation scale and the stored q2fact can momentarily differ in the CKKW path; the generated fallback is HT/2, not the clustering geom-mean.

## Cautions
- **The combination rule is process-dependent and frozen at output.** For an edff/chff joint flux you need BOTH initial legs to be photons AT GENERATION (`22 in initial_states[0] and [1]`); a process where MG didn't see two incoming photons won't get the PHOTONPDFSQUARE branch even with `pdlabel=edff` and `lpp=2` — it falls through to the normal per-beam path. Verify the generated auto_dsig.f, not just the run-card.
- **edff/chff μF is ignored** (pdlabel-coherence.md: gamma-UPC ignores μF since 3.5.0) — consistent with this being an x-only joint flux with no factorization-scale dependence.
- **dressed-lepton dot-product ≠ g1*g2**: reasoning about the lepton luminosity as a simple product of two PDFs is wrong; it is a 4-component inner product (beamstrahlung+ISR components). `'dressed'` is not user-typable at LO (Flavor 2 revert, beam-pdf-params.md) — reached via the lep-density/ISR machinery.
- RUNTIME flux values not probe-verified here; the assembly STRUCTURE (which branch is generated) is statically verified from export_v4.py + the Fortran defs.
