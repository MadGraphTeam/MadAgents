---
description: ProcessExporterFortranFKS.finalize — what the NLO finalize step writes/links (proc_characteristic, run/shower cards, StdHEP 3-branch, jpeg/html, make_amcatnlo_tar, MA5).
---

# finalize for the NLO process dir (v3.7.1)

`ProcessExporterFortranFKS.finalize(self, matrix_elements, history, mg5options, flaglist)` — `$MADGRAPH_INSTALL/madgraph/iolibs/export_fks.py:842`. This is the per-output (not per-subprocess) wrap-up. The optimised default exporter's `finalize` (`:4700`) just delegates here; EW-Sudakov's (`:5061`) calls `super().finalize` then writes the python dispatcher.

## proc_characteristic populated (:870-885)
- `ew_sudakov` = `'ewsudakov' in matrix_elements.keys() and matrix_elements['ewsudakov']` (`:871`).
- `grouped_matrix=False` (`:874`), `complex_mass_scheme` from mg5options (`:875`), `nlo_mixed_expansion` from mg5options (`:876`).
- `perturbation_order` (`:878-885`): derived by regex `\[(.*)\]` on `history.get('generate')` (the first process string). Appends `'QED'` if QED in the bracket, `'QCD'` if QCD. So the order list is read back out of the process-string brackets, NOT from the matrix element. Then `create_proc_charac()` (`:887`).

## Cards + model files written (:889-904)
- `orderstag_base.inc` rewritten (`:889`, `write_orderstag_base_file`).
- `create_run_card(processes, history)` (`:892`, def `:802`): instantiates `banner_mod.RunCardNLO()` (the NLO-specific run-card class, DISTINCT from LO `RunCard`), `create_default_for_process(proc_characteristic, history, processes)`, writes BOTH `Cards/run_card_default.dat` and `Cards/run_card.dat` (`:811`-812). No external template arg — defaults come from the RunCardNLO class itself.
- `create_shower_card` (`:893`, def `:817`): `shower_mod.ShowerCard()`, `create_default_for_process(...)`, writes `shower_card_default.dat` + `shower_card.dat` BOTH using `template=Template/NLO/Cards/shower_card.dat` (`:825`-828) — unlike run_card, the shower card REQUIRES the template file to render. NOTE the in-source file is `run_card.dat`/`shower_card.dat` (the "run_card_NLO.dat" name in some docs is not what this exporter emits).
- `Source/MODEL/get_mass_width_fcts.f` + `makeinc.inc` via `write_get_mass_width_file` (`:904`, def `:1408`) — emits get_mass_from_id / get_width_from_id model functions.
- Touch `SubProcesses/done` (`:907`).

## lhapdf sanity check (:847-859)
Calls `lhapdf --version`; on failure logs a warning telling the user to fix `lhapdf` in config or `amcatnlo_configuration.txt` (does NOT abort — built-in PDFs still work).

## jpeg / html / proc_card (:909-963)
- Discovers P-dirs by `os.path.isdir(proc) and proc[0]=='P'` (`:915-916`) — anything starting `P` in SubProcesses is treated as a subprocess dir.
- If `'nojpeg' not in flaglist`: per P-dir runs `bin/internal/gen_jpeg-pl` (`:923`).
- Runs `bin/internal/gen_cardhtml-pl` (multiple times, `:933`/`:962`/...).
- Writes `Cards/proc_card_mg5.dat` from `history.write` (`:952`).
- Duplicates `run_card`/`FO_analyse_card`/`shower_card` `.dat` → `_default.dat` (`:955-960`).

## make_amcatnlo_tar (:965-967)
If `SubProcesses/subproc.mg` exists: removes any `amcatnlo.tar.gz`, runs `bin/internal/make_amcatnlo_tar`. So the gate for tarball creation is the presence of `subproc.mg` (appended per born ME in generate_born_fks_files).

## StdHEP setup — three output_dependencies branches (:975-1042)
StdHEP (libstdhep.a + libFmcfio.a) is needed for NLO+PS with PY6/Herwig6. Driven by `mg5options['output_dependencies']`:
- **`'external'`** (`:981`): compiles `vendor/StdHEP` once if libs absent and no `vendor/StdHEP/fail` sentinel; on failure writes the `fail` file + warns "forbids to run NLO+PS with PY6 and Herwig6". On success links libstdhep.a/libFmcfio.a into `MCatNLO/lib` (`:1004-1009`).
- **`'internal'`** (`:1011`): copytree StdHEP into `Source/StdHEP`, links libs into `MCatNLO/lib`, forces a `make clean` (`:1026`).
- **`'environment_paths'`** (`:1028`): `misc.which_lib('libstdhep.a')`/`libFmcfio.a`; if found links abspath into `MCatNLO/lib`, else **raises InvalidCmd** (`:1038-1040`).
- Any other value → `MadGraph5Error` (`:1042`).

## MadAnalysis5 cards (:1045-1066)
If `madanalysis5_path` set and `proc_defs` not None: collects processes (falls back to `self.born_processes`, warns if empty — happens with `low_mem_multicore_nlo_generation`), then `create_default_madanalysis5_cards(... levels=['hadron'])`.

## Cautions
- StdHEP compilation is a side effect of `finalize` and is one-time/global (touches `MG5DIR/vendor/StdHEP`), not per-process — a stale `vendor/StdHEP/fail` sentinel silently skips re-compile.
- `perturbation_order` comes from re-parsing the process-string brackets in history, not the ME — if history is unavailable/odd this regex (`order[0]`) can IndexError. Runtime behavior — probe before asserting.
- `environment_paths` is the only StdHEP branch that aborts the whole finalize on a missing lib; external just warns and continues.
- P-dir discovery by `proc[0]=='P'` for jpeg/html is the same heuristic used elsewhere — a non-subprocess dir named `P*` would be swept in.
