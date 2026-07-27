---
description: How dynamical_scale_choice=-1 (CKKW) renorm/fact scales are actually computed in setclscales (reweight.f) from clustered pt2 — the path scale-runtime-eval.md deferred as "set later".
---

# CKKW (dynamical_scale_choice=-1) scale resolution

`set_ren_scale`/`set_fac_scale` (setscales.f) for `dynamical_scale_choice=-1` set `rscale=0d0` / `q2factorization=0d0` (scale-runtime-eval.md). The REAL μR/μF for CKKW are then computed in `setclscales` from the clustered pt² values. This page walks that deferred computation.

Source: `$MADGRAPH_INSTALL/Template/LO/SubProcesses/reweight.f`, `logical function setclscales(p, keepq2bck, ivec)` (def :555).

## Early-return short-circuit (:643)
```
if(ickkw.le.0 .and. (xqcut.le.0d0.or.init_mode) .and. q2fact(1).gt.0 .and. q2fact(2).gt.0 .and. scale.gt.0) return
```
So clustering does NO scale work when scale and both q2fact are already positive (non-CKKW dynamical choices 1-4, or fixed scales — set upstream by set_ren/fac_scale). It proceeds to cluster + set scales only when `scale==0 .or. q2fact==0` (the dsc=-1 case where setscales.f left them zero) OR `ickkw>0` OR `xqcut>0`. This is the runtime gate that makes "dsc=-1 = clustering scale" real.

There is a second short-circuit at :1104 (`if(ickkw.eq.0 .and. (fixed_fac_scale1.or.q2fact(1)>0) .and. (fixed_fac_scale2.or.q2fact(2)>0) .and. (fixed_ren_scale.or.scale>0)) return`) — bails after the xqcut/xmtc cuts but before scale-setting if all scales are already fixed/set.

## Clustering (:666)
`clustered = cluster(p(0,1), ivec)` (cluster.f) builds the kt-clustering tree; `pt2ijcl(n)` = the pt² at clustering vertex n; `jcentral(1/2)`, `jlast(1/2)`, `jfirst(1/2)` index the central / last / first relevant vertices per beam side. Central vertices get mT² (transverse mass) instead of pt² (:1047-1055).

## Factorization scale (:1126-1146)
When `q2fact(1)==0 .or. q2fact(2)==0`:
- geom. average of jlast and jcentral pt²: `q2fact(i) = sqrt(pt2ijcl(jlast(i))*pt2ijcl(jcentral(i)))` (:1128-1129), per beam, only if `.not.fixed_fac_scaleN`.
- if a single QCD line runs through the whole event (`jcentral(1)==jcentral(2)`), uses one scale `max(q2fact1,q2fact2)` for both (:1135-1138).
- `scalefact` enters as **`scalefact**2 * q2fact`** (:1139-1140) — note SQUARED because q2fact is a scale².
- result cached into `q2bck(1/2)` unless `keepq2bck` (:1141-1143).
- Special cases when jcentral is 0 (:1178-1190): falls back to `scalefact**2*pt2ijcl(jfirst)` or `pt2ijcl(nexternal-2)`.

## Renormalization scale (:1150-1176)
When `scale==0d0`:
- both beams have a last vertex: `scale = (pt2_jlast1 * pt2_jcentral1 * pt2_jlast2 * pt2_jcentral2)**0.125` — 8th-root = geom. mean of four pt² (:1153-1156).
- one beam: `(pt2_jlast * pt2_jcentral)**0.25` — 4th-root (:1158-1163).
- only central vertices: `(pt2_jcentral1*pt2_jcentral2)**0.25` or `sqrt(pt2_jcentral)` (:1164-1170).
- fallback: `scale = sqrt(pt2ijcl(nexternal-2))` (:1170).
- then `scale = scalefact*scale` (:1171) — note NOT squared (scale is a scale, not scale²), unlike q2fact.
- `G = SQRT(4d0*PI*ALPHAS(scale))` (:1173) — αs re-evaluated at the clustered ren scale, strong coupling reset.

## scalefact asymmetry (trap)
`scalefact` multiplies the renormalization scale linearly (`scalefact*scale`, :1171) but the factorization scale² as `scalefact**2*q2fact` (:1139-1140). Both end up linear in the physical scale (since q2fact is a scale²), consistent — but when reading source the squared form on the fact side can mislead.

## myamp.f grid interaction (:546)
`dynscale_cut = (dynamical_scale_choice.eq.-1 .and. .not.(FIXED_REN_SCALE.and.FIXED_FAC_SCALE1.and.FIXED_FAC_SCALE2))`. When set, the phase-space grid uses a different shat lower bound (`xo=max(4/stot, Smin/stot)` or `4/stot`) than the non-CKKW path. So choosing dsc=-1 (without fully fixing scales) also shifts the integration grid's minimum shat. The grid mechanics are the phase-space slice's territory; the *trigger condition* (dsc=-1) is ours — flag, don't own.

## Caution
- The "dsc=-1 = CKKW" label in the run card does NOT mean a fixed formula: the scale is event-by-event the geometric mean of clustering pt²/mT² values. For a process with no QCD radiation / no clusterable jets, jcentral/jlast may be 0 and the scale falls back to `pt2ijcl(nexternal-2)` — verify per process, not from the label.
- This whole path is bypassed (early-return :643) for dsc=1-4 and fixed scales — those never touch clustering. Don't attribute clustering-scale behavior to a non-CKKW dynamical choice.
