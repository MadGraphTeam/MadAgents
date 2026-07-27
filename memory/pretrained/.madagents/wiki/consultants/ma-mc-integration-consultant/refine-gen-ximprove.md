---
description: gen_ximprove refine logic — class dispatch (v4/share/gridpack/nogridupdate), gen_events_security + combining_job constants, find/get_job_for_event channel selection + splitting, get_job_for_precision. v3.7.1.
---

# Refine logic — gen_ximprove.py (v3.7.1)

File: `$MADGRAPH_INSTALL/madgraph/madevent/gen_ximprove.py` (2067 lines). Refine = take survey results and generate jobs to reach a target #events or precision.

## Class dispatch — gen_ximprove.__new__ (1006)
Picks a concrete subclass:
- `force_class=='gridpack'` → `gen_ximprove_gridpack`; `=='loop_induced'` → `gen_ximprove_share`.
- proc loop_induced → `gen_ximprove_share`.
- run_card `gridpack` truthy → `gen_ximprove_gridpack`.
- run_card `job_strategy==2` → `gen_ximprove_share`.
- else → `gen_ximprove_v4` (default LO path).

## Hardcoded constants — read them fresh per subclass (they drift; never cache the value)
Each subclass defines its OWN block of class-attribute constants — `gen_events_security`, `combining_job`, `max_request_event`, `max_event_in_iter`, `min_event_in_iter`, `max_splitting`, `min_iter`, `max_iter`, `keep_grid_for_refine`. **Read the assignments at the class's definition line; do not assume the base value carries down** — every subclass overrides some.

| class | where the constant block lives (read the assignments) |
|---|---|
| gen_ximprove (base) | class body ~990-991 |
| gen_ximprove_v4 | ~1173 |
| gen_ximprove_v4_nogridupdate | ~1524 (+ `increase_parralelization` ~1542) |
| gen_ximprove_share | ~1563 (also `nb_ps_by_job`, `mode="refine"`) |
| gen_ximprove_gridpack | ~1826-1833 |

`gen_events_security` (base 990): "multiply requested #events by this for security" (the over-generation multiplier). In `configure` (1105), when err_goal>=1 (event-count mode), `err_goal *= gen_events_security`. `combining_job` (991): "allow to run multiple channel in sequence" — number of channels batched into one ajob script.
- gridpack (1859-1862): `combining_job=0` if nprocs>1 else `sys.maxsize` (all channels one script).
- v4_nogridupdate: `__init__` (1533) calls `increase_parralelization(nexternal)` **only if** `proc_characteristics['loopinduced'] and nexternal>2` (1537-1539). That method (1542) resets `max_splitting` to the loop-induced value (1545; the class-attr is the non-loop-induced value), then — gated on `run_card['refine_evt_by_job']==-1` — reduces `max_request_event` in tiers by nexternal, and at high nexternal also lowers `min_event_in_iter` and `max_iter` (1547-1556; read the tier values there). So the reductions are loop-induced-parallelization tiers, NOT accuracy branches; a non-loop-induced nogridupdate run keeps the class-attr values.

`gensym.combining_job` (class attr, line 70) — the **survey** default number of channels batched per job; overridden by run_card `survey_nchannel_per_job` or forced to a single channel if `hard_survey>1` (112-115).

## v4.increase_precision (1209)
Auto-tightens for high-accuracy refine (called when opts['accuracy'] < survey default). Sets `max_event_in_iter` and `gen_events_security` (rate<3 → sets a high `max_event_in_iter` / `self.min_events` / `gen_events_security`, 1212-1214; else rate-scaled, 1217-1219 — read the values there). **NB the `min_events` it sets is a DIFFERENT attribute from `min_event_in_iter`** — `min_event_in_iter` is left at its class default in this method and is touched only by the nhel==1 helicity multiplier below. nhel==1 → `min_event_in_iter *= 2**(nexternal//3)`, `max_event_in_iter *= 2**(nexternal//2)` (1221-1223, see mc-helicity-event-multipliers.md).

## find_job_for_event (1112) — channel selection (event mode)
`goal_lum = err_goal/axsec` (pb^-1). For each channel sorted by luminosity desc: select if `goal_lum/C.luminosity >= 1 + (gen_events_security-1)/2` (channel under-produces), OR if `xerr > max(axsec, axsec_smallest/(100*sqrt(err_goal)))`.

## get_job_for_event (v4, 1228) — build jobs
1. `needed_event = goal_lum*axsec`; `nb_split = ((needed_event-1)//max_request_event)+1` (capped at max_splitting; forced 1 if `not split_channels`).
2. per-iter events `nevents = needed_event/nb_split * (nevents/nunwgt) / (2**min_iter -1)`; clamped to [min_event_in_iter, max_event_in_iter]; if too low, raise nb_split.
3. `write_multijob` (multijob.dat) if nb_split>1; builds info dict per job (offset/directory letter-suffixed a0,b0,...), `precision = -goal_lum/nb_split` (negative ⇒ event-count target). Packet → `combine_runs.CombineRuns`.
- **combining_job reordering** (1242-1262): if >1, interleaves to_refine (big+small) for cluster load balance.

