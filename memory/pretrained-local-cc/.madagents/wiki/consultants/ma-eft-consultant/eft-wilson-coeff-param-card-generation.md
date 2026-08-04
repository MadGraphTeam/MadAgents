---
description: How EFT-UFO Wilson-coeff external params (parameters.py lhablock+lhacode+default) become param_card blocks; the no-restrict vs restrict-default default-card divergence; lowercased-block + per-model-lhacode-map cautions.
---

# Wilson coefficient → param_card block (the generation path) (v3.7.1)

The param_card-generation side of EFT setup: how the external Wilson-coeff params declared in an
EFT UFO's `parameters.py` turn into the `Block ...` entries a user edits in the generated
`param_card.dat`, and the per-model default-value divergence. Companion pages:
eft-model-content-wilson-coupling-vertex.md (coeff→coupling→order→vertex), smeftatnlo-restrict-card-taxonomy.md
(which restrict card zeroes which coeff), bundled-eft-models.md (which models ship).

## The generation path (source-walked)
1. Each Wilson coefficient is an `external` `real` `Parameter` in the model's `parameters.py`, tagged
   with `lhablock = '<BLOCK>'` and `lhacode = [n]` (SMEFTatNLO/parameters.py uses spaced form
   `lhablock = 'DIM6'` — grep with spaces, not `lhablock='DIM6'`, or you get 0 hits).
2. `models/<m>/write_param_card.py` `ParamCardWriter.write_card` (lines 63-87): collects
   `all_lhablock = set(param.lhablock for param in all_ext_param)`, sorts alphabetically (with MASS/DECAY
   pulled to front), then `write_block` + `write_param` each external param into its block. So **every
   external Wilson-coeff param appears in the generated card under its `lhablock`, with its `value` as the
   default** — the param_card block structure is a direct image of `parameters.py` external params.
3. Restriction selection happens before this: `madgraph_interface.py:find_restrict_card` (~:2912)
   defaults `no_restrict=True` but auto-picks `restrict_default.dat` when one exists in the model dir
   (`:2936`). A model with NO restrict_*.dat (dim6top) writes the raw `parameters.py` defaults; a model
   WITH restrict_default (SMEFTatNLO) writes the restrict-overridden values.

## The default-card divergence (the non-obvious part — per-model)
The "EFT contribution in the default generated card" differs by model and is NOT uniform even within
a model:

- **dim6top_LO_UFO (no restrict card)** — `parameters.py` defaults **ALL** Wilson coeffs to `value = 0.`,
  with the cutoff `Lambda` at `lhablock='DIM6' lhacode=1` (read its default off parameters.py). Two Wilson
  blocks (`DIM6` + `FCNC`) hold the coeff lines minus the 1 Lambda line; the bare import also writes the
  non-Wilson externals (DECAY + MASS + SMINPUTS + YUKAWA). Count these fresh off parameters.py if a total
  is needed — do not cache it. **Probe-verified** (`generate g g > t t~ DIM6=1; output`): generated
  `param_card.dat` has `Block dim6` with a nonzero `# Lambda` line and every coeff `0.000000e+00`. →
  default card is SM at the param level; user MUST set coefficients by hand. (No restrict card means no
  zeroing trap, but also no "turn everything on" — it ships off.)
- **SMEFTatNLO (restrict_default auto-selected)** — `parameters.py` raw defaults are **non-uniform by block**:
  DIM6 (bosonic) and DIM62F (2-fermion) default to a nonzero placeholder; the three 4-fermion blocks
  DIM64F / DIM64F2L / DIM64F4L default to an effectively-zero tiny placeholder (read the literals off
  parameters.py). BUT bare-import applies `restrict_default.dat`, which zeroes EVERY coeff → NP order
  REJECTED (smeftatnlo-default-restriction-trap.md). Use `-LO`/`-NLO` to get the nonzero (random-placeholder)
  coeffs. So for SMEFTatNLO the parameters.py defaults are almost never what lands in the card — the
  restrict card overrides them.

## Block → lhacode → default value maps (source-walked, parameters.py)
These are the model's OWN parameters.py defaults (pre-restriction). lhacode gaps = operators not in
this model's basis.

