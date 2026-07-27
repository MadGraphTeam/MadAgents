---
description: The sample spans several jet multiplicities and will be showered, so ME and shower both fill the same jet bins.
---

# Matching & merging setup — fan-out

Any "set up MLM / FxFx / CKKW-L" / "matched W+jets|Z+jets|tt̄+jets sample" / "multi-jet-multiplicity + shower" request is a **multi-jet matched-sample** build. Center of gravity is the **run_card + model-load** side (not the shower) — so this is the primary fanout; `pythia8-shower-configuration-fanout` owns only the PY8-card sub-slice and is cross-referenced, not duplicated.

Surface keywords that route here: `matching`, `merging`, `MLM`, `FxFx`, `CKKW-L`, `ickkw`, `xqcut`, `qcut`/`JetMatching`, `ktdurham`/`Merging:`, `DJR`, multiplicity ladder (`add process … j`, `… j j`) + `shower=`.

## Owner map (per sub-question)

- **`ma-matching-consultant`** — scheme selection and the run_card matching knobs: `ickkw` (accepted set + meaning, **per class**), `xqcut` (the generation-level kt cut in `reweight.f setclscales`), `ktdurham` (CKKW-L generation cut; `>0` marks the run 'CKKW'), `asrwgtflavor` semantics, `alpsfact` (MLM-only), the matched-σ / DJR / matching-uncertainty concepts. THE primary owner.
- **`ma-pythia8-interface-consultant`** — the PY8-card side: `JetMatching:*` (MLM) and `Merging:*` (CKKW-L) params, which MG auto-writes vs which the user sets, the auto-managed-param FATAL, `applyVeto`, DJR output format. See also `pythia8-shower-configuration-fanout`.
- **`ma-kinematic-cuts-consultant`** — cut auto-disable under matching: `drjj`/`drjl`→0, `ptj` override, the `maxjetflavor=6`+matching guard.
- **`ma-scales-pdf-consultant`** — `maxjetflavor` default/auto-set-from-beam-content, the 4F/5F↔PDF consistency requirement (no code guard), `lhaid` nf identity (external), `asrwgtflavor` run_card mechanics.
- **`ma-model-loader-consultant`** — default `p`/`j` multiparticle content: b-in-`p`/`j` is **mass-driven** (drives `sm` vs `sm-no_b_mass` and 4FS vs 5FS).
- **`ma-amcatnlo-consultant`** — FxFx NLO runtime: `ickkw=3` accepted set (NLO class), the shower requirement (FxFx forbids fixed-order launch), the no-pure-QCD-multijet-guard, `parton_shower`.
- **`ma-nlo-syntax-consultant`** — the `[QCD]` bracket on each FxFx multiplicity; `[QCD]` and `@N` are orthogonal (parse-order safe).
- **`ma-physics-consultant`** — regime judgments source can't settle: which σ (post-shower) is physical, whether the matching scale suits the process, DJR-continuity interpretation, the 4F/5F physics trade-off.

## Dispatch ordering

The **flavor scheme is decided first** because it cascades: 4FS (`import model sm`, massive b) → b absent from default `p`/`j`, `maxjetflavor`=4, 4F PDF, explicit b allowed in the final state; 5FS (`sm-no_b_mass`, massless b) → b in `p`/`j`, `maxjetflavor`=5, 5F PDF, no explicit b in ME. Then: model-load → process (multiplicity ladder; add `[QCD]` per line for FxFx) → run_card matching knobs → PY8 card → runtime. A **"why is my matched σ wrong / did matching even fire"** question routes differently — start at the observable (physics: post-shower σ vs pre-shower sum) and the reweight/veto path (matching), not at the card.

## Anticipated traps (behavioural shape → owning consultant page)

- **"qCut=30 / nJetMax=2 are the MLM defaults."** Fabricated. Real card values are sentinels `qCut=-1`→`1.5·xqcut`, `nJetMax=-1`→`max_n_matched_jets`; `scheme=1` is force-set at run. → pythia8 `matching-param-handoff`, matching `mlm-py8-bridge`. Don't answer PY8 matching-card content from recall.
- **"xqcut must be nonzero (enforced)."** Nonzero is a *physics* need — `check_validity` does NOT enforce it; `ickkw=1`+`xqcut=0` passes validity silently and the `reweight.f` merging cut is simply skipped. → matching `mlm-reweight-lhe-write`.
- **"A 5F PDF with maxjetflavor=4 gets caught."** NO code guard — `maxjetflavor` derives from beam content, never from the PDF's nf; the mismatch runs silently wrong. Only guards are `>6` and `=6`+matching. → scales-pdf `flavor-scheme-maxjetflavor`.
- **"MG blocks FxFx for pure-QCD multijet."** No guard; the auto-detect would actively turn FxFx *on* for an all-jet multi-multiplicity run. Applicability is physics-only. → amcatnlo `fxfx-ickkw3-lifecycle`.
- **"doFxFx / qCutME are pythia8_card params you `set`."** Not LO-card params; FxFx's PY8 config is a `Pythia8Plugins/JetMatching.h` patch driven from amcatnlo, not a card knob. → pythia8 `matching-param-handoff` (boundary → amcatnlo).
- **"Merging:doMGMerging enables auto file handling."** Not registered in 3.7.1 (only `doKTMerging` / `doPTLundMerging`). → pythia8 `matching-param-handoff`.
- **"Just set SpaceShower/TimeShower:pTmaxMatch (or Merging:nQuarksMerge) too."** These are unconditional `MadGraphSet` when `ktdurham>0` → co-setting triggers the FATAL "parameter already set". (Asymmetry: `qCut`/`nJetMax`/`TMS` are force=True and instead *respect* a user value.) → pythia8 `matching-param-handoff`.
- **"One ickkw table: 0/1/3/4."** LO `RunCardLO`=`[0,1]`, NLO `RunCardNLO`=`[-1,0,3,4]` — different classes; `1`=MLM is LO-only, `3`=FxFx/`4`=UNLOPS(no MG interface)/`-1`=NNLL+NLO-jet-veto are NLO-only. Never merge the tables. → matching `lo-ickkw-mlm` / `nlo-ickkw-fxfx`.
- **"drjj/drjl zeroing is ickkw-gated."** Gate is `xqcut>0` (not `ickkw`); the "Since ickkw>0…" warning text is a source misnomer. → kinematic-cuts `cut-precondition-auto-disable`.

## Cross-slice seam — the flavor-scheme invariant (check by hand)

4F/5F consistency must hold across FOUR independently-owned pieces — model import (b mass, model-loader), `p`/`j` content (model-loader), `maxjetflavor` (scales-pdf, auto-set from beam content), and the PDF nf (scales-pdf/external LHAID) — plus `asrwgtflavor` (auto=`maxjetflavor`). **MG enforces none of it.** So when assembling a matched spec, the lead must reconcile the scheme across these four by hand (a trivial-invariant check per whole-spec reconciliation); a clean run with a 5F PDF and `maxjetflavor=4` is exactly the silent-wrong outcome this seam exists to catch.

## What source cannot settle (route to physics / flag external)

- Which reported σ is physical (post-shower matched), DJR-continuity quality, matching-scale suitability, 4F-vs-5F trade-off → `ma-physics-consultant`.
- Pythia8-internal mechanics — `JetMatchingMadgraph` light-parton counting, the `exclusive=(nParton==nJetMax)` logic, CKKW-L Merging weight math, the internal DJR histogram — are **external to MG source**; flag as gap, never fabricate an MG citation. The MG side outputs DJR as **HwU** (`djrs.dat`), not XML.
