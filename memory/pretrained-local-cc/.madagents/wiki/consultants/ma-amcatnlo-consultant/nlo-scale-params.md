---
description: RunCardNLO scale parameters — mur_over_ref/muf_over_ref (NLO scalefact-analog, scalefact ABSENT at NLO), reweight_scale/rw_rscale/rw_fscale defaults, dynamical_scale_choice allowed list + sentinel resolution in setscales.f (-1→HT/2, -2→fixed, 10/0→USER-defined NOT geometric mean).
---

# `RunCardNLO` scale parameters

`$MADGRAPH_INSTALL/madgraph/various/banner.py`, `class RunCardNLO`, `default_setup` block lines 5667-5703. Formula resolution: `$MADGRAPH_INSTALL/Template/NLO/SubProcesses/setscales.f` (cross-slice — scales-pdf owns the Fortran; I own the run_card param surface + banner check_validity).

## Central-scale ratio knobs (scalefact analog)
- `mur_over_ref` (banner.py:5685); `muf_over_ref` (5686) — multipliers on the renormalization / factorization reference scale (`mu_R = mur_over_ref * mu_ref`, `mu_F = muf_over_ref * mu_ref`); read their defaults at those lines. Per-beam variants `muf1_over_ref`/`muf2_over_ref` (hidden, 5687-5688); the sentinel-default at those lines makes muf1/muf2 inherit `muf_over_ref` (inheritance at 5840-5844). `mue_over_ref` (Ellis-Sexton) is `system=True` — user cannot modify (5689).
- The reference scale itself: fixed case uses `mur_ref_fixed`/`muf_ref_fixed` (default read at 5674/5676, shortcuts mz/mw/mt/mh); dynamical case uses `scale_global_reference` computed in setscales.f.
- **`scalefact` is ABSENT at NLO.** It exists only in `RunCardLO` (banner.py:4283). Grep confirms no `scalefact` param in the RunCardNLO range (5594-6100). The NLO card splits the single LO `scalefact` into the independent `mur_over_ref`/`muf_over_ref` pair.

## Scale-variation reweight knobs
- `reweight_scale` (list), fortran_name `lscalevar` (5691, read default there) — whether scale-variation weights are computed. Forced to length-1 when both fixed scales set (5872).
- `rw_rscale` fortran_name `scalevarR` (5696); `rw_fscale` fortran_name `scalevarF` (5697) — the scale-variation multiplier lists (read their default entries at those lines). check_validity forces `1.0` to be present and first (5909-5920), rejects duplicates (5922-5925), caps list length (5904-5907).
- Backward-compat scalars `rw_rscale_down/up`, `rw_fscale_down/up` (hidden, 5692-5695, sentinel-default there); if set they rebuild the list as `[1.0, up, down]` (5852-5857).
- `reweight_pdf` (lpdfvar, 5698); `pdf_set_min`/`pdf_set_max` (hidden, read default IDs there). NLO scale/PDF uncertainty runs through this built-in reweight, NOT the `systematics` program (which defaults `'none'` at NLO — see [[runcardnlo-defaults-and-ickkw]]).

## `dynamical_scale_choice` — allowed list + sentinel resolution
`add_param("dynamical_scale_choice", [-1], allowed=[-2,-1,0,1,2,3,10], ...)` (banner.py:5679-5682, fortran_name `dyn_scale`, shortcuts ht/2→3, ht→2, et→1). It is a **list** (default `[-1]`); multiple entries → multi-scale reweight, capped at a max entry count (5900), no duplicates (5888).

Sentinel resolution in `scale_global_reference` (setscales.f:544-590), NLO side:
- **1** → sum of transverse energy eT (548).
- **2** → HT = sum of transverse masses mT (555).
- **3 AND -1** → **HT/2** (563: `.eq.3.or.dynamical_scale_choice.eq.-1`). So `-1` does NOT do CKKW back-clustering at NLO; it falls through to the HT/2 branch. The run_card comment (5682) still says "-1 is CKKW back clustering" (copied from LO) — the comment is misleading for the NLO code path.
- **-2** → **fixed scale** `tmp = muR_ref_fixed` (572-574). This is the auto-set sentinel: banner check_validity sets `dynamical_scale_choice=[-2]` whenever `fixed_ren_scale and fixed_fac_scale` are both True (5871-5873). Effectively internal, though it is in the allowed list.
- **10 AND 0** → **USER-DEFINED scale** `tmp = user_dynamical_scale(PP)` (576-583). NOT geometric mean. The "USER-DEFINED SCALE: ENTER YOUR CODE HERE" block explicitly says "to use this code you must set dynamical_scale_choice = 10". The geometric-mean code elsewhere in setscales.f (lines 230-342) belongs to the FxFx **merging-scale** clustering reference, a different routine — not to `scale_global_reference`.
- else → `write ... 'Unknown option' ; stop` (587-589).

## LO vs NLO allowed-list divergence (do not carry one across)
- LO `dynamical_scale_choice` (banner.py:4266): `allowed=[-1,0,1,2,3,4,10]`, default scalar `-1`, includes **4** (center-of-mass energy / sqrt(shat), shortcut `shat`), no `-2`.
- NLO (5680): `allowed=[-2,-1,0,1,2,3,10]`, default list `[-1]`, includes **-2** (fixed sentinel), drops **4**.
- So `4` (shat) is LO-only; `-2` is NLO-only. `10`/`0` (user-defined) and `-1`/`1`/`2`/`3` are common to both. `10` is NOT NLO-only.

## FxFx / jet-veto overrides
`ickkw==3` (FxFx) forces `dynamical_scale_choice=[-1]` + reweight_scale truncated (5807-5810); `ickkw==-1` (jet veto) forces `[-1]` → ptj scale via the `ickkw.eq.-1` branch (setscales.f:544-547, which pre-empts the dyn_scale switch entirely). See [[runcardnlo-defaults-and-ickkw]] / [[fxfx-ickkw3-lifecycle]].
