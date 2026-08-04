---
description: Mapping a physics operator name (e.g. O_lq^(1)) to the correct DIM6* lhablock and parameter name in SMEFTatNLO — block naming encodes fermion content, procedure to verify by vertex legs.
---

# SMEFTatNLO operator identification: physics name → block → parameter (v3.7.1)

When the prompt names a physics operator (e.g. $O_{\ell q}^{(1)}$, $O_{qq}^{(1)}$, $O_{Qd}^{(8)}$), mapping it to the correct lhablock and parameter name in the SMEFTatNLO param_card requires reading the block's fermion content, not assuming the block name.

## Block naming encodes fermion content

SMEFTatNLO Wilson-coefficient blocks are named by the fermion composition of the operator:

| Block | Fermion content | Example operators |
|---|---|---|
| `DIM6` | Bosonic (no fermions) | `cpDC`, `cpWB`, `cG`, `cpG` |
| `DIM62F` | 2 fermions (currents + dipoles) | `cpQ3`, `ctW`, `ctG`, `cpe` |
| `DIM64F` | 4 fermions, **all quarks** | `cQq11`, `cQq13`, `cQQ1`, `cQu1`, `cQd1`, `ctt1` |
| `DIM64F2L` | 4 fermions, **2 leptons + 2 quarks** (semileptonic) | `cQlM1`, `cQlM2`, `cQl31`, `cQe1`, `ctl1` |
| `DIM64F4L` | 4 fermions, **4 leptons** | `cll1111`, `cll2222`, `cll3333` |

**Key rule:** `DIM64F` means 4-fermion **all-quark**, NOT "4-heavy-quark". `DIM64F2L` is semileptonic (lepton-quark). `DIM64F4L` is 4-lepton. The naming is literal: the `2L` suffix means "2 leptons" (the other 2 fermions are quarks), and `4L` means "4 leptons".

## Failure mode: wrong block for a named operator

Setting parameter `cQq11` in Block `DIM64F` to affect $O_{\ell q}^{(1)}$ (semileptonic $\ell$-$\ell$-$q$-$q$) is **wrong**. `cQq11` in `DIM64F` is the four-**quark** operator $O_{qq}^{(1)}$. The semileptonic $O_{\ell q}^{(1)}$ is `cQlM1` in Block `DIM64F2L`, lhacode 1.

**Verification** (source-grounded): `parameters.py` declares `cQlM1` with `lhablock='DIM64F2L'`, `lhacode=[1]`, texname `c_{Ql1}^{(-)}`. The coupling `GC_79 = '(cQlM1*complex(0,1))/Lambda**2'` carries `order={'NP':2}`. Vertex `V_370` uses `GC_79` with particles `b~ b e+ e-` — both quark and lepton legs, confirming semileptonic.

## Procedure: verify the block by checking vertex particles

When mapping a physics operator name to a SMEFTatNLO parameter:

1. **Identify the fermion content** of the operator from its name (e.g., $\ell q$ = lepton + quark = semileptonic → `DIM64F2L`).
2. **Search the correct block** for the matching texname or parameter name in `parameters.py`.
3. **Verify by the vertex:** trace the coupling to a vertex in `vertices.py` — a semileptonic operator **must** have both lepton and quark legs. A four-quark operator has only quarks. If the vertex legs contradict the operator's fermion content, you are in the wrong block.

**Never assume the block name from memory.** The block taxonomy is `eft-model-content-wilson-coupling-vertex.md`; the restrict-card zeroing per block is `smeftatnlo-restrict-card-taxonomy.md`.

## Declared-but-inert operators — a param-card line does NOT mean a usable vertex

A Wilson coefficient having a `parameters.py` entry (and thus a param_card line) does NOT guarantee it does
anything — some are declared but referenced by no coupling. Verify by grepping the coefficient name in
`couplings.py` (LO/tree couplings) and `CT_couplings.py` (NLO counterterm couplings):

| coeff | block | couplings.py | CT_couplings.py | status |
|---|---|---|---|---|
| `cG` (triple-gluon O_G) | DIM6, code 7 | 0 | 0 | **inert at ALL orders** — declared, never used |
| `ctlS3` | DIM64F2L, code 19 | 0 | 0 | **inert at ALL orders** |
| `ctlT3` | DIM64F2L, code 20 | 4 | 0 | **LO-only** (tree couplings, NO NLO counterterm) |
| `cblS3` | DIM64F2L, code 21 | 1 | 0 | **LO-only** |
| `cll1111` (4-lepton) | DIM64F4L, code 1 | 0 | 0 | **inert at ALL orders** (four-lepton excluded) |
| `ctG` (chromomagnetic) | DIM62F, code 24 | 10 | 599 | active LO + NLO |

Mechanism: **LO-only** = has entries in `couplings.py` but zero in `CT_couplings.py`, so its UV divergence
has no counterterm → cannot renormalize → the `restrict_NLO` card zeros it (cG/cpG/ctlS3/ctlT3/cblS3 are the
5 operators LO→NLO drops, per smeftatnlo-restrict-card-taxonomy.md). **Inert at all orders** = zero
references anywhere → setting its value never changes a cross-section (the silent no-op face of
clean-run-not-correct-physics). Top-FCNC exclusion (flavor-changing top vertices absent) is NOT settled by a
name grep — it needs a vertices.py leg-flavor walk (GAP / probe-candidate).

`ctG` normalization: couplings.py value expressions are `ctG*G/Lambda**2` (G = strong coupling gs is an
explicit factor), so the chromomagnetic vertex carries gs·ctG/Λ² (i.e. ctG = gs·c_tG in the coupling
value). Whether the input `ctG` equals the Warsaw C_tG or already absorbs gs is the external definitions.pdf
convention (GAP — not resolvable from UFO source alone).

## Boundary

- The Warsaw basis operator naming convention and which operator controls which physical process is ma-physics-consultant's territory.
- The restrict-card selection (which operators survive under each restriction) is covered in `smeftatnlo-restrict-card-taxonomy.md`.
- Param-card editing mechanics (overwriting Wilson coefficient values) are param-card slice.