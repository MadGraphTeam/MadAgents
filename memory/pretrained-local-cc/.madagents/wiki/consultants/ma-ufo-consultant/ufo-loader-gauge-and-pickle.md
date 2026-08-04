---
description: Gauge selection effects (Goldstone/ghost dropping, propagator pick) and the pickle-cache path in import_full_model — which py3_*.pkl file is chosen and the cache-validity checks (mtime + version_tag, plus the prefix cache-hit-vs-reload decision).
---

# Gauge selection and pickle cache (import_ufo.py, v3.7.1)

Refs in `$MADGRAPH_INSTALL/models/import_ufo.py` unless noted.

## aloha.unitary_gauge
Module-level flag, default `True` at `$MADGRAPH_INSTALL/aloha/__init__.py:2` (`unitary_gauge = True`). `True == 1` in Python. Set by the `gauge` REPL option (the setting mechanism `set2_gauge` is interface/model-loader slice). The numeric values and their string source (`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:8079-8086`):
- `unitary` -> `True` (==1)
- `axial` (parton-shower gauge; massless only) -> `2`
- `FD` (**Feynman Diagram gauge**; refs 2203.10440 / 2405.01256) -> `3`
- `feynman` / anything else -> `False` (==0)

Naming (source-confirmed): gauge `3` = "FD" = **Feynman Diagram gauge**, NOT "Four-Dimensional". Five source sites name it Feynman Diagram gauge — `aloha/__init__.py:6` ("3: Feynman Diagram gauge (5D aloha)"), `madgraph_interface.py:851` and `:8062` ("FD is for Feynman Diagram gauge"), and four `# FD gauge` comments in `aloha/aloha_writers.py` (l.45,574,679,942). Only the one help line `madgraph_interface.py:8072` says "Four-Dimensional gauge" — treat that as the outlier. Physics (`madgraph_interface.py:8062`): FD is "the extension of the axial gauge to massive particles". Both `FD` and `axial` are tree-level only — `madgraph_interface.py:4879` raises if `LoopOption != 'tree'` and gauge in `['FD','axial']`.

Non-obvious (pickle path): gauge `3` (FD) is still DISTINCT from gauge `0` (Feynman) in the pickle-name code — FD gets `py3_model_FDG.pkl`, Feynman gets `py3_model_Feynman.pkl`. `axial`=2 groups with unitary ONLY for Goldstone dropping (`import_ufo.py:1245-1246` tests `aloha.unitary_gauge in [1,2]`); but the pickle-name code special-cases only `==1` (model.pkl) and `==3` (model_FDG.pkl), so `axial`=2 falls to the else branch -> `py3_model_Feynman.pkl`. So "FD" the gauge name contains "Feynman", but its pickle file is `_FDG`, not `_Feynman`.

## Pickle file naming (l.355-363)
```
unitary_gauge == 1  -> model.pkl
unitary_gauge == 3  -> model_FDG.pkl
else                -> model_Feynman.pkl
```
then `dec_` prepended if `decay=True`, then `py3_` prepended. So default (unitary) load uses `py3_model.pkl`; decay variant `py3_dec_model.pkl`; Feynman `py3_model_Feynman.pkl`; FDG `py3_model_FDG.pkl`. PROBE-CONFIRMED: with default `aloha.unitary_gauge=True` (int 1) the sm dir's `py3_model.pkl` is the one used. Do not assume the `_Feynman` suffix is the default — it is NOT.

## Cache-validity — two structural layers (mtime + version_tag), then a prefix cache-hit decision
1. **mtime check** `files.is_uptodate(pickle, files_list)` (`$MADGRAPH_INSTALL/madgraph/iolibs/files.py:105`): pickle must exist, its ctime must exceed every source file's mtime, AND exceed a hardcoded floor `min_time=1343682423` (~Jul 2012). `files_list` includes the model's required `.py` files PLUS `import_ufo.py` itself (l.353) — so editing the loader invalidates ALL model pickles.
2. **version_tag check** (l.375-377): the unpickled model's `version_tag` must `startswith(realpath(model_path))` and `endswith('##' + str(misc.get_pkg_info()))`. `get_pkg_info` (`$MADGRAPH_INSTALL/madgraph/various/misc.py:116`) returns the version dict from `VERSION`. A version bump or a moved model dir invalidates the cache.
3. **prefix check** (l.379-397): scans loaded parameter names. PRECISE mechanics: it iterates params, SKIPPING the case-insensitive set `['as','mu_r','zero','aewm1']` (l.382 — note this is FOUR names, NOT the 5-name prefix whitelist; `g` is missing here), and inspects the FIRST non-skipped param then `break`s — it does NOT scan all params. If `prefix` requested and that param `.startswith(prefix)` -> cache HIT (`_import_once.append(...); return model`, l.385-387); if it lacks the prefix -> logs "reload from .py file" (l.389). No-prefix branch is symmetric: a leading `mdl_` -> "reload", else cache hit (l.393-397).

If all pass, the pickled model is returned directly (l.387/397). On any mismatch it falls through to the full rebuild and re-saves the pickle (l.450-452), gated by `ReadWrite and model['allow_pickle']` (non-QCD-gluon-emission models set allow_pickle False).

## allow_reload / _import_once coupling (l.365-406) — the modified-on-disk guard
`allow_reload` is set True ONLY inside the `if files.is_uptodate(...)` block (l.366) — i.e. only when a CURRENT pickle exists. The cache-HIT paths (l.386/396) append `(model_path, unitary_gauge, prefix, decay)` to module-global `_import_once` (l.327) right before returning. The guard at l.404 — `if (key) in _import_once and not allow_reload: raise MadGraph5Error('This model %s is modified on disk. To reload it you need to quit/relaunch MG5_aMC')` — therefore fires ONLY when: this exact (path,gauge,prefix,decay) was successfully served from pickle earlier this session, BUT the pickle is no longer uptodate now (so `allow_reload` is False). Meaning: editing a model's `.py` mid-session AFTER it was already imported once (invalidating its mtime) is what triggers "modified on disk … quit/relaunch" — not a first-import-of-the-session edit. A fresh process never hits it.

Stale-pickle symptom: model loads with wrong parameter set/prefix after an edit but timestamps look new — check version_tag and the `_import_once` guard above.

## Goldstone / ghost dropping by gauge (add_particle, l.1240-1254)
- Ghosts (UFO `spin < 0`) dropped for tree (non-perturbation) models: `if not self.perturbation_couplings and particle_info.spin < 0: return` (l.1242). Loop models keep them with positive spin and `type='ghost'` (l.1281-1286).
- Goldstone bosons dropped when `(unitary_gauge in [1,2] and 0 in gauge) or (1 not in gauge)` (l.1245). Detected via `GoldstoneBoson`/`goldstoneboson`/`goldstone` attributes (l.1249-1254). Kept ones get `type='goldstone'` (l.1260-1264).
- PROBE: sm declares 43 particle objects (24 `Particle()` + 19 `.anti()`) but loads 17 in unitary gauge — the 3 Goldstones (G0,G+,G-) and 4 ghosts (+antis) are dropped.

## Propagator pick by gauge (l.1295-1303, 1320-1326)
If a particle's `propagator` attribute is a list/dict the test is `if aloha.unitary_gauge:` (l.1298) — TRUTHINESS, not `==1`. So unitary(1), axial(2) AND FD(3) all take `value[0]`; only Feynman(0/False) takes `value[1]`. Default (no propagator attr): spin>=3 massless gets propagator 0 (l.1324); spin==3 and `not aloha.unitary_gauge` (i.e. Feynman) gets propagator 0 (l.1325-1326).
