---
description: How SMEFTatNLO restrict_*.dat cards drive Wilson-coefficient operator selection — zero prunes an operator, distinct nonzero keeps+de-duplicates, and the default/LO/NLO/NLO_no4q differences (models/SMEFTatNLO v3.7.1)
---

# SMEFT restrict cards — operator selection by Wilson-coefficient value

How a SMEFT (EFT) model's dim-6 operators get turned on/off through restriction. Concrete target: `$MADGRAPH_INSTALL/models/SMEFTatNLO/`. NOTE the EFT-model roster oscillates (models come and go across environments) — re-run `ls $MADGRAPH_INSTALL/models/` before asserting which EFT UFOs are present. When installed, `dim6top_LO_UFO` ships NO restrict card (`ls restrict_*.dat` returns none), so its operators are never pruned by restriction; SMEFTatNLO's four-card set is likewise a when-present observation of the current environment.

## The card structure (read targets)
SMEFTatNLO ships four cards: `restrict_default.dat`, `restrict_LO.dat`, `restrict_NLO.dat`, `restrict_NLO_no4q.dat`. A restrict card IS a param_card. The Wilson coefficients live in five blocks:
- `Block DIM6` (Lambda + cpDC,cpWB,cdp,cp,cWWW,cG,cpG,cpW,cpBB) — bosonic dim-6.
- `Block DIM62F` (two-fermion current operators: cpl*, c3pl*, cpe/cpmu/cpta, cpq*, cpQ*, cpu/cpt/cpd, ctp, ctZ, ctW, ctG).
- `Block DIM64F` (four-fermion / four-quark: cQq*, cQu*, ctq*, cQd*, ctu*, ctd*, cQQ*, cQt*, ctt1).
- `Block DIM64F2L` (two-quark-two-lepton: cQlM*, cQl3*, cQe*, ctl*, cte*, ctlS3, ctlT3, cblS3).
- `Block DIM64F4L` (four-lepton: cll*).

Entry `DIM6 1` is `Lambda` (the EFT scale, kept nonzero in ALL four cards). MZ/MU_R/mueft are deliberately kept "slightly different" — all three carry pairwise-distinct values (read the three in the active card) — per the card's own comment (restrict_LO.dat:198 "keep MZ, MU_R and mueft slightly different to avoid issues with restrictions"), so they don't get merged as identical by `detect_identical_parameters`.

## How a value maps to an operator's fate
The Wilson coefficients are EXTERNAL parameters (in their LHA blocks). They flow through the standard `RestrictModel` pipeline (see restrict-model-pipeline.md). Three value-classes:

1. **value == 0** → `detect_special_parameters` (import_ufo.py:2615) puts it in the null list; the coupling(s) built from it evaluate to 0 → `detect_identical_couplings` flags those couplings zero → `remove_interactions` (2425/2876) drops the vertices that carry ONLY that operator's coupling (or trims it from multi-coupling vertices). The operator is OFF — its vertices are pruned from the operative model. The external param itself becomes an internal `0.0` (or is removed if unused). **This is operator de-selection.**

2. **value nonzero AND distinct within its block** → not special (kept external/free), and `detect_identical_parameters` (2709) does NOT merge it (no other param in the same `(lhablock, value)` group). The operator is ON and remains an independently-settable coefficient in the user's param_card. **This is operator selection.**

3. **value nonzero but EQUAL to another coeff in the SAME block** → would be merged by `detect_identical_parameters` (grouping key `(param.lhablock, value)`, import_ufo.py:2728): the two operators collapse to one free param + a rule_card `add_identical` entry emitted by `merge_iden_parameters` (2843-2848), so the user can no longer vary them independently. The SMEFT cards AVOID this on purpose (see Cautions).

## Why the LO/NLO values look like random fractions
`restrict_default.dat`: every Wilson coefficient == `0.` (only Lambda, MU_R, mueft, ymt nonzero). **Default restriction prunes EVERY dim-6 operator** — `import model SMEFTatNLO` with no `-restriction` suffix gives a pure-SM operative model. Verified: lines 80-181 of restrict_default.dat, all DIM* entries are `0.`.

`restrict_LO.dat` / `restrict_NLO.dat` / `restrict_NLO_no4q.dat`: each enabled coefficient is set to a DISTINCT random-looking fraction in (0,1) — e.g. LO cpDC, cpWB carry distinct fractions (read magnitudes in `restrict_LO.dat`). These values are NOT physics inputs (the user overrides them in the real param_card later). Their only jobs:
- be **nonzero** so the operator's vertices survive `remove_interactions`;
- be **mutually distinct within each block** so `detect_identical_parameters` never accidentally merges two operators into one free coefficient.
Verified: an awk scan over all DIM blocks of all three cards found ZERO duplicate nonzero values within any block — the distinctness is deliberate and complete.

