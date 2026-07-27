---
description: Fortran standalone output flow (ProcessExporterFortranSA) — P-dir file inventory (matrix.f/check_sa.f/nexternal.inc/pmass.inc), f2py python wrapper entry points (matrix2py vs all_matrix2py), --prefix flag, per-P make default target = check, standalone caveats (MG5_aMC v3.7.1)
---

# Fortran standalone output flow (ProcessExporterFortranSA)

`output standalone <dir>` (also `matrix`, `standalone_msP/msF/rw`) selects
`ProcessExporterFortranSA` (`export_v4.py:2466`, factory `:10011` — anything
`startswith('standalone')` or `'matrix'`). This page covers the SA-specific P-dir
inventory, the f2py python wrappers, and caveats. copy_template skeleton (manual mkdir,
no Template/LO copytree, no Common) is in template-copy-mechanics.md; factory selection in
exportv4-factory-classes.md. File: `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py`.

## generate_subprocess_directory (`:2866-3012`) — per-P file inventory
P-dir = `SubProcesses/P<shell_string>` (`:2873`). shell_string carries the process's `@N`
number as the numeric prefix (e.g. `@42` → `P42_gg_ttx`); default first proc → `P1_...`.
Files WRITTEN into each P-dir:
- `matrix.f` (`:2920`; `matrix_prod.f` for `standalone_msP`) — via `write_matrix_element_v4`.
- `f2py_matrix_wrapper.f` (`:2943`) — the per-process f2py wrapper (see below).
- `nexternal.inc` (`:2969`), `pmass.inc` (`:2973`), `ngraphs.inc` (`:2977`).
- `matrix.ps` EPS diagram (`:2982`) unless `output_options['noeps']=='True'` (eps-jpeg-two-gates.md).
- `standalone_msP` adds `configs_production.inc`, `props_production.inc`, `nexternal_prod.inc`;
  `standalone_msF` adds `helamp.inc`.
Files SYMLINKED from parent SubProcesses (`:2994-3006`): `check_sa.f`, `coupl.inc`, and
`makefile` -> `../makefileP`. EXCEPTION: when `--prefix` is set, `check_sa.f` is COPIED (not
linked) with `smatrix`→`<prefix>smatrix` regex-substituted (`:2996-3002`).

## check_sa.f (`template_files/check_sa.f`) — the standalone driver
Copied by SA copy_template only if `format=='standalone'` (`:2543`). It `call setpara('param_card.dat')`
then `CALL SMATRIX(P,MATELEM)` — reads ONLY `Cards/param_card.dat`, hardcodes/reads-in momenta.
`make` builds it into the `check` executable.

## --prefix flag (`:2922-2933`, parsed in do_output)
`output standalone --prefix=int` → per-proc prefix `M<number>_` (`:2925`); `--prefix=proc` →
`shell_string` name (`:2927`); any other value raises. Setting `--prefix` populates
`self.prefix_info`, which switches finalize onto the multi-process f2py path (all_matrix2py)
instead of the single-process one. (do_output default is prefix ON for madevent; `--noprefix`
strips it — that's the aloha_prefix mdl_ concern, model-loader's, distinct from this SA `--prefix`.)

## f2py python wrappers — two mechanisms
### Single-process (no --prefix): `matrix2py.so` per P-dir
Emitted from `template_files/matrix_standalone_f2py.inc` into `f2py_matrix_wrapper.f`. f2py
exposes (name lowercased, `PY_` kept):
- `py_smatrixhel(P, HEL, ANS)` — |M|² at a single helicity config HEL.
- `py_smatrix(P)` → ANS — summed/avg over colors & helicities.
- `py_matrix(P, NHEL, IC)` → real*8 — |M|² no average/symmetry.
- `py_get_value(P, ALPHAS, NHEL)` → ANS (`:GET_value`) — the canonical single-process entry; NHEL selects
  a helicity, and the summing semantics of a sentinel NHEL live in the generated matrix.f
  (SMATRIX/MATRIX internals — helas-amplitude/color slices), not the wrapper.
