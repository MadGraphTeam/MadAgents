---
description: do_output control flow — flag parsing, format->exporter selection, group_subprocesses=Auto, export()/finalize() sequence (MG5_aMC v3.7.1)
---

# do_output orchestration

`do_output` is the `output <dir>` entry point. File: `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:9108`.

## Sequence (top level)
1. `self._export_plugin = None`; `self.check_output(args)` (`:9114`) -> sets `self._export_format` and `self._export_dir`.
2. Parse flags into `noclean`/`force`/`nojpeg` and `flaglist` (`:9116-9142`).
3. ALOHA-only short-circuit if `_export_format == 'aloha'` (`:9157`, returns at `:9187`).
4. Build `config` dict mapping format -> {check, exporter, output} (`:9197-9208`).
5. Decide `group_processes` (`:9257-9287`).
6. Instantiate exporter via `ExportV4Factory` (v4) or `ExportCPPFactory` (cpp/gpu) (`:9290-9296`).
7. `self.export(nojpeg, main_file_name, group_processes, args)` (`:9345`) then `self.finalize(nojpeg, flaglist=flaglist)` (`:9348`).
8. Record `_done_export`, reset `_export_dir = None` (`:9351-9354`).

## Flag parsing (`:9116-9152`)
- `-noclean`, `-f` (force), `-nojpeg`; `--noeps=True` also sets `nojpeg=True` (`:9119`).
- `--postpone_model` -> flaglist `'store_model'` (`:9123`).
- `--hel_recycling=False` -> flaglist `'no_helrecycling'` (`:9125`).
- `--me_exporter=<name>` (`:9129`): appends `--hel_recycling=False` to **args** if not already present (`:9131-9132`, cpp/cuda mixed-mode rule), and appends flaglist `me_exporter=<name>`. NOTE the ordering: the flaglist test for `no_helrecycling` at `:9125` runs ABOVE `:9131`, so the arg appended here does NOT reach flaglist — it reaches only `line_options` (`:9144`) and thence the exporter's `output_options['hel_recycling']`. So me_exporter suppresses recycling at the exporter-opt level, NOT via the finalize `no_helrecycling` flaglist gate (`:9707`). See no-helrecycling-two-mechanisms.md.
- spin>3 auto-disable (`:9140`): `if any(spin > 3 for spin in self._curr_model.get_all_spin())` -> flaglist `'no_helrecycling'` + appends `--hel_recycling=False`. Spin is the MG5 2S+1 convention (`base_objects.py:2020`, `get_all_spin` returns `{p.get('spin') ...}`), so spin>3 means 2S+1>3 i.e. S>=2: spin-3/2 (value 4) and spin-2 (value 5).
- `--format=` / `--output=` only consumed in the ALOHA branch.
- `-name <name>` -> `main_file_name` (pythia8 main program name) (`:9148`).
- `line_options`: every `--k=v` (or `--k`->True) collected into dict, passed as `cmd_options` to the factory (`:9144`).

## config table (`:9197-9208`) — {check, exporter, output}
- `madevent`: check True, exporter v4, output Template.
- `matrix`: check False, v4, output **dir** (just matrix_*.f, no Template).
- `standalone`/`standalone_msF`/`standalone_msP`/`standalone_rw`: v4, Template (msF/msP/rw check False).
- `standalone_cpp`/`standalone_gpu`: exporter **cpp**, Template.
- `pythia8`: cpp, output **dir**.
- `matchbox`: v4, Template; `matchbox_cpp`: cpp, Template.
- `madweight`: v4, Template.
- `plugin`: pulls check/exporter/output off `self._export_plugin` (`:9211`).

`check=True` means: if dir exists and not noclean, prompt/delete (`:9242-9253`).

## group_subprocesses decision (`:9257-9287`)
- option True/False -> used directly.
- option `'Auto'` -> default True, BUT turned False for a 1->N decay process defined with multiparticle labels yielding >1 subprocess with non-unique process ids (`:9266-9285`), so per-channel branching ratios stay separable. Loop-induced madevent decays in this case emit a multi-line warning recommending `group_subprocesses=True` (`:9272-9284`).

## second exporter (`--me_exporter`) (`:9298-9323`)
If `me_exporter` differs from the primary `exporter`, a second exporter `_me_curr_exporter` is built (v4 via factory, or cpp/gpu via ExportCPPFactory + plugin import). Both get `pass_information_from_cmd`. Used in `export()` for madevent (CPP/CUDA matrix-element alongside Fortran madevent).

## madevent-only channel limits (`:9335-9342`)
For `madevent`: sets `base_objects.Vertex.max_n_loop_for_multichanneling` (from option `max_npoint_for_channel`, else a default read at `:9335-9342`) and `max_tpropa` (`max_t_for_channel`).

## Path resolution in check_output (`:1749-1778`)
- User-supplied path popped at `:1751`. Forbidden chars checked at `:1752`: `['>','<',';','&']` — a path containing any raises InvalidCmd. **Space is NOT in this list** — there is no explicit no-space check. A name with a space fails only because line tokenization splits it (`output my proc` -> path=`my`, `proc` left as a stray arg), not via a validation message.
- Reserved dir names (`HELAS`, `tests`, `MadSpin`, `madgraph`, `mg5decay`, `vendor`, `madevent_gpu`, `madevent_simd`) rejected only if cwd==MG5DIR (`:1764`).
- `output auto` -> `get_default_path()`; auto-appends `-noclean` if dir already exists (`:1761`, `:1777`).
- No path given at all (`args` empty or next arg starts with `-`) -> `get_default_path()` (`:1776`, non-pythia8).

## get_default_path — default dir naming (`:1879-1961`)
When no name is given, MG5 auto-generates `<PREFIX>_<model>_<i>` where `<model>` = `self._curr_model['name']` and `<i>` is the first integer in a bounded `range(...)` for which no such dir exists (`:1953-1958`); exceeding that cap -> InvalidCmd (`:1959`) — read the cap fresh at `:1953-1959`. So the counter is a first-free-slot scan starting at **0**, NOT a monotonic counter. Prefix by `_export_format`:
- `madevent*` -> `PROC_<model>_<i>` (`:1909`). Default `output` (format=madevent) on `sm` first run -> **`PROC_sm_0`** (verified against source).
- `NLO`/`ewsudsa` -> `PROCNLO_<model>_<i>` (`:1904`).
- `standalone` -> `PROC_SA_<model>_<i>`; `standalone_cpp` -> `PROC_SA_CPP_...`; `standalone_gpu` -> `PROC_SA_GPU_...` (`:1913-1928`).
- `madweight` -> `PROC_MW_...`; `matchbox`/`matchbox_cpp` -> `PROC_MATCHBOX_...`; `plugin` -> `PROC_PLUGIN_...` (`:1929-1943`).
- `pythia8` -> `pythia8_path` or `.` (no PROC dir) (`:1944`); fallback else -> `.` (`:1950`).

## Cautions
- `check_output` at `:2049` is a WEB-RESTRICTED override (raises unless madevent); the operative one for normal CLI is `CheckValidForCmd.check_output` at `:1707`.
- Default cards land in `<dir>/Cards/` only for Template-copying formats (madevent copies Template/LO -> Cards/ operative, per template-copy-mechanics + finalize's default run_card/MA5 creation); `output matrix`/standalone_cpp/pythia8 do NOT produce a full run_card Cards/ set.
