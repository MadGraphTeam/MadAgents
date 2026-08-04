---
description: The standard per-G-dir MadEvent job runs nconfigs==1 — one structural root (driver inits =1, only negative-dconfig map-all mode bumps it) that makes the channel draw trivial, computes nb_tchannel, and disables every map-all-only branch (alpha adaptation, multi-config psect).
---

# nconfigs==1: the one fact behind "per-G-dir channel selection is trivial"

The standard MadEvent integration job is per-channel: each surviving ICONFIG is integrated in
its OWN `G<mincfig>` (or `G<mincfig>.<jconfig>`) directory, and that job runs with `nconfigs==1`.
This single structural fact propagates to FOUR distinct consequences across the LO path; each of
my other pages mentions it as a side-note to its own scope, but no page owns the invariant itself.
Knowing it lets you answer "does MadEvent draw a channel per event / adapt alpha / bump itmax in
a normal run?" from ONE fact, for ANY process.

## The single root: driver inits nconfigs=1, bumps it ONLY in map-all mode
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_driver.f`:
- `nconfigs = 1` (madevent_driver.f:129) — the init.
- Reassigned `nconfigs=maxcfig-mincfig+1` (madevent_driver.f:179) ONLY inside `if (mincfig.lt.0)`
  (madevent_driver.f:176) — the negative-dconfig "map-all-configs" mode.
- `mincfig` is the 4th arg of `get_user_params` (caller binds it at :166; `maxcfig=mincfig` at :167).
  For a normal positive `dconfig` the `mincfig.lt.0` block is skipped → `nconfigs` stays 1.
- `nconfigs` threads into the sampler: `sample_full(...,nconfigs,...)` (`Source/dsample.f:1`) →
  `sample_init(p1..p5,...)` → `configs = p5` (dsample.f:790, capped at maxconfigs 805-807). So the
  driver's `nconfigs` IS the sampler's `configs`.

## The four consequences that gate on nconfigs/configs == 1
1. **nb_tchannel is computed (→ itmax bump).** `map_invarients` assigns `nb_tchannel` ONLY inside
   `if (nconfigs .eq. 1)` (`Source/invarients.f:230`, `nb_tchannel=nbranch-ns_channel-1` at :243);
   the multi-config `else` leaves it 0. The driver then fires `if (nb_tchannel.gt.1) itmax=itmax+2`
   (madevent_driver.f:196-198). So the t-channel iteration bump fires per-G-dir precisely BECAUSE
   each such job is nconfigs==1. (See genps-momentum-generation.md, st-channel-classification-invariant.md.)
2. **The per-event channel draw is a no-op.** `sample_get_config` (dsample.f:1096-1105):
   `if (configs .gt. 1)` walks the cumulative `alpha`; `else` sets `iconfig=mincfig` directly — no
   draw. For nconfigs==1 the chosen `ipole` IS `mincfig`, handed straight to `x_to_f_arg`. (See
   alpha-channel-selection-fortran.md.)
3. **alpha init is uniform / trivial.** `if (configs .eq. 1)` → `alpha(1)=1` (dsample.f:876+,
   'Using uniform alpha' banner at :881); the multi-config else gives `alpha(i)=1/configs`. (See
   alpha-channel-selection-fortran.md.)
4. **Every map-all-only branch is unreachable.** The (already-dead, commented-psect) Pittau
   alpha update (dsample.f:2062 `if (configs .gt. 1)`) and the per-iteration `Configs:` psect
   print (dsample.f:2022) only run for configs>1. So in the normal job they never execute — a
   SECOND reason (on top of the commented accumulation) the alpha adaptation is inert. (See
   alpha-channel-selection-fortran.md.)

## What this predicts (for ANY process, any channel)
- Channel "selection" inside a standard survey/refine G-dir job is trivial: `iconfig=mincfig`. The
  real multi-channel competition is BETWEEN G-dirs (VEGAS point budgets allocated by the Python
  gen_ximprove + combine_grid.py DiscreteSampler), not inside one job's `alpha` array.
- The `itmax+=2` t-channel bump DOES fire per-G-dir (because nconfigs==1 is the only path that
  computes nb_tchannel) — count TPRID!=0 branches in configs.inc; >1 ⇒ bump.
- The negative-dconfig "map-all-configs" mode (`mincfig<0`) is the ONLY regime where `configs>1`,
  where the alpha cumulative draw is live, and where nb_tchannel stays 0 (no bump). It is not the
  standard per-channel job.

## Boundary
- The VEGAS point/iteration budget and the cross-G-dir allocation are the numerical/VEGAS slice;
  this page owns only the `nconfigs==1` structural fact and its four gated consequences in the
  source I own (driver, genps/invarients, dsample channel draw).
- The alpha adaptation is ALSO disabled by the commented psect accumulation (independent of
  nconfigs); see alpha-channel-selection-fortran.md. nconfigs==1 is the SECOND, structural reason
  it never runs in a normal job — both hold.
