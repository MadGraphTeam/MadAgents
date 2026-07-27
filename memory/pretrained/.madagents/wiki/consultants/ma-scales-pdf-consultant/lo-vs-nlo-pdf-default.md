---
description: PDF/lhaid default divergence between RunCardLO (nn23lo1, scalar lhaid) and RunCardNLO (nn23nlo, list lhaid); NO ME-perturbative-order vs PDF-order guard — LO PDF + NLO ME runs silently.
---

# LO vs NLO run_card PDF defaults + the missing order guard

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py`.

## The two cards' PDF defaults DIVERGE
- **RunCardLO** (`default_setup` @:4208): default `pdlabel` (:4253), per-beam `pdlabel1/2` (:4254-4255), `lhaid` SCALAR (:4256) — read each default fresh at its coordinate. The default `pdlabel` (nn23lo1) selects the bundled NNPDF2.3 LO grid whose αs(MZ)=0.130 (`Template/LO/Source/PDF/pdfwrap.f:252-255`).
- **RunCardNLO** (`default_setup` @:5611): default `pdlabel` (:5648), `lhaid` LIST (:5650, `fortran_name='lhaPDFid'`) — read fresh. The default `pdlabel` (nn23nlo) selects the bundled NNPDF2.3 NLO grid whose αs(MZ)=0.119 (`Template/NLO/Source/PDF/pdfwrap.f:268-275`).

So the bundled NLO card ALREADY ships an NLO PDF (`nn23nlo`) by default — an `output` of an `[QCD]` process writes `run_card.dat` from the NLO template, so the default IS NLO-consistent. The "LO process card defaults to nn23lo1" describes the LO template only; a fixed-order NLO process gets the NLO template's `nn23nlo` default. Two structural differences:
- `lhaid` is a SCALAR at LO, a LIST at NLO (NLO supports multiple PDF-error members / reweighting; check_validity :5878-5903 manages list length, max 25).
- The NLO `allowed` list (:5648-5649) includes `emela`, `cteq6_d`, `ct14q00/07/14/21` and EXCLUDES `iww`/`mixed`; LO `valid_pdf` (:4251) includes `iww`/`mixed` and EXCLUDES emela/ct14q*/cteq6_d.

## lhaid is consumed ONLY in lhapdf mode — number ≠ active grid
`get_pdf_id` (:3839-3854): returns `lhaid` ONLY when `pdlabel=='lhapdf'`; otherwise returns a hardcoded bookkeeping pdfsup from the table (:3849-3851: nn23lo1→247000, nn23nlo→244800, etc.). run_card.dat comment (LO :51, NLO :76): "if pdlabel=lhapdf, this is the lhapdf number." So with the default `pdlabel=nn23nlo`/`nn23lo1`, the `lhaid` field is IGNORED — the bundled `.grid` is selected by pdlabel string in pdfwrap.f. To use a specific lhapdf set (e.g. NNPDF31_nlo 303400, NN23NLO central 244600) you MUST set `pdlabel=lhapdf` AND `lhaid=<id>` together; setting lhaid alone with a bundled pdlabel does nothing.
- LHAPDF index sanity — these are external catalog identities of named sets (keep), read from `HEPTools/lhapdf6_py3/share/LHAPDF/pdfsets.index`: `230000=NNPDF23_nlo_as_0119`, `244600=NNPDF23_nlo_as_0118_qed`, `244800=NNPDF23_nlo_as_0119_qed`, `247000=NNPDF23_lo_as_0130_qed`, `303400=NNPDF31_nlo_as_0118`. NOTE the LO `lhaid` default (read at :4256) has historically been an NLO-labelled set in this index — irrelevant unless pdlabel=lhapdf, but a reason not to read PDF identity off the lhaid number.

## NO ME-order vs PDF-order guard — the mismatch is SILENT
grep across `banner.py` / `amcatnlo_run_interface.py` / `common_run_interface.py`: there is NO check tying the matrix-element perturbative order to the PDF's perturbative order. RunCardLO.check_validity (:4585-4612) only does lpp↔pdlabel coherence; RunCardNLO.check_validity (:5761+) checks lepton-collision PDF handling, pineappl/reweight_pdf→lhapdf coupling (:5828, :5862), lhaid list-length — never "is this PDF the right perturbative order for the ME." A LO PDF with an NLO ME (or vice versa) parses, coheres, and RUNS; the only effect is a soft σ shift from the wrong αs running / wrong PDF evolution order — NOT an error or warning. The agent must set the NLO PDF deliberately. (Runtime-silence not probe-verified here; established by absence of any guard in the source paths walked.)

## Caution
- The NLO PDF-default question's CARD is amcatnlo/launch's (which template, fixed_order, req_acc_FO); the PDF FIELD value within it is this slice. The above establishes the pdlabel/lhaid defaults + coherence + the no-order-guard fact — the surrounding NLO-card knobs are out-of-slice.
