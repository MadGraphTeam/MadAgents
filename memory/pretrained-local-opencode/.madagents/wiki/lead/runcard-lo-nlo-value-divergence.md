---
description: About to quote or set a run_card default, cut name, or allowed value without having pinned the card class LO vs NLO.
---

# Run_card LO-vs-NLO value & name divergence — pin the class first

The LO and NLO run_cards are not one card with a few extra NLO rows — they are two classes (`banner.py` `RunCardLO` vs `RunCardNLO`) with independently-set defaults, partly-different parameter names, and different available knobs. A run_card fact (a default, a cut-variable name, an allowed-value set) is **class-scoped**: correct for one, wrong for the other. Any dispatch that quotes a run_card value must carry the card class as a premise; a value stated without a class is unverified.

## The divergence (illustrative, not exhaustive — verify per input against the class's source)

- **Cut defaults differ.** The LO cut defaults (kinematic-cuts, `../consultants/ma-kinematic-cuts-consultant/runcard-cut-params.md`) and the NLO cut defaults (amcatnlo, `../consultants/ma-amcatnlo-consultant/nlo-cut-block-and-ir-safety.md`) diverge value-for-value across the shared cut names (`ptj/ptl/pta/etaj/etal/etaa/ptgmin`) — read each class's default from its `banner.py` class (`RunCardLO` vs `RunCardNLO`) or the consultant page. Several NLO cut defaults are `-1`/`0` disable-sentinels where the LO name carries a real cut value, so a table quoting the NLO numbers as "the" defaults has silently quoted the wrong card. Route the LO cut set to kinematic-cuts, the NLO cut set to amcatnlo (the NLO cut block is *narrower* for IR-safety, not a feature gap).
- **Pair-mass cut NAMES differ.** LO uses `mmll` (same-flavour opposite-sign pair mass, `setcuts.f`); NLO uses `mll` (default is the `0.0` no-cut sentinel) plus `mll_sf` (same-flavour; read its default in `RunCardNLO`/`banner.py`). Quoting `mll` at LO or `mmll` at NLO is a name error, not a value error — the parameter does not exist in the other class.
- **Available knobs differ.** Several LO knobs have no NLO analogue and vice-versa; `update <block>` reveal is LO-only (see `card-set-update-dispatch-seam.md` trap 2). `use_syst`/systematics surfaces also differ by class.
- **`dynamical_scale_choice` allowed-list AND integer→formula mapping diverge — a per-value trap.** The scale-selector is class-scoped in three independent ways (both consultants cited their own `setscales.f`, LO Template vs NLO Template — a genuine LO/NLO seam, not a conflict):
  - *Allowed lists differ.* LO `allowed=[-1,0,1,2,3,4,10]` (`banner.py` RunCardLO ~4266); NLO `allowed=[-2,-1,0,1,2,3,10]` (RunCardNLO ~5680). `=4` (√ŝ, partonic COM) is **LO-only**; `=-2` (fixed-scale auto-flag, set automatically when both `fixed_ren_scale` and `fixed_fac_scale` are True) is **NLO-only**.
  - *`=10` means different things by class, and is NEVER "geometric mean of masses".* LO: `10` is in the allowed list but LO `setscales.f` has **no `=10` branch** → runtime `stop 'Unknown option'`. NLO: `=10` (and `=0`) route to the **user-defined scale hook** `user_dynamical_scale(PP)` (NLO `setscales.f`). The geometric-mean routine is a *separate* FxFx merging-scale clustering path, not the `dynamical_scale_choice=10` formula. Any answer telling a user "set 10 for geometric mean" is wrong on both classes.
  - *`=-1` diverges.* LO: CKKW back-clustering (default). NLO: falls back to HT/2 (= choice 3) — CKKW is not implemented in the NLO code. The shipped NLO run_card comment still reads "CKKW back clustering" (LO-inherited text); flag it as misleading when quoting the card comment.
  - *Route:* LO scale-formula/`setscales.f` questions → **ma-scales-pdf-consultant**; the NLO run_card scale surface (allowed list, `mur_over_ref`/`muf_over_ref`, `reweight_scale`) → **ma-amcatnlo-consultant**. Confirmed integer→formula mapping (both classes, for 1/2/3): `1`=Σ E_T, `2`=HT=Σ√(m²+pT²), `3`=HT/2. `scalefact` is **LO-only**; NLO uses `mur_over_ref`/`muf_over_ref` (both default 1.0).

## Dispatch rule

1. **Pin the card class before routing.** "NLO" anywhere in the spec → the run_card is `RunCardNLO`; a bare LO process → `RunCardLO`. If the class is ambiguous, resolve it first (it changes both the default and sometimes the name).
2. **Route by class to the class-owning slice.** LO run_card values → the LO owning slice (scales-pdf / kinematic-cuts / matching / launch / systematics). NLO run_card values → **ma-amcatnlo-consultant** (owns the NLO run_card block), with the specific physics slice for the value's meaning.
3. **A recalled defaults table is orientation, not evidence.** Because the two classes share parameter *stems* but not *values*, a memory of "the run_card default for X" is exactly the kind of claim that is confidently-wrong when the class flips. Read the class's own defaults from `banner.py` (or the rendered `run_card.dat` for THIS output) — do not adopt a defaults list that does not name its class. (`ma-truth-sources`: verify for THIS input; a defaults table is a config-content claim.)

See also: `fiducial-cuts-fanout.md` (the cut LO/NLO split + `cut_decays` silent exemption), `card-set-update-dispatch-seam.md` (the `update`-reveal LO-only consequence), `config-value-lifecycle-layers.md` (written-card ≠ enforced value).
