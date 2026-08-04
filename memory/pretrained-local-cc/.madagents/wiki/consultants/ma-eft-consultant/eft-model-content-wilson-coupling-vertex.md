---
description: What an EFT UFO adds to the SM — Wilson coeffs (external params in DIM6* lhablocks) → coupling values = coeff/Lambda**2 carrying an NP/DIM6 order → effective vertices; why the per-insertion increment is model-specific.
---

# EFT model content: Wilson coeff → coupling (1/Lambda²) → order → vertex (v3.7.1)

How an EFT UFO encodes "dim-6 operators on top of the SM" as concrete UFO objects, and why
the per-insertion power-counting increment differs between models. This is the **model-content**
angle (the objects the model adds); the truncation/parser side is in eft-power-counting-parser.md
and eft-order-token-rewriting.md, the restrict-card zeroing in smeftatnlo-restrict-card-taxonomy.md.

## The four-link chain (verified SMEFTatNLO + dim6top_LO_UFO)

1. **Wilson coefficients are `external` real parameters**, grouped into EFT-specific `lhablock`s.
   - `SMEFTatNLO/parameters.py`: e.g. `cpDC = Parameter(nature='external', type='real', value=…,
     lhablock='DIM6', lhacode=[2])` (read the default off parameters.py); `cbp ... lhablock='DIM62F',
     lhacode=[18]`. The `lhablock` (not the python attr) is what appears in the generated `param_card.dat`.
   - `Lambda = Parameter(nature='external', type='real', value=…, lhablock='DIM6', lhacode=[1])`
     is the EFT cutoff scale, also external (SMEFTatNLO parameters.py:46; dim6top parameters.py:20) —
     read its default off parameters.py, do not cache the number.
2. **A coupling value literally is the Wilson coefficient over Lambda².**
   - `SMEFTatNLO/couplings.py GC_13`: `value = '(2*cdp*complex(0,1))/Lambda**2 -
     (cpDC*complex(0,1))/(2.*Lambda**2)'`, `order = {'NP':2,'QED':2}`.
   - dim6top: `value = '-(cblSI1/Lambda**2) + (cblS1*complex(0,1))/Lambda**2'` (DIM6:1);
     FCNC couplings same `/Lambda**2` shape with flavour-indexed coeffs (`cblSx1x13` etc.).
   - **Every** EFT coupling carries exactly one power of `1/Lambda**2` = one dim-6 insertion:
     in SMEFTatNLO every NP-bearing coupling has `Lambda**2` (not `Lambda**4`) in its value and
     `'NP':2` in its order dict — **no `'NP':4` coupling** (no single vertex with two insertions), and
     `'NP':2` is the only NP value present (no `'NP':1`). Recipe: `grep -oE "'NP': ?[0-9]+" couplings.py
     | sort | uniq -c` (mind the optional space — `"'NP': ?2"`, else the count is 0). Read the tally
     fresh; the point is that only `'NP':2` appears, not any particular count.
3. **The coupling carries the EFT coupling-order in its `order` dict** (`{'NP':k,...}` /
   `{'DIM6':1,...}` / `{'FCNC':1,...}`). This is where the power-counting integer lives.
4. **Vertices inherit the order through the coupling they reference.** A `Vertex(... couplings =
   {(c,l):C.GC_13})` uses `GC_13`, so the diagram picks up `GC_13`'s `NP:2`. (SMEFTatNLO V_13 is a
   Goldstone 4-point using `C.GC_13`.) The vertex objects themselves carry no order; the order rides
   on the coupling. This is why zeroing a Wilson coeff in a restrict card removes the *interaction*:
   the coupling value collapses and restriction strips the vertex (smeftatnlo-restrict-card-taxonomy.md).

## Why the per-insertion increment is model-specific (the key cross-model fact)

The SAME physics — **one dim-6 insertion = one power of 1/Lambda²** — is encoded with a DIFFERENT
order increment in different UFOs:

| model | EFT order(s) | increment per 1/Lambda² | coupling_orders expansion_order |
|---|---|---|---|
| `SMEFTatNLO` | `NP` | **+2** (every NP coupling `'NP':2` in couplings.py) | NP: 2 |
| `dim6top_LO_UFO` | `DIM6`, `FCNC` | **+1** (`DIM6:1` / `FCNC:1` in couplings.py) | DIM6/FCNC: 99 |

Both models put exactly `1/Lambda**2` in the coupling value; only the integer in the `order` dict
differs. **Consequence:** "linear in EFT" (interference, SM×dim6) is `NP=2` in SMEFTatNLO but `DIM6=1`
in dim6top; "squared" (dim6²) is `NP^2=4` vs `DIM6^2=2`. The factor-2 convention in SMEFTatNLO makes
`NP` count amplitude×amplitude cleanly (squared amp at `NP^2 = 2×amp-order`). NEVER assume an
increment — read the active model's `couplings.py` order dict. (Recorded also in bundled-eft-models.md;
this page adds the *why*: it is the Lambda² power that is physical, the integer is convention.)

