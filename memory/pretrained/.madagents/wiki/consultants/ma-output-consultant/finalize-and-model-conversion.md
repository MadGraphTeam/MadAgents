---
description: finalize() — UFO->MG4 model conversion (UFO_model_to_mg4), helicity-recycling P1N wanted_lorentz augmentation, jpeg/eps/html generation (MG5_aMC v3.7.1)
---

# finalize() and model conversion

`finalize` in `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:9686`. Runs after `export()`.

## Model handling (`:9694-9731`)
- MG4 v4 model path -> `export_model_files` + `export_helas` (copies, no UFO conversion) (`:9695-9699`).
- UFO model (normal) -> compute `wanted_lorentz = self._curr_matrix_elements.get_used_lorentz()` and `wanted_couplings = get_used_couplings()` (`:9704-9705`).

### Helicity-recycling wanted_lorentz augmentation (`:9707-9712`) — the OUTPUT-TIME trigger
For `madevent`, when `'no_helrecycling'` NOT in flaglist AND not a LoopAmplitude:
```
for (name, flag, out) in wanted_lorentz[:]:
    if out == 0:
        newflag = list(flag) + ['P1N']
        wanted_lorentz.append((name, tuple(newflag), -1))
```
This duplicates each `out==0` Lorentz routine with a `P1N` tag and `out=-1` so ALOHA generates the recycling variant. (The recycling ALGORITHM itself is the mc-integration slice; output emits the routine.) Disabled exactly when flaglist has `no_helrecycling`. CAUTION — only two things put `no_helrecycling` in flaglist (`madgraph_interface.py:9126`, `:9141`): an explicit `--hel_recycling=False` arg, and spin>3 in the model. `--me_exporter=` does NOT — it appends `--hel_recycling=False` to *args* at `:9132`, but the `:9125` flaglist test already ran above it, so me_exporter's suppression flows only into the exporter opt (`output_options['hel_recycling']`, export_v4.py:4214-4216), not this gate. With `output madevent --me_exporter=cpp` on an SM-like model, flaglist is `['me_exporter=cpp']` and this P1N block STILL fires. See no-helrecycling-two-mechanisms.md.

### convert_model dispatch (`:9721-9731`)
- `'store_model'` in flaglist (`--postpone_model`) -> stash `previous_lorentz`/`previous_couplings`, do NOT convert yet (lets a later same-dir output of a different exporter merge) (`:9716-9723`).
- else -> `self._curr_exporter.convert_model(model, wanted_lorentz, wanted_couplings)` and same for `_me_curr_exporter` if present (`:9725-9731`).

## convert_model -> UFO_model_to_mg4 (`export_v4.py:1023`)
`ProcessExporterFortran.convert_model` (`:1023`):
- write_dir = `<PROC_DIR>/Source/MODEL` (`:1032`).
- `UFO_model_to_mg4(model, write_dir, ...)` (`:1039`, class def `:6879`) then `.build(wanted_couplings)` (`:1040`) — emits coupl.inc, param_read.f, the MG4-format Fortran model files.
- ALOHA Lorentz routines computed (compute_subset(wanted_lorentz) or compute_all) and written to `<PROC_DIR>/Source/DHELAS` (`:1062-1071`).
- `vector.inc` option True only for madevent (`:1070`).
- copies aloha_functions.f (or _loop / _fd variant), then `make_model_symbolic_link` (`:1077-1092`).
- `ProcessExporterFortranME.convert_model` (`:4339`) ALSO copies the full UFO model tree into `<PROC_DIR>/bin/internal/ufomodel` and writes `restrict_default.dat` there (`:4347-4361`).

## Config-file save (`:9742-9759`)
- NLO/ewsudsa -> `Cards/amcatnlo_configuration.txt`.
- madevent/madweight -> `Cards/me5_configuration.txt` (with mg5_path).

## Dedicated exporter finalize (`:9765`)
Calls `self._curr_exporter.finalize(matrix_elements, history, options, flaglist, **add_options)`.
ME finalize (`export_v4.py:4615`): sets proc_characteristic (grouped_matrix, complex_mass_scheme, gauge, pdg_initial1/2), writes combine_events.f / maxconfigs.inc / maxparticles.inc, touches `SubProcesses/done`, generates jpeg+html.

### proc_characteristics file — output-time facts the run interface reads (`:587-589`, `:4636-4736`)
`create_proc_charac` (`:587`) writes `self.proc_characteristic.write(<PROC_DIR>/SubProcesses/proc_characteristics)`
(`:589`), called from ME finalize at `:4736`. The object is a `banner.ProcCharacteristic` (ConfigFile,
`banner.py:1743`) built at exporter `__init__` (`:203`) and populated across output:
- defaults `banner.py:1747-1771`: `grouped_matrix=True`, `hel_recycling=False`, `single_color=True`,
  `gauge='U'`, `complex_mass_scheme=False`, `nlo_mixed_expansion=True`, and `colored_pdgs` (numeric
  default list read fresh at `banner.py:1747-1771` — differs from the per-process probed set below), etc.
