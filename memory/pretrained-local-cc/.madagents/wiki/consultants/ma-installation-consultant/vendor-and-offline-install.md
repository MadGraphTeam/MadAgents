---
description: $MADGRAPH_INSTALL/vendor inventory, the offline reduction-library installer path, and advanced_install/HEPToolsInstaller mechanics (v3.7.1).
---

# Vendor tarballs & offline install

## vendor inventory (`$MADGRAPH_INSTALL/vendor/`, read live)
Bundled tarballs: `collier.tar.gz`, `ninja.tar.gz`, `oneloop.tar.gz`, `SMWidth.tar.gz`, `OfflineHEPToolsInstaller.tar.gz`.
Pre-extracted source trees: `CutTools/` (DOC, examples, includects, src, makefile), `IREGI/src/`, `StdHEP/`, `ply/`, `DiscreteSampler/`, `eepdfgrid/`, `SudGen/`, plus `__init__.py` + `__pycache__`. NON-OBVIOUS: these ARE populated source trees (`.f` source + makefiles; SudGen is the largest, multi-MB in this image), NOT empty. The `0` shown by `ls -la` for these dirs is the directory inode's own size field, not emptiness — `ls -la` size 0 does NOT mean empty placeholder. Verify contents live with `ls -A <dir>` / `du -sh <dir>`, never infer from the `ls -la` size column.

## install looptools / reduction-library offline path
`install_reduction_library(force=False)` at `$MADGRAPH_INSTALL/madgraph/interface/loop_interface.py:511`. Reached via `do_install('looptools')` (force=True, `madgraph_interface.py:6542`) or auto-triggered on first loop-ME output.
- Early return `:517` when not forced and (`ninja` option None OR `libninja.a` already present).
- Skips during test runs (`test_manager.py` in argv) `:521-523`.
- Asks via `AskLoopInstaller` (timeout 300s) `:527`. OWNERSHIP: the menu class that PRODUCES the code dict AND the full per-key dispatch table (cuttools/iregi path-copy, `install`, `off`, resume-path) live on `reduction-library-install-menu.md` (`:530-605`). THIS page owns ONLY the `'local'` / offline-vendor-tarball branch, because that is the one branch whose mechanics are vendor-tarball-specific:
  - value `'local'` → OFFLINE install: `do_install(key, paths={'HEPToolsInstaller': vendor/OfflineHEPToolsInstaller.tar.gz}, additional_options=['--ninja_tarball=vendor/<key>.tar.gz'(, '--oneloop_tarball=vendor/oneloop.tar.gz' for ninja)])`. `:568-589`. The tarball flag is literally `--ninja_tarball=` even when `key=='collier'` (read generically by OfflineHEPToolsInstaller). On failure: warns and `set <key> ''` + saves (disables the tool). NOTE: `'local'` is never AUTO-selected (online is hardcoded True in the menu) — it is user-opt-in only; see `reduction-library-install-menu.md`.

KEY: passing `paths=` to `do_install` bypasses the network entirely (`if paths: path = paths` at `madgraph_interface.py:6563-6564`), so the offline ninja/collier install reads tarballs straight from `vendor/`.

## advanced_install / HEPToolsInstaller `madgraph_interface.py:6115`
- Refreshes `$MG5DIR/HEPTools/HEPToolsInstallers` each call; downloads installer tarball from `path['HEPToolsInstaller']` via `misc.wget` (or `shutil.copyfile` for a local path; `//` heuristic at `:6141`). `--local` uses a sibling `../HEPToolsInstallers` dir (debug only). `:6126-6162`.
- Name remap `lhapdf6_py3 -> lhapdf6` `:6165`.
- Compiler options from `options['cpp_compiler']`/`['fortran_compiler']`; `--cpp_standard_lib` always set. `:6171-6187`.
- The `heptools_install_dir` prefix/config-file logic (`:6189-6203`) and the per-tool pre-install option assembly (`:6206-6304`: mg5amc_py8_interface/madanalysis5/rivet/pythia8-eMELA-lhapdf) are owned by `advanced-install-writeback.md` — this page owns only the vendor-tarball *fetch* mechanics above; the post-fetch flow is there.

## Cautions
- CutTools/IREGI rebuild on `install update` if their `.a` already exists (`madgraph_interface.py:7127-7130`).
- DiscreteSampler/eepdfgrid/SudGen/ply LOOK 0-byte under `ls -la` (directory inode size) but are populated source trees — verify with `ls -A`/`du -sh`, not the `ls -la` size column.
- MISLABELED TARBALL (this image, probe-confirmed): `vendor/SMWidth.tar.gz` is byte-identical to `vendor/ninja.tar.gz` (both md5 `830360426c4ed37bbed08f9eb5ec8767`, 595807 bytes) and unpacks to `ninja-1.2.0/` — it does NOT contain SMWidth source. An offline SMWidth install reading that tarball would get ninja contents. Verify a vendor tarball's actual contents (`tar -tzf`) before relying on it; don't trust the filename. (Real SMWidth source ships inside the MG5 tree, not via this vendor tarball.)
