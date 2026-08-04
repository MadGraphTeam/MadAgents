---
description: madevent_driver.f orchestration (Program DRIVER, get_user_params, lbw decode, nb_tchannel itmax bump) and the combine_grid.py DiscreteSampler channel-selection grids.
---

# driver.f orchestration + channel-selection sampling

## driver.f — generated from madevent_driver.f
`<P>/driver.f` is written by `write_driver` (export_v4.py) from
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_driver.f`. Template placeholders:
`%(param_card_name)s`, `%(ncomb)i`, `%(hel_init_points)d`, `%(DRIVER_EXTRA_*)s`, `%(secondparam)s`.

`Program DRIVER` (madevent_driver.f:1) sequence:
- Reads process group number from `dname.mg` (madevent_driver.f:90-101).
- Reads `twgt` from `results.dat` if present (gridpack first-iteration reuse, line 105-117).
- `setrun` / `setpara` / `setcuts` / `printout` (line 123-128).
- `get_user_params(ncall,itmax,itmin,iconfig)` (subroutine signature at madevent_driver.f:228; the
  dummy 4th arg is named `iconfig` at :245, but the CALL site at :166 binds it to `mincfig`, then
  `maxcfig=mincfig` at :167 — so the 4th param is really the channel/config number). Reads stdin:
  ncall, itmax, itmin; accuracy;
  use_cut (0 fixed / 2 adjustable grid); suppress-amplitude -> `multi_channel`; helicity mode
  (`isum_hel`); and the **configuration number** `dconfig` (line 274-358).
- `map_invarients(minvar,...,nb_tchannel)` sets the invariant mapping (line 181).
- `ndim = 3*(nexternal-nincoming)-4`, +1 per beam with `lpp>=1` (line 183-185).
- **nb_tchannel bump**: `if (nb_tchannel.gt.1) itmax = itmax + 2` (line 196-199) — t-channel-heavy
  channels get 2 extra VEGAS iterations.
- `call sample_full(ndim,ncall,itmax,itmin,dsig,ninvar,nconfigs,VECSIZE_USED)` (line 202).

### get_user_params decodes the BW sub-channel (line 228)
- `iconfig=int(dconfig*(1+10**(-ncode)))` extracts the integer config; `diag_number=iconfig`.
- The fractional part -> `jconfig`, `DeCode(jconfig,lbw(1),3,nexternal)` fills the `lbw` array (line
  339-348) consumed by myamp's cut_bw. `lbw(0)=0` means "not subdividing B.W."
- `ncode=int(dlog10(3d0)*(max_particles-3))+1` — must match madevent_symmetry.f enCode.
- helicity: `isum_hel=0` exact sum; `-1` zero-hel determination (init_mode); `i>0` MC-over-hel,
  registers DiscreteSampler 'Helicity' dimension with `%(hel_init_points)d` min points (line 318-327).

### open_file_local — the G-directory convention (line 366)
Builds the per-channel run directory name: `G<mincfig>` if `lbw(0)==0`, else `G<mincfig>.<jconfig>`
(BW-subdivided sub-channel) (line 420-435). This is the on-disk ICONFIG <-> directory mapping.

## combine_grid.py — DiscreteSampler channel-selection grids
`$MADGRAPH_INSTALL/madgraph/madevent/combine_grid.py`.
- `grid_information(mc_hel)` (line 19) accumulates per-channel sums: `sum_wgt`, `sum_abs_wgt`,
  `sum_wgt_square`, `max_wgt`, `nb_ps_point`; `add_one_grid_information` parses the Fortran grid dump
  (nonzero/ng/maxinvar header + grid_base/original_grid/non_zero_grid blocks, line 56-107).
- `DiscreteSampler(dict)` (line 510) reads/writes `<DiscreteSampler_grid>` blocks keyed by
  `(name, grid_type)`. `grid_type` 1=reference, 2=running. `mode='add'` sums running grids but keeps
  one reference (line 558-565). Used for both 'Helicity' and channel dimensions.
- `DiscreteSamplerDimension(name)` (line 642) holds per-bin attributes: `min_bin_probing_points`,
  `grid_mode` (1=default,2=initialization), `small_contrib_threshold`, `damping_power`.
- `Bin_Entry(n_entries, weight, weight_sqr, abs_weight)` (line 757) = one channel/helicity bin; its
  abs_weight relative to the total is the sampling probability. `damping_power` softens the
  weight->probability map.

### damping_power / small_contrib_threshold are set per RUN MODE, not fixed defaults
`write_grid_for_submission(..., mode='survey')` (combine_grid.py:163) overrides every discrete
dimension's `small_contrib_threshold` and `damping_power` at grid-write time depending on `mode` (read
the per-mode values at combine_grid.py:228-242):
- `mode=='survey'`: conservative — cube-root-ish damping, drops channels below a small contribution
  threshold.
- `mode=='refine'`: aggressive — square-root damping, a much smaller drop threshold.
- else (e.g. event generation): drop-nothing threshold, square-root damping.
So the channel-selection probabilities track weight *more aggressively as the run progresses*, and a
channel below the survey threshold can be pruned from sampling. The file-format comment lines show the
written defaults (read them at combine_grid.py:528-531, e.g. `min_bin_probing_points`). `damping_power<1`
flattens the probability distribution (more democratic sampling); survey's vs refine's `damping_power`
(read at :228-242) is the lever.

## Cautions
- The number of VEGAS points/iterations, convergence, and grid refinement are the **numerical/VEGAS
  slice** — I own the *channel structure and the discrete-sampler scaffolding*, not the iteration
  counts (except the source-visible `itmax+=2` t-channel bump, which is in the driver I own).
- multi_channel=.false. (full amplitude) bypasses single-diagram enhancement entirely; whether a run
  uses it is decided in get_user_params from the "Suppress amplitude" answer (driven by the launcher).
- The G-directory `.jconfig` suffix is how BW sub-channels surface on disk; a config with conflicting
  BWs produces multiple G-dirs for one MAPCONFIG.
