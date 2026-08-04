---
description: pdlabel=lhapdf runtime gate — MG5 links LHAPDF ONLY when pdlabel=='lhapdf'; bundled sets (nn23lo1/cteq6*) are compiled Fortran needing NO LHAPDF; NO auto-fallback, invalid lhaid errors. lhaid consumed only in lhapdf mode.
---

# LHAPDF vs bundled-PDF runtime linking gate

Answers "without LHAPDF, what PDF does MG5 use / is there a fallback?" and the `pdlabel=lhapdf`+`lhaid` runtime coupling. Complements beam-pdf-params (params/defaults) and lo-vs-nlo-pdf-default (lhaid-only-in-lhapdf-mode).

## The gate: pdlabel=='lhapdf' is the ONLY LHAPDF trigger
`$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py:6111-6124` (compile/treatcards path):
- `if run_card['pdlabel']=='lhapdf'` (:6111): `make_opts_var['lhapdf']='True'`, `link_lhapdf(lib)` (:6113), `copy_lhapdf_set([int(lhaid)], pdfsetsdir)` (:6116). LHAPDF is linked and the lhaid's set is installed/validated.
- `if run_card['pdlabel']!='lhapdf'` (:6117): `make_opts_var['lhapdf']=""` — the build does NOT link LHAPDF. Bundled Fortran grids are used.

So LHAPDF is a per-`pdlabel` opt-in, gated on the exact string `'lhapdf'`. NLO path mirrors this: `amcatnlo_run_interface.py:4738/4752/5472/5494` call the same `link_lhapdf`/`copy_lhapdf_set`.

## Bundled (internal, no-LHAPDF) PDF sets — the "internal set"
Active (non-commented) branches in `$MADGRAPH_INSTALL/Template/LO/Source/PDF/pdfwrap.f`:
- `cteq6_m` (:224), `cteq6_d` (:227), `cteq6_l` (:230), `cteq6l1` (:233), `nn23lo` (:247), `nn23lo1` (:252), `nn23nlo` (:257); `eva`/`iww`/`none` (:264, flux — no PDF).
- `nn23lo1` → `NNPDF23_lo_as_0130_qed_mem0.grid`, `asmz=0.130` (:253-255). `nn23lo` → `NNPDF23_lo_as_0119_qed_mem0.grid`, asmz=0.119 (:249-251). `nn23nlo` → `NNPDF23nlo_as_0119_qed_mem0.grid` (:258+).
- These `.grid` files ship with MG5 and are read by the compiled Fortran directly; they need NO LHAPDF install. This is the "internal (limited) PDF set" — the DEFAULT is `pdlabel='nn23lo1'` (banner.py:4253).
- NOTE `cteq6_d` is an active pdfwrap.f branch but is NOT in the LO `valid_pdf` static list (banner.py:4251) — reachable only via NLO card (allowed at :5648). Not a valid LO pdlabel input.

## Fallback answer: NO auto-fallback; invalid lhaid ERRORS
- There is NO runtime fallback from `pdlabel=lhapdf` to a bundled set. If `pdlabel=lhapdf`, MG5 requires a configured LHAPDF (`self.options['lhapdf']`, default `'lhapdf-config'`, common_run_interface.py:659). The bundled sets are a SEPARATE user choice (a different `pdlabel` string), not a graceful degradation.
- `copy_lhapdf_set` (common_run_interface.py:4554-4572): if the lhaid is not in the installed lhapdf's `pdfsets.index`, raises `MadGraph5Error('lhaid %s not valid input number for the current lhapdf')` (:4571). Not-locally-present-but-valid sets are auto-downloaded via `install_lhapdf_pdfset` (:4657). (Error text and download path read from source, not runtime-verified.)
- The common claim that "without LHAPDF MG5 uses its internal set" is loosely right only because the DEFAULT pdlabel (nn23lo1) is bundled — it is NOT a runtime fallback triggered by a missing/failed LHAPDF; choosing `pdlabel=lhapdf` without LHAPDF configured fails.

## lhaid coupling (cross-ref lo-vs-nlo-pdf-default)
`lhaid` is consumed ONLY when `pdlabel=='lhapdf'` (get_pdf_id banner.py:3840-3845; copy_lhapdf_set reads `int(run_card['lhaid'])` at :6115). With a bundled pdlabel the `.grid` is picked by the pdlabel STRING in pdfwrap.f and lhaid is ignored (get_pdf_id returns a hardcoded bookkeeping pdfsup, banner.py:3849-3851). To use e.g. NNPDF3.1 LO you MUST set `pdlabel=lhapdf` AND `lhaid=<id>` together.
- The "set pdlabel lhapdf / lhaid 315000" idiom is the correct BOTH-fields form. The id→name mapping (315000=NNPDF31_lo_as_0118, 303400=NNPDF31_nlo_as_0118, etc.) is an LHAPDF-catalogue fact from `pdfsets.index`, NOT MG5 source — treat as external/HYPOTHESIS.

## Environment note (this install)
LHAPDF6 IS present: `$MADGRAPH_INSTALL/HEPTools/lhapdf6_py3/bin/lhapdf-config`. So `pdlabel=lhapdf` is usable here; verify a specific lhaid is in this install's pdfsets.index before relying on it.
