---
description: LO run_card scale parameters (fixed_ren/fac_scale, scale, dsqrt_q2fact1/2, dynamical_scale_choice, scalefact, EVA evaorder/eva_xcut/ievo_eva) — defaults + allowed values + the run-card-vs-source dynamical_scale_choice discrepancy.
---

# Scale parameters (RunCardLO.default_setup)

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py`, `RunCardLO.default_setup`.

## Fixed-scale switches
- `fixed_ren_scale` (:4257) default `False`.
- `fixed_fac_scale` (:4258) default `False`, hidden, `include=False`. Comment: define instead `fixed_fac_scale1/2` for per-beam choice.
- `fixed_fac_scale1`/`fixed_fac_scale2` (:4259-4260) default `False`, hidden.
- `fixed_extra_scale` (:4261) default `False`, hidden — the (non-QCD) extra running scale; in RUNNING block (banner.py :4011-4022). NOT in systematics.

## Scale values
- `scale` (:4262) default read at :4262, shortcut `{mz:91.188, mh:125.0, mt:173.0, mtau:1.77686}`. This is the fixed μR value.
- `dsqrt_q2fact1` (:4263) default read at :4263, `fortran_name=sf1`, same shortcuts. Fixed μF for beam 1.
- `dsqrt_q2fact2` (:4264) default read at :4264, `fortran_name=sf2`. Fixed μF for beam 2.
- `mue_ref_fixed` (:4265) default read at :4265, hidden (extra-scale fixed ref).
- `mue_over_ref` (:4270) default read at :4270, hidden (μ_other/μ ratio for dynamical extra scale).

INERT-AT-LO: `mue_ref_fixed`, `mue_over_ref`, `fixed_extra_scale` are declared in the runtime common block `/to_scale/` (Source/run.inc :7,:9,:15-17) but have NO consuming code anywhere in `Template/LO/` (grep across SubProcesses+Source finds only the run.inc declaration). They are the (non-QCD) second-running-scale knobs and only take effect for models with a separate running coupling, handled in the NLO/MadLoop machinery — Flavor-3 dead/inert at LO (see parser-vs-fortran-mismatch.md). Setting them in an LO run_card changes nothing.
NOTE: `alpsfact` (also in `/to_scale/`, used in reweight.f :43,:1601 as the αs-reweight multiplier) is the MATCHING slice's parameter (ickkw αs reweighting), not mine.

## dynamical_scale_choice
- `dynamical_scale_choice` (:4266) default read at :4266, allowed `[-1,0,1,2,3,4,10]`,
  shortcut `{ckkw:-1, ht:2, ht/2:3, et:1, shat:4}`.
- Comment: -1=CKKW back-clustering; 1=sum ET; 2=HT (sum transverse mass); 3=HT/2; 4=COM energy; 0=user_hook (custom_fct).

DISCREPANCY (carried from card): the allowed list includes `10`, and source-handled `5` (decay mass) is NOT in the list.
`setscales.f` set_ren_scale handles -1,0,1,2,3,4,5 and `else -> stop "Unknown option"`. So `=10` parses OK in the
run card but Fortran hits the `else` stop (PROBE-VERIFIED in 3.7.1 — surfaces as a misleading FileNotFoundError, see
scale-runtime-eval.md); `=5` is rejected by the run-card allowed list but the Fortran supports it.

## scalefact
- `scalefact` (:4283) default read at :4283. Applied as final multiplier in set_ren_scale: `rscale = scalefact*rscale` (setscales.f :93).
- LO-ONLY knob: `scalefact` lives in RunCardLO only. RunCardNLO has NO `scalefact`; the NLO scale multipliers are `mur_over_ref`/`muf_over_ref` (different names, different class — see lead runcard-lo-nlo-value-divergence). Confirmed: grep of RunCardNLO block finds no `scalefact` add_param. For interference-dominated σ, separate `scalefact`∈{0.5,1,2} runs is the LO manual-envelope path; the on-the-fly reweight multiplier is `sys_scalefact` (:4430, default "0.5 1 2", include=False/hidden) consumed by the Systematics module (systematics slice), distinct from `scalefact`.
- Commented-out coupling (banner.py :4539-4541): a dead block that would have forced `scalefact`→1 when `use_syst=T`. It is COMMENTED OUT — `scalefact` and on-the-fly systematics are NOT mutually reset in 3.7.1.

## Systematics consumption of these params (dynamical_scale_choice / scalefact)
The Systematics module (systematics slice owns the flag parsing; I own what the integers MEAN) consumes my scale integers:
- `--dyn=VALS` maps to `dynamical_scale_choice` by IDENTITY — `Systematics.__init__` default `dyn=[-1,1,2,3,4]` (systematics.py:58), stored `self.dyn=[int(i) for i in dyn]` (:200). Doc default `-1,1,2,3,4` CONFIRMED = source default. Each value IS a `dynamical_scale_choice` integer fed to the runtime scale evaluator.
- `dyn=-1` is special-cased throughout systematics.py as "use the as-generated dyn scale, no relabel" (:500,:527,:629,:637,:677 skip when dyn==-1). The human-readable label map at :679/:761 is `{1:'sum pt',2:'HT',3:'HT/2',4:'sqrts'}` and the resume LaTeX map :583 covers only `{1,2,3,4}` — so passing `--dyn` a value outside {-1,1,2,3,4} (e.g. 0 or 10, both in the LO allowed run_card list) would KeyError in the label emit. The default set is exactly the labelled set.
- LO/NLO allowed-set divergence (both verified live): LO `dynamical_scale_choice` allowed `[-1,0,1,2,3,4,10]` (banner.py:4267); NLO allowed `[-2,-1,0,1,2,3,10]` (banner.py:5680, default read at :5680 — a LIST not a scalar, fortran_name `dyn_scale`). So `=4` (√ŝ/COM) is LO-only, `=-2` NLO-only, `=10` in both lists but LO setscales.f runtime-stops (see scale-runtime-eval). The systematics default `--dyn` includes 4 — LO-consistent; at NLO the reweighting computes scales in its own machinery (systematics slice) rather than via the run_card allowed-list gate.

## PDF error-set reweighting (claim 2) — boundary
From my slice: the generation PDF is fixed by `pdlabel`+`lhaid`; `lhaid` is consumed ONLY in `pdlabel=='lhapdf'` mode (see lhaid-is-not-the-active-pdf lesson, lo-vs-nlo-pdf-default). A bundled pdlabel (nn23lo1) exposes NO LHAPDF error members. The error-member ENUMERATION and Hessian-vs-MC-replica COMBINATION are NOT in my slice: systematics.py delegates to LHAPDF's `pdfset.uncertainty(values)` (systematics.py:576), which internally handles `errorType` (hessian/symmhessian/replicas); `errorType=='unknown'` is skipped (:570). `--pdf=errorset` default (systematics.py:57,:239) enumerates every member of the generation `lhaid` set. Requires lhapdf6. → hand off error-set/Hessian-vs-MC to systematics slice; my contribution is only the central-PDF identity.

## EVA-specific (eva_pdf block, displayed only when active)
- `ievo_eva` (:4271) default read at :4271, allowed `[0,1]`. 0 = μf evolution by q^2; 1 = by pT^2.
- `evaorder` (:4273) default read at :4273, allowed `[0,1,2]`. 0=EVA(LLA), 1=iEVA(full LP), 2=iEVA@nlp [2502.07878].
- `eva_xcut` (:4275) default read at :4275, allowed `[0,1]`. 1 = impose ξ>MV/Ebeam (recovers 2502.07878); 0 = no restriction (recovers 2111.02442).
- Block template at banner.py :3970-3979.

## EVA runtime (ievo_eva/evaorder/eva_xcut carried into Fortran)
The three switches enter Fortran via `common/to_eva/ievo_eva,evaorder,eva_xcut` (ElectroweakFluxDriver.f). Runtime dispatch is in pdg2pdf.f (see runtime-pdf-dispatch page):
- EVA flux is only defined for produced bosons `|ipart|∈{7(γ),23(Z),24(W)}` (else `stop 1`) and only for `|lpp/ih|∈{3(e),4(mu)}` beams (else `stop 24`).
- `fLPol = pol(beamid)` — the fermion-polarization fraction comes from `polbeam1/2` (see beam-pdf-params); unpolarized fLpol=0.5 corresponds to pol left at default.
- helicity spin-average is undone via `helMulti` multiplier; q2max=μF^2 (the factorization scale).
