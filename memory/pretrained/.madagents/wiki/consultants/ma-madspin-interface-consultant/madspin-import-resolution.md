---
description: do_import resolves sentinel options (BW_cut/Nevents_for_max_weight/nb_sigma/frame_id) from the input LHE banner; NWA warnings live here
---

# do_import — banner handoff and sentinel resolution

`do_import` at `$MADGRAPH_INSTALL/MadSpin/interface_madspin.py:188`. This is where the input LHE banner is read and several sentinel options resolve. NOT at do_launch (my card text was wrong on the BW_cut location — it is import-time).

## Banner-required checks (:232-241)
- `'slha' not in banner` -> InvalidCmd "Event file does not contain model information" (:232).
- `'mg5proccard' not in banner` -> InvalidCmd "does not contain generation information" (:235).
- `'madspin' in banner` -> InvalidCmd: already-decayed file, cannot re-decay (:240).

## Sentinel resolution when `mgruncard` present (:243-258)
- `Nevents_for_max_weight==0` -> `N_weight = max(<floor>, int(k*nevents**(1/3)))`; `nb_sigma = max(<floor>, log(nevents, base))` (:245-250 — read the floors/constants fresh). Scales the max-weight estimation statistics with event count.
- `BW_cut == -1` (sentinel) -> set to `float(bwcutoff)` from the run_card banner detail (:251-252).
  - If the inherited `BW_cut` exceeds the NWA-validity threshold (hardcoded at :253) -> `logger.critical`: bwcutoff "much too large value for Madspin and the validity of the Narrow-width-Approximation … overwrite that value via set BW_cut X" (:253-254). Critical only; does NOT abort.
- LO (`RunCardLO`): `frame_id` overwritten from run_card `frame_id` (:256-258). NLO: forced `frame_id = 6` (:260).

## No-banner branch (:261-266)
When `mgruncard` absent: `Nevents_for_max_weight`, `nb_sigma`, and `BW_cut==-1` take hardcoded no-banner fallbacks (registered at :261-266 — read the literals fresh). With a banner, BW_cut inherits the run_card's `bwcutoff` instead of the fallback.

## `import model NAME [CARD_PATH]` inside the card (import_model :341)
`do_import` routes `import model ...` lines to `import_model` (:194-195). This lets the MadSpin card swap the model/param_card used for the DECAY ME generation, independent of the production banner:
- `import model NAME` alone -> warns "No param_card defined ... might completely wrong"; auto-generates a default param_card via `create_param_card_static` (:349-364).
- `import model NAME CARD_PATH` -> loads CARD_PATH (:357-360).
- **strict diff guard (:368-386)**: unless `--bypass_check` (or `input_format in ['hepmc','lhe_no_banner']`), the new param_card is diffed against the banner's `param_card` (`create_diff`); ANY differing parameter -> InvalidCmd "Original param_card differs on some parameters ... we prefer not to proceed" (:382-386). A diff that fails to even compute -> "The two param_card seems very different" (:378-380).
- on accept, the banner's old `slha` is backed up as `slha_original` and replaced by the new card (:391-396); `banner.param_card` is rebuilt via `charge_card('slha')`.
So the in-card `import model` is essentially a width/param-card refresh that the guard forces to be value-identical to production (decay-width edits go through param_card too, and would trip the guard unless bypassed).

## pure-decay shortcut (:216-221)
`spinmode=='none'` AND input is non-lhe (hepmc / not `.lhe` tail under auto) -> empty banner + `setup_for_pure_decay()` and early return; the banner-required checks above are skipped.

## Model + multiparticle replay (:280-339)
- Multiparticle defs from `proc_card` replayed via `do_define` (:281).
- proc_card `set` lines re-executed; `complex_mass_scheme` detected to load model in complex-mass mode (:296-301).
- Model loaded from banner `model` line; `-modelname` toggles mg_names (:304-312).
- `final_state` collected from generate/add-process lines to know which PDGs may be decayed (:316-323).

## Cautions
- The NWA-threshold warning (:253) is `logger.critical` but non-fatal — easy to miss in a long log; the only hard abort on BW_cut is the hard-threshold check in `do_launch` (:653), not here.
- `bwcutoff` semantics/registration itself is the bw-window slice; here we only consume the value from the banner.

## Gaps
- How decay.py uses BW_cut to sample off-shellness — MadSpin internals, out of slice.
