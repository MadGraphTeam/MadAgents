---
description: The cross-section/error combination ladder — at each aggregation level (PS-point → iteration → channel → job → total) MadGraph sums, averages, or 1/sigma^2-weights, and xerru always combines in quadrature while xerrc/xsec follow the level rule. v3.7.1.
---

# Cross-section combination ladder (v3.7.1)

A cross-section number on `results.dat` or the HTML page is the top of a fixed aggregation ladder. This page answers the cross-level question — *which combination produced this error bar?* — that the per-level pages (combine-grid-vegas, iteration-combination-and-results) each answer only for one rung. Pure source-walk; no runtime prediction.

## The four rungs (LO/tree integration)

| rung | where | value rule | error rule |
|---|---|---|---|
| 1. PS-points → channel-iteration | `combine_grid.get_cross_section` (combine_grid.py:372) | `mean = sum_wgt*target_evt/nb_ps_point` | MC variance of the mean: `sigma = sum_wgt_square/vol^2 - nonzero*mean^2`, `/= nb_ps_point*(nb_ps_point-1)` |
| 2. iterations → channel | `gen_ximprove` accumulator (gen_ximprove.py:786-797) | `1/sigma^2`-weighted mean: `cross = sum(cross^3/sigma^2)/sum(cross^2/sigma^2)` | chi2/dof-folded: `sqrt(|chi2/cross^2 - sigma|/(step-1)/sigma)` (step>1); `sigma/cross` (step==1) |
| 3a. channels → total (running) | `get_current_axsec` (gen_ximprove.py:854) | **sum** of per-channel `abscross/(sigma+1e-99)` | — |
| 3b. jobs → channel (combine) | `sum_html.compute_values` (sum_html.py:440) | **sum**: `xsec=sum`, `axsec=sum`, `xerrc=sum`, `nunwgt/nevents=sum` | `xerru = sqrt(sum xerru^2)` (quadrature) |
| 3c. jobs → channel (average) | `sum_html.compute_average` (sum_html.py:459) | **average over nbjobs**: `xsec=sum/nbjobs`, `xerrc=sum/nbjobs` | `xerru = sqrt(sum xerru^2)/nbjobs` |

## The symmetry-multiplicity (mfactor) — where it IS and ISN'T applied
Each `OneResult` carries `mfactor` (symmetry multiplicity from `symfact.dat`), but it is applied **only via the explicit `.get()` accessor**, NOT in the total roll-up:
- `OneResult.get('xsec'/'xerru'/'xerrc')` returns stored × `mfactor` (sum_html.py:404-405); `luminosity` is **÷ mfactor at read only when `mfactor>1`** (324-325, guarded) and `get('luminosity')` returns it raw (406-409). `get('xerr')` = `sqrt(xerru^2 + xerrc^2)` (412-413) — combined per-channel error, NOT mfactor-scaled; `get('eff')` = `xerr*sqrt(nevents/(xsec+1e-99))` (410-411). (Earlier wiki revision swapped these two accessor labels — corrected.)
- **Consumed by the refine arithmetic** (gen_ximprove.py): event-mode uses `C.get('axsec')`/`C.get('xsec')` (1126-1947) — mfactor-scaled; precision-mode uses `cerr = C.mfactor*(xerru + Nchan*xerrc)` explicitly (1412-1444). So channel selection / event budgeting *does* see the multiplicity.
- **NOT applied in `Combine_results.compute_values`** (sum_html.py:444-447): the HTML/total roll-up sums **raw** `one.xsec`/`one.axsec`/`one.xerrc` and quadratures **raw** `one.xerru` — no `mfactor`. The headline total therefore relies on the Fortran-written per-channel `results.dat` *already folding* symmetry into its integral (consistent with `luminosity /= mfactor` at read undoing a representative-vs-family scaling). **Do NOT claim the Python total multiplies by mfactor — it does not.**
- In `symfact.dat`, lines with **`mfactor < 0` are skipped entirely** in `collect_result` (sum_html.py:726-727): symmetry *copies* never independently integrated; the positive-mfactor representative G-dir is the one that ran. So #G-dirs in `results.dat` < #ICONFIG.
- **Gap:** whether the representative channel's Fortran `axsec` already carries the ×mfactor (so the raw sum is correct) vs is per-single-config (so the raw total under-counts) is not settled from the Python alone — the multiplicity application sits in the Fortran integrand/symfact handling (phase-space / matrix-element territory). Source-confirmed here: the *Python* roll-up does not re-apply it.

## The invariant that's easy to misremember

**`xerru` (uncorrelated statistical) ALWAYS combines in quadrature; `xerrc` (correlated/systematic) and `xsec`/`axsec` follow the rung's value rule (sum at compute_values, average at compute_average).** Source: both sum_html functions do `xerrc = sum(...)` (linear) and `xerru = sqrt(sum(...^2))` (quadrature) — compute_values divides neither, compute_average divides both by `nbjobs`. Do not assume the two error columns combine the same way: they don't, and conflating them mis-states the error bar.

**Where the xerru/xerrc split is *born*:** at the per-channel write (`write_results`, gen_ximprove.py:861) BOTH columns are written to the *same* value — fields 2 and 3 of `results.dat` are each `fstr(error*cross)`, i.e. the rung-2 relative error × cross (884-888). So in a freshly-written channel `xerru == xerrc`. The divergence is introduced *only* by rung-3 combination (xerru → quadrature, xerrc → linear sum). A reader who sees `xerru != xerrc` is looking at an already-combined number.

## Which average vs sum fires where
- **compute_values (sum)** — the survey/refine in-channel combine of split jobs and the channel→total roll-up; the headline cross-section is a sum of channel contributions.
- **compute_average (average)** — multi-job channels combined by `combine_runs.CombineRuns` (those carrying `multijob.dat`): the same channel integrated by several jobs is *averaged*, not summed, because each job is an independent estimate of the same integral. Carries a consistency check: any job with `xsec < mean - 25*xerru` is dropped and the result recomputed with `error = (max_xsec - min_xsec)/2` (sum_html.py:495-505).

## Why the level matters for reading a number
- A `results.dat` channel error in a single-job channel = rung 2 (chi2/dof). A multi-job channel error = rung 3c with the (max-min)/2 fallback if any job was inconsistent. Same column, different estimator depending on `multijob.dat`.
- The total cross-section error is NOT a single MC variance — it is the quadrature roll-up of rung-2 per-channel errors (each already chi2/dof-folded). A large total error traces to one channel's chi2/dof, not to overall point count.

## Boundary
- LO/tree integration only. NLO FKS-contribution error combination is amcatnlo/fks territory. PDF/scale-variation error combination is the systematics slice.
- Secondary-unweighting max-weight (`get_max_wgt`) is a separate quantity, not part of the xsec error ladder — see combine-grid-vegas.md.

## Instances generalized
- combine-grid-vegas.md (rung 1: get_cross_section MC variance).
- iteration-combination-and-results.md (rung 2: 1/sigma^2 + chi2 accumulator; rung 3b/3c: compute_values/compute_average; get_current_axsec total).
Both kept — they carry the per-rung mechanism detail; this page carries only the cross-rung rule.
