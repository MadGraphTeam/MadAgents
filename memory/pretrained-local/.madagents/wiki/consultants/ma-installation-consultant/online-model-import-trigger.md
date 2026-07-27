---
description: import model <name> auto-downloads a non-local model from the online model-DB — find_ufo_path web-search gate, hyphen/restriction retry, get_model_db endpoint URLs (models_db.dat @ UCL/INFN — an MG-maintained INDEX, not "any FeynRules-wiki model"), curated _online_model list (incl loop_qcd_qed_sm_Gmu; EWdim6/heft IN, SMEFTsim/SMEFTatNLO/dim6top NOT), NO install-command route for models, host-agnostic tarball fetch, manual drop-in into models/ (dir-existence recognition, models/__init__.py is package code NOT a manifest), display modellist FeynRules-vs-MG5 labelling (v3.7.1).
---

# `import model <name>` → online model-DB download trigger

Scope: how `import model <name>` decides a model is MISSING locally and fires the online fetch (relevant for obtaining non-bundled SMEFT models: SMEFTsim, EWdim6, heft, TopEffTh). The fetch BODY (`get_model_db`/`import_model_from_db`) is summarized in `source-server-selection.md` and is ufo-slice territory; this page is the TRIGGER + static recognition, which is install-slice.

## Resolution chain (a missing-model import)
`do_import` → `import_ufo.import_model(args[1], ...)` → `get_path_restrict` (`:248`) → `find_ufo_path`.

### find_ufo_path `$MADGRAPH_INSTALL/models/import_ufo.py:69-101`
Tries in order: `./`-relative dir; `$MG5DIR/models/<name>` (`:77`); each `PYTHONPATH` dir (`:79-85`); literal `os.path.isdir(model_name)` (`:86`). If none found:
- **WEB-SEARCH GATE `:91`**: `elif web_search and '-' not in model_name:` → `found = import_model_from_db(model_name)` (`:92`). If `found` truthy, re-calls `find_ufo_path(name, web_search=False)` (`:94`) to resolve the now-downloaded dir; else raises `UFOImportError`.
- The two KEY conditions: (a) `web_search=True` (default; set False only on the post-download retry), and (b) **`'-' not in model_name`**. A name CONTAINING a hyphen does NOT web-search at this level — it raises immediately.

### get_path_restrict hyphen retry `:201-220`
`get_path_restrict` wraps `find_ufo_path`. On `UFOImportError`:
- if `'-' not in model_name`: re-raise (`:206-209`) — terminal miss.
- else (`:210+`): strip the trailing `-tag`, set `model_name='-'.join(split[:-1])`, retry `find_ufo_path` on the bare name (`:213`). The bare name has no hyphen now, so the `:91` gate CAN fire web search on this second attempt. The stripped tag becomes `restrict_name` → `restrict_%s.dat` (`:218-220`); `-full` bypasses the restrict file (`:223-224`).

NET: both `import model SMEFTsim_X` (bare) and `import model SMEFTsim_X-myrestrict` (hyphenated) can reach the online fetch — the bare name on the first `find_ufo_path` call, the hyphenated one on the post-strip retry. The fetch always runs on the BARE model name; the restriction tag is applied locally after download.

## The DB endpoint — `get_model_db()` `import_ufo.py:104-133`
The "model database" is a single file `models_db.dat` fetched from HARDCODED hosts (`:107-108`):
- `http://madgraph.phys.ucl.ac.be/models_db.dat` (UCL)
- `http://madgraph.mi.infn.it//models_db.dat` (INFN Milan mirror; note the double-slash is literal in source)

`r=random.randint(0,1); r=[r,1-r]` → random primary with the other as fallback (`:111-112`). If env `MG5aMC_WWW` non-empty, its `/models_db.dat` is appended and tried FIRST (`r.insert(0,2)`, `:114-116`). All hosts unreachable → `MadGraph5Error('Model not found locally and Impossible to connect any of us servers...')` (`:130-131`). NOTE: `--source=ucl/uiuc/<url>` does NOT steer this — that flag governs only `do_install`'s `package_info.dat`. Pin the model-DB mirror via `MG5aMC_WWW`. (Same two hosts as the install-server list; see `source-server-selection.md`.)