## create_ajob (1335) — combining_job batching
Splits jobs by P_dir (no mixed-subprocess submission, 1344-1351). If `combining_job>1`: writes `nb_sub = n_channels//combining_job` scripts (`ajob1`, `ajob2`,...), each templating `combining_job` job dicts into `refine.sh`. Edge-case: if last batch underfull, `skip1` scripts get one fewer; if `skip1>nb_sub`, decrement combining_job and recurse (1371-1373).

## get_job_for_precision (1405) — precision mode
Selects channels whose `cerr = mfactor*(xerru + Nchan*xerrc)` exceeds a per-channel limit; refines limit via quadrature of unselected error. `nevents = 0.2*C.nevents*(yerr/limit)**2`; `nb_split = (...)**(2/3)` ("slow down job-count growth"). `precision = yerr/sqrt(nb_split)/(xsec+yerr)` (positive ⇒ precision target). NB BUG-LOOKING line 1457: `nevents = min(min_event_in_iter, max(max_event_in_iter, nevents))` — min/max appear swapped vs event-mode clamp (1290).

## share variant (loop-induced, 1558)
Refines in multicore, distributing PS points across jobs (`nb_ps_by_job`, default + floor read at the share class def ~1563).

### share `combine_iteration` (1648) — accumulating refine controller (distinct from survey `combine_iteration` at 590)
After `combine_grid`, decides whether enough unweighted events exist, accumulating across iterations rather than re-running from scratch:
1. `needed_event = cross*goal_lum`; if `err_goal>=1` capped at `int(gen_events_security*err_goal)` (1666-1668).
2. **Old-event carry-over with re-unweighting** (1670-1687): prior `(nunwgt,maxwgt)` from `self.generated_events[(Pdir,G)]`; on a *second* refine with an existing `G<G>/events.lhe` and no recorded count, re-derives via `lhe.unweight(None,trunc_error=0.005)`. New common `maxwgt = max(grid.get_max_wgt(), old_maxwgt)`; old events rescaled `nunwgt = old_nunwgt*old_maxwgt/maxwgt` then `+= new_evt` (raising maxwgt *shrinks* the surviving old count). `efficiency = new_evt / sum(R.nevents)`.
3. **Drop-previous-iteration decision** (1689-1702): compares PS points the last iteration *alone* would need (`n_target_one_iter`) vs the *combined* accumulation (`n_target_combined = (needed_event-nunwgt)/efficiency`). If one-iter < combined (because carrying old events at a worse maxwgt is inefficient), set `drop_previous_iteration=True`, restart `events.lhe` from scratch (`'w'` not `'a'`, 1704-1709), keep only this iteration's count/eff.
4. Concatenate split `Gdirs/events.lhe` via `cat` (1711). **Real-unweight recheck** (1716-1719): if `nunwgt < 0.6*needed_event and step>min_iter`, do a true `lhe.unweight(trunc_error=0.01)` to replace the estimate.
5. **Stop test** (1726): `nunwgt >= int(0.96*needed_event)+1` (the stop factor at 1726). Source comment "0.96*1.15=1.10 =real security" — `needed_event` already carries the share `gen_events_security`, so the stop factor nets an effective over-generation just above 1 (read the share security at its class def). Also stops at `step>=max_iter`. On stop calls `write_results(...,efficiency)` (the share `write_results` at 1788 takes the extra `efficiency` arg).
6. Else resubmit: `need_job` from `(needed_event-nunwgt)/efficiency // nevents`; before min_iter clamped to `expected_remaining_job*1.25` (1744-1759), after min_iter clamped to `nb_split_before*1.5`, with a `1.20×` bump on the iteration before max_iter (1768-1769). Resubmits via `create_resubmit_one_iter` + `write_grid_for_submission` (conservative_factor=max_iter is the dead param, see combine-grid-vegas.md).

## gridpack variant (1826)
`find_job_for_event` (1864) is **stochastic**: per channel `R=random.random()`, skip if `goal_lum*axsec < R*ngran`; sets `gscalefact`. `check_events` (2015) re-reads each G results.dat, resubmits (recursively) channels with `nunwgt < requested_event`, concatenating new events to `.previous`. Class constants (read at ~1826-1833) set a single min-iter and no over-generation (`gen_events_security`).

## Cautions
- `gen_events_security` differs per class (gridpack has none; high-precision refine raises it) — read the chosen subclass. Over-generation factor is class-dependent, not global.
- precision-mode clamp (1457) min/max ordering looks inverted vs event-mode — flag if a precision refine produces odd nevents.
- gridpack channel selection is RNG-driven; #channels refined varies run-to-run.
