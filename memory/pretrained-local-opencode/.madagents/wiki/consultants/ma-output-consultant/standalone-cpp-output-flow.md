---
description: C++/GPU standalone whole-output flow (export_cpp.py ProcessExporterCPP/GPU) — src/lib/Cards/SubProcesses skeleton, UFOModelConverterCPP model conversion (NOT UFO_model_to_mg4), raw-name P-dirs, finalize=compile only (MG5_aMC v3.7.1)
---

# C++ / GPU standalone output flow (export_cpp.py)

`output standalone_cpp` / `standalone_gpu` / `pythia8` / `matchbox_cpp` build a whole-output
exporter from `ExportCPPFactory` (see exportv4-factory-classes.md). This page is the OUTPUT
FLOW (copy_template -> convert_model -> generate_subprocess_directory -> finalize) for the
C++ path, which is materially DIFFERENT from the Fortran path. File:
`$MADGRAPH_INSTALL/madgraph/iolibs/export_cpp.py`.

## ProcessExporterCPP class attrs (`:2543-2562`)
- `grouped_mode = False` (so the C++ standalone path is NEVER grouped — no SubProcessGroup,
  one P-dir per matrix element).
- `exporter = 'cpp'` (drives `CPPUFOHelasCallWriter` selection, see export-phase-helas-writer.md).
- `default_opt = {'clean': False, ...}` — `clean` defaults FALSE, unlike the Fortran factory
  which sets `clean = not noclean`. No `clean_template` step on the C++ path.
- `oneprocessclass = OneProcessExporterCPP` (the per-ME `.h`/`.cc` emitter).
- `from_template` = `{'src':[rambo.h, rambo.cc, read_slha.h, read_slha.cc],
  'SubProcesses':[check_sa.cpp]}`. `to_link_in_P = ['check_sa.cpp','Makefile']`.
- `template_src_make = Makefile_sa_cpp_src`, `template_Sub_make = Makefile_sa_cpp_sp`.
- `create_model_class = UFOModelConverterCPP` (the C++ model converter, NOT UFO_model_to_mg4).

## copy_template (`:2577-2622`) — the C++ skeleton
- `os.mkdir(dir_path)` (`:2586`), then the dir loop mkdir `src`, `lib`, `Cards`, `SubProcesses`
  (loop `:2592-2597`). NO `Source/`, NO `bin/`, NO `HTML/`, NO `Template/LO` copytree.
- Writes `Cards/param_card.dat` DIRECTLY from `model.write_param_card()` (`:2604-2605`) — not
  the run-card machinery; the C++ path needs only a param card.
- Copies `from_template[key]` files into `src` and `SubProcesses` (`:2605-2607`).
- Fills `src/Makefile` and `SubProcesses/Makefile` from the template files, substituting
  `model` name (via `get_model_name`, - -> _, + -> _plus_) and `cpp_compiler` (`:2609-2620`).

## convert_model (`:2636-2643`) — UFOModelConverterCPP, NOT UFO_model_to_mg4
- `create_model_class(model, dir_path/src, wanted_lorentz, wanted_couplings).write_files()`.
- Emits `src/Parameters_<model>.{cc,h}` and the ALOHA C++ HelAmps. So the C++ model files
  live in `src/`, named `Parameters_sm.*`/`HelAmps_sm.*` — NOT `Source/MODEL/coupl.inc`.

## generate_subprocess_directory (`:2657-2685`) — raw-name P-dir, .h/.cc
- One P-dir per matrix element (no grouping). Named `P%d_%s` from the OneProcessExporter's
  `process_number` and `process_name` (`:2667`) — the RAW process name (`Sigma_<model>_<procname>`),
  NOT the q/l/vl abstraction the Fortran madevent path uses.
- `generate_process_files()` writes the process `.h`/`.cc` (`CPPProcess.{cc,h}`); then symlinks
  `to_link_in_P` (`check_sa.cpp`, `Makefile`) into the P-dir.

## finalize (`:2691-2695`) — compile only, no html/jpeg/tar/proc_charac
- `ProcessExporterCPP.finalize` is just `self.compile_model()` (runs `make_model_cpp`). NO
  jpeg/PNG, NO HTML info page, NO madevent.tar.gz, NO proc_characteristics file, NO run_card.
