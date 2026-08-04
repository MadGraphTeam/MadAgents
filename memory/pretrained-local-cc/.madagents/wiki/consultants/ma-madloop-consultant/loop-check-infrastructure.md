---
description: Python loop-ME check infrastructure — check_stability/check_timing/check_profile, LoopMatrixElement{Evaluator,Timer}, DP/QP UPS/EPS classification, loop-direction-power + consistency diagnostics, StabilityCheckDriver I/O contract (process_checks.py, MG5_aMC v3.7.1)
---

# Loop check infrastructure (Python side)

`$MADGRAPH_INSTALL/madgraph/various/process_checks.py`. The Python orchestration behind `do_check stability|timing|profile` for the loop ME. The Fortran per-point evaluator (`StabilityCheckDriver.f`) is in ./madloop-init-and-stability.md; THIS page is the Python layer that drives it, classifies points, and reports diagnostics. Boundary note: my MEMORY.md earlier scoped "rotation orchestration" out — but my card lists "the numerical-stability check infrastructure" as in-slice, and these `Loop*` classes ARE the loop-ME stability check (not a tree check), so they are mine. The generic gauge/lorentz checks (below) lean check-infra-adjacent.

## Command dispatch
`madgraph_interface.py do_check`: `args[0] in ['timing','stability','profile']` ⇒ `process_checks.check_timing` (:4531-4532) / `check_stability` (:4542-4543) / `check_profile` (:4552-4555). `loop_interface.py do_check` (:778) only pre-validates (model gauge, stability statistics count as 2nd arg :800-802) then delegates to `MadGraphCmd.do_check` (:813). `_check_opts` (madgraph_interface.py:2999) = `['full','timing','stability','profile','permutation', ...]`.

## Loop check classes
- `LoopMatrixElementEvaluator(MatrixElementEvaluator)` (:523) — gauge/ward + stability evaluator; `fix_MadLoopParamCard` (:680, forces `MLReductionLib` per-tool :696-712), `get_me_value`/`parse_check_output` (the Fortran-driver I/O, below), `setup_ward_check` (:1001).
- `LoopMatrixElementTimer(LoopMatrixElementEvaluator)` (:1057) — timing/profile; `setup_process` (:1115), `time_matrix_element` (:1232), and `check_matrix_element_stability` (:1388) live here.
- Module functions: `check_profile` (:2107, timing THEN stability in one output, no regen), `check_stability` (:2156), `check_timing` (:2229), `generate_loop_matrix_element` (:2013), `output_profile` (:2536), `output_stability` (:2560), `output_timings` (:2897).
- Tool-name map: `bannermod.MadLoopParam._ID_reduction_tool_map` (banner.py:6135) = {1:CutTools,2:PJFry++,3:IREGI,4:Golem95,5:Samurai,6:Ninja,7:COLLIER} — same numbering as runtime `MLReductionLib` (see ./madloop-params-runtime-knobs.md).

## check_matrix_element_stability (:1388-...) — UPS/EPS classification
Default `nPoints` (:1399, read fresh) PS points; `split_orders=-1` sentinel (:1400). Loops over each requested reduction tool (`MLOptions['MLReductionLib']`, deduped :1474); a tool whose `lib<tool>.a` is missing is silently dropped from the list (:1478-1487); empty ⇒ returns None.
- `accuracy_threshold` (:1464) — DP accuracy above this magnitude ⇒ unstable; read the default fresh at :1464.
- `num_rotations` (:1468) — # Lorentz rotations beyond the loop-direction (CTMode A/B) switch; read default at :1468. Each point gets CTModeA (mode 1), CTModeB (mode 2 = reversed propagator order), plus `num_rotations` rotated evaluations (mode 1) (:1710-1720).
- **`dp_accuracy = (max(dp_res)-min(dp_res))/|mean(dp_res)|`** (:1724-1725). If `> accuracy_threshold`:
  - tool ∈ `[1,6]` (CutTools or Ninja — ONLY these can redo in QP, :1728) ⇒ mark `UPS` (unstable), redo CTModeA/B(modes 4/5)+rotations in QP, compute `qp_accuracy`; if QP still `> threshold` ⇒ mark `EPS` (exceptional) (:1731-1752).
  - other tools ⇒ just mark `UPS`, no QP recovery (:1753-1756).
