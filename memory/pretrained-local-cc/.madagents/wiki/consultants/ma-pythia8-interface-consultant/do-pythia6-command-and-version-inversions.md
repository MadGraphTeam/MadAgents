---
description: The legacy do_pythia (Pythia6) command body and how it inverts/diverges from do_pythia8 — event_norm gate inversion, LHE-input format/deletion, StdHEP output, shared ask_pythia_run_configuration with pgs mode, .tree files for MLM.
---

# Legacy `do_pythia` (Pythia6) command + PY6/PY8 version inversions

`madevent_interface.py:5320 def do_pythia(self, line)`. The Pythia6 / pythia-pgs path. My shower-card-and-routing.md documented only the *card* (`pythia_card_default.dat`); this page is the *command body* and the structural inversions vs `do_pythia8` (`:4579`). All citations v3.7.1.

## The event_norm gate is INVERTED between PY6 and PY8
- `do_pythia8` (`:4627-4628`): `if run_card['event_norm'] not in ['unit','average']` (i.e. `'sum'`) => `logger.critical("Pythia8 does not support normalization to the sum. Not running Pythia8")` and return.
- `do_pythia` (`:5342-5344`): `if run_card['event_norm'] != 'sum'` => `logger.error('pythia-pgs require event_norm to be on sum. Do not run pythia6')` and return.

So a single `event_norm` value cannot satisfy both: `'sum'` runs Pythia6 and blocks Pythia8; `'unit'`/`'average'` runs Pythia8 and blocks Pythia6. On a `do_shower --no_default` chain that fires both interfaced showers, whichever shower matches the run_card's `event_norm` runs; the other silently early-returns at its gate. This is a real trap: "both cards present, only one showered" is explained by `event_norm`, not by card existence.

## `--no_default` card-existence gate (same shape as PY8)
`:5326-5330`: with `--no_default`, if `Cards/pythia_card.dat` absent => return (silent no-op). Mirrors do_pythia8's `:4592-4594` gate against `pythia8_card.dat`. This is what makes the `do_shower --no_default` "run all interfaced showers, each self-checks" pattern work for the Pythia6 leg (see lo-autolaunch-entry-chain.md).

## LHE input: uncompressed, and DELETED after the run
- Input file `Events/unweighted_events.lhe` (uncompressed `.lhe`, `:5389`) — contrast do_pythia8 which feeds `unweighted_events.lhe.gz` via `Beams:LHEF` (gzip-on-demand at check_pythia8 `:1444-1447`).
- `os.remove(.../unweighted_events.lhe)` immediately after the run (`:5398`). PY6 path consumes-and-deletes the uncompressed LHE; PY8 leaves the `.gz` in place.
- LHAPATH is appended to `pythia_card.dat` in-place if not already present (`:5369-5374`) — the card is mutated on disk before the run.

## Output artefacts (StdHEP, not HepMC)
- `output_files = ['pythia_events.hep']` (`:5381`) — StdHEP `.hep`, not HepMC. (PY8 produces `<tag>_pythia8_events.hepmc[.gz]`.)
- `if use_syst`: also `syst.dat` (`:5382-5383`).
- `if ickkw==1` (MLM): also `beforeveto.tree`, `xsecs.tree`, `events.tree` (`:5384-5385`) — the MLM matching `.tree` files. So Pythia6 MLM emits `.tree` files; PY8 MLM emits DJR (`<tag>_djrs.dat`, see py8-result-extraction.md).
- Success check: if `pythia_events.hep` absent => `logger.warning('Fail to produce pythia output...')` and return (`:5400-5402`).
- Run via `self.cluster.launch_and_wait(pjoin(pythia_src,'pythia'), ...)` (`:5388-5395`), `pythia_src = pythia-pgs_path/src` (`:5357`). Blocking (launch_and_wait), unlike PY8's optional fifo-background path.

## Matched-xsec readback (parallels PY8 but PY6-specific regex)
`:5407-5438`, only `if int(run_card['ickkw'])`:
- regex `pythiare` matches the `I  0 All included subprocesses  I <generated> <tried>  I <xsec>  I` log line (`:5411`), read bottom-up via `misc.reverse_readline` (`:5412`).
- `sigma_m = xsec*1e9` (mb->pb), `Nacc=generated`, `Ntry=tried` (`:5419-5421`).
- error formula `error_m = sqrt((error_LO*Nacc/Ntry)^2 + sigma_m^2*(1-Nacc/Ntry)/Nacc)` (`:5433`) — same form as PY8 (`:5188-5193`); `Nacc==0` => `error_m = 10000*sigma_m` (`:5435`, PY8 instead InvalidCmd's). Stored as `cross_pythia`/`nb_event_pythia`/`error_pythia` (`:5428-5437`) — the SAME result keys PY8 writes, so a Pythia6 and a Pythia8 run overwrite each other's `cross_pythia` if both run in one chain. (PY8 additionally has `cross_pythia8` from the DJR; PY6 has no `cross_pythia8`.)

## Shared run-config dialog `ask_pythia_run_configuration` (`:6810`)
Used by BOTH commands; `pythia_version` arg (6 default, 8 for PY8). Version-keyed divergences:
- available modes: `['0','1']` always; **`'2'` (pgs) only for version 6** (`:6815-6816`); `'3'` (delphes) iff `delphes_path` set.
- PY8 question text says `1. pythia8`; PY6 says `1. pythia` + `2. pgs : Pythia + PGS` (`:6824-6828`).
- `auto` resolution (`:6843-6851`): version-6 prefers `pgs_card.dat` -> pgs, else `delphes_card.dat` -> delphes, else pythia; version-8 has no pgs branch (delphes else pythia8 — consistent with do-pythia8-handoff.md which notes "no PGS for PY8").
- `keep_cards` then prunes to the chosen mode's cards (`:6862-6868`).

## Boundary
In slice: the MG-side command flow, gates, I/O artefacts, result readback for the Pythia6 interface. Out of slice: Pythia6's own shower/hadronization/MPI internals, and PGS detector sim (pgs is a separate downstream tool).
