---
description: The four SMEFTatNLO restrict cards (default/LO/NLO/NLO_no4q) — the five DIM6* Wilson-coefficient block taxonomy, which coeffs each card zeroes, and the LO→NLO and NLO→no4q differences.
---

# SMEFTatNLO restrict cards — block taxonomy and card-to-card diff (v3.7.1)

`import model SMEFTatNLO[-LO|-NLO|-NLO_no4q]` selects `restrict_default.dat` / `restrict_LO.dat` /
`restrict_NLO.dat` / `restrict_NLO_no4q.dat`. All four read from
`$MADGRAPH_INSTALL/models/SMEFTatNLO/`. Line counts: default 234, the other three 252 each.
Companion: smeftatnlo-default-restriction-trap.md (why bare-default rejects NP);
coupling-order-validity-from-surviving-interactions.md (the validity mechanism the zeroing triggers).

## The five Wilson-coefficient blocks (grep `^Block` restrict_NLO.dat)
| Block | line | content | example coeffs |
|---|---|---|---|
| `DIM6`     | 98  | bosonic operators              | cpDC, cpWB, cdp, cp, cWWW, **cG**, **cpG**, cpW, cpBB |
| `DIM62F`   | 113 | 2-fermion (current + dipole)   | cpl1-3, c3pl*, cpe/cpmu/cpta, cpQ3, ctp, ctZ, ctW, ctG |
| `DIM64F`   | 138 | 4-fermion all-quark (heavy-Q bilinear × {light-q OR heavy-Q} bilinear) | cQq83, cQq81, cQu8, ctq8, cQd8, ctu8, …, cQQ8/1, cQt1, ctt1, cQt8 |
| `DIM64F2L` | 162 | 4-fermion 2-lepton             | cQlM*, cQl3*, cQe*, ctl*, cte*, **ctlS3**, **ctlT3**, **cblS3** |
| `DIM64F4L` | 185 | 4-lepton                       | cll1111, cll2222, cll3333, cll1122, …, cll2332 |
Plus non-coefficient blocks: SMINPUTS, MASS, DECAY, LOOP, Renor, YUKAWA, QNUMBERS.
**Naming trap:** the "four-quark" coefficients live in block **`DIM64F`**, not `DIM64F4L`.
`DIM64F4L` is the **4-lepton** block (cll****), identical across all of LO/NLO/no4q.

**Flavour-label trap.** Do NOT call `DIM64F` the "4-heavy-quark" block. It is a
4-fermion **all-quark** block whose ops pair a heavy-Q (3rd-gen) bilinear with EITHER a light-quark OR a
heavy-quark bilinear. Several DIM64F ops are **light-quark-coupling** and drive `q q̄ → t t̄` from a
light-quark initial state. Verified (vertices.py, v3.7.1): `cQq83` (with cQq81) sits in coupling
`GC_35 = (cQq81+cQq83)/Lambda**2`, order `{'NP':2}` (couplings.py:1681-1683), which attaches to
vertices `t̄ t ū u`, `c̄ c t̄ t`, `b̄ b d̄ d`, `b̄ b s̄ s` — heavy-Q current × **light-quark** current.
So `cQq83` is a (8,3) `(Q̄_3 Q_3)(q̄ q)` operator, NOT 4-heavy-quark. The purely-4-heavy ops in the block
are cQQ8/cQQ1/cQt1/ctt1/cQt8 (the last 5). `cQq83` param: block `DIM64F` lhacode 1, external
(parameters.py:286-292).

## Per-card zeroing (verified: diffs + awk-grep of `0.000000` per coeff block)
- **`restrict_default.dat`** — **every** Wilson coefficient in all five blocks is `0.` (only the
  scale `DIM6` code 1 (Lambda) is nonzero). **Also** every particle width/decay is `0.` (DECAY 6/23/24/25
  and all the `# X : 0.0` lines). → no NP interaction survives restriction → `NP` order REJECTED
  (the trap). Top/Z/W/H are stable (zero width).
