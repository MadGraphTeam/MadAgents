---
description: How aMC@NLO (amcatnlo_run_interface.py) invokes MA5 — hadron-only, post-shower, with NLO-specific gates (no parton MA5, shower-required consistency, QED/decay disable) absent from the LO path.
---

# NLO (aMC@NLO) MA5 interface (v3.7.1)

The earlier pages all walk the LO/MadEvent path (`madevent_interface.py`) and the shared base (`common_run_interface.py`). The aMC@NLO driver `$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py` has its OWN MA5 wiring with constraints the LO path does not impose. The shared driver `run_madanalysis5` (common_run_interface.py:3102) is reused — so input-resolution, get_MA5_cmds, runMA5, failure-handling all behave as the other pages describe; only the ENTRY and the SWITCH/GATE layer differ at NLO.

## HADRON-ONLY: there is no parton MA5 at NLO
- `def do_madanalysis5_parton` exists ONLY in `madevent_interface.py:4226` (the LO MadEvent cmd). `grep -n "madanalysis5_parton\|do_madanalysis5_parton" amcatnlo_run_interface.py` returns ZERO hits. The aMC@NLO interface never references parton MA5 in any form.
- `do_madanalysis5_hadron` is the shared-base entry (`common_run_interface.py:3096`); aMC@NLO inherits it via `common_run.CommonRunCmd`.
- CONSEQUENCE: parton-level MA5 is a LO-only feature. At NLO, MA5 can only run at hadron level, only after the shower. (Physically consistent: NLO LHE events before showering are not physical — the noshower branch even warns this, 1874-1875.)

## The single dispatch (run_generate / after run_mcatnlo, 1869-1872)
```
if not mode in ['LO','NLO','noshower','noshowerLO'] and not options['parton']:
    self.run_mcatnlo(evt_file, options)
    self.exec_cmd('madanalysis5_hadron --no_default', postcmd=False, printcmd=False)
```
- MA5 fires ONLY in the showered branch (`aMC@NLO`/`aMC@LO` event-gen mode), AFTER `run_mcatnlo` (the shower), with `--no_default` (MG-triggered -> silent skip on missing card, per failure-handling-two-layers Layer 1).
- Fixed-order (`LO`/`NLO`) and parton-only (`options['parton']`) and `noshower*` modes do NOT trigger MA5 at all. There is no parton/pre-shower MA5 hook anywhere in this file.

## NLO-specific switch gates (class AskRunNLO + helpers) — absent from LO
The NLO `launch` menu is the `AskRunNLO(ControlSwitch)` class. Its `madanalysis` switch carries gates the LO `analysis` switch does not:

- **availability seed** `check_available_module` (969-973): `'MA5'` added to `available_module` iff `options['madanalysis5_path']` truthy. Same path-gate idea as LO.
- **QED (NLO EW) DISABLE** — `get_allowed_madanalysis` (1433-1434): if `'QED' in proc_characteristics['splitting_types']` -> returns `[]` (no allowed values). `set_default_madanalysis` (1450-1451): switch = `'Not Avail'`. AND in `AskRunNLO.__init__` (945-946) the whole `madanalysis` line is HIDDEN (`hide_line`) alongside madspin/shower/reweight for QED processes. So for NLO EW/QED-split processes MA5 is unavailable AND not even shown.
- **DECAY (1->N) DISABLE** — `get_allowed_madanalysis` (1439-1442): if `proc_characteristics['ninitial']==1` it `available_module.remove('MA5')` and allows only `['OFF']`. A 1->N (decay) process cannot run MA5.
- **otherwise** (1443-1445): allowed `['OFF','ON']`; `set_default_madanalysis` -> `'ON'` iff `Cards/madanalysis5_hadron_card.dat` EXISTS on disk, else `'OFF'`. (Only the hadron card is ever checked — consistent with hadron-only.)
- `check_value_madanalysis` (1459-1468): accepts the allowed set; shortcut `'hadron'` -> `'ON'` if ON allowed, else False. (`'parton'` is NOT a valid value.)
- `proc_characteristics` keys are real run params (banner.py:1755 `ninitial`, :1764 `splitting_types`), written by the FKS exporter for NLO output (export_fks.py:559-560,657 etc.). `splitting_types==['QCD']` is pure-QCD NLO; `'QED'` membership means EW/QED corrections were generated.

## Shower-coupling consistency (NLO-only) — 1282-1293
Two paired consistency callbacks tie the `madanalysis` switch to the `shower` switch (no LO analogue, because parton MA5 at LO needs no shower):
- `consistency_shower_madanalysis(vshower, vma5)` (1282-1287): if `shower=='OFF'` and `ma5=='ON'` -> returns `'OFF'` (forces MA5 OFF).
- `consistency_madanalysis_shower(vma5, vshower)` (1289-1293): if `ma5=='ON'` and `shower=='OFF'` -> returns `'ON'` (forces shower ON).
- Docstring: "MA5 only possible with (N)LO+PS if shower is run." So at NLO you cannot have hadron MA5 without a shower; toggling one forces the other consistent.

## Card-set inclusion + run-chaining
- `cards` assembly (5853-5854): `madanalysis5_hadron_card.dat` appended only when `switch['madanalysis'] in ['HADRON','ON']`. (Only the hadron card; no parton card path.)
- `upgrade_tag` (set_run_name, 4449-4453): `parton`/`shower` levels enable `madanalysis5_hadron`; there is NO `madanalysis5_parton` key (vs the LO upgrade_tag in madevent_interface.py:6377-6393 which has both). Reflects hadron-only again.
- The control-switch label (929): `('madanalysis','Run MadAnalysis5 on the events generated')`; shortcut `ans_madanalysis5 -> madanalysis` (1048-1049).

## Cautions
- A user expecting parton-level MA5 plots from an NLO run gets nothing: there is no parton hook in the NLO driver. Only hadron MA5, only with a shower.
- For NLO EW (QED in splitting_types) the MA5 switch is hidden and 'Not Avail' — a user will not even see it offered; not a bug, an explicit gate (1433,1450,945-946).
- For decay (ninitial==1) processes MA5 is removed from available_module — also silently absent from the menu.
- HYPOTHESIS (runtime, NOT probe-verified): the above gating is read off the switch-class branch structure; `madanalysis5_path` is unset in this install (config-and-install page), and these are NLO-process-shape dependent, so the actual menu rendering was not driven. Probe when an MA5-enabled install + an NLO EW or decay process are available: launch and confirm the madanalysis line is hidden/Not-Avail.