## import_model_from_db match + landing `:135-199`
(ufo-slice body; recorded here only for trigger-completeness.) `models_db.dat` lines are `name<ws>url`. Match is EXACT on `split[0]==model_name` (`:147`). No match → `logger.debug('no model with that name ... found online')` and returns False (→ caller raises UFOImportError). On match: emits `logger.info("download model from %s to the following directory: %s", link, target)` (`:174`, visible at default INFO) then `misc.wget(link,'tmp.tgz')` into `target` (`:175`), untar (`.tgz`/`.tar.gz`/`.tar`/`.zip` handled `:180-197`). **NO confirmation prompt / y-n ask anywhere** — the fetch is fully automatic once the name matches a `models_db.dat` line; the only user-facing signal is the INFO "download model from …" line. **Landing dir** `target` = `$MG5DIR/models` (`:174`) for the normal user (the `omattelaer`-username PYTHONPATH special-case `:165-171` never applies to other users). So a downloaded model lands at `$MADGRAPH_INSTALL/models/<name>/`, becoming locally present for subsequent imports. The tarball URL can point at ANY host (a feynrules-website URL or a madgraph-server URL) — the fetch is host-agnostic; classification is cosmetic (only `display modellist` labels the source, below).

## Curated static list `_online_model` `madgraph/interface/madgraph_interface.py:2894-2909`
A HARDCODED dict of "known online" models → advertised restriction tags, consulted BEFORE any network call. Full v3.7.1 keys: `2HDM`, `loop_qcd_qed_sm`(`:2895`, tags full/no_widths/with_b_mass/with_b_mass_no_widths), `loop_qcd_qed_sm_Gmu`(`:2896`, tags ckm/full/no_widths), `4Gen`, `DY_SM`, `EWdim6`(`:2899` full), `heft`(`:2900` ckm/full/no_b_mass/no_masses/no_tau_mass/zeromass_ckm), `nmssm`(full), `SMScalars`(full), `RS`, `sextet_diquarks`, `TopEffTh`, `triplet_diquarks`, `uutt_sch_4fermion`, `uutt_tch_scalar`.
- **`SMEFTsim`/`SMEFTatNLO`/`dim6top` are NOT in this dict** — discoverable only via the live `models_db.dat` at runtime.
- What this dict does NOT do: being listed here does NOT itself cause a download. It only (a) feeds `find_restrict_card` `:2924-2926` — when `not local_model` but `model_name in _online_model`, returns curated `<name>-<tag>` restriction suggestions WITHOUT touching disk/network (so tab-complete / restriction listing works offline-of-the-model); (b) seeds `display modellist`. The ACTUAL download requires the name to be present in the network-fetched `models_db.dat` (`import_model_from_db` match, above). The two lists overlap but are independent: `_online_model` is compiled-in metadata, `models_db.dat` is the live download index.

## loop_qcd_qed_sm_Gmu (NLO loop model) — auto-on-import, NOT bundled, NO install command
- NOT bundled: the release ships `models/loop_sm` (an LO+loop SM model) but NOT `loop_qcd_qed_sm` / `loop_qcd_qed_sm_Gmu` — which is what forces the online-import path. Whether a given name is present locally is install-STATE (a user or prior import may have placed it), so verify live rather than caching "absent": `ls -d $MADGRAPH_INSTALL/models/loop_qcd_qed_sm* 2>/dev/null`.
- `import model loop_qcd_qed_sm_Gmu` (no hyphen) → `find_ufo_path` local misses → web-search gate `:91` fires → `import_model_from_db('loop_qcd_qed_sm_Gmu')` → `get_model_db()` → exact match in `models_db.dat` → wget+untar into `$MG5DIR/models/`. So the fetch is AUTOMATIC on import; the curated `_online_model` entry `:2896` supplies its restriction tags (ckm/full/no_widths) for completion but is not the trigger.
- **There is NO `install <model>` command.** Models are NOT in `_install_opts`/`_advanced_install_opts` (those are downstream *tools*: pythia8/lhapdf/Delphes/…). `install_ad` is a citation map for tools, not models. The ONLY route to fetch a non-bundled model is `import model <name>` (auto web-search) — never `do_install`.