- `py_initialisemodel(PATH)` → calls `setpara(PATH)` — read a param_card benchmark point.
- `py_is_born_hel_selected(HELID)`.
Built with `make matrix2py.so` (per-P makefile target, MENUM=2 → `matrix2py.so`).

### Multi-process (--prefix): `all_matrix2py.so` at SubProcesses level
finalize (`:2665-2669`) calls `write_f2py_splitter` → writes `all_matrix.f` + `f2py_wrapper.f`
(from `f2py_wrapper_all.inc` + `f2py_splitter.py`), plus `write_f2py_makefile`. The dispatcher
entry point:
`smatrixhel(PDGS, PROCID, NPDG, P, ALPHAS, SCALE2, NHEL, ANS)` — routes by matching PDGS to a
sub-process. `PROCID<=0` (`.le.0`) AUTO-SELECTS the process (`:2720` `procid.le.0.or.procid.eq.<pid>`).
Also `initialise(PATH)`, `change_para(NAME,VALUE)`, `update_all_coup()`, `get_pdg_order`,
`get_prefix`, and scale/asmz setters. (A widely-cited signature `smatrixhel(pdgs, proc_id, P, alphas, scale2, nhel)`
is right in spirit but the real signature interleaves NPDG and returns ANS as an OUT arg.)

## finalize (`:2634-2682`)
`compiler_choice` + `self.make()` (compiles the check exes + libs), writes
`Cards/proc_card_mg5.dat` from history, base `ProcessExporterFortran.finalize`, touches
`__init__.py` in dir + SubProcesses. If `prefix_info`: the multi-proc f2py splitter/makefile.
Else: appends an aggregate `all:` target to `SubProcesses/makefile` that builds every
`P*/matrix2py.so`. `create_MA5_cards` is overridden to a no-op for SA (`:2853`).

## Model files & param_card
`export_model_files` (`:2579`) copies `param_card.dat` into `Cards/` and rewrites check_sa.f's
`setpara('param_card.dat')` → `setpara('param_card.dat', .true.)`. Base (`:696-722`) also leaves
`Cards/param_card_default.dat`. Source/MODEL comes from `UFO_model_to_mg4` (convert_model,
finalize-and-model-conversion.md), same as madevent — the Fortran-model conversion is shared.

## Standalone caveats
- No αs RUNNING: couplings are computed once by `setpara` from the param_card (`aS` value);
  the SA driver has no PDF/scale evolution loop. User supplies αs (via `py_get_value` ALPHAS arg,
  or `set_asmz`/param_card).
- No PDF evaluation, no `run_card.dat`: SA copy_template writes no run_card; check_sa.f/SMATRIX
  read only `Cards/param_card.dat`. Flux/PDF/cuts are the caller's job.
- No madevent runtime: no proc_characteristics, no HTML/xsec pages, no grouping abstraction
  (SA P-dirs use raw shell_string names, and there's no SubProcessGroup merge).

## Cautions / corrections
- CORRECTION to a common write-up myth: the per-P `make` DEFAULT target is `check` (the first rule
  in `makefile_sa_f_sp` is `$(PROG): ... PROG=check`), NOT the f2py wrapper. The f2py
  `matrix2py.so` is a SEPARATE explicit target you must name (`make matrix2py.so`). Only the
  SubProcesses-level aggregate `all:` (non-prefix) or the f2py makefile (prefix) builds the .so.
- `sa_symmetry` (True for `standalone_msP/msF/rw`, `:9990`) makes generate_subprocess_directory
  skip symmetric permutations (`:2876-2898`) — a P-dir may be silently omitted if a permuted
  equivalent already exists.
- The C++ standalone path (`standalone_cpp`) is entirely different — see
  standalone-cpp-output-flow.md (UFOModelConverterCPP, CPPProcess API, no f2py).
