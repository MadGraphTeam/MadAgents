---
description: do_install command flow — citation print, server fetch, advanced vs built-in dispatch, plugin handling, post-install config writeback (v3.7.1).
---

# do_install flow

`do_install(self, line, paths=None, additional_options=[])` at `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:6518`.

## Sequence
1. `check_install(args)` (`:1325-1380`) validates the target and splits options. Web variant `:2019` raises `WebRestriction` (only relevant in online/cluster mode). `:6531`.
   - Option splitting `:1337-1356`: for `update`, `=`-form args go to `update_options`; for any other target, every extra arg (incl. `--source=`, `--force`, `--keep_source`) goes verbatim to `options_for_HEPToolsInstaller`. Then `args` is truncated to `args[:1]` (target only). (The advertised-vs-completed-vs-parsed flag disagreement — which flags actually work — is on `install-flag-surface.md`.)
   - Target validity `:1358-1361`: must be in `_install_opts + hidden_prog + _advanced_install_opts`, else `InvalidCmd('Not recognize program ...')` — UNLESS it `startswith('td')` (the `td` plotting tool bypasses the set check).
   - HARD ROOT PRECONDITION `:1363-1378`: for `ExRootAnalysis`/`Delphes`/`Delphes2`, raises `InvalidCmd` (before any download) if `misc.which('root')` is falsy ("you need to install Root ... first") OR if `ROOTSYS` is not in `os.environ` ("environment variable ROOTSYS is not configured"). Plain `Delphes3` is NOT in this list (the `Delphes`->`Delphes3` rename happens later at `:6620`, after check_install). NB: in this ROOT is present and `ROOTSYS` is exported so the gate passes here — it bites only on images without ROOT.
   - PROBE-CONFIRMED (direct call to `check_install`): `''`->InvalidCmd "install command require at least one argument"; `notarealtool`->InvalidCmd "Not recognize program notarealtool"; `Delphes`/`pythia8`->OK; `tdfoo`->OK (the `startswith('td')` bypass at `:1359` lets any `td*` through the set check).
2. Download program selection: `program = "curl"` if `sys.platform=="darwin"` else `"wget"`. `:6533-6536`.
3. Special commands dispatch:
   - `update` → `install_update(['update']+install_options['update_options'], wget=program)` then return. `:6539`.
   - `looptools` → `install_reduction_library(force=True)` then return. `:6542`. (Defined in `loop_interface.py:511`, NOT in madgraph_interface.)
4. Citation advertisement: if `args[0] in install_ad`, prints `"You are installing '<tool>', please cite ref(s): <refs>."` in green. `:6552-6558`. Earlier block-style print is commented out.
5. Server fetch of `package_info.dat` (see `source-server-selection.md`); populates `path[tool] = url`. `:6560-6612`.
6. `Delphes` → `Delphes3` rename. `:6620`. Name remap via `install_name` dict `:6508-6516,6624-6628`.
7. Advanced dispatch: if `args[0] in _advanced_install_opts`, append `--mg5amc_py8_interface_tarball=`, HEPToolsInstaller options, `--logging=`, then `return self.advanced_install(name, path['HEPToolsInstaller'], ...)`. `:6635-6650`.
8. Outdated-package warning for `Delphes2`/`pythia-pgs` (substitution dict → suggests Delphes/pythia8); asks y/n, default n. `:6658-6665`.
9. `rm -rf $MG5DIR/<name>` then download+untar tarball via `misc.wget` + `tar -xzpf`. `:6668-6698`.
10. `RunningCoupling` → installed name becomes `Template/Running`. `:6700-6701`.
11. Per-tool build (see "Built-in build steps" below): `post_install_<name>` hook if present `:6713`; else compile. Golem95/QCDLoop use `./configure` + `make install` `:6754-6767,6871-6887`. Delphes3 patches Makefile rpath from `$ROOTSYS` `:6770-6779`. SysCalc links lhapdf `:6782-6797`.
   - POST_INSTALL HOOK SHORT-CIRCUITS (`:6713-6714`): the hook is dispatched generically via `hasattr(self,'post_install_%s'%name)` / `getattr(...)()` and its result is **`return`ed** — so when a hook matches, the ENTIRE remaining built-in block (compile at `:6716`, FC resolution, Delphes/SysCalc patching, the `:6971-6992` config writeback) is SKIPPED. `RunningCoupling` is the ONLY `post_install_*` method in the tree (`:7737-7739`): it just `shutil.move`s `$MG5DIR/RunningCoupling` → `$MG5DIR/Template/Running` and returns. So `install RunningCoupling` does NOT compile and does NOT write any config key — it is a pure untar+move. `name` for the hash comes from `install_name[args[0]]` with KeyError→`args[0]` fallback (`:6624-6628`); `RunningCoupling` is absent from `install_name`, so `name='RunningCoupling'` and the hook matches.