- **`restrict_LO.dat`** — **NO** Wilson coefficient zeroed (all five blocks fully nonzero), AND it
  restores physical widths + decay tables: `DECAY 6 1.4708…` (t→bW), `DECAY 23 2.416…` (Z), `DECAY 24
  2.003…` (W), `DECAY 25 4.088e-03` (H), plus the goldstone/ghost widths (ghZ/ghWp/ghWm/G0/G+ ≈ 2.0-2.5).
  → the full SMEFT operator set is active at LO.
- **`restrict_NLO.dat`** — re-zeroes ONLY the **ghost/goldstone** widths back to `0.` (DECAY
  9000002/9000003/9000004 = ghZ/ghWp/ghWm, DECAY 250/251 = G0/G+; LO had ghZ/G0=2.4952,
  ghWp/ghWm/G+=2.085). **The physical t/Z/W/H widths are KEPT nonzero and byte-identical to LO**
  (DECAY 6=1.4708, 23=2.416023, 24=2.00295, 25=4.088e-03) — NLO does NOT re-zero them (verified:
  the only LO↔NLO decay diff is the 5 ghost/goldstone lines). Also zeroes **5 NLO-incompatible
  operators**: `cG` (DIM6 7), `cpG` (DIM6 8), `ctlS3` (DIM64F2L 19), `ctlT3` (DIM64F2L 20),
  `cblS3` (DIM64F2L 21). All other coeffs nonzero. The DIM64F (4-fermion all-quark) block stays nonzero.
- **`restrict_NLO_no4q.dat`** — identical to NLO **plus** the entire `DIM64F` block zeroed (the
  4-fermion all-quark coeffs: cQq83, cQq81, cQu8, ctq8, cQd8, ctu8, ctd8, cQq13, cQq11, cQu1, ctq1, cQd1,
  ctu1, ctd1, cQQ8, cQQ1, cQt1, ctt1, cQt8). cG/cpG/ctlS3/ctlT3/cblS3 are zeroed in both NLO cards.
  The 4-LEPTON block `DIM64F4L` is UNCHANGED between NLO and no4q (the diff is purely the DIM64F lines
  and nothing else — verify with `diff restrict_NLO.dat restrict_NLO_no4q.dat`).
  **no4q zeros EVERY DIM64F op, including the light-quark-coupling cQq83** (nonzero under NLO →
  `0.000000` under no4q, `# cQq83` at restrict_NLO_no4q.dat:139 — read the zero/nonzero status there).
  Consequence: under `SMEFTatNLO-NLO_no4q`, `set cQq83 1.0` is **inert** — the operator's vertices were
  stripped at restriction, so a qq̄→tt̄ NLO σ comes back ≈ σ_SM_NLO silently (no warning). LO keeps cQq83
  nonzero (restrict_LO.dat:139); the knob only bites under LO/NLO, not no4q. So "no4q = drop 4-quark
  contamination" includes the light-quark 4-fermion ops, NOT just the 4-heavy ones.

## What "zeroing a coefficient" does (the mechanism, not the value)
A restrict-card coefficient set to `0.` makes the restriction algorithm strip the interactions whose
coupling is identically that coefficient → those operator vertices leave the surviving interaction set
(restriction-slice mechanism). So zeroing `cG`/`cpG` at NLO removes the chromo-bosonic operator
vertices from the NLO model; `no4q` additionally removes all four-heavy-quark vertices. The NP order
itself stays valid as long as *some* nonzero NP-carrying coefficient survives (it does in LO/NLO/no4q).

## The nonzero values are RANDOM PLACEHOLDERS, not physics (caution)
In LO/NLO/no4q the nonzero coefficients are pseudo-random 0.xxxxxx placeholders (e.g. cpDC differs
between the LO and NLO cards — meaningless physics, deliberately distinct so restriction does not
accidentally identify/merge two operators). Their PURPOSE is solely to be nonzero so the operator's
vertices survive restriction. The user MUST overwrite them in the generated `param_card.dat` with the
real Wilson coefficients. Do not read any physics off a restrict-card coefficient value — only its
zero/nonzero status is load-bearing (it decides operator presence).

