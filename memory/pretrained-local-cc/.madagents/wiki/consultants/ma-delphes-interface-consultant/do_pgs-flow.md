---
description: do_pgs legacy detector flow — pgs compile, run_pgs launch, LHCO banner assembly, ExRootLHCOlympics root conversion
---

# `do_pgs` flow (legacy PGS detector)

`$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py:2318`, host `CommonRunCmd`.
Superseded by Delphes for new analyses; still wired as the `pgs` command and a laststep mode.

## Step sequence
1. `--no_default` parse; if set and no `Cards/pgs_card.dat`, returns early (2323-2331).
2. `check_pgs(args, no_default)` (2338) — may spawn a gunzip thread, returns a `lock`
   awaited later (2375-2376).
3. Card copy (2341-2344): no `pgs_card.dat` → copy `pgs_card_default.dat` (= LHC set).
4. Card-edit prompt unless `no_default`/`force` (2346-2347).
5. `pgsdir = pythia-pgs_path/src` (2351). Compiles `pgs` binary if missing (2357-2359).
   → PGS depends on the **pythia-pgs** package, NOT delphes_path.
6. Banner (2364-2370) written with pgs_card added.
7. Output LHCO assembly (2377-2407): writes banner-header `pgs_events.lhco`, runs
   `../bin/internal/run_pgs` with arg `[pgsdir]`, cwd=`Events/`, stdout→`<tag>_pgs.log`.
   Requires a `pgs.done` sentinel else logs "Fail to create LHCO events" and returns.
8. Optional ROOT via ExRootAnalysis `ExRootLHCOlympicsConverter` →
   `<run>/<tag>_pgs_events.root` (2410-2417).
9. Final LHCO moved to `<run>/<tag>_pgs_events.lhco`, plots (create_plot('PGS')), gzip
   (2418-2423). `update_status('finish', level='pgs')`.

## Cautions
- Two visible legacy bugs (cosmetic, do not block normal runs): line 2407 removes
  `'pgs_uncleaned_events.lhco '` with a trailing space (likely never matches); run_delphes2
  wrapper header still says "runs pgs". Flag only if debugging a PGS file-cleanup oddity.
- PGS output naming differs from card-page runtime-artefacts: pre-move file is
  `Events/pgs_events.lhco`; final is `<run>/<tag>_pgs_events.lhco`.
