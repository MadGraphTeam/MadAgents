---
description: Fixed-order (LO/NLO) histogram/plot artefacts are keyed on FO_analyse_card fo_analysis_format (default HwU→MADatNLO.HwU+gnuplot; alt topdrawer/root/lhe); combine_plots_FO/finalise_run_FO assemble them, and do_plot only converts MADatNLO.top (no-op for the default HwU).
---

# Fixed-order analysis artefacts — `combine_plots_FO` / `finalise_run_FO` / `do_plot`

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`. A fixed-order (LO/NLO) run produces a histogram file whose **format and name depend on the `FO_analyse_card`**, not a fixed `MADatNLO.HwU`. This refines the flat "fNLO → MADatNLO.HwU" claim in [[runtime-shell-commands]] and [[print-summary-and-event-assembly]]. The histogram CONTENTS (the binned observables) come from the FO analysis Fortran (nlo-export/fks territory); this page owns the runtime file-assembly and the format switch.

## The format switch — `FO_analyse_card['fo_analysis_format']`
Default card `$MADGRAPH_INSTALL/Template/NLO/Cards/FO_analyse_card.dat`: **`FO_ANALYSIS_FORMAT = HwU`**, `FO_ANALYSE = analysis_HwU_template.o` (root/topdrawer alternatives are commented examples in the same card). So the **default fixed-order artefact is `MADatNLO.HwU`** plus a gnuplot file — but it is a card choice.

`combine_plots_FO` (2933, called by `finalise_run_FO`) branches on `self.analyse_card['fo_analysis_format'].lower()`:
- **`hwu`** (2951): `combine_plots_HwU(jobs, out)` → `Events/<run>/MADatNLO.HwU`, then `gnuplot MADatNLO.gnuplot` (failure swallowed, 2958). The default.
- **`topdrawer`** (2937): `./combine_plots_FO.sh` over each job's `MADatNLO.top` → copies `MADatNLO.top` into `Events/<run>/`.
- **`root`** (2962): `./combine_root.sh` over each job's `MADatNLO.root` → `MADatNLO.root`.
- **`lhe`** (2976): `combine_FO_lhe(jobs)` → an LHE file "to be used for plotting only".
- else (2980): just logs "results saved", no plot file.

## `finalise_run_FO` (3183) — end of a fixed-order run
Called once after the FO integration loop ([[integration-driver-mint-loop]]) converges. Moves `SubProcesses/res_*.txt` → `Events/<run>/`, calls `combine_plots_FO`, and — only if `run_card['pineappl']` — `pineappl_combine(cross, error, jobs)` writes `Events/<run>/amcblast_obs_<N>.pineappl` grids (3124-3147).

## `do_plot` (1544) — HTML plots, TopDrawer-only
`do_plot [parton|all]` converts a histogram into MA5/td HTML plots. NON-OBVIOUS: it only acts on a **`MADatNLO.top`** file (1568) — `if os.path.exists(MADatNLO.top)` → copies it to `HTML/<run>/plots_parton/plots.top` and runs the `plot` + `plot_page-pl` scripts (uses `madanalysis_path`, `td_path`, `dirbin`). **For the default HwU format there is NO `.top` file, so `do_plot` silently does nothing** beyond the optional `events.lhe` parton path (1556-1565, which needs an LHE — fixed-order LO/NLO produce no events.lhe). `do_plot` is therefore effectively a no-op for a default-config fixed-order run; the HwU/gnuplot plots are already produced inline by `combine_plots_FO`.

## Cautions
- The fixed-order histogram file is **`MADatNLO.HwU` only under the default `FO_ANALYSIS_FORMAT=HwU`**. A user who set `topdrawer`/`root`/`lhe` in the FO_analyse_card gets `MADatNLO.top`/`.root`/an LHE instead — do not assume `.HwU` exists.
- `do_plot` operates on `.top` only — running `plot` on a default (HwU) fixed-order run produces nothing. To get HTML plots from FO output, the FO_analyse_card must be set to topdrawer, or use the HwU+gnuplot output `combine_plots_FO` already made.
- The gnuplot call in the HwU branch swallows all exceptions (2958) — a missing/broken gnuplot leaves the `.HwU` but no rendered plot, silently.
- (Runtime predictions — exact files produced per format, the gnuplot success — are source-read, not probe-verified end-to-end; needs a completed FO run.)
