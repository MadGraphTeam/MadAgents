---
description: The output_dependencies triad (internal/external/environment_paths) — uniform copy-in / vendor-compile-once / system-find-or-raise shape across every NLO-export library link (CutTools, StdHEP, TIR), with a per-library failure-handling asymmetry.
---

# output_dependencies link-mode triad (v3.7.1)

## The principle
Every external/reduction library the NLO exporter links into the process dir is wired through the SAME three-mode switch on `mg5options['output_dependencies']` (alias `self.dependencies`). The three modes have a uniform *shape*; the failure handling differs per library. Knowing the shape lets you predict the layout for ANY linked library (CutTools, StdHEP, TIR libs pjfry/ninja/golem/samurai/collier, IREGI) — more cases than any single instance page covers.

The three modes:
- **internal** — copytree the library SOURCE into the process dir's `Source/<Lib>`, compile it in-tree (recompiled with the rest), link the built libs into `lib/` by relative path. Self-contained / relocatable.
- **external** — compile the library ONCE in its vendor location (`self.cuttools_dir`, `MG5DIR/vendor/StdHEP`, ...) if the lib is absent, then link the prebuilt lib into `lib/` by ABSOLUTE path. Shared across all process dirs; breaks if the vendor disk isn't mounted on worker nodes.
- **environment_paths** — `misc.which_lib(<lib>)` to find it on the system; link the found abspath, or RAISE `InvalidCmd` if not found. No compile.
- Any other value → `MadGraph5Error`.

## Instances (source-confirmed)
- **link_CutTools** (`loop_exporters.py:115`): internal copytree→`Source/CutTools` + in-tree compile (`:145`); external vendor-compile-once, raises `MadGraph5Error` if compile fails (`:153`-167); environment_paths `which_lib('libcts.a'/'mpmodule.mod')` find-or-raise `InvalidCmd` (`:175`). Plus a pre-branch: `heptools_install_dir` + external uses a pre-compiled CutTools and returns early (`:120`).
- **StdHEP in finalize** (`export_fks.py:981`/`1011`/`1028`): external compile-once in `MG5DIR/vendor/StdHEP` gated on a `fail` sentinel (`:981`); internal copytree→`Source/StdHEP` + `make clean` (`:1011`); environment_paths `which_lib('libstdhep.a'/'libFmcfio.a')` find-or-raise `InvalidCmd` (`:1028`). (finalize-nlo-process-dir.md.)
- **TIR libs** (optimized `copy_fkstemplate`, `link_TIR` `loop_exporters.py:1910`): linked per `self.all_tir` under the same dependency mode; IREGI is self-contained, others link `-L/-l`; ninja additionally needs `libavh_olo`. (copy-fkstemplate-and-scaffolding.md.)

## TIR has a CRITICAL twist on the triad (link_TIR loop_exporters.py:1910)
The triad shape holds but TIR splits libraries into two classes, and `internal` mode behaves NON-uniformly:
- **Non-self-contained TIR libs** = `pjfry`, `golem`, `samurai`, `ninja`, `collier` (`:1914`). These are NOT distributed with MG5.
  - `internal` mode: **forcibly DISABLED** — `tir_available_dict[lib]=False` + info log "cannot be employed because it is not distributed with the MG5_aMC code so that it cannot be copied locally" (`:1951`-1957). So `output_dependencies=internal` means NONE of pjfry/golem/samurai/ninja/collier are available, regardless of install. Only CutTools + IREGI survive internal mode.
  - `external`/`environment_paths`: link the prebuilt lib by abspath; for ninja/samurai also a VERSION/AUTHORS sibling-file version check warns if too old (`:1927`-1940).
- **Self-contained (IREGI)** — the only TIR lib MG5 can build itself (`:1958`):
  - `internal`: copytree `<libpath>/..` → process-dir `Source/IREGI`, fix the compiler in `makefile_ML5_lib`, link `libiregi.a` (`:1960`-1975).
  - `external`: compile-once in the vendor IREGI dir if `libiregi.a` absent ("Compiling IREGI. This has to be done only once") with a `heptools_install_dir` pre-compiled shortcut (`:1982`-1989); on compile failure → WARN + `tir_available_dict=False` (soft, like StdHEP — NOT a hard raise) (`:2006`-2011).
  - `environment_paths`: `which_lib(libname)`; found → link abspath + available=True; not found → WARN + available=False (soft, NOT InvalidCmd) (`:2016`-2033).

### Failure-handling: TIR is SOFT everywhere (vs CutTools hard / StdHEP soft)
`link_TIR` never RAISES on a missing/failed lib — every miss sets `tir_available_dict[lib]=False` and warns/infos, then continues. The warning only appears when an EXPLICIT wrong path was given in mg5_configuration.txt (`:1920`-1923, `:1944`-1947); a simply-absent lib downgrades silently. So TIR libs are the softest-failing of the three triad instances: CutTools external RAISES, StdHEP external soft-fails-with-sentinel, TIR always soft-fails-into-unavailable. This is WHY GOLEM/COLLIER `.f` interface files are conditional on `tir_available_dict` at output time (loop-matrix-writer page) — a missing TIR lib silently yields no interface file rather than aborting.

## The failure-handling asymmetry (the trap)
The **external** branch does NOT fail uniformly:
- CutTools external: compile failure → `raise MadGraph5Error("CutTools could not be correctly compiled")` (`loop_exporters.py:167`). Hard abort.
- StdHEP external: compile failure → writes a `vendor/StdHEP/fail` sentinel + WARNS ("forbids to run NLO+PS with PY6 and Herwig6"), continues. Soft. A stale `fail` sentinel then silently skips re-compile forever. (finalize-nlo-process-dir.md.)
- environment_paths is the only mode that uniformly ABORTS (InvalidCmd) on a missing lib across both CutTools and StdHEP.

So do not assume "external mode fails the same way" — CutTools aborts, StdHEP degrades. Verify per library.

## The move
A dispatch about where/how a given library ends up in the NLO dir → identify the `output_dependencies` value for THIS run, then apply the triad shape. For failure behavior, do NOT generalize across libraries — read the specific link_* / finalize branch (CutTools raises, StdHEP soft-fails with a sentinel).

## Instances generalized (kept)
- finalize-nlo-process-dir.md — StdHEP 3-branch + fail-sentinel detail (kept).
- copy-fkstemplate-and-scaffolding.md — link_CutTools / link_TIR per-mode detail (kept).
