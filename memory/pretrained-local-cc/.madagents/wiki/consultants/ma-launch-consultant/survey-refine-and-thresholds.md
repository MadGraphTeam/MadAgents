---
description: do_survey and do_refine internals — gensym/gen_ximprove launch, difficult-integration-mode trigger (mmjj / hard_survey), the second-refine threshold bypass via prev_cross, run.inc rewrite.
---

# Survey, refine, and integration thresholds

Cites: `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (v3.7.1).

## do_survey (3484-3572)
- `check_survey(args)`; removes stale `error` file; `configure_directory()` (compiles + writes run.inc, see treatcards page); saves `random_orig`, updates/saves random seed; `update_status('Running Survey')`.
- Reads `SubProcesses/subproc.mg` for the P-dir list (3508).
- Loop-induced: tars `MadLoop5_resources` if `need_transfer` (3514-3520).
- `ajobcreator = gen_ximprove.gensym(self)` (3523) — the job creator (phase-space/mc-integration slice owns gensym internals).
- **Difficult-integration trigger** (3526-3529):
  - if `mmjj > 0.01*(ebeam1+ebeam2)` -> `pass_in_difficult_integration_mode()` (rate=1).
  - elif `run_card['hard_survey']` truthy -> `pass_in_difficult_integration_mode(hard_survey)`.
- Helicity recycling: `get_helicity()` if `proc_characteristics['hel_recycling']` and `run_card['hel_recycling']` (3531-3532); else copies `matrix*_orig.f` -> `_optim` and clears `Hel/selection` (3534-3545). Helicity-recycling internals are mc-integration slice.
- `jobs, P_zero_result = ajobcreator.launch()` (3547).
- Zero-PS handling (3549-3559): if ALL subprocs have no phase space -> `ZeroResult` from `ajob.no_ps.log`; if only some -> warning listing them.
- `monitor(run_type='All jobs submitted for survey', html=True)` (3561).
- HTML/print only on first survey (or ninitial==1 or gridpack) (3562-3569); otherwise xsec is computed during refine.

## pass_in_difficult_integration_mode (3575-3601)
- If survey opts are still at defaults, scales them up: points -> `(rate+2)*1000`, iterations -> `1+rate+5`, accuracy -> `0.1/(rate+2)` (3579-3584). The baseline `_survey_options` defaults are registered at line 2053 (points/iterations/accuracy) — read them fresh there.
- Rewrites `Source/run_config.inc`: `min_events = 2500*(2+rate)`, `max_events = 10000*(rate+1)` (3591-3596), backs up to `.bk`, then recompiles `gen_ximprove` and `all` (3600-3601).

## do_refine (3605-3741)
- `self.nb_refine += 1` (3608).
- **Second-refine threshold bypass** (3614-3624): if a `--treshold=T` arg is present, compares `prev_cross` (old survey xsec) vs `cross` (current). If `old_xsec > new_xsec * T` -> "No need for second refine due to stability of cross-section" and returns WITHOUT refining. Default T = `run_card['second_refine_treshold']` (hidden param registered banner.py:4448 — read the value there). Else strips the arg and proceeds.
  - `prev_cross` is set by `AllResults.add_detail` (gen_crossxhtml.py:367-369): whenever `cross` is written and the prior value was nonzero, the prior is saved into `prev_cross`. So the threshold test compares the survey estimate against the first-refine estimate.
- `refine_opt = {'err_goal': args[0], 'split_channels': True}`; optional `max_process` (3628-3631).
- `configure_directory()`, update random, clean old ajob/wait/run/done files (3634-3654).
- `x_improve = gen_ximprove.gen_ximprove(self, refine_opt)` (3656); loads survey run_statistics (3657-3674); `x_improve.launch()` (3676).
- For `gen_ximprove_v4` (old/non-split): writes ajob files, compiles `madevent`, removes per-G `results.dat`, launches each ajob via `launch_job` (3682-3711). Split mode handles cluster submission internally.
- `monitor(...html=True)` (3714); for v4 merges via `combine_runs.CombineRuns(self.me_dir)` and sets `refine_mode='old'`, else `'new'` (3723-3729).
- `make_make_all_html_results(get_attr=('xsec','xerru','axsec'))` -> updates cross/error/axsec details (3731-3735).

## Cautions
- `mmjj > 0.01*(ebeam1+ebeam2)` silently boosts survey effort; a large mmjj cut therefore changes integration cost without user opt-in.
- Second refine is SKIPPED when the survey-to-refine ratio is stable (threshold = `second_refine_treshold`, banner.py:4448) — the final statistics may come from a single refine. A user expecting two refines may get one.
- The difficult-mode opt scaling only fires if the survey opts are still at their exact defaults; passing any custom `--points/--iterations/--accuracy` disables the auto-boost.
