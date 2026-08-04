---
description: do_delphes control flow in common_run_interface.py — card copy, delphes2-vs-3 detection, prog dispatch, banner, LHCO-conversion gap
---

# `do_delphes` flow (MG → Delphes handoff)

Host: `CommonRunCmd` in `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py`
(class def line 635). Inherited by MadEventCmd; exposed as the `delphes` shell command
and as `generate_events --laststep=delphes`. Companion arg-checker `check_delphes` at line 335.

## Step sequence (`do_delphes`, line 3367)
1. `--no_default` parsing (3372-3376). If `--no_default` and no `Cards/delphes_card.dat`
   exists, logs "No delphes_card detected, so not run Delphes" and returns (3378-3380).
2. `check_delphes(args, nodefault)` (3383) → returns input event `filepath` (the pythia/
   pythia8 output to feed Delphes). check_delphes also re-reads config / raises InvalidCmd
   if `delphes_path` is unset (342-350).
3. **Delphes 2 vs 3 detection** (3389-3396): if `pjoin(delphes_path,'data')` EXISTS →
   `delphes3=False`, `prog='../bin/internal/run_delphes'`; else `delphes3=True`,
   `prog='../bin/internal/run_delphes3'`. i.e. presence of a `data/` dir under the Delphes
   install marks it as legacy Delphes2. Delphes2 rejects `.hepmc` input (3392-3393).
4. **Card copy** (3400-3406): if no `Cards/delphes_card.dat`, copies
   `Cards/delphes_card_default.dat` → `Cards/delphes_card.dat`, logs "No delphes card found.
   Take the default one." Trigger card copied only for delphes2 (3407-3409):
   `delphes_trigger_default.dat` → `delphes_trigger.dat`.
5. **Card edit prompt** (3410-3414): unless `no_default` or `self.force`. delphes3 edits
   only `delphes_card.dat`; delphes2 edits `delphes_card.dat` + `delphes_trigger.dat`.
6. **Banner** (3420-3424): if `Source/banner_header.txt` exists, adds delphes_card (and
   trigger for delphes2) to banner, writes `<run>_<tag>_banner.txt`.
7. **Launch** (3426-3436): `cross` from results; runs `prog` via cluster
   (`cluster.onecore` if no cluster set, line 3429-3432) with args
   `[delphes_dir, run_name, tag, str(cross), filepath]`, cwd=`Events/`,
   stdout→`<tag>_delphes.log`.
8. **LHCO note** (3438-3443): if neither `<tag>_delphes_events.lhco[.gz]` exists, logs
   "If you are interested in lhco output. please run root2lhco converter." — because
   run_delphes3 leaves the root2lhco step commented out (see run-delphes-scripts page).
9. Plots only if a PLAIN `.lhco` exists (3450-3453, create_plot('Delphes')); gzip lhco
   (3455-3456). create_plot('Delphes') itself triple-gates on madanalysis_path + td_path +
   plot_card.dat and is the legacy plot_events/td pipeline — see delphes-plot-and-lhco-output
   page for the full output half.
10. `update_status('delphes done', level='delphes', makehtml=False)` (3458) — note makehtml=False.

## Caution
- `delphes_path` MUST be set or check_delphes raises InvalidCmd (342-350). The `delphes`
  laststep mode is also gated in madevent_interface.py:1203 ("delphes not install").
  PRECISE GATE (check_generate_events, madevent_interface.py:1195-1206, v3.7.1): a
  `--laststep=delphes` arg first raises `'pythia-pgs not install'` if `pythia-pgs_path` is
  unset (1200-1202, fires for ANY non-parton laststep), THEN raises `'delphes not install'`
  if `delphes_path` is unset (1203-1205). So `generate_events --laststep=delphes` demands the
  pythia-pgs PACKAGE installed even though Delphes can run on Pythia8/HepMC — a non-obvious
  cross-dependency: missing pythia-pgs blocks the delphes laststep with a pythia-pgs error,
  not a delphes one.
- delphes2 path is detected purely by a `data/` subdir — a Delphes3 install that happens to
  have a `data/` dir would be misrouted to the legacy wrapper.
- Default ROOT output is `<run>/<tag>_delphes_events.root`; LHCO is NOT produced unless the
  user enables root2lhco. Plots therefore do not appear by default for delphes3.
