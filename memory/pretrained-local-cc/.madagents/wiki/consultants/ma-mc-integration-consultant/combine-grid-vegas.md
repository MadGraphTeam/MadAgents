---
description: combine_grid.py — VEGAS grid combination, cross-section/error estimator, DiscreteSampler/Bin_Entry format, secondary-unweighting max-wgt, new-grid rebinning. v3.7.1.
---

# combine_grid.py — VEGAS grid + xsec estimator (v3.7.1)

File: `$MADGRAPH_INSTALL/madgraph/madevent/combine_grid.py` (806 lines).

## grid_information (line 19)
Accumulates per-subjob `grid_information` files into one combined grid + xsec/err.
- `add_one_grid_information(path)` (56): reads a subjob `grid_information` file. First line `nonzero ng maxinvar`; then `grid_base` (summed), `original_grid` (overwritten, not summed — last wins, line 101), `non_zero_grid` (summed int), `min_on_axis`/`max_on_axis` (min/max reduce), then cumulative line (124-133): `sum_wgt += data[0]`, `sum_abs_wgt += data[1]`, `sum_wgt_square += data[2]`, `max_wgt = max(...,data[3])`, `nb_ps_point += data[4]`, `target_evt` asserted-equal-across-subjobs (130), `force_max_wgt.append(data[6])`.
- Empty/malformed first line → `nb_ps_point += 500000`, `oneFail=True`, return (72-81). NB typo: line 73 sets `self.onefail` (lowercase) but line 80 sets `self.oneFail`; `get_cross_section` reads `self.oneFail` (377). The first-info branch's `self.onefail` is a dead attribute.
- `convert_to_number` (53): replaces fortran `d` exponent with `e`.

## get_cross_section (372)
Returns `(mean, rmean, sqrt|sigma|)`.
- `mean = sum_wgt*target_evt/nb_ps_point`; `rmean = sum_abs_wgt*target_evt/nb_ps_point` (382-383).
- `vol = 1/target_evt`; `sigma = sum_wgt_square/vol**2 - nonzero*mean**2`, then `/= nb_ps_point*(nb_ps_point-1)` (385-388). Standard MC variance of the mean.
- Returns `0,0,0` if `nb_ps_point==0 or nonzero==0` (375). If `oneFail` and `nonzero < 10*len(results)` → declare failure `0,0,0` (377-380).

## get_max_wgt(trunc_max=...) (248)
Force-max-weight for **secondary unweighting**: the weight allowing a `trunc_max` fraction of events above 1 (the default is the arg default at 248 — read it there). Uses per-result `th_maxwgt`/`th_nunwgt`, sorts desc, accumulates until `xsum - X*nb_event` crosses `trunc_max*total_sum`, then solves linearly for exact-trunc weight (283). In `write_associate_grid` it is called with a looser trunc value (line 221) than the 248 default.

## get_nunwgt(max_wgt) (293)
Estimates #unweighted events for a given max weight by interpolating each result between its `(maxwgt,nunwgt)` and `(th_maxwgt,th_nunwgt)` points (solves `a+b/x=N`). Capped at written `nunwgt`.

## write_grid_for_submission (163) — wrapper that places + links ftn25
Thin wrapper called by `combine_iteration` (gen_ximprove.py:641) and the refine paths. Builds the list of split dirs `G<G>_<i>` (i in range n_split), creates `G<G>/`, writes `G<G>/ftn25` via `write_associate_grid(...,conservative_factor,mode)` (176-177), and **only in survey mode** symlinks that ftn25 into every split dir (180-182; "in refine the link is made by the job"). So the survey grid is computed once per channel and shared (by symlink) across its split jobs.
- **`conservative_factor` is a DEAD parameter** (caution below): it is declared at 164 and passed through to `write_associate_grid` at 177, but `write_associate_grid`'s body never reads it. `combine_iteration` passes `conservative_factor=5.0` (gen_ximprove.py:644) — no effect.

## write_associate_grid (184) — the ftn25/ftn26 grid file
- Bails if `nb_ps_point==0` (PS returned 0).
- Writes new grid (4 floats/line, `%+.16f`), then `twgt force_max_wgt` line where `twgt = mean/8.0/nb_event` (219; the `/8.0` is "be more conservative re max iterations"), `force_max_wgt = get_max_wgt(...)` with the looser trunc value (see get_max_wgt above, called at 221).
- If `not mc_hel`: writes the helicity_line read in add_one_grid_information (138-139, 225-226).
- **Mode-dependent discrete-grid params** (231-242): the survey / refine / else branches each stamp a different `(small_contrib_threshold, damping_power)` pair onto every dimension just before write — read the three branches at 231-242.

