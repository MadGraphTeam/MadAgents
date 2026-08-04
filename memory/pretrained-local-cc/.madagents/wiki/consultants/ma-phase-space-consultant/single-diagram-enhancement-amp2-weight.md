---
description: The single-diagram-enhancement channel weight ANS=ANS*AMP2(CHANNEL)/XTOT in the generated matrix element, plus the grouped-subprocess prepare_grouping_choice/select_grouping PDF-weighted selection in auto_dsig.f. Includes the SMEFT pure-quadratic-bin 'All amp2 are zero but not the total matrix-element' STOP 1 crash and the sde_strategy=2 fix (amp2 replaced by propagator denominator; banner auto-set forces DY back to strategy 1).
---

# Single-diagram enhancement: the amp2 channel weight (and grouped-subprocess selection)

The genps/configs/set_peaks machinery on my other pages chooses *how a channel samples phase
space*. This page covers the complementary half: *how the matrix-element value returned for that
channel is re-weighted so the channel only "sees" its own diagram's resonant structure*. That
re-weight IS single-diagram enhancement, and it lives in the generated matrix element, not in the
static Template SubProcesses.

## The enhancement weight: ANS = ANS * AMP2(CHANNEL) / XTOT
In the generated `<P>/matrix<i>_orig.f` (template
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/matrix_madevent_v4.inc:174-185`), inside
`IF (MULTI_CHANNEL)`:
- `XTOT = sum_i AMP2(i)` over all diagram channels (matrix_madevent_v4.inc:176-178).
- `set_amp2_line` expands to **`ANS=ANS*AMP2(MAPCONFIG(ICONFIG))/XTOT`** (ungrouped:
  `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:4797`).
So the matrix element returned for channel ICONFIG is the full |M|² scaled by the *fraction of total
|amp|² carried by this channel's own diagram*. A channel whose diagram is far off its resonance has
tiny AMP2(this)/XTOT and contributes little; near its resonance AMP2(this)≈XTOT and it carries ~all
the weight. Summed over channels (each sampled with its own peak-flattening map) this reproduces the
full cross section while letting each channel concentrate sampling on its own peak. This is the
"single-diagram enhancement" — the reason MadEvent uses one channel per diagram instead of RAMBO.

## AMP2(i) = |sum of amplitudes of diagram i|^2 (filled in the matrix element)
`get_amp2_lines` (export_v4.py:1390) writes the AMP2 fill lines:
- Ungrouped (export_v4.py:1432-1442): `AMP2(idiag+1)=AMP2(idiag+1)+ AMP(a)*dconjg(AMP(a)) + ...`
  summing the squared amplitudes belonging to that one diagram. **4-vertex diagrams are skipped**
  here too (`max(vertex_leg_numbers)>minvert` -> `continue`, export_v4.py:1434) — same exclusion as
  configs.inc, so AMP2 indices are sparse/non-consecutive.
- Grouped (export_v4.py:1400-1430, `config_map` present): AMP2 is summed over *diagrams with
  identical propagator properties* (`get_multi_channel_dictionary`), keyed by the FIRST diagram
  number of that config: `AMP2(first+1)=AMP2(first+1)+(AMP(a)+AMP(b)+...)*dconjg(...)`. The amplitudes
  are summed *before* squaring (coherent), not |M|²-summed — comment cites the JIM/non-diagonal-CKM
  reason (export_v4.py:1421-1426).
- Probe (`<PROC_DIR>/SubProcesses/P2_gg_ttx/matrix1_orig.f`, grouped gg>ttx):
  `AMP2(3)=AMP2(3)+(AMP(3)+AMP(4))*DCONJG(AMP(3)+AMP(4))` (line 496),
  `AMP2(5)=AMP2(5)+(AMP(5)+AMP(6)+AMP(7))*DCONJG(...)` (497) — coherent grouped sums, indices 2,3,5,8
  (non-consecutive, confirming the skip).

## CHANNEL vs MAPCONFIG(ICONFIG) — grouped path differs, and get_channel_cut IS called here
The grouped exporter's generated block is richer than the static `matrix_madevent_v4.inc` template.
In the grouped `matrix1_orig.f` (probe gg>ttx, lines 260-275) the enhancement is
`ANS=ANS*AMP2(CHANNEL)/XTOT` where `CHANNEL` is a **subroutine argument** of `SMATRIX1` (matrix1_orig.f:1,42),
the channel-to-keep passed in by the caller — not the bare `MAPCONFIG(ICONFIG)` of the ungrouped
template. And the XTOT loop multiplies in `get_channel_cut`:
```
DO I=1,LMAXCONFIGS
  J = CONFSUB(1, I)
  IF (J.NE.0) THEN
    IF(SDE_STRAT.EQ.1) THEN
      AMP2(J) = AMP2(J) * GET_CHANNEL_CUT(P, I)   ! default: cut returns 1 -> no change
      XTOT=XTOT+AMP2(J)
    ELSE                                           ! sde_strat==2
      AMP2(J) = GET_CHANNEL_CUT(P, I)              ! amp2 REPLACED by propagator approximation
      XTOT=XTOT+AMP2(J)
ENDIF
```
(matrix1_orig.f:260-274). So `get_channel_cut` is **called inside the enhancement loop**, not only in
genps. On the default LO path (`sde_strat==1`, `tmin_for_channel==-1`) it returns 1
(genps.f:1878-1881) so the value is unchanged — but the call site is real. Under `sde_strat==2` the
true |amp|² is discarded and the channel weight becomes purely the propagator-denominator
approximation (`1/(t-M^2)^2` etc., genps.f:1931-1952). This REFINES the genps-momentum-generation
caution: get_channel_cut is a value-no-op by default, not a dead call.
- `XTOT==0 && ANS!=0` is a hard error: `'Problem in the multi-channeling. All amp2 are zero but not
  the total matrix-element'` then `stop 1` (matrix_madevent_v4.inc:182-183; grouped form has an
  `NB_FAIL` tolerance before the stop — read the threshold at matrix_madevent_group_v4.inc:230-235). Five generated
  templates carry this string verbatim (matrix_madevent_v4.inc:182, matrix_madevent_group_v4.inc:231,
  matrix_madevent_group_v4_hel.inc:152, matrix_loop_induced_madevent.inc:317,
  matrix_loop_induced_madevent_group.inc:327).

