---
description: MLM alphas/PDF reweighting (reweight.f setclscales) and the LHE clustering/mgrwt tag write-out (unwgt.f) — Fortran consumption of pdfwgt/clusinfo/alpsfact/asrwgtflavor; the generation-level xqcut vertex cut inside setclscales (gated xqcut>0, so xqcut=0 skips it); plus the ickkw==2 Sudakov-reweighting (CKKW-internal) branch and its reachability gate (alpha/legacy, dead treat_ckkw_matching call).
---

# MLM αs/PDF reweighting + LHE matching-tag write-out (LO Fortran)

The LO `ickkw` comment (`banner.py:4284`) promises MLM "activates alphas and pdf
re-weighting according to a kt clustering of the QCD radiation." The `lo-ickkw-mlm`
page lists the Python registrations (`pdfwgt`, `clusinfo`, `alpsfact`,
`asrwgtflavor`, `chcluster`) and the `ktscheme`/`auto_ptj_mjj` Fortran sides.
THIS page is the **Fortran consumption that actually performs the reweighting and
writes the matching tags into the LHE** — the missing physics layer.

All cites `$MADGRAPH_INSTALL/Template/LO/SubProcesses/` (reweight.f, unwgt.f),
generated source per ma-truth-sources.

## The kt-clustering + scale assignment: `setclscales` (reweight.f:555)
`logical function setclscales(p, keepq2bck, ivec)` @555 clusters the event back
to a "tree" of QCD branchings and stores per-vertex clustering scales in
`pt2ijcl(...)` (the squared kT measure; `DJ`/`PYDJ`/`PYJB` from kin_functions.f
per ktscheme, see lo-ickkw-mlm).
- @700-705: caches central factorization scales into `q2bck(1:2)`
  (`common /to_rw/...q2bck`), respecting `fixed_fac_scale1/2`.
- @1195-1203 (`ickkw.eq.2 .or. (pdfwgt.and.ickkw.gt.0)`): sets factorization
  scale to the **minimum clustering scale** found, `q2fact(i)=scalefact**2*
  min(pt2ijcl(jfirst(i)),q2fact(i))` — the comment @1196: "Total pdf weight is
  `f1(x1,pt2E)*fj(x1*z,Q)/fj(x1*z,pt2E)`". This is the PDF-reweighting scale.
- @1206-1219: **factorization-scale floor** — if `q2fact < 4` GeV² (i.e. scale
  `<2` GeV) on an incoming hadron leg, warns ("Too low fact scales", capped at 10
  warnings) and returns `setclscales=.false.` / `clustered=.false.` → that event's
  clustering/reweighting is dropped.

## Generation-level xqcut cut inside setclscales (reweight.f:1063-1089)
After clustering, `setclscales` applies the MLM **generation-level kt cut** itself
(comment @558 "Also perform xqcut and xmtc cuts"). The whole loop is gated
`if(xqcut.gt.0)` @1066: for every clustered vertex `n` whose daughters are among
the jets (`iqjets(fsno)>0`), if `sqrt(pt2ijcl(n)) < xqcut` @1075 it sets
`setclscales=.false.`, `clustered=.false.` and returns @1081-1083 — the event's
clustering is rejected (dropped from the matched sample). So this is where the
xqcut merging scale actually kills below-cut configurations at generation time.
- **xqcut=0 ⇒ this cut is SKIPPED** — the `if(xqcut.gt.0)` guard @1066 is false, so
  no vertex is rejected and no generation-level kt cut is applied. Confirms the
  doc-level claim "when xqcut=0 the generation-level kt cut in the matching
  reweighting code is skipped." Combined with lo-ickkw-mlm (check_validity never
  enforces xqcut>0 under ickkw=1), an `ickkw=1 + xqcut=0` run passes validity AND
  silently applies no merging-scale cut — a physically-broken but non-aborting MLM.
- @1090-1094: a parallel `xmtc` (central-process) cut, gated `xmtc**2>0`.
- Distinct from the two 2-GeV floors below (fact-scale @1206, per-vertex αs @1597) —
  those are absolute low-scale protections; this is the user's merging scale.

