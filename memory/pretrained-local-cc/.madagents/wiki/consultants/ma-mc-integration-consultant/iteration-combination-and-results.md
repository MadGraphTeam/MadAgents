---
description: Run/iteration combination — gen_ximprove combine_grid/combine_iteration 1/sigma^2 weighting + chi2 accumulator + instability-security discard; sum_html OneResult/Combine_results, results.dat fields. v3.7.1.
---

# Iteration / run combination + results tables (v3.7.1)

Files: `$MADGRAPH_INSTALL/madgraph/madevent/gen_ximprove.py`, `.../sum_html.py`, `.../combine_runs.py`.

## gensym.combine_grid (gen_ximprove.py:692)
Per-channel-iteration combination. Builds `combine_grid.grid_information(run_card['nhel'])`, reads each subjob's `results.dat` (`add_results_information`) + `grid_information` (`add_one_grid_information`). Subjobs with `axsec==0` set `onefail=True` and skip grid read (707-709).

- Gets `(cross, across, sigma)` from `grid_information.get_cross_section()` (720).
- **Instability security (722-783):** if not first survey step (or non-survey class), compute `rel_contrib = Gdir_across/Pdir_across`. If `rel_contrib>1e-8 and nunwgt<2 and >1 result`, compare the two largest per-subjob `th_maxwgt`. If `ratio>1e4` → discard the worst subjob, log a warning, store the max-weight event into `<Pdir>/DiscardedUnstableEvents/discarded_G<G>.dat`, increment `run_statistics['skipped_subchannel']`, and **recurse** `combine_grid(...,exclude_sub_jobs)` (783).

### Iteration accumulation (786-808) — the core estimator
When `sigma!=0`, accumulates over iterations into `self.cross/abscross/sigma/chi2` keyed `(Pdir,G)`:
- `cross[(Pdir,G)]   += cross**3 / sigma**2`
- `abscross[(Pdir,G)]+= across * cross**2 / sigma**2`
- `sigma[(Pdir,G)]   += cross**2 / sigma**2`
- `chi2[(Pdir,G)]    += cross**4 / sigma**2`
Then current estimate `cross = self.cross/self.sigma` (a 1/sigma^2-weighted mean of per-iter `cross`).
- `error` (step>1): `sqrt(|(chi2/cross^2 - sigma)/(step-1)| / sigma)` — combined relative error folding in chi2/dof spread (795-796). step==1: `error = sigma/cross`.
- If `sigma==0` (single nonzero point etc.): store raw cross, set sigma/chi2=0, error=0.
`get_current_axsec()` (854) = sum over all `(Pdir,G)` of `abscross/(sigma+1e-99)` = current total |xsec| estimate.

## combine_iteration (590) — survey iteration controller
Calls `combine_grid`, then decides `need_submit`:
- step < min_iterations (class attr, read at gen_ximprove.py:72) and cross!=0: step1 always resubmit; else resubmit unless `across/tot_across < 1e-6` or `error < accuracy/100`.
- step >= opts['iterations'] → stop.
- else: stop if `across==0`, `across/tot_across<1e-5`, or `error<=accuracy`; resubmit if `error>accuracy`.
On stop with cross>0: copies new grid `ftn25`→`G<G>/ftn26`, concatenates subjob `events.lhe`, writes `results.dat` via `write_results`.
`resubmit_survey` (898) doubles points per step: `event = 2**step * opts['points']/splitted_grid`; if helicity==1 extra `2**(nexternal//3)` factor (see mc-helicity-event-multipliers.md for all four sites).

## warnings_from_statistics (835) — EPS fraction
`EPS_fraction = exceptional_points/n_madloop_calls`. `0.001 < f < 0.01` → warning. `f > 0.01` → **critical + raise Exception** (loop processes only; n_madloop_calls==0 → no-op).

## sum_html.py — results tables
- `OneResult` (243): one channel/job. `read_results` (275) parses `results.dat` line1: `axsec xerru xerrc nevents nw maxit nunwgt luminosity wgt xsec [maxwgt [th_maxwgt th_nunwgt]]` (305-323). Following lines are per-iteration `l sec err eff maxwgt asec` → `ysec_iter`/`yerr_iter`/etc. `secure_float` (294) repairs fortran `1.23-105` (missing E) exponent format. XML tail parsed for run_statistics (357).
- `Combine_results(list, OneResult)` (419):
  - `compute_values` (440): xsec/axsec/xerrc **summed**; `xerru = sqrt(sum xerru^2)` (quadrature); nunwgt/nevents summed; `luminosity = min(0, per-channel lumis)`.
  - `compute_average` (459): **averages** xsec/axsec/xerrc over nbjobs; `xerru = sqrt(sum xerru^2)/nbjobs`; used by combine_runs multi-job combine. Consistency check (495-505): drops any job with `xsec < mean - 25*xerru` and recomputes with error=(max-min)/2.
  - `compute_iterations` (509): currently just collapses each result's iterations to one bin (`change_iterations_number(0)`); the per-iteration chi2 block is commented out.

## combine_runs.py (CombineRuns)
Combines multi-job channels (those with `multijob.dat`). `sum_multichannel` (85): reads njobs, adds each subjob `results.dat`, `compute_average`, writes combined `results.dat`, then re-reads each subjob `events.lhe` and re-unweights to common `maxwgt = axsec/nunwgt` (128) with per-job scale `ratio=job.nunwgt/total.nunwgt` (copy_events, 162). `get_channels` (213) reads `symfact.dat`; BW-coding digits `ncode = int(log10(3)*(maxparticles-3))+1`; integer xi → `G%i`, fractional (BW-coded) → `G%.{ncode}f` (228-236).
- **copy_events unweighting (162-211)**: per `<event>`, the line *after* `<event>` must have exactly 6 fields (else MadGraph5Error); weight is field index 2, scaled `new_wgt = wgt*scale_wgt`. **Sign is split off and preserved** (185-189) — `abs(new_wgt)` is compared against `random()*max_wgt`; below ⇒ event skipped (unweighted out). For a surviving event the written weight is **`max(max_wgt, |new_wgt|)`** (199) — i.e. sub-max weights are *raised up to* max_wgt, not truncated down (over-max survivors keep their value). `get_fortran_str` (154) reformats to `0.<mantissa>E+0NN` (mantissa/10, power+1) — the same /10 trick as `fstr` in write_results. So the combined `events.lhe` carries signed weights with a max_wgt floor.

## Cautions
- The chi2-based error (795) needs step>1; single-iteration channels report `sigma/cross`.
- `compute_values` sums `xerru` in quadrature but `xerrc` linearly (correlated). Don't conflate.
- Instability-security only fires when `len(results)>1` (i.e. splitted_grid>1) and not on first survey step. Single-job channels never get the discard.
