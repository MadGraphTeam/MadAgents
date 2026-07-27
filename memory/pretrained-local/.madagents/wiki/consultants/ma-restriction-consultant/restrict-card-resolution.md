---
description: How a "model-restriction" string resolves to a restrict_*.dat path (get_path_restrict in import_ufo.py + find_restrict_card listing in madgraph_interface.py), incl. -full bypass and implicit default (v3.7.1)
---

# Restrict-card resolution — string → path

Two functions, two jobs. `get_path_restrict` (import_ufo.py) RESOLVES one model-restriction string to a concrete path at load time. `find_restrict_card` (madgraph_interface.py) LISTS the available `model-tag` options (autocomplete / online enumeration), it does not resolve.

## get_path_restrict(model_name, restrict=True) — the resolver
`$MADGRAPH_INSTALL/models/import_ufo.py:201-241`. Returns `(model_path, restrict_file, restrict_name)`.

Two branches on whether `model_name` is itself a valid UFO path:

1. **`model_name` is NOT a valid UFO path** (UFOImportError at 204):
   - if no `-` in name → re-raise (with a special mssm→MSSM_SLHA2 error message, 207-209).
   - else split on `-`: everything before the last `-` is the model, the last token is `restrict_name` (210-218). So `sm-no_b_mass` → model `sm`, restrict `no_b_mass` → `restrict_file = <model_path>/restrict_no_b_mass.dat` (220).
   - **`-full` is the bypass** (223-224): `split[-1] == 'full'` → `restrict_file = None`. So `import model sm-full` loads the UNRESTRICTED UFO (no default restriction applied). This is the canonical way to get massive charm/e/mu AND off-default behaviour without picking a specific restrict file.

2. **`model_name` IS a valid UFO path** (else, 225-239):
   - `restrict_name = ""`.
   - **Implicit default** (228-229): if `restrict` is truthy AND `restrict_default.dat` exists in the model dir → `restrict_file = restrict_default.dat`. This is why plain `import model sm` is silently restricted (charm/e/mu massless, diagonal CKM — see sm-restrict-files.md).
   - else `restrict_file = None`.
   - if `restrict` is a STRING (233-239): treat it as a relative-to-model path, then an absolute path; if neither exists → `raise Exception("%s is not a valid path for restrict file")`. This is the programmatic override path (not the `model-tag` CLI form).

NOTE: branch 1 builds the path from `restrict_<tag>.dat` but does NOT check existence — a typo'd tag (`sm-no_b_masss`) produces a path that fails later at card-read time, not here. Branch 2's string override DOES check existence and raises early.

## find_restrict_card(model_name, base_dir, no_restrict=True, online=True) — the lister
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:2912-2949`. Returns a LIST of valid `model` / `model-tag` strings for completion/validation.
- `no_restrict=True` → seeds output with the bare `model_name` (2917-2918).
- `local_model` = does `<base_dir>/<model_name>/couplings.py` exist (2922).
- online + not-local + in `self._online_model` → returns `['<model>-<tag>' for tag in online tags]` and STOPS (2924-2926). Online DB enumeration is installation slice; recorded here only as the early-return.
- not local → return whatever's accumulated (2928-2930).
- if `restrict_default.dat` exists → append `'<model>-full'` (the bypass option, 2936-2937).
- for every `restrict_<tag>.dat` (excluding `*default.dat`) → append `'<model>-<tag>'`, tag = `name[9:-4]` (2940-2946).

## Caution
- `-full` and `restrict_default.dat`-presence are coupled: a model with NO `restrict_default.dat` is unrestricted by default already, and `-full` is only OFFERED by the lister when a default exists. But `get_path_restrict` honours `-full` as a bypass regardless (223-224).
- `get_path_restrict` does not validate the constructed `restrict_<tag>.dat` exists in the dash branch — invalid tags surface downstream, not here.
- The implicit-default branch only fires when `restrict` is truthy; `import_model(..., restrict=False)` skips even `restrict_default.dat`. Whether the CLI ever passes `restrict=False` is model-loader's orchestration slice.
