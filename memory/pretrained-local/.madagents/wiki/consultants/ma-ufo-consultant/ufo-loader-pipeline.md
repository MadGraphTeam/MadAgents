---
description: How import_ufo.py turns UFO files into a MadGraph Model — import_model/import_full_model entry points, the UFOMG5Converter and OrganizeModelExpression stages, and the online-DB fetch path.
---

# UFO loader pipeline (import_ufo.py, v3.7.1)

All line refs in `$MADGRAPH_INSTALL/models/import_ufo.py` unless noted.

## Entry points
- `import_model(model_name, decay=False, restrict=True, prefix='mdl_', ...)` (l.243) — the high-level wrapper. Resolves path+restriction via `get_path_restrict` (l.201), calls `import_full_model`, then wraps in `RestrictModel` and applies the restrict file if one was found (l.263-311). Complex-mass-scheme conversion happens here, BEFORE restriction (l.277-295). Restriction mechanics themselves are restriction slice.
  - **CMS trigger** (l.260): `useCMS = (complex_mass_scheme is None and aloha.complex_mass) or (complex_mass_scheme==True)` — i.e. CMS fires either from the global `aloha.complex_mass` flag (when the caller didn't override) or an explicit request. When CMS is on with a restrict file, the param_card is read a FIRST time with `complex_mass_scheme=False` (l.283) so `change_mass_to_complex_scheme` can tell which particles are massive/zero-width before the model is mutated. Caution (l.292-295): even when CMS is NOT requested the loader still calls `change_mass_to_complex_scheme(toCMS=False)` — because a model's own `CMSParam` default may already be CMS, and this resets it to the NWA renormalization condition. The `change_mass_to_complex_scheme` transform itself is a `Model` method (`madgraph/core/base_objects.py:1863`), model-object territory, not the UFO loader; only the trigger/ordering above is in this slice.
- `import_full_model(model_path, decay=False, prefix='')` (l.328) — the actual loader, no restriction. Validates the file set (l.338-352), tries the pickle cache (see `ufo-loader-gauge-and-pickle.md`), else: `ufomodels.load_model` (raw import) -> `UFOMG5Converter().load_model()` -> `OrganizeModelExpression(...).main()` -> sets parameters/couplings/functions on the Model, applies prefix, stamps version_tag, saves pickle. Exact post-convert sequence (l.415-452): `OrganizeModelExpression(ufo_model).main(additional_couplings = ufo2mg5_converter.wavefunction_CT_couplings if perturbation_couplings else [])` (the loop-model CT-coupling thread feeds in HERE); `model.set('parameters'/'couplings'/'functions', ...)`; decay attachment (see structure page); then if `prefix` truthy, `model.change_parameter_name_with_prefix()` (l.442) — this is WHERE the `mdl_` prefix is stamped onto parameter names (a `Model` method), which the pickle-cache prefix check later compares against. Finally `version_tag` is set and the pickle saved iff `ReadWrite and model['allow_pickle']`.

## get_path_restrict (l.201)
A `model-restrict` string like `sm-no_b_mass` is split on `-`; the suffix names `restrict_<suffix>.dat`. `-full` suppresses restriction (l.223). With no suffix and `restrict=True`, `restrict_default.dat` is auto-applied if present (l.228). `restrict` may also be a string path to a custom restrict file (l.233).

## Raw import (`$MADGRAPH_INSTALL/models/__init__.py:30` load_model)
`__import__` of the model package under a temporary `sys.path`; on ANY import failure it raises `UFOError` (l.100-101). This is where a Python-2 UFO (old `print`, `iteritems`, `raise X,"msg"`) fails — caught downstream by the interface to trigger auto-conversion (see `ufo-py2to3-conversion.md`). Stale `sys.modules` entries for prior models are purged first (l.89-95) to avoid cross-model contamination.

## Stage 1 — UFOMG5Converter (l.461)
`load_model` (l.530) validates: single-word lhablocks, no duplicate parameter names, CTparameter name clashes (l.534-556). Decides `case_sensitive` by comparing name sets with/without `.lower()` (l.563-567). Then:
- `detect_incoming_fermion` then `add_particle` per UFO particle (l.571-574). add_particle drops ghosts (tree models) and Goldstones (unitary gauge) — see gauge page. `assert(10 == nb_property)` (l.1328) enforces the 10 required particle fields are present.
- color-rep detection, sets `lorentz` list (l.582-585).
- `add_interaction` per vertex (l.605-606); CT vertices added for loop models (l.620-627).
- prunes interactions whose couplings emptied out (l.630-633).
- Colored-scalar models flag `fix_scale` limitation (l.576-579); non-QCD gluon emission disables pickling and flags MLM limitation (l.612-618).

## Stage 2 — OrganizeModelExpression (l.2040)
Separates parameters/couplings into event-dependent vs compute-once. `track_dependant = ['aS','aEWM1','MU_R']` (l.2043); anything depending on these (transitively) is recomputed per phase-space point. If `aEWM1` is not external, `Gf` is added to the tracked set (l.2139-2143); `loop`-block externals and running elements also tracked. For loop models, `get_additional_CTparameters` (l.2115) splits each `CTParameter` into per-pole internal parameters named `<name>_<pole>_` (e.g. `_FIN_`, `_1EPS_`, `_2EPS_`); `treat_couplings`/`revert_CTCoupling_modifications` temporarily expand CT couplings to pole dicts during conversion.

## Online model DB (l.104-199)
`get_model_db()` fetches `models_db.dat` from hardcoded UCL (`madgraph.phys.ucl.ac.be`) with INFN mirror (`madgraph.mi.infn.it`), tried in random order; `MG5aMC_WWW` env var prepends a third source (l.114). `import_model_from_db` matches the name, downloads the tarball to `models/` (or a user UFOMODEL dir for specific usernames, l.165-171), untars in place. Detailed fetch mechanics are installation slice.
