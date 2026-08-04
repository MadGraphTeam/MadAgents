---
description: Launch-time silent overrides — MadGraph mutates run_card values and integration effort at launch, gated on process characteristics or card conditions, independent of (sometimes overriding) what the user set. Lens for "why did my run_card setting not take effect at runtime".
---

# Launch-time run_card / effort overrides (the override-without-opt-in lens)

Cross-cutting principle over the LO launch path. At several points between `do_generate_events` and the first integration, MadGraph **silently changes run_card values or integration effort** based on process characteristics or card conditions — without user opt-in, and sometimes overriding an explicit user setting. When a user asks "I set X in the run_card but the run behaved differently / didn't use my value", the answer is usually one of these.

All cites `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (v3.7.1) unless noted.

## The catalogue (gate -> mutation)
| Gate condition | What is mutated | Cite |
|---|---|---|
| `loop_induced and run_mode==0` | forces `run_mode 2`, `nb_core 1` (warns) | 2567-2574 |
| `run_card['gridpack']` truthy | survey opts taken from a hardcoded `gridpack_opts` list (accuracy/points/iterations/gridpack=.true., literals at 2578-2581 — read fresh), overriding `_survey_options`; refine skipped | 2576-2592 |
| `mmjj > 0.01*(ebeam1+ebeam2)` | difficult-integration boost: points/iter up, accuracy down, run_config.inc min/max_events rewritten | 3526-3527, pass_in_difficult_integration_mode 3575-3601 |
| `run_card['hard_survey']` truthy | same difficult-integration boost at rate=hard_survey | 3528-3529 |
| `--treshold` present & `prev_cross > cross*T` (T=second_refine_treshold, default registered banner.py:4448 — read fresh) | second refine SKIPPED | 3614-3624 |
| `ninitial == 1` (decay/width) | `lpp1/lpp2/ebeam1/ebeam2` all zeroed in run mode (beam settings ignored) | 3276-3280 |
| `bias_module not in dummy/none` | `run_card['bias_parameters']` rebuilt from the module's declared C-comment defaults; user keys merged only where recognized, **unrecognized keys discarded** ("X not supported by the bias module. We discard this entry.") | do_treatcards 3300-3341 |
| `nevents > 1000000` | `check_nb_events` perl-rewrites the card to `1000000 = nevents`, warns "Limiting number to 1M. Use multi_run for larger statistics." | 6471-6483 |
| `configured >= card mtime` | configure_directory early-out: treatcards/compile NOT re-run; edits that don't bump run_card.dat/param_card.dat mtime are ignored | 6068-6072 |

## Why these are one principle (not eight notes)
They share the same failure shape: a launch-time decision overrides or bypasses a configured value, with at most a log line and no card-level record (except check_nb_events, which does rewrite the card). The lens catches:
- **Future overrides** added to the survey/refine/treatcards/configure path under the same "gated on process/card condition" pattern — the catalogue is the current set, not the closed set.
- The **user-facing question class** "why did my run_card setting not take effect at runtime" — answered holistically here, not in any single flow-stage page.

## Boundary (what this lens is NOT)
- NOT phase-space channel/propagator choices (phase-space slice).
- NOT VEGAS / numerical / helicity-recycling internals (mc-integration slice).
- NOT card *content validation* or per-parameter defaults (per-card slices) — this is runtime *mutation* of already-validated values.
- The mechanism details of each instance live in the flow / survey-refine / treatcards pages; this page is the index + the principle.
- A SIBLING override family exists with a different trigger: the launch-**menu** consistency rules (AskRun `consistency_*`, launch-menu-switcher page) silently flip one *switch* (shower/detector/analysis) when another is set — e.g. Pythia8+PGS forces detector OFF, Rivet forces shower Pythia8. Same "override-without-opt-in" shape, but the gate is the menu combination, not a run_card/process characteristic, so it lives on the launch-menu-switcher page, not in this catalogue.

## Probe note
`check_nb_events` 1M cap is runtime-probe-verified: setting `nevents=2000000` and launching a forced `generate_events` rewrote the run_card to `1000000 = nevents` during `configure_directory` (before integration) and emitted the "Limiting number to 1M" warning exactly once. The other rows are source-walked, not individually probed — treat their runtime text/behavior (incl. the bias_parameters discard warning) as source-grounded but unprobed.
