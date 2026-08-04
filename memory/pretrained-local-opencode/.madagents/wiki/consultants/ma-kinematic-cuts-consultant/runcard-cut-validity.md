---
description: RunCardLO.check_validity cut auto-corrections — nhel/maxjetflavor guards, photon-isolation auto-disable, xqcut/matching drjj-drjl zeroing, mmjj reset
---

# RunCardLO.check_validity — cut-relevant auto-corrections

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py`, `RunCardLO.check_validity`
at :4494 (calls `super().check_validity()` first at :4497). MG5_aMC v3.7.1.
This is the PARSE-TIME (Python) correction layer. A second RUNTIME (Fortran) layer
in setcuts.f re-applies some of these — see cuts-f-filter.md.

## Guards (raise / reject)
- :4502 `nhel` must be defined else InvalidRunCard.
- :4504 `nhel` must be in [1,0]; else InvalidRunCard "can only be '0' or '1'".
  (0 = sum over helicities / no MC; 1 = MC over helicity with importance sampling.)
- :4507 `int(maxjetflavor) > 6` -> InvalidRunCard. NOTE exact message text:
  "maxjetflavor should be lower than 5! (6 is partly supported)" — the guard fires only
  at >6, so 6 is allowed here (but rejected later if matching is on, see below).
- :4510 `len(pdgs_for_merging_cut) > CAP` -> InvalidRunCard (read the numeric cap at :4510).

## Photon-isolation auto-disable (:4516)
If `ptgmin > 0`:
- :4517 if `pta > 0`: warning "pta cut discarded since photon isolation is used"; `pta=0.0`.
- :4520 if `draj > 0`: warning "draj cut discarded since photon isolation is used"; `draj=0.0`.
Rationale: Frixione smooth isolation replaces the fixed photon pt / a-j separation cuts.
The photon still gets a min pt — setcuts.f sets `etmin = max(pta, ptgmin)` so ptgmin
becomes the photon pt floor (cuts-f-filter.md). pta/draj are zeroed only, never re-raised.

## Matching / xqcut corrections
- :4544 `ickkw > 0`: if `!=1` -> critical + interactive abort (ickkw>1 is alpha).
- :4551 if `use_syst` & ickkw>0: force `alpsfact=1.0` with warning.
- :4556 if `ickkw>0` & `maxjetflavor==6` -> InvalidRunCard
  "maxjetflavor at 6 is NOT supported for matching!".
- :4562 if `xqcut > 0`:
  - :4563 if `ickkw==0`: logger.ERROR "xqcut>0 but ickkw=0. Potentially not fully
    consistent setup. Be careful" + `time.sleep(5)` (a 5-second blocking pause, not abort).
  - :4566 if `drjj != 0`: set `drjj=0` (warning only if drjj in user_set).
  - :4570 if `drjl != 0`: set `drjl=0` (warning only if drjl in user_set).
  - :4574 if NOT `auto_ptj_mjj` and `mmjj > xqcut`: warning "mmjj > xqcut ... MMJJ set to 0";
    `mmjj=0.0`. (When auto_ptj_mjj=True this branch is skipped — mmjj handled in Fortran.)

## Cautions
- The xqcut block keys on `xqcut>0` regardless of ickkw for the drjj/drjl/mmjj edits, but
  the matching-consistency warning keys on ickkw==0. drjj/drjl auto-zero whenever xqcut>0.
- maxjetflavor=6 passes :4507 but fails :4556 under matching — two different gates,
  two different messages. Don't conflate "≤6 allowed" with "6 always allowed".
- The 5-second sleep at :4565 is a soft nudge, not a hard error — run still proceeds.
- update_system_parameter_for_include (:4701) is where *_pdg dicts become system arrays;
  it raises above the distinct-PDG cap (:4714) and on negative/forbidden-PDG, AFTER check_validity.
