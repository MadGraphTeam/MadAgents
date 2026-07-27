---
description: pdlabel-triple coherence engine (PDLabelBlock) and lpp/pdlabel auto-correction rules in RunCardLO.check_validity — the full branching, auto-set/auto-correct/reject behavior with file:line cites.
---

# pdlabel coherence + lpp auto-correction

## PDLabelBlock.check_validity (banner.py :4052-4090)
Fills the inactive template from the active one. `status()` True = per-beam template (`pdlabel1/2`); False = single `pdlabel`.
Block also activates the per-beam template when `pdlabel == 'mixed'` (:4095-4096).

When per-beam template active (status True), `pdlabel` is derived from `pdlabel1/2`:
- if either is `'lhapdf'` -> `pdlabel='lhapdf'` (:4056-4057).
- elif either in `['edff','chff']` (:4058-4067): if they differ, the edff/chff one wins and is copied to both pdlabel and the other beam; if equal, `pdlabel`=that value.
- elif either is `'emela'` -> `pdlabel='emela'` (:4068-4069). (emela not valid at LO; relevant for NLO card.)
- else (:4070-4083):
  - if `pdlabel1==pdlabel2` -> `pdlabel` set to that.
  - elif pdlabel1 or pdlabel2 is a lep-density -> `InvalidRunCard("Assymetric beam pdf not supported for e e collision with ISR/bemstralung option")`.
  - elif one is `'none'` -> `pdlabel` = the other.
  - else -> `pdlabel='mixed'`.

When single template (status False): `pdlabel1=pdlabel2=pdlabel` (:4084-4086).

Hard reject (:4088-4090): if `|lpp1|==1==|lpp2|` (proton-proton) and `pdlabel1 != pdlabel2`
-> `InvalidRunCard("Assymetric beam pdf not supported for proton-proton collision")`.

post_set hooks (:4100-4116): setting `pdlabel` removes pdlabel1/2 from user_set; setting pdlabel1/2 removes pdlabel from user_set (last-writer wins on which template is active).

## lpp <-> pdlabel auto-correction (RunCardLO.check_validity :4585-4612)
Loop over beams i=1,2 with `lpp=lppi`, `pdlabelX=pdlabeli`:
- `lpp==0` (no PDF): if pdlabelX != 'none' -> set 'none' (:4589-4592). Auto-fix.
- `|lpp|==1` (proton lib PDF): if pdlabelX in `['eva','iww','edff','chff','none']` -> `InvalidRunCard` (:4593-4595). Hard reject, NO auto-fix.
- `|lpp|∈[3,4]` (e/mu lepton beams): if pdlabelX not in `['none','eva','iww'] + lep_densities` -> warn + set `'eva'` (:4596-4600). Auto-correct.
- `|lpp|==2` (elastic photon): if pdlabelX not in `['none','chff','edff','iww']` -> warn + set `'edff'` (:4601-4605). Auto-correct.
- If any mod happened (:4607-4612): drop 'pdlabel' from user_set, add 'pdlabel1', and re-run check_validity to re-coherence the lhapdf/pdlabel block.

## fixed_fac_scale coherence (FixedfacscaleBlock + check_validity :4623-4671)
- FixedfacscaleBlock.post_set_fixed_fac_scale (:4135-4144): setting `fixed_fac_scale` copies it to both `fixed_fac_scale1/2`.
- FixedfacscaleBlock.post_set (:4146-4156): setting one of fixed_fac_scale1/2 drops `fixed_fac_scale` from user_set and (if the sibling not user_set) copies into the sibling.
- check_validity (:4628-4659): if only one of fixed_fac_scale1/2 user-set with fixed_fac_scale -> warn + copy. If lpp asymmetric (one beam in {2,3,4}, other ==1) and only `fixed_fac_scale` set -> that beam's fixed_fac_scaleX forced True with warning (:4646-4653).
- μF cut-off warnings (:4662-4671): for lepton/photon beams with fixed fac scale left at default Mz (91.188), warns the cut-off is likely unintended; gamma-UPC edff/chff note that μF is ignored since 3.5.0.