12. Plugin tools (`name in install_plugin`): no compile; `shutil.move` into `PLUGIN/<name>`, import to read `new_interface/new_output/latest_validated_version/minimal_/maximal_mg5amcnlo_version`; if py3 import fails, warns "Plugin not python3 compatible! It will run with python2" and falls back to text scan. `:6802-6860`. If `new_interface`, writes a launcher `bin/<name>.py`.
13. Post-install config writeback: `options_name` map (Delphes→delphes_path, ExRootAnalysis→exrootanalysis_path, MadAnalysis→madanalysis_path, SysCalc→syscalc_path, pythia-pgs→pythia-pgs_path, Golem95→golem); `save options <opt>`. `:6971-6988`.

## Target sets (read live — drift across versions)
- `_install_opts` `:3002-3004`: Delphes, MadAnalysis4, ExRootAnalysis, update, Golem95, QCDLoop, maddm, maddump, looptools, MadSTR, RunningCoupling.
- `_advanced_install_opts` `:3007-3010` (HEPToolsInstaller-managed): pythia8, zlib, boost, lhapdf6, lhapdf5, collier, hepmc, mg5amc_py8_interface, ninja, oneloop, MadAnalysis5, yoda, rivet, fastjet, fjcontrib, contur, cmake, eMELA, cudacpp, hepmc3, pythia8_hepmc3, DMTCP. Extended into `_install_opts` at `:3012`.
- `install_plugin` `:6484`: maddm, maddump, MadSTR, cudacpp.
- `install_ad` (citation map) `:6485-6503`.
- `hidden_prog` (accepted but not advertised) `:1331`: Delphes2, pythia-pgs, SysCalc.