**Authoring pattern verified (restrict_LO.dat, v3.7.1 + `$MADGRAPH_INSTALL/tests/input_files/SMEFTatNLO_running/restrict_LO.dat`):**
every nonzero DIM6* Wilson coeff carries a MUTUALLY-DISTINCT pseudo-random `0.0xxxxx` value
(distinct-count == nonzero-count), none equal to `1.0`; the scale `DIM6` code 1 (Lambda) is not
an operator. Off operators are EXACTLY `0.`. This is the model authors shipping the exact "correct"
pattern a user must follow: operators to VARY → distinct-nonzero-≠1 placeholders (defeats the RestrictModel
identical-value merge — GIVEN premise, restriction-slice); operators OFF → exactly `0.`. The `≠1` matters
independently of the merge: an external set to value 1 (or 0) is converted to a FIXED internal by
RestrictModel (GIVEN premise "zero/one-value externals → internals"), so a coeff shipped as `1.0` would be
locked out of the generated param_card — hence Lambda is shipped ≠1, and every operator 0.0xxx not 1. This
distinct-nonzero-≠1-placeholder pattern is literally how the bundled SMEFTatNLO cards are authored.

## Probe-verified (v3.7.1)
- `SMEFTatNLO-NLO; generate p p > t t~ NP<=2 [QCD]` → 11 born FKS processes generate as
  `g g > t t~ NP<=2 QCD<=100 QED<=99 NP^2=4 QCD^2=200 QED^2=198` (NP valid, squared auto-filled
  to NP^2=4 = 2× the NP<=2 amplitude bound; see eft-nlo-order-determination.md). Confirms the
  restrict_NLO card keeps NP-carrying vertices → NP order survives at NLO.
- bare `SMEFTatNLO` (default) → `NP not valid` (the trap); `SMEFTatNLO-LO` + `NP==2` generates
  diagrams (smeftatnlo-default-restriction-trap.md).

## Scale params — Λ and mueft; raw UFO default ≠ operative default
- **Λ**: `parameters.py:46` `Lambda`, `lhablock='DIM6'`, `lhacode=[1]` — so `Block DIM6` code 1 is the
  cutoff SCALE, NOT a Wilson coefficient. Read its default off parameters.py / the active restrict card
  (all 4 cards agree); do not cache the number.
- **mueft** (EFT renormalization scale, `Block Renor` lhacode 1): its raw UFO default is at
  `parameters.py:654`, but ALL FOUR restrict cards write a DIFFERENT `Renor` code-1 value. Since a
  restriction auto-applies at import (restrict_default when bare, or the chosen -LO/-NLO card), the
  **operative** default in the generated param_card = the value in the active card, NOT the parameters.py
  raw. Read BOTH off their coordinates — do not cache either number. General trap: **restrict cards
  override raw UFO parameter defaults — quote the operative (card) value, not the parameters.py value.**
- **No RG running in this UFO**: no `all_running_elements`/running module file in `SMEFTatNLO/` (grep empty).
  mueft is a fixed renormalization point (Renor block), not evolved. "No RG evolution" is source-visible as
  the absence of the running hook. (The separate SMEFTatNLO_running variant DOES ship running — not this one;
  see eft-rge-running-machinery.md.)

## Boundary
- WHICH operator basis/subset a user physically wants (e.g. 4-heavy-quark in or out, dipoles) is
  ma-physics-consultant's call. The restriction algorithm's zero-stripping itself is restriction-slice;
  this page records the observable card contents and the EFT consequence (which operators / the NP order
  survive). Param-card editing mechanics (overwriting the placeholders) are param-card slice.