- finalize overrides (`:4637-4655`): `grouped_matrix=False` UNLESS MEGroup; `nlo_mixed_expansion`,
  `complex_mass_scheme`, `gauge` from `mg5options`; `pdg_initial1/2` = list of initial-state PDGs.
- `grouped_matrix=True` re-forced by MEGroup.finalize AFTER super() (`:6860`) — so for the production
  MEGroup path the field is always True regardless of the `:4637` else.
- `hel_recycling` field set in MEGroup.generate_subprocess_directory (`:6277`, = `self.opt['hel_recycling']`).
- `single_color=False` set at `:1340` when any diagram is multi-color (else stays default True).
- `nb_channel = make_info_html(...).rep_rule['nb_gen_diag']` (`:4725`).
- `colored_pdgs`/`nexternal`/`ninitial`/`max_n_matched_jets` set per-ME at `:5007-5027`.
- Probe-confirmed (v3.7.1, `generate u u~ > z`, default SM import = unitary gauge): file carries
  `grouped_matrix = True`, `hel_recycling = True`, `single_color = True`, `gauge = unitary`,
  `pdg_initial1 = [2]`, `pdg_initial2 = [-2]`, `colored_pdgs = [1,2,3,4,5,6,21]`, `nb_channel = 1`.

### output also writes the DEFAULT run_card and MA5 cards (`:254-283`, `:540-582`)
`ProcessExporterFortran.finalize` (`:540`, invoked from ME finalize at `:4739`) calls `create_run_card`
which `run_card.create_default_for_process(proc_characteristic, history, processes)` then writes
`Cards/run_card_default.dat` and copies it to `Cards/run_card.dat` (`:281-283`). A second exporter's
`run_card_class` overrides via TMP_variable (`:553-555`). It also calls `create_MA5_cards` (`:560`):
IF `opt['madanalysis5_path']` set AND `proc_defs` present, writes `madanalysis5_{hadron,parton}_card_default.dat`
and copies to the operative `_card.dat` names (`:578-582`) — turning MA5 ON by default. `proc_defs` is
stashed by `pass_information_from_cmd` (`:532-535`, = `cmd._curr_proc_defs`). So output-time finalize is
what creates the operative run_card; the run_card CONTENT/defaults are the card slice's, but the FACT
that output writes run_card_default.dat + run_card.dat (probe-confirmed both present) is this slice's.

### beam_polarization gate (export_processes `:216-246`)
Before generating subprocess dirs, `export_processes` sets `self.beam_polarization[beam-1] = False` for
any beam whose initial-state particle has `spin != 2` (i.e. not a spin-1/2 fermion). Default `[True,True]`.
Drives whether per-beam polarization machinery is emitted.

## raster (PNG) / eps / html (`export_v4.py:4623-4719`)
- `'nojpeg'` in flaglist -> `makejpg=False` (`:4623`). flaglist gets `'nojpeg'` from `do_output`'s `nojpeg` (`:9735`), itself from `-nojpeg` or `--noeps=True`. NOTE the EPS `matrix*.ps` write is a SEPARATE gate (`output_options['noeps']` inside generate_subprocess_directory), not this `nojpeg` flaglist — `-nojpeg` skips only the raster and keeps the `.ps`, `--noeps=True` kills both. See eps-jpeg-two-gates.md.
- The raster conversion requires `misc.which('gs')` (ghostscript); else silently skipped (`:4705`). Runs `bin/internal/gen_jpeg-pl` per P-dir (`:4708`). DESPITE the `jpeg`/`nojpeg`/`makejpg` naming, `gen_jpeg-pl` emits **PNG** (`gs -sDEVICE=pngmono -sOutputFile=matrix$imatrix%00d.png`), not `.jpg` — probe `generate u u~ > z` produced `matrix11.png`, no `.jpg`. The names are a historical misnomer. See eps-jpeg-two-gates.md.
- `gen_cardhtml-pl` web pages (`:4714`); `gen_infohtml.make_info_html(self.dir_path)` (`:4719`).
- EPS drawing: `draw.MultiEpsDiagramDrawer(...).draw()` in generate_subprocess_directory paths (`:2984`, `:3782`, `:4537`, `:6361`) — drawing core `core/drawing.py`, EPS emission `iolibs/drawing_eps.py`.

## Final user messages (`:9771-9777`)
"Output to directory ... done." for madevent/standalone/standalone_cpp/madweight/matchbox; "Type launch ..." for madevent/NLO.

## Caution
- The P1N augmentation is silent: a madevent output WITHOUT no_helrecycling will carry extra recycling Lorentz routines even though the user never asked. The DISABLE side (spin>3, me_exporter, explicit flag) is the part to verify per input.
