---
description: HEPMCoutput:file handling in setup_Pythia8RunAndCard (hepmc/gz/remove/fifo/path) plus PY8 config paths and runtime artifact locations.
---

# HepMC output handling + PY8 paths/artifacts

## `HEPMCoutput:file` resolution (`madevent_interface.py:4321-4394`)
- `auto` -> `hepmc.gz`; `autoremove` -> `hepmcremove` (`:4322-4325`).
- `hepmc*` formats (`:4328-4362`): base path `Events/<run>/<tag>_pythia8_events.hepmc`. Card value forced (MadGraphSet force=True) to `<tag>_pythia8_events.hepmc` (`:4362`).
  - `@<path>` suffix => custom output dir; queues `to_store "moveHEPMC@..."` (`:4334-4343`).
  - `.gz` suffix => queues `compressHEPMC` in `to_store` (`:4346-4348`).
  - `remove` suffix => queues `removeHEPMC` (`:4354-4356`) — used when running Delphes (don't keep the hepmc).
- `fifo*` (`:4364-4389`): creates a fifo at `Events/<run>/PY8.hepmc.fifo` (or `@<custom>`). Sets via `defaultSet` (not to clobber user). PY8 then launched in background and do_pythia8 returns immediately (see do-pythia8-handoff). Note: fifo file extension must be `.hepmc.fifo`.
- `''` / `/dev/null` / `None` => logger.warning "User disabled the HepMC output" and HepMC_event_output=None (`:4390-4392`).
- anything else => InvalidCmd "Unknow HEPMCoutput:file setting" (`:4393-4394`).
- `auto` -> `hepmc.gz`, `autoremove` -> `hepmcremove` handled at (`:4322-4325`) BEFORE the startswith dispatch; both are pre-normalization aliases.
- Matching is `startswith("hepmc")` / `startswith("fifo")` on the lowercased value (`:4328`,`:4364`), so `hepmc.gz@<dir>`, `hepmcremove@<dir>` etc. all parse; `@` splits path, `.gz` suffix on `hepmc_specs[0]` gates compressHEPMC (`:4346`), `remove` suffix gates removeHEPMC (`:4354`).
- fifo `.hepmc.fifo` extension is a **documented convention only** (card comment line 29); the code (`:4374-4388`) does NOT validate the extension — it only checks existence / S_ISFIFO. So a wrong-extension custom fifo is not rejected here.

## BUG: `hepmc@<dir>` (no `.gz`) crashes in store_result (v3.7.1, `:5813-5835`)
`store_result()` assigns `hepmc_fileformat = ".gz"` **only inside** the `if 'compressHEPMC' in self.to_store:` branch (`:5824-5826`), but uses `file_path + hepmc_fileformat` unconditionally on the moveHEPMC path (`:5835`). So a plain `hepmc@<dir>` value (moveHEPMC queued, compressHEPMC NOT queued because no `.gz`) hits line 5835 with `hepmc_fileformat` unbound => `UnboundLocalError: cannot access local variable 'hepmc_fileformat'`.
- **Working form is `hepmc.gz@<dir>`** — the `.gz` queues compressHEPMC, so `hepmc_fileformat` is defined before the move. The non-compressed redirect is the broken one.
- Root: variable initialized in the wrong scope; no `hepmc_fileformat=''` default before the compress branch.

## Config paths (`input/mg5_configuration.txt`)
- `pythia8_path = $MADGRAPH_INSTALL/HEPTools/pythia8` (`:77`).
- `mg5amc_py8_interface_path = $MADGRAPH_INSTALL/HEPTools/MG5aMC_PY8_interface` (`:84`).
- Default-interface executable: `<pythia8_path>/share/Pythia8/examples/main164` (fallback `<pythia8_path>/examples/main164`).
- Old-interface executable: `<mg5amc_py8_interface_path>/MG5aMC_PY8_interface`.
(Whether these are actually installed/compiled is a runtime/installation-slice question — probe before asserting presence.)

## Runtime artifacts produced
- `Cards/pythia8_card.dat` — operative PY8 card.
- `Cards/shower_card.dat` — operative shower card (NLO+PS; `qcut` for matched).
- `Events/<run>/<tag>_pythia8.cmd` — actual card fed to PY8 (with run-instructions preamble).
- `Events/<run>/<tag>_pythia8.log` — PY8 stdout/stderr.
- `Events/<run>/run_shower.sh` — bash/tcsh wrapper that sets HEPTools libs and invokes pythia_main (`-c` flag for main164 path).
- `Events/<run>/<tag>_pythia8_events.hepmc[.gz]` — HepMC output.
- LHE input read by PY8: `Events/<run>/unweighted_events.lhe.gz` (LO; set via `Beams:LHEF`). NLO+PS shower reads `events.lhe`.
