---
description: run_delphes (delphes2) and run_delphes3 internal bash wrappers — which Delphes executable is called per input type, LHCO conversion commented out
---

# Internal Delphes wrapper scripts

`do_delphes` launches one of two bash scripts via `clus.launch_and_wait` with args
`[delphesdir, run, tag, cross, filepath]`.

## run_delphes3 (the modern path)
`$MADGRAPH_INSTALL/Template/LO/bin/internal/run_delphes3`
(copied into `<PROC_DIR>/bin/internal/` at output; LO-template only — no NLO copy found).

- Requires `$delphesdir/DelphesSTDHEP` to exist (else "No Delphes executable found … Quitting").
- **Executable choice by input file extension** (`$5` = filepath):
  - `.hep.gz`  → `gunzip --stdout | DelphesSTDHEP  card root` (Pythia6/STDHEP input)
  - `.gz` not `.hep.gz` (i.e. `.hepmc.gz`) → `DelphesHepMC2`
  - `.hep` → `DelphesSTDHEP`
  - else (`.hepmc`) → `DelphesHepMC2`
- Output: `<run>/<tag>_delphes_events.root`. Only the card is passed (no trigger card).
- **root2lhco / LHCO banner block is COMMENTED OUT** at the tail of the script. So LHCO
  output and Delphes plots are NOT produced by default — matches the "please run root2lhco
  converter" log in `do_delphes` (common_run_interface.py:3442) and the hint to "edit
  bin/internal/run_delphes3 to run the converter automatically".

## run_delphes (legacy Delphes2)
`$MADGRAPH_INSTALL/Template/Common/bin/internal/run_delphes`
(header comment still says "runs pgs" — copy-paste legacy).

- Requires `$delphesdir/Delphes` executable.
- Reads `inputfiles.list` = `pythia_events.hep` (STDHEP only; delphes2 has no hepmc).
- `sed` substitutes `DELPHESDIR` token in the card → `tmp_card.dat`, then calls
  `Delphes inputfiles.list delphes.root tmp_card.dat ../Cards/delphes_trigger.dat` —
  **the trigger card is consumed here only** (delphes2). Then `LHCO_Only delphes.root`.
- Produces `delphes_events.lhco`, prepends banner → `<run>/<tag>_delphes_events.lhco`.

## Cautions
- The trigger card (`delphes_trigger.dat`) is used ONLY by the delphes2 wrapper. delphes3
  ignores it entirely — its trigger/selection lives inside the delphes3 card modules.
- run_delphes3 hard-requires the `DelphesSTDHEP` binary name even for HepMC input (the
  existence check is on DelphesSTDHEP, line ~22), so a Delphes install missing that binary
  fails the guard before reaching the HepMC branch.
