---
description: do_convert_model py2->py3 UFO converter, auto_convert_model option, and the auto-conversion trigger in do_import on UFOError (v3.7.1).
---

# UFO py2 -> py3 conversion

All in `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`.

## do_convert_model `:3483-3520`
"Not in help" shortcut for `convert model <full_path>`. In-place edit (NO backup).
- Requires a full directory path (`os.path.isdir(args[0])`) else raises. `:3486-3487`.
- Confirmation gate `:3491-3495`: literal `if not ('-f' not in args or self.options['auto_convert_model']):`. Solving the boolean: the prompt fires ONLY when **`-f` IS in args AND `auto_convert_model` is False**. (De Morgan: `not(A or B)` with `A='-f' not in args`, `B=auto_convert` → `('-f' in args) and not auto_convert`.) CAUTION — the `-f` sense is INVERTED vs intuition: `-f` does NOT suppress the prompt; with `auto_convert_model` False, passing `-f` is the ONLY way to MAKE the prompt appear, and NOT passing `-f` means it never prompts (proceeds silently). This is almost certainly a code bug, but it is the v3.7.1 behavior. Warns conversion is in-place, "NO guarantee of success," "can make the model stop working under PY2 as well." Default answer 'y'.
- SMEFT/auto-recovery relevance: the auto-conversion path (`do_import:5796`) issues `convert model <path>` with NO `-f` → `'-f' not in args` is True → inner expr True → `not True`=False → **the prompt NEVER fires on the auto-recovery path**; conversion proceeds silently. So a freshly-downloaded OLD (py2) SMEFT UFO that raises UFOError is converted in-place with no confirmation when `auto_convert_model` is True (default). The in-place edit has NO backup (see CAUTION below).
- `object_library.py`: replaces `.iteritems()`->`.items()` `:3500`; rewrites `raise UFOError, "msg"` -> `raise UFOError("msg")` via regex `:3502-3503`.
- Copies `models/sm/write_param_card.py` into the model dir (overwrites). `:3507-3508`.
- `__init__.py`: prepends `import object_library` / `import function_library` if missing. `:3511-3520`.

CAUTION: conversion only patches `object_library.py` + `__init__.py` + drops in sm's `write_param_card.py`. It does NOT touch `parameters.py`/`couplings.py`/`vertices.py`/`lorentz.py`. Models with py2-isms elsewhere (print statements, dict.has_key, etc.) will still fail to import after conversion.

## auto_convert_model option
- Default `True` `:3096`.
- Setter `set2_auto_convert_model` `:8687-8696`: prepends `auto_convert_model`, `check_set`, stores as bool via `ConfigFile.format_variable`. Docstring warns the UFO model will be overwritten.
- Dispatched in `do_set` for `args[0] in ['crash_on_error','auto_convert_model','acknowledged_v3.1_syntax']` `:9041`.

## Auto-conversion trigger in do_import `:5787-5806`
`import_ufo.import_model(...)` wrapped in try; on `ufomodels.UFOError`:
- If `auto_convert_model` True `:5793`: logs "fail to load model but auto_convert_model is on True. Trying to convert the model", runs `convert model <model_path>`, then retries the import with `auto_convert_model` temporarily forced False (so a second failure does not loop). If retry raises, re-raises the original `err`. `:5796-5804`.
- If False `:5805-5806`: raises `InvalidCmd('UFO model not python3 compatible. You can convert it via the command\nconvert model <path>\nYou can also type "set auto_convert_model T" ...')`.

`model_path` for the message comes from `import_ufo.get_path_restrict(args[1])`. `:5792`.

## Gaps
- Whether a given model actually converts cleanly is runtime/model-specific — not statically decidable. The converter is best-effort by design (docstring "NO guarantee of success").
