---
description: LO alpha_s evaluation paths — setrun.f init OVERWRITES param_card asmz with the PDF's asmz(MZ) for any PDF run (pdf_list.txt/pdfwrap.f table); internal alfas_functions.f vs LHAPDF alfas_functions_lhapdf.f (alphasPDF); make_opts build swap.
---

# alpha_s evaluation paths (LO)

Two mutually-exclusive compile-time paths, selected by `make_opts`.

## Build selection (Template/LO/Source/make_opts)
- `lhapdf` set (:110-114): `alfas_functions=alfas_functions_lhapdf`, cleans `alfas_functions.o`, links `-lLHAPDF`.
- `lhapdf` empty (:123-126): `alfas_functions=alfas_functions` (internal), cleans the lhapdf object.
So configuring LHAPDF (typically driven by `pdlabel='lhapdf'`) swaps which `ALPHAS` is compiled.

## Where asmz/nloop are SET: setrun.f init (the param-card-αs override)
`asmz`,`nloop` live in `common/a_block/asmz,nloop` (`Template/LO/Source/alfas.inc` :8-10) — the values the internal `ALPHAS(Q)` reads. They are SET at runtime init in `setrun.f` (called from setcuts.f), NOT taken straight from the param_card:
- **Any beam has a PDF** (`lpp(1)≠0 .or. lpp(2)≠0`, setrun.f :130-136): prints "A PDF is used, so alpha_s(MZ) is going to be modified"; calls `setpara(param_card)` → `asmz=G**2/(16·atan(1))` = G²/(4π) (the param_card αs); then **`call pdfwrap` OVERWRITES `asmz`** with the chosen PDF's αs(MZ) (the per-pdlabel table below). Prints "Old value ... from param_card" then "New value ... from PDF". So **for ANY PDF run the param_card αs(MZ) is DISCARDED and replaced by the PDF's αs(MZ)** — a runtime supersession (scale-pdf-value-supersession.md). (LHAPDF build: the alfas wrapper uses alphasPDF directly, so asmz here is moot.)
- **No PDF at all** (`lpp(1)==0 .and. lpp(2)==0`, :137-145): `asmz=G²/(4π)` from param_card is KEPT, `nloop=2` forced, and **`pdlabel='none'` forced at runtime** (the runtime side of the lpp=0→'none' parse coherence, pdlabel-coherence.md). αs(MZ) is the model's.
- alfas.inc comment (:5): "asmz = alpha_s(Mz) is set based on the pdf chosen in setcuts.f" — confirms the override site.

## Internal path: alfas_functions.f
- `DOUBLE PRECISION FUNCTION ALPHAS(Q)` (:74). (Header comment block mentions a 3-arg `alphas(scale,asmz,nloop)` signature but the actual compiled function is single-arg `ALPHAS(Q)`; asmz/nloop come from common block alfas.inc.)
- Newton-iteration beta-function evolution from `asmz` (NEWTON1, :135,:151). If asmz<=0 falls back to 0.1185 with warning (:112-116).
- `asmz`/`nloop` set per-pdlabel in `pdfwrap.f` (default nloop=2 NLO running, :13):
  - cteq6_m/cteq6_d/cteq6_l: asmz=0.118 (:224-232)
  - cteq6l1: asmz=0.130, nloop=1 (:233-236)
  - nn23lo: asmz=0.119 (:247-250); nn23lo1: asmz=0.130 (:252-255); nn23nlo: asmz=0.119 (:257-260)
  - nn23 branches also INITIALIZE the grid here: `NNPDFDriver('NNPDF23_lo_as_0130_qed_mem0.grid')` + `NNinitPDF(0)` (:248-260) — so `pdfwrap` both sets asmz/nloop AND loads the PDF grid the runtime `NNevolvePDF` (runtime-pdf-dispatch.md) reads.
  - eva/iww/none: asmz=asmz (unchanged) (:264-265)
  - else (incl. 'lhapdf' here, and arbitrary lep PDFs): asmz=0.118 (:266-267). The old "Unimplemented distribution" stop is commented out.

## LHAPDF path: alfas_functions_lhapdf.f
- `ALPHAS(Q)` is a thin wrapper: `ALPHAS = alphasPDF(Q)` (:75-83). αs comes entirely from the LHAPDF set's own running (and order), bypassing the internal asmz/nloop and pdfwrap values.

## Reference table: pdf_list.txt (authoritative asmz/nloop)
`$MADGRAPH_INSTALL/Template/LO/Source/PDF/pdf_list.txt` is the human-readable table behind the `pdfwrap.f` asmz/nloop assignments — columns `name | pdflabel | Data file | as(Mz) | nloop`. Confirms the values pdfwrap.f hardcodes:
- `cteq6_m/cteq6_d/cteq6_l 0.118 nloop=2`; `cteq6l1 0.130 nloop=1`.
- `nn23nlo 0.119 nloop=2`; `nn23lo 0.119 nloop=2`; `nn23lo1 0.130 nloop=1`. (NOTE table lists nn23lo as nloop=2; pdfwrap.f sets nn23lo nloop default=2 too — consistent. The αs=0.130/nloop=1 of nn23lo1 (grid property) is the LO-card default pdlabel's grid; its LHAPDF-catalog identity is 247000. The run-card default `lhaid` (read fresh at banner.py:4256) is a SEPARATE field, inert unless pdlabel=='lhapdf' — do not equate it with the active nn23lo1 grid.)
- LEGACY-ONLY rows (mrs02nl..mrs98l5, cteq5_*, cteq4_*, cteq3_*): these pdflabels have asmz/nloop entries in pdf_list.txt AND commented-out PDF readers in pdf.f, but are **NOT in the LO `valid_pdf` static list** (banner.py :4251). So a user cannot type e.g. `pdlabel='cteq5_m'` at LO — it reverts to default (parser-vs-fortran-mismatch Flavor 2). The table documents capability the LO parser does not expose.

## Notes / cautions
- There is NO `pdfwrap_lhapdf.f` in LO Source/PDF; LHAPDF αs is supplied via the alfas swap, not a pdfwrap variant. `pdg2pdf_lhapdf6.f` supplies the LHAPDF PDF values.
- Caution: with `pdlabel='lhapdf'` the internal `pdfwrap.f` would map to the `else` asmz=0.118/nloop=2 branch, but that branch is inert because the LHAPDF αs wrapper replaces ALPHAS at build time. The authoritative αs is the LHAPDF set's.
