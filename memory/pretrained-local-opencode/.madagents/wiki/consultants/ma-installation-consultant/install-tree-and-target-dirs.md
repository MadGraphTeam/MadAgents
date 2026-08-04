---
description: Where installed tools land (advanced→HEPTools/, built-in→$MG5DIR/<name>), case-sensitivity of install tokens, and the full base install-tree top-level contents (v3.7.1).
---

# Install target directories, token case-sensitivity, base tree

Install-command tokens, HEPTools/ vs $MG5DIR target directories, and the base install-tree structure, from source + the live tree.

## Command tokens are CASE-SENSITIVE — FULL live sets (v3.7.1)
`check_install` target gate `madgraph_interface.py:1358-1361`: `if args[0] not in self._install_opts + hidden_prog + self._advanced_install_opts:` — a plain Python `in` membership test, NO `.lower()` normalization anywhere before it (the many `.lower()` calls nearby are for `set`/`check`/`display`, never the install target). So case is significant and the token must match a set entry exactly. The three accepted sets, verbatim from source:

- **`_advanced_install_opts` (HEPToolsInstaller-managed) `:3007-3010`** — full list, spelled exactly as shown:
  `pythia8`, `zlib`, `boost`, `lhapdf6`, `lhapdf5`, `collier`, `hepmc`, `mg5amc_py8_interface`, `ninja`, `oneloop`, `MadAnalysis5`, `yoda`, `rivet`, `fastjet`, `fjcontrib`, `contur`, `cmake`, `eMELA`, `cudacpp`, `hepmc3`, `pythia8_hepmc3`, `DMTCP`.
- **`_install_opts` (built-in) `:3002-3004`** — full list:
  `Delphes`, `MadAnalysis4`, `ExRootAnalysis`, `update`, `Golem95`, `QCDLoop`, `maddm`, `maddump`, `looptools`, `MadSTR`, `RunningCoupling`.
  Note `:3012` `_install_opts.extend(_advanced_install_opts)` — at runtime `_install_opts` already CONTAINS all advanced opts (so the `+ _advanced_install_opts` in the gate is redundant/doubled, harmless for membership).
- **`hidden_prog` `:1331`** — three undocumented-but-accepted tokens: `Delphes2`, `pythia-pgs`, `SysCalc`.
- Exact valid spellings: `install pythia8` OK, `install Delphes` OK, `install MadAnalysis5` OK, `install lhapdf6` OK. But `install delphes` / `install DELPHES` / `Pythia8` (wrong case) / `install lhapdf` (bare) / `install madanalysis5` (lowercase) → `InvalidCmd('Not recognize program …')`. There is NO `lhapdf` target (only `lhapdf6`/`lhapdf5`); `lhapdf` is only a *config key* for the lhapdf-config path.
- Sole exception to the exact-match rule: any token `startswith('td')` bypasses the set check `:1359`.

## No token is a command-level alias; two undergo INTERNAL name remaps
The user must type the exact token; `do_install` then remaps some tokens to a download/dispatch name (not user-visible, not an alternate accepted spelling):
- `Delphes` → `args[0]='Delphes3'` `:6620-6621` (tarball name) before the `install_name` lookup `:6625-6626`. User still types `Delphes`.
- `MadAnalysis4` → `'MadAnalysis'` `:6629-6630`. (`MadAnalysis5` is a DISTINCT advanced-set token — the two MA5/MA4 targets are separate.)
- `update` → `install_update` `:6539-6541`; `looptools` → `install_reduction_library(force=True)` `:6542-6544` (both short-circuit, never reach the advanced/built-in dispatch).
- `pythia8`, `lhapdf6`, `MadAnalysis5` reach the advanced branch `:6635`; no remap of the accepted spelling.
- Dead lowercase branch: `:6631-6633` remaps `['madstr','madSTR']→'MadSTR'`, but those lowercase forms fail the `:1358` gate first (only `MadSTR` is in the set) — unreachable via normal `do_install`.

