---
description: The launch-time menu (AskRun ControlSwitch + ask_run_configuration) that builds the switch dict + cards list driving the downstream flow — module-availability gating, default selection, and silent consistency auto-changes (Py8+PGS, Rivet->Py8).
---

# Launch-menu switcher (AskRun / ask_run_configuration)

The step between `do_generate_events` and the integration flow that decides which downstream tools run. Cites `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (ME) and `common_run_interface.py` (CR), v3.7.1.

## ask_run_configuration (ME 6745-6807) — the driver
`do_generate_events`/`do_multi_run` call this to obtain the `switch` dict.
- `-R`/`--reweight` -> seeds `reweight=ON`; `-M`/`--madspin` -> `madspin=ON` as `first_cmd` (6749-6752).
- `self.ask(..., ask_class=self.action_switcher, ...)` (6754) runs the `AskRun` menu (`action_switcher = AskRun`, ME 6743), returns `(switch, cmd_switch)`. Result stored on `self.switch` (6758, "for plugin purpose").
- **Builds the `cards` list from the switch** (6765-6789): always `param_card.dat`+`run_card.dat`; then conditionally `pythia_card.dat` (shower==Pythia6) / `pythia8_card.dat` (Pythia8) / `pgs_card.dat` (detector in PGS,DELPHES+PGS) / `delphes_card.dat` (+`delphes_trigger.dat` only for **Delphes2**, i.e. when `delphes_path/data` does NOT exist, 6774-6777) / `madspin_card.dat` / `reweight_card.dat` / `madanalysis5_parton_card.dat` / `madanalysis5_hadron_card.dat` (MA5 + shower!=OFF) / `plot_card.dat` (MA4) / `rivet_card.dat`.
- `self.keep_cards(cards)` (6791) — hides every non-selected optional card as a `.card` dotfile (keep_cards on monitor-status page). **So the cards list this menu builds is exactly what survives un-hidden.**
- `MadLoopParams.dat` appended to the edit list if present (6795-6796).
- **Forced path** (6798-6800): if `self.force`, only `check_param_card` then returns the switch — NO card-edit prompt. So `-f` launches take the menu defaults silently.
- Otherwise `ask_edit_cards(cards, ...)` opens the card editor; `dynamical` switch -> mode='auto' (6803-6806).

## AskRun (ME 497-906) — the ControlSwitch subclass
`to_control` order (ME 500-505, statically confirmed): `shower, detector, analysis, madspin, reweight`. Each key has `get_allowed_<k>` / `set_default_<k>` / optional `check_value_<k>` / `ans_<k>` / `consistency_<k>_<other>` methods.

### The exact switch set + option strings (get_allowed_*, ME 560-897)
The LO madevent launch menu offers **five** switches, in `to_control` order: `shower`, `detector`, `analysis`, `madspin`, `reweight` (ME 500-505). Each option list is built from `available_module`; the literal option strings (verbatim from source, not the uppercase forms a hand doc may use):
- **shower** (get_allowed_shower 560-573): `Pythia6` (if PY6), `Pythia8` (if PY8), then `OFF` appended only if at least one is available. There is **no HERWIG option in the LO madevent AskRun** — Herwig7/HW6 belong to the NLO `AskRunNLO` dialog (amcatnlo slice), not here. So the real LO shower list is `Pythia6|Pythia8|OFF`, gated by install.
- **detector** (643-657): `PGS` (if PGS), `Delphes` (if Delphes), then `OFF`. Real list `PGS|Delphes|OFF` — not `DELPHES|OFF`; PGS is present whenever pythia-pgs is installed.
- **analysis** (742-759): `ExRoot`, `MadAnalysis4`, `MadAnalysis5`, `Rivet` (each gated by its module), then `OFF`. Real list `ExRoot|MadAnalysis4|MadAnalysis5|Rivet|OFF` — far richer than `MadAnalysis5|OFF`.
- **madspin** (827-840): `['OFF','ON','onshell','full']` when MadSpin available, else `[]`. So the values are `OFF|ON|onshell|full` (onshell/full are spinmode shortcuts, see below) — not a bare `ON|OFF`. `check_value_madspin` (841-853) also aliases `madspin`->`full`, `none`->`none`.
- **reweight** (881-895): `['OFF','ON']` (+ any plugin `new_reweight` opts) when the `reweight` module is available. **This switch exists** — a hand doc listing only shower/detector/madspin/analysis omits it entirely.

A switch key whose `get_allowed_*` returns `[]` (module not installed) is shown by the ControlSwitch base as `Not Avail.` rather than dropped; the option strings above appear only for installed tools. So on a bare install (only Pythia8 configured) shower shows `Pythia8|OFF` and detector/analysis/madspin/reweight read `Not Avail.`.

### check_available_module (ME 516-544) — what's offered at all
Builds `self.available_module` from configured tool paths:
- `pythia-pgs_path` -> PY6 + PGS; `pythia8_path` -> PY8; `madanalysis_path` -> MA4; `madanalysis5_path` -> MA5; `exrootanalysis_path` -> ExRoot.
- `delphes_path` -> Delphes **only if PY6 or PY8 already present**; else warns "Delphes program installed but no parton shower module detected. Please install pythia8" and Delphes is NOT added (530-534).
- `rivet_path` -> Rivet **only if PY8 present**; else warns similarly (535-539).
- MadSpin available if not MADEVENT-standalone or `mg5_path` set; reweight added on top only if `has_f2py()` or an `f2py_compiler` is configured (541-544). **So reweight can be unavailable purely for lack of f2py even with everything else installed.**

### Default selection (set_default_*) — card-presence driven
Each switch defaults ON to a tool only if both the module is available AND its card already exists in `Cards/`:
- shower (575-586): Pythia6 if PY6+`pythia_card.dat`; elif Pythia8 if PY8+`pythia8_card.dat`; elif any shower available -> OFF; else 'Not Avail.'.
- detector (660-673): **explicitly calls `set_default_shower()` first** ("ensure that this one is called first!", 662) — so detector default depends on the already-set shower default. PGS if PGS-avail + shower==Pythia6 + `pgs_card.dat`; elif Delphes if Delphes-avail + shower!=OFF + `delphes_card.dat`; elif available -> OFF.
- analysis (807-822): MA4 if `plot_card.dat`; elif MA5 if either MA5 card present; elif ExRoot; elif OFF.
- madspin (855-864): ON if `madspin_card.dat` present else OFF.
- reweight (897-906): ON if `reweight_card.dat` present else OFF.

So **a default launch (no `-f`) auto-selects a downstream tool iff its card was already left in `Cards/`** — the presence of a card from a prior run silently re-enables that step.

### Consistency auto-changes (consistency_XX_YY) — silent cross-switch mutation
When the user sets one switch, these fire to keep the combination valid (return value = forced new value for the *other* key):
- `consistency_shower_detector` (623-636): shower->OFF forces detector OFF; **shower==Pythia8 + detector==PGS forces detector OFF** (PGS needs Pythia6).
- `consistency_detector_shower` (720-736): detector==PGS forces shower Pythia6; detector==Delphes forces shower Pythia8 (or Py6 fallback).
- `consistency_shower_analysis` / `consistency_analysis_shower` (782-804): **Rivet requires Pythia8** — selecting Rivet forces shower Pythia8; setting shower!=Pythia8 forces analysis OFF if it was Rivet.

These are silent value changes driven by the menu, not by the run_card — they belong to the same "override-without-opt-in" family as the launch-time-runcard-overrides lens, but here the trigger is the menu combination, not a process characteristic.

### MadSpin spinmode shortcuts (get_cardcmd_for_madspin 866-876)
madspin switch values `onshell`/`full`/`none` are not just ON/OFF: each injects an `edit madspin_card ... set spinmode <mode>` pre-command so the madspin_card's spinmode line is rewritten before the user edits cards. (MadSpin-card-content semantics are the MadSpin slice; this is the launch-menu hook that sets spinmode.)

## Cautions
- A downstream tool is **offered only if its tool path is configured** (`check_available_module`); a "missing" Pythia8/Delphes/Rivet option in the menu means the path isn't set in `mg5_configuration.txt`, not a bug. Delphes additionally needs a shower; Rivet specifically needs Pythia8.
- A tool is **auto-selected by default** purely because its card was left in `Cards/` from a prior run — re-running `generate_events` can silently re-trigger a downstream step the user thought they were done with. `keep_cards` only hides cards for *deselected* tools.
- `-f` (force) skips the card-edit prompt entirely and runs the menu defaults — the silent auto-selection above applies with no chance to deselect.
- detector default is order-dependent on shower (set_default_shower called inside set_default_detector); the `to_control` order shower-before-detector is load-bearing.
- Consistency rules silently flip a switch you didn't touch: e.g. selecting Rivet flips shower to Pythia8; selecting PGS while shower is Pythia8 flips detector to OFF.
- `delphes_trigger.dat` is added to the cards list only for Delphes2 (no `delphes_path/data` dir) — a Delphes3 install never edits a trigger card here.
