---
description: ALOHA-only output mode (output aloha --format=) — how do_output short-circuits to write Lorentz routines without a process directory (MG5_aMC v3.7.1)
---

# ALOHA-only output mode

Triggered when `self._export_format == 'aloha'` in `do_output`. File: `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:9157-9187`. Returns early — no exporter, no Template copy, no process directory, no finalize.

## Flow
1. `format = [d[9:] for d in args if d.startswith('--format=')]`; default `'Fortran'` if absent (`:9159-9163`). Accepts the `--format=` value verbatim (card lists F | CPP | GPU | Python; `'Fortran'` is the literal default).
2. Output dir from `--output=<dir>` (`:9165`). If absent: locate the UFO model via `import_ufo.find_ufo_path(self._curr_model['name'])` and use `<ufopath>/<format>`, creating it if missing (`:9166-9170`). If `--output=` given but not an existing dir -> InvalidCmd (`:9173`).
3. `names = [d for d in args if not d.startswith('-')]` -> `wanted_lorentz = aloha_fct.guess_routine_from_name(names)` (`:9177-9178`). Bare names select specific routines.
4. Build `AbstractALOHAModel(self._curr_model.get('name'))`, add the model's lorentz objects (`:9180-9181`).
5. If wanted_lorentz -> `compute_subset(wanted_lorentz)`; else `compute_all(save=False, custom_propa=True)` (`:9182-9185`).
6. `aloha_model.write(output, format)` (`:9186`), then `return`.

## Notes
- `'aloha'` is in `_export_formats` but NOT in `_v4_export_formats` (`madgraph_interface.py:3016`), so an MG4 v4 model cannot use it — check_output's UFO-required guard at `:1732` fires.
- check_output returns immediately for aloha (`:1741-1742`) without resolving a process `_export_dir` — the aloha branch manages its own `output` variable.
- The ALOHA routine-GENERATION algorithm (how compute_subset/compute_all build the Lorentz routines) is the aloha slice; output mode only selects routines and a target format and calls write.
