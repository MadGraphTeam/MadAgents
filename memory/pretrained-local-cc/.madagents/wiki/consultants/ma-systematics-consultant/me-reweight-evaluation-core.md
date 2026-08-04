---
description: ME-reweight evaluation core in ReweightInterface — per-event calculate_weight (LO) + calculate_matrix_element (smatrixhel f2py call) + calculate_nlo_weight (NLO-accurate), mode->weight-name map, helicity/ordering/identical-particle/loop-stability/allow_missing_finalstate handling.
---

# ME-reweight evaluation core

`$MADGRAPH_INSTALL/madgraph/interface/reweight_interface.py`, v3.7.1. How `ReweightInterface` actually computes the alternate-hypothesis weight per event, *below* the command layer (commands/gating live in `reweight-interface`; the Sudakov branch in `ew-sudakov-reweight`). This is the standalone-matrix-element evaluation that produces each `<weight id='rwgt_<id>'>` value.

## Mode → weight-name map (`get_weight_names`, ri.py:480-494)
`change mode` selects which weight suffixes are produced:
- `LO` → `['']` ; `NLO` → `['_nlo']` ; `LO+NLO` → `['_lo','_nlo']` ; `NLO_tree` → `['_tree']`.
- empty mode + NLO event → `['_nlo']` ; else (empty mode, LO event) → `['']`.
The suffix is appended to the weight id (interacts with `lhe-weight-indexing`); a single launch can emit multiple weights per hypothesis (e.g. LO+NLO → two ids).

## LO branch (`calculate_weight`, ri.py:1129-1171)
Plain reweight (not Sudakov, not NLO-mode):
1. `w_orig = calculate_matrix_element(event, 0)` — ME under the *original* param card/process.
2. `jac, new_event = self.change_kinematics(event)` — reshuffles external kinematics for mass effects (external masses only); returns a Jacobian. `new_event` can be the same object (in-place).
3. `w_new = calculate_matrix_element(new_event, 1)` — ME under the *new* hypothesis (`hypp_id=1`).
4. Returns `{'orig': orig_wgt, '': w_new/w_orig * orig_wgt * jac}` (ri.py:1171).
   The reweighted value is the ME ratio times the original event weight times the reshuffling Jacobian.
- `w_orig == 0` → dumps diagnostics and `raise Exception("Invalid matrix element for original computation (weight=0)")` (ri.py:1169). Hard error.

## change_kinematics — mass-reweight Jacobian (ri.py:1104-1126)
Called from `calculate_weight` step 2 to reshuffle external kinematics when the new param_card changes external masses. **LO-only**: only `isinstance(self.run_card, banner.RunCardLO)` triggers a reshuffle; NLO returns `jac=1, new_event=event` unchanged (ri.py:1107-1112).
- LO path: `jac = event.change_ext_mass(self.new_param_card)` (ri.py:1108). `change_ext_mass` (lhe_parser.py:2326-2356) is a **RAMBO mass-shuffle**: collects status==1 (final-state) momenta, looks up each new mass from `new_param_card` mass block, and if ALL masses match the event within tolerance (`misc.equal(...)` with the sig-fig/zero-limit args at lhe_parser.py:2326-2356) **returns 1 (no reshuffle)**; else `mass_shuffle(old_momenta, sqrts, new_masses)` rescales final-state masses **preserving sqrts** and returns the phase-space Jacobian. Internal (resonance) masses are NOT preserved — only external. The reshuffled momenta overwrite the event in place.
- **Hard gate when `jac != 1`** (ri.py:1114-1117): if `output_type == 'default'` → `logger.critical('mass reweighting requires dedicated lhe output!. Please include "change output 2.0" in your reweight_card'); raise Exception`. A mass-changing reweight REQUIRES `change output 2.0` (a fresh reweighted LHE), because reshuffled kinematics cannot be expressed as a weight on the original event. With default output a mass change is a HARD error.
- New-event scale/αs recompute (ri.py:1118-1124, only when `jac != 1`): `mode = run_card['dynamical_scale_choice']`; **if mode == -1 → forced to 3 (HT/2) with `logger.warning('dynamical_scale is set to -1. New sample will be with HT/2 dynamical scale for renormalisation scale')`** (warning emitted once, `dynamical_scale_warning` flag). Then `new_event.scale = event.get_scale(mode)` and `new_event.aqcd = self.lhe_input.get_alphas(new_event.scale, lhapdf_config=...)` — αs is recomputed at the new scale for the reshuffled event. (Distinct from the no-reshuffle case where `event.aqcd` is used directly.)

