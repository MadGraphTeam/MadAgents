---
description: LO matching output side — the matched cross-section reporting and 'Matched Integrated weight' banner write (ickkw>0 / ktdurham / ptlund), the use_syst-reweights-instead-of-vetoes notice, and the legacy PY6 MLM tree files (beforeveto/xsecs/events.tree).
---

# Matched cross-section reporting + banner write-out (LO matching, madevent side)

The post-shower/merging cross-section for a matched LO run is NOT the
matrix-element integration result — it is the count after the matching driver
vetoes/reweights events. This page maps how MadGraph (madevent side) reports it
and records it in the banner. Cites `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py`.
(The FxFx/NLO analogue is fxfx-amcatnlo-execution; the LHE per-event matching
tags are mlm-reweight-lhe-write.)

## Matched cross-section logged to screen / results (@2850-2878)
After the matching step, when `data['cross_pythia']` and `nb_event_pythia` are set:
- @2871: `logger.info("Matched cross-section : %.4g +- %.4g pb")` (decay process @2869 logs "Matched width").
- @2872: "Nb of events after matching/merging : %d".
- **@2873-2878 — the systematics-changes-merging notice:** if `use_syst` AND (`ickkw==1` OR `ktdurham>0` OR `ptlund>0`) AND `cross_pythia==-1` →
  `logger.info("Notice that because Systematics computation is turned on, the merging did not veto events but modified their weights instead. The resulting hepmc/stdhep file should therefore be use[d] with those weights.")`.
  **Non-obvious behavior: with `use_syst=True`, a merged run does NOT veto events — it keeps every event and adjusts the weight.** So the event count is unchanged and the matched xsec is encoded in weights, not in the surviving-event fraction. (Consistent with the PY8-bridge `Merging:applyVeto=False` / `JetMatching` weight path under use_syst.)

## Matched-xsec written to the banner (@5253-5258, @5446-5453)
For `int(ickkw)` truthy (any nonzero ickkw):
```
if 'MGGenerationInfo' in self.banner:
    self.banner['MGGenerationInfo'] += '#  Matched Integrated weight (pb)  :  %s\n' % cross_pythia
else:
    self.banner['MGGenerationInfo'] = '#  Matched Integrated weight (pb)  :  ...'
```
So a matched LHE banner carries a `# Matched Integrated weight (pb)` line (the post-merging xsec) in `MGGenerationInfo` — distinct from the un-matched ME integrated weight. Appears at two call sites (PY8 path @5256, legacy PY6 path @5449). **When verifying a matched run's cross-section, read `Matched Integrated weight`, not the ME `Integrated weight`.**

## Legacy PY6 MLM output files + xsec scrape (@5384-5462)
The legacy Pythia6 MLM driver (`run_type=='MLM'`, PY6):
- @5384-5385: for `ickkw==1`, output files include `beforeveto.tree`, `xsecs.tree`, `events.tree` (the MLM clustering trees the PY6 driver writes; `beforeveto.tree` is gzipped to `<tag>_pythia_beforeveto.tree.gz` @5458-5460).
- @5404-5428: for `int(ickkw)`, scrapes `<tag>_pythia.log` (regex on "I 0 All included subprocesses I <gen> <tried> I <xsec> I") for the matched xsec → `cross_pythia` (sigma_m), `nb_event_pythia`. So the PY6 matched xsec, like FxFx+PY8, comes from the SHOWER LOG, not the ME run.

## Cautions
- The matched cross-section ALWAYS comes from the matching driver's log/output, never the matrix-element integration — for both LO (MLM/CKKW, this page) and NLO (FxFx, fxfx-amcatnlo-execution). The ME "Integrated weight" over-counts (it is the inclusive multi-multiplicity sum before merging).
- `use_syst=True` flips merging from veto-mode to reweight-mode: event count unchanged, matching encoded in weights. A user expecting fewer events after merging will see the SAME count with `use_syst=True` — the merging is in the weights. This is the single most surprising matched-run behavior on the output side.
- The `Matched Integrated weight` banner line is written for ANY nonzero ickkw (`int(ickkw)` truthy) — so an MLM (1) run gets it; a fixed-order (0) run does not.
- All static-source (control flow + format strings). The actual scraped xsec value, the event-count-unchanged-under-use_syst behavior, and the verbatim log lines are runtime — probe-candidates, not asserted.
