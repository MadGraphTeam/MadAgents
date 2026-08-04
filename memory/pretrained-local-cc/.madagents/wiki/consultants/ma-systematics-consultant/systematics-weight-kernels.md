---
description: Systematics per-event weight kernels (get_lo_wgt/get_nlo_wgt) — dyn scale formulas (get_et/ht/sqrts_scale), ion-PDF scaling (get_pdfQ/get_pdfQ2), EVA muf-variation stripped-PDF machinery (calc_eva_*), and the getpdfQ latent bug.
---

# Systematics per-event weight kernels

`$MADGRAPH_INSTALL/madgraph/various/systematics.py`, v3.7.1. The numerical core *below* the `run()` loop and the banner/report layers: how one variation arg `(Dmur, Dmuf, Dalps, dyn, pdf)` becomes a weight for one event. `systematics-class` describes the constructor/detection and the 2-line algorithm summary; THIS page is the kernel detail (dyn scale formulas, ion-PDF scaling, EVA muf-variation). The ratio `event.wgt*wgts[i]/wgts[0]` and cross-section summing are in `parton-systematics-log-report`.

## dyn → scale, the actual functions (get_lo_wgt sys.py:946-958; get_nlo_wgt sys.py:1042-1049)
`dyn` selects the dynamical scale; the *computed quantity* (LO, called on the `event` object, lhe_parser.py):
- `dyn==1` → `event.get_et_scale(1.)` — Σ over final-state (status==1) of `E*pt/sqrt(pt**2+pz**2)` = **transverse energy E_T** (E·sinθ), only for pt>0 (lhe_parser.py:2858-2869).
- `dyn==2` → `event.get_ht_scale(1.)` — Σ `sqrt(m**2 + pt**2)` = **HT** (sum of transverse masses) (lhe_parser.py:2846-2855).
- `dyn==3` → `event.get_ht_scale(0.5)` — **HT/2**.
- `dyn==4` → `event.get_sqrts_scale(1.)` — `sqrt((p_init1+p_init2)**2)` = **√ŝ** (or init mass for 1→N) (lhe_parser.py:2875-2885).
- `dyn==-1` → use the **stored** scales from the event's `<mgrwt>` info (`loinfo['ren_scale']`, `pdf_q1/q2[-1]`), no recompute (sys.py:936-945).
- NaN scale → `get_lo_wgt` returns `mur` (NaN) early (sys.py:960-961); NLO floors `mur2 = max(1.0, scale**2)` for dyn 1/2/3 (1 GeV² floor), NOT for dyn 4 (sys.py:1043-1049).

**Label trap.** The dyn=1 description string written into the weight body and the per-arg table is `'sum pt'` (`get_wgt_info` sys.py:679, `print_cross_sections` sys.py:761), but the LaTeX name is `\sum ET` (sys.py:583) and the computed quantity is **Σ E_T (transverse energy)**, NOT sum-of-pt. Read dyn=1 as Σ E_T. (Other labels match: 2=HT, 3=HT/2, 4=sqrts.)

## LO weight assembly (get_lo_wgt, sys.py:931-1034)
For each arg, multiply contributions onto `wgt`:
- **αs(μR) factor** (sys.py:976-982): no-beam OR `pdlabel=='eva'` → `self.alpsrunner(Dmur*mur)**n_qcd`; else `pdf.alphasQ(Dmur*mur)**n_qcd`. (`n_qcd==0` → factor 1.)
- **PDF/μF factor per beam** (sys.py:985-1014): EVA beam → `get_eva_scale_wgt_by_vx(...)` (see below); else `get_pdfQ(pdf, b*pdg, x, Dmuf*muf, beam)`. Beam skipped if `b==0` or `muf==0` (elastic-photon guard).
- **αs-reweight (asrwt) loop** (sys.py:1016-1020): for clustering scales in `loinfo['asrwt']` — **BUG-ish**: in the no-beam/EVA branch it does `wgt = self.alpsrunner(Dalps*scale)` (plain ASSIGNMENT, overwriting accumulated wgt), vs `wgt *= pdf.alphasQ(...)` in the beam branch. Only bites the rare no-beam-with-asrwt case.
- **ALS (clustering μF) loop** (sys.py:1023-1031): for each of `n_pdfrw1/2 - 1` clustering steps, multiply by `get_pdfQ(...,scale)/get_pdfQ(...,next_scale)` at `scale = min(Dalps*pdf_q, Dmuf*muf)` — the MLM/CKKW αs-clustering PDF ratio.

