---
description: PRINCIPLE — run_card Python allowed-lists (allowed=/valid_pdf) and the Fortran runtime handlers are independently maintained and drift BOTH ways; check both layers for any enumerated scales/PDF value. Three mismatch flavors + observed failure modes.
---

# Parser-allowed vs Fortran-handled mismatch (generalization)

## Principle
For any *enumerated* parameter in the scales/PDF slice, two independent gatekeepers decide whether a value works:
1. the **Python parser** allowed-list (`add_param(..., allowed=[...])`, or `valid_pdf` for the pdlabel triple) — enforced in `banner.py` `RunCard.__setitem__`/`set`;
2. the **Fortran runtime** handler (`setscales.f`, `pdg2pdf.f`, `pdf.f`, `pdfwrap.f`, ...) that actually consumes the value.

These two sets are maintained independently and **drift apart in both directions**. A value passing one layer does NOT imply the other accepts it. ALWAYS check BOTH layers when reasoning about whether a slice value will work.

Scope: enumerated params (pdlabel/pdlabel1/pdlabel2, dynamical_scale_choice, ievo_eva, evaorder, eva_xcut, lpp, nb_proton/neutron, mass_ion).
Boundary: does NOT apply to free-numeric params with no `allowed=` list (scale, dsqrt_q2fact1/2, ebeam1/2, scalefact, polbeam) — those have no parser enum to mismatch. The principle is "agreement is not guaranteed", not "the layers always disagree".

## Parser enforcement mechanism (banner.py)
- Scalar enum check: `__setitem__`/`set` :1286-1308. List enum check: :1176-1209.
- On invalid value: calls `self.warn(text, 'warning', raiseerror)` (:1308).
- `warn` (:1055-1061): if `raiseerror is True` -> raise `InvalidCardEdition`; else just `logger.warning(...)` and **the assignment is skipped — previous value is preserved**.
- So the file-read path (raiseerror=False) does NOT crash on a bad enum value: it WARNS "value 'X' for entry 'Y' is not valid. Preserving previous value: '<prev>'" and **silently keeps the old value**. The interactive-edit path (raiseerror=True) hard-raises.

## Three mismatch flavors + observed failure mode

### Flavor 1 — parse-accepted, Fortran-unhandled -> runtime stop
Value is in the Python allowed-list, sticks, but no Fortran branch handles it.
- Instance: `dynamical_scale_choice=10` (allowed list `[-1,0,1,2,3,4,10]` banner.py :4267; `setscales.f` set_ren_scale has no `=10` branch, falls to `else -> stop "Unknown option in scale_global_reference"`). PROBE-VERIFIED (3.7.1): dsc=10 parses (value stays 10), Fortran stops at runtime; surfaces as a MISLEADING `FileNotFoundError` bug-report (G1/results.dat missing), real stop only in `G*/log.txt`. See scale-runtime-eval.md.

### Flavor 2 — parse-rejected -> warn+silent-revert (file) / InvalidCardEdition (interactive)
Value is NOT in the Python allowed-list. File-read silently reverts to previous; interactive edit raises.
- Instance: `pdlabel='emela'` at LO — `emela` is in PDLabelBlock (:4068) and NLO valid list (:5648) but NOT in LO `valid_pdf` (:4251) and NOT a lep-density dir. PROBE-VERIFIED (3.7.1): file-read warns "value 'emela' ... not valid. Preserving previous value: 'nn23lo1'" and **reverts to nn23lo1** (run proceeds with the WRONG default PDF, no error); interactive set raises `InvalidCardEdition`.
- Instance: `dynamical_scale_choice=5` (decay-mass, Fortran-handled at setscales.f :75-77) is NOT in the allowed list. PROBE-VERIFIED (3.7.1): file-read warns + reverts to previous (-1 default); the Fortran capability is unreachable from the run card.
- DANGER: the silent-revert is the trap. A typo or a cross-card-copied value (e.g. an NLO-only pdlabel pasted into an LO card) does not error on file read — it reverts to the default and the run silently uses the wrong PDF/scale.

### Flavor 3 — source-present but dead/inert -> no effect
The Fortran code path exists but is unreachable or overridden, so the value (even if it parses) never takes effect.
- Instance: DEAD epa photon tail in `pdf.f` :298-308 — `stop 23 "impossible call (or was it)"` fires BEFORE the `epa_lepton`/`epa_proton` call; the live photon path is `pdg2pdf.f` :253-262. Reading the dead tail misleads. See runtime-pdf-dispatch.md.
- Instance: inert `pdfwrap.f` else-branch (asmz=0.118/nloop=2) for `pdlabel='lhapdf'` — present but overridden at build time by the LHAPDF αs wrapper (`alfas_functions_lhapdf.f` ALPHAS=alphasPDF). The internal asmz is never used. See alphas-paths.md.
- Instance: `'dressed'` is a live `pdg2pdf.f` branch (:99) and in `get_pdfup`'s numspdf name table (setrun.f) but NOT in LO `valid_pdf` — so a user CANNOT type `pdlabel='dressed'` (Flavor 2 would revert it); it is reached only indirectly via the lep-density/ISR machinery. See beam-pdf-params.md, runtime-pdf-dispatch.md.

## Operating heuristic
When asked whether a scales/PDF enum value will work for THIS input:
1. Is it in the Python allowed-list / valid_pdf for the card being used (LO vs NLO lists differ — emela, ct14q*, cteq6_d are NLO-only)? If not -> Flavor 2 (silent revert on file read).
2. Does the Fortran handler actually have a branch for it? If not -> Flavor 1 (runtime stop) for parse-accepted values.
3. Is the Fortran branch reachable/effective (not dead, not build-overridden)? If not -> Flavor 3 (no effect).
A value must clear all three to behave as the name suggests.
