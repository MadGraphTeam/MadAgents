---
description: PDG-specific dict cuts (pt_min_pdg/mxx_min_pdg/...) lowering + setcuts.f enforcement that BYPASSES the >20GeV do_cuts rule, plus the smin integration-floor derivation from cuts, grouped-subprocess consistency hard-abort, ERROR TRAPS, and setxqcuts forest mapping
---

# PDG-specific cuts, the smin integration floor, and subprocess-grouping consistency

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py` (RunCardLO) and
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/setcuts.f`. MG5_aMC v3.7.1.
This page covers the parts of setcuts.f beyond the per-type etmin/etmax mapping already in
cuts-f-filter.md: (1) PDG-specific cut lowering+enforcement, (2) the smin partonic-ŝ floor
the cuts feed to the integrator, (3) the grouped-subprocess consistency check, (4) ERROR
TRAPS, (5) setxqcuts. These are the cut layer's coupling into phase-space integration.

## 1. PDG-specific dict cuts — lowering (banner.py:4701)
`update_system_parameter_for_include` (:4701) turns the user-facing dict cuts
(`pt_min_pdg`, `pt_max_pdg`, `e_min_pdg`, `e_max_pdg`, `eta_min_pdg`, `eta_max_pdg`,
`mxx_min_pdg`, `mxx_only_part_antipart`) into flat Fortran arrays:
- :4708-4711 union of all dict keys -> `pdg_to_cut`; discards `__type__`/`default`.
- :4714 too many distinct PDGs -> `Exception("Maximum ... different pdgs...")` (read the cap literal at :4714).
- :4717-4719 any negative PDG -> warning + `MadGraph5Error` (cuts are symmetric on
  particle/antiparticle, so only positive codes allowed).
- :4722-4723 any PDG in `[1,2,3,4,5,21,22,11,13,15]` -> `Exception("Can not use PDG
  related cut for light quark/b quark/lepton/gluon/photon")`. So PDG cuts target ONLY
  heavy/exotic states (t=6, W=24, Z=23, H=25, BSM), never the light objects (those use
  ptj/ptb/pta/ptl). PROBE-CONFIRMED (v3.7.1): `pt_min_pdg {6:50}` on `p p > t t~` made the
  PASSCUTS cut table print `Et > 50.0 50.0` on the two tops (idx 3,4) — a pt cut applied to
  a pmass>20 GeV state the generic ptX cuts skip; confirms PDG cuts bypass do_cuts.
- :4725-4753 builds `ptmin4pdg`, `Emin4pdg`, `etamin4pdg` (+max), `mxxmin4pdg`,
  `mxxpart_antipart` arrays, one slot per tracked PDG, filling per-pdg value or the
  min=0./max=-1. default (:4742). `mxx_only_part_antipart` per-pdg or its `default` key
  (:4747-4753); missing default with missing pdg -> Exception.
- These land in `run.inc` common block `TO_PDG_SPECIFIC_CUT` (run.inc:103-104):
  `pdg_cut(0:25)`, `ptmin4pdg/ptmax4pdg/Emin4pdg/.../mxxmin4pdg(0:25)`,
  `mxxpart_antipart(1:25)`. `pdg_cut(0)` = count, `pdg_cut(1..)` = the PDG codes.

## 1b. Why generic ptX/etaX/drXY skip BSM particles — non-classification (setcuts.f:200-314)
Confirms the "generic cuts are SM-only" claim by the actual mechanism (verified v3.7.1):
- :260-267 EVERY final particle defaults `etmin(i)=0`, `emin(i)=0`, `etamin(i)=0`
  (etmax/emax/etamax=-1, i.e. no upper). A particle that matches no class keeps these.
- :217-233 classification is by PDG CODE: `|pdg|<=maxjetflavor` (or 21 gluon) -> is_a_j;
  `maxjetflavor+1..5` -> is_a_b; 11/13/15 -> is_a_l; `idup==22` (NOTE: no abs) -> is_a_a;
  12/14/16 -> is_a_nu (and do_cuts=false).
- :269-313 the generic pt/E/eta cut is assigned ONLY inside `if(do_cuts(i))` AND only in the
  `is_a_j/is_a_l/is_a_b/is_a_a` branches. drXX/mmXX (:346-397) key on the same is_a_X flags.
