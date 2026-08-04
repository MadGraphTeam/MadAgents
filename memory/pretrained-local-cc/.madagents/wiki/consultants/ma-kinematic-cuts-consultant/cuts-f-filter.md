---
description: cuts.f PASSCUTS filter sequence and pass_point — NaN/shat/pt/eta/DR/mass/HT/photon-iso order, CUTSDONE memoisation, dummy_cuts hook
---

# cuts.f — PASSCUTS filter sequence

Source: `$MADGRAPH_INSTALL/Template/LO/SubProcesses/cuts.f` (1732 lines, v3.7.1).
Per-process copy lives at `<PROC_DIR>/SubProcesses/cuts.f`; reads runtime values from
`run.inc` (+ `cuts.inc`). The actual run-card->Fortran VALUE mapping happens in
setcuts.f (see "Mapping layer" below), NOT in cuts.f.

## pass_point (:1)
`pass_point = .true.` unconditionally (:20); the `passcuts(p)` call is commented out (:21).
=> Cuts are NOT applied at the sampling/phase-space-point stage; they run later via
PASSCUTS. Pretraining intuition that cuts gate sampling is wrong here.

## PASSCUTS(P, VECSIZE_USED) (:24)
Momenta are in the parton CM rest frame (:30). Memoised: `CUTSDONE/CUTSPASSED`
common block (:159-161). On entry if CUTSDONE return cached CUTSPASSED (:282); else
set CUTSDONE=.true. (:286). FIRSTTIME block (:207-280): calls `initcluster()` (:210),
sets G if fixed_ren_scale (:266-271), AND prints the per-process CUT TABLE — the verbatim
lines probes observe: `Particle` header (:214), `Et >`(etmin) (:216), `E >`(emin) (:217),
`Eta <`(etamax) (:218), `xqcut:`(xqcuti) (:219), `d R #j >`(r2min) (:222), `s min #j>`(s_min)
(:230), `xqcutij #j>`(xqcutij) (:234). **At :225-226 it SQUARES r2min/r2max in place**
(`r2min=r2min*dabs(r2min)`) because the DR filter compares distance-SQUARED (see step 11).
So a run-card `drjj` becomes r2min, then r2min² here, compared against ΔR². (This is
why the `Et >`/`d R #` lines in probe logs match the card values — they print BEFORE the
square for d R, but the Et/Eta/s-min lines print the enforced values directly.)

Filter order (each fails fast with passcuts=.false.;return):
1. :292 `p(0,1) <= 0` reject (bad energy).
2. :298 NaN/Inf guard: any `p(j,i) > 1d32` or `p!=p` reject.
3. :310 dsqrt_shat: if nincoming==2 and (`dsqrt_shat != 0` or `dsqrt_shatmax != -1`),
   compute shat = sumdot(p1,p2); reject if shat < dsqrt_shat^2 or > dsqrt_shatmax^2.
4. :322 `$B$ DESACTIVATE_CUT $E$` MadWeight tag (selectively disables what follows).
5. :330 per-particle pt: reject if pt < etmin(i) or (etmax>=0 and pt > etmax(i)).
6. :351 missing-Et: vector-sum nu momenta -> ptemp; reject if pt < misset or > missetmax.
   Also sums lepton momenta -> ptemp2.
7. :379 `mmnl`/`mmnlmax`: invariant mass of (nu-system + lepton-system).
8. :390 `ptheavy`: if >0, require AT LEAST ONE is_heavy particle with pt > ptheavy
   (OR logic: passcuts set true if any heavy passes; only enforced if a heavy exists).
9. :411 per-particle E: reject if p(0,i) <= emin(i) or > emax(i).
10. :424 rapidity: reject if |rap| > etamax(i) or < etamin(i).
11. :437 DR (pairwise): if r2min/r2max set, reject on `r2(i,j)` (=ΔR², :442) out of
    [r2min,r2max] — where r2min/r2max were PRE-SQUARED at FIRSTTIME (:225-226), so the
    comparison is ΔR² vs (drXY)². Per-pair value selected by pair-type in setcuts.f (Mapping layer).
12. :457 ptll (pairwise pt of 4-mom sum): ptll_min/ptll_max.
13. :480 invariant mass (pairwise s = SumDot): s_min/s_max; supports inverted window
    (s_min>s_max => veto INSIDE the window, :494).