## The SMEFT pure-quadratic-bin crash and the sde_strategy=2 fix
This is the non-obvious failure mode of the `XTOT==0 && ANS!=0` branch above, for a LO SMEFT bin
(e.g. `p p > l+ l-` isolating a pure-quadratic Wilson-coefficient term). Anchored empirical: with the
DEFAULT `sde_strategy=1`, MadEvent crashes at survey with the `All amp2 are zero but not the total
matrix-element` STOP 1.
- **Why amp2 goes all-zero while ANS≠0.** `AMP2(i)=|amplitudes of diagram i|²` is filled per-diagram
  in the matrix element (`get_amp2_lines`, export_v4.py:1390; section above). The XTOT loop
  (matrix_madevent_v4.inc:175-178 ungrouped / matrix_madevent_group_v4.inc:214-226 grouped) sums those
  filled amp2 over channels. Under `sde_strat==1`, `get_channel_cut` returns `1d0` immediately
  (genps.f:1878-1881) so `AMP2(J)` is used as-filled. When the matrix file contains ONLY EFT-tagged
  amplitudes (the SM/NP=0 amplitudes were stripped out as channels by an amplitude-level filter — see
  the coupling-order/eft seam below) AND only a single Wilson coefficient is nonzero, every per-channel
  `AMP2(i)` evaluates to zero for that point while the COHERENT total `ANS=|sum of amps|²` is nonzero —
  so `XTOT=0` but `ANS≠0`, tripping the abort. The per-channel amp2 array is the squared single-diagram
  weight; it can vanish for a channel whose diagram is the SM piece even when the total survives.
