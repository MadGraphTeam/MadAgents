---
description: Run-time HTML cross-section pages (gen_crossxhtml AllResults/RunResults/OneTagResults, sum_html.make_all_html_results) and BIAS module scaffolding (dummy/ptj_bias, impact_xsec/requires_full_event_info). v3.7.1.
---

# HTML cross-section pages + BIAS scaffolding (v3.7.1)

## gen_crossxhtml.py — persistent results DB + HTML
File: `$MADGRAPH_INSTALL/madgraph/madevent/gen_crossxhtml.py` (1664 lines). The run-result database that backs `HTML/<run>/results.html` and the crossx.html index.
- `AllResults(dict)` (128): top container for all runs of a process dir. `_run_entries` (133) = the per-run fields tracked (cross, error, axsec, nb_event, pythia/pythia8 cross/error, run_mode, run_statistics, shower_dir). On init, re-adds existing runs from `Events/` (readd_old_run, 166, reading `unweighted_events.lhe`). `AllResultsNLO` (502) is the NLO subclass.
- `RunResults(list)` (509): all tags of one run; `get_html` (547).
- `OneTagResults(dict)` (739): one tag within a run; `get_html` (1349).
Distinct from `sum_html.py` which holds the per-channel numeric `OneResult`/`Combine_results`. gen_crossxhtml is the *run-level* presentation/DB layer; sum_html is the *channel-level* numeric layer.

## sum_html.make_all_html_results
`collect_result(cmd, main_dir=...)` (used by gen_ximprove.launch, gen_ximprove.py:1076) walks SubProcesses, builds `Combine_results` per P-dir, sums to a total. `update_html` (gen_ximprove.py:1138/1487) writes `HTML/<run>/results.html` (header from `sum_html.results_header`) and `SubProcesses/results.dat`, and pushes `cross`/`error` into `cmd.results`.

## BIAS scaffolding — Template/LO/Source/BIAS/
Full treatment: see `biased-event-generation.md`. Summary: `bias_module` MULTIPLIES the integrand by `bias_weight` (auto_dsig_v4.inc:166), then MG divides it back out at LHE write/parse (XWGTUP de-biased, lhe_parser.py:3391-3401). Two shipped modules: `dummy/dummy.f` (returns 1.0, `impact_xsec=.True.`), `ptj_bias/ptj_bias.f` (`(max_ptj/target)^power`, `impact_xsec=.False.`).
- `impact_xsec` does NOT mean "is σ unbiased" — it flags whether the per-event bias weight is WRITTEN to the LHE (`.True.`=don't write, assumed dummy bias≡1; `.False.`=write so it can be de-biased). Consumer alias `is_bias_dummy` (reweight.f:1306); auto-forced `.false.` when any bias≠1 (madevent_combine_events.f:172).

## Cautions
- Biased generation → WEIGHTED output events (de-biased weight ∝ 1/bias varies). Distinct from `flavour_bias`/`event_norm='bias'` (banner.py:5708-5945).
- gen_crossxhtml rebuilds its DB from `Events/` LHE files if the pickled DB is gone — stale/renamed event files can repopulate the HTML with old runs.