14. :505 `$B$DESACTIVATE_BW_CUT$B$` ... BW cut via cut_bw(p) (:509). [BW = bw-window slice.]
14b. Merging-shape cuts (:542-:808) over `is_pdg_for_merging_cut` particles (NOT all jets;
    the merging-cut PDG set, from_decay excluded). Two sub-blocks, each a fast-fail veto:
    - `KT_DURHAM > 0` (:542-625): builds a Durham kT measure. e+e- (LPP==0): kt=
      sqrt(2*min(E_i²,E_j²)*(1-cosθ)) (:605). Hadronic: FastJet def
      kt=sqrt(min(pt_i²,pt_j²)*((Δη)²+(Δφ)²)/D_PARAMETER²) (:608, D_PARAMETER=`dparameter`,
      run_card default at banner.py:4421). Also each jet's pt-vs-beam. Veto if min measure < ktdurham (:618).
      Needs NJETS>0 AND >=1 massless(jet/b) (:572) — won't fire on a single massive FS.
    - `PT_LUND > 0` (:631-808): Pythia pt-separation via `RHOPYTHIA` (ISR off each beam +
      FSR jet-jet with initial spectator). Veto if min separation < ptlund (:801). Special
      2-massless-FS case uses min pt-vs-beam (:672-688). BSM (|flav|>30 / >1e6) excluded as
      shower emissions (:741,:764). [These are CKKW-L / shower-kt MERGING-scale cuts: the
      ENFORCEMENT is here (my slice), the matching SEMANTICS are matching slice. ktdurham/
      dparameter/ptlund registered at banner.py:4420-4422 (runcard-cut-params.md).]
15. jet/HT/ordered-pt/xptX blocks (:518-:1095, interleaved with 14b): sort jets/heavyjets
    by pt, apply htjmin/htjmax, ihtmin/ihtmax, ptj1min.., xptj/xpta/.., deltaeta/xetamin.
    Full detail (jetor AND/OR, staged HT, WBF goto-21 bypass): ordered-ht-wbf-cuts.md.
16. :1097 photon isolation (Frixione) — see "Photon isolation" below.
17. :1226 `dummy_cuts(P)` user/plugin hook (dummy_fct.f) — last gate. Default
    body returns `.true.` unconditionally (dummy_fct.f:37); user-editable. Receives
    rest-frame P plus the `TO_SPECISA` common block (is_a_j/is_a_b/is_a_a/is_a_l/
    is_a_nu/is_heavy/is_a_onium/do_cuts — the same classification arrays setcuts.f fills),
    so a custom cut can use the particle-type tags without re-deriving them.

## Photon isolation (:1097-:1220)
Active only if `ptgmin != 0` (:1104). Builds nQCD light partons (is_a_j), nph photons,
and (if isoEM) nem = photons+leptons. For each photon: reject if ptg < ptgmin (:1158);
then for partons within R0gamma, require running Et-sum <= chi_gamma_iso (:1176).
`chi_gamma_iso(dr,R0,xn,eps,ptg) = eps*ptg*((1-cos dr)/(1-cos R0))^|xn|`
(:1327, Eq.3.4 of hep-ph/9801442 — smooth Frixione cone). isoEM repeats vs EM (photon+lepton)
energy, dropping the photon itself (:1188). goto 444 if no photons.

## Mapping layer (setcuts.f) — where run-card values become Fortran cut arrays
Source: `$MADGRAPH_INSTALL/Template/LO/SubProcesses/setcuts.f`.
- :203 `do_cuts(i)=.false.` if `.not.cut_decays .and. from_decay(i)` (decay products skip cuts;
  `do i=` at :201, `do_cuts(i)=.true.` at :202, the from_decay override at :203). `from_decay`
  is populated by `check_decay` (:961-1003), called ONLY when cut_decays=False (:192-193), which
  tags gForceBW=1 propagators + daughters. cut_decays defaults False (banner.py:4306), so a
  COMMA/CHAIN decay (`p p > z, z > l+ l-`) silently drops ptl/etal/drll on the leptons while the
  ARROW form (`p p > z > l+ l-`, gForceBW=0) keeps them — set cut_decays=True to apply.
  Full mechanism + anchored σ (arrow 1131 / comma 2840 / comma+cut_decays=True 1123 pb):
  cut-decays-decay-product-exemption.md.
- :212 `pmass > 20 GeV` => do_cuts=.false. (NO cuts on top/W/Z/H). Neutrinos do_cuts=.false.
- :217 classification by maxjetflavor: |pdg| <= min(maxjetflavor,6) => is_a_j;
  maxjetflavor+1..5 => is_a_b. :225 gluon(21) always is_a_j. :233 photon(22) is_a_a.
  :235 nu(12/14/16) is_a_nu. :238 `pmass > 10 GeV` => is_heavy (target of ptheavy cut).
- **is_a_onium is DEAD code**: the quarkonium cut block (setcuts.f:308-:311, ptonium/
  etaonium -> etmin/etamax/SMIN) is entirely COMMENTED OUT, and is_a_onium is never set
  .true. in the active path. There is NO active quarkonium-specific cut at LO; the array
  survives only in the TO_SPECISA common block. Don't promise a ptonium cut from the run_card.
