---
description: Survey driver — gensym.launch (gensym binary → channel list), submit_to_cluster job_strategy dispatch + splitted_grid parallelization, input_app.txt template / gridmode 2 vs -2. v3.7.1.
---

# Survey driver & job splitting — gensym (gen_ximprove.py, v3.7.1)

The layer that turns symmetry-reduced channels into running survey jobs, upstream of `combine_iteration`/`combine_grid` (those are on iteration-combination-and-results.md). File: `$MADGRAPH_INSTALL/madgraph/madevent/gen_ximprove.py`.

## gensym.__init__ (76) — splitted_grid / combining_job config
Sets the two parallelization knobs read everywhere below:
- `self.splitted_grid` (97): default `False`. **Loop-induced** (98-100): `max(2,(nexternal-2)**2)`, and if the survey accuracy is at its loose default it is tightened (102 — read the values there). On a `cluster.MultiCore` with splitted_grid>1 (104-107): reset to `int(nb_core**0.5)` (≥2 if >1 core). Run-card override: `survey_splitting != -1` sets it directly (110-111).
- `self.combining_job`: overridden by run_card `survey_nchannel_per_job` (if user_set, 112-113) else forced to a single channel when `hard_survey>1` (114-115). Base default comes from the class (`gensym.combining_job`, line 70 — read the survey channels-per-job default there).
- `splitted_for_dir = lambda x,y: self.splitted_grid` (119) and `combining_job_for_Pdir = lambda x: self.combining_job` (120) — per-Pdir hooks, rebound by `submit_to_cluster` under job_strategy.
- `min_iterations` (class attr, line 72): used as survey `miniter` (960) and the `step < min_iterations` resubmit gate (607).

## gensym.launch (326) — the survey driver
Per subprocess in `subproc.mg`:
1. clean prior `*ajob*`/`G*` (results.dat, ftn25) if `clean` (347-355).
2. compile + run the **`gensym` Fortran binary** (358-366). Its stdout is the **symmetry-reduced channel list**: `jobs = stdout.split()` (373) — each token is a channel job ID. (This is the "symmetry-aware channel grouping" — gensym, the Fortran, decides which integration channels survive after symmetry; Python just consumes the list.)
3. validates every token is float-parseable; if not, scans stdout line-by-line for the one valid numeric line (375-394), else raises "Parsing error in gensym".
4. on `error` file present → moves to `ajob.no_ps.log`, records Pdir in `P_zero_result`, skips (368-371).
5. compile `madevent`; if `to_submit`, `submit_to_cluster(job_list)` per Pdir.
Returns `(job_list, P_zero_result)`.

## resubmit (403) — recover/relaunch under-precise channels
Re-collects all channel results (`launch(to_submit=False, clean=False)`) and relaunches any channel that (a) has no `results.dat` or fails to read, (b) returned `xsec==0` (only if `resubmit_zero=True`), or (c) has `max(xerru,xerrc)/xsec > min_precision` (default read at its definition). Resubmittable G-dirs are `rmtree`'d then re-`submit_to_cluster`'d per Pdir. This is the entry for restart/recover-from-partial flows (the *driver* is launch-slice; this method is the in-slice channel-selection-by-precision logic).

## submit_to_cluster (447) — job_strategy dispatch + splitting mode
First, if run_card `job_strategy>0` (its default value normally skips this block; hidden run_card param, allowed [0,1,2], "appendix of 1507.00020 page 26"):
- reads `nexternal.inc`'s `PARAMETER (NEXTERNAL=...)` for this Pdir (457-458).
- **job_strategy==2** (460-470): force `splitted_grid=2`; split (`to_split=2`) only the **full-multiplicity** subprocess (`nexternal==int(ext)`), else `to_split=0`; rebinds `splitted_for_dir` to read per-Pdir `splitted_Pdir`.
- **job_strategy==1** (471-480): combine (`combine=1`) for the full-multiplicity subprocess, else `combine=self.combining_job`; rebinds `combining_job_for_Pdir`.
- (job_strategy>1 with multiple Pdirs recurses one Pdir at a time, 451-454.)

Then the mode dispatch (482-489) — fall back to **no-splitting** if: `not splitted_grid`, OR `cmd.cluster_mode==0` (single/serial), OR `cluster_mode==2 and options['nb_core']==1`. Else **splitted**. (`cluster_mode` is a `cmd` attribute owned by the launch/madevent_interface layer, not this slice — boundary at 484-489.)

## submit_to_cluster_no_splitting (492)
Old single-core path. Writes one `input_app.txt` per Pdir (`write_parameter(parralelization=False)`), then submits channels in batches of `combining_job_for_Pdir(Pdir)` via `survey.sh`, argument `['0', chan, chan, ...]` — **first arg is the offset** (`'0'`), rest are the batched channel IDs (506-513).

## submit_to_cluster_splitted (566)
Splitted-grid path. Per Pdir: if `splitted_for_dir<=1` fall back to no-splitting (576-577). Else `write_parameter(parralelization=True)` then, **per channel**, launch `splitted_for_dir(Pdir,job)` copies of `survey.sh` with argument `[i+1, job]` (the split index + channel), each registered in a `cluster.Packet((Pdir,job,1), self.combine_iteration, (Pdir,job,1))` (582-588). The Packet callback is what fires `combine_iteration` once all splits of a channel's iteration finish — that is the seam into the estimator layer.

## write_parameter / write_parameter_file (953 / 939) — input_app.txt
`write_parameter_file` template (942-947), one line each:
```
  <event>  <maxiter>  <miniter>   !Number of events and max and min iterations
  <accuracy>                      !Accuracy
  <gridmode>                      !Grid Adjustment 0=none, 2=adjust
  1                               !Suppress Amplitude 1=yes
  <helicity>                      !Helicity Sum/event 0=exact
  <channel>
```
`write_parameter` (953) survey defaults: `event=opts['points']`, `maxiter=opts['iterations']`, `miniter=min_iterations`, `helicity = run_card['nhel_survey'] else run_card['nhel']`, `gridmode=2`.
- **helicity==1 (MC-over-helicity)**: `event *= 2**(nexternal//3)` (968-969) — see mc-helicity-event-multipliers.md.
- **gridmode semantics** (944): `0`=no grid adjust, `2`=adjust (normal serial survey). `parralelization=True` (971-975) sets **`gridmode=-2`**, forces `maxiter=miniter=1` (dsample does the iteration automatically), and divides `event /= splitted_grid` (each split job does its share of points). So negative gridmode == "this is a single split job, write your grid separately for later combination."
- `create_resubmit_one_iter` (516) and the refine `input_app.txt` also use `gridmode=-2`, `maxiter=miniter=1`, `channel=G` (529-540).

## Cautions
- `job_strategy`'s default value leaves the whole 450-480 block dead in a default run; splitting is then governed purely by `splitted_grid` (loop-induced / MultiCore / `survey_splitting`). Don't assume job_strategy logic fires unless the run_card sets it.
- splitted_grid for loop-induced is `max(2,(nexternal-2)**2)` but gets *capped* to `int(nb_core**0.5)` on MultiCore — the effective number of split jobs is the smaller of the two, not the formula value.
- gridmode `-2` (parallelization) divides the per-job event budget by `splitted_grid`; total survey statistics is preserved across splits, but a single split's `input_app.txt` shows the divided count.
- gensym (the Fortran) owns channel symmetry reduction; Python's `launch` only parses its stdout. Channel *construction* (propagator mappings, ICONFIG) is phase-space slice — this page covers only the job-dispatch consumption of the channel list.