## Wilson-coefficient block taxonomy is the operator catalog (model content)

The `lhablock` of the external coeffs IS the operator-class catalog the model adds to the SM:
- `SMEFTatNLO/parameters.py` external coeff blocks (grep `lhablock = '...'` — SPACED form): five
  Wilson blocks **DIM6** (bosonic, incl. lhacode 1 = cutoff `Lambda`, NOT an operator),
  **DIM62F** (2-fermion currents+dipoles), **DIM64F** (4-fermion all-quark, incl. light-quark-coupling
  ops — NOT "4-heavy"; smeftatnlo-restrict-card-taxonomy.md), **DIM64F2L** (4-fermion
  2-lepton), **DIM64F4L** (4-lepton).
- `dim6top_LO_UFO/parameters.py`: two Wilson blocks **DIM6** (flavour-conserving, incl. lhacode 1 =
  Lambda) and **FCNC** (flavour-changing — the larger set here; dim6top-fcnc-second-eft-order.md).
- **The per-block entry counts, lhacode→coeff maps, and shipped default values are the SINGLE SOURCE
  OF TRUTH in eft-wilson-coeff-param-card-generation.md** (volatile counts — do not restate them here;
  this page records only that the blocks ARE the model's *external-parameter* operator catalog).
  smeftatnlo-restrict-card-taxonomy.md covers which restrict card zeroes which (its per-block counts can
  differ — restriction drops entries).

## SM gauge self-couplings are dim-4; aTGC/dim-6 SMEFT are deviations ON TOP (framing trap)

A common category error: calling an SM tree-level triple-gauge-coupling (TGC) effect "anomalous TGC /
dim-6 / SMEFT". The SM gauge self-couplings WWZ and WWγ are **dim-4** and present in the default `sm`
UFO out of the box — no EFT model needed:
- `sm/couplings.py:220` `GC_53 = (cw*ee*complex(0,1))/sw`, **`order = {'QED':1}`** — the WWZ trilinear,
  dimension-4 (one power of `ee`, QED:1).
- `sm/coupling_orders.py` declares **only QCD and QED** — there is **no `NP`/`DIM6`/`EFT` order in
  default `sm`** (grep `name='(NP|DIM6|EFT|FCNC)'` → NONE). So a `NP=…` constraint is meaningless in
  `sm`; you cannot select a "dim-6 TGC" there because none exists.

aTGC / dim-6 SMEFT operators (Warsaw O_W, O_WWW; SMEFTatNLO, SMEFTsim, EWdim6/TopEffTh online) add
operators that **deviate from** the SM g_WWZ baseline — they ride on the EFT machinery this page
describes: external Wilson coeff → coupling `coeff/Lambda**2` → `order={'NP':k,…}` → effective vertex,
and **require a SMEFT/anomalous-coupling UFO** (carries `Lambda`). SMEFTatNLO
TGC-type couplings carry `order={'NP':2,'QED':1}` (e.g. `SMEFTatNLO/couplings.py:15,107,111`) and the
model has external `Lambda` (`SMEFTatNLO/parameters.py:46`, lhablock DIM6). In the
Hagiwara–Peccei–Zeppenfeld parametrization the SM values are g₁ᵛ=1, κᵛ=1, λᵛ=0; aTGC measures the
**deviations** Δg₁, Δκ, λ (HPZ convention; physics-slice for the parametrization detail).
- **Consequence for routing:** if a σ exceeds a naive "ISR off the quark line" estimate (e.g. LO
  pp→W⁺W⁻Z), the excess is the **SM dim-4 WWZ self-coupling**, NOT SMEFT. Attributing it to dim-6 is
  wrong twice over: it needs no EFT UFO/NP-order, and it would falsely predict the SM σ agrees with
  the naive estimate. Don't reach for SMEFT to explain an SM tree-level gauge self-coupling.

## Boundary
- The *physics meaning* of each operator (which SM amplitude it corrects, gauge structure) is
  ufo-slice / ma-physics territory. This page records only the UFO-object encoding: coeff→coupling
  (1/Lambda²)→order→vertex, and that the increment integer is a per-model convention on a physical
  1/Lambda² power. The SM-vertex content itself (GC_53 value/order in default `sm`) is ufo-slice; this
  page cites it only to mark the dim-4-vs-dim-6 boundary.
- The restriction *algorithm* that strips a zeroed-coeff vertex is restriction-slice; param_card
  editing of the coeffs is param-card slice.
