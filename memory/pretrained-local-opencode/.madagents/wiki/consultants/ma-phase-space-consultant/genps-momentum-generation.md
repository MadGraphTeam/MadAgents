---
description: genps.f momentum-generation scaffolding — f_get_nargs, x_to_f_arg, gen_mom, one_tree (s/t decomposition + t-channel ping-pong), gentcms, get_channel_cut bias, and map_invarients (Minvar + nb_tchannel).
---

# genps.f momentum generation (integration-variable -> 4-momenta)

`$MADGRAPH_INSTALL/Template/LO/SubProcesses/genps.f`. Per-process copy lives at `<P>/genps.f`.

## Entry points
- `f_get_nargs(ndim)` (genps.f:1) = `4*nexternal+2` — the integrator-argument count handed to the
  matrix element (all 4-momenta + x1,x2).
- `x_to_f_arg(ndim,iconfig,...,x,p)` (genps.f:11) — sample's hook: calls `gen_mom` to build momenta,
  then if `ISUM_HEL/=0` calls `sample_get_discrete_x(wgt, hel_picked, iconfig, 'Helicity')` to draw
  the MC-over-helicity choice and pass `hel_picked` (gen_ps.inc) to `matrix<i>.f` (genps.f:60-65).
  Helicity *recycling at event time* is the mc-integration slice; this is only the per-point hel draw.
  Note the helicity unbias is *deferred*: `sample_get_discrete_x` (`Source/dsample.f:1206-1241`) does
  NOT multiply `wgt` by the DiscreteSampler jacobian — it stores `hel_jacobian=jacobian` to be divided
  out later "at the level of matrix<i>" (dsample.f:1239-1241 comment). The full per-dimension timing
  map (LO has exactly these four discrete MC choices, each draw-with-bias then correct-with-jacobian,
  but at DIFFERENT sites):
  - **Helicity** (`'Helicity'` dim) — DEFERRED: `hel_jacobian` stored, divided out in matrix<i>
    (dsample.f:1239-1241).
  - **channel** (amp2) — DEFERRED by construction: `ANS=ANS*AMP2(CHANNEL)/XTOT` inside matrix<i>
    (single-diagram-enhancement-amp2-weight.md).
  - **ee_mc / dressed beam** (`'ee_mc'` dim) — INLINE: `sjac = sjac * ee_jacobian` right after the
    draw (genps.f:266-268).
  - **subprocess** (`select_grouping`, `'grouped_processes'`/`'PDF_convolution'` dims) — INLINE:
    `WGT *= SUMPROB/SELPROC` or `*MC_GROUPED_PROC_JACOBIAN` in auto_dsig.f.
  So all four stay unbiased, but the timing is NOT uniform and is NOT derivable from the dimension's
  nature — it is a per-dimension implementation choice; read each. (These are the only DiscreteSampler
  dimension names in the LO template: `Helicity`, `ee_mc`, `grouped_processes`(+`PDF_convolution`);
  the channel-amp2 path is NOT a DiscreteSampler dimension.) Do not assume a single draw-then-unbias
  shape.

## gen_mom (genps.f:68) — orchestrates the channel's PS generation
- `this_config=iconfig` is passed to the amplitude (genps.f:221).
- Reads `iforest`/`tstrategy` (common /to_forest/), `sprop`/`tprid` (/to_sprop/),
  `spole`/`swidth` (/to_brietwigner/) — the configs.inc + set_peaks tables.
- Integration-variable layout (header genps.f:86-90): first `nbranch` vars = branch masses; for each
  t-channel invariant, `x(ndim-1),x(ndim-3),...` carry cos(theta), `x(ndim),x(ndim-2),...` the phi.

## one_tree (genps.f:710) — the s/t decomposition
Requires at least one t-channel part as `itree(1,i)` first.
- Counts `ns_channel` / `nt_channel` by walking itree until the incoming-leg index (`iopposite`,
  set by tstrategy sign, genps.f:784-795).
- Trivial 2->1 trap returns p3=p1+p2 (genps.f:774-779).
- s-channel masses: `sample_get_x` draws each s in [smin,smax], jac*=stot (genps.f:836-865).
- t-channel: chooses remaining invariant masses, then 2->2 scattering via the
  **ping-pong strategy** keyed on `tstrategy` (= +/-1, +/-2): genps.f:924+ alternates which end of the
  t-chain each branching attaches to ("T-channel ping-pong starting with 2"). `gentcms` does the
  actual t-channel 2->2 momentum build.
- Energy/mass feasibility guards return negative jac codes (-2..-9) that sample treats as a rejected
  point (genps.f:815-819, 843-850, 898-913).

## gentcms (genps.f:1418) — t-channel 2->2 kinematics
Given t and phi, builds p1 and remainder pr for `pa+pb->p1+p2` (Byckling-Kajantie ch.6). Returns
jac<0 on unphysical pp (genps.f:1457-1475).

## get_channel_cut (genps.f:1817) — the channel-sampling bias factor
Returns a multiplicative weight that biases multi-channel selection toward this config's propagator
structure. Behavior gated on `sde_strat`:
- `sde_strat==1 and tmin_for_channel==-1`: returns 1 (no bias) — the common LO default path
  (genps.f:1878-1881).
