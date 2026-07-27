---
description: Cross-model EFT loop-capability pattern (source-verified on SMEFTatNLO; an expectation for un-installed EFT models) — the EFT operator order (NP/DIM6) is NEVER itself perturbed, only QCD is; NP power counting lives in CT coupling order dicts, not perturbative_expansion. dim6top_LO_UFO is an EFT model (build-dependent presence) with a VESTIGIAL empty CT stub that is genuinely LO (CT presence != loop capability). Which EFT models are installed is volatile → route to bundled-online-loop-models.
---

# EFT coupling orders and loop capability (cross-model)

(v3.7.1, `$MADGRAPH_INSTALL`.) The generic
loop-UFO machinery is in loopmodel-detection / ct-files-and-vertex-types / perturbation-
couplings-spine; the SMEFTatNLO instance is in smeft-at-nlo-loop-structure. This page is the
EFT-coupling-order pattern that holds ACROSS loop-capable EFT models and the traps specific to
EFT model files.

## The pattern: the EFT operator order is never perturbed; QCD is
SCOPE — this is SOURCE-VERIFIED on exactly ONE loop-capable EFT (SMEFTatNLO) plus one LO
counterexample (dim6top_LO_UFO); the other EFT models named below are online-only and NOT
installed here, so for them this is a physically-motivated EXPECTATION, not a verified fact
(you don't "loop in" extra operator insertions, so the EFT power-counting order should not be
perturbed — but confirm with the `perturbative_expansion>0` scan once the model is downloaded).
Where verified: the EFT power-counting order (`NP`, `DIM6`, …) is a plain `CouplingOrder` with
NO `perturbative_expansion` (so → 0); only `QCD` carries `perturbative_expansion = 1`. So
`perturbation_couplings == ['QCD']` and the model is **NLO QCD on a fixed EFT order** — no
NLO-EW/NLO-QED.
- SMEFTatNLO `coupling_orders.py:9-20` (live-read):
  - `NP  = CouplingOrder(expansion_order=2, hierarchy=1)` — no perturbative_expansion → 0.
  - `QCD = CouplingOrder(expansion_order=99, hierarchy=2, perturbative_expansion=1)` → perturbed.
  - `QED = CouplingOrder(expansion_order=99, hierarchy=4)` — no perturbative_expansion → 0.
  `NP`'s `expansion_order=2` caps the dim-6 amplitude expansion at NP=2 (squared dim-6); this
  is the EFT power-counting CAP, NOT a loop flag — it is consumed by process squared-order
  bracketing (nlo-syntax / eft slices), not by import_ufo's `perturbative_expansion>0` test.
- dim6top_LO_UFO `coupling_orders.py:9-23`: `QCD/QED` (expansion_order=99, hierarchy 1/2) and
  `DIM6/FCNC` (expansion_order=99, hierarchy 1) — **none** carry perturbative_expansion
  (`grep -c perturbative_expansion coupling_orders.py` → 0). So it is loop-INCAPABLE (LO).

## NP power counting rides in the CT coupling `order` dict, not in perturbative_expansion
The renorm constant of a dim-6 operator lives at the same NP order as the operator's tree
contribution; the loop adds QCD powers. So a SMEFTatNLO CT coupling reads
`order={'NP':2,'QCD':3,'QED':1}` (`CT_couplings.py:8168`, UVGC_1646_1, chromomagnetic `ctG`).
MadGraph's coupling-order bookkeeping then keeps the CT in the right NP slice automatically
(per-order Laurent-unfold split in add_CTinteraction, ct-files-and-vertex-types page). Durable
split (SMEFTatNLO `CT_couplings.py`): MOST CT Coupling blocks carry `'NP':2`, a minority carry
NO `'NP'` key (the pure-SM-sector CTs the EFT still renormalizes, e.g.
`R2GC_1302_474 order={'QCD':4}`). Every NP value present is exactly 2 — no NP=1/NP=4 CT
couplings. Read the split fresh: `grep -c "= Coupling(" CT_couplings.py` (total) vs
`grep -c "'NP':" CT_couplings.py` (NP-carrying). (See smeft-at-nlo-loop-structure for the full
SMEFTatNLO breakdown + restrict-card hazards; this page is the cross-model abstraction.)

