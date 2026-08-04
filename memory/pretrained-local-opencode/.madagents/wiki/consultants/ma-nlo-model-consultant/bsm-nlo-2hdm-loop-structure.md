---
description: The 2HDM-family NLO loop models (BSM, not EFT; build-dependent presence — absent on some installs) — QCD-only, pure QCD/QED CT order dicts (no BSM order), and the cross-model CT_parameters.py dichotomy (loop_sm uses the CTParameter renorm pattern; SMEFTatNLO + the 2HDM-NLO family encode renorm as CT_couplings pole dicts instead, per-model when installed).
---

# Bundled BSM-NLO loop models (2HDM family) + the CT_parameters dichotomy

(v3.7.1, `$MADGRAPH_INSTALL/models/`.) Whether these models are installed is VOLATILE — live `>0`
scan, single source of truth for membership/count is bundled-online-loop-models; do NOT restate
the count here (they are ABSENT on the current build, present on the authoring build — build-drift).
The durable per-model BSM facts (whenever installed): the **2HDM-NLO family** — `2HDM5F_NLO`,
`2HDMtII_NLO`, `2HDMtypeII` (three distinct directories, all loop-capable; `2HDMtypeII` is NOT
a mis-transcription of `2HDMtII_NLO` — both exist with their own CT files) — are canonical
BSM (non-EFT) NLO-QCD models. This page is their loop structure and the cross-model
CT_parameters.py pattern that distinguishes loop_sm from the other loop models.

## The three bundled 2HDM-NLO models
`models/2HDM5F_NLO`, `models/2HDMtII_NLO`, `models/2HDMtypeII` — all loop-capable
(`coupling_orders.py` QCD `perturbative_expansion=1`, QED absent→0; `expansion_order=99`
on both orders). So `perturbation_couplings == ['QCD']` — **NLO QCD only**, like loop_sm
and SMEFTatNLO. `gauge = [0, 1]` (unitary-or-Feynman; NOT Feynman-forced — consistent with
QCD-only, the EW/QED gauge-forcing branch does not apply). These are renormalizable BSM
(two-Higgs-doublet) models at NLO-QCD, NOT EFTs.