- **How sde_strategy=2 sidesteps it.** Under `sde_strat==2` the XTOT loop does NOT consult the filled
  amp2: it REPLACES it — `AMP2(J) = GET_CHANNEL_CUT(P, I)` (matrix_madevent_group_v4.inc:222; ungrouped
  uses the genps strat-2 path). `get_channel_cut` then returns the pure propagator-denominator
  approximation `∏ 1/((t−M²)²+M²Γ²)` (s-channel, genps.f:1945-1951) / `1/(t−M²+stot·1e-10)²`
  (t-channel, genps.f:1931-1934), built from kinematics + props.inc masses/widths ALONE — never the
  amplitude. So XTOT is a sum of strictly-positive propagator factors, can't be all-zero, and the
  abort branch is unreachable. The channel weight is then the propagator shape rather than the true
  |amp|² — fine for an EFT-only matrix file where the amp2 single-diagram weight is degenerate.
  banner.py:4458 registers `SDE_strategy` (read its default + allowed list there), `fortran_name=sde_strat`,
  comment cites hep-ph/0208156 for strategy 1 and "use the product of the denominator" for strategy 2.
- **Why the DEFAULT crashes on DY (banner auto-set).** banner.py's `create_default_for_process`
  auto-tunes `sde_strategy`: an interference/squared process (`'^2' in nice_string()`,
  banner.py:4975) → strategy 2 (:4988); a single-color non-FD gauge process → strategy 2 (:4995-4996);
  BUT a pure-lepton final state with proton initial state is forced BACK to strategy 1 (:4998-5012,
  the `if pure_lepton and proton_initial: self['sde_strategy']=1`), and `$`-syntax forbidden-onshell
  also forces 1 (:5055-5059). `p p > l+ l-` is exactly pure-lepton/proton → auto-set lands on
  strategy 1 → crash. The user must manually set `sde_strategy = 2` in run_card.dat; this is NOT
  auto-corrected for the amplitude-filtered EFT-only case.
- **Amplitude-filter vs squared-filter (coupling-order/eft seam, premise here).** The integrator
  consults the AMPLITUDE-level `AMP2(i)` array (export_v4.py:1390 fills it from `AMP(a)*dconjg(AMP(a))`
  per diagram), NOT a squared-order bin. So what governs the crash is the PRESENCE/ABSENCE of the SM
  (NP=0) amplitudes as channel slots in the matrix file, not which squared-order bin is selected:
  - An amplitude-level constraint that STRIPS the SM/NP=0 amplitudes (e.g. SMEFTsim `NP==1`, or
    SMEFTatNLO-LO `NP=2 NP^2==4`) removes those multi-channel slots → all surviving amp2 can be zero →
    crash under strat 1.
  - A squared-order constraint (`NP^2==2`) leaves the NP=0 amplitudes physically PRESENT in the channel
    pool as nonzero-amp2 slots even though the squared bin is zeroed → XTOT≠0 → no crash.
  WHICH filter strips which amplitudes (the NP-per-insertion convention) is coupling-order/eft's slice;
  that the integrator keys on the amplitude-level amp2 array (so amplitude presence, not the squared
  bin, governs the crash) is mine — confirmed by the amp2-fill site and the XTOT loop above.

## multi_channel=.false. bypasses all of this
`IF (MULTI_CHANNEL)` gates both the AMP2 zeroing (matrix_madevent_v4.inc:90-94) and the enhancement
(174-185). With `multi_channel=.false.` (the "Suppress amplitude" launcher answer routed through
get_user_params) ANS stays the full |M|²/IDEN with no per-channel reweight — the run integrates the
whole amplitude in one channel. See driver-and-channel-selection-sampling.md for where the flag is set.

