---
description: generate_events() per-PDG decay-ME event generation — gridpack vs non-gridpack regimes, over-gen headroom, under-gen critical, seed/width/systematics wiring (interface_madspin.py)
---

# generate_events — per-PDG decay-sample generation (interface seam)

`generate_events(pdg, nb_event, mg5, restrict_file=None, cumul=False, output_width=False)` at
`$MADGRAPH_INSTALL/MadSpin/interface_madspin.py:1211`. Called from run_bridge and run_onshell to
produce the decay-event samples that get merged onto production events. The bridge/onshell pages
cover WHEN it is called and the cap on the count argument; this page caches the **body**:
how a decay subprocess is built and run, and the run_card/seed/width wiring the interface controls.
The decay matrix-element physics (decay.py) is out of slice — this is the MadEvent-driver seam.

## per-decay subprocess directory (:1239-1250)
- one dir per (pdg, branch index): `decay_<PDG>_<i>` under `path_me` (pdg `-` -> `x`, :1239).
- `cumul=True`: `generate <proc>` then `add process <proc2>` for every other branch of that name,
  one combined `output <dir> -f` (:1241-1247) — all branches share one ME dir, events drawn by
  relative cross-section. `cumul=False`: a single `generate`+`output` (:1248-1250).
- skipped if the dir already exists (reuse).

## two generation regimes, selected by `ms_dir`
### gridpack regime (`ms_dir` set, :1252-1298) — build-once, reuse
- a per-dir `MadEventCmdShell` (`me_int[decay_dir]` cache, :1255-1270); disables
  `automatic_html_opening`, nulls `madanalysis5_path`/`madanalysis_path`, removes the MA5 parton
  cards, `allow_notification_center=False`.
- run_card forced: `iseed = options['seed']`, **`gridpack = True`**, **`systematics_program='False'`**,
  **`use_syst=False`** (:1276-1280); param_card written from `banner['slha']` (:1281-1282).
- `options['seed'] += 1` and `self.seed = options['seed']` (:1283-1284) — the per-PDG seed increment
  (also noted on the staging page).
- `generate_events run_01 -f` builds the gridpack; `output_width` accumulates the cross
  (cumul: `width += cross`; else `width *= cross`, :1287-1291).
- then strips Cards/bin/Source/SubProcesses and untars `run_01_gridpack.tar.gz` in place so the dir
  becomes a runnable gridpack (`run.sh`, :1294-1298).
- later events drawn via `run.sh <int(over_gen*nb_event)> <seed>` (:1363); gridpack seed =
  `<offset> + mother.run_card['iseed']` when driven by ME (:1356), wraps modulo the seed-space bound (:1360-1361),
  output `events.lhe.gz` (:1364). Read the over-gen factor, offset, and bound fresh at their lines.

### non-gridpack regime (no `ms_dir`, :1300-1351) — generate inline
- same MadEventCmdShell setup + MA5/html disabling (:1304-1317) (note duplicated
  `automatic_html_opening` line :1306-1307 — harmless).
- run_card from `options['run_card']` if set, else the dir's run_card (:1318-1327).
- **`nevents = int(over_gen*nb_event)`** (:1328 — over-gen factor >1, read fresh) — generates more than asked (over-gen headroom);
  `iseed = self.seed`, `systematics_program='None'` (:1335-1336); param_card from `banner['slha']`
  (:1338-1339); `self.seed += 1` (:1340).
- `generate_events run_01 -f`; width accumulated as above (:1341-1346); output read as
  `Events/run_01/unweighted_events.lhe.gz` (:1351).
- **under-generation critical (:1347-1349)**: if `nevents` exceeds the actual generated count by more than a small tolerance (read fresh at :1347) ->
  `logger.critical('The number of event generated is only %s/%s. This typically indicates that you
  need specify cut on the decay process.')` + 'We strongly suggest that you cancel/discard this run.'
  Non-fatal, but a strong signal that the decay phase space is being cut/zeroed. (Runtime text — not
  probe-verified here, read from source.)

## width return (:1368-1371)
With `output_width=True` returns `(out, width)` where `width` is the summed (cumul) or multiplied
partial cross-section, consumed by run_onshell's BR computation (pwidth, see onshell-algorithm page).
Otherwise returns just `out` (dict branch-index -> EventFile).

## Cautions
- Systematics are FORCED OFF for every decay subprocess in both regimes (gridpack:
  `systematics_program='False'`+`use_syst=False`; inline: `systematics_program='None'`). A user
  expecting systematic weights on the decay leg won't get them from the decay generation — the
  production systematics ride through unchanged on the merged event.
- The `int(over_gen*nb_event)` over-gen (:1328) and the generation count cap (bridge/onshell pages) compose: the actual
  run_card nevents is `int(over_gen * min(needed, CAP))` — read both constants fresh.
- The under-gen critical is the canonical "decay BR is being cut" symptom; it does not abort, so a
  decayed file can be produced from a starved decay sample.

## Gaps
- decay-ME generation/sampling internals (decay.py), gridpack survey precision — out of slice /
  MadSpin internals.