## TRAP: CT-file presence != loop capability — dim6top_LO_UFO is a vestigial EFT example
`dim6top_LO_UFO` (bundled, the top-quark dim-6 EFT, Durieux/Zhang 2020) SHIPS a
`CT_couplings.py` yet is genuinely LO. Concretely (live):
- `coupling_orders.py` has ZERO `perturbative_expansion` → import builds a plain
  `base_objects.Model`, no LoopModel, no perturbation_couplings (loopmodel-detection page).
- `CT_couplings.py` is an 11-line STUB — `grep -c "= Coupling("` → **0** actual Coupling
  objects (only the FeynRules header + imports).
- There is NO `CT_vertices.py` at all; `__init__.py:37-43` does `try: import CT_vertices /
  except ImportError: pass` (the `try:` is at line 37) so the missing file is SILENTLY swallowed
  (`all_CTvertices` stays the empty default). `vertices.py` has zero `type=` (no R2/UV
  interactions).
So a "CT_couplings.py exists" check would WRONGLY flag dim6top as loop-capable. The only
correct test is the importer's own `perturbative_expansion>0` over `coupling_orders.py`
(import_ufo.py:501). This is the concrete EFT instance of "CT files alone do not make a loop
model" — the FeynRules export left vestigial CT stubs on an LO model. (NLO top-quark EFT is
the separate FeynRules-only `dim6top` NLO release / SMEFTatNLO, not this bundled LO UFO.)

## Online EFT models are install-dependent — behind the live-scan pointer
`_online_model` (`madgraph_interface.py:2894`, live) lists EFT-relevant online
entries: `EWdim6:['full']` (EW dim-6), `TopEffTh:['']` (top-quark EFT), `heft:[...]` (Higgs
EFT, the HEFT-TIR-branch model — heft-tir-vertex-branch page). On THIS build NONE of EWdim6 /
TopEffTh / heft / loop_qcd_qed_sm are present in `models/` (all online-only, `ls -d models/X`
→ absent). Their internal coupling-order / CT structure CANNOT be source-walked on this build —
their loop-capability and NP-counterterm layout are an install-dependent / runtime question
(see Gaps). Whether any given online EFT model is loop-capable is decided by the SAME
`perturbative_expansion>0` predicate once downloaded — do not assert from the model name.

## Which EFT models are installed is VOLATILE — route the membership to one page
Whether SMEFTatNLO / dim6top_LO_UFO / any online EFT model is present under `models/` DRIFTS
across builds (both were present when this page was authored and are ABSENT on the current
build) — that live membership + count lives in exactly ONE page, bundled-online-loop-models
(live `ls models/` + `>0` scan, NEVER `=1`). Do NOT restate the member list or count here.
The EFT-specific per-model STRUCTURE facts that hold whenever the model IS installed: **when
SMEFTatNLO is installed it is a loop-capable EFT** (QCD-only; the 2HDM family, if present, are
renormalizable BSM not EFT — bsm-nlo-2hdm-loop-structure); **when dim6top_LO_UFO is installed it
is LO** despite its vestigial CT stub (above). Frame these as "when installed," never as "bundled."

## Gaps (source can't settle)
- The internal coupling-order / CT-coupling order-dict structure of the online EFT models
  (EWdim6, TopEffTh, heft) — absent from this build, unreadable until downloaded.
- Whether a given online EFT model, once imported, perturbs only QCD or also QED — decided by
  its `perturbative_expansion` after download; not predictable from the name.

## Cautions
- "CT_couplings.py present ⇒ loop-capable" is FALSE (dim6top_LO_UFO counterexample). Always
  use `perturbative_expansion>0` over coupling_orders.py.
- "All EFT CT couplings carry NP" is FALSE — pure-SM-sector CTs (NP-less, a minority) coexist
  with the operator CTs (NP=2, the majority) in SMEFTatNLO; read the split with
  `grep -c "= Coupling(" vs grep -c "'NP':"`.
- Any "EFT model X is/ isn't loop-capable / is bundled" claim is install-dependent → live
  `ls models/` + `>0` scan, never a memorized count or name-based guess.