- `sde_strat==1` with `<2` t-channels: returns 1 (genps.f:1910-1913).
- `sde_strat==2`: divides by the propagator denominator squared — t-channel `1/(t-M^2)^2`,
  s-channel `1/((t-M^2)^2+(M*Gamma)^2)` (genps.f:1931-1952) using prmass/prwidth from props.inc.
- t-channel `t/stot < tmin_for_channel`: damps by `exp((t-tmin)/(t+1))` (genps.f:1938-1943).

## configure_integral (genps.f:598) — per-config setup before integration
Sets stot from beams (incl. proton mass 0.938 / lepton masses by lpp), maps the requested diagram
number to `this_config`, calls `map_invarients` and `set_peaks`, and primes dsig (genps.f:653-705).

## map_invarients (Source/invarients.f:188) — Minvar map + nb_tchannel count
Defined in `$MADGRAPH_INSTALL/Template/LO/Source/invarients.f:188` (NOT in genps.f); called from
both configure_integral (genps.f:694) and the driver (madevent_driver.f:181). Inputs `ninvar`,
`iforest`; outputs `Minvar(invariant, config)`, `ninvar`, **`nb_tchannel`**.
- Builds `Minvar(j,iconfig)` = which integration-variable index branch invariant `j` of config
  `iconfig` uses (invarients.f:249-265 multi-config path; 230-243 the `nconfigs==1` simple path
  `minvar(j)=j`).
- A branch is t-channel when `iforest(1,-j,iconfig)` is an incoming leg (1, or 2 when nincoming==2)
  (invarients.f:252); it then also allocates the cos-theta slot `minvar(nbranch-1+2*j,...)`.
- **`nb_tchannel` is computed here** by walking the forest until the incoming leg:
  `ns_channel` counts s-channel branches, then `nb_tchannel = nbranch - ns_channel - 1`
  (invarients.f:238-243, simple path). This is the count the driver reads.
- The last pure-s-channel invariant is dropped for 2->n (`minvar(nbranch-1)=0`, invarients.f:262-265)
  — it's fixed by the overall s-hat, not an independent integration variable.

`nb_tchannel` flows straight into the driver's VEGAS-iteration bump:
`if (nb_tchannel.gt.1) itmax = itmax + 2` (madevent_driver.f:196-199) — t-channel-heavy channels
(>1 t-channel propagator) get 2 extra iterations. I own where nb_tchannel is *computed* and *read*;
the iteration-count *policy* otherwise is the numerical/VEGAS slice.

### nb_tchannel is ONLY computed on the nconfigs==1 path — and that's the standard per-channel job
`map_invarients` initializes `nb_tchannel=0` (invarients.f:229) and assigns a nonzero value **only**
inside the `if (nconfigs.eq.1)` branch (invarients.f:243: `nb_tchannel=nbranch-ns_channel-1`). The
multi-config `else` branch (invarients.f:246+) never touches it — `nb_tchannel` stays 0 there. This is
not a bug because the standard MadEvent per-channel driver invocation IS `nconfigs==1`:
- driver inits `nconfigs=1` (madevent_driver.f:129) and only reassigns it inside `if (mincfig.lt.0)`
  (madevent_driver.f:176-179), i.e. only for the negative-dconfig "map-all-configs" mode.
- `get_user_params`'s 4th arg is bound to `mincfig` at the call site (madevent_driver.f:166), then
  `maxcfig=mincfig` (167). For the normal positive `dconfig`, `mincfig>0`, the `mincfig.lt.0` block is
  skipped, `nconfigs` stays 1, and the simple path computes `nb_tchannel`. So the itmax bump fires per
  G-directory job exactly because each such job integrates a single config.
- (Note: the driver template *declares* the get_user_params dummy arg as `iconfig` at :245 but the
  caller passes `mincfig` at :166 — same storage, different name; don't be misled by the dummy name.)

## Cautions
- get_channel_cut RETURNS 1 (value-no-op) for the common `sde_strat==1`,`tmin_for_channel==-1` LO
  case, but it is genuinely CALLED in the generated matrix element's XTOT enhancement loop
  (`AMP2(J)=AMP2(J)*GET_CHANNEL_CUT(P,I)` under sde_strat==1; `AMP2(J)=GET_CHANNEL_CUT(P,I)` replacing
  amp2 under sde_strat==2) — not a dead call. See single-diagram-enhancement-amp2-weight.md. The real
  per-event channel-selection probability weighting happens via the DiscreteSampler grids (see
  driver-and-channel-selection-sampling page).
- one_tree assumes the t-channel propagator is itree(1,i) first — purely-s-channel configs route
  through the `nt_channel==0` branch (genps.f:797-799, 867-874), not the t-channel block.
- stot is capped by `dsqrt_shatmax**2` when set (run_card) — appears in both gen_s and set_peaks.
- `boost_to_frame(P1, frame_id, P2)` (genps.f:1759) is DEAD on the LO path — defined but has NO caller
  anywhere in Template/LO (grep-confirmed; only `ungen_s` is similarly dead). It boosts to the rest
  frame of the particle subset tagged by `frame_id` (cluster.f `sum 2**(N-1)` convention, decoded via
  `mapid`, cluster.f:128), with a `trivial_boost` early-out for the all-final-state tag. Don't cite it
  as runtime PS behavior. (`get_channel_cut` builds its propagator momenta `ptemp` by direct daughter
  summation, genps.f:1898-1928 — it does NOT call boost_to_frame.)