## The ME call (`calculate_matrix_element`, ri.py:1544-1686)
The single point where the f2py-compiled standalone ME is invoked.
- `tag, order = event.get_tag_and_order()`; `id_to_path[tag] -> (orig_order, Pdir, hel_dict)` (ri.py:1566). Second model/process uses `id_to_path_second` for `hypp_id != 0` (ri.py:1567-1575).
- Module dispatch: `base = basename(dirname(Pdir))`; `rw_me` → `f2pylib[(base, 2+hypp_id)]`, else (`rw_mevirt`) → `f2pylib[(base, 2)]` (ri.py:1577-1583). Virtual hypp_id is a string `'V0'`/`'V1'` → tag gets `'V'` appended, int extracted (ri.py:1558-1560).
- **The actual ME**: `module.smatrixhel(pdg, pid, p, event.aqcd, scale2, nhel)` inside `misc.chdir(Pdir)` with stdout muted (ri.py:1664-1666). `event.aqcd` is the event's αs (the header warns param_card αs is ignored — αs taken from event). `scale2 = event.scale**2` if not passed (ri.py:1658-1662).
- **Loop stability**: if `smatrixhel` returns a tuple `(value, code)`, `(code%1000)//100 == 4` → value forced to `0.` (unstable phase-space point dropped) (ri.py:1669-1674).

## Helicity / ordering (ri.py:1585-1602)
- `keep_ordering` → single momentum config `[get_momenta]`; else `get_all_momenta` returns *all* permutations consistent with the tag. If `len(all_p) > 1` (ordering ambiguity), **helicity reweighting is silently forced off** with `logger.warning("due to ordering ambiguity, we flip off helicity per helicity reweighting.")` (ri.py:1589-1592).
- `nhel = hel_dict[tuple(hel_order)]` if `helicity_reweighting and 9 not in hel_order`; else `nhel = -1` (sum over helicities) (ri.py:1597-1601). Undefined helicity (`9` present in event) → summed.

## identical_particle_in_prod_and_decay (ri.py:1642-1686)
Governs combination over the multiple momentum permutations in `all_p` (the assignments produced when an identical particle appears in BOTH production and decay). Default `"average"` (constructor, ri.py:95).
- `average` → `me_value += new_value` per permutation (1675-1676), return `me_value/len(all_p)` (1683-1684).
- `max` → keep the largest-abs `new_value` (1677-1679), return it (1685-1686).
- `crash` → if `len(all_p) > 1` raise `Exception("Ambiguous particle in production and decay. crash as requested...")` (1642-1644).
Set via `do_change` → `change identical_particle_in_prod_and_decay average|max|crash`; the value is lower-cased and any other value is rejected with `Exception("...can only be one of the following ['average', 'max', 'crash']")` (ri.py:441-444).
- **`crash` trap (ri.py:1675-1681)**: the per-permutation loop's dispatch is `if average / elif max / else: raise Exception("not valid option")`. There is NO branch for `crash`, so when `len(all_p) == 1` (no ambiguity, the early crash-check at 1642 does not fire) a `crash`-configured reweight still enters the loop and hits the `else` → raises "not valid option" on that ordinary event. Net: with `crash` set, `len>1` raises the "Ambiguous..." message and `len==1` raises "not valid option" — every event raises. `crash` is a hard-abort mode (loud-fail), usable only to assert "no identical-particle ambiguity is tolerated"; it does not compute a weight. Note the common assumption that `crash` aborts only on detected ambiguity holds for `len>1` but misses the non-ambiguous `len==1` case, which also aborts with the different "not valid option" message.