## αs reweighting (reweight.f, in the rewgt caller ~1460-1795)
- **ickkw-gate (why alpsfact is "MLM-only"):** `rewgt` (@1333) has two early exits
  before any αs reweight: @1421 `if(ickkw.le.0.and..not.use_syst) return`, and
  @1450 `if(ickkw.le.0)then ... asref=0; goto 100` — the ickkw<=0 path sets
  `asref=0` and jumps past the clustering + vertex loop entirely. So the alpsfact
  αs reweight @1601 is reached ONLY when `ickkw>0` (=1 for normal LO config,
  allowed=[0,1]). Under `ickkw=0 + use_syst` the function only gathers PDF/syst
  info; it never applies the multiplicative αs reweight.
- @1557: `asref = all_G(ivec)**2/(4*PI)` — the reference αs is taken from the
  matrix-element strong coupling `all_G` (the αs at which the ME was evaluated).
- @1560-1615 loop over the `nexternal-2` clustered QCD vertices: at each vertex
  scale `q2now`, multiply `rewgt = rewgt * alphas(alpsfact*sqrt(q2now))/asref`
  (@1601). So each QCD branching gets αs re-evaluated at ITS clustering scale
  (times `alpsfact`), divided by the central αs. **`alpsfact` (default read at
  `banner.py:4287`) rescales the argument of αs at every clustered vertex** — this is what
  `check_validity` force-resets to 1.0 under `use_syst` (lo-ickkw-mlm @4553).
- @1597-1599: per-vertex αs floor — if `q2now <= 4` GeV² the whole event weight
  `rewgt=0d0` and returns (event killed). Distinct from the fact-scale floor above.
- @1786-1795: after reweighting, for `ickkw.gt.0 .and. pdfwgt` reset
  `q2fact(1:2)=q2bck(1:2)` — restore the central (un-clustered) fact scales as the
  **PS starting scale** written to the event. (`ickkw==2` pure-shower branch
  @1786 sets `q2fact=pt2min` instead — Sudakov path, alpha-only.)

## `asrwgtflavor` — flavour ceiling on what counts as a reweightable parton
`isparton(ipdg)` (reweight.f:213-217): `irfl=abs(ipdg)`; a leg is a parton iff
`irfl <= max(asrwgtflavor,maxjetflavor)` OR `irfl==21` (gluon). So
`asrwgtflavor` ("highest quark flavor for a_s reweighting in MLM",
`banner.py:4290` — read the default fresh there) raises the ceiling of quark flavours treated as clusterable
QCD partons for the αs reweight, taking the max with `maxjetflavor`. A heavy quark
above this ceiling is NOT clustered as radiation.

## LHE matching-tag write-out (unwgt.f, write_leshouche ~760-865)
Two buffer groups are written into the event, gated differently:

### `<mgrwt>` systematics/reweight buffer — gated on `use_syst` (@769-834)
When `use_syst=True`, writes a `<mgrwt>` block with:
- `<rscale>` @779: `n_qcd-n_alpsem` and the central scale `s_scale`.
- `<asrwt>` @783-787: `n_alpsem` (number of αs-reweighted vertices) and the list
  of vertex scales `s_qalps(...)` — these are the per-vertex `sqrt(q2now)` stored
  @1605 during the αs reweight.
- `<pdfrwt beam="1/2">` @793-830: PDF reweight info (flavours, x, Q) per beam.
- `<totfact>` @831: `s_rwfact(ivec)` — the total reweight factor (computed
  @1804-1817: `rewgt × initial-PDF × asref**n_qcd`).
This block is the SysCalc/systematics input; it is written whenever `use_syst`,
independent of `ickkw`.

