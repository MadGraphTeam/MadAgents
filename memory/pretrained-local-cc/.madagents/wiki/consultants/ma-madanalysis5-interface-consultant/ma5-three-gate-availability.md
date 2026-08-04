---
description: The three independent gates that each silently no-op MG's MA5 step (path-truthy / card-exists / card-non-default) — MA5's instance of the lead downstream-card-existence-gate playbook.
---

# MA5 three-gate availability (v3.7.1)

Generalization over the path/card checks scattered across config-and-install, invocation-flow, input-resolution-and-cmds, failure-handling-two-layers, and nlo-amcatnlo-ma5-interface. The deeper rule: **MA5 running at all is gated by THREE independent checks evaluated at THREE different lifecycle stages; each one, if it fails, makes MA5 silently do nothing — and they fail differently, so "MA5 produced no plots" has three distinct root causes.** This is the MA5-specific instance of the lead's `downstream-card-existence-gate` playbook (which routes Delphes/Rivet/MA5/PGS/Pythia "did it run?" questions to each tool's gate page).

All cites: `madevent_interface.py` (LO switch), `common_run_interface.py` (driver), `amcatnlo_run_interface.py` (NLO switch).

## Gate 1 — PATH truthy (switch-surface time, earliest)
`options['madanalysis5_path']` must be truthy for MA5 to be offered as an analysis choice.
- LO: `if options['madanalysis5_path']: self.available_module.add('MA5')` (madevent_interface.py:527); then `if 'MA5' in self.available_module: self.allowed_analysis.append('MadAnalysis5')` (:754). If unset, MA5 is never in `allowed_analysis`.
- NLO: `if options['madanalysis5_path']: self.available_module.add('MA5')` (amcatnlo_run_interface.py:972, in `check_available_module`).
- THIS INSTALL: `madanalysis5_path = $MADGRAPH_INSTALL/None` (mg5_configuration.txt:180). PRECISION (probe-confirmed): the gate does NOT pass `if options['madanalysis5_path']:` on a "falsy string" — a non-empty string would be truthy. Instead config-load RESOLVES the value to python `None` (madgraph_interface.py:7441-7448 nulls `self.options['madanalysis5_path']` when `<path>/bin/ma5` is absent OR `is_MA5_compatible_with_this_MG5` returns a reason). `$MADGRAPH_INSTALL/None` has no `bin/ma5`, so the option is `None`, and the `if options['madanalysis5_path']:` test is False -> Gate 1 CLOSED. PROBE: `MasterCmd().options['madanalysis5_path']` is `None` (NoneType), not the string. Until `install MadAnalysis5` populates it, MA5 is unavailable at every level. (config-and-install / output-time-card-creation pages.)
- Effect of failure: switch never appears / not in allowed set. Most invisible failure — user never even sees the option.

## Gate 2 — CARD exists (dispatch / pre-flight time)
Even with a valid path, the operative `Cards/madanalysis5_<mode>_card.dat` must exist on disk.
- Switch auto-select needs it: LO `analysis` switch auto-selects 'MadAnalysis5' only if a parton OR hadron card exists (madevent_interface.py:813-816, the `elif 'MA5' in self.available_module and (...card exists...)` branch). NLO `set_default_madanalysis` -> 'ON' only iff `madanalysis5_hadron_card.dat` exists, else 'OFF' (amcatnlo_run_interface.py:1454-1456).
- Pre-flight in `run_madanalysis5`: missing card under `--no_default` (MG-triggered) -> bare `return` (silent); user-issued -> `raise InvalidCmd` (common_run_interface.py:3114-3134). This is failure-handling-two-layers' Layer 1.
- Effect of failure: silent skip for the MG-driven generate_events chain; hard InvalidCmd only if a user types the command by hand.

## Gate 3 — CARD is non-default (load time, latest)
The card must NOT be the shipped `@MG5aMC skip_analysis` default. Existence is necessary but not sufficient.
- `MA5_card = MadAnalysis5Card(...); if MA5_card._skip_analysis: logger.info("... skipped following user request"); return` (common_run_interface.py:3159-3164).
- The SHIPPED default templates (`Template/LO/Cards/madanalysis5_{parton,hadron}_card_default.dat`) are exactly `@MG5aMC skip_analysis` -> `_skip_analysis=True` (ma5-card-structure page, probe-confirmed). So an install that copied the default card has Gate 2 OPEN (card exists) but Gate 3 CLOSED (it's a no-op).
- Effect of failure: card loads, the analysis is a NO-OP, only an INFO log ("skipped following user request") — NOT an error. The most deceptive of the three: the file is right there, MA5 path is set, yet nothing happens.

## Why three gates, not one — the load-bearing insight
The three gates close at successively later stages and produce successively more deceptive symptoms:
1. Gate 1 (path) closed -> MA5 never offered (invisible at the menu).
2. Gate 2 (card) closed -> MG silently skips (no menu/no plot, no error) OR a hand-user gets InvalidCmd.
3. Gate 3 (skip_analysis) closed -> MA5 "runs" but no-ops with only an INFO line.

So "why did MA5 produce nothing?" has THREE root causes, distinguishable only by which stage failed: not-offered (path), silently-skipped (no card), ran-but-no-op (default card). A user who copied the default card and set the path will pass Gates 1+2 and still get nothing — Gate 3. This is the non-obvious part: a present, parseable, path-backed MA5 card can still be a deliberate no-op.

## Routing / cautions
- This page is the MA5 endpoint of the lead's `downstream-card-existence-gate` playbook. When a user asks "did my MA5 step run / why skipped / why not offered," walk the three gates in order.
- Gate 3 is MA5-specific (the `skip_analysis` escape tag); Delphes/Rivet's third gate is "card is the default/empty template," not a skip tag — do not assume the mechanism transfers verbatim across tools.
- Detection-by-content edge: a `skip_analysis`-only card is NOT even recognized as an MA5 card by `detect_card_type` (returns 'unknown') — see card-identity-and-banner-roundtrip. Filename-keyed paths (keep_cards/banner.add) are unaffected; only content-classification has this hole.
- The NLO switch adds process-shape gates ON TOP of these three (QED/EW hide+'Not Avail'; decay ninitial==1 removes MA5) — see nlo-amcatnlo-ma5-interface. Those are availability gates too but keyed on process characteristics, not path/card.
