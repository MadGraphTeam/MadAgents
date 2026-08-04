---
description: copy_template mechanics — which Template tree is copied into PROC_DIR per exporter (LO+Common for madevent, manual mkdir for SA), clean_template, why Cards/ becomes operative (MG5_aMC v3.7.1)
---

# Template copy mechanics (copy_template)

File: `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py`. `copy_template(model)` is the
first thing the exporter does in export() before writing subprocesses. It is what
populates `<PROC_DIR>/` with the operative skeleton (Cards, Source, bin, SubProcesses).

## VirtualExporter / base (`:136`)
`VirtualExporter.copy_template` returns nothing. Real work is in the concrete exporters.

## ProcessExporterFortranME.copy_template — madevent, production path (`:349-440`)
- If `dir_path` doesn't exist: `misc.copytree(Template/LO, dir_path, True)` then
  `misc.copytree(Template/Common, dir_path)` (`:360-364`). So madevent copies BOTH the
  `Template/LO` tree AND `Template/Common` into PROC_DIR. The `True` 3rd arg = overwrite.
- Copies `plot_card.dat` -> `plot_card_default.dat` if present (`:365-371`).
- If cwd == realpath(dir_path) (working in-place): re-copytrees LO + Common (`:373-394`).
- Writes `MGMEVersion.txt` (`:401-405`).
- If `opt['clean']` (i.e. NOT `-noclean`): runs `bin/internal/clean_template` (with `--web`
  if `MADGRAPH_BASE` in os.environ) to strip stale info, then writes `SubProcesses/MGVersion.txt`
  (`:408-426`).
- Writes `Source/vector.inc` via `write_vector_size` (`:431`).
- Copies `vendor/DiscreteSampler/{DiscreteSampler.f,StringCast.f}` into Source (`:434-437`).
- `write_pdf_opendata()` for the pdf open_data (`:440`).
- ME-subclass tail (`:4250-4276`): writes `Source/run_config.inc`, `SubProcesses/symmetry.f`,
  `SubProcesses/addmothers.f`, `copy_python_file()` (copies ~30 .py into bin/internal —
  madevent_interface, common_run_interface, banner, lhe_parser, cluster, systematics, etc.),
  and copies `Template/Running` -> `Source/RUNNING` iff `model['running_elements']`.

## ProcessExporterFortranSA.copy_template — standalone (`:2489-2560`)
- Returns immediately if dir_path already exists (`:2496-2497`).
- Does NOT copytree the whole LO tree. Manually `os.mkdir`s the dir structure (Source,
  Source/MODEL, Source/DHELAS, SubProcesses, bin, bin/internal, lib, Cards) (`:2503-2511`).
- temp_dir = `Template/LO`; copies only selected files: `TemplateVersion.txt`,
  `iolibs/template_files/makefile_sa_f_sp` -> `SubProcesses/makefileP`, `check_sa.f` (only
  if `format == 'standalone'`), `Source/make_opts` (`:2514-2548`). Writes `Source/makefile`.
- running_elements: rewrites makefileP to link `-lrunning` (`:2528-2540`).
So standalone is a much lighter skeleton — no Cards content, no madevent python, no Common.

## Why Cards/ under PROC_DIR is operative
For madevent, `Cards/` is copied from `Template/LO/Cards/` into `<PROC_DIR>/Cards/`. The
operative cards the user edits and `launch` reads are THESE copies. The install-tree
`Template/LO/Cards/*.dat` are the source skeleton, NOT what a run uses. (Card *content*
is owned by the per-card slices; this page only states which directory is operative.)

## Cautions
- `-noclean` skips the `clean_template` call (`opt['clean']` is `not noclean`, set in the
  factory opt). On a re-output into an existing dir without -noclean, clean_template runs
  and wipes prior run artefacts — a silent destructive step.
- `Template/Common` is copied ONLY by the ME exporter, not SA/standalone_cpp. Don't assume
  a standalone PROC_DIR has the Common files.
- `Template/Running` (-> Source/RUNNING) requires the RunningCoupling install; ME
  copy_template raises if `model['running_elements']` but the library is absent (`:4271`).
- Exact file list copied by copy_python_file drifts across versions — read `:4283-4338`
  for the current set rather than trusting this summary.
