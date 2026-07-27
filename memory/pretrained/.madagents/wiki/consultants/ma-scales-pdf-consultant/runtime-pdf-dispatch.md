---
description: LO runtime PDF dispatcher — pdg2pdf.f branching by pdlabel/lpp (eva, photon/IWW, eepdf, dressed, cteq6, nn23/lhapdf, ion x-scaling) + get_pdfup lhaid mapping.
---

# Runtime PDF dispatch (LO)

How a run-card `pdlabel`/`lpp` choice turns into a parton density at integration time.
Source: `$MADGRAPH_INSTALL/Template/LO/Source/PDF/pdg2pdf.f` and `pdf.f`; `get_pdfup` is in `$MADGRAPH_INSTALL/Template/LO/Source/setrun.f` (one level up from `PDF/`).

## pdg2pdf.f — main per-flavour dispatcher
Entry `pdg2pdf(ih, ipdg, beamid, x, xmu)` returns one parton density. Branch order:

- **ih=9 (PLUGIN)** (:73-76): returns `1d0` flat — PLUGIN beam has no internal PDF.
- **nb_hadron x-scaling** (:78): `nb_hadron = nb_proton+nb_neutron`; x is checked against `x*nb_hadron`. For ions, Bjorken-x is per-nucleon; out-of-range `x*nb_hadron>1` returns 0 (ion) or stops (single hadron) (:85-95).
- **`pdlabel=='dressed'`** (:99-127): dressed-lepton ISR. Maps e/mu/tau pdg 8/9/10 -> 11/13/15, builds `ih_local`, calls `compute_eepdf(x, omx_ee, xmu, i_ee, ipart, ih_local)`. NOTE `'dressed'` is a RUNTIME pdlabel NOT in the LO `valid_pdf` static list (banner.py :4251) — it is set indirectly (lep-density / ISR path), not user-typed as `pdlabel='dressed'`.
- **`pdlabel=='eva'` (or per-beam pdsublabel)** (:133-135, :222-251): EVA effective-W/Z/photon flux.
  - Only `|ipart| ∈ {7(γ),23(Z),24(W)}` supported; else `stop 1` "EVA PDF only supported for A/Z/W".
  - Beam must be `|ih| ∈ {3(e),4(mu)}`; else `stop 24` "only supported for e+/- and mu+/- beams". (ih 0..2 explicitly rejected.)
  - `ppid = 11 or 13`, signed by beam; `fLPol = pol(iabs(beamid))` (from polbeam, see scale-params.md EVA-runtime + beam-pdf-params.md polbeam); `q2max=xmu^2`; helicity via `GET_NHEL`; calls `eva_get_pdf_by_PID(...)` then multiplies by `helMulti` to undo spin-averaging.
- **photon ipart=7, non-EVA** (:253-262): the `iww`/elastic path. `q2max=xmu^2`;
  - `|ih| ∈ {3,4}` (lepton beam) -> `epa_lepton(x,q2max,|ih|)` (improved Weizsäcker-Williams / IWW).
  - `|ih|==2` (elastic photon from proton) -> `epa_proton(x,q2max,beamid)`.
- **cteq6 (`pdlabel(1:5)=='cteq6'`)** (:271-286): `Ctq6Pdf`; **u and d are FLIPPED inside cteq** (code passes 2 for u, 1 for d). Ion case routes through `get_ion_pdf`.
- **else (nn23 / lhapdf / generic)** (:292-295): `call pftopdg(|ih|, x*nb_hadron, xmu, pdflast)` then `get_ion_pdf(...)`.

**Reuse cache** (:171-218): keys on `x*nb_hadron`, `xmu`, `pdlabel`, `ih`; two slots (xlast(1..2)). Returns cached `pdflast` if hit.

**Ion reweighting** `get_ion_pdf(pdf, ipart, nb_proton, nb_neutron)` combines proton/neutron PDFs by isospin for heavy-ion beams. Plain pp/ee runs have nb_proton=1,nb_neutron=0 (identity).

## pdf.f — pftopdg / fdist (the nn23 / cteq catch-all)
- `pftopdg(ih,x,q,pdf)` (:1) just wraps `fdist(ih,x,xmu,fx)` (:16).
- `fdist` (:21): zeroes fx(-7:7); `x>=1` returns zero. `pdlabel(1:4)=='nn23'` -> `NNevolvePDF` (NNPDFDriver) (:44-45). Long block of commented-out legacy MRS/CTEQ4/5 calls.
- **DEAD photon tail** (:298-308): a second `epa_lepton`/`epa_proton` block guarded by `ih ∈ {2,3,4}` but it `stop 23` "impossible call (or was it)" BEFORE the epa call — this path is dead; the live photon path is in pdg2pdf.f :253-262.

## get_pdfup — pdlabel -> LHAPDF set number (setrun.f :208-...)
`get_pdfup(pdfin,pdfgup,pdfsup,lhaid)` writes the PDF set id into the LHE banner (`pdfsup`).
- `pdlabel=='lhapdf'` -> `pdfsup = lhaid` (the run-card lhaid).
- Internal table `numspdf` (:241-263) maps known labels to fixed ids: `none/eva/iww/edff/chff/dressed -> 00000`; `cteq6_m->10000, cteq6_l->10041, cteq6l1->10042, nn23lo->246800, nn23lo1->247000, nn23nlo->244800` (+ legacy mrs/cteq4/5). The 00000 entries mean "no standard LHAPDF id" for the flux/elastic/dressed pseudo-PDFs.

## Cautions
- EVA/photon/eepdf/dressed are NOT standard hadronic PDFs — they are flux functions; the `numspdf=00000` banner id reflects that. Don't expect an LHAPDF set in the LHE for these.
- cteq6 u/d flip is a per-flavour trap when reasoning about which density is returned.
- The DEAD epa tail in pdf.f (:298-308) is a refactor remnant; reading it can mislead — the real elastic/IWW dispatch is in pdg2pdf.f.
- edff/chff (gamma-UPC elastic FF) are NOT dispatched in pdg2pdf.f; they route through the gammaUPC f90 path (`Template/Common/Source/PDF/gammaUPC/`) — see pdlabel-coherence page note that μF is ignored for these since 3.5.0.
