---
description: How SMEFTatNLO is loop-capable — QCD-only perturbative expansion, NP power counting carried in CT coupling order dicts, NO CT_parameters.py (UV renorm lives in CT_couplings UVGC pole dicts), restrict_LO/NLO/no4q hazards. Loop capability is IDENTICAL across -LO/-NLO (restrict card does not gate it); -NLO vs -LO differ by internal widths + five operators (cG,cpG,ctlS3,ctlT3,cblS3) turned OFF at NLO, NOT by CT pruning.
---

# SMEFTatNLO loop structure (NLO-QCD EFT)

(v3.7.1, `$MADGRAPH_INSTALL/models/SMEFTatNLO` when installed — an external/FeynRules model that
lives under models/ only if locally installed, NOT in `_online_model`; verify presence with `ls`,
it is build-dependent and absent on some installs.) SMEFT@NLO v1.0.3, arXiv:2008.11743. This is the
concrete SMEFT-at-NLO instance of the generic loop-UFO machinery; it differs from loop_sm in
two load-bearing ways (no CT_parameters.py; NP power counting in CT order dicts).

## Loop capability: QCD-only perturbative expansion
`coupling_orders.py` (live-read):
- `NP  = CouplingOrder(expansion_order=2, hierarchy=1)` — NO perturbative_expansion → 0.
- `QCD = CouplingOrder(expansion_order=99, hierarchy=2, perturbative_expansion=1)` → perturbed.
- `QED = CouplingOrder(expansion_order=99, hierarchy=4)` — NO perturbative_expansion → 0.
Applying the importer's own predicate (`import_ufo.py:501`, `perturbative_expansion>0`): only
QCD qualifies. So `perturbation_couplings == ['QCD']` — **NLO QCD only**. There is NO NLO-EW /
NLO-QED in SMEFTatNLO, and the EFT order NP is NOT itself perturbed (you don't "loop in" extra
operator insertions; loops are QCD on a fixed NP order).
Live import confirms: model class `RestrictModel` (a LoopModel subclass), `get('perturbation_
couplings') == ['QCD']`, `gauge=[0,1]`.

## NP power counting is carried in the CT coupling `order` dict
This is the SMEFT-specific mechanism. Most UVGC/R2GC counterterm Couplings in `CT_couplings.py`
carry `'NP':2` in their `order` dict (amplitude-squared dim-6 level; a single dim-6 insertion is
NP=1 in the amplitude, so an interference/squared CT piece is NP=2) — but NOT all (see the
SM-sector subsection below; an NP-less minority coexists — read counts fresh, they drift).
Representative (`CT_couplings.py:8168`):
```
UVGC_1646_1 = Coupling(name='UVGC_1646_1',
   value = {-1:'(-5*ctG*G**3)/(16.*cmath.pi**2*Lambda**2*cmath.sqrt(2))'},
   order = {'NP':2,'QCD':3,'QED':1})
```
Reads as: the UV counterterm of the chromomagnetic operator `ctG` (the `1/Lambda**2`,
Wilson-coeff `ctG`) at one QCD loop carries NP=2 (EFT level), QCD=3 (one extra power of G**3
from the loop renormalization), single pole `{-1:...}`. This is how the counterterm preserves
EFT power counting: the renorm constant of a dim-6 operator lives at the same NP order as the
operator's tree contribution, with the loop adding QCD powers — so MadGraph's coupling-order
bookkeeping keeps the CT in the right NP slice automatically. Order-dict population observed
across `CT_couplings.py`: many each of `{'NP':2,'QCD':2}`, `{'NP':2,'QCD':2,'QED':1}`,
`{'NP':2,'QCD':3}`, etc. (dict forms durable; multiplicities drift — enumerate live with
`grep -oE "order = \{[^}]*\}" CT_couplings.py | sort | uniq -c`).

