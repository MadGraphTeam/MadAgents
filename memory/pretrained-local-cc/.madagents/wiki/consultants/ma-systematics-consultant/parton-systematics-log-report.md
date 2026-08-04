---
description: parton_systematics.log summary report — print_cross_sections output format, per-arg cross-section table, envelope arithmetic for scale/alps/dyn/PDF, event_norm normalization, and the multicore cross-section re-aggregation.
---

# parton_systematics.log cross-section report

`$MADGRAPH_INSTALL/madgraph/various/systematics.py`, `print_cross_sections` (sys.py:465-600), v3.7.1. This is the human-readable summary written to `parton_systematics.log` (the `result_file` from `do_systematics`, cri.py:1845) after a Systematics run. My other pages describe the per-event `<rwgt>` weights; this describes the *summary block* a user reads to see the envelope percentages.

## Cross-section accumulation (`run`, sys.py:436-437)
- Per event: `wgt = event.wgt * wgts[i]/wgts[0]` (ratio to nominal arg index 0).
- `all_cross[j] += event.wgt*wgts[j]/wgts[0]` for every arg j — a running sum of reweighted cross-sections, one per variation.
- `wgts[0] == 0` → dumps event and `raise Exception` (sys.py:431-434).

## event_norm normalization (sys.py:468-485)
`norm = run_card['event_norm']` (default `'sum'`):
- `'sum'` → norm = 1 (weights already summed cross-sections).
- `'average'` / `'bias'` → norm = `1/nb_event`.
- `'unity'` → norm = 1.
`all_cross = [c*norm for c in all_cross]` before reporting. So the reported cross-sections honor the run_card's event normalization convention — an `average`-normalized run divides by event count.

## Per-arg table (sys.py:486-497)
Header `# mur  muf  alpsfact  dynamical_scale  pdf  cross-section`, then one row per arg:
`mur  muf  alps  dyn  <lhapdfID>  cross-section`. For EVA the pdf column is forced to `0` (sys.py:490-491); else `pdf.lhapdfID` (sys.py:493). This table is the machine-parseable part the multicore merge re-reads (see below).

## Envelope classification (sys.py:499-534)
Each arg is sorted into at most one envelope by which axes differ from nominal (`pdf==orig_pdf` required for all scale/alps/dyn buckets):
- **scale**: dyn∈{orig_dyn,-1} and (mur≠1 or muf≠1 or alps≠1) → min/max into `max_scale/min_scale`.
- **alps (emission scale)**: mur==muf==1, alps≠1, dyn∈{orig,-1} → `max_alps/min_alps`.
- **central (dyn) scheme**: mur==muf==alps==1 → `max_dyn/min_dyn` (this is the variation across *dynamical-scale schemes* at nominal mur/muf).
- **per-dyn buckets** (`dyns[dyn]`): non-orig dyn values get their own central + max/min (sys.py:513-525).
- **PDF**: nominal mur/muf/alps and dyn∈{orig,-1}, non-EVA → collected into `pdfs[lhapdfID][memberID]` for the per-set uncertainty combination (sys.py:527-532).

## Summary block (`resume`, sys.py:538-599)
Written between `#***...***#` rules:
- `# original cross-section: <all_cross[0]>`.
- `#     scale variation: +X% -Y%` = `(max_scale-c0)/c0*100`, `(c0-min_scale)/c0*100` (only if max_scale set).
- `#     emission scale variation: +X% -Y%` (ALPS).
- `#     central scheme variation: +X% -Y%` (dyn schemes at nominal mur/muf).
- `# PDF variation: +X% -Y%` from `pdfset.uncertainty(values)` (LHAPDF's own combination — `errplus`/`errminus`); `'unknown'` errorType skipped, `RuntimeError` → `# PDF variation: missing combination` (sys.py:551-581).
- Per non-orig PDF set: `#PDF <name>: <central> +X% -Y%`.
- Per dyn scheme: `# dynamical scheme # <key> : <central> +X% -Y% # <latex name>` with `dyn_name = {1:'\sum ET', 2:'\sum\sqrt{m^2+pt^2}', 3:'0.5 \sum\sqrt{m^2+pt^2}', 4:'\sqrt{\hat s}'}` (sys.py:583).
- `# PDF variation not available for EVA.` if pdlabel eva (sys.py:549-550).

## Multicore re-aggregation (`do_systematics`, cri.py:1992-2023)
For split runs, the parent re-builds the global cross-sections from each job's `log_sys_<i>.txt` table:
- Parses each non-`#` row: `key = tuple(floats[:-1])`, `cross = float(last)`.
- For `event_norm in {average, unity, bias}` multiplies `cross` back by that job's event count (`event_per_job(+1)`) before summing (cri.py:2003-2005) — because each job reported an *averaged* cross-section.
- After summing all jobs, `unity` re-divides by total `nb_event` (cri.py:2012-2014).
- Then a `running=False` `call_systematics` builds a `sys_obj` whose `print_cross_sections(all_cross, nb_event, result_file)` emits the merged summary (cri.py:2017-2023). The per-job `tmp_*` LHE outputs are `cat`-concatenated into the final output (cri.py:2028-2031).

## Cautions
- The reported percentages are an *envelope over the args that landed in each bucket* — if a requested variation didn't run (soft no-op; see `fail-soft-vs-fail-hard`), its bucket is simply empty and the corresponding line is omitted, not flagged. Absence of a "PDF variation" line can mean the PDF scan silently didn't run.
- `event_norm` mis-set between generation and systematics would mis-scale the reported cross-sections; the multicore path special-cases average/unity/bias, so a custom norm not in that set could merge inconsistently.
- `'unknown'`/custom PDF errorType → no uncertainty line (skipped), only the per-set rows.
- RUNTIME claim: exact emitted text and percentages are read from source, not probe-confirmed — a real `systematics` run would confirm the `parton_systematics.log` layout.
