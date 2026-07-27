---
description: param_card SMINPUTS aS(MZ) is a genuine external param that reaches coupl.inc, but for hadron/PDF beams (lpp!=0) the runtime SUPERSEDES it with the PDF's alpha_s in setrun.f+pdfwrap — my side holds it, the run/PDF Fortran overrides it (cross-slice to scales-pdf).
---

# SMINPUTS aS(MZ): held external in the card, superseded by the PDF at runtime

For proton beams the param_card SMINPUTS aS(MZ) is overridden by the PDF's fitted alpha_s. The precise seam: the param_card side genuinely HOLDS aS as an external param; the override itself lives in the run/PDF Fortran (cross-slice pointer to **scales-pdf**), not in any param_card machinery.

## What my slice holds (param_card side) — VERIFIED
- `aS = Parameter(nature='external', value=<default>, lhablock='SMINPUTS', lhacode=[3])` — `$MADGRAPH_INSTALL/models/sm/parameters.py:37-43` (read the default value there). So the operative card carries a `SMINPUTS ... 3 <value>` line; read `SMINPUTS 3` in the generated card for the current default.
- aS is EXTERNAL → gets an `ident_card.dat` line → `write_inc_file` emits it into `param_card.inc`, and `setpara` initializes the strong coupling `G` from it (`G = 2*sqrt(aS)*sqrt(pi)`, parameters.py:292). Standard external-param path (operative-source-chain, restriction-pruned-external-is-dropped). Nothing in my slice modifies aS for hadron beams — the card value is written verbatim.

## Where the override actually happens (run/PDF Fortran — scales-pdf territory)
`$MADGRAPH_INSTALL/Template/LO/Source/setrun.f:130-145`:
```
if(lpp(1).ne.0.or.lpp(2).ne.0) then          ! ANY beam carries a PDF
    call setpara(param_card_name)
    asmz=G**2/(16d0*atan(1d0))                ! recover aS(MZ) from param_card's G
    write(*,*) 'Old value of alpha_s from param_card: ',asmz
    call pdfwrap                              ! <-- OVERWRITES asmz with the PDF's value
    write(*,*) 'New value of alpha_s from PDF ',pdlabel,':',asmz
else                                          ! lpp(1)=lpp(2)=0, no PDF
    call setpara(param_card_name)
    asmz=G**2/(16d0*atan(1d0)); nloop=2; pdlabel='none'
    write(*,*) 'No PDF is used, alpha_s(MZ) from param_card is used'
endif
```
The code labels the param_card value literally "Old value" and the PDF value "New value" — the replacement is explicit.

### How pdfwrap sets asmz (`Template/LO/Source/PDF/pdfwrap.f`)
- Internal PDF sets: asmz is HARDCODED per set (drift-prone per-set numbers — read them at the cited lines, do not cache the values). Coordinates: cteq6_m/d/l (L225/228/231), cteq6l1 (L234-236, ALSO sets nloop=1), nn23lo (L250), nn23lo1 (L255), nn23nlo (L260); unknown set falls back (L267). Durable mechanism: each internal set overrides asmz with its own fitted value, and cteq6l1 additionally forces nloop=1.
- `eva`/`iww`/`none` → `asmz=asmz` (L264-265): NO override even though lpp!=0 (lepton-density / photon modes keep the param_card value).
- **LHAPDF**: the running function is swapped, not just asmz. With LHAPDF, `alfas_functions_lhapdf.f:83` compiles `ALPHAS(Q)=alphasPDF(Q)` — alpha_s at EVERY scale comes straight from the LHAPDF set, bypassing both param_card aS and the internal RGE entirely (asmz argument ignored). So "fitted to the chosen PDF" is literal for lhapdf.

## Net effect on what the matrix element uses
- **Hadron/PDF beams (lpp!=0, real PDF):** the running alpha_s(mu) driving the ME comes from the PDF's asmz (or directly alphasPDF(Q) for lhapdf). The param_card aS(MZ)=0.118 is superseded — it seeds the initial `G` but is immediately replaced before event generation. Editing SMINPUTS[3] does NOT change the strong coupling in a hadron-collider run (silent no-op for the coupling, same family as an internal/dependent override but via a different, run-side mechanism).
- **No-PDF beams (lpp(1)=lpp(2)=0, e.g. e+e- with no ISR PDF):** the param_card aS IS the operative alpha_s(MZ), with nloop=2 running. Here SMINPUTS[3] genuinely governs the coupling.

## Cautions / seam
- Gate is `lpp(1)!=0 .or. lpp(2)!=0` — ANY beam with a PDF, not specifically lpp=1 (proton). lpp=1 is the canonical case; lpp=2 (γ-from-p), ±3/4, heavy-ion also trigger it, EXCEPT eva/iww/none which pass asmz through.
- The override is **run/PDF Fortran** (`setrun.f`, `pdfwrap.f`) — owned by **scales-pdf**, not param_card. My side's honest statement: aS is a genuine external SMINPUTS param that reaches coupl.inc, but for hadron beams its value is not what runs.
- NLO: this is the LO Template. The NLO alpha_s-from-PDF wiring differs (amcatnlo/scales-pdf) — not walked here; do not assume identical file layout.
- Whether/how `G` and all aS-dependent couplings are re-derived from the overridden asmz at each phase-space point (the coupling-refresh) is the run-side coupling machinery — scales-pdf/model territory; I established only the asmz replacement.
