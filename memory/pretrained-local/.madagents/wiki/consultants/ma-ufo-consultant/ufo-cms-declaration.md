---
description: What a UFO model declares vs. what the loader does for the complex-mass scheme (CMS) — no CMS-specific model/restriction needed at LO; CMS reads the generic mass/width Parameter declarations; optional CMSParam gate lives only in loop UFOs that declare it (shipped sm/loop_sm do NOT).
---

# UFO declaration side of the complex-mass scheme (CMS)

Scope: what the UFO FILES declare that CMS consumes; the transformation `change_mass_to_complex_scheme` itself lives in `madgraph/core/base_objects.py` (Model-object method, orchestrated from `import_ufo.py` — model-loader slice owns the runtime flag + orchestration). This page is the model-declaration half.

## No CMS-specific model, restriction, or particle attribute is required at LO
- CMS is NOT gated by a dedicated model variant, `sm-full`, or a `-cms` restriction. `ls models/sm|models/loop_sm` -> NO `restrict_*cms*` file; no `complexmass`/`sm-cms` model on disk.
- The transformation runs on the GENERIC mass/width declarations every UFO already carries. It is switched on by the runtime flag `aloha.complex_mass` (default `False`, `aloha/__init__.py:1`) or `complex_mass_scheme==True` — set via `set complex_mass_scheme True` (model-loader slice), NOT by anything in the UFO.
- Loader path: `import_ufo.py:259-295` computes `useCMS`, then calls `model.change_mass_to_complex_scheme(toCMS=True/False)` BEFORE restriction (`:290`). Even when CMS is OFF it calls `toCMS=False` (`:295`) to force any CMSParam to 0.0.

## What CMS reads from the UFO (the promotable declaration)
`base_objects.py:1898-1963`, per particle:
- Reads `particle.get('mass')` and `particle.get('width')` — the Particle's mass/width attributes, which are Param NAME refs (e.g. sm W `particles.py:38`: `mass = Param.MW`, `width = Param.WW`). See [[ufo-width-declaration]] / [[ufo-declaration-object-grammar]].
- SKIP condition: width value==0 OR width name.lower()=='zero' (`:1907-1910`) -> particle stays real (e.g. Param.ZERO width). So a stable/zero-width particle is never complexified.
- PROMOTE condition: nonzero width OR mass name!='zero' (`:1914`). For an EXTERNAL mass (`ParamCardVariable`, i.e. nature=='external', LHA MASS block — see [[ufo-param-to-paramcard-chain]]) it synthesizes internal `ModelVariable` `CMASS_<massname> = cmath.sqrt(M**2 - i*M*Γ)` (`:1940-1943`); width gets `re(...)` prefix (`:1912`), Yukawas re-pointed to the (complex) mass (`:1966-1989`).
- So the ONLY declaration a UFO needs for a particle to be CMS-promotable: mass as an external Parameter (MASS block) + a nonzero-width external Parameter (DECAY block). Nothing CMS-specific. Internal-mass particles are handled too but the W (pdg 24) with a `ModelVariable` mass triggers `change_electroweak_mode({mz,mw,alpha})` (`:1917-1927`) because default sm MW is internal (alpha-Gmu scheme, see [[ufo-sm-ew-input-scheme]]) — CMS wants MW external.

## The CMSParam gate — optional, model-declared, ABSENT from shipped sm/loop_sm
- `base_objects.py:1881-1896`: loader looks up Parameter `CMSParam` (or `mdl_CMSParam`); if found, flips its `.expr` to `'1.0'` (CMS on) / `'0.0'` (off). If absent -> `CMSParam=None`, transformation still runs on generic mass/width.
- Purpose (`:1866`): CMSParam multiplies the `real(...)` prefix on UVCT wavefunction-renormalization expressions in a loop UFO, so CMSParam=1 removes the `real` prefix (correct CMS renorm) vs =0 (NWA renorm).
- `grep -rn CMSParam models/` -> ONLY `import_ufo.py` (source), NO model .py declares it. Shipped `sm`, `loop_sm`, `MSSM_SLHA2`, `hgg_plugin`, `taudecay_UFO` do NOT declare CMSParam. The comment at `:1866` names the `loop_qcd_qed` model, which is ONLINE (not on disk here) — its CMSParam declaration is UNVERIFIED here (gap).

## NLO loop UFO CMS declarations
- `loop_sm` CT files carry NOTHING CMS-specific: `CT_parameters.py`/`CT_couplings.py` have NO `CMSParam` and 0 `real(` prefixes (it is a QCD-only NLO model — only G-coupling UV/R2 counterterms, e.g. `CT_parameters.py:52-112` reglog/cond terms). See [[ufo-ct-file-object-grammar]] for the general CT grammar.
- The CMS-aware CT declaration pattern (UVCT expressions wrapped in `CMSParam*real(...)`) exists only in loop models that opt in — verified for none shipped on this install; `loop_qcd_qed_sm` (online) is the canonical example but UNVERIFIED here.
- MadLoop's RUNTIME consumption of CMS counterterms = madloop slice (redirect).

## Routing
"Does model X support CMS / need a cms model" -> LO: no special model, reads generic mass/width, gated by `set complex_mass_scheme`. "Which loop model carries CMS counterterms" -> loop_sm does NOT; loop_qcd_qed (online) does but unverified here. Runtime flag/orchestration -> model-loader. MadLoop consumption -> madloop.
