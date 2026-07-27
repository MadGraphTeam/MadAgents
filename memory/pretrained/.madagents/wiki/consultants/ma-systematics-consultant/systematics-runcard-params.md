---
description: run_card systematics parameters — LO use_syst gate, systematics_program/systematics_arguments (modern engine), deprecated `syscalc` RunBlock + `update syscalc` reveal, AND the NLO RunCardNLO reweight params (reweight_scale/rw_rscale/rw_fscale/reweight_pdf).
---

# Systematics run_card parameters (LO run_card)

All in `RunCardLO.default_setup`, `$MADGRAPH_INSTALL/madgraph/various/banner.py`.

## The visible gate — use_syst
- `banner.py:4426`: `add_param("use_syst", True, ...)` — **default True**, NOT hidden, appears in run_card. Comment: "Add in the lhef file information needed for the computation of systematic uncertainty (scale variation and pdf)".
- It does NOT itself reweight. It gates whether the LHE stores the per-event info the systematics program later consumes. `do_systematics` raises `InvalidCmd` at LO if `use_syst=False` (see `do-systematics-entry`).

## The MODERN engine params (default path)
- `banner.py:4427`: `systematics_program` default `'systematics'` (include=False, hidden=True). Options in comment: `none, systematics, syscalc`.
- `banner.py:4428`: `systematics_arguments` — default list of `--mur=`/`--muf=`/`--pdf=` args (read the default at banner.py:4428; include=False, hidden=True). **This is what systematics.py actually reads** — the `--from_card` path recurses on this string when it is user_set (sys.py:1371-1374; see `do-systematics-entry`).

## The DEPRECATED SysCalc params (the `syscalc` block)
Block template header, `banner.py:3917-3918`: "Parameter used by SysCalc **--code not supported anymore--**". These feed the retired SysCalc program (`systematics_program='syscalc'`), NOT systematics.py:
- `banner.py:4430`: `sys_scalefact` — scale-variation multiplier default (space-separated string); read the value at banner.py:4430. include=False, hidden=True.
- `banner.py:4431`: `sys_alpsfact` default **`"None"`** (literal string "None").
- `banner.py:4432`: `sys_matchscale` default **`"auto"`**.
- `banner.py:4433`: `sys_pdf` default **`"errorset"`** — NOT empty. Template comment: "list of pdf sets. (errorset not valid for syscalc)".
- `banner.py:4434`: `sys_scalecorrelation` — sentinel default (read at banner.py:4434); extra hidden param, not in the template body.

## The block + its reveal mechanism
- `banner.py:3931`: `syscalc_block = RunBlock('syscalc', template_on=..., template_off="")`. **template_off is the EMPTY string** (banner.py:3929) — when off, the syscalc block writes NOTHING to the run_card (unlike ion_pdf/beam_pol which print a "type update X" hint).
- Registered in the block list `banner.py:4190`: `blocks = [heavy_ion_block, beam_pol_block, syscalc_block, ecut_block, ...]`.
- `RunBlock.status(card)` (banner.py:2646-2658): returns True (→ writes template_on) iff `self.name in card.display_block`, OR a user_set field forces it. Default = off.
- **Reveal**: `update syscalc`. `do_update` (common_run_interface.py:6833) at cri.py:6892-6895: `elif args[0] in self.update_block:` → `self.run_card.display_block.append(args[0].lower())`. `update_block` is filled at cri.py:5246 `+= [b.name for b in self.run_card.blocks]`, so `'syscalc'` is a valid target. Interface owns the `do_update` dispatch; the block name + param semantics are ours.

## NLO run_card reweight params (RunCardNLO — DIFFERENT class, banner.py:5594)
These are the NLO analogue of LO `use_syst`/`systematics_arguments`. `RunCardNLO.default_setup`, banner.py:
- `banner.py:5691`: `reweight_scale` default **`[True]`** (fortran_name `lscalevar`) — gate to store scale-variation reweight info. NLO analogue of use_syst for scales.
- `banner.py:5696`: `rw_rscale` (fortran_name `scalevarR`) — μR multiplier-list default; read the list at banner.py:5696.
- `banner.py:5697`: `rw_fscale` (fortran_name `scalevarF`) — μF multiplier-list default; read the list at banner.py:5697.
- `banner.py:5698`: `reweight_pdf` default **`[False]`** (fortran_name `lpdfvar`) — gate to store PDF-error reweight info (default OFF at NLO, unlike LO's sys_pdf=errorset).
- `banner.py:5692-5695`: `rw_rscale_down/up`, `rw_fscale_down/up` default to a sentinel (hidden; read at banner.py:5692-5695) — legacy 2-point form; if set, overwrite `rw_(r/f)scale` to `[1.0,up,down]` (banner.py:5851-5857).
- **check_validity constraints**: `len(rw_rscale)`/`len(rw_fscale)` capped at a max length (read the cap at banner.py:5904-5907, else InvalidRunCard); `1.0` must be present and forced to be the FIRST element (banner.py:5908-5918, warns+inserts/swaps); `store_rwgt_info` default False (banner.py:5701, needed for NLO systematics/reweight); `reweight_pdf`/`lhaid` and `reweight_scale`/`dynamical_scale_choice` lists must be equal-length (banner.py:5896-5899).

**The scalevarR×scalevarF tensor-product combination computation is amcatnlo's slice** (integrator-side Fortran `reweight_xsec.f`, emitted per-event during NLO integration). The run_card params HERE are the multiplier lists + gates I own; the full enumeration and the post-hoc envelope at analysis time are NOT filtered at generation — MG stores every combo, with NO anti-correlated up/down·down/up exclusion at the generation stage. Cross-slice pointer: amcatnlo for the weight-emission mechanics.

## use_syst side-effects at check_validity
- `banner.py:4529-4538`: if `use_syst` and both beams EVA (`pdlabel1==pdlabel2=='eva'`), a `--pdf=errorset` in `systematics_arguments` is swapped to `--pdf=central` with `logger.warning` (no PDF replicas for EVA).
- `banner.py:4551-4555`: if `use_syst` and `ickkw>0`, `alpsfact` forced to 1.0 with warning.
- `banner.py:4787,4840,4984`: various regimes force `use_syst=False`.

## Doc-myth corrections (this input)
1. `sys_pdf` default is **`"errorset"`, not empty** (banner.py:4433).
2. sys_scalefact/sys_pdf/sys_alpsfact/sys_matchscale drive the **deprecated SysCalc**, not the modern on-the-fly reweighting. Modern systematics.py reads `systematics_arguments` (banner.py:4428). Do not describe editing sys_pdf as "the way to add PDF variations" — that path is retired.
3. `use_syst` "enables on-the-fly reweighting" is loose: it stores the LHE info; the reweighting is run by `do_systematics`/the systematics program, and use_syst=True is a precondition (InvalidCmd otherwise).
4. lhapdf6 requirement is a runtime gate in `do_systematics`, not a run_card param (lhapdf5/absent → silent no-op; see `do-systematics-entry`).