## NLO-accurate branch (`calculate_nlo_weight`, ri.py:1373-1502)
Reached when `has_nlo and rwgt_mode != 'LO'` (ri.py:1133-1138). Operates on `<mgrwgt>` partial-weight info.
- `event.parse_nlo_weight(threshold=self.soft_threshold)` (ri.py:1379; `change soft_threshold FLOAT`).
- **Pure-QCD gate**: `if not event.nloweight.ispureqcd(): raise Exception('NLO reweighting does not support mixed expansion mode. Only LO accurate mode is allowed.')` (ri.py:1380-1381). `ispureqcd` (lhe_parser.py:3612-3622) returns False if any contribution-event's weights span >1 value of `int(orderflag/10)` — i.e. the Born is not a unique power of αs. **Mixed QCD+QED Born → hard error; NLO ME reweight is QCD-expansion-only.**
- Per contribution-event (`cevent`): Born ratio `ratio_T = w_new/w_orig` from two `calculate_matrix_element` calls. If `need_V` (any cwgt type in `[2,14,15]` and `_nlo` requested), also computes virtual via `'V0'`/`'V1'` hypp_id at `scale2=scale2**2`, forming `ratio_BV = (w_newV+w_new)/(w_origV+w_orig)` (ri.py:1404-1420).
- `_nlo` weight: type∈[2,14,15] uses `ratio_BV`, else `ratio_T`, applied to `pwgt`; `_tree` applies `ratio_T` to all; `_lo` is a plain LO ratio (ri.py:1432-1486).
- Recombined via `combine_wgt_local(scales2, pdg, bjx, ..., gs, qcdpower, self.pdf)`.
- **Precision filter**: per-contribution `avg = partial_check/ref_wgt`; contributions with `avg` outside a tolerance band around 1 (read the band at ri.py:1466-1468, 1477-1480) are dropped (set 0) for `_nlo`, or kept un-corrected for `_tree`. A numerical-stability guard inside the reweight, not VEGAS.
- `self.pdf` lazily built as `lhapdf.mkPDF(run_card.get_lhapdf_id())` on first NLO weight (ri.py:1134-1136) — uses the *event's* PDF id.

## allow_missing_finalstate — message inversion trap (ri.py:1571-1575)
When the event's `tag` is absent from the second model/process `id_to_path_second`:
- `allow_missing_finalstate == True` → `return 0.0` (event's reweighted weight set to zero).
- `== False` → `logger.critical('...If you want to set the weights of such events to zero use "change allow_missing_finalstate False"'); raise Exception`.
**The critical-message text is wrong**: it says set the option to *False* to zero such weights, but the code zeros only when the option is *True* (ri.py:1571). Correct action to zero-out missing-state events: `change allow_missing_finalstate True`. Default is False (ri.py:94), so a final state absent from the new model crashes the reweight by default.

## Cautions
- αs is always taken from the event (`event.aqcd`), never from the new param_card — consistent with the reweight_card header note. A new-hypothesis param_card with a different αs(MZ) will NOT change the αs used in the ME.
- Ordering ambiguity silently disables helicity reweighting (warning only) — a multi-permutation final state loses per-helicity accuracy.
- Loop-stability code 4xx silently zeros that point's ME — contributes 0 to the reweighted weight, no error.
- NLO ME reweight is restricted to pure-QCD-expansion Born (`ispureqcd`); EFT/EW-mixed Born at NLO → hard Exception, must fall back to LO-accurate mode.
- `allow_missing_finalstate=False` (default) + a final state not in the new model → Exception, and the suggested fix in the message is the wrong boolean.
- **Mass-changing reweight requires `change output 2.0`**: any external-mass change (LO) reshuffles kinematics (`jac != 1`) and HARD-errors under default output — a mass-shift reweight silently expects the dedicated-LHE output mode. Mass changes are also NLO-inert (NLO `change_kinematics` never reshuffles, `jac` always 1).
- RUNTIME claims (smatrixhel return shape, emitted warnings, the precision-filter effect) are read from source, not probe-confirmed — a launch on an actual reweight_card would confirm the emitted weights and any warnings.