## get_new_grid_for_var (409) — VEGAS rebinning
1. Bias toward zero regions: `factor=min(10000, nonzero/non_zero_grid[(i,var)])`, `grid=grid_base*factor` (414-417).
2. 3-point moving average (421-434).
3. Log transform `((x0-1)/log(x0))**1.5` to speed rebinning convergence (438-443).
4. Endpoint handling for first/last bin vs `min_on_axis`/`max_on_axis` (450-464).
5. Equal-mass rebinning: cumulative target `avg = sum_var/(stop-start+1)` (467-489).
6. Minimal 1e-14 spacing enforced; sanity pass from top if a node exceeds xmax (491-504).

## DiscreteSampler (510) / DiscreteSamplerDimension (642) / Bin_Entry (757)
- `DiscreteSampler(dict)`: maps tag `(name, grid_type)` → dimension. `read(mode='init'|'add')`. In `add` mode, grids with `grid_type==1 and grid_mode==1` (reference, default mode) are skipped (not summed) since "they should all be the same" (561-564); other tags `+=`.
- File block delimited by `<DiscreteSampler_grid>`...`</DiscreteSampler_grid>`. Field order (get_grid_from_file, 567): name, grid_type (1=ref,2=run), min_bin_probing_points, grid_mode (1=default,2=initialization), small_contrib_threshold, damping_power, then bin lines `binID n_entries weight weight_sqr abs_weight`.
- **PROBE-CONFIRMED (parse+write round-trip, v3.7.1):** dict key tag preserves original-case `name` ("Helicity") even though `read` lowercases lines only to find the marker; `get_grid_from_file` reads name from the raw line. Bin IDs kept as **strings** (`'1'`,`'4'`). On write, bins re-sorted by `weight` descending (742). `small_contrib_threshold`/`damping_power` written `%3.3f`.
- `DiscreteSamplerDimension.update(running_grid)` (659): if `grid_mode==1`, just `self += running_grid`. If initialization mode (2): rescales ref by `ratio=sum_run/sum_ref`, blends per-bin using `min_bin_probing_points` (reset in this branch, 680 — read the value there), then sets grid_mode=1. Bins with zero `abs_weight` deleted (696-698).
- `Bin_Entry.__iadd__` (768): n_entries-weighted average of `weight`/`weight_sqr`/`abs_weight`; `n_entries` summed.
- `DiscreteSampler.write` (627): for each ref dimension (grid_type==1), calls `update(self[(name,2)])` (the run grid) then writes. Assumes a matching run grid exists.

## SIGFPE-during-integration is NOT this Python code (misattribution correction)
A runtime SIGFPE during integration is sometimes attributed to "VEGAS/DiscreteSampler grid degradation — a channel whose integral underflows to zero → 0/0 when the grid is rebuilt (combine_grid)." Source refutes that mechanism on two counts:
- `DiscreteSamplerDimension.update` DOES carry two UNGUARDED divisions in the `grid_mode != 1` (initialization) branch: `ratio = sum_run / sum_ref` (675) and `ratio_sqr = sum_run_sqr / sum_ref_sqr` (678), where `sum_ref = sum(w.abs_weight …)`. If a reference channel's total abs_weight is exactly 0, these divide by zero. (The `get_new_grid_for_var` divisions ARE epsilon-guarded: `x0 = 1e-14 + grid/(sum_var+1e-99)` at 442; `avg = sum_var/(stop-start+1)` at 469 has denom = grid-size ≠ 0; the 486 split is `and`-guarded on a truthy denominator.)
- BUT this is **Python**: a zero denominator raises a Python `ZeroDivisionError` with a traceback (probe-confirmed `1.0/0.0 → ZeroDivisionError`), NOT a hardware **SIGFPE**. A SIGFPE is an OS FP/integer trap raised by the compiled **Fortran** madevent binary during matrix-element / phase-space evaluation, not by this combiner. So a runtime SIGFPE during integration is Fortran-side (ME eval / `genps.f` = phase-space slice; whether FP-trapping is on = installation/make_opts), not `combine_grid.py`.
- Net: that attribution has the *locus* wrong (Python combiner ≠ SIGFPE source) and the *signal type* wrong (ZeroDivisionError ≠ SIGFPE). The unguarded 675/678 divide is real but manifests as a Python traceback between iterations, and only in initialization mode with a fully-zero reference channel.

## Cautions
- `original_grid` is overwritten (`=`), not accumulated, across subjobs — only the last subjob's original grid survives. Intentional (it's the input grid, same for all) but easy to misread.
- `oneFail` vs `onefail` attribute-name split (73 vs 80) — only `oneFail` is consulted.
- `write` (627) assumes every reference dimension has a paired run-grid tag `(name,2)`; KeyError if absent.
- `conservative_factor` (write_grid_for_submission 164 / write_associate_grid 185) is never read in the body — `twgt = mean/8.0/nb_event` is hardcoded `/8.0`. The `conservative_factor=5.0` survey caller (gen_ximprove.py:644) is a no-op. Don't reason about it affecting the truncated max weight.
