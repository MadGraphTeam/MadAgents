---
description: OUTPUT half of do_delphes — create_plot('Delphes') triple-gate (madanalysis_path+td_path+plot_card.dat), legacy plot_events/plot/plot_page-pl pipeline on <tag>_delphes_events.lhco, root2lhco commented-out tail, why default delphes3 yields no plots
---

# The output / plotting half of `do_delphes`

Complements `do_delphes-flow` (steps 8-10, one-lined there) and `run-delphes-scripts`
(the executable launch). This page is what happens AFTER `run_delphes3` returns: the
LHCO-existence gates, the `create_plot('Delphes')` pipeline, and why a default delphes3
run produces NO plots and NO LHCO. All in
`$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py` unless noted.

## 1. The LHCO-existence message (do_delphes 3438-3443)
After the wrapper launch, do_delphes checks for `<run>/<tag>_delphes_events.lhco[.gz]`:
```
if not os.path.exists(... '%s_delphes_events.lhco.gz' % tag)
   and not os.path.exists(... '%s_delphes_events.lhco' % tag):
    logger.info('If you are interested in lhco output. please run root2lhco converter.')
    logger.info(' or edit bin/internal/run_delphes3 to run the converter automatically.')
```
This fires on EVERY default delphes3 run, because run_delphes3 leaves root2lhco commented
(see §4). It is informational, not an error.

## 2. The plot gate inside do_delphes (3450-3456)
do_delphes only calls the plotter / gzips the LHCO if a PLAIN `.lhco` exists:
```
if os.path.exists(... '%s_delphes_events.lhco' % tag):   # 3450-3451
    self.create_plot('Delphes')                           # 3453
if os.path.exists(... '%s_delphes_events.lhco' % tag):   # 3455
    misc.gzip(... '%s_delphes_events.lhco' % tag)         # 3456
```
So **no LHCO ⇒ no plot call and no gzip.** The root output `.root` is untouched here.
Final: `update_status('delphes done', level='delphes', makehtml=False)` (3458) —
NOTE the `makehtml=False` (do_delphes-flow step 10 omitted this).

## 3. `create_plot('Delphes')` — the legacy td/MadAnalysis plot pipeline (1417-1649)
`create_plot(self, mode='parton', ...)` (def 1417) handles parton/Pythia/PGS/Delphes/shower.
For mode=='Delphes':

### TRIPLE GATE (1423-1429) — silent `return False` if any missing
```
if mode != 'Pythia8':
    madir = self.options['madanalysis_path']
    td = self.options['td_path']
    if not madir or not td or \
       not os.path.exists(pjoin(self.me_dir, 'Cards', 'plot_card.dat')):
        return False
```
Three independent preconditions, ALL required: `madanalysis_path` set, `td_path` set,
AND `Cards/plot_card.dat` exists. Any one absent → returns False, no plot, no error.
- BOTH config paths ship COMMENTED in `input/mg5_configuration.txt`:
  `# madanalysis_path = ./MadAnalysis` (line 176), `# td_path = ./td` (line 189). So a
  default install has neither set → Delphes plots are off by default even if an LHCO existed.
- This `madanalysis_path` is the LEGACY MA5/`plot_events` tool, NOT the modern MadAnalysis5
  Python interface (that is `run_madanalysis5`, a separate downstream slice). do_delphes only
  INVOKES create_plot; the plot-tool internals are out of slice.

### Input file and output (1575-1578)
```
elif mode == 'Delphes':
    event_path = '<run>/%s_delphes_events.lhco' % tag
    output     = 'HTML/<run>/plots_delphes_%s.html' % tag
```
It reads the SAME `<tag>_delphes_events.lhco` whose absence gated the call — so create_plot
on Delphes is only ever reached when that LHCO exists (do_delphes 3450). If the file is `.gz`
it is gunzipped (1591-1598).

### The pipeline (1611-1646) — three external programs
1. `plot_dir = HTML/<run>/plots_delphes_<tag>` created; `plot_card.dat` symlinked in as
   `ma_card.dat` (1614, `files.ln`).
2. `madir/plot_events` run with the lhco path fed on stdin (1617-1622).
3. `<dirbin>/plot madir td` (1625-1628) — the td histogram step.
4. `<dirbin>/plot_page-pl <plotdir> delphes` (1630-1635) builds the HTML page;
   `plots.html` moved to `plots_delphes_<tag>.html` (1637-1638).
5. On OSError: `logger.error('fail to create plot: ... check that MadAnalysis is correctly
   installed.')` (1642-1643) — non-fatal, do_delphes continues.

## 4. Why default delphes3 yields no LHCO and no plots (run_delphes3 tail, verbatim)
`$MADGRAPH_INSTALL/Template/LO/bin/internal/run_delphes3` lines 46-58 are COMMENTED:
```
# Uncomment the following to have the LHCO file:
#$delphesdir/root2lhco ${run}/${tag}_delphes_events.root delphes_events.lhco
#if [ -e delphes_events.lhco ]; then
#    sed -e "s/^/#/g" ${run}/${run}_${tag}_banner.txt > ${run}/${tag}_delphes_events.lhco
#    echo "##  Integrated weight (pb)  : ${cross}" >> ${run}/${tag}_delphes_events.lhco
#    cat delphes_events.lhco >> ${run}/${tag}_delphes_events.lhco
#    gzip ${run}/${tag}_delphes_events.lhco
#    rm -f delphes_events.lhco
#fi
```
So the chain on a default delphes3 run is: ROOT produced → no root2lhco → no `.lhco` →
do_delphes 3450 gate fails → create_plot('Delphes') NEVER called → no
`plots_delphes_<tag>.html`. The triple gate in §3 is therefore a SECOND barrier the default
run never even reaches. To get Delphes plots a user must (a) uncomment root2lhco in
run_delphes3 (or run it by hand) AND (b) have madanalysis_path + td_path + plot_card.dat.

The wrapper's extension dispatch (lines 21,27-42) also hard-requires the `DelphesSTDHEP`
binary to exist (line 21 guard) before any branch, even for HepMC input — see
run-delphes-scripts page.

## 5. plot_card.dat ownership
- Template: `$MADGRAPH_INSTALL/Template/Common/Cards/plot_card.dat` (one file, no
  ATLAS/CMS variants). Classified by `detect_card_type` via the `begin minpts` token
  (common_run_interface.py:1257-1258) — NOT one of my detector cards. Its CONTENT (the
  plot/histogram definitions) belongs to the legacy-plot/MA tooling, out of slice. My slice
  owns only that do_delphes/create_plot REQUIRE its existence to plot Delphes output.

## Cautions
- A standalone `Template/LO/bin/internal/run_plot_delphes` script exists (gunzip lhco →
  `$dirbin/plot` → `plot_page-pl ... Delphes`, gated on `delphes_events.lhco` AND
  `plot_card.dat`), but it has NO caller anywhere in madgraph/ or Template/ (grep-confirmed,
  v3.7.1) — it is dead legacy. The ACTIVE delphes-plot path is `create_plot('Delphes')` (§3).
  Do not mistake this script for a live delphes3 plotting route.
- The Delphes ROOT file (`<tag>_delphes_events.root`) is the only default delphes3 artefact;
  LHCO and HTML plots are both OFF by default (two independent reasons: root2lhco commented,
  and the plot triple-gate). A user expecting `.lhco`/plots from a vanilla `generate_events`
  with Delphes gets neither — only the ROOT file.
- create_plot's OSError handler blames "MadAnalysis correctly installed" even though the
  failure could be td or plot_card — misleading error text if debugging a Delphes-plot fail.
