---
description: check_delphes input-file resolution — which pythia/pythia8 output feeds Delphes (the LHE/HepMC->Delphes handoff), priority order, and two copy-paste .gz path bugs
---

# `check_delphes` input-file resolution (the handoff input)

`$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py`, `check_delphes`
(line 335). Called first by `do_delphes` (line 3383); its return value `filepath`
is the showered-event file fed to Delphes. This is the input-selection half of the
MG→Delphes handoff (the executable-selection half is in run_delphes3 — see
run-delphes-scripts page; it branches on this filepath's extension).

## delphes_path guard (335-350)
- If `options['delphes_path']` falsy → `set_configuration()` re-read, then if still
  falsy raise `InvalidCmd('No valid Delphes path set...')`. (Same guard my
  do_delphes-flow page notes; anchored here at the source.)

## No-arg case: ordered candidate `paths` list (367-390)
With no run-name arg, after `set_run_name(self.run_name, tag, 'delphes')` gives
`prev_tag`, it tries this list IN ORDER and takes the FIRST existing file (379-382):
1. `<run>/<tag>_pythia_events.hep.gz`     (Pythia6/STDHEP, gzipped)
2. `<run>/<tag>_pythia8_events.hepmc.gz`  (Pythia8/HepMC, gzipped)
3. `<run>/<tag>_pythia_events.hep`        (STDHEP, plain)
4. `<run>/<tag>_pythia8_events.hepmc`     (HepMC, plain)
5. `Events/pythia_events.hep`             (legacy fixed-name STDHEP)
6. `Events/pythia_events.hepmc`           (legacy fixed-name HepMC)
7. `Events/pythia8_events.hep.gz`
8. `Events/pythia8_events.hepmc.gz`
- Priority is **STDHEP(Pythia6) before HepMC(Pythia8), gzipped before plain** within
  each tagged pair. So in a run dir holding both a `.hep.gz` and a `.hepmc.gz`, Delphes
  gets the Pythia6 STDHEP file.
- If NONE exist: `input("NO INPUT")` blocks (384; a leftover debug prompt), then if
  `nodefault` return False, else `help_pgs()` + raise `InvalidCmd('No file file
  pythia_events.* ...')`.

## One-arg case: explicit run name (392-405)
Only FOUR candidates, if/elif (no `Events/`-level fallbacks):
- `.hep.gz` → that path
- `.hepmc.gz` → that path
- `.hep` (plain) → **sets filepath to the `.hep.GZ` path** (399, copy-paste bug)
- `.hepmc` (plain) → **sets filepath to the `.hepmc.GZ` path** (401, copy-paste bug)
- else raise `InvalidCmd('No events file corresponding to %s run...')`.

## Caution — two copy-paste path bugs (399, 401), source-confirmed
In the one-arg branch the plain-file `elif`s TEST `_pythia_events.hep` /
`_pythia8_events.hepmc` (no .gz) but ASSIGN the `...hep.gz` / `...hepmc.gz` path:
```
elif os.path.exists(... '%s_pythia_events.hep' % prev_tag):
    filepath = pjoin(... '%s_pythia_events.hep.gz' % prev_tag)   # 398-399
elif os.path.exists(... '%s_pythia8_events.hepmc' % prev_tag):
    filepath = pjoin(... '%s_pythia8_events.hepmc.gz' % prev_tag) # 400-401
```
So when only a PLAIN (un-gzipped) showered file exists and the user names the run
explicitly, `do_delphes` is handed a `.gz` path that may not exist → downstream
run_delphes3 gets a missing file. The no-arg `paths` list (367-382) does NOT have this
bug. Flag only when debugging "delphes can't find the events file" with an explicit run
name on a plain (non-gzip) pythia output.

## Caution — delphes2 hepmc reject uses a fragile slice (3392)
After resolution, `do_delphes` rejects HepMC for delphes2 via
`'.hepmc' in filepath[:-10]` (line 3392) — slices off the trailing 10 chars before the
substring test. Source-visible fragility; not normally triggered (delphes2 is legacy).
