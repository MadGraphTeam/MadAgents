---
description: Rivet/YODA/Contur install + *_path config wiring — advanced_install set, what each install saves, validity checks, and the as-shipped (uninstalled) state in this v3.7.1 image.
---

# Install & config wiring (rivet/yoda/contur paths)

## advanced_install set (madgraph_interface.py:3007-3010)
`_advanced_install_opts` is registered at `madgraph_interface.py:3007-3010` — read the full list fresh there (drift-prone enumeration; this same list was found short by 4 entries in a prior walk). My-slice-relevant members as of this walk: `rivet`, `yoda`, `contur`, `fastjet`, `fjcontrib` (3009) plus `hepmc` (3008) and `hepmc3` (3010) — Rivet's HepMC dependency can be either. `_install_opts.extend(_advanced_install_opts)` at 3012, so each is reachable via `install <tool>`.
- For `madanalysis5` and `rivet`, advanced_install adds `--mg5_path=` and, unless the caller already passed `--with_fastjet`/`--veto_fastjet`, auto-adds `--with_fastjet=<fastjet-config>` IF `misc.which(self.options['fastjet'])` resolves (6221-6228) — Rivet needs FastJet. CAUTION: the bare `--with_fastjet` fallback (when fastjet-config does NOT resolve) is `madanalysis5`-ONLY (6227-6228); for `rivet` with an unresolvable fastjet-config, NO fastjet option is appended.

## What each install saves (6394-6426)
- `install contur` (6394-6411): saves contur_path; if `<prefix>/yoda` exists saves yoda_path; if `<prefix>/rivet` saves rivet_path; if `<prefix>/fastjet` sets `fastjet=<prefix>/fastjet/bin/fastjet-config`; if `<prefix>/hepmc` saves hepmc_path. So `install contur` pulls the whole rivet+yoda+hepmc+fastjet stack under one prefix.
- `install rivet` (6412-6426): saves rivet_path; conditionally yoda_path, fastjet, hepmc_path (same prefix probing). Does NOT save contur_path.

## Default config (uninstalled)
- `madgraph_interface.py:3050`: default `'rivet_path' : './HEPTools/rivet'` (relative placeholder until install resolves it).
- After install, `save options` writes the absolute path into `input/mg5_configuration.txt` (6410, 6425).

## Validity check before use
- `madevent_interface.py:2159-2162`: a configured rivet_path is rejected (logged "No valid rivet path found") unless `<path>/bin/rivet` exists.
- `common_run_interface.py:5340-5343`: `has_rivet` gate — if `get_path('rivet', cards)` is falsy, the rivet card init returns [] (no rivet menu/shortcut).

## upgrade_tag (which stage triggers rivet) (madevent_interface.py:6387-6396)
`rivet` is in the upgrade list for `parton` and `pythia8` levels (6387, 6389) and keyed standalone as `'rivet':['rivet']` (6396). NOT in the `pythia` (PY6) level. (File is madevent_interface.py — the install save blocks at the same 6394-6426 line range live in madgraph_interface.py; do not conflate.)

## As-shipped state in THIS image (v3.7.1, $MADGRAPH_INSTALL)
- `HEPTools/` contains: bin, collier, fastjet, hepmc, HEPToolsInstallers, include, lhapdf6_py3, lib, MG5aMC_PY8_interface, ninja, oneloop, pythia8, zlib. NO rivet/yoda/contur dirs (the load-bearing fact).
- `input/mg5_configuration.txt` has NO rivet_path/yoda_path/contur_path lines; `hepmc_path = $MADGRAPH_INSTALL/None` (placeholder).
- => Rivet is NOT installed here. Any Rivet/Contur task requires `install rivet` (or `install contur`) first. do_rivet would fail at the fastjet `--prefix` / rivet_path env steps if invoked without install. Caution, not a runtime claim.