### `<clustering>` matching buffer — gated on `ickkw.ne.0 .and. clusinfo` (@836-846)
```
if(icluster(1,1,ivec).ne.0 .and. ickkw.ne.0 .and. clusinfo)then
   nclus=nexternal
   write(buffclus(1),...) '<clustering>'
   do i=1,nexternal-2
      write(buffclus(i+1),'(...)') '<clus scale="', dsqrt(pt2ijcl(i)),'">',
         (icluster(j,i,ivec),j=1,4),'</clus>'
   ...
```
So **`clusinfo` (Python default True) is what writes the `<clustering>` /
`<clus scale="...">` tags** — one `<clus>` per clustered branching, carrying the
clustering scale `sqrt(pt2ijcl(i))` and the 4 leg indices `icluster(1:4)`. These
tags are the matching information a shower/MLM driver reads. Gated on `ickkw.ne.0`:
a fixed-order (ickkw=0) LHE carries NO `<clustering>` tags even if clusinfo=True.
- @861: both buffers passed to `write_event(...,nclus,buffclus)`.

## ickkw==2: Sudakov-reweighting (CKKW-internal) branch (reweight.f) — alpha/legacy
`ickkw==2` selects a SECOND, distinct reweighting mode in the SAME reweight.f
machinery — initial-state Sudakov form factors, NOT the MLM αs+PDF reweight of
ickkw==1:
- Setup @1490-1497: for each external leg `pt2prev`/`pt2pdf` seeded from `pt2min`
  (the minimum clustering scale); @1528-1531: `q2fact(1:2)=0` (reset for PDF-reweight rebuild).
- Sudakov form factor @1640-1656: at each clustered QCD radiation vertex, when the
  parton id changes / non-radiation vertex AND `pt2prev < pt2ijcl(n)`:
  `rewgt = rewgt * min(1, getissud(beam,id,x,x',pt2ijcl(n)) / getissud(...,pt2prev))`
  — the **ratio of initial-state Sudakovs** between the previous and current
  clustering scale (`getissud` reads the Sudakov grid `issudgrid.dat`, the
  `issgridfile` param). This suppresses configurations by the no-emission
  probability between scales (the CKKW analytic Sudakov).
- @1786: `ickkw==2 .and. lpp(1)==0 .and. lpp(2)==0` (lepton beams) sets
  `q2fact=pt2min` as the PS starting scale (the alpha-only Sudakov path noted earlier).
- `myamp.f:341`: `ickkw==2` also scales the ME cut `xqfact=0.3d0` (same as ktscheme=2).

**Reachability tension (non-obvious):** `ickkw==2` is NOT in the LO Python
`allowed=[0,1]` (banner.py:4284) — `check_validity` raises on `ickkw>1` unless
the user overrides the alpha prompt, and the prompt-decline path raises
`InvalidRunCard('ickkw>1 is still in alpha')`. So this whole Sudakov branch is the
"alpha and only partly implemented" code (lo-ickkw-mlm); it exists in the Fortran
but is gated off from normal card config. The `madevent_interface.py:6156`
`if ickkw==2: self.treat_ckkw_matching()` call references a method that does NOT
exist in the class (no `def treat_ckkw_matching` anywhere in source) —
effectively dead, consistent with ickkw==2 being unreachable via validity.

## Cautions
- **`clusinfo` is the on/off switch for the `<clustering>` LHE tags** (default
  True). Turning it off (hidden param) yields an MLM run whose LHE lacks the
  per-branching clustering scales — a downstream MLM/CKKW driver would then have no
  matching info. Non-obvious: the tags are gated on `ickkw.ne.0 AND clusinfo`, not
  on `ickkw` alone.
- **Two independent event-kill floors** in reweight.f: fact-scale `q2fact<4`
  (@1206, returns .false., drops clustering) and per-vertex αs `q2now<=4`
  (@1597, sets rewgt=0). Both at 2 GeV. A very-low-scale clustered configuration
  is silently zero-weighted, not aborted.
- `asref` is the ME coupling `all_G`, NOT the run-card central scale's αs directly
  — reweighting is relative to whatever αs the matrix element used.
- `alpsfact` multiplies the αs ARGUMENT at each clustered vertex (`alphas(alpsfact*
  sqrt(q2now))`); it is the MLM αs-scale variation knob, force-reset to 1.0 under
  use_syst at card-validity time (so its nominal effect is only seen with
  use_syst=False or via the `sys_alpsfact` systematics list).
- All static generated-Fortran. The actual number of clustered vertices, the
  fraction of events hitting the 2-GeV floors, and the emitted `<clus>` scale
  values are runtime outputs — probe-candidates, not asserted here.