## NLO weight assembly (get_nlo_wgt, sys.py:1036-1103)
`nloinfo = event.parse_nlo_weight(real_type=(1,11,12,13))`; sum over contribution-events (`cevent`) and their `onewgt`:
- `tmp = pwgt[0] + pwgt[1]*log(Dmur²·mur2/Q2) + pwgt[2]*log(Dmuf²·muf2/Q2)`, Q2 = `scales2[0]` = **Ellis-Sexton scale** (sys.py:1062,1069-1071).
- `tmp *= sqrt(4π·αs)**qcdpower` where αs from `alpsrunner` (no-beam) or `pdf.alphasQ2(Dmur²·mur2)` (sys.py:1073-1078).
- `tmp *= get_pdfQ2(beam1)·get_pdfQ2(beam2)` at `Dmuf²·muf2` (sys.py:1064-1067, 1091).
- dyn==-1 reads `mur2=scales2[1], muf2=scales2[2]` from the stored weight (sys.py:1059-1061).
- **nn23 zero-PDF workaround** (sys.py:1080-1089): if a PDF returns 0, for the nominal arg back-solve `wgtpdf = ref_wgt/tmp` and cache by `(pdg1,pdg2,x1,x2,muf2)`; reuse cached for variations; else genuine 0.
- **`-O` (not `__debug__`) nominal short-circuit** (sys.py:1055-1057): the nominal arg (`dyn==-1,Dmur==Dmuf==1,pdf==orig`) returns the stored `onewgt.ref_wgt` directly, skipping recompute.
- **`__debug__` (default) consistency assertion** (sys.py:1095-1101): in debug mode the nominal arg DOES recompute and cross-checks `misc.equal(tmp, ref_wgt, sig_fig=…)` (tolerance read at sys.py:1095-1101); mismatch → `raise Exception('not enough agreement between stored value and computed one')`. So a corrupt/inconsistent stored NLO weight is a HARD error in default (debug) mode but silently trusted under `-O`.

## Ion-PDF scaling (get_pdfQ sys.py:839-878; get_pdfQ2 sys.py:880-916)
`get_pdfQ` is the LO PDF accessor (xfxQ), `get_pdfQ2` the NLO accessor (xfxQ2, with a `self.pdfQ2` memo cache). Both apply the same heavy-ion scaling when `self.orig_ion_pdf and (self.ion_scaling or pdf.lhapdfID==orig_pdf)`:
- `nb_p = run_card['nb_proton<beam>']`, `nb_n = run_card['nb_neutron<beam>']`.
- For u/d (pdg 1,2 and antis): isospin mix `f = nb_p·pdf_pdg + nb_n·pdf_otherflavour` (proton↔neutron isospin: u in a proton = d in a neutron), then `f *= (nb_p+nb_n)` (sys.py:854-871).
- Other flavours: `f = (nb_p+nb_n)·xfx · (nb_p+nb_n)` (sys.py:868-871, the `(nb_p+nb_n)²` overall).
- Plain (non-ion): `f = pdf.xfxQ(pdg,x,scale)/x`.
- pdg in [-21,-22] → `abs` (gluon/photon sign-agnostic); pdg 0 → return 1 (sys.py:841-844).

