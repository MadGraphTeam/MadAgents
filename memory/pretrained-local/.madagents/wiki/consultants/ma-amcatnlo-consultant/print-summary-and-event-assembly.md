---
description: aMCatNLOCmd runtime reporting + event assembly — print_summary (xsec/decay-width, bias DO-NOT-USE, scale/PDF block, summary.txt), reweight_and_collect_events (events.lhe.gz), banner_to_mcatnlo (MCatNLO/banner.dat shower-input bridge).
---

# Runtime reporting + event assembly + shower-input bridge

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`. Three runtime-side methods that the [[runtime-shell-commands]] `run()`/pipeline calls but that page only names abstractly. The cross-section/scale numbers themselves are computed by FKS/MadLoop and the scales-pdf slice; this page owns the *reporting and file-assembly* of those numbers.

## `print_summary` (3269) — the cross-section / decay-width banner
Called with `(options, step, mode, scale_pdf_info, done)`. `step==2` = after event generation (final, with advanced stats).
- **ninitial==1 → decay-width, not cross-section** (3280-3294): `cross_sect_dict['unit']='GeV'`, strings become "(Partial) decay width" / "(Partial) abs(decay width)". ninitial==2 → unit `'pb'`, "Total cross section". So a 1→N process reports a WIDTH in GeV, not a σ in pb.
- **`event_norm=='bias'` → appends ", incl. bias (DO NOT USE)"** to the xsec string (3295-3296): a biased run's reported cross section is explicitly flagged unusable.
- Status strings differ by mode (3298-3306): event modes ("Determining/Updating the number of unweighted events per channel", "Summary:") vs fixed-order ("Results after grid setup:", "Current results:", "Final results and run summary:"). `computed` tag = "(computed from LHE events)" vs "(computed from histogram information)".
- **Scale/PDF variation block** (3336-3374): printed only if `scale_pdf_info` AND (`nevents` ≥ the threshold literal at 3336-3374 OR mode∈{NLO,LO}). For `ickkw!=-1` prints "Dynamical_scale_choice N (envelope of M values): cen +max% -min%"; for `ickkw==-1` prints "Soft and hard scale dependence (added in quadrature)". PDF block prints per-set with method (none/unknown/hessian-etc). The variation NUMBERS are the scales-pdf slice; the formatting/gating is here.
- **Intermediate vs final** (3308-3380): non-final steps `logger.info` and `return` early. Final step also runs `compile_advanced_stats` (3402, wrapped so it never aborts the run) and writes artefacts.
- **Artefacts** (3416-3421): writes `Events/<run_name>/summary.txt` (message) and `.full_summary.txt` (message + debug stats), then `archive_files`. `summary.txt` is later read back by `getSysSummaryFromLog` (2799/2820).

## `reweight_and_collect_events` (3865) — assembling events.lhe.gz
Final event-mode step (called from `run()`); returns the event-file path.
- **Reweight branch taken ONLY if** `reweight_scale` OR `reweight_PDF` OR `len(dynamical_scale_choice)>1` OR `len(lhaid)>1` OR `store_rwgt_info` (3869-3871) → `run_reweight` produces `scale_pdf_info` + per-channel evt_files. Otherwise NO reweighting: reads `SubProcesses/nevents_unweighted`, takes lines with nonzero event count (3875-3877). So scale/PDF uncertainties in the summary appear only when one of those run_card knobs is set.
- Assembles final `Events/<run_name>/events.lhe.gz` via `collect_events.collect_events`, keeping banner tags `['MGVersion','MG5ProcCard','MGRunCard','slha','MGShowerCard']`, seed from `get_randinit_seed`, pigz-preferred, gzip level 6 (3885-3897).
- If not reweightonly: calls `print_summary(options, 2, mode, scale_pdf_info)` (the final step==2 summary, 3900) and moves `res*.txt` into the run dir.

## `banner_to_mcatnlo` (4629) — banner → `MCatNLO/banner.dat` (shower-input bridge)
Writes the `KEY=VALUE` env script that the MCatNLO shower scripts (`run_mcatnlo`, see [[runtime-shell-commands]]) consume. THE concrete banner→shower translation.
- `MCMODE=<shower>` (from banner run_card `parton_shower`, uppercased), `PDLABEL`, `NEVENTS`/`NEVENTS_TOT` (shower_card nevents capped at run_card nevents, divided by `nsplit_jobs`) (4633-4655).
- `ALPHAEW` resolved from param_card sminputs(1)/aEWM1/aEW with EWscheme awareness (4658-4687); top/Z/W/Higgs masses+widths from param_card (4690-4701, with hardcoded Higgs mass/width fallbacks if absent — read the fallback literals at 4690-4701).
- **MC masses** from the banner `montecarlomasses` block → `DMASS..GMASS` (4706-4728); lepton masses fall back to `SubProcesses/MCmasses_<SHOWER>.inc` on KeyError (4715-4726).
- `EVENT_NORM`, `ICKKW` (FxFx flag passed to shower), `DELTA=ON/OFF` (from `mcatnlo_delta`), `PTJCUT` (from `ptj`) (4729, 4782-4787).
- **LHAPDF-for-shower decision tree** (4731-4780) keyed on `shower_card['pdfcode']`: pdfcode>1 or (lhapdf & pdfcode==1) or HERWIGPP → link LHAPDF, copy set; pdfcode==1/-1 → try same set as generation, fall back to internal PDF with warning if no LHAPDF; else `PDFCODE=0` internal. HERWIGPP ALWAYS forces LHAPDF linking.
- Appends `PY8PATH`/`HWPPPATH`/`THEPEGPATH`/`HEPMCPATH` from options (4789-4796). Output → `MCatNLO/banner.dat`; returns the shower name.

## Cautions
- A decay process (`ninitial==1`) summary is a WIDTH in GeV — reading it as a cross section in pb is wrong by units and meaning.
- Scale/PDF uncertainties are absent from the summary unless a reweight/multi-scale/multi-lhaid/store_rwgt_info knob is set (3869-3871) — "no uncertainty band printed" usually means "no reweight requested", not "zero uncertainty".
- `banner_to_mcatnlo` reads `parton_shower` from the BANNER (the snapshot at launch), not the live run_card — consistent with `run_mcatnlo` reading the banner too. A run_card edited after the banner was written does not change the shower used.
- (Runtime predictions — exact summary text, which PDF branch fires — are source-read, not probe-verified end-to-end.)