## Delphes-specific gate: ROOT + ROOTSYS required BEFORE any download
After the `:1358` token gate, `check_install:1363` adds a hard prerequisite for the ROOT-dependent built-ins: `if args[0] in ["ExRootAnalysis", "Delphes", "Delphes2"]:` → requires `misc.which('root')` (else `InvalidCmd` telling user to install ROOT from root.cern.ch) AND `'ROOTSYS' in os.environ` (else `InvalidCmd` with the export-lines recipe). So `install Delphes` fails at parse-time with NO download attempt unless ROOT is on PATH and `ROOTSYS` is set. Delphes3 (the actual tarball, via `Delphes`→`Delphes3` remap) links against ROOT — this gate is why. Note the built-in `Delphes` also triggers a post-compile PY8-shower advisory (`:6969 logger.warning` "no parton-shower module installed/linked … install/link pythia8") but that is non-fatal.

## Delphes build mechanism (built-in path, Linux)
`install Delphes` (token in `_install_opts`, NOT advanced) does NOT use HEPToolsInstaller. `do_install`: `rm -rf $MG5DIR/Delphes` → `misc.wget(path['Delphes3'], 'Delphes.tgz')` (`:6690-6691`; `wget` on Linux, `curl` on Darwin) where the URL `path['Delphes3']` comes from the fetched us-server manifest (NOT `vendor/`) → `tar -xzpf` → `make` in place (`:6717`) → Delphes-specific Makefile library-link edit (`:6769-6779`) → copies `delphes_card_CMS.tcl`/`ATLAS.tcl` from `Delphes/cards|examples` into `Template/Common/Cards/delphes_card_*.dat` (`:6956-6966`) → writes `delphes_path=./Delphes` (`options_name:6972`). Compiles in place within the MG5 installation tree.

## Where tools land — TWO destinations, not one
- **Advanced (HEPTools-managed) targets → `$MG5DIR/HEPTools/`.** `advanced_install` sets `prefix = pjoin(MG5DIR,'HEPTools')` `:6202`; config keys point inside it: `pythia8_path=./HEPTools/pythia8`, `madanalysis5_path=./HEPTools/madanalysis5/madanalysis5`, `rivet_path=./HEPTools/rivet`, ninja/collier→`./HEPTools/lib`, `mg5amc_py8_interface_path=./HEPTools/MG5aMC_PY8_interface`, `heptools_install_dir=./HEPTools` (`:3043-3099`). The `HEPTools/` dir is CREATED on demand (`:6131-6132 os.mkdir` if absent), not shipped pristine.
- **Built-in targets → `$MG5DIR/<name>` directly, NOT HEPTools/.** `do_install` does `rm -rf $MG5DIR/<name>` then untars there (`:6668-6698`). So `install Delphes`→`$MG5DIR/Delphes`, config `delphes_path=./Delphes` (relative to $MG5DIR); Golem95→`$MG5DIR/Golem95`; ExRootAnalysis→`$MG5DIR/ExRootAnalysis`.
- **Key distinction:** "tools land in HEPTools/" holds only for advanced targets (pythia8/lhapdf6/MA5/rivet/hepmc/ninja/collier); built-in targets (Delphes/Golem95/ExRootAnalysis) land at the $MG5DIR root instead.

## Base install tree — full live top-level contents
Live top-level of `$MADGRAPH_INSTALL` (v3.7.1): `aloha/ Analyses/ bin/ HELAS/ HEPTools/ input/ madgraph/ MadSpin/ mg5decay/ models/ PLUGIN/ Template/ tests/ vendor/` (+ installed-tool dirs like `Delphes/`, files `VERSION INSTALL README.md UpdateNotes.txt proc_card.dat`).
- Commonly-overlooked dirs beyond the obvious `bin/ input/ models/ Template/ HEPTools/ madgraph/ tests/`: `aloha/`, `Analyses/`, `HELAS/`, `MadSpin/`, `mg5decay/`, `PLUGIN/`, `vendor/`.
- `bin/` holds ONLY `mg5_aMC` (the single launcher); other executables (`madevent`, `generate_events`, …) live in generated process dirs, not the root `bin/`.
- `HEPTools/` is present only because advanced tools were installed here — it is not part of a pristine unpacked release (created on first advanced install).

## Version files (for update/compat questions)
- `$MADGRAPH_INSTALL/VERSION`: `version` + `date` fields — read live (tier scopes to MG5 v3.7.1; `date` drifts per build).
- Also `HELAS/HELASVersion.txt`, `Template/{LO,NLO,MadWeight}/TemplateVersion.txt` — read live for the bundled component versions (drift-prone; see `plugin-install-and-version-compat.md`).
