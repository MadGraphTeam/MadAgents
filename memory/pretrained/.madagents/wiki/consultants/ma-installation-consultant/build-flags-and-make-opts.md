---
description: make_opts build-flag defaults (FPE-trapping is NOT a MG5 default — it is a commented debug line), compiler-config-key writeback into make_opts headers, and this image's NLO overlay patch (v3.7.1).
---

# Build flags & make_opts (FPE-trap myth, compiler writeback)

## Where make_opts lives / is templated
- LO: `$MADGRAPH_INSTALL/Template/LO/Source/make_opts` (working copy) + `.make_opts` (pristine source-of-truth). `do_output`/startup copies `.make_opts`->`make_opts` when the working copy is missing or older (`madgraph_interface.py:3169-3175`); `install update` force-refreshes it (`:7327-7329`). Each generated process dir gets a COPY of this file at `<PROC>/Source/make_opts`.
- NLO: `$MADGRAPH_INSTALL/Template/NLO/Source/make_opts.inc` (no dot-variant).
- `find . -name 'make_opts*'`: only these two Templates + `vendor/StdHEP/src/make_opts`.

## FPE-trapping is NOT a MadGraph default
The common belief that "MadGraph ships strict FPE-trapping flags in make_opts; fix = remove `-ffpe-trap`" is BACKWARDS. In every shipped make_opts the `-ffpe-trap` line is **commented out**:
- LO `Template/LO/Source/make_opts:16-17` and `.make_opts:16-17`:
  - ACTIVE default: `FFLAGS= -w -fPIC` (line 16). Note `-w` actively **suppresses** all warnings — the opposite of strict.
  - COMMENTED: `#FFLAGS+= -g -fbounds-check -ffpe-trap=invalid,zero,overflow,underflow,denormal -Wall -fimplicit-none` (line 17).
- NLO `Template/NLO/Source/make_opts.inc:11-13`:
  - ACTIVE default: `FFLAGS = -O` (line 12).
  - COMMENTED: `#FFLAGS= -O -w` (line 11) AND `#FFLAGS+= -g -fbounds-check -ffpe-trap=... -Wall` (line 13).

So a SIGFPE from a default build is NOT caused by MG5's own flags — nothing in the stock build traps IEEE_DIVIDE_BY_ZERO/IEEE_INVALID. FPE-trapping only appears if a USER (or a site overlay) uncomments line 17/13, or exports `FFLAGS` with `-ffpe-trap` in the environment (the `ifeq ($(origin FFLAGS),undefined)` guard at LO:15 / NLO:10 means an env-set `FFLAGS` REPLACES the default entirely). The "remove `-ffpe-trap` from make_opts" fix only applies to the user-added case; on a stock tree there is nothing to remove.

## Compiler config keys -> make_opts header writeback
`input/mg5_configuration.txt` keys, all default `None` (commented):
- `fortran_compiler` (`:38`), `f2py_compiler_py2` (`:39`), `f2py_compiler_py3` (`:40`), `cpp_compiler` (`:46`).
When set (or auto-detected), they are written into the make_opts **header block** (the lines above `#end_of_make_opts_variables`), NOT into FFLAGS:
- `export_v4.py:2398-2420` `replace_make_opt_f_compiler` -> `DEFAULT_F_COMPILER` + `DEFAULT_F2PY_COMPILER` via `CommonRunCmd.update_make_opts_full`.
- `export_v4.py:2422-2456` `replace_make_opt_c_compiler` -> `DEFAULT_CPP_COMPILER` + `MACFLAG`/`STDLIB`/`STDLIB_FLAG` (clang/libc++ detection).
- `misc.py:639-642` `mod_compilator` line-rewrites `FC=`/`CXX=` and `DEFAULT_F_COMPILER`/`DEFAULT_CPP_COMPILER` across makefiles in a dir.
Because every process-dir make_opts is a copy of the Template, setting `fortran_compiler`/`cpp_compiler` in the global config propagates the SAME compiler to all generated dirs at output — this is the source basis for the "recompile all deps with the same compiler" fix for compiler-mismatch crashes.

## Bundled vs optional reduction libs (cross-ref vendor page)
- BUNDLED as pre-extracted source trees in `vendor/`: `CutTools/`, `IREGI/` (built in place; not `install`-fetched). See `vendor-and-offline-install.md`.
- OPTIONAL (advanced_install targets `collier`/`ninja`/`oneloop`, `_advanced_install_opts` `madgraph_interface.py:3007`): vendor also ships `collier.tar.gz`/`ninja.tar.gz`/`oneloop.tar.gz` for the OFFLINE (`'local'`) install path. GoSam/golem95 is a separate built-in (`Golem95`). Whether any of these are *already built* under `HEPTools/` is install-STATE that drifts — never cache it; check live with `ls $MADGRAPH_INSTALL/HEPTools/lib/lib{ninja,collier,avh_olo}.*` at use time.
So "CutTools+IREGI bundled; Ninja/Collier/GoSam optional" is CORRECT.

## Cautions
- ENVIRONMENT-SPECIFIC OVERLAY PATCH (this image, NOT stock MG5): `Template/NLO/Source/make_opts.inc` has been patched to add `FFLAGS+= -mcmodel=medium` (`:63`) and `LDFLAGS=... -Wl,--no-relax -mcmodel=medium` (`:77`), with in-file comments citing CutTools `libcts.a` GOTPCREL relocations and high-multiplicity NLO (pp->4t) COMMON-block addressing, "see CLAUDE.md". A vanilla 3.7.1 NLO make_opts.inc does NOT carry these. If a build/link claim hinges on NLO flags, read this file live — it is overlay-modified here.
- The `-ffpe-trap` commented lines are IDENTICAL text in LO make_opts and .make_opts; a user who edits the working `make_opts` but not `.make_opts` will have their edit reverted on the next `install update` / older-mtime refresh (`:7327-7329`, `:3174`). Edit both, or set `FFLAGS` in the environment.
- CAUTION (runtime/version, not source-decidable): whether a specific COLLIER/CutTools/IREGI intermediate FPE actually becomes a fatal SIGFPE depends on the compiler, the env `FFLAGS`, and library version — a runtime/probe question, not answerable from the make_opts template alone.
