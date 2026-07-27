---
description: The do_pythia8 command in madevent_interface.py — how MadEvent steers a Pythia8 shower at LO (check_pythia8 LHE prep, run-mode/card-pruning, interface selection, card composition, parallelization depth).
---

# `do_pythia8` — the MG -> PY8 handoff (LO)

`madevent_interface.py:4579 def do_pythia8(self, line)`. This is the operative LO Pythia8 entry point (the `Pythia8Launcher` at `launch_ext_program.py:718` is a *different* thing — the standalone `main_*.cc` example compiler/runner; see shower-card-and-routing.md).

## Interface selection (which executable steers PY8)
- `--old_interface` flag => `use_mg5amc_py8_interface=True` => steers via the standalone `MG5aMC_PY8_interface` binary at `options['mg5amc_py8_interface_path']/MG5aMC_PY8_interface` (`:4635-4645`). Missing => InvalidCmd telling user to `install mg5amc_py8_interface` (`:4639`).
- Default (no flag) => `pythia_main = pythia8_path/share/Pythia8/examples/main164` (or `pythia8_path/examples/main164`) (`:4650-4652`). If `main164` not found/compiled => warns and recursively retries with `--old_interface` (`:4654-4655`).
- `mg5amc_py8_interface_consistency_warning` (`:4236`, static) compares `MG5AMC_VERSION_ON_INSTALL` / `PYTHIA8_VERSION_ON_INSTALL` files against current versions; mismatch => warning to refresh the interface install. Only fires on the `--old_interface` path (`:4646`).

## check_pythia8 — argument parsing + LHE-input preparation (`:1391`)
Called near the top of `do_pythia8` (`:4607`/`:4612`). This is where the LHE input is actually staged:
- `pythia8_path` validity requires `<pythia8_path>/bin/pythia8-config` to exist (`:1411-1412`) — a *different* check from the `main164`/old-interface executable check in `do_pythia8` itself.
- `--laststep=` arg (allowed: `auto`/`pythia`/`pythia8`/`delphes`, `:1400`) controls how far the downstream chain runs; `--tag=` sets the run_tag.
- **LHE input gzip-on-demand** (`:1444-1447`): if `Events/<run>/unweighted_events.lhe.gz` is absent but the uncompressed `unweighted_events.lhe` exists, it is gzipped via `misc.gzip`. Missing both => InvalidCmd "No event file". So the `Beams:LHEF=unweighted_events.lhe.gz` the card points at is materialized here, not assumed pre-existing.

## ask_pythia_run_configuration — run-mode selection + card pruning (`:6810`)
Invoked only when **not** `--no_default` (`:4620-4621`). For PY8 (`pythia_version=8`) the offered modes are `0/auto`, `1/pythia8`, and `3/delphes` (only if `delphes_path` set) — no PGS for PY8 (`:6815-6819`). `auto` resolves to `delphes` if `Cards/delphes_card.dat` exists else `pythia8` (`:6849-6852`). Then `keep_cards([...])` (`:6865`) prunes which downstream cards survive for the chosen mode (keeps `pythia8_card.dat` + `delphes_card.dat` when delphes), and `ask_edit_cards` opens the editor unless `self.force`. (This is the run-mode/card-pruning step my matching/hepmc pages assume has already happened.)

## --no_default card-existence gate (whether PY8 runs at all)
`:4592-4594`: when called with `--no_default` (the form the auto-launch chain uses, see lo-autolaunch-entry-chain.md), if `Cards/pythia8_card.dat` does NOT exist => **return immediately, silent no-op**. This is the gate that makes the `do_shower --no_default` "run all interfaced showers, each self-checks" pattern work: PY8 fires iff its card is present. Without `--no_default` (e.g. an explicit `pythia8` command), no such gate — it proceeds and `ask_pythia_run_configuration` (`:4621`) is invoked for the run mode.

## event_norm gate
`:4627-4629`: if `run_card['event_norm'] not in ['unit','average']` (i.e. `'sum'`) => `logger.critical("Pythia8 does not support normalization to the sum. Not running Pythia8")` and returns. PY8 parallelization additionally rejects `event_norm='sum'` at `:4821-4825`.