- modes: 1/2 = DP original/reversed propagator order; 4/5 = QP original/reversed (matches CTModeRun semantics in ./madloop-params-runtime-knobs.md).
- Reuse: `SavedStabilityRun_<tool>_<n>.pkl` per tool (:1556); `-reuse` loads & combines, extra files renamed `LOADED_*` (:1562-1576).
- `MadLoopInitializer.fix_PSPoint_in_check(... read_ps=True, npoints=1, hel_config=-1)` (:1618-1619) sets the driver to read one PS point from stdin; for 2>1 processes the HelFilter double-check is kept ON (:1671-1673, special back-to-back kinematics).

## output_stability (:2560) — the reported diagnostics
Writes `stability_<mode>_<proc>.log` (mode = optimized|default, :2640-2646). Defines 3 diagnostic statistics over the per-point eval dicts:
- **accuracy(list)** = `2*(max-min)/|max+min|` (:2565-2568) — note this is the symmetric form, slightly different from the per-point `dp_accuracy` (/|mean|) used in the classifier above.
- **loop_direction_test_power P** (:2574-2602) = `accuracy(CTModeA,CTModeB) / accuracy(all rotations)`. Large P ⇒ the loop-direction (propagator-reversal) test is an effective stability probe on its own. Returns `(log10(median P), log10(min P), frac)` where `frac` = fraction of points with `log10(P) < -3` (points where the reading-direction test overstates accuracy by 3+ digits vs the rotation tests).
- **consistency test C** (:2604-2625) = `accuracy(all DP) / |best_QP - best_DP|`, `best = (max+min)/2`. C≈1 ⇒ the DP accuracy estimate is consistent with the actual DP↔QP shift. Returns `(log10 median, min, max)`.
- Reported per tool: #PS points, median/max/min DP accuracy, the P and C tuples, UPS/EPS counts. Full dump in `Stability_result_<proc>.dat`.

## time_matrix_element / profile (:1232-...) — timing diagnostics
- Disk usage (`du -shc`) of Source `.f`, process `.f`, `MadLoop5_resources/*.dat` (color), and the `check` exe (:1270-1275).
- Reads `MadLoop5_resources/<proc_prefix>HelFilter.dat`, counts contributing helicities (`int(hel)>-10000` in optimized mode, or `'T'`) into `n_contrib_hel` / `n_tot_hel` (:1301-1315) — this is where the timing report's helicity-fraction number comes from.
- `Booting_time` via `boot_time_setup(... bootandstop=True)` (:1290-1292) — one-time init cost (reduction-lib cache warm-up) separated from per-PS time.
- `target_pspoints_number = max(int(30/time_per_ps)+1, 50)` (:1319) — aims for a ~30 s run; `time_per_ps` estimated from Initialization time (`/4/2`) or a 3-point probe run (:1277-1288).
- `check_profile` (:2107) runs `time_matrix_element` THEN `check_matrix_element_stability` reusing the same dir/infos (`infos_IN=timing`, :2142-2145), merging the two reports.

## StabilityCheckDriver I/O contract (parse_check_output :800)
The Fortran `check`/`StabilityCheckDriver` writes `result.dat`; `parse_check_output` (:801) parses into a dict: `born, finite, 1eps, 2eps, gev_pow, accuracy, return_code, export_format`, plus split-order arrays `Split_Orders_Names`, `Loop_SO_Results`, `Born_SO_Results`, `Born_kept`, `Loop_kept` (:807-821). `get_me_value` (:732, the `check`-exe variant) compiles `make check`, runs `./check`, returns the parsed tuple; the stability variant feeds PS points to the persistent `StabilityCheckDriver` Popen via stdin. This dict is THE bridge from the Fortran driver (./madloop-init-and-stability.md) to the Python diagnostics.

## Boundary / cautions
- `check_gauge`/`check_gauge_process` (:3060/:3147, ward identity) and `check_lorentz`/`check_lorentz_process` (:3326/:3411) are tree+loop-shared check drivers; the loop ME participates but the orchestration is general MG5 check infra (check-infra-adjacent), not loop-specific — cited as the boundary, not owned in detail.
- Only CutTools(1)/Ninja(6) trigger QP recovery in the stability check (:1728); a stability run with Collier/IREGI/Golem/Samurai as the sole tool marks every unstable point UPS with no EPS distinction. (caution)
- The classifier's per-point `dp_accuracy` (/|mean|, :1724) and the reporter's `accuracy` (2*(max-min)/|max+min|, :2565) are DIFFERENT formulas — don't conflate the threshold-trigger metric with the logged statistic. (caution)
