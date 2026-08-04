---
description: aMCatNLOCmd.compile + compile_dir — mode→executable mapping, the test_ME/test_MC/check_poles suite, internal-dependency (StdHEP/CutTools/IREGI) compilation, PYTHIA8 activation, pole-cancellation threshold.
---

# `compile()` / `compile_dir` — the NLO compile + test machinery

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`. `do_compile` (1888) is the thin command driver (covered in [[runtime-shell-commands]]); the worker is `compile(self, mode, options)` (5403), driven by `run_generate_events`. Per-subprocess compilation is the module-level `compile_dir` (106). This page owns the compile/test orchestration; the FKS/MadLoop code being compiled is the **fks**/**madloop** slices.

## Mode → executable (5434-5446)
- `'+' in mode` → keep only the part before `+` (5435).
- `mode in ['NLO','LO']`: `exe='madevent_mintFO'`, `tests=['test_ME']`; writes `SubProcesses/analyse_opts` from the FO analyse_card and updates `ajob_template` FO extrapaths (5439-5440).
- `mode in ['aMC@NLO','aMC@LO','noshower','noshowerLO']`: `exe='madevent_mintMC'`, `tests=['test_ME','test_MC']`; writes a DUMMY `analyse_opts` (`FO_ANALYSE=analysis_dummy.o ...`) so compilation goes through (5445-5446).
- `--nocompile`: if all `exe` already exist in every p_dir, returns early (5459-5461).

## Banner write + characteristics (5406-5412)
`compile` is the FIRST step of a run (called before `run()`): it `os.mkdir`s `Events/<run_name>/`, writes `<run_name>_<run_tag>_banner.txt`, and loads `SubProcesses/proc_characteristics`. `make_opts_var['madloop']='true'` if `has_loops` and no `OLP_virtuals` (5422-5424).

## PYTHIA8 Fortran activation (`activate_Pythia8_compilation`, 5237)
- For `NLO`/`LO`, OR whenever `not run_card['mcatnlo_delta']`: writes DUMMY `pythia8_opts` (`PYTHIA8TARGETS=pythia8_fortran_dummy.o`) and `pythia8_control_setup.inc` with `data is_pythia_active/-1/` (5244-5250). So ordinary aMC@NLO does NOT link PYTHIA8 into the Fortran — the shower runs externally.
- Only when `mcatnlo_delta=True` AND an event mode: requires `pythia8_path` (else `aMCatNLOError`), sets `PYTHIA8DATA` env, links `libpythia8.a -lz -ldl`, writes `is_pythia_active/0/` (available-but-not-initialised) (5252-5265). This is the only path that compiles PYTHIA8 INTO the executable, and it is gated on `mcatnlo_delta` — consistent with the `mcatnlo_delta requires parton_shower=='pythia8'` validity guard in [[runcardnlo-defaults-and-ickkw]].

`is_pythia_active`: `-1` = unavailable/dummy, `0` = available-not-yet-initialised.

## PDF library decision tree (5463-5530) — same `compile()` body
Selects how PDFs are linked (then `do_treatcards` writes run_card.inc at 5532):
- `pdlabel=='lhapdf'` and a hadron beam (|lpp| not in {0,3,4}) → `link_lhapdf` + `copy_lhapdf_set` (5468-5475).
- dressed-lepton (|lpp1|==|lpp2| ∈ {3,4}): LHAPDF FORBIDDEN (`aMCatNLOError`, 5483); `emela*` pdlabel → eMELA path (links libeMELA.a, UV scheme from sminputs, 5485-5513); internal lepton densities → `copy_lep_densities` (5515-5517).
- `lpp==1` both → "Using built-in libraries for PDFs"; `lpp==2` both with `edff`/`chff` → gamma-UPC (5519-5529).

## Internal-dependency compilation (5567-5648) — only with `output_dependencies='internal'`
After Source builds (`libdhelas/libgeneric/libmodel/libpdf.a` checked, else `aMCatNLOError('Compilation failed')`, 5559-5565):
- **StdHEP** (5567-5585): if `libstdhep.a`/`libFmcfio.a` missing and `Source/StdHEP` exists → compile; FAILURE is non-fatal — warns "StdHep failed to compiled. This forbids to run NLO+PS with PY6 and Herwig6". This is the build-side counterpart of the StdHEP shower-availability gate in [[askrunnlo-dialog-and-showers]] — no libstdhep.a ⇒ no PYTHIA6/HERWIG6.
- **CutTools** (5587-5600): missing `libcts.a`/`mpmodule.mod` → compile (`-j1`); failure is FATAL (`aMCatNLOError`).
- Compiler-version check (5602-5620, 5629-5648): both CutTools and IREGI store `compiler_version.log`; if current gfortran differs, auto-recompile (`cleanCT`/`cleanIR`).
- **IREGI** (5622-5627): compiled if `libiregi.a` missing and `Source/IREGI` exists.

## Test suite
`tests` list per mode (above); `check_poles` appended when `has_loops` and no `OLP_virtuals` and mode ∈ {NLO,aMC@NLO,noshower} (5651-5655). Input files written by `write_test_input` (5752):
- `test_ME`/`test_MC`: header (`2` for ME / `1 \n <SHOWER>\n 1 -0.1\n-1 -0.1` for MC) + `-2 -2` (random E/angle) + `100 100` (100 soft + 100 collinear points) + `0` (all FKS configs) + 50×`-1`.
- `check_poles`: `20 \n -1`.

Per-subprocess execution (`compile_dir`, 106, run on MultiCore at 5675-5688):
- `test_ME`/`test_MC` compile/run the binary `test_soft_col_limits` (133), output → `<test>.log`.
- `check_poles` SKIPPED for LOonly dirs (`parton_lum_0.f` present, 127) or no-virtual dirs (no `V*`, 130); after running it tars `MadLoop5_resources` → `.tar.gz` (142-146).
- if not reweightonly: compile+run `gensym <mode>`, then compile `exe` (mintFO/mintMC) (148-154).
- event modes also compile `reweight_xsec_events` (155-156).

## Test-log parsing (`check_tests` 5705)
- `parse_test_mx_log` (5716): any `FAILED` in log → `aMCatNLOError('Some tests failed, run cannot continue...')`; else "Passed."
- `parse_check_poles_log` (5728): counts PASSED/FAILED lines; **fails the run only when the fail-fraction `nfail/(nfail+npass)` exceeds the threshold literal at 5728** (read it) → `aMCatNLOError('Poles do not cancel, run cannot continue')`; 0 points tried → warn-only. The pole-cancellation PHYSICS is fks/madloop; this runtime fail-fraction threshold gate is the slice boundary.
- `check_tests` (5705) itself re-skips `check_poles` for LOonly folders (`parton_lum_0.f` present OR no `V*`).

## gfortran requirement (`check_compiler`, 164)
NLO enforces a minimum gfortran version. `check_compiler` (190-192) blocks (`aMCatNLOError`) or warns on an old major/minor — read the exact version literals at 190-192. `aMCatNLOCmd.__init__` (1524) calls `check_compiler(block=True)` when `[real=QCD]` is NOT in the proc_card (virtuals present).

## Cautions
- StdHEP compile failure is SILENT to the run (warn only) but removes PY6/HERWIG6 NLO+PS capability — a HERWIG6 shower request can later fail/become-unavailable purely because libstdhep.a never built. Build-time gate, separate from the dialog availability gate.
- `check_poles` tolerance is a fail-FRACTION threshold (literal at 5728), NOT all-points-must-pass — a run can proceed with a bounded fraction of pole-check points failing.
- Ordinary aMC@NLO compiles a PYTHIA8 *dummy* (`is_pythia_active/-1/`); only `mcatnlo_delta` links real PYTHIA8 into Fortran. Do not assume "aMC@NLO with PYTHIA8" means PYTHIA8 is compiled in.
- (Runtime predictions here — exact warning text, which libs get built — are source-read, not probe-verified end-to-end; internal-dep compilation only fires under `output_dependencies='internal'`.)