## Grouped-subprocess selection — prepare_grouping_choice / select_grouping (auto_dsig.f)
Template `$MADGRAPH_INSTALL/madgraph/iolibs/template_files/super_auto_dsig_group_v4.inc`, generated
into `<P>/auto_dsig.f`. This is a SECOND, orthogonal selection: among the *subprocesses that share
one symmetry config* (the P<n> grouped directory lumps several initial states), pick which one this
event is.
- `prepare_grouping_choice(PP,WGT,INIT)` (super_auto_dsig_group_v4.inc:1) loops `SYMCONF`×`MAXSPROC`×
  mirror, calls `DSIGPROC(...,4)` to get each subprocess's **PDF-convoluted weight** `XSDUM`,
  accumulates `SELPROC(imirror,iproc,j)` and `SUMPROB` (lines 83-108). If `MC_GROUPED_SUBPROC`, each
  weight is also fed to the DiscreteSampler dimension `'PDF_convolution'` via `DS_ADD_ENTRY` (line 93).
- `select_grouping(imirror,iproc,iconf,wgt,IWARP)` (line 118) draws `RANMAR(R)`:
  - grid not yet initialized (`GROUPED_MC_GRID_STATUS==0`) or `.NOT.MC_GROUPED_SUBPROC`: pick by
    cumulative `SELPROC` (PDF-weighted), then **`WGT *= SUMPROB/SELPROC(imirror,iproc,iconf)`** to undo
    the selection bias (lines 186-212).
  - grid initialized: `DS_GET_POINT('grouped_processes',...)` draws from the learned grid and
    multiplies in `MC_GROUPED_PROC_JACOBIAN` instead (lines 214-222).
- `MAP_3_TO_1` / `MAP_1_TO_3` (lines 92,222) flatten the `(iconf,iproc,imirror)` triple to the single
  DiscreteSampler bin index. Probe: generated `auto_dsig.f` carries `TO_GROUPING_SELECTION`,
  `SELPROC(IMIRROR,IPROC,J)`, `TOTWGT=TOTWGT+SELPROC(K,I,J)` verbatim
  (`<PROC_DIR>/SubProcesses/P2_gg_ttx/auto_dsig.f:39,92,199`).

So there are TWO discrete selections per event in grouped output: (1) which **subprocess** within the
group — `select_grouping`, by PDF weight or `'grouped_processes'`/`'PDF_convolution'` grid; (2) which
**diagram channel** — the amp2 enhancement above plus the channel DiscreteSampler grid
(driver-and-channel-selection-sampling.md). Both reweight WGT to stay unbiased.

## select_color (super_auto_dsig_group_v4.inc:1087) — color-flow draw, not channel
`select_color(rcol,jamp2,iconfig,iproc,icol,ivec)` draws a color flow proportional to the `jamp2(i)`
color-decomposed squared amplitudes (cumulative `targetamp`, lines 1133-1154). Mentioned for
completeness: it is the *color* MC choice (for LesHouches color tags), not a phase-space channel —
out of slice detail, but it shares the cumulative-draw pattern.

## Cautions / boundaries
- AMP2 indices are diagram-numbered with gaps (4-vertex skip + grouped first-diagram keying); never
  assume `AMP2(c)` for config `c`. The enhancement uses `AMP2(MAPCONFIG(ICONFIG))` / `AMP2(CHANNEL)`
  precisely because the index is the diagram number, not the config index — same lesson as
  iconfig-channel-structure.md's MAPCONFIG-not-identity.
- The DiscreteSampler grids ('PDF_convolution'/'grouped_processes'/channel) tune *probabilities*; the
  amp2/XTOT factor is the *exact unbiasing weight*. Probabilities are numerical/VEGAS-adjacent but the
  selection scaffolding and the unbiasing weights are mine.
- `sde_strat`/`tmin_for_channel` come from common `/TO_CHANNEL_STRAT/` (run.inc:112). They originate
  in the run_card as `SDE_strategy` (banner.py:4458 — read default + allowed list;
  `fortran_name="sde_strat"`; strat 1 cites hep-ph/0208156, strat 2 = product of denominators) and
  `tmin_for_channel` (banner.py:4447, hidden — read default; validated negative at banner.py:4693-4697).
  The card-key *registration/validation* is the run-card slice's; the strat *semantics* (what 1 vs 2
  does to the amp2/XTOT weight) are mine, above.
