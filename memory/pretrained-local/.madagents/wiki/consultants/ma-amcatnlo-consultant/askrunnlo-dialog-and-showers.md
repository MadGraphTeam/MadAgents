---
description: AskRunNLO ControlSwitch dialog — six switches, lo/nlo/aMC@LO/aMC@NLO shortcuts, shower availability/aliasing, ninitial==1 / QED forcing, AND the LO AskRun vs NLO AskRunNLO dialogue contrast (order/fixed_order added, detector dropped).
---

# `AskRunNLO` — interactive run-mode dialog + shower selection

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`, `class AskRunNLO(cmd.ControlSwitch)` (line 922).

## Six switches (to_control, line 924)
`order` (LO/NLO), `fixed_order` (ON = no shower, OFF = with shower / MC@[N]LO matching), `shower`, `madspin`, `reweight`, `madanalysis`. `quit_on += ['onlyshower']` (line 931).

`hide_line` (line 944): if `'QED' in proc_characteristics['splitting_types']`, hides `madspin/shower/reweight/madanalysis` (EW corrections → only fixed-order fNLO).

## Mode shortcuts (ans_* methods)
- `ans_lo` (990): order=LO, fixed_order=ON, shower=OFF.
- `ans_nlo` (1000): order=NLO, fixed_order=ON, shower=OFF.
- `ans_amc__at__nlo` (1008): order=NLO, fixed_order=OFF, shower=ON.
- `ans_amc__at__lo` (1016): order=LO, fixed_order=OFF, shower=ON.
- `ans_noshower` (1024): NLO, fixed_order=OFF, shower=OFF. `ans_noshowerlo` (1040): LO equivalent.
- `ans_onlyshower` (1032): mode=onlyshower, madspin=OFF, reweight=OFF.
- `ans_madanalysis5` (1048): alias → `madanalysis`.

The four resolved run modes (`LO/NLO/aMC@LO/aMC@NLO` + `noshower/noshowerLO`) are mapped from switches in `ask_run_configuration` (line ~5817), not here.

## fixed_order forcing (lines 1072–1090)
`get_allowed_fixed_order`: returns `['ON']` only (no shower possible) when `ninitial==1` (decay, 1→N) OR `'QED' in splitting_types`; else `['ON','OFF']`. `set_default_fixed_order` mirrors this. So decay processes and EW-correction processes are **fixed-order-only**.

## Shower availability (check_available_module line 969, get_allowed_shower line 1191)
Module detection sets `self.available_module`:
- `MA5` if `madanalysis5_path`; `PY8` if `pythia8_path`; **`HW7`** if `hwpp_path AND thepeg_path AND hepmc_path` (note: the module token is `HW7`, used for Herwig++/Herwig7); `StdHEP` if `MCatNLO/lib/libstdhep.a` exists; `MadSpin`/`reweight` depend on mg5_path / f2py.

`get_allowed_shower` base list = `['OFF']`; if `StdHEP` present: `['HERWIG6','OFF','PYTHIA6Q','PYTHIA6PT']`; `+PYTHIA8` if PY8; `+HERWIGPP` if HW7. Returns `['OFF']` if `ninitial==1`, QED splitting, or `bc` not on PATH (line 1201).

`check_value_shower` (1222) aliases: `P8/PY8/PYTHIA_8→PYTHIA8`; `PY6/P6/...→PYTHIA6PT`; `PY6Q/...→PYTHIA6Q`; `HW7/HERWIG7→HERWIG7`; `HW++/HWPP/HERWIG++→HERWIGPP`; `HW6/HERWIG_6→HERWIG6`; `ON`→`run_card['parton_shower']`.

`answer` property (952): `HERWIG7→HERWIGPP` normalisation; sets `out['runshower']` False if shower not in allowed or == 'OFF'.

## Consistency couplings
- `consistency_fixed_order_shower` (1150): fixed_order ON forces shower (also madspin/reweight) OFF; symmetric `consistency_shower_fixed_order` (1172) forces fixed_order OFF when a shower/madspin/reweight/MA5 is turned on.
- `consistency_QED` (1122): for QED splitting forces fixed_order=ON, shower/madanalysis/reweight=OFF, madspin∈OFF/none, warns "NLO+PS mode is not allowed for processes including electroweak corrections".
- `consistency_shower_madanalysis` (1282): MA5 requires a shower (shower OFF + MA5 ON → MA5 OFF). MA5 only on (N)LO+PS.
- reweight allowed values (1394): `['OFF','ON','NLO','NLO_TREE','LO']`; madspin (1324): `['OFF','ON','onshell']`.
- `get_allowed_madspin` (1305): `ninitial==1` (decay) → **removes `'MadSpin'` from `self.available_module`** (1317) and returns `['OFF']`; `'QED' in splitting_types` → `['OFF']`; else `['OFF','ON','onshell']`. The ninitial==1 case is a hard module-removal (not just a value restriction), so MadSpin is unavailable for 1→N decay computations at NLO.

## get_cardcmd_for_* (run_card edits emitted by the dialog)
- shower (1295): `set parton_shower <X>`.
- madspin (1361): edits madspin_card spinmode (onshell/madspin/none).
- reweight (1410): edits reweight_card `change mode` (LO/NLO/NLO_tree) + `set store_rwgt_info T` for NLO modes.

## LO `AskRun` vs NLO `AskRunNLO` — the two launch dialogues are different classes
An aMC@NLO output (from a `[QCD]`-style generate → `output`) launches through `aMCatNLOCmd.do_launch` (1739) → `ask_run_configuration` (1764/1766) → **`AskRunNLO`**. A plain LO/tree output launches through `madevent_interface.py` `do_launch` → **`AskRun`** (`madevent_interface.py:497`). Different ControlSwitch subclasses, different switch sets:

| | LO `AskRun` (madevent_interface.py:500) | NLO `AskRunNLO` (amcatnlo_run_interface.py:924) |
|---|---|---|
| switches | `shower`, `detector`, `analysis`, `madspin`, `reweight` (5) | `order`, `fixed_order`, `shower`, `madspin`, `reweight`, `madanalysis` (6) |
| `order` (LO/NLO) | **absent** | present |
| `fixed_order` (ON/OFF) | **absent** | present |
| `detector` (Delphes/PGS) | present | **absent** |
| standalone `analysis` | present (plot/convert + MA5) | folded into `madanalysis` |

So the NLO dialogue *adds* `order` and `fixed_order` (the two knobs that pick LO/NLO/aMC@LO/aMC@NLO/noshower — see mode resolution in [[ask-run-configuration-mode-resolution]]) and drops the standalone `detector` switch. The `fixed_order=ON` → shower-forbidden coupling (`consistency_fixed_order_shower`, 1150) has **no analogue** in the LO menu — LO has no fixed-order concept. NLO shower option list (`HERWIG6/PYTHIA6Q/PYTHIA6PT/PYTHIA8/HERWIGPP/OFF`, get_allowed_shower 1191) is gated by `StdHEP`/`PY8`/`HW7` modules + `bc` on PATH + `ninitial>1` + no-QED, none of which constrain the LO shower list the same way.

**Caution:** a user carrying LO-`launch` interactive-mode expectations to an NLO output will see a *different* menu — the first two questions (`order`, `fixed_order`) do not exist in the LO dialogue, and there is no `detector` question. Do not assume the LO switch numbering/options transfer; the class is `AskRunNLO`, not `AskRun`.

## Cautions
- Shower availability is environment-dependent: no `bc` binary silently forces shower OFF (1201, 1271 warns). PYTHIA6/HERWIG6 require `StdHEP` (libstdhep.a built). Do not assume a shower is offered without checking these module gates against the install.
- `set_default_order` (1061) has a fall-through bug-ish pattern: it sets LO conditionally then unconditionally `self.switch['order']='NLO'` on line 1065 — default order is effectively always NLO.