CT file inventory (presence is durable; counts are drift-prone — read fresh, don't cache):
| model       | CT_vertices.py | CT_couplings.py | CT_parameters.py | raw CTVertex types |
|-------------|----------------|-----------------|------------------|--------------------|
| 2HDM5F_NLO  | yes            | yes             | **NO**           | R2, UV only        |
| 2HDMtII_NLO | yes            | yes             | **NO**           | R2, UV only        |
| 2HDMtypeII  | yes            | yes             | **NO**           | R2, UV only        |

Read a count when needed: `grep -c "= Coupling(" models/<m>/CT_couplings.py` (CT coupling blocks),
`grep -oE "type = '[^']*'" models/<m>/CT_vertices.py | sort | uniq -c` (R2/UV split).
(`2HDMtII_NLO` vs `2HDMtypeII` `coupling_orders.py` differ only in the FeynRules header
comment — same QCD/QED order structure.) Raw CTVertex types are only `R2`/`UV` (no explicit
UVtree/UVmass/UVloop literals) — the importer auto-classifies `UV`→UVmass/UVloop at
import_ufo.py:1568-1579 (see ct-files-and-vertex-types).

## CT order dicts are pure QCD/QED — no BSM order rides in them
Unlike SMEFTatNLO (whose CT couplings carry `'NP':2`, the EFT power-counting order — see
smeft-at-nlo / eft-coupling-orders pages), the 2HDM-NLO CT coupling `order` dicts are
**pure QCD/QED** (2HDM5F_NLO `CT_couplings.py`; enumerate live with
`grep -oE "order = \{[^}]*\}" CT_couplings.py | sort | uniq -c`): only
`{'QCD':2,'QED':1}`, `{'QCD':2,'QED':2}`, `{'QCD':4}`, `{'QCD':3}`, `{'QCD':2}`,
`{'QCD':3,'QED':1}` appear — the dict *forms* are the durable fact, the multiplicities drift.
No 2HDM-specific order in any CT dict. This is the
structural EFT-vs-renormalizable-BSM distinction: a renormalizable BSM model has NO extra
power-counting order to preserve in its counterterms — only the SM gauge orders QCD/QED. The
EFT NP-in-CT-order-dict mechanism (eft-coupling-orders page) does NOT appear here.

Renorm pole structure: 2HDM5F_NLO `CT_couplings.py` value dicts are single-pole `{-1:...}` +
finite `{0:...}` only, with ZERO double poles (`grep "{-2:" CT_couplings.py` → 0 — the durable
fact), consistent with the importer's `poleOrder==2 → InvalidModel` rule (ct-files-and-vertex-types).

## The CT_parameters.py dichotomy across the loop models (load-bearing)
Of the loop models examined (loop_sm + SMEFTatNLO + the three 2HDM-NLO), **only loop_sm ships
CT_parameters.py**; every other encodes renormalization directly in CT_couplings pole dicts
(per-model facts below — which are installed is volatile, the dichotomy is the durable fact):
- `loop_sm`     — CT_parameters.py PRESENT → CTParameter EPS/FIN machinery fires
  (ctparameter-eps-fin-expansion); count via `grep -c "CTParameter(" models/loop_sm/CT_parameters.py`.
- `SMEFTatNLO`  — NO CT_parameters.py → renorm in CT_couplings pole dicts.
- `2HDM5F_NLO`  — NO CT_parameters.py → renorm in CT_couplings pole dicts.
- `2HDMtII_NLO` — NO CT_parameters.py → renorm in CT_couplings pole dicts.
- `2HDMtypeII`  — NO CT_parameters.py → renorm in CT_couplings pole dicts.
So loop_sm is the **exception**, not the template: the CTParameter Laurent-renorm-constant
pattern is loop_sm-specific; the common bundled-loop-model pattern (4 of 5) is
pole-dict-in-CT_couplings. Do not assume a loop UFO carries CT_parameters.py.

### TWO distinct "no CTParameter machinery" mechanisms — both caught by the importer guard
The importer guards every CTParameter step with `hasattr(self.ufomodel,'all_CTparameters')`
(`import_ufo.py:549` and `:595`, verbatim `if hasattr(self.ufomodel,'all_CTparameters'):`;
also `:2088`). When `__init__.py` never sets `all_CTparameters`, every CTParameter step is
silently skipped — `treat_couplings` is not even called (`:595` gates it). The four
non-loop_sm models reach this skip by TWO different `__init__.py` shapes:
- **SMEFTatNLO**: `__init__.py:45-49` HAS a `try: import CT_parameters / except ImportError:
  pass` block — the file is absent so the ImportError is swallowed, `all_CTparameters` never
  set. (My smeft-at-nlo page's "ImportError swallowed" framing is correct *for SMEFTatNLO*.)
- **2HDM-NLO**: `__init__.py` has NO `import CT_parameters` block at all (`grep CT_parameter
  2HDM5F_NLO/__init__.py` → nothing) — the attribute is simply never set; there is no import
  to fail. CT_couplings is loaded transitively (`CT_vertices.py:8 import CT_couplings as C`),
  and `__init__.py` only does `try: import CT_vertices / except ImportError: pass` (:38-43)
  → `all_CTvertices`. So "no try-block" vs "try-block-with-swallowed-ImportError" both end at
  the same importer `hasattr` skip.
- **loop_sm** contrast: `__init__.py` explicitly `from . import CT_couplings/CT_parameters/
  CT_vertices` (:5,8,10) and sets `all_CTparameters = CT_parameters.all_CTparameters` (:25)
  → the attribute exists → the CTParameter machinery runs.

## Cautions
- A loop UFO with no CT_parameters.py is NORMAL and NLO-correct (renorm in CT coupling pole
  dicts). Absence of CT_parameters.py is NOT a sign of an incomplete/LO model — the only
  loop-capability test remains `perturbative_expansion>0` over coupling_orders.py.
- Do not assume CT order dicts carry a BSM order. Renormalizable BSM (2HDM) CTs carry only
  QCD/QED; only EFTs (SMEFTatNLO) carry the operator order (NP) in their CT dicts. If a
  reasoning step expects a BSM order in a 2HDM counterterm, it is wrong.
- All three 2HDM-NLO models are QCD-only NLO (`perturbation_couplings == ['QCD']`, durable
  per-model fact). Whether ANY bundled model perturbs QED is build-volatile (the only QED
  candidate is the SM model loop_qcd_qed_sm, not a BSM model) → route to
  bundled-online-loop-models, do not assert here.
