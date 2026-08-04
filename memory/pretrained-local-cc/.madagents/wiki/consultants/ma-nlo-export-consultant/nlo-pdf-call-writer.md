---
description: NLO parton_lum_N.f writer — write_pdf_calls/write_pdf_file + get_pdf_lines_mir; PDG2PDF calls, pdgtopdf code map (photon/charged-lepton PDF-index remap + collision-avoidance renumber), UPC PHOTONPDFSQUARE, ee-PDF components (LPP 3/4), mirror beam swap.
---

# NLO PDF-call writer (parton_lum) (v3.7.1)

The NLO PDF luminosity files (`parton_lum_N.f`) wrap `PDG2PDF` calls per beam for each real-emission process. The interesting source is `get_pdf_lines_mir` — it encodes the PDG→PDF-index map, photon/lepton special cases, ultra-peripheral-collision (UPC) photon flux, and the e+e- beamstrahlung component handling.

## The writer chain
- `write_pdf_calls` (export_fks.py:2123): one `parton_lum_<n+1>.f` per real process via `write_pdf_file`, OR a single `parton_lum_0.f` from the BORN ME if `not matrix_element.real_processes` (`:2127`-2137). So a [LOonly]/no-real run still gets `parton_lum_0.f`.
- `write_pdf_file` (`:3757`): fills `template_files/parton_lum_n_fks.inc` (confirmed present). Requires `1 <= ninitial <= 2` else raises FortranWriterError (`:3768`). Substitutes `pdf_vars`/`ee_comp_vars`/`pdf_data`/`pdf_lines` from `get_pdf_lines_mir(matrix_element, ninitial, False, False)` (`:3783`-3788). The template declares `double precision ee_comp_prod` and `%(ee_comp_vars)s` (template `:48`-49).

## get_pdf_lines_mir (export_fks.py:4315) — the substance
Signature `(matrix_element, ninitial, subproc_group=False, mirror=False)`. Returns `(pdf_definition_lines, pdf_data_lines, pdf_lines, ee_pdf_definition_lines)` (`:4478`).

### ninitial==1 (decay): trivial — `PD(IPROC)=1d0` per process, no PDF (`:4327`-4333).

### ninitial==2 (collision): the real machinery (`:4334`+)
- **pdgtopdf map** (`:4348`): `{21:0, 22:7, -11:-8, 11:8, -13:-9, 13:9, -15:-10, 15:10}` — gluon→0, **photon→7**, charged leptons e/μ/τ → ±8/±9/±10. Any other PDG maps to itself; if a PDG collides with an existing PDF index (e.g. another particle is code 7), it gets `6000000+pdg` (`:4350`-4355).
- **PDF variable names** built from particle names with `~→x`, `+→p`, `-→m` substitution (`:4342`-4345).
- **UPC / photon-photon** (both beams have PDG 22, `:4380`): emits `IF (ABS(LPP)==2 .AND. PDLABEL(1:4) in {'edff','chff'})` guarded block calling `PHOTONPDFSQUARE(XBK(1),XBK(2))` — the non-factorized photon flux for ultra-peripheral collisions. Sets photon1=sqrt, photon2=photon1 (`:4384`-4392). Wrapped in IF/ELSE/ENDIF so non-UPC falls through.
- **per-beam PDG2PDF** (`:4396`+): for each initial state with `abs(pdgtopdf[is])<=10`, `<name><beam>=PDG2PDF(LPP(beam),pdgtopdf,beam,XBK(beam),DSQRT(Q2FACT(beam)))`. Guarded by `IF (ABS(LPP(beam)).GE.1)`. Partons OUTSIDE quark/gluon/photon (`abs(pdgtopdf)>10`) are set `=0d0` with a comment (`:4424`-4428).
- **ee-PDF components** (`:4418`/`:4434`): right after each PDG2PDF, `IF ((ABS(LPP)==4 .or. ==3) .and. pdlabel.ne.'none') <name><beam>_components(1:n_ee) = ee_components(1:n_ee)` — captures the per-bin electron-PDF (beamstrahlung/ISR) component array. LPP 3/4 are the lepton-PDF beam types.
- **PD(IPROC) assembly** (`:4452`+): `PD(IPROC)=<b1>*<b2>` product over both beams; for the ee case appends `IF (ABS(LPP(1))==ABS(LPP(2)) .and. in {3,4} .and. pdlabel.ne.'none') PD(IPROC)=ee_comp_prod(<b1>_components,<b2>_components)` (`:4473`-4475) — for lepton collisions the luminosity is the convolution `ee_comp_prod` of the two component arrays, not the plain product.

### mirror flag
`ibeam = i+1` if not mirror, else `2-i` (`:4397`-4400) — swaps which physical beam each initial-state slot reads. Used for mirror-process PDF lines.

### subproc_group flag
Switches `LPP(N)`/`XBK(N)` between direct index and `LPP(IB(N))`/`XBK(IB(N))` (group-permutation indirection) — `:4381` vs `:4388`, etc. For FKS NLO the caller passes `subproc_group=False` (`write_pdf_file:3784`), so the direct-index branch is what NLO `parton_lum_N.f` emits.

## Cautions
- Photon PDG maps to PDF index **7** (`:4348`); a model where a different particle legitimately uses PDF index 7 triggers the `6000000+pdg` collision-avoidance — a non-obvious renumbering. Verify the pdgtopdf map for an exotic-beam process before asserting the PDF index.
- The ee-component path (`_components`/`ee_comp_prod`/`n_ee`) only activates for `LPP in {3,4}` AND `pdlabel.ne.'none'`. A lepton-collision run with `pdlabel='none'` falls back to plain product — the beamstrahlung component is silently dropped. Runtime/run-card dependent (LPP and pdlabel are run_card values); verify before asserting the ee luminosity is used.
- `write_pdf_calls` writes `parton_lum_0.f` from the BORN ME when there are no real processes — don't assume "no parton_lum file" for a no-real run.
- UPC block keys on `PDLABEL(1:4) in {'edff','chff'}` (elastic/inelastic photon form-factor labels). A photon-photon process with a different pdlabel does NOT get the PHOTONPDFSQUARE flux.