## Built-in build steps (`:6700-6992`)
- **Directory fuzzy-rename** `:6703-6710`: if `$MG5DIR/<name>` is absent after untar, finds a dir whose lowercased name `startswith(name.lower())` and not `.gz`, then `files.mv` it to `<name>`. Lets a tarball whose top dir is versioned (e.g. `Delphes-3.x.y`) still land at `Delphes`.
- **FC resolution** `:6731-6753`: if `FC` env unset, picks `options['fortran_compiler']` else `gfortran` else `g77` else raises "Require g77 or Gfortran". For pythia-pgs/MadAnalysis(4) it rewrites `FC=...` in `make_opts`/`makefile`.
- **pythia-pgs Mac 64-bit** `:6720-6727`: rewrites `MBITS=32`->`MBITS=64` in `src/make_opts` and creates `libraries/pylib/lib`.
- **golem95** (`name=='golem95'`) `:6755` and **QCDLoop** `:6761` run `./configure --prefix=$MG5DIR/<name> FC=...` then `make install` (`:6873-6875`, `misc.compile(['install'])`).
- **Delphes3** `:6768`: Makefile `DELPHES_LIBS` rpath appended with `$ROOTSYS/lib`. **SysCalc** `:6781`: runs `lhapdf --libdir`, prepends to `LD_LIBRARY_PATH`/`PATH`; raises if `lhapdf` option empty; adds `CXX=<cpp_compiler>`.
- **Compile dispatch** `:6845-6890`: two branches by `logger.level <= INFO`. INFO branch uses `misc.call(['make'...])` (output shown); quieter branch uses `self.compile`/`misc.compile`. golem95/QCDLoop → `make install`; pythia-pgs → builds `libraries/pylib` first ("SLC6 needs this first").
- **pythia-pgs second-underscore retry** `:6904-6917`: on FIRST compile failure, strips `-fno-second-underscore` lines from two stdhep arch files (`mcfio/arch_mcfio`, `src/stdhep_Arch`) and recompiles before declaring success/failure.
- **MadAnalysis(4) -> td + ghostscript** `:6913-6948`: only when `args[0]=='MadAnalysis'`. Creates `$MG5DIR/td`, downloads `td` per platform/bitness: darwin -> `home.fnal.gov/~parke/TD/td_mac_intel64.tar.gz`; Linux 64-bit -> `home.fnal.gov/~parke/TD/td_linux_64bit.tar.gz`; Linux 32-bit -> `madgraph.phys.ucl.ac.be/Downloads/td`. chmod 0775, sets `options['td_path']=$MG5DIR/td`. Warns if `gs` (ghostscript) absent (no jpg/html plots). These td URLs are EXTERNAL (FNAL/UCL), not from `package_info.dat`.
- **Delphes2/3 card writeback** `:6950-6969`: Delphes2 rewrites `DetectorCard.dat` -> `Template/Common/Cards/delphes_card_default.dat`. Delphes3 copies `delphes_card_CMS.tcl`/`ATLAS.tcl` from `Delphes/cards` (fallback `Delphes/examples`) into `Template/Common/Cards/` as default/CMS/ATLAS cards; warns if neither pythia-pgs nor pythia8 linked.
- **Standalone `install td`**: `td` passes `check_install` via the `startswith('td')` bypass (`:1359`) but is NOT in `install_ad`/`install_plugin`/advanced sets, and the td-download block above runs ONLY for `args[0]=='MadAnalysis'`. So `install td` alone proceeds to the generic server fetch and needs a `td` entry in remote `package_info.dat` — a runtime/external answer (see `install-static-vs-runtime-boundary.md` case 1).

## Built-in config writeback subtlety (EXTENDED — `:6971-6992`)
`options_name` map writes back AFTER build. CAUTION: for non-golem tools (`:6986-6987`), it sets `options[opt] = options_configuration[opt]` — i.e. the **relative configured default** (`./Delphes`, `./MadAnalysis`, `./ExRootAnalysis`, `./SysCalc`, `./pythia-pgs` from `:3043-3056`), NOT an absolute install path — and ONLY if `options[opt]` currently differs from that default. Golem95 is the exception: `golem = $MG5DIR/<name>/lib` (absolute). So after `install Delphes` the config records `delphes_path = ./Delphes` (relative), resolved against `$MG5DIR` at use time. `td_path` default is `./td` (`:3053`).

## Cautions
- The `:6683` "Program not yet released" placeholder path is currently DORMANT. Check is `'xxx' in advertisements[name][0]` (lowercase, FIRST ref only). The only placeholder in `install_ad` is `mg5amc_py8_interface`'s SECOND ref `arXiv:XXXX.YYYYY` (`:6495`) — uppercase `XXXX`, second slot, AND mg5amc_py8_interface is an advanced target so it returns at `:6649` and never reaches `:6683`. So no current `install_ad` entry triggers this path; the mechanism exists for a future lowercase-`xxx` first-ref entry. Reaching `:6683` at all requires the tarball name to be absent from `path` after fetch WITH an explicit `--source` (else the other-mirror recursion at `:6672-6681` fires first).
- Built-in compile failure does NOT raise — logs `warning('Error detected during the compilation...')` and continues. `:6911`.