### NOT all CT couplings carry NP — some are pure-SM-sector
The durable fact: MOST CT Coupling blocks carry `'NP':2`, but a minority carry NO `'NP'` key.
Read the split fresh (drift-prone counts): total blocks `grep -c "= Coupling(" CT_couplings.py`;
NP-carrying `grep -c "'NP':" CT_couplings.py`; the difference is the NP-less set.
The NP-less ones are the **pure-SM-sector** renormalization counterterms the EFT model
still needs — e.g. `R2GC_1302_474 = Coupling(value='-G**4/(192.*cmath.pi**2)',
order={'QCD':4})`. Their order dicts are `{'QCD':4}`, `{'QCD':2,'QED':1}`, `{'QCD':3}`,
`{'QCD':2,'QED':2}`, `{'QCD':2}`, `{'QCD':3,'QED':1}` (forms durable; multiplicities drift).
So the model carries BOTH the dim-6-operator CTs (NP=2) AND the SM-sector CTs (no NP) — the
NLO QCD computation renormalizes the SM part of the EFT too, not only the operators. Every NP
value observed is exactly 2 (no NP=1 or NP=4 CT couplings — durable structural fact):
`grep -oE "'NP':[0-9]+" CT_couplings.py | sort -u` returns only `'NP':2`.

## NO CT_parameters.py — UV renorm lives in CT_couplings pole dicts
Unlike loop_sm (which ships CT_parameters.py with CTParameter Laurent renorm constants),
**SMEFTatNLO has NO CT_parameters.py file** (`ls` → absent). `__init__.py:45-49` does
`try: import CT_parameters` and the ImportError is swallowed, so `all_CTparameters` is never
set on the module (importer then skips all CTParameter steps via `hasattr` guard at
import_ufo.py:549/595). NB this no-CT_parameters pattern is the COMMON bundled-loop-model
case, not a SMEFT quirk: loop_sm is the ONLY bundled loop model carrying CT_parameters.py;
SMEFTatNLO + all three 2HDM-NLO models encode renorm as CT_couplings pole dicts — see
bsm-nlo-2hdm-loop-structure for the cross-model dichotomy and the two distinct `__init__`
skip-mechanisms. Consequence: the EPS/FIN CTParameter fan-out machinery
(ctparameter-eps-fin-expansion page) does NOT fire for SMEFTatNLO — `get_additional_CTparameters`
finds nothing. Instead the renormalization is encoded directly in the CT *couplings*: each UVGC
Coupling's `value` is a pole-keyed dict (`{-1:...}` single pole, `{0:...}` finite). The Laurent
unfolding in `add_CTinteraction` still applies (per-pole + per-loop_particle + per-order split);
it just operates on coupling pole dicts, not on CTParameter-derived params.
- `CT_couplings.py` is loaded transitively: `CT_vertices.py:8` does `import CT_couplings as C`
  (NOT via __init__). No double pole anywhere (`grep "{-2:"` → 0 hits) — consistent with the
  importer's `poleOrder==2 → InvalidModel` rule (UV renorm is at most 1/eps).

## CT vertex types (live import)
Raw `CT_vertices.py` carries `type='R2'` and `type='UV'` only (no explicit UVtree/UVmass/UVloop
literals; counts drift — `grep -oE "type='[^']*'" CT_vertices.py | sort | uniq -c`).
After import auto-classification (`import_ufo.py` UV→UVmass/UVloop guess + Laurent
unfolding), the live interaction-type counts include: `R2`, `UVloop`, `UVloop1eps`, `UVmass`,
`UVmass1eps`, plus `base` (ordinary tree interactions). The `1eps` suffixed types are the
single-pole pieces split out by Laurent unfolding.

