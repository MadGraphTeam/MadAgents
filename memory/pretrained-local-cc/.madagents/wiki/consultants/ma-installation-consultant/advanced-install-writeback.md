---
description: advanced_install post-install config writeback per tool, chained dependency installs, HEPToolInstaller exit-code contract, env-var advisory (v3.7.1).
---

# advanced_install post-install: writeback, chained installs, exit-code contract

All in `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, in `advanced_install` (`:6115`). Complements `vendor-and-offline-install.md` (which owns the HEPToolsInstaller tarball-fetch / offline mechanics); THIS page owns what happens *after* `HEPToolInstaller.py` returns.

## config_file target (`:6189-6203`)
- Default `heptools_install_dir == './HEPTools'` → `prefix = $MG5DIR/HEPTools`, **`config_file = ''`** → `save options <opt>` writes to the standard `input/mg5_configuration.txt`.
- Custom `heptools_install_dir` set → `prefix = that dir`, `config_file = <config_dir>/mg5_configuration.txt` (legacy `~/.mg5` or `$XDG_CONFIG_HOME` — see vendor page). So a custom install dir redirects ALL the writebacks below to that config file, not the in-tree one.

## Pre-install tool-specific option assembly (`:6206-6304`)
- **mg5amc_py8_interface** `:6206`: warns if `gnuplot` missing (merging plots); appends `--with_pythia8=<abspath pythia8_path>` if set.
- **madanalysis5 / rivet** `:6219`: append `--mg5_path=$MG5DIR`; auto-add `--with_fastjet=<fastjet-config>` if found (madanalysis5 falls back to bare `--with_fastjet`).
- **madanalysis5** `:6229`: if `delphes_path` is a real dir, append `--with_delphes3=<that dir>`.
- **pythia8 / eMELA** `:6235`: LHAPDF dependency resolution. Probes `lhapdf-config --version` (must be 5 or 6 else InvalidCmd). If absent → ask y/n to auto-install lhapdf6 (recursive `advanced_install('lhapdf6')`); pass `--with_lhapdf{5,6}=<path|OFF>`. `--force` forced last, `--mg5_path` appended.

## Exit-code contract from HEPToolInstaller.py (`:6305-6349`)
`return_code = misc.call([python, HEPToolInstaller.py, tool, --prefix=..., ...])`:
- **0 or 11** → success ("%s successfully installed in %s"). For plugins, "installed in PLUGIN directory."
- **66** → already installed → ask y/n overwrite (default y); on y recurse with `add_options+['--force']`; on n abort. `:6324-6334`.
- **anything else** → failure path `:6335-6349`. For madanalysis5 (no `--update`/`--no_MA5_further_install`): under `not __debug__` (default release) auto-reinstalls with `--no_MA5_further_install --no_root_in_MA5 --force` (see `debug-flag-release-behavior.md` site 3); else `logger.critical` suggestion only. Then `raise InvalidCmd("Installation of %s failed.")`.
- madanalysis5 success with no `--with_/--veto_/--update` opt prints the "install MadAnalysis5 --with_delphes --update" recasting hint. `:6315-6320`.

## Post-install config writeback per tool (`:6351-6434`)
Each writes `self.options[...]` then `save options ... config_file`:
- **pythia8** → `pythia8_path = prefix/pythia8`, then **CHAINED**: auto-reinstalls `mg5amc_py8_interface` with `--force`. `:6352-6358`.
- **lhapdf6** → sets BOTH `lhapdf_py3 = prefix/lhapdf6_py3/bin/lhapdf-config` AND `lhapdf = lhapdf_py3`. `:6359-6362`.
- **lhapdf5** → `lhapdf = prefix/lhapdf5/bin/lhapdf-config`. **eMELA** → `eMELA = prefix/bin/eMELA-config`.
- **madanalysis5** → `madanalysis5_path = prefix/madanalysis5/madanalysis5`.
- **mg5amc_py8_interface** → `mg5amc_py8_interface_path = prefix/MG5aMC_PY8_interface` (and backfills `pythia8_path` if empty).
- **collier** → `collier = prefix/lib`. **fastjet** → `fastjet = prefix/fastjet/bin/fastjet-config`.
- **ninja** → quad-prec check (`misc.get_ninja_quad_prec_support`); warns + advises reinstall with a quad-capable cpp compiler if absent; sets `ninja = prefix/lib`. `:6382-6393`.
- **contur / rivet** → set own `<tool>_path = prefix/<tool>`, plus conditionally `yoda_path`, `rivet_path` (contur only), `fastjet`, `hepmc_path` — each ONLY if that subdir exists in prefix. `:6396-6428`.
- **Generic fallback** `:6433`: any tool whose `<tool>_path` key exists in options → `prefix/<tool>`; else `logger.warning("path not saved for %s")`. So e.g. zlib/boost/cmake/hepmc3 fall through this generic branch (or get no path).

## Env-var advisory (`:6440-6480`)
After writeback, checks whether `HEPTools/{lib,bin,include}` are on `LD_LIBRARY_PATH` (`DYLD_` on darwin) / `PATH`; if not, composes a shell-appropriate (`bash`->`.bashrc` / `tcsh`->`.cshrc`) `export`/`setenv` line. CAUTION: emitted at **`logger.debug`**, so INVISIBLE at the default INFO log level — a user relying on stdout won't see the "add these to your env" advice. The runtime risk (a system copy of the tool shadowing the freshly installed one) is real but the warning is silent by default.

## Cautions / chains to remember
- Installing **pythia8 always drags in a fresh mg5amc_py8_interface** (`--force`) — you cannot install pythia8 alone via this path.
- Installing **pythia8 or eMELA may silently trigger an lhapdf6 install** if LHAPDF is absent and the user answers default-y.
- The writeback target is the in-tree `input/mg5_configuration.txt` ONLY when `heptools_install_dir` is the default; a custom dir redirects it.

## Gaps
- HEPToolInstaller.py's own internal logic (what it fetches, how it returns 11 vs 0 vs 66) lives in `HEPTools/HEPToolsInstallers/HEPToolInstaller.py`, refreshed/downloaded per call — the *meaning* of the codes is consumed here, but the *production* of them is in that (externally-refreshed) installer script. The 11/66 specific semantics are not defined in madgraph_interface.py.
