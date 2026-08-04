---
description: input/mg5_configuration.txt tool-path key schema, the None-sentinel meaning, and how install writes paths back — active-vs-unset state is per-install, grep the live file (v3.7.1).
---

# mg5_configuration.txt tool paths

File: `$MADGRAPH_INSTALL/input/mg5_configuration.txt`. Commented (`#`) entries are unset/use-default; uncommented are active.

## Key schema (which tool-path keys the file carries)
`pythia8_path`, `mg5amc_py8_interface_path`, `hwpp_path`, `thepeg_path`, `hepmc_path`, `madanalysis5_path`, `delphes_path`, `rivet_path`, `lhapdf` (path to `lhapdf-config`, NOT a lib dir), plus compilers `fortran_compiler`/`cpp_compiler` and `auto_update` (days between auto-update checks). `rivet_path` may be absent from a given file — grep, don't assume it's present.

## Which are active vs unset is INSTALL-STATE — grep live, never cache
Whether any given key is uncommented (a real path) or carries the `<MG5DIR>/None` sentinel reflects **what has been installed in THIS install** and drifts as tools are added — it is an environment fact, not a standing truth. Do not read an "active/unset" verdict off this page. At use time:
```
grep -nE '^(pythia8_path|mg5amc_py8_interface_path|hwpp_path|thepeg_path|hepmc_path|madanalysis5_path|delphes_path|rivet_path|lhapdf)' \
  $MADGRAPH_INSTALL/input/mg5_configuration.txt
```
A line present + uncommented = active; a line resolving to `.../None` = the `None`-sentinel (tool NOT installed/linked — treat as unset, not a real path). Config-file line numbers also shift as entries are added — locate by grep, not by a cached `:NN`.

NB: how these entries are READ and resolved at startup (config-file precedence chain, `None`-sentinel → Python None, per-tool sentinel-file validation that silently resets a stale path to None, golem/samurai 'auto', generic do_set fallback) is on `mg5-configuration-read-resolve.md`. THIS page owns the entries + install writeback; that page owns the read/resolve.

## How install writes back
`do_install` post-install map `options_name` (`madgraph_interface.py:6971-6988`): Delphes->delphes_path, ExRootAnalysis->exrootanalysis_path, MadAnalysis->madanalysis_path, SysCalc->syscalc_path, pythia-pgs->pythia-pgs_path, Golem95->golem (set to `<name>/lib`). Writeback via `save options <opt>` only when the option changed from `options_configuration`.

Advanced-install tools written to `$MG5DIR/HEPTools/...` (or `heptools_install_dir` if set, with config writeback to `~/.mg5` or `$XDG_CONFIG_HOME` — see vendor-and-offline-install.md).

## Gaps
- `lhapdf` entry is the path to `lhapdf-config`, not a lib dir; consumers run it to get `--libdir`/`--prefix` at runtime.