## `display modellist` `:3926-3954` (inside do_display)
Two sources merged: the curated `_online_model` (`:3926-3932`, comment "automatic download from MG5aMC server") then a LIVE `get_model_db()` call (`:3936`) listing everything else (`_online_model2`). The live block classifies each by URL: `'feynrules' in path` → "automatic download from FeynRules website" (`:3945`); `'madgraph.phys' in path` → "automatic download from MG5aMC server" (`:3947`); else "automatic download." `_v4` names are skipped (`:3942`). Restriction shown as `'unknown'` for live entries (`:3951`). So `display modellist` is the canonical way to see whether e.g. SMEFTsim currently resolves online and from which host (FeynRules vs MG5aMC server) — a RUNTIME/network answer.

## Manual install (drop-in into models/) + the `__init__.py` caution
- **Local recognition is directory-existence ONLY.** `find_ufo_path:77` recognizes a model iff `os.path.isdir(os.path.join(MG5DIR,'models',<name>))`. There is NO registry, manifest, or index file that must be edited — extracting a UFO tarball's model dir into `$MADGRAPH_INSTALL/models/<name>/` is the complete and correct manual-install path (the same landing dir the auto-fetcher writes to, `:174`). So "manually drop the UFO dir into models/" is CORRECT.
- **`models/__init__.py` is NOT a model registry.** It is the `models` Python *package* module (`$MADGRAPH_INSTALL/models/__init__.py`) — it defines `class UFOError`, `def load_model(...)`, etc. (the loader that reads a model's `particles.py`/`couplings.py`/… after `find_ufo_path` resolves the dir). It does NOT list or enumerate models; model discovery never reads it. Grep confirms nothing consults it for discovery; `find_ufo_path` uses `os.path.isdir` only.
- So the common caution "do not overwrite `models/__init__.py`" is PRUDENT but its usual REASON (that it's a discovery manifest listing models) is FOLKLORE. The real hazard: a badly-packaged UFO tarball whose top level contains an `__init__.py` could, if untarred at `models/` root instead of into a subdir, clobber the package's own `__init__.py` and break `load_model` for ALL models. A well-formed UFO tarball unpacks to `models/<name>/…` (its own subdir with the model's own `__init__.py`) and never touches `models/__init__.py`. Net: keep `models/__init__.py` intact because it is live package code, not because it is a model list.

## Cautions
- The web-search trigger is SILENT-ish: a missing local model first attempts a network fetch before failing. Offline, `get_model_db` raises `MadGraph5Error('Model not found locally and Impossible to connect any of us servers...')` (`import_ufo.py:130-131`) — distinct from the local "not a valid pathname" error. An exact-name typo that is also not online → `logger.debug` (not visible at default INFO level) + UFOImportError.
- `--source=ucl/uiuc/<url>` does NOT steer this fetch (governs only `do_install`'s `package_info.dat`). Pin the model-DB mirror via `MG5aMC_WWW` env. (See `source-server-selection.md`.)
- Match is exact and case-sensitive on the FIRST token of each `models_db.dat` line; whether a given SMEFT spelling (e.g. `SMEFTsim` vs `SMEFTsim_general_MwScheme_UFO`) resolves is a RUNTIME/network fact — only `display modellist` or the live fetch can settle it. Not statically decidable.
- A freshly-downloaded OLD SMEFT UFO (py2) raises `ufomodels.UFOError` on the import retry → auto_convert_model recovery fires (default True). See `convert-model.md` for the in-place, best-effort, no-backup converter and the `-f` flag logic.

## Gaps (runtime/network — not source-decidable)
- Whether any specific SMEFT name resolves online today and from which host (FeynRules vs MG5aMC) — `models_db.dat` is network-fetched.
- Whether a downloaded SMEFT UFO imports cleanly or needs conversion (model-version dependent).