## run_type determination (drives matching-param setup)
`:4671-4677`:
- `ickkw==1` => `run_type='MLM'`
- `ickkw==2` OR `run_card['ktdurham']>0.0` OR `run_card['ptlund']>0.0` => `run_type='CKKW'`
- else `'default'` (no merging)

Note the CKKW marker is the *positivity of ktdurham/ptlund*, not an ickkw value (LO ickkw is only 0/1; see matching-param-handoff page).

## Card composition
- Reads `pythia8_card_default.dat` first, then overlays `pythia8_card.dat` with `setter='user'` so user_set tags are correct (`:4666-4669`).
- `setup_Pythia8RunAndCard(PY8_Card, run_type, ...)` (`:4307`) sets all process/run-specific params and returns the HepMC output path (see matching-param-handoff and hepmc-output pages).
- Written to `Events/<run>/<tag>_pythia8.cmd` with a preamble that pins HEPTools lib paths (`:4687-4713`). `direct_pythia_input=True`.
- LHE input: `PY8_Card.subruns[0].systemSet('Beams:LHEF', "unweighted_events.lhe.gz")` (`setup_Pythia8RunAndCard:4319`). `Beams:frameType=4` (LHEF) is a hidden always-written default (`banner.py:1925`).

## Run modes / parallelization
- `run_mode==0` (or run_mode==2 with nb_core==1): single local run via `run_shower.sh` wrapper (`:4733-4814`). For the non-old-interface (`main164`) path the wrapper passes `-c` before the card (`:4734`).
- `Main:numberOfEvents` set to `run_card['nevents']` for single-core non-old-interface (`:4683-4684`); also defaulted in `setup_Pythia8RunAndCard:4316-4317` when 0/-1.
- run_mode 1/2 multi-core: splits the LHE file into N partitions, copies `pythia_main` into `PY8_parallelization/`, writes per-split cards, `min_n_events_per_job` = the run_mode-keyed constants at `:4793-4796` (run_mode 2/local vs 1/cluster; read the two literals fresh at those lines).
- HepMC fifo output: launches PY8 in background (non-blocking) and returns immediately (`:4755-4769`).

### Parallelization depth (run_mode 1/2, `:4827-5143`)
- A `ParallelPY8Card` copy is written to `PY8_parallelization/PY8Card.dat` with `HEPMCoutput:file` normalized to `events.hepmc` (or `/dev/null` if no HepMC) and `Beams:LHEF=events.lhe.gz` (`:4835-4848`).
- LHE split into N partitions by event count (`partition`, `:4890-4892`); a separate `partition_for_PY8` tracks the user-requested-events split (`:4896-4898`).
- **Per-split renormalization** (`:4922-4937`): each split gets its own `PY8Card_<i>.dat` with `Main:numberOfEvents=partition_for_PY8[i]` (force) and `HEPMCoutput:scaling` multiplied by `partition_for_PY8[i]` (force) — because each showered split no longer carries the original total event count, the pb-scaling must be corrected per split. Written with `add_missing=False`.
- **HepMC reassembly** (`:5071-5139`): per-split `events.hepmc` files concatenated as header (from split 0, all non-`E` lines) + bodies (each stripped of its `n_head` header lines and trailing `HepMC::` line via `head -n -1 | tail -n +k`) + a single tail. `cat`'d together; if too many files, batched in steps of 20.
- DJR/pts/log merging and cross-section aggregation: see py8-result-extraction.md.

## CAUTION: Main:numberOfEvents not set for old-interface single-core (`:4683`)
The line-4683 assignment `PY8_Card['Main:numberOfEvents']=run_card['nevents']` is guarded by
`not use_mg5amc_py8_interface and run_mode==0 or (run_mode==2 and nb_core==1)`. Python precedence
(`not`>`and`>`or`) makes this `((not old) and run_mode==0) or (run_mode==2 and nb_core==1)`, NOT the
single-core test used at `:4800`/`:4807`. Verified: for the **old interface with run_mode==0** the guard
is False (any nb_core), so `Main:numberOfEvents` is NOT set to nevents here — it falls back to the
`setup_Pythia8RunAndCard:4316-4317` default (sets to nevents only if currently 0/-1). A user `Main:numberOfEvents`
in pythia8_card.dat would therefore survive on the old-interface single-core path but be overwritten on main164.
