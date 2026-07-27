---
description: Runtime scale evaluation in LO templates — setscales.f set_ren_scale / set_fac_scale dynamical branches, reweight.f fixed-vs-dynamical application loop, and the dynamical_scale_choice=10 stop trap.
---

# Runtime scale evaluation (LO)

## set_ren_scale (setscales.f :1-95)
Branches on `dynamical_scale_choice` (returns `rscale`, the dynamical μR before scalefact):
- `-1` (:46-49): CKKW back-clustering; `rscale=0d0` here — the real μR/μF are computed later in `setclscales` (reweight.f) from clustered pt²/mT² via geometric means, NOT in this file. See ckkw-clustering-scale-resolution.md for the full deferred path (incl. the :643 early-return gate that makes "dsc=-1 → clustering scale" real).
- `1` (:50-55): sum of ET over final states i=3..nexternal.
- `2` (:56-63): sum of transverse mass sqrt((E+pz)(E-pz)) over final states (HT).
- `3` (:64-71): same sum / 2 (HT/2).
- `4` (:72-74): sqrt(shat) = sqrt(sumdot(p1,p2)) — partonic COM energy.
- `5` (:75-77): sqrt(dot(P1,P1)) — decaying-particle mass (for decays). SOURCE-HANDLED but NOT in run-card allowed list `[-1,0,1,2,3,4,10]`.
- `0` (:78-88): user-defined, `rscale = user_dynamical_scale(P)` (dummy_fct.f / custom_fct).
- `else` (:89-92): `write 'Unknown option in scale_global_reference' ; stop`.
- Final (:93): `rscale = scalefact*rscale`.

TRAP: `dynamical_scale_choice=10` is in the run-card allowed list (banner.py :4267) but `setscales.f` has NO `=10` branch
-> falls to `else` -> runtime `stop`. PROBE-VERIFIED (MG 3.7.1, `p p > t t~, t > b w+, w+ > e+ ve`, dsc=10, 100 evts):
set_ren_scale prints `Unknown option in scale_global_reference          10` and the Fortran job stops. The survey job
then produces no `results.dat`, and the Python layer surfaces this as a MISLEADING `FileNotFoundError` bug-report
(`.../G1/results.dat` missing + "Please report this bug on launchpad"), NOT a clean invalid-scale error. The real
stop message is only visible in `SubProcesses/P*/G*/log.txt` (e.g. `:147` of G1 log). So a user who sets dsc=10 sees a
spurious bug-report, not a scale diagnostic — check the G*/log.txt when this FileNotFoundError appears at survey/refine.

## set_fac_scale (setscales.f :98-193)
- `-1` (:133-137): set q2factorization(1/2)=0d0 unless fixed_fac_scaleN (real μF from clustering).
- `0` (:138-148): user-defined; default body calls `set_ren_scale` and uses tempscale^2 for the non-fixed beams.
- `else` (:182-186): calls `set_ren_scale(P,tempscale)` and sets q2factorization(N)=tempscale^2 for non-fixed beams.
  => for choices 1,2,3,4 the factorization scale DEFERS to the renormalization scale by default.

## Application loop (reweight.f :1890-1933)
- If `.not.fixed_ren_scale`: zero `scale`, call `set_ren_scale`, then `G=SQRT(4*PI*ALPHAS(scale))`, store `all_scale(i)` (:1890-1901).
  If `fixed_ren_scale=.true.`, `scale` keeps its run-card `scale` value (μR fixed) — set_ren_scale is skipped.
- If `.not.fixed_fac_scale1 .or. .not.fixed_fac_scale2`: call `set_fac_scale` (:1903-1905). Fixed beams keep dsqrt_q2factN^2.
- `setclscales` then applies clustering/PDF reweighting; stores all_q2fact(1/2,i) (:1907-1913).
- update_as_param(i) re-evaluates couplings at the new scale (:1918-1926).

initcluster.f :28 short-circuit: clustering skipped entirely when `ickkw<=0 .and. xqcut<=0 .and. fixed_ren_scale .and. fixed_fac_scale1 .and. fixed_fac_scale2` (fully-fixed-scale fixed-order run).