- So the rich Fortran-finalize artefact set (per-pdir-file-inventory.md, finalize-and-model-
  conversion.md, gen-infohtml-output-info-page.md) does NOT exist on the C++ path.

## ProcessExporterGPU (`:2859-2887`) — legacy in-tree GPU subclass
- Subclass of ProcessExporterCPP. `exporter = 'gpu'`, `oneprocessclass = OneProcessExporterGPU`,
  `create_model_class = UFOModelConverterGPU`. GPU-specific from_template (`gpu/rambo.{h,cc}`,
  `gpu/grambo.cu`, `gpu/mgOnGpuTypes.h`, `gpu/timer.h`, `gpu/Makefile`, `gpu/check.cc`, ...),
  GPU `to_link_in_P` (Makefile, timer.h, timermap.h, nvtx.h, perf.py, Memory.h, runTest.cc).
- `compile_model` OVERRIDDEN to a no-op (`def :2885`, `return :2886`) — GPU output does NOT compile at output
  time (needs nvcc; deferred to the user). This is the legacy in-tree GPU path; the modern
  cudacpp output is a separate PLUGIN (output plugin, not this class).

## ProcessExporterMatchbox / ProcessExporterPythia8 (`:2696-2701`)
- Both subclass ProcessExporterCPP with a different `oneprocessclass`. pythia8 additionally
  has `convert_model_to_pythia8` (`:2518`); the pythia8 config table entry uses output='dir'
  (no Template), see do-output-orchestration.md.
- CAUTION: ProcessExporterPythia8 OVERRIDES `grouped_mode = 'madevent'` (`:2701`) — it is NOT
  `grouped_mode=False` like the standalone_cpp/gpu/matchbox_cpp siblings. The "C++ path is never
  grouped" statement above is scoped to ProcessExporterCPP/GPU/Matchbox, not pythia8.

## Probe (v3.7.1, `generate u u~ > z`, `output standalone_cpp`)
- Top-level: `Cards/ lib/ src/ SubProcesses/` only (no Source, no HTML, no bin).
- `src/`: `Parameters_sm.{cc,h,o}`, `HelAmps_sm.{cc,h,o}`, `rambo.{cc,h,o}`,
  `read_slha.{cc,h,o}`, `Makefile` — the `.o` files confirm `compile_model` ran in finalize.
- `SubProcesses/`: `check_sa.cpp`, `Makefile`, and P-dir `P1_Sigma_sm_uux_z` (RAW name, not
  `P1_qq_z`) holding `CPPProcess.{cc,h}`, `check_sa.cpp`, `Makefile`.
- `Cards/`: `param_card.dat` ONLY (no run_card, no proc_card_mg5.dat).
- ABSENT (confirmed): `madevent.tar.gz`, `Source/MODEL/coupl.inc`, `SubProcesses/proc_characteristics`,
  `SubProcesses/procdef_mg5.dat`, `HTML/info.html`.

## CPPProcess API (`template_files/cpp_process_class.inc`, driven by check_sa.cpp)
The emitted `CPPProcess` class exposes (verbatim from cpp_process_class.inc):
- `virtual void initProc(string param_card_name)` (`:14`) — read param_card, set params.
- `virtual void sigmaKin()` (`:17`) — compute |M|².
- `void setMomenta(vector<double*>& momenta){p = momenta;}` (`:31`).
- `const double* getMatrixElements() const` (`:35`) — pointer to results.
- `const vector<double>& getMasses() const {return mME;}` (`:27`).
`check_sa.cpp` drives them in order: initProc("../../Cards/param_card.dat") → get_momenta →
setMomenta → sigmaKin → getMatrixElements.
Thread-safety: `Parameters_<model>` is a static-singleton (`cpp_model_parameters_h.inc:18`
`static getInstance()`, `:47` `static instance`) — global mutable state, so the default C++
standalone is NOT thread-safe across concurrent CPPProcess instances sharing the model params.

## Cautions
- Do NOT carry Fortran-madevent expectations onto the C++ path: no grouping (grouped_mode=False),
  no q/l P-dir abstraction (raw process names), no proc_characteristics, no run_card, no
  hel_recycling P1N gate (that gate is `_export_format=='madevent'`-only, finalize-and-model-
  conversion.md), no diagram html/png.
- standalone_gpu here is the LEGACY in-tree path with a no-op compile; the production CUDA path
  is `output plugin` (cudacpp), a different exporter not in export_cpp.py.