- => A BSM final state (dark photon, Z', dark-sector scalar) with a non-SM PDG matches NO
  class, so it keeps etmin=0/etmax=-1 and gets NO generic pt/eta/dr/mass cut — REGARDLESS of
  its mass. This is a DISTINCT mechanism from the pmass>20 do_cuts disable (:212): a LIGHT
  BSM particle (pmass<20) still has do_cuts=true but is simply never classified, so no
  generic branch fires. The supported ways to cut it: `pt_min_pdg`/`eta_*_pdg`/`mxx_min_pdg`
  by its PDG (sec 2 below), or `custom_fcts`/`dummy_cuts` (custom-cuts-and-nocut.md).

## 2. PDG-specific cut — event enforcement (setcuts.f) **BYPASSES the >20 GeV rule**
- **Per-particle (pt/E/eta) :318-335**: if `pdg_cut(1).ne.0`, for each tracked PDG j and
  each final particle i with `abs(idup(i))==pdg_cut(j)`, OVERWRITE
  `etmin(i)=ptmin4pdg(j)`, `etmax(i)=ptmax4pdg(j)`, `emin/emax`, `etamin/etamax` (:326-331).
  Guard is ONLY `.not.cut_decays .and. from_decay(i)` -> cycle (:322). It does **NOT**
  check `do_cuts(i)`. setcuts.f:211 comment is explicit: *"CAREFULL: PDG_CUT do not
  consider do_cuts (they simply check the cut_decays)"*.
  => A PDG cut applies to particles that the generic ptX cuts skip — including
  `pmass>20 GeV` resonances that setcuts.f:212 disabled for do_cuts. **This is the
  supported way to put a pt/eta cut on a top/W/Z/H/Z' directly**: use `pt_min_pdg {6: ...}`
  not `ptheavy`/`ptj`. (cuts-f-filter.md caution "can't cut a >20 GeV particle via ptX"
  is true for the GENERIC cuts; PDG cuts are the exception.)
- **Pairwise invariant mass `mxx_min_pdg` :438-463**: sets `s_min(j,i)=mxxmin4pdg(k)**2`
  for pairs both matching the tracked PDG. `mxxpart_antipart(k)=True` (:451) restricts to
  exact particle+antiparticle (`idup(j)==-idup(i)`, :452); else any same-|PDG| pair
  (:456). Same cut_decays/from_decay guard, again no do_cuts. The s_min array is then
  enforced by the pairwise invariant-mass filter in cuts.f (cuts-f-filter.md step 13).

## 3. The smin integration floor — cuts set the minimum partonic ŝ (setcuts.f:528-708)
After classification, setcuts.f accumulates a lower bound `smin` on partonic ŝ from the
cuts and hands it to the phase-space integrator (this is the cut layer's contribution to
integration efficiency; the channel/propagator mapping itself is phase-space slice).
- :528 `smin = 0d0`. Per-class blocks add a contribution = the max over that class's
  applicable cuts, squared/summed:
  - jets :~530-572: ptj/ej/xptj + ordered ptj1..4min + htjmin/ht2..4min, plus
    `(nb_j-nb_nocut)*(...)/2*mmjj**2` pair term (:569); `smin += max(smin_p**2,smin_m,htjmin**2)`.
  - b :574-601 (ptb/eb/xptb/mmbb/ihtmin), photon :602-633 (pta/ea/xpta/mmaa, only if
    `ptgmin==0`), lepton :634-676 (ptl/el/xptl + ptl1..4min/mmll/mmnl/ptllmin/misset).
  - PDG particles :678-691: `smin += max(nb_pdg*(pmass²+ptmin4pdg²), ...mxxmin4pdg² term)`.
- :693-700 symmetrize s_min(i,j) and fold in `(pmass(i)+pmass(j))**2` mass thresholds.
- :702-707 `smin = max(smin, (sum of final masses)**2, dsqrt_shat**2)`. So dsqrt_shat and
  the produced-particle masses are floors on smin too.
- :708 prints VERBATIM `Define smin to <value>` to stdout. PROBE-CONFIRMED (v3.7.1): a
  `p p > t t~` + `pt_min_pdg {6:50}` survey printed `Define smin to 119716.0` in the
  per-channel survey log; 119716 = (2*173)^2 = the top-pair produced-mass floor (:707
  `max(smin, smin_p**2=Sum(pmass)**2, dsqrt_shat**2)` dominated here). This is the observable
  trace that cuts shaped the integration lower bound.
- Consequence: raising a pt/mass cut tightens smin, which improves integration efficiency;
  this is WHY auto_ptj_mjj/xqcut force ptj=mmjj=xqcut (cuts-f-filter.md) — to lift smin.

## 4. Grouped-subprocess consistency — HARD ABORT (setcuts.f:710-811)
Subprocesses grouped into one channel (the default `group_subprocesses`) must produce
IDENTICAL cut state. On `iproc==1` setcuts.f saves all per-particle cut arrays + do_cuts
+ classification (:712-...); for every later iproc it recomputes and compares. ANY mismatch
sets `fail_reason` (:739-797 — do_cuts, etmin/etmax, emin/emax, etamin/etamax, s_min/s_max,
ptll_min/max, ordered ptj/ptl, htj, mmnl, xptj/xpta/xptb/xptl, ptgmin, ktdurham, ...).
If `fail_reason.ne.''` (:799): prints *"Grouping of subprocesses not consistent with
setcuts.f. Either change your cuts and/or turn grouping of subprocesses off:"* + reason,
writes `../../../error`, and `stop 1` (:808) — a HARD CRASH of the survey/integration.
(Runtime text not yet probe-verified — predicted from source.)
=> A user who applies a cut that lands differently across grouped subprocesses (e.g. a PDG
cut that hits one subprocess's particle ordering but not another's) gets a crash, not a
silent wrong result. The fix offered is `group_subprocesses=False` (phase-space slice owns
the grouping flag itself; the consistency requirement on cuts is ours to explain).

## 5. ERROR TRAPS (setcuts.f:817-880)
After the loop, source-visible auto-corrections + warnings (runtime, predicted):
- :819-825 jet or photon with `etmin==0 .and. emin==0` -> Warning "pt or E min of a
  jet/gamma should in general be >0" (advisory only, does not change values).
- :835-838 no jets but `xptj>0` -> "cuts on the jet will be ignored", `xptj=0`.
- :840-844 fewer than 2 jets but `xetamin>0 .and. deltaeta>0` -> "WBF cuts not will be
  ignored", `xetamin=deltaeta=0` (the VBF rapidity-gap cut needs >=2 jets).
- :846-880 same ignore-and-zero pattern for `xpta` (no photons), `xptb` (no b),
  `xptl` (no leptons). These are RUNTIME (Fortran) cut auto-disables, distinct from the
  banner.py parse-time ones (runcard-cut-validity.md) — a FOURTH place cut values mutate.
  PROBE-CONFIRMED (v3.7.1): `xpta=30` on photon-less `p p > t t~` printed `Warning: cuts on
  the photon will be ignored` (setcuts.f:854) in the survey log; xpta dropped to 0. The
  unifying shape across all these disables is generalized in cut-precondition-auto-disable.md.

## 6. setxqcuts — per-channel xqcut thresholds (setcuts.f:892-955)
Called only if `xqcut>0` (:883). Walks the diagram FOREST (`iforest`, to_forest common) for
every config and sets:
- `xqcutij(a,b)=xqcut` for two jet/gluon legs (|pdg|<=maxjetflavor or 21) sharing a forest
  vertex, both with do_cuts (:939-946).
- `xqcuti(i)=max(0d0, sqrt(xqcut**2 - pmass(i)**2))` for an unpartnered jet leg (:950-951)
  — the mass-corrected single-particle xqcut floor.
Stored in `to_xqcuts` common for grid preparation. The forest/channel topology is
phase-space slice; the xqcut->threshold translation is the matching/cut coupling.

## Cautions
- **PDG cuts bypass do_cuts** (setcuts.f:211-212, :318-335): unlike generic ptX, a
  `pt_min_pdg`/`eta_*_pdg`/`mxx_min_pdg` cut DOES fire on a >20 GeV resonance. This is the
  intended override, but it means "no cuts on heavy particles" is FALSE once a PDG cut is
  set on that PDG. Update cuts-f-filter.md's heavy-resonance caution accordingly.
- **PDG cuts forbid light objects** at parse time (banner.py:4722) — you cannot target
  jets/leptons/photons by PDG; use ptj/ptl/pta. The error is raised in
  update_system_parameter_for_include, AFTER check_validity.
- **Source bug in the smin PDG loop (setcuts.f:678-691)**: the inner loop variable is `j`
  (:680) but the body reads `idup(i,...)`/`do_cuts(i)`/`pmass(k)` using the OUTER PDG-index
  `i` (1..pdg_cut(0)), not the particle index `j`. This malforms the PDG contribution to
  the smin integration FLOOR (an efficiency hint), not the event-level PDG enforcement
  (:318/:438 are correct). Consequence is a possibly-wrong smin estimate for PDG-cut runs;
  needs a probe to characterize. Pointer, not a runtime claim.
- The grouped-subprocess consistency `stop 1` (:808) is a HARD crash, not a warning — a
  cut that classifies differently across a subprocess group aborts the run.
- Cut values mutate at FOUR sites across THREE layers: creation defaulting (banner.py,
  layer 1), parse check_validity (banner.py, layer 2), setcuts.f xqcut block (:156-189,
  cuts-f-filter.md, layer 3a), AND the setcuts.f ERROR TRAPS (:835-880) which zero
  xptj/xpta/xptb/xptl/xetamin when the target class is absent (layer 3b). The Fortran
  layer 3 is the two sub-stages 3a (xqcut corrections) + 3b (ERROR-TRAP ignore-and-zero);
  cut-value-layer-precedence.md already models layer 3 as 3a+3b, so its "3 layers" framing
  is consistent with this four-site count, not an undercount.
