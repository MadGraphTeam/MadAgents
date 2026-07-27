---
description: The aMCatNLOCmd accuracy-adaptive integration driver beneath run() — create_jobs_to_run / update_jobs_to_run / collect_the_results MINT + fixed-order refinement loop, job splitting, random event distribution, cluster/multicore dispatch, check_event_files LHE-integrity resubmit, update_random_seed.
---

# The integration driver — MINT / fixed-order refinement loop beneath `run()`

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`. [[runtime-shell-commands]] describes `run()` (1923) at high level and names these workers abstractly; this page documents the accuracy-adaptive job loop they implement. The FKS/MadLoop matrix-element code being integrated is the **fks**/**madloop** slices; this page owns the orchestration: how many jobs, how many points/iterations, when to stop, how to split, how events are distributed.

## The two loop shapes (`run()`)
- **Fixed order (LO/NLO)** (1951-1979): `req_acc = run_card['req_acc_FO']`; `create_jobs_to_run` → `prepare_directories` → `while True:` step loop — each pass `run_all_jobs` → `collect_log_files` → `collect_the_results`; breaks when `collect_the_results` returns empty `jobs_to_run`. Then `finalise_run_FO`. No fixed step count: refinement continues until accuracy met.
- **Event modes (aMC@NLO/aMC@LO/noshower/noshowerLO)** (1981-2060): exactly **3 MINT steps** `['Setting up grids','Computing upper envelope','Generating events']` (1943, `for mint_step,status in enumerate(...)` 2032). `mint_step==2 and nevents==0` → print summary and return (grids only). After the 3 steps: `check_event_files` → (`reweight_and_collect_events`).

## `create_jobs_to_run` (2094) — building the job list
Each job is a dict. Reads `P*/channels.txt` (written by the `gensym` executable; missing → "No integration channels found ... too large masses/low energy?" warn-and-skip the contribution, 2108-2110).
- **Fixed order** (2111-2142): channels combined up to `maxchannels` per job (literal at 2113 — read it); per job sets `nchans`, `configs` (the channel id list). Initial points/iters: `req_acc==-1` → `npoints_FO_grid`/`niters_FO_grid` defaults with `accuracy=0`; `req_acc>0` → hardcoded initial `accuracy`/`niters` with `npoints=-1` (read the literals at 2111-2142); else `aMCatNLOError('No consistent "req_acc_FO" set')`.
- **Event mode** (2143-2156): ONE job per channel; `accuracy=0.03, niters=12, npoints=-1`.
- `only_generation=True` (2158-2180): does NOT rebuild — unpickles `SubProcesses/job_status.pkl` (raises if unreadable), rebases dirnames, then either `collect_the_results` (FO) or `append_the_results` (event) to restore state and skip to the next needed step.

## `update_jobs_to_run` (2654) — the accuracy decision (loop termination)
Returns the jobs that still need running; empty return ⇒ loop stops.
- **Fixed order, `req_acc==-1`** (2667-2680): step 0 only does grids; step 1 runs `npoints_FO`/`niters_FO` (read their defaults in the NLO run_card); step ≥2 raises. So `req_acc=-1` is a **fixed 2-pass** (grid + one integration), not adaptive.
- **Fixed order, `req_acc>0`** (2681-2710): continues only while `err/|tot| > req_acc * slack`, where the slack multiplier `>1` is a literal at 2681-2710 (read it) — the loop stops somewhat beyond the requested target. Per-job target accuracy `= req_accABS*sqrt(totABS/job_resultABS)` — channels with larger |xsec| get tighter accuracy. Jobs already accurate enough are skipped (2691). Next-pass `npoints`/`niters` estimated from `niters_done*(errorABS/(accuracy*resultABS))^2` times a headroom factor, with `itmax` capped (2704). Zero-xsec jobs skipped.
- **Event modes, step+1≤2** (2711-2746): per-job upper-envelope accuracy `= min(sqrt(totABS/(req_acc2_inv*resultABS)),0.2)` where `req_acc2_inv = nevents` (if req_acc<0) else `1/req_acc²`. At **step+1==2 the events are distributed across jobs** by a random draw proportional to |ABS xsec|: `target=random.random()*totABS`, walk the cumulative `resultABS` sum, increment that job's `nevents`, repeat `nevents` times (2733-2743). So per-channel event counts are stochastic, seeded from `randinit` via `get_randinit_seed` (2726, set once with `random.mg_seedset` guard).

## `collect_the_results` (2302) — per-step bookkeeping
`append_the_results` reads each job's `res_<step>.dat` (or `res.dat` for FO only_generation, step<0) → `resultABS/errorABS/result/error/niters_done/npoints_done/time_spend` (2759-2794; missing file → collects log paths and raises `aMCatNLOError`). `write_res_txt_file` → `self.cross_sect_dict`. Updates HTML (`make_make_all_html_results`), `results.add_detail('cross'/'error')`. FO: combines split jobs (`combine_split_order_run`), pickles `job_status.pkl` (restart point) + `job_status2.pkl` (debug). Calls `update_jobs_to_run`; if empty & FO → final summary; else intermediate summary (event modes defer summary to after reweight/collect).

## Job splitting (parallelism)
- **`split_jobs_fixed_order` (2547)** — splits long FO jobs by expected wall-time. `nb_submit` = nb_core (multicore) / cluster_size (cluster) / 1 (serial). Estimates `time_expected` per job from `time_spend*(niters*npoints)/(niters_done*npoints_done)`; splits when a job's expected time exceeds `max(2*time_spend/combined, time_per_job)` OR `npoints >= __maxint__`. `nsplit` capped at `nb_submit`; split jobs get `wgt_mult=1/nsplit` and divided npoints. Only invoked when `req_acc_FO>0` (2360).
- **`check_the_need_to_split` (2612)** — splits the EVENT-generation step by `nevt_job` (run_card; the default sentinel means no split — read it). When `nevt_job>0`: a job needing `>nevt_job` events is split into `ceil(nevents/nevt_job)` sub-jobs, each carrying `wgt_frac` = its share; jobs needing 0 events are dropped. When `nevt_job<=0`: just drops the 0-event jobs.
- **`__maxint__ = 2**31 - 1`** (line 58) — the Fortran INT4 ceiling; the split logic forces extra splits to keep per-job `npoints` under it, and raises `aMCatNLOError('Too many point... Fortran will likely crash for integer overflow')` if a split still exceeds it (2600).

## Cluster / multicore dispatch
- **`setup_cluster_or_multicore` (3198)** — `cluster_mode==1`: instantiate `cluster.from_name[cluster_type]` (or a plugin `new_cluster`). `cluster_mode==2`: `cluster.MultiCore`; `nb_core` from `options['nb_core']` or `multiprocessing.cpu_count()`; ImportError → 1 core + warning.
- **`run_exe` (5020)** — the per-job launcher. Serial (`cluster_mode==0`): `misc.call(['./'+exe]+args)`. Cluster/multicore: branches on exe name — `reweight`/`ajob`/`shower` each assemble their own `input_files`/`output_files`/`required_output` and `cluster.submit2`. `ajob` is the standard amcatnlo integration job (5070). Missing exe → `aMCatNLOError('Cannot find executable')`.
- **`run_all_jobs` (2272)** — loops jobs, executable always `ajob1` (2287), args `[channel, run_mode|name_suffix, split, integration_step]`; multicore sleeps 1s for launch safety; then `wait_for_complete`.
- **`run_all` (4976)** / **`wait_for_complete` (4964)** — generic submit + `self.cluster.wait(me_dir, update_status)`; on any exception `cluster.remove()` then re-raise. `run_type=='shower'` path submits a single exe (4987-4991).

## `check_event_files` (4998) — LHE-integrity resubmit
After the 3 MINT steps, `tail -n1 events.lhe` per job; if the last line `!= "</LesHouchesEvents>"` the job is **resubmitted** (`run_all_jobs(...,2,fixed_order=False)`). So a truncated/crashed event file is silently re-run, not failed. cluster_mode==1 then `time.sleep(10)` to let files transfer back (2047-2052).

## `update_random_seed` (1906) — the iseed reset
`iseed = run_card['iseed']`. **`iseed==0` → reads `SubProcesses/randinit`, increments by 1** (so successive auto runs advance the seed). **A NON-zero `iseed` is USED then `reset_iseed_in_run_card()` resets the run_card iseed to 0** (defined in `common_run_interface.py:4931`) — "to ensure subsequent runs will be statistically independent." Either way `randinit` is rewritten `r=<iseed>`. NON-OBVIOUS: setting a fixed seed in the run_card is a ONE-SHOT — it is wiped to 0 after the run, so re-launching does NOT reproduce the same seed unless you re-set it each time.

## Relevant run_card integration params (RunCardNLO default_setup, banner.py ~5615-5626 — read each default fresh at its line)
Inventory (numeric defaults drift — read at their `add_param` lines; the include/split semantics below are stable): `nevents`; `req_acc` (event-mode, include=False); `req_acc_fo` (FO, include=False); `nevt_job` (event-split; the sentinel default means split-off, include=False); `npoints_fo_grid`, `niters_fo_grid`, `npoints_fo`, `niters_fo` (all include=False); `iseed` (default `0` = auto-seed from `randinit`, a load-bearing sentinel — see `update_random_seed` above).

## Cautions
- The FO loop binds `req_acc = run_card['req_acc_FO']` (run():1955), NOT `req_acc`. `req_acc_fo`'s default is POSITIVE (banner.py:5621, read it) — so a DEFAULT fixed-order run takes the *adaptive* refinement path (req_acc>0 branch, with job-splitting), converging to that relative accuracy. Setting `req_acc_FO = -1` switches it to a **fixed 2-pass** (grid + one run at npoints_FO/niters_FO defaults), NOT adaptive: a user picking -1 gets a fixed point budget, not convergence to a target. (-1 is NOT the FO default: the NEGATIVE default belongs to the *event-mode* `req_acc` (banner.py:5616), a different param — read each param's own default at its own line.)
- The FO stop condition applies a slack factor `>1` (`err/|tot| > req_acc*slack`, literal at 2681-2710): the achieved accuracy can be somewhat looser than the requested `req_acc_FO`.
- Per-channel event counts are **stochastic** (random draw proportional to |ABS xsec|), seeded from `randinit`. Two runs with the same seed reproduce the split; different seeds do not.
- A fixed `iseed` in the run_card is consumed and reset to 0 (1917) — reproducibility across re-launches requires re-setting it each time.
- `check_event_files` silently resubmits jobs whose `events.lhe` doesn't end in `</LesHouchesEvents>` — a broken event file is re-run, masking transient failures.
- (Runtime predictions — exact job counts, which channels split, the achieved accuracy — are source-read, not probe-verified end-to-end; needs a completed NLO run to confirm the loop behavior.)
