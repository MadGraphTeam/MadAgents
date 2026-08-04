---
description: do_import model dispatch in madgraph_interface.py v3.7.1 — check_import pre-branch gate (flag normalization, --last, find_import_type format guess), find_ufo_path path-resolution order + online-fetch gate, get_path_restrict restrict-as-string form, V4 deprecation, prefix selection, UFO load with CMS wrapper (3-arm keep_external SLHA2, double param_card read), post-load gauge check, process_model; import_ufo_model convenience method + non-model do_import tails boundary.
---

# `do_import` model-loading flow (v3.7.1)

`do_import(self, line, force=False, options={})` at
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:5753`.
Entered for any `import <X>`; `args[0].startswith('model')` is the model branch (`:5759`).

## Pre-branch gate: `check_import` (runs before the model branch)
`do_import` calls `self.check_import(args)` at `:5758` BEFORE inspecting `args[0]`.
Operative def is `CheckValidForCmd.check_import` at `:1256` (the `:2003` copy is the
Web-restricted override). It normalizes flags and resolves the format:
- **Flag normalization** (`:1259-1270`, `:1317-1321`): strips `-modelname`, `--modelname`
  (double-dash alias), and `--noprefix` from `args`, sets local bools, then **re-appends a
  canonical single-dash form** at the end (`--noprefix` if not prefix; `-modelname` if
  modelname). This is why do_import only ever tests `'--noprefix' in args` / `'-modelname'
  not in args` (single forms) — `--modelname` is folded to `-modelname` here.
- **`--last`** (`:1272-1291`): for `model --last`, finds the newest (`os.path.getmtime`) dir
  containing `*/particles.py` under `MG5DIR/models` + each `PYTHONPATH` entry, skipping
  `__REAL`/`__COMPLEX` restriction dirs; inserts it as `args[1]`.
- **Format guessing** (`:1300-1315`): if only one arg and it isn't a known format, calls
  `find_import_type(path)` (`:1429`) and inserts the guessed format at `args[0]`, logging
  "The import format was not given, so we guess it as %s". `_import_formats =
  ['model_v4','model','proc_v4','command','banner']` (`:3001`).
- `find_import_type` (`:1429-1460`): dir with `particles.py` → `'model'`; dir with
  `particles.dat` → `'model_v4'`; for a `-`-bearing name also tries the pre-`-` base dir;
  a file is read and regex-matched (`Begin process|<MGVERSION>`): 0 matches → `'command'`,
  >1 → `'banner'`, single "begin process" → `'proc_v4'`, single `<MGVERSION>` → `'banner'`;
  non-file fallback → `'proc_v4'`.

## Order of operations inside the model branch
1. `self._model_v4_path = None`; `self.clean_process()` (reset amps/MEs) — `:5760-5762`.
2. **V4 branch** if `args[0].endswith('_v4')` (`:5764`):
   - `logger.critical(...)` "Support for V4 model is deprecated and known to not be fully working" (`:5765`).
   - If `not force`: `ans = self.ask("Do you want to continue anyway?", "stop", ["continue","stop"], timeout=20)`; default answer is `"stop"` → 20-second prompt that aborts (returns) unless user types `continue` (`:5766-5769`).
   - On continue: `self._curr_model, self._model_v4_path = import_v4.import_model(args[1], self._mgme_dir)` (`:5770-5771`). [import_v4 internals are V4 territory, not this slice's source.]
3. **UFO branch** (else, `:5772`):
   - `loop_qcd_qed_sm*` Feynman force — see `gauge-selection-and-loopmodel-autoswitch.md`.
   - **Prefix selection** (`:5781-5785`): `prefix = not '--noprefix' in args`. If prefix → `aloha.aloha_prefix='mdl_'`; else `aloha.aloha_prefix=''`. `aloha.aloha_prefix` is module-level (affects all later ALOHA gen).
   - `self._curr_model = import_ufo.import_model(args[1], prefix=prefix, complex_mass_scheme=self.options['complex_mass_scheme'], options=options)` (`:5788-5790`). Note CMS is read from the persistent `self.options`, NOT a per-import flag.
   - `except ufomodels.UFOError` → auto-convert recovery, see `ufoerror-autoconvert-recovery.md` (`:5791-5806`).
   - History rewrite when path-style import: if `os.path.sep in args[1]` and last history line has "import", rewrite to `'import model %s' % self._curr_model.get('modelpath+restriction')` (`:5807-5808`).
   - **Post-load gauge check** (`:5810-5837`) — see gauge page.
4. After both branches: `self._curr_model._curr_gauge = self.options['gauge']` if model loaded (`:5838-5839`).
5. If `'-modelname' not in args`: `self._curr_model.pass_particles_name_in_mg_default()` (`:5841-5842`) — renames particles to MG convention from `particles_name_default.txt`; see process-model page.
6. `self.process_model()` (`:5845`) — multiparticle/autocomplete setup.
7. Reset `_curr_amps`, `_curr_proc_defs`, `_curr_matrix_elements`, `process_checks.store_aloha=[]` (`:5846-5851`).

## Path resolution: `find_ufo_path` (`models/import_ufo.py:69`)
Called by `get_path_restrict`→`find_ufo_path(model_name, web_search=True)`. Resolution ORDER (first match wins):
1. `./` or `../` prefix AND is a dir → return as-is (`:75-76`).
2. `MG5DIR/models/<name>` is a dir → that (`:77-78`).
3. each `PYTHONPATH` entry: `MG5DIR/<p>/<name>` is a dir → that, info-logging "model loaded from PYTHONPATH" on first hit (`:79-85`).
4. bare dir match `os.path.isdir(model_name)` → warns "Did you mean 'import model ./%s'"; raises only if name has a path sep (`:86-90`).
5. **online fallback** (`:91-96`): only if `web_search and '-' not in model_name` → `import_model_from_db(model_name)`; on success re-resolves with `web_search=False`. [online DB mechanics are installation slice; the RESOLUTION ORDER + the "no `-` in name" gate are the load-orchestration boundary.]
- A `-`-bearing name NEVER triggers online fetch (the `-` is reserved for `name-restriction` splitting); failed local resolution of `name-restriction` re-tries with the restriction stripped (`get_path_restrict:209-216`).
- **`SMEFTatNLO-NLO` worked example** (`get_path_restrict:201-241`): `find_ufo_path('SMEFTatNLO-NLO')` first tries a dir named EXACTLY that (none) and, because `'-' in name`, skips the online gate (`:91`, `web_search and '-' not in model_name` is False) → falls to the `else:` (`:97`) → `raise UFOImportError` (`:98`). The except handler (`:205`) splits on `-`: `model_name='SMEFTatNLO'` (re-resolved to the dir, `:211-213`), `restrict_name='NLO'` → `restrict_file=<dir>/restrict_NLO.dat` (`:218-220`). `find_ufo_path` does NOT special-case the `-` itself; the `name-restriction` split is entirely `get_path_restrict`'s except branch. Suffix `-LO`/`-NLO`/`-NLO_no4q`/`-default` each map to `restrict_<suffix>.dat`; `-full` → `restrict_file=None` (bypass).
- **Bare `SMEFTatNLO` (no suffix)** takes the `else` branch (`:225-231`): with `restrict=True` and `restrict_default.dat` present, it AUTO-SELECTS `restrict_default.dat` (`:228-229`). So `import model SMEFTatNLO` is NOT the unrestricted model — it silently applies the default card. SMEFTatNLO ships `restrict_default/LO/NLO/NLO_no4q.dat`. `dim6top_LO_UFO` ships NO restrict card → bare import is unrestricted (`restrict_file=None`), and any `dim6top_LO_UFO-<x>` suffix would fail at `restrict_<x>.dat` resolution.
- **Restrict-card auto-pick gap (the MECHANISM, not a model list)** (`:225-231`): the else-branch auto-pick at `:228` is gated SPECIFICALLY on `os.path.exists(.../restrict_default.dat)` (`:228`, `restrict_file` set `:229`, else `None` `:231`) — NOT on "any restrict card present." So **"model ships a restrict card" does NOT imply "bare import is restricted"** — only a card literally named `restrict_default.dat` is auto-applied; any other-named card needs the explicit `-<suffix>` (the `-`-split branch, e.g. `2HDM5F_NLO-noL` → `restrict_noL.dat`). WHICH installed models hit this gap is volatile (depends on which `restrict_*.dat` each ships) — derive it, don't memorize: `for d in "$MADGRAPH_INSTALL"/models/*/; do ls "$d"/restrict_*.dat 2>/dev/null | grep -q restrict_default || echo "$(basename "$d"): no restrict_default → bare import UNRESTRICTED"; done`. As of last scan (sanity-check, re-run for the input): `2HDM5F_NLO` ships only `restrict_noL.dat`, `2HDMtypeII` only `restrict_nobmass.dat`, `2HDMtII_NLO`/`dim6top_LO_UFO` no card → all four load bare-UNRESTRICTED (probe: plain `LoopModel`/`Model`, NOT `RestrictModel`); `SMEFTatNLO` ships `restrict_default.dat` → bare is auto-restricted. (The LoopModel-vs-Model class of each is a gauge-page fact — see `gauge-selection-and-loopmodel-autoswitch.md`; here the point is purely the restrict auto-pick.)
- `mssm` special: `find_ufo_path`/`get_path_restrict` failure for `model_name=='mssm'` logs "mssm model has been replaced by MSSM_SLHA2 model" guidance before re-raising `UFOImportError` (`get_path_restrict:208`, `:215`).

## import_ufo.import_model signature
`$MADGRAPH_INSTALL/models/import_ufo.py:243`:
`import_model(model_name, decay=False, restrict=True, prefix='mdl_', complex_mass_scheme=None, options={})`.
- `get_path_restrict(model_name, restrict)` (`:248`, def at `:201`) splits `name-restriction` on the LAST `-`; `restrict_name='full'` → bypass restriction (`restrict_file=None`, `:222-223`). For a bare path with a `restrict_default.dat` present and `restrict=True`, that default is auto-selected (`:228-229`).
- **`restrict` may be a STRING**, not just a bool (`:232-238`): when the resolved name had no `-restriction` and `isinstance(restrict, str)`, the string is treated as a path to a specific restrict card — tried first relative to the model dir (`model_path/<restrict>`), then as an absolute path; neither existing → `raise Exception("%s is not a valid path for restrict file")`. (do_import always passes a bool, so this form is for programmatic callers.)
- `import_full_model(model_path, decay, prefix)` (`:251`, def at `:328`) does the actual UFO read + pickle cache [pickle details are ufo slice].
- README info-log if `README` present (`:253-254`).
- `restrict_name` restoration: if a restriction was split off, `model["name"] += '-' + restrict_name` (`:256-257`) so the loaded model carries the `name-restriction` tag.
- CMS decision: `useCMS = (complex_mass_scheme is None and aloha.complex_mass) or complex_mass_scheme==True` (`:260-261`). NB do_import passes `complex_mass_scheme=self.options['complex_mass_scheme']` (a bool, default False), so the `is None`→`aloha.complex_mass` fallback only fires for OTHER callers; from do_import, CMS is on iff `self.options['complex_mass_scheme']==True`.
- **CMS activation = `model.change_mass_to_complex_scheme(toCMS=...)`** — this is the in-slice activation boundary; the conversion interior is shared with restriction. Called on BOTH branches:
  - **restrict_file branch** (`:263-311`): wrap as `RestrictModel(model)` (`:273`). If `useCMS`, FIRST `set_parameters_and_couplings(param_card=restrict_file, complex_mass_scheme=False)` — a **double read**: the restrict card is read once with CMS off so `change_mass_to_complex_scheme` can classify which particles are massive / zero-width (`:277-284`), THEN `change_mass_to_complex_scheme(toCMS=True, bypass_check=allow_qed)` (`:290`). Else `change_mass_to_complex_scheme(toCMS=False)` to force `CMSParam=0` (NWA) even if the model defaulted to CMS (`:291-295`). Restriction (`restrict_model`) runs AFTER (`:309`). [restrict algorithm is restriction slice.]
  - **no-restrict-file branch** (`restrict=full`, `:312-322`): still runs `change_mass_to_complex_scheme(toCMS=True/False, bypass_check=allow_qed)` — so CMS applies even with no restriction.
  - `allow_qed = options.get('allow_qed_cms', False)` → `bypass_check` (skips the QED-CMS sanity check) (`:285-288`, `:313-316`).
- **`keep_external` SLHA2 detection** (`:297-309`) — THREE separate `if/elif` arms (gated INSIDE the `restrict_file` branch; a `-full` import never evaluates SLHA2 detection):
  1. `model_name=='mssm'` or basename `mssm` → True (`:298-299`).
  2. `else` `all(b in blocks for b in ['USQMIX','SL2','MSOFT','YE','NMIX','TU','MSE2','UPMNS'])` over `get_param_block()` → True (`:300-301`).
  3. `else` `model_name=='MSSM_SLHA2'` or basename `MSSM_SLHA2` → True (`:302-303`).
  Any → "Detect SLHA2 format. keeping restricted parameter in the param_card" (`:307`) and `keep_external=True` → restricted params stay in the param_card rather than baked in.
- `restrict_model(restrict_file, rm_parameter=not decay, keep_external=keep_external, complex_mass_scheme=complex_mass_scheme)` (`:309-310`) is passed the RAW `complex_mass_scheme` arg (from do_import: the bool out of `self.options`), NOT the derived `useCMS`. [restrict_model interior is restriction slice.]
- Default `prefix='mdl_'` in this signature, but `do_import` always passes an explicit bool.

## `import_ufo_model` convenience method (`:5948`)
`def import_ufo_model(self, model_name): self._curr_model = import_ufo.import_model(model_name)` — a thin programmatic helper that calls `import_model` with NO keyword args, so it takes the SIGNATURE defaults: `restrict=True, prefix='mdl_', complex_mass_scheme=None`. Because `complex_mass_scheme=None`, CMS here follows the `aloha.complex_mass` fallback (`useCMS = complex_mass_scheme is None and aloha.complex_mass`), UNLIKE `do_import` which forces the bool from `self.options`. It also does NOT run the post-load gauge check, `pass_particles_name`, or `process_model` — it's a bare model-object loader, not the full interface flow. (Grep shows it's largely unused by the interactive path.)

## Non-model `do_import` tails (orchestration boundary)
`do_import` also dispatches `command`/`banner`/`proc_v4` (`:5862-5901`), but these hand straight to OTHER slices:
- `command` → `import_command_file` (runs a card of MG5 commands).
- `banner` → `detect_card_type` check, `Banner` parse, replays `mg5proccard` lines via `exec_cmd`, then `output . -f` + `launch` unless `--no_launch`. [output/launch are their own slices.]
- `proc_v4` → `import_mg4_proc_card` (V4 proc-card conversion; V4 territory).
These are NOT model loading — only the `args[0].startswith('model')` branch is this slice's core.

## Defaults (interface options, `:3088-3110`)
- `auto_convert_model: True` (`:3096`)
- `complex_mass_scheme: False` (`:3105`)
- `gauge: 'unitary'` (`:3107`)
- `acknowledged_v3.1_syntax: True` (`:3097`)