## Restriction-card hazards (LO vs NLO vs no4q)
SMEFTatNLO ships `restrict_default.dat`, `restrict_LO.dat`, `restrict_NLO.dat`,
`restrict_NLO_no4q.dat`. (The restriction *algorithm* is the
restriction slice's; what each ENABLES for a loop run is in-slice here.)

**Loop capability is IDENTICAL across `-LO` and `-NLO` — the restrict card does NOT gate it.**
Both variants import the same UFO: same `coupling_orders.py` (QCD `perturbative_expansion=1`)
and same `CT_vertices.py`/`CT_couplings.py`, all read at UFO-import time BEFORE `RestrictModel`
runs on the already-built model. So `import model SMEFTatNLO-LO` ALSO yields a LoopModel with
`perturbation_couplings==['QCD']`; the CT/R2/UV structure survives in both. The "`-LO` is LO
only, `-NLO` adds counterterms" doc phrasing is **misleading if read as "restrict_LO prunes the
CT couplings"** — it does not. The real card differences (per `diff restrict_LO.dat
restrict_NLO.dat`) are two, both about *content selection*, not loop-machinery pruning:
- **Internal widths.** NLO restriction **zeroes goldstone/ghost widths** (ghZ/ghWp/ghWm/G0/G+):
  nonzero in `restrict_LO.dat` (around `:88-93`) vs exactly 0. in `restrict_NLO.dat` — read the
  cited lines for the values; the LO-nonzero→NLO-zero *contrast* is the durable fact. Rationale:
  on-shell unstable internal particles would break the loop integrand / IR structure.
  (Quark/lepton/γ/g widths are 0 in BOTH.) Picking `restrict_LO.dat` for a loop run is a
  source-visible width hazard.
- **Operators turned OFF at NLO.** `restrict_NLO.dat` sets to EXACTLY `0.000000` (⇒ pruned per
  the restriction premise) five Wilson coeffs that `restrict_LO.dat` leaves nonzero:
  **`cG` (:105), `cpG` (:106)** (pure-gluonic + Higgs-gluon dim-6, block param 7/8) and
  **`ctlS3` (:178), `ctlT3` (:179), `cblS3` (:180)** (semileptonic scalar/tensor 4-fermion).
  These operators exist at LO tree level but are DISABLED in the NLO model (their NLO-QCD
  renormalization is not provided). So `-NLO` is not a superset of `-LO` at the operator level —
  it drops these five while gaining the width treatment for loops.
- Random per-parameter benchmark draws differ across ALL params (restriction randomization) —
  irrelevant to structure; do not read a nonzero-vs-nonzero value change as meaningful.
- `restrict_NLO` vs `restrict_NLO_no4q`: identical except the `no4q` variant **zeroes the
  four-quark operator Wilson coefficients** (cQq83, cQq81, cQu8, ctq8, cQd8, ctu8, ctd8, cQq13,
  cQq11, cQu1, ctq1, cQd1, ctu1, ctd1, cQQ8, cQQ1, cQt1, ctt1, cQt8 — Block lines 139-157).
  Use `no4q` when the four-quark operators' NLO QCD pieces are unwanted/incomplete for the
  process at hand.

## Distinction from the `heft` model / HEFT-TIR branch
SMEFTatNLO is a renormalizable-EFT completion with a DYNAMICAL Higgs — it is NOT the `heft`
online model (which has a fundamental ggH effective vertex). The TIR `HAS_AN_HEFT_VERTEX`
branch (heft-tir-vertex-branch page) is a structural runtime detection (massive-scalar +
massless-vector loop), orthogonal to SMEFT loop capability. Do not conflate "SMEFT at NLO"
with the HEFT-vertex TIR handling.

## Probe-candidates (runtime, not yet probe-verified)
- (cheap) `import model SMEFTatNLO-NLO; generate p p > t t~ [QCD]` — does it generate loop +
  CT diagrams cleanly with the NP order respected? (expected: yes, QCD-only NLO).
- (cheap) `generate p p > t t~ [QED]` against SMEFTatNLO → expected REJECTED (QED not in
  perturbation_couplings; Gate-2 / CheckLoop path).
- (expensive) full launch of a dim-6 NLO-QCD process to confirm NP-order CT bookkeeping in the
  written matrix element.