## The four cards' operator-set differences (source-diffed)
- **default**: all dim-6 OFF (SM only).
- **LO**: all listed coefficients ON (nonzero).
- **NLO**: like LO but with specific coefficients ZEROED — `DIM6 cG (7)=0`, `DIM6 cpG (8)=0`, and `DIM64F2L ctlS3 (19)=ctlT3 (20)=cblS3 (21)=0`. Those operators lack the NLO (QCD) ingredients in this model, so they are pruned for NLO use. (cWWW is nonzero but tiny — still ON.)
- **NLO_no4q**: identical to NLO EXCEPT the ENTIRE `DIM64F` block is zeroed (all four-quark operators OFF). "no4q" = no four-quark operators. DIM64F2L (2q2l) and DIM64F4L (4l) stay as in NLO.
Verified by `diff` of the DIM-block regions: LO↔NLO differ in DIM6 (cG,cpG→0) + DIM64F2L (ctlS3/ctlT3/cblS3→0) plus the random-value reshuffle; NLO↔NLO_no4q differ ONLY in DIM64F (all→0).

### Anchored values + the DIM64F membership (v3.7.1, via `diff restrict_NLO.dat restrict_NLO_no4q.dat`)
The `diff` is EXACTLY DIM64F lines 139-157 (all block entries nonzero→`0.000000`); nothing else changes. The zeroed operators ARE the full four-quark set, and **`cQq83` is `DIM64F` lhacode 1 — the FIRST entry of the block** (NLO `1 <nonzero> # cQq83`; no4q `1 0.000000 # cQq83`). So a 4-quark operator that COUPLES TO LIGHT QUARKS (cQq83) is unambiguously among the no4q-zeroed set — "no4q" means *no four-quark* operators (all of DIM64F), NOT "no four-HEAVY-quark". If an eft (operator-catalog) page claims no4q drops only 4-heavy-quark ops, that catalog framing is too narrow: the restriction MECHANISM zeros the entire DIM64F block including the light-quark-coupling cQq83/cQq81/cQq13/cQq11/cQu1/ctq1/cQd1/ctu1/ctd1 etc. (operator-sector identity is eft's to settle; what restriction DOES is zero the entire block.)
- Anchored operator addresses (the distinct-nonzero anti-merge idiom): `DIM6 cWWW(6)` nonzero (ON), `cG(7)=0`, `cpG(8)=0`; `DIM62F ctG(24)` nonzero; `DIM64F cQq83(1)`, `cQu1(12)` nonzero. Magnitudes are scrambled placeholders, NOT physics (read the active card) — distinct within each block so `detect_identical_parameters` can't merge them.
- **removed≠small consequence (ties to bsm-eft-param-card-value-fate.md):** because no4q sets `cQq83=0.000000` in the SHIPPED restrict card, the operator is PRUNED at load — `detect_special_parameters` nulls it, `remove_interactions` drops its vertices, the external param is gone from the operative model. A later `set cQq83 1.0` in the process-dir param_card is **INERT**: the parameter no longer exists as a settable card line (no entry written for a pruned coefficient), and the model was never re-restricted against the user card. The fix is to choose `SMEFTatNLO-NLO` (or `-LO`) at IMPORT time, never to set the coefficient afterward.

## Gaps (runtime, not settle-able from source)
- Whether a given card leaves the EXACT intended operator set in the operative model is a runtime question: vertex pruning depends on how each coefficient threads through `couplings.py` (a coefficient could appear in a coupling shared with a surviving operator, so the vertex is trimmed not removed). Confirm with a probe: `import model SMEFTatNLO-NLO_no4q` then inspect surviving interactions / `display couplings`.
- The "merged unexpectedly" hazard (two coeffs that happen to share a value) is detectable only after restriction runs — source diffing the card shows distinctness, but a USER-edited param_card that sets two same-block coeffs equal would NOT re-trigger merging. CONFIRMED from the call structure: `restrict_model(self, param_card,...)` sets `self.restrict_card = param_card` (import_ufo.py:2401) and reads values via `set_parameters_and_couplings(param_card,...)` (2407); the `param_card` here is the SHIPPED `restrict_*.dat`, and `detect_identical_parameters`/`merge_iden_parameters` run against those values (2446/2450). By the time the user edits the process-dir param_card the model is already pruned/merged; the user card is validated against the accumulated `rule_card`, never re-restricted. So a user setting two coeffs equal does NOT merge them — that is safe; merging is a load-time-only concern driven by the SHIPPED card.

## Transfer to other SMEFT models (SMEFTsim) — mechanism, not file names
The RestrictModel passes above are model-agnostic (bsm-eft-param-card-value-fate.md). SMEFTsim
is **NOT installed in this environment** (only SMEFTatNLO ships under `models/`; SMEFTatNLO's
running variant lives at `tests/input_files/SMEFTatNLO_running/`). So SMEFTsim's specific
restrict-card NAMES and contents are a **GAP** — do not assert them from memory. What DOES
transfer, grounded in `import_ufo.py`:
- A card in which every WC == 0 (a "SM-limit" card, whatever SMEFTsim calls it, e.g. a
  `SMlimit_*`-style file) → `detect_special_parameters` nulls every WC → `remove_interactions`
  drops every EFT vertex → the NP coupling order has NO surviving interaction. The order then
  gets dropped with a WARNING (import_ufo.py:2477-2489, restriction-and-coupling-orders.md) and
  a later `generate ... NP=1` fails the order-validity check (that check is coupling-order/eft's
  slice; the vertex-removal that STARVES it is ours).
- A card with WCs at distinct nonzero values (a "massless"-style file) → operators kept, NP
  order valid. The distinct-nonzero requirement is the same anti-merge idiom SMEFTatNLO uses.
- A `massless` vs `SMlimit_massless` style naming distinction (if SMEFTsim ships such files)
  maps exactly onto the "distinct-nonzero ⇒ operators ON / NP valid" vs "all-zero ⇒ operators
  pruned / NP invalid" mechanism above. Confirm the actual SMEFTsim file names/contents by
  reading the installed model if/when SMEFTsim is present; the mechanism needs no re-derivation.

## value == 1.0 is a CONVERSION, not a merge (a distinct WC hazard)
Setting a WC to exactly `1.0` does NOT prune it and does NOT merge it — it hits the one-list
in `detect_special_parameters` (import_ufo.py:2623) and `fix_parameter_values` converts it
external→internal fixed at 1.0. The operator's vertices SURVIVE (coupling nonzero), but the
coefficient stops being a free param_card line — it is hard-wired to 1.0 and cannot be varied
or scanned. Two WCs both set to 1.0 do NOT merge with each other either (2724 skips value 1),
they each independently convert. This is why the SMEFT cards use random fractions in (0,1)
rather than 1.0: distinct fractions keep every coefficient FREE and independent. A doc that
lumps "1.0" together with "same value" as a single merge hazard is imprecise — 1.0 is a
conversion (loses freedom), a generic shared value is a merge (loses independence).

## Cautions
- **Picking the wrong card silently changes the operator set.** `SMEFTatNLO-NLO_no4q` silently drops all four-quark operators; a user who needs cQq/ctq/... in a tt+jets EFT analysis but typed `-NLO_no4q` gets them pruned with no error (only model-modification-level log lines "remove interactions"). `-default` (or bare `import model SMEFTatNLO`) drops ALL dim-6 — easy to do by accident and get pure SM.
- **Distinct-value idiom is fragile by design.** If a model author adds a new operator to the card but copy-pastes an existing coefficient's value into the SAME block, `detect_identical_parameters` will merge the two and the second operator becomes non-independent (rule_card `add_identical`). The random fractions exist precisely to prevent this; they are not physics.
- **Opposite-value trap:** `detect_identical_parameters` also matches `(lhablock, -value)` with coeff -1 (detection at import_ufo.py:2729/2734-2735) → two same-block coeffs that are exact negatives are grouped, and `merge_iden_parameters` then emits an `add_opposite` rule (2846-2848, not `add_identical`). SMEFT cards use all-positive fractions, so this is dormant here, but a card author using ±x in one block would trigger it.
- The dim-6-squared / linear-vs-quadratic choice is NOT a restriction concern — it is a coupling-order / `NP` interaction-order matter at generate time, not something the restrict card controls. Restriction only decides which operators EXIST in the operative model.
- For what restriction does to the coupling-ORDER labels themselves (do NP/QED/QCD survive merging; can an order be dropped entirely), see restriction-and-coupling-orders.md — restriction's merge is order-aware (never collapses an NP coupling into an SM one), but zeroing every operator of an order drops the order with a WARNING and wipes `order_hierarchy`/`expansion_order`.
