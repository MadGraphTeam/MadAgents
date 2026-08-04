---
description: FxFx/UNLOPS/jet-veto generation-side Fortran — the ickkw merging-scale cut (passcuts_fxfx, passcuts_unlops_jv) and the ickkw-driven dynamical-scale branches, in cuts.f / setscales.f of the NLO template.
---

# FxFx / UNLOPS / jet-veto: generation-side Fortran (NLO template)

The Python-side `ickkw` (3=FxFx, 4=UNLOPS, -1=jet-veto) and its auto-corrections
are on the `nlo-ickkw-fxfx` page. THIS page is the **Fortran counterpart**: how
`ickkw` is consumed at event-generation time inside the matrix-element directory
to (a) apply the merging-scale cut and (b) drive the dynamical scale. This is why
the Python auto-correction forces `dynamical_scale_choice=[-1]` — that value
routes to these branches.

All cites `$MADGRAPH_INSTALL/Template/NLO/SubProcesses/` (cuts.f, setscales.f),
which is generated source per ma-truth-sources.

## Cut dispatch by ickkw (cuts.f `passcuts_user`)
`cuts.f` (passcuts_user body @~85-116) routes by `ickkw` (from run.inc):
- `passcuts_unlops_jv(...)` @99 runs first — handles ickkw=4 (UNLOPS) and ickkw=-1 (jet-veto).
- @103-111: `if (ickkw.ne.3)` → `passcuts_jets(...)`; `else` (ickkw==3) → `passcuts_fxfx(...)`. So FxFx swaps out the ordinary jet cut for the FxFx merging-scale cut.

### `passcuts_fxfx` (cuts.f @448-485) — FxFx merging-scale cut at generation
"use the lowest clustering scale to apply the cut":
- Runs a kT-jet clustering (palg=1.0 kt, R=1.0, pTmin=`ptj`) via `amcatnlo_fastjetppgenkt_etamax_timed`.
- @475: stability cut — fail unless `njet == nQCD .or. njet == nQCD-1`.
- @480: the actual merging cut — fail if `minval(FxFx_ren_scales(0:nFxFx_ren_scales)) < ptj`. So **`ptj` (run-card) is the generation-side FxFx merging cut**, applied against the *lowest FKS clustering scale*, NOT against the shower-card Qcut. (The shower-card Qcut is the *Pythia8-side* matching scale; see shower-card-qcut. Two distinct scales: run-card `ptj` cuts the generation, shower-card `Qcut` cuts the shower.)
- `FxFx_ren_scales` / `nFxFx_ren_scales` live in `common/c_FxFx_scales/`, **filled in `fks_singular.f`** via `setclscales` (the FKS clustering/reweighting — NLO-FKS slice's territory, not asserted here). This page consumes the common block; it does not own its population.

### `passcuts_jets` (cuts.f @487-566) — non-FxFx jet cut, with ickkw=4 bypass
- @513: `if (ickkw.eq.4) return` — UNLOPS does NO ordinary jet cut here (it has its own, below).
- Otherwise the standard `ptj`/JETALGO/JETRADIUS fastjet cut: fail unless `njet == nQCD .or. njet == nQCD-1`.

### `passcuts_unlops_jv` (cuts.f @570-618) — UNLOPS and jet-veto cuts
- ickkw=4 (UNLOPS) and `ptj>0` @592: calls `pythia_UNLOPS(p_unlops, passUNLOPScuts)`. So **UNLOPS DOES have a generation-side Fortran cut** — `pythia_unlops.f` implements the theta-function structure `[B+V+∫R θ(ptj−d(φ_R))] θ(d(φ_B)−ptj)` (header of `pythia_unlops.f`), cutting on the first-cluster scale and simultaneously on the Born momentum.
- ickkw=-1 (jet-veto) and `ptj>0` @605: requires exactly one QCD parton (`nQCD.ne.1` → hard `stop`), then fail if `pt(pQCD(0,1)) > ptj` — the veto'ed cross-section cut for analytic NNLL resummation (arxiv:1412.8408).

### EW-jet exclusion from FxFx matching (cuts.f @435)
In the QCD-parton collection loop: `if (ickkw.eq.3 .and. need_matching_cuts(j).eq.-1) cycle ! skip the 'EW-jets'`. Jets flagged `need_matching_cuts==-1` are excluded from the FxFx clustering/cut. `need_matching_cuts` is set in `fks_singular.f` (FKS slice). This is the NLO analogue of the LO HEFT/hgg jet-flagging on heft-merging-jetflag — effective/EW-origin jets must not enter the matching.

## Dynamical scale by ickkw (setscales.f)
The Python force of `dynamical_scale_choice=[-1]` for FxFx and jet-veto exists
because these `ickkw` values select hard-coded scale branches in setscales.f:
- **FxFx (ickkw==3)** @250-270: scale = geometric-mean construction over `FxFx_ren_scales` — `tmp = (∏ FxFx_ren_scales(i))**(1/max(bpower,1))`, with a `bpower=born_orders(qcd_pos)/2` correction for Born αS powers; `temp_scale_id='FxFx merging scale'`. (Also fac-scale branch @425-428: `(FxFx_fac_scale(1)+FxFx_fac_scale(2))/2`.)
- **jet-veto (ickkw==-1)** @544-547: `tmp = ptj`, `temp_scale_id='NLO+NNLL veto scale: ptj_max'` — the veto scale IS ptj.

So forcing `dynamical_scale_choice=[-1]` (Python, nlo-ickkw-fxfx) is what lets these `ickkw`-branches take over the scale; a non-(-1) dynamical choice would conflict, which is exactly why the Python check overrides it.

## Cautions
- **Corrects the over-simple "UNLOPS has no MadGraph interface".** That is true only of the *Python merging driver* — there is no FxFx-style Python auto-config and no aMC@NLO showered-UNLOPS flow. But the **generation-side Fortran cut exists** (`passcuts_unlops_jv`→`pythia_UNLOPS`, ickkw=4). The user still does the final merging outside MadGraph, but MadGraph DOES apply the UNLOPS phase-space cut at generation. Don't tell a user "ickkw=4 does nothing in MadGraph".
- The FxFx generation cut is on **`ptj`** (run-card), against the lowest FKS clustering scale — distinct from the shower-card `Qcut` (Pythia8 matching scale). A user must set BOTH consistently; this page's `ptj` is the run-card knob, Qcut is shower-card.
- `FxFx_ren_scales` / `need_matching_cuts` are populated in `fks_singular.f` (NLO-FKS slice). This page owns their *consumption as matching cuts/scales*, not their derivation. Hand off questions about how the clustering scales are computed to the FKS slice.
- All static-source (generated Fortran). The runtime cut-efficiency / actual scale values are launch-time outputs — probe-candidates, not asserted here.
