---
description: The Fortran per-event ICONFIG draw (sample_get_config cumulative alpha) and why the classic Ohl/Pittau alpha-weight adaptation is DISABLED in v3.7.1 — for the standard configs==1 G-dir job the draw is a no-op returning mincfig.
---

# alpha channel selection (sample_get_config) and the disabled Pittau adaptation

The Python/DiscreteSampler channel grids (driver-and-channel-selection-sampling.md,
combine_grid.py) are one half of channel selection. The OTHER half is the Fortran
per-event ICONFIG draw inside the VEGAS loop, via the `alpha(maxconfigs)` cumulative
probabilities in common `/to_mconfig2/ psect, alpha`. This page owns that Fortran path and
the non-obvious fact that its classic adaptation is mostly dead code in v3.7.1.
`$MADGRAPH_INSTALL/Template/LO/Source/dsample.f`.

## The live draw: sample_get_config (dsample.f:1041)
Called at the top of BOTH main integration loops (`sample_get_config(wgt,iter,ipole)`,
dsample.f:174 and :429), and the chosen `ipole` is passed straight to
`x_to_f_arg(ndim,ipole,...)` (dsample.f:178,432). So `ipole` IS the per-event channel.
- `wgt = 1d0/(dble(events)*dble(itm))` — the flat per-point weight (dsample.f:1093).
- **Channel choice** (dsample.f:1096-1105):
  - `if (configs .gt. 1)`: draw `xrnd=ran1(idum)`, walk the cumulative `tot=Sum alpha(iconfig)`
    until `tot >= xrnd` — a standard cumulative-probability draw over `alpha`.
  - `else` (`configs==1`): `iconfig=mincfig` directly — NO draw.

## configs == nconfigs == 1 for the standard per-channel job — so the draw is a no-op
`configs = p5` inside `sample_init` (dsample.f:790, `configs=p5`; capped at maxconfigs at :807),
and `p5` is the `nconfigs` arg of `sample_full` (dsample.f:1) = the driver's `nconfigs`. The
driver inits `nconfigs=1` (madevent_driver.f:129) and only reassigns it (`maxcfig-mincfig+1`)
inside `if (mincfig.lt.0)` (madevent_driver.f:176-179). So:
- Standard per-channel G-dir job (positive dconfig, one config): `configs==1` => `sample_get_config`
  returns `iconfig=mincfig`, the `alpha` cumulative branch is skipped entirely.
- Only the negative-dconfig "map-all-configs" mode has `configs>1` and actually draws over `alpha`.
This is the SAME nconfigs==1 fact that gates nb_tchannel (genps-momentum-generation.md,
st-channel-classification-invariant.md): one structural fact, two consequences.

## The alpha adaptation is DISABLED in v3.7.1 (the trap)
Pretrained recall says MadEvent adapts channel weights via the Ohl/Pittau scheme
(`alpha *= sqrt(sqrt(psect))`). The code is THERE but inert:
- **alpha init** (dsample.f:875-892, 911-919): always uniform — `configs==1` => `alpha(i)=1`;
  else `alpha(i)=1d0/dble(configs)`. The runtime banner prints `'Using uniform alpha'`
  (dsample.f:881,922). There is NO non-uniform init from a grid file in the live path.
- **psect accumulation is dead** (dsample.f:1856-1872): the accumulation is guarded
  `if (.true.) then` with a body of TWO COMMENTED-OUT lines (the `!Ohl` and
  `!Not doing multi_config` lines, :1858-1859), `else` branch (the live Pittau accumulation,
  :1861-1870) unreachable. So `psect(i)` is NEVER incremented — it stays 0.
- **the Pittau update therefore zeroes** (dsample.f:2056-2069, under `if(use_cut.ne.0)` and
  `configs.gt.1`): `alpha(i)=alpha(i)*sqrt(sqrt(psect(i)))` with `psect(i)==0` gives `alpha(i)=0`
  for all i, then `tot=0`, then `alpha(i)=alpha(i)/tot` = 0/0. In practice this branch is only
  reachable with `configs>1` (map-all mode) AND it would corrupt alpha — confirming the per-config
  alpha adaptation is not the operative channel-weighting mechanism in v3.7.1.
- The per-iteration `write(*,'(8f10.5)') (psect(i)/tot, i=1,configs)` (dsample.f:2021-2023) and
  `'Configs:'` print (:2070-2071) still fire for `configs>1`, printing the (zero) psect fractions.

## What this means for the real channel weighting
The operative per-channel importance weighting in v3.7.1 is NOT this `alpha` array — it is:
- the single-diagram-enhancement `AMP2(CHANNEL)/XTOT` weight in the matrix element
  (single-diagram-enhancement-amp2-weight.md), and
- the cross-channel allocation of VEGAS POINTS done at survey/refine by the Python side
  (gen_ximprove + combine_grid.py DiscreteSampler), each config integrated in its own G-dir
  with `configs==1`.
So channel "selection" at the standard per-G-dir job is trivial (`iconfig=mincfig`); the
multi-channel competition happens between G-dirs (point budgets), not inside one job's `alpha`.

## Cautions / boundaries
- Do NOT cite `alpha`/`psect`/the Pittau `sqrt(sqrt)` update as the live channel-weight adaptation
  — it is disabled (commented psect accumulation) in v3.7.1. A claim that "MadEvent adapts the
  per-config alpha weights during survey" is wrong at this source level.
- `sample_get_config` IS live and IS mine (the per-event channel draw), but for the normal job it
  returns `mincfig` unconditionally.
- The VEGAS point/iteration budget per channel and the grid (`graph_point`, grid(2,i,j)) are the
  numerical/VEGAS slice. I own the channel-DRAW (`sample_get_config`) and the alpha-array semantics,
  not the per-invariant grid binning.
- `use_cut` (0 fixed grid / 2 adjusting) gates the alpha-update block; it is set from get_user_params
  ("use_cut" stdin) and flipped to 0 after a hardwired number of iterations (`itmax_adjust`, read
  dsample.f:421-424). The
  adjust/fix policy is numerical-slice-adjacent; I cite it only as the gate on the (dead) alpha update.
