---
description: The task names a physics operator and you must find which parameter carries it in the loaded model.
---

## When it applies

Any prompt that names a specific SMEFT operator (e.g., $O_{\ell q}^{(1)}$, $c_{\ell q}^{(1)}$, $\mathcal{O}_{qq}^{(1)}$) and asks for the corresponding Wilson coefficient in the param_card, or any model import where the task-specific restriction matters.

## The mistake

The lead named `cQq11` (Block DIM64F, lhacode 11) as the param_card parameter for $c_{\ell q}^{(1)}$ (semileptonic ℓℓqq). DIM64F contains four-QUARK operators. The semileptonic operator $O_{\ell q}^{(1)}$ maps to `cQlM1` in Block DIM64F2L (lhacode 1).

## The fix

When the prompt names a physics operator, **verify the parameter-to-operator mapping by reading the model source**:

1. Read `parameters.py` for the lhablock/lhacode — confirmed `cQlM1` at `parameters.py:495-502` (Block DIM64F2L, lhacode 1, texname `c_{Ql1}^{(-)}`).
2. Verify the vertex content in `vertices.py` — `GC_79` (coupling of cQlM1) appears in `V_370` with particles `b~ b e+ e-` (semileptonic, both quark and lepton legs).
3. Use the model's task-specific restriction: `import model SMEFTatNLO-LO` for LO analysis (not bare `SMEFTatNLO`).

## SMEFTatNLO block naming

The block name encodes fermion content:

- **DIM64F** — four-fermion quark-only (cQq11, cQq13, cQQ1, cQu1, cQd1, ctq1, ...)
- **DIM64F2L** — four-fermion with 2 leptons (semileptonic: cQlM1, cQlM2, cQl31, cQe1, ctl1, ...)
- **DIM64F4L** — four-fermion lepton-only (cll1111, cll2222, cll3333, ...)

This naming convention is model-specific; dispatch `ma-eft-consultant` for the exact mapping in the loaded model.

## See also

- [[clean-run-not-correct-physics]] — setting a wrong Wilson coefficient is a silent-physics-wrong failure: the process generates, σ is computed, but for the wrong operator.
- [[eft-smeft-fanout]] — the EFT fanout already routes operator questions to the eft consultant; this lesson hardens that the lead (or consultant) must verify the mapping against source, not memory.