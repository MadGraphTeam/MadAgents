---
description: Cut values are touched at 3 pipeline layers (creation defaulting / parse check_validity / runtime setcuts.f); latest layer wins, so run_card.dat text is NOT necessarily the enforced cut — trace all 3 to answer "what cut actually fires?"
---

# Multi-layer cut-value precedence — the written card is not the enforced cut

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py` (RunCardLO) and
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/setcuts.f`. MG5_aMC v3.7.1.

## The principle
A single cut datum can be set, zeroed, or overridden at up to THREE layers. The
**latest-firing layer wins**, and only layers 1-2 are reflected in `run_card.dat`. Layer 3
(Fortran `setcuts.f`) mutates the value *in memory* at integration time and writes it back
to NO visible file. So to answer "what cut is actually enforced?" you must trace all three —
reading the run_card alone can be wrong.

- **Layer 1 — creation-time process defaulting** (`create_default_for_process`, banner.py:4767;
  see runcard-cut-process-defaults.md). Picks the DEFAULTS the fresh card carries:
  `remove_all_cut` for 1->N, multiplicity matching auto-enable (ickkw=1, xqcut set to the
  matching default, drjj=0, drjl=0 at :4956-4966), maxjetflavor auto-set from beams (:4807-4810).
- **Layer 2 — parse-time `check_validity`** (banner.py:4494; see runcard-cut-validity.md).
  Runs on every card read (creation AND user edits). Photon-iso auto-disable (pta=0, draj=0
  if ptgmin>0, :4516-4522); xqcut>0 zeroes drjj/drjl (:4566-4573); mmjj reset if
  auto_ptj_mjj=F (:4574-4577). Output of layer 2 IS the run_card text the user sees.
- **Layer 3 — runtime `setcuts.f`** (see cuts-f-filter.md), in TWO sub-stages:
  - 3a xqcut corrections (:156-189): re-applies AUTHORITATIVELY `ptj=xqcut` (auto_ptj_mjj
    & ptj>=0 & ktscheme==1, :157-158), `mmjj=xqcut` (:168-169), drjj/drjl forced to 0
    (:181-188). ALSO `etmin = max(pta, ptgmin)` for photons (:300) — re-imposes a photon
    pt floor that layer 2 stripped from pta. PDG-specific cuts OVERWRITE etmin/etmax/eta*
    by PDG here too (:318-335; pdg-cuts-and-smin.md), bypassing do_cuts.
  - 3b ERROR TRAPS (:817-880, pdg-cuts-and-smin.md): zero `xptj/xpta/xptb/xptl` when the
    target class has no members, and `xetamin/deltaeta` when <2 jets — a runtime
    ignore-and-zero that fires AFTER 3a. So "layer 3" is really 3a+3b; the latest-firing
    sub-stage still wins.

## Why this catches MORE than the per-page cautions
Each instance page warns about its own layer. The principle is the *cross-layer law*: any
question of the form "I set cut X in the card but events don't respect it — why?" resolves
by asking which later layer overrode X. It catches cases none of the instances enumerate,
e.g. a user hand-editing `ptj` to a hard value in a matched card (xqcut>0) and being surprised
the jets are soft — because layer 3 forces ptj=xqcut regardless of the edit, and check_validity
(layer 2) never touches ptj at all so the card keeps showing the user's edited value.

## Probe-confirmed (v3.7.1)
`generate p p > j; add process p p > j j; output` (matching auto-enabled at creation):
- Written `Cards/run_card.dat`: `ptj=20.0`, `mmjj=0.0`, `xqcut=30.0`, `ickkw=1`, `drjj=0.0`
  (layers 1-2 output). `auto_ptj_mjj=True`; `ktscheme=1` (hidden default, banner.py:4286).
- Generated `SubProcesses/setcuts.f:158` carries `ptj=xqcut` unconditionally under those
  conditions (per-process copy == template).
- Survey run per-channel log (`SubProcesses/P*/G*/log.txt`) prints VERBATIM:
  `Warning! ptj set to xqcut=   30.000000000000000       to improve integration efficiency`
  `Warning! mmjj set to xqcut=   30.000000000000000       to improve integration efficiency`
  => enforced ptj=xqcut and mmjj=xqcut, NOT the card's ptj / 0. Layer 3 won; no file records it.
  (The `ptj=20`, `xqcut=30` above are the v3.7.1 version-REGISTERED defaults — ptj at
  banner.py:4312, the matching-xqcut set by create_default at :4958 — read them FRESH at those
  coordinates, not portable constants. The GENERAL claim is the mechanism: layer 3 forces
  ptj=mmjj=xqcut regardless of whatever the card shows, whatever those numbers happen to be.)

## Boundary
- The law is about the SAME datum being OVERWRITTEN to a DIFFERENT value (latest wins). The
  sibling case — a cut SILENTLY ZEROED because its enabling precondition is unmet (isolation/
  matching active, or target class absent) — is cut-precondition-auto-disable.md: there the
  prediction is value->0 + a warning, not a value-swap. Layer 3b's xptX/xetamin zeroing is an
  instance of THAT law; this page covers the override (value-swap) half.
- The law is about the SAME datum touched at multiple layers. A cut touched at only one layer
  (e.g. ordered-pt cuts) has no precedence question — card == enforced. CAVEAT: even a
  single-layer cut (`mmll`, `drll`, `ptl`, …) is silently neutralized on a DECAY-PRODUCT leg
  under the default `cut_decays=False` — its setcuts.f array slot is never filled (do_cuts=F),
  so card != enforced for those legs. That is the cut_decays exemption (a fourth neutralization
  mode landing in setcuts.f), cut-decays-decay-product-exemption.md.
- Layer 3's xqcut block fires only when `xqcut>0`; the photon `max(pta,ptgmin)` re-imposition
  only when the particle is is_a_a and ptgmin>0. Outside those triggers, layers 1-2 are final.
- This is the LO path. NLO (`run_card_NLO.dat` / setcuts in amcatnlo) is out of slice.
- The BW-window cut (`cut_bw`, cuts.f:509) is bw-window slice, not covered here.

## Instances (kept)
- runcard-cut-process-defaults.md — layer 1 (creation defaulting, matching auto-enable).
- runcard-cut-validity.md — layer 2 (parse-time corrections).
- cuts-f-filter.md "Mapping layer" — layer 3 (setcuts.f runtime override).
- cut-decays-decay-product-exemption.md — decay-product neutralization (cut_decays=False),
  the fourth setcuts.f mode: a single-layer cut goes inert on from_decay legs at array-fill.
- runcard-cut-params.md — the param registry the three layers all act on.
