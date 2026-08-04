---
description: aMCatNLOCmd.ask_run_configuration — the layer between AskRunNLO dialog and run() — mode resolution from switches, card-keeping, banner run_settings, run_name _LO suffix, runtime ickkw guards.
---

# `ask_run_configuration` — mode resolution / card-keeping / banner

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`, `aMCatNLOCmd.ask_run_configuration(self, mode, options, switch={})` (line 5779). This is the orchestration layer that sits BETWEEN the `AskRunNLO` ControlSwitch dialog (which only sets the six switches) and `run()` (which integrates). Called by `do_launch` (1739), `do_shower` (1529, mode `'onlyshower'`), `do_compile` (1888), `do_calculate_xsect` (via do_launch). Returns the resolved `mode` string.

## Pre-dialog mode coercion (5782-5806)
- `options['parton']`/`['reweightonly']` default to False if absent.
- `mode == 'auto'` → `mode = None` (5787).
- `not mode and (options['parton'] or options['reweightonly'])` → `mode = 'noshower'` (5789). So `do_calculate_xsect` (sets parton=True) and `-r/--reweightonly` land on noshower path pre-dialog.
- `passing_cmd` built from incoming `switch` items + `do_reweight`/`do_madspin` options (`reweight=ON`/`madspin=ON`). `mode=='onlyshower'` appends `'onlyshower'` and forces `force=True` (5802); else appends the mode.

## The dialog call (5809)
`self.ask('', '0', [], ask_class=self.action_switcher, mode=mode, force=(force or mode), first_cmd=passing_cmd, return_instance=True)` → returns `(switch, cmd_switch)`. `action_switcher` is `AskRunNLO`. `force or mode` means: if a concrete mode was passed (e.g. shortcut `aMC@NLO`), the dialog is auto-forced (non-interactive).

## Mode resolution from switches (5814-5832)
If dialog returned `switch['mode']` (onlyshower path), use it. Else if `mode` still unset/auto, resolve from switch values:
- `order=='LO'`: `runshower` → `aMC@LO`; `fixed_order=='ON'` → `LO`; else → `noshowerLO`.
- `order=='NLO'`: `runshower` → `aMC@NLO`; `fixed_order=='ON'` → `NLO`; else → `noshower`.
- Logs `will run in mode: <mode>` (5832). **This is where the four+two run modes are actually named** — `AskRunNLO` only holds switches; the LO/NLO/aMC@LO/aMC@NLO/noshower/noshowerLO string is produced here.

`switch['runshower']` is set by `AskRunNLO.answer` (False if shower not in allowed or =='OFF'); so a NLO order with shower==OFF resolves to `noshower`, not `aMC@NLO`.

## noshower warning (5834-5838)
- `mode=='noshower'` + `shower=='OFF'` → warning: "NLO events without showering are NOT physical... choose NOW which parton-shower you WILL use and specify it in the run_card."
- `mode=='noshower'` + shower set (but unavailable) → info ($MG:BOLD): "Your parton-shower choice is not available for running. Events will be generated for the associated parton shower."

## Card keeping (5841-5865)
Builds `cards = ['param_card.dat','run_card.dat']`, `ignore=[]`:
- `mode in ['LO','NLO']` (fixed order): forces `options['parton']=True`, `ignore=['shower_card.dat','madspin_card.dat']`, appends `FO_analyse_card.dat`.
- else (event modes): append `madspin_card.dat` if `switch['madspin']!='OFF'`; `reweight_card.dat` if `switch['reweight']!='OFF'`; `madanalysis5_hadron_card.dat` if `switch['madanalysis'] in ['HADRON','ON']`.
- `'aMC@' in mode` → append `shower_card.dat` (5855).
- `mode=='onlyshower'` → `cards=['shower_card.dat']` (overrides).
- `options['reweightonly']` → `cards=['run_card.dat']`.
- `self.keep_cards(cards, ignore)` (5862) — physically removes cards not in the list from Cards/ (so e.g. a fixed-order run strips shower/madspin cards).

## Card editing + banner (5868-5921)
- `first_cmd = cmd_switch.get_cardcmd()` (5869) — the `set parton_shower X` / madspin / reweight edits the dialog accumulated.
- `ask_edit_cards(cards, ..., first_cmd, switch)` unless forced (5871).
- Builds `self.banner` (Banner()), adds each card, AND adds a `run_settings` text block = `'\n'.join('%s = %s' % (k,v) for k,v in switch.items())` (5880). **`do_banner_run` reads this `run_settings` block back to reconstruct `mode_status`** — that is the round-trip seam.
- For non-onlyshower: charges `run_card`, `run_tag`; auto-generates `run_name` via `find_available_run_name` if unset, and appends `_LO` to a `run_`-prefixed name when `mode in ['LO','aMC@LO','noshowerLO']` (5890-5892). `set_run_name(..., 'parton')`.

## Runtime ickkw guards (5894-5915) — the FxFx/jet-veto mode gates [stage 3 of [[fxfx-ickkw3-lifecycle]]]
Evaluated here (after run_card charged), distinct from RunCardNLO.check_validity (banner.py, stage 2) which fires at card-write time. The full five-stage FxFx enforcement map is [[fxfx-ickkw3-lifecycle]]:
- `ickkw==3` + `mode in ['LO','aMC@LO','noshowerLO']` → `InvalidCmd("FxFx merging (ickkw=3) not allowed at LO")`.
- `ickkw==3` + (`aMC@NLO` with `parton_shower!='PYTHIA8'`) or `noshower` → FxFx by-hand-removal warning; then:
  - `parton_shower=='PYTHIA6Q'` → `InvalidCmd("FxFx merging does not work with Pythia6's Q-squared ordered showers")`.
  - parton_shower not in {HERWIG6, PYTHIA8, HERWIGPP} → asks y/n "FxFx merging not tested for X shower" (n → recurses ask_run_configuration; commented-out raise).
- `ickkw==-1` + `mode in ['aMC@NLO','noshower']` → `InvalidCmd("NNLL+NLO jet veto runs (ickkw=-1) only possible for fNLO or LO")`.
- charges `shower_card` for aMC@/onlyshower; `FO_analyse_card` for LO/NLO.

## Cautions
- The mode string is NOT produced by `AskRunNLO`; it is resolved here from switches (5817-5832). A page describing "the dialog returns mode X" is wrong — the dialog returns switches; this method maps them.
- `keep_cards` is destructive to the Cards/ directory: switching a run from event mode to fixed-order can strip shower/madspin cards. The card set is mode-dependent, decided here.
- These runtime ickkw guards (FxFx/jet-veto) duplicate intent with `RunCardNLO.check_validity` but fire at a different time (run-launch vs card-write) and have different exact branches (e.g. the y/n untested-shower prompt only exists here). Cite the right one for the question's timing.
- `do_calculate_xsect` and `--reweightonly` silently pre-coerce mode to `noshower` (5789) before the dialog even runs.
