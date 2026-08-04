---
description: gen_mom's initial-state half — the x1/x2/tau/eta sampling + s(-nbranch)=shat + cm_rap + flux assembly across the five beam regimes (pp GENCMS, dressed-ee/ISR, lpp==9 dummy, single-beam, no-PDF fixed). The integration-var->incoming-momenta side of x_to_f_arg.
---

# Beam x1/x2, s-hat, rapidity, and the flux factor (gen_mom initial-state block)

`genps-momentum-generation.md` documents `gen_mom`'s FINAL-STATE half (one_tree forest
decomposition, get_channel_cut, map_invarients). This page owns the INITIAL-STATE half:
how the last 1-2 integration variables become the parton momentum fractions `xbk(1),xbk(2)`,
the partonic `s(-nbranch)=shat`, the CM rapidity `cm_rap`, and the overall `flux`.
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/genps.f`, inside `gen_mom` (genps.f:68), block
genps.f:246-444. All five branches gate on `lpp(1)/lpp(2)` (beam-particle codes from run_card)
and `pdlabel`.

## ndim accounting (genps.f:233-236)
`ndim = 3*nfinal-4` (floored at 0 for 2->1), then `+1` for EACH beam with `abs(lpp).ge.1`.
So a standard pp run (both lpp!=0) reserves the TOP TWO integration vars `x(ndim),x(ndim-1)` for
the initial state; a single-PDF beam reserves only `x(ndim)`; a no-PDF run (lpp==0 both) reserves
none. These are the vars the block below consumes.

## The five beam regimes (mutually exclusive if/elseif chain)
Each sets `xbk(1)`, `xbk(2)`, `s(-nbranch)` (= shat), and `cm_rap`; `sjac` accumulates the
sampling jacobian.

1. **Two-beam standard pp** — `abs(lpp(1)).ge.1 .and. abs(lpp(2)).ge.1` (genps.f:252), the
   non-9 / non-dressed sub-branch (genps.f:330-349):
   - `sample_get_x` draws `x(ndim-1)` (->tau) and `x(ndim)` (->eta).
   - `CALL GENCMS(STOT,Xbk(1),Xbk(2),X(ndim-1),SMIN,SJAC)` (genps.f:342). **GENCMS (genps.f:1621)**
     maps `X(1)->TAU=x1*x2` linearly in `[TAUMIN=0, TAUMAX]` (TAUMAX = `dsqrt_shatmax**2/S` if the
     run_card cap is set, else 1; genps.f:1659-1664), then `X(2)->ETA=.5*log(x1/x2)` linearly in
     `[.5*log(tau), -.5*log(tau)]`; finally `X1=sqrt(tau)*exp(eta)`, `X2=sqrt(tau)*exp(-eta)`
     (genps.f:1665-1681). Jacobian `*= (TAUMAX-TAUMIN)*(ETAMAX-ETAMIN)` (genps.f:1666,1678).
   - **2->1 trap**: if `nexternal.eq.3`, tau is FIXED to `pmass(3)^2/stot` and `sjac=1/stot` for the
     d_tau delta function (genps.f:336-339); `x(ndim-1)` is saved/restored around the GENCMS call
     (`xtau`, genps.f:335,343).
   - `cm_rap=.5*log(xbk(1)*ebeam(1)/(xbk(2)*ebeam(2)))`, `s(-nbranch)=xbk(1)*xbk(2)*stot`
     (genps.f:345-348).
   - NOTE the s-hat BW: GENCMS does NOT itself apply an s-channel pole to tau (the commented
     TRANSPOLE at genps.f:1653-1655 is disabled). The s-hat Breit-Wigner, when one is wanted, is
     installed by `set_peaks` onto the s-hat variable instead ("Setting PDF BW", myamp.f:430-442;
     see propagator-mappings-gen_s-transpole.md). GENCMS is the flat tau/eta fallback.

2. **dressed-ee / ISR / beamstrahlung** — same outer two-beam guard but `pdlabel.eq.'dressed'`
   (genps.f:263-327). The Bjorken x's are generated DIRECTLY (x1,x2 first), not via tau/eta:
   - DiscreteSampler dimension `'ee_mc'` picks `ee_picked` (1 or 2) when an s-hat resonance is
     present (`spole(ndim-1)>0 .and. swidth(ndim-1)>0`), via `DS_get_point('ee_mc',...)`
     (genps.f:264-271); else `ee_picked=1`.
   - `ee_picked==2`: resonance path — uses `GENCMS_EE` (genps.f:1685), which picks tau and ONE
     Bjorken x (genps.f:282).
   - `ee_picked==1` (default): `generate_x_ee` (genps.f:2006) draws each x with importance sampling
     `x = 1 - rnd^(1/(1-expo))` from `xmin` to 1, jac `*= 1/(1-expo)*(1-xmin)^(1-expo)`
     (genps.f:2023,2033-2037). `expo=get_ee_expo()` (HARDWIRED, read the `parameter (expo=...)` at
     `Source/PDF/pdg2pdf.f:307`) — the soft `(1-x)^{-expo}` ISR enhancement. Then `get_y_from_x12` (genps.f:1961) recomputes
     `cm_rap` from x1,x2 with Taylor-expanded logs near x->1 for numerical stability
     (genps.f:1974-1992).
   - A multichannel mix weight blends the flat-vs-resonant tau samplings:
     `sjac *= t1/(t1+t2)` or `t2/(t1+t2)` where `t1=(1-x1*x2)^(1-2*expo)` and
     `t2=1/((x1*x2-tau_m)^2+tau_m*tau_w)` (genps.f:312-327).
   - `s(-nbranch)=x1_ee*x2_ee*stot`. **This is the only regime where the s-hat variable carries a BW
     drawn through a DiscreteSampler dimension I own (`ee_mc`)** — contrast the pp s-hat BW which is a
     set_peaks transpole map.

3. **lpp==9 dummy-PDF, two-beam** — `abs(lpp(1)).eq.9 .or. abs(lpp(2)).eq.9` inside the two-beam
   guard (genps.f:253-260): `get_dummy_x1_x2(sjac, Xbk(1), x(ndim-1), pi1, pi2, stot, s(-nbranch))`
   (`SubProcesses/dummy_fct.f:67`) — a user-overridable dummy beam-spectrum hook. `pi1/pi2` are the
   dummy incoming momenta used later for the initial-state legs.

4. **lpp==9 single-side dummy** — outer `elseif (lpp(1).eq.9.or.lpp(2).eq.9)` (genps.f:350-362):
   draws one var, `get_dummy_x1` (`dummy_fct.f:42`) for the dummy side, the other `xbk=1`.

5. **Single-PDF beam** — `abs(lpp(1)).ge.1` XOR `abs(lpp(2)).ge.1` (genps.f:363-383): draws ONE
   var `x(ndim)` as that beam's `xbk`; the other beam is `xbk=1` (a lepton/fixed beam). `cm_rap` is
   built from the asymmetric `p0/p3` of the boosted system (genps.f:367-369 / 378-380);
   `s(-nbranch)=x(ndim)*stot`.

6. **No PDF (both lpp==0)** — `else` (genps.f:384-391): `xbk(1)=xbk(2)=1`, `s(-nbranch)=stot`
   (FIXED collider energy, e.g. fixed e+e-), `cm_rap` from the static beam energies.

After the chain: `m(-nbranch)=sqrt(s(-nbranch))`, and the -nbranch "system" 4-vector is set at rest
`p(:,-nbranch)=(m,0,0,0)` (genps.f:394-398). `set_cm_rap` is a one-shot latch so cm_rap is computed
once per point (used by the `rap()` cut function downstream).

## Initial-state leg momenta (genps.f:403-417)
- lpp==9: `mom2cx` (a HELAS back-to-back 2-body builder) if `dummy_boostframe()`, else literally the
  dummy `pi1/pi2`.
- `nincoming.eq.2`: `mom2cx(m(-nbranch),m(1),m(2),1d0,0d0,p(0,1),p(0,2))` — back-to-back incoming
  momenta in the partonic CM at cos=1,phi=0.
- decay (`nincoming==1`): leg 1 = the -nbranch system itself, with `p(3,1)=1e-14` planted to dodge a
  HELAS `ixxxxx` neg-mass branch (genps.f:413-416).

## The flux factor (genps.f:425-433) — assembled here, not in one_tree
After `one_tree` returns `jac>0`:
- `nincoming==2`: `flux = 1/(2*sqrt(LAMBDA(shat,m1^2,m2^2)))` — the 2->n Moller flux
  (`LAMBDA` = Kallen triangle function).
- decay (`nincoming==1`): `flux = 1/(2*sqrt(stot))` — the 1/(2M) decay normalization.
- Both then `flux /= (2*pi)^(3*nfinal-4)` — the per-final-state phase-space (2pi) factors.
- `pwgt(1)=max(sjac*jac*pswgt*wgt, 1d-99)`; final `wgt = pwgt(1)*flux`. So the returned event weight
  multiplies: the beam-sampling jac (`sjac`), the forest/one_tree jac (`jac`), the RAMBO-like
  `pswgt`, the incoming `wgt`, and `flux`.
- The Bjorken x's are stashed past the momenta: `p1(0,nparticles+1)=xbk(1)`,
  `p1(1,nparticles+1)=xbk(2)` (genps.f:440-441) — this is how PDF reweighting downstream recovers x1,x2.
- `jac<=0` (one_tree rejected the point): the whole event is flagged dead via `p1(0,1)=-99`
  (genps.f:442-443).

## Cautions
- The big `if (.false.) then ... endif` block from genps.f:449 onward is DEAD CODE (legacy
  re-determination loop); the live path ends at genps.f:444. Don't cite anything inside the
  `.false.` guard as runtime behavior.
- `dsqrt_shatmax` (run_card `dsqrt_shat`) caps tau via TAUMAX in GENCMS AND smax in gen_s — same cap,
  two sites (see propagator-mappings-gen_s-transpole.md and genps-momentum-generation.md). The actual
  run_card key registration is the run-card slice's; I own its effect on the tau/smax range here.
- `get_ee_expo()` is HARDWIRED in `pdg2pdf.f:307` (`parameter (expo=...)`; returned at :308 — read the
  literal there) — it is NOT a run_card knob. A claim that the ISR/dressed sampling exponent is
  user-tunable is wrong at the LO source level; it is a fixed importance-sampling exponent.
  - The lhapdf6 build does NOT carry this value: `Source/PDF/pdg2pdf_lhapdf6.f:244-251` is a `stop 21`
    STUB that returns nothing. So the dressed-ee / ISR sampling path (regime 2, which calls
    `get_ee_expo()` at genps.f:315 and inside `generate_x_ee`/`GENCMS_EE`) is an INTERNAL-PDF-only
    feature at the source level — built against lhapdf6 it would `stop 21` if that path is reached.
    (Earlier wording claimed the lhapdf6 copy also hardwires the same exponent — that is wrong; it aborts.)
- VEGAS draws the raw x's via `sample_get_x`; the bin layout / point budget is the numerical/VEGAS
  slice. I own how those x's are MAPPED to x1/x2/tau/shat/cm_rap and the flux assembly, not the
  sampler internals.
- The `ee_mc` DiscreteSampler dimension's add/update lifecycle lives in `Source/dsample.f:1142,1613-
  1664`; the per-event draw I cite is genps.f:267. The grid-tuning is numerical/VEGAS-adjacent; the
  draw->ee_picked->x-generation mapping is mine.