- merging-cut tag (setcuts.f:241-:249): sets `is_pdg_for_merging_cut(i)` when |pdg| matches
  an entry of `pdgs_for_merging_cut` AND `.not.from_decay(i)` (decay products excluded). This
  is the runtime consumer of run_card `pdgs_for_merging_cut` (matching/merging, not a kin cut).
- :272-:306 per-type etmin/etmax/emin/emax/etamax/etamin from ptj/ptl/ptb/pta etc.
  Photon (:300): `etmin = max(pta, ptgmin)` => ptgmin is the photon pt FLOOR even
  though check_validity zeroed pta when ptgmin>0.
- **Pairwise DR mapping by pair-type (:338-384)**: for each FS pair (i,j), `r2min(j,i)` is
  selected by the `is_a_X(i)`/`is_a_Y(j)` flags — `drjj` (j+j), `drbb`, `drll`, `draa`, and
  the MIXED pairs `drbj` (b+j), `draj` (a+j), `drjl` (l+j), `drab` (a+b), `drbl` (b+l),
  `dral` (a+l) at :351-362; `r2max` the same with the `*max` variants (:364-380). Guarded by
  `if(do_cuts(i).and.do_cuts(j))` (:344): a pair where EITHER is a >20 GeV resonance or a
  neutrino gets r2min=0 / r2max=-1 (no DR cut). So a mixed pair gets ITS OWN cut value, not
  drjj — e.g. a b+light-jet pair is governed by `drbj`, not `drjj`.
- **Pairwise mass mapping (:388-433)**, `s_min(j,i) = mm*dabs(mm)` (sign-PRESERVING square,
  so a NEGATIVE mm yields negative s_min -> inverted-window veto, cuts.f step 13):
  - `mmjj`/`mmaa`/`mmbb` on same-type pairs (:393-395), `s_max` the `*max` variants (:401-403).
  - **`mmll` ONLY on same-flavour OPPOSITE-SIGN lepton pairs** (:396-399): set only when
    `abs(idup(i))==abs(idup(j))` AND `idup(i)*idup(j)<0`. So mmll does NOT cut e+mu-, like-sign,
    or different-flavour pairs — only true SFOS l+l-. (mmllmax same, :404-407.)
  - **`mmnl` ONLY when EXACTLY 2 lepton/neutrino objects** (:412-433): if the FS has exactly 2
    is_a_l-or-is_a_nu particles, mmnl/mmnlmax are `max`/`min`-folded onto that pair's s_min/s_max
    (:424-425). With !=2 lepton/nu in the FS, mmnl is silently inert.
  - PDG mxx (:438-463): `s_min(j,i)=mxxmin4pdg(k)**2` per tracked PDG, same/anti restricted by
    `mxxpart_antipart` — pdg-cuts-and-smin.md §2; bypasses do_cuts.
- **Pairwise ptll mapping (:469-483)**: `ptll_min/max(j,i) = ptllmin/max*dabs(...)` set ONLY for
  (SFOS lepton pair) OR (lepton+neutrino) OR (two neutrinos) (:473-478). So `ptllmin` (pt of the
  pair 4-mom sum) covers l+l- (SFOS), l+nu, and nu+nu systems — NOT same-type jets/photons.
- :156-:189 xqcut>0 RUNTIME re-corrections (second layer after banner.py):
  - auto_ptj_mjj & ktscheme==1: `ptj = xqcut` (warn) ; else if ptj>xqcut: `ptj=0`.
  - auto_ptj_mjj: `mmjj = xqcut` (warn) ; else if mmjj>xqcut: `mmjj=0`.
  - drjj>0: `drjj=0` (warn) ; drjl>0: `drjl=0` (warn).
  So under matching, Fortran FORCES ptj=mmjj=xqcut even if banner.py left user values.

## Cautions
- Cuts deliberately skip heavy resonances (>20 GeV) and neutrinos AND (under default
  cut_decays=F) decay-product legs of a forced-BW/chain decay — e.g. ptl/etal/drll will
  NOT cut leptons from `p p > z, z > l+ l-` (comma form) though they DO on the arrow form
  `p p > z > l+ l-`. See cut-decays-decay-product-exemption.md. The "no cuts on >20 GeV"
  line means cutting a
  reconstructed Z/W/top/H directly via the GENERIC ptX cuts is impossible — use
  dsqrt_shat or the PDG-specific dict cuts (`pt_min_pdg`/`eta_*_pdg`/`mxx_min_pdg`).
  The PDG-specific cuts BYPASS do_cuts (setcuts.f:211-212, :318-335) and so DO fire on a
  >20 GeV state — that is the supported override. See pdg-cuts-and-smin.md.
- ptheavy is OR-logic across heavy particles and only fires if a heavy (>10 GeV) exists.
- The xqcut/auto_ptj_mjj/drjj corrections live in TWO places (banner.py + setcuts.f);
  the Fortran layer is authoritative at runtime and can override the written card values.