**SMEFTatNLO** (5 Wilson-coeff blocks + Lambda; read entry counts + defaults off **parameters.py**).
NOTE the parameters.py entry counts are NOT identical to the restrict-card counts in
smeftatnlo-restrict-card-taxonomy.md: restriction drops one DIM62F entry (so DIM62F has one fewer line
in restrict_NLO.dat than in parameters.py); the other four blocks match. Coeff catalogs (names, not
counts/defaults — those read fresh):
- `DIM6`: lhacode 1 = **Lambda** (the cutoff, NOT an operator); 2+ = bosonic coeffs
  cpDC,cpWB,cdp,cp,cWWW,cG,cpG,cpW,cpBB (default to a nonzero placeholder). *Caution:* lhacode 1 is the
  scale, not an operator.
- `DIM62F`: cpl1-3,c3pl1-3,cpe/cpmu/cpta,cpqMi,cpq3i,cpQ3,cpQM,cpu,cpt,cpd,cbp,ctp,ctZ,ctW,ctG
  (nonzero placeholder). lhacode gaps exist — read the exact map off parameters.py.
- `DIM64F`: 4-fermion all-quark cQq83…cQt8 (effectively-zero placeholder). (NOT "4-heavy-quark" — cQq83
  etc. are light-quark-coupling; see smeftatnlo-restrict-card-taxonomy.md.)
- `DIM64F2L`: cQlM1-3,cQl31-33,cQe1-3,ctl1-3,cte1-3,ctlS3,ctlT3,cblS3 (effectively-zero placeholder).
- `DIM64F4L`: cll1111…cll2332 (effectively-zero placeholder).
- Plus DECAY block (parameters.py ships WT/WZ/WW/WH defaults) — these are overridden by the restrict
  cards (restrict-card page); read the operative values off the active card.

**dim6top_LO_UFO** (2 Wilson-coeff blocks + Lambda):
- `DIM6`: lhacode 1 = **Lambda**; 2+ = flavour-conserving coeffs ctp,ctpI,cpQM,cpQ3,cpt,… (all `0.`).
  NOTE the dim6top DIM6 block is MUCH larger than SMEFTatNLO's and the lhacode→name map is ENTIRELY
  different: **same block `DIM6`, same lhacode 2 → dim6top `ctp` vs SMEFTatNLO `cpDC`** (different
  operators). SMEFTatNLO's DIM6 block is short (no lhacode 18); the SMEFTatNLO coeff `cbp` lives at
  lhacode 18 of **DIM62F**, a different block — do not compare it to dim6top's DIM6 lhacode 18 `cQlM1`.
- `FCNC`: flavour-changing, flavour-indexed coeffs ctpx13,ctpx23,… (all `0.`) — the larger set
  (dim6top-fcnc-second-eft-order.md).

## Cautions (source/probe-visible hazards)
- **Block name is lowercased in the card.** parameters.py `lhablock = 'DIM6'` → generated card writes
  `Block dim6`. The Python attr case and the card case differ (probe-confirmed `Block dim6`). Don't grep
  the generated card with uppercase block names.
- **Same block NAME, different lhacode→operator map across models.** Both dim6top and SMEFTatNLO have a
  `DIM6` block but the lhacodes mean different operators (lhacode 2 = `ctp` in dim6top vs `cpDC` in
  SMEFTatNLO; the blocks are also different SIZES — dim6top's DIM6 is much larger than SMEFTatNLO's,
  read each off parameters.py). A lhacode is
  only interpretable against THAT model's parameters.py — never carry a lhacode→coeff identification from
  one EFT model to another, and a lhacode present in one model's block may not exist in another's.
- **dim6top default card is all-zero (SM)** — no restrict trap, but the user gets nothing turned on;
  must set coeffs. SMEFTatNLO bare-default is all-zero via restrict (the trap) — same end-state, different
  cause (one has no restrict, one has an all-zeroing restrict).
- **Default coeff values are not physics.** dim6top ships `0.` (off); SMEFTatNLO's parameters.py
  placeholders and the random `0.xxxxxx` placeholders in restrict_LO/NLO are all non-physical — the user
  overwrites them with real Wilson coefficients in the generated param_card.

## Boundary
- Param_card EDITING mechanics (hand-editing values, param-card layer precedence) are param-card slice;
  this page records only how the EFT-coeff blocks come to EXIST in the card and their shipped defaults.
- WHICH operator each lhacode physically is (gauge structure, the SM amplitude it corrects) is
  ufo-slice / ma-physics. The restriction zero-stripping algorithm is restriction-slice.
- heft / EWdim6 are online-only (not under models/; _online_model dict madgraph_interface.py:2894-2912)
  — cannot read their parameters.py locally; mark as gap rather than asserting their card contents.