**Ion detection is LO-ONLY** (sys.py:175-179): `orig_ion_pdf` is set True only inside the `RunCardLO` branch when any `nb_neutron1/2 != 0` or `nb_proton1/2 != 1`. The NLO branch (sys.py:180-183) NEVER sets `orig_ion_pdf` → ion scaling is inert for NLO systematics even though `get_pdfQ2` contains the code. (Correction to an earlier reading that cited sys.py:175-179 without the LO-only scoping.)

## EVA muf-variation (get_eva_* sys.py:1106-1311)
When a beam is EVA (`pdlabel`/`pdlabel1`/`pdlabel2 == 'eva'`), the μF variation of the Effective-Vector-boson-Approximation flux replaces the ordinary PDF factor. `get_eva_scale_wgt_by_vx(muf, vPID, fPID, vPol, xx, beam, ievo_eva, evaorder)` dispatches by vector-boson polarization `vPol` (event[0/1].helicity) and PID (event[0/1].pid):
- `vPol==0` (longitudinal) → `get_eva_stripped_pdf_v0`; `+1`→`_vp`; `-1`→`_vm` (sys.py:1106-1115). Photon (`vPID in [7,22]`) with vPol==0 → AssertionError (no longitudinal photon).
- **accuracy level `evaorder`** (run_card `evaorder`): 0=LLA (leading-log, default), 1=full-LP, 2=NLP (next-to-leading-power). Each `calc_eva_stripped_pdf_*_{lla,xlp,nlp}` returns the analytic μ-dependence (sys.py:1151-1273). Photon → only LLA supported regardless (sys.py:1120,1132).
- **`ievo_eva`** (run_card): 0 = evolve by q (mu2Min squared), 1 = evolve by pT (`(1-xx)·mu2Min²`) (sys.py:1198-1200). `ievo_eva != 0` with >1 x-value in pdfrwt → `SystematicsError('too many x1/x2 in pdfrwt ... for EVA')` (sys.py:992,1007).
- Mass lookups (must match `ElectroweakFlux.inc`): `get_eva_mf_by_PID` (fermion masses, sys.py:1284-1296), `get_eva_mv_by_PID` (V masses — γ/γ_KK (pid 7,22) = 0, Z/W = hardcoded EW-boson-mass literals; read the values fresh at sys.py:1298-1305, they are source constants that can drift per version), `get_eva_mufMin_byPID` (sys.py:1276-1282).
- Only applied for `abs(vPID) in [7,22,23,24]` (γ_KK, γ, Z, W) (sys.py:995,1010).

## getpdfQ latent bug (sys.py:847)
On the `only_beam` PDF-variation path, sys.py:847 calls `self.getpdfQ(...)` (no underscore) — a method that **does not exist** on the class (only `get_pdfQ`/`get_pdfQ2`). Probe-confirmed: `hasattr(Systematics,'getpdfQ')` is False. So `only_beam` set + a PDF-variation member ≠ orig_pdf for the non-named beam → **AttributeError at runtime**. Narrow path (`only_beam` is API/subprocess-only, see `fail-soft-vs-fail-hard` whitelist trap), but it is a live bug, not a fallback.

## Cautions
- dyn=1 is Σ E_T (transverse energy), not Σ pt, despite the `'sum pt'` label string.
- Ion-PDF scaling code runs only for LO (`orig_ion_pdf` LO-only); NLO ion systematics get no nuclear scaling.
- NLO stored-weight consistency is asserted (`raise`) only under `__debug__`; `-O` (multicore subprocess runs with `-O` when `not __debug__`) silently trusts `ref_wgt`.
- `only_beam` + non-orig PDF on the other beam → AttributeError (`getpdfQ` typo), not a graceful fallback.
- asrwt no-beam branch overwrites `wgt` (assignment bug) — affects only no-beam events carrying clustering asrwt scales.
- RUNTIME claims (the AttributeError firing, EVA flux numerical values) beyond the parse-time `hasattr` probe are read from source — a real EVA/ion systematics run would confirm emitted weights.
