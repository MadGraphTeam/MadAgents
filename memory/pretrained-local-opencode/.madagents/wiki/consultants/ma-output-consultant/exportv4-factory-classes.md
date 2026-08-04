---
description: ExportV4Factory exporter-class selection and the v4 exporter class hierarchy (SA/MatchBox/MW/ME/MEGroup) (MG5_aMC v3.7.1)
---

# ExportV4Factory and v4 exporter classes

File: `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py`.

## ExportV4Factory (`:9862`)
Signature `ExportV4Factory(cmd, noclean, output_type='default', group_subprocesses=True, cmd_options={})`. `output_type` branches:
- `'madloop'` / `'madloop_matchbox'` -> loop_exporters (`:9922`).
- `'amcatnlo'` -> export_fks ProcessExporterFortranFKS / ProcessOptimizedExporterFortranFKS (`:9943`) — NLO slice.
- `'ewsudsa'` -> export_fks ProcessExporterEWSudakovSA (`:9961`).
- `'default'` (tree-level, the do_output path) -> `:9974`.

### default-branch selection (`:9974-10046`), keyed on `cmd._export_format`
- `'matrix'` or anything `startswith('standalone')` -> `ProcessExporterFortranSA(dir, opt, format=format)` (`:10011`).
- `'madevent'` AND group_subprocesses:
  - LoopAmplitude -> `LoopInducedExporterMEGroup` (`:10017`).
  - else if `cmd._export_plugin` -> the plugin class (`:10020`).
  - else -> **`ProcessExporterFortranMEGroup`** (`:10022`) — production default.
- `'madevent'` not grouped: LoopAmplitude -> `LoopInducedExporterMENoGroup`, else `ProcessExporterFortranME` (`:10030`).
- `'matchbox'` -> `ProcessExporterFortranMatchBox` (`:10032`).
- `'madweight'` grouped -> `ProcessExporterFortranMWGroup` (`:10035`); ungrouped -> `ProcessExporterFortranMW` (`:10037`).
- `'plugin'` -> `cmd._export_plugin(...)`, with loop_induced_opt if LoopAmplitude (`:10038`).

### opt built for default branch (`:9977-9986`)
`clean=not noclean`, `complex_mass=cmd.options['complex_mass_scheme']`, `export_format=cmd._export_format`, `model`/`v5_model`/`running` from current model. `sa_symmetry=True` for `standalone_msP/msF/rw` (`:9990`).

## Class hierarchy (line numbers = class def)
- `VirtualExporter` (`:86`) — abstract base. Class attrs are the exporter contract: `grouped_mode='madevent'`, `sa_symmetry=False`, `check=True`, `output='Template'`, `exporter='v4'`, and `default_vector_size` (its numeric default read at `:90-111`). Stub methods: copy_template, generate_subprocess_directory, convert_model, finalize, pass_information_from_cmd, modify_grouping, export_model_files, export_helas.
- `ProcessExporterFortran` (`:177`) — v4 base. `default_opt` (`:181`), `grouped_mode=False` (overrides Virtual), `jamp_optim=False`. Carries write_decayBW_file, write_driver, write_addmothers, write_combine_events, write_dname_file (per card; these are invoked, detail owned by other slices).
- `ProcessExporterFortranSA` (`:2466`) — Standalone.
- `ProcessExporterFortranMatchBox` (`:3254`) — subclass of SA.
- `ProcessExporterFortranMW` (`:3380`) — MadWeight.
- `ProcessExporterFortranME` (`:4185`) — MadEvent (ungrouped). `finalize` at `:4615`.
- `ProcessExporterFortranMEGroup` (`:6195`) — MadEvent grouped, production default. `grouped_mode='madevent'` (`:6201`).
- `ProcessExporterFortranMWGroup` (`:10056`) — MadWeight grouped, `grouped_mode='madweight'`.

## ExportCPPFactory (`export_cpp.py:3470`)
Signature `ExportCPPFactory(cmd, group_subprocesses=False, cmd_options={})`.
Keyed on `cmd._export_format`: `pythia8`->ProcessExporterPythia8 (`:3480`), `standalone_cpp`->ProcessExporterCPP (`:3482`), `standalone_gpu`->ProcessExporterGPU (`:3484`), `matchbox_cpp`->ProcessExporterMatchbox (`:3486`), else `cmd._export_plugin`.

### C++ exporter class hierarchy (`export_cpp.py`)
Whole-output exporters (the factory return type, subclass `VirtualExporter`):
- `ProcessExporterCPP` (`:2543`) — standalone_cpp base; `exporter='cpp'`.
- `ProcessExporterMatchbox` (`:2696`), `ProcessExporterPythia8` (`:2699`),
  `ProcessExporterGPU` (`:2859`, `exporter='gpu'`).
Per-process emitters (one per matrix element, do the actual `.cc`/`.h`/`.cu` writing):
- `OneProcessExporterCPP` (`:526`) base, `OneProcessExporterGPU` (`:1405`),
  `OneProcessExporterMatchbox` (`:1814`), `OneProcessExporterPythia8` (`:1916`).
The C++ per-process emission (the analogue of matrix_*.f for Fortran) lives in the
OneProcessExporter* classes; routing only needs the factory + whole-output class above.

## Format enumerations (`madgraph_interface.py:3014`)
`_v4_export_formats = ['madevent','standalone','standalone_msP','standalone_msF','matrix','standalone_rw','madweight']`.
`_export_formats = _v4_export_formats + ['standalone_cpp','pythia8','aloha','matchbox_cpp','matchbox','standalone_gpu']`.
(MG4-format v4 models are restricted to `_v4_export_formats`; UFO required otherwise, `:1732`.)
