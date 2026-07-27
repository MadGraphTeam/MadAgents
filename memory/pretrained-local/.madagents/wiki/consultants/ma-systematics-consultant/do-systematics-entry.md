---
description: do_systematics runtime entry (common_run_interface.py) — option syntax, lhapdf6 gate, run_card flag checks, from_card path, multicore split, call_systematics dispatch.
---

# do_systematics runtime entry

`$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py:1776` (`do_systematics`).
Top-level command run from the madevent/launch shell; delegates to `systematics.call_systematics`.

## lhapdf gate (cri.py:1788-1801)
- Calls `get_lhapdf_version()`. **If version starts with '5' → `logger.info('can not run systematics with lhapdf 5')` and returns (silent no-op).** Requires lhapdf 6.
- If no lhapdf version detectable → `logger.info('No version of lhapdf...')` returns.
- If python-lhapdf import fails → `logger.info` returns.

## Option syntax (cri.py:1813-1817)
Accepted option prefixes (raises InvalidCmd otherwise):
`--mur=` `--muf=` `--alps=` `--dyn=` `--together=` `--from_card` `--pdf=` `--remove_wgts=` `--keep_wgts` `--start_id=` `--weight_format=` `--weight_info=`.
Syntax: `systematics [INPUT [OUTPUT]] OPTIONS`. INPUT may be a run_name (resolved to `Events/<run>/unweighted_events.lhe[.gz]` or `events.lhe[.gz]`, cri.py:1832-1835).

## Run_card flag checks (cri.py:1862-1872)
- `store_rwgt_info=False` → InvalidCmd (NLO).
- `use_syst=False` → InvalidCmd (LO).
- Decay process (`ninitial==1`): with `--from_card` → `logger.warning('systematics not available for decay processes. Bypass it')` and return; without → InvalidCmd.

## PDF set provisioning (cri.py:1874-1914)
- `get_lhapdf_pdfsetsdir()`; on failure → `logger.warning('Systematic computation requires lhapdf...')` return.
- Collects requested lhaids (from `--pdf=` or run_card `systematics_arguments`/`sys_pdf`), then `copy_lhapdf_set` each. Download failure → `logger.warning('impossible to download...')` return.

## --from_card (cri.py:1881-1900) → call_systematics from_card path (sys.py:1352-1417)
Replaces `--from_card` with `--from_card=internal`. `call_systematics` then reads the LHE banner's run_card (`--from_card=internal`) or a named run_card file (`--from_card=PATH`, sys.py:1353-1354):
- **internal LHE-open retries a bounded number of times** with a growing back-off sleep on OSError (NFS/race tolerance; retry count + sleep base at sys.py:1356-1364).
- **`systematics_arguments` in `user_set`** (LO or NLO) → recurse `call_systematics([input,output]+systematics_arguments)` (sys.py:1371-1374, 1411-1414) — that string wins.
- else **LO** builds opts (sys.py:1377-1408): `mur=muf=sys_scalefact` (split floats), `alps=sys_alpsfact` (or [1.0] if 'None'), `together=[('mur','muf','alps','dyn')]`, `dyn=[-1,1,2,3,4]`. **`sys_pdf` parsing**: `&&`-separated sets, OR space-separated where a token that `isdigit()` and exceeds a large-integer threshold starts a new set name, a digit below it is a member-COUNT appended to the prior set (expanded to `SET@0..@N-1`); empty → `pdf='central'`. (Threshold in the parser at sys.py:1377-1408.)
- else **NLO with no `systematics_arguments`** → bare `raise Exception` (sys.py:1416).

## Multicore split (cri.py:1916-2034)
- run_mode 2 (multicore): `nb_submit = min(nb_core, nb_event//<per-job event divisor>)`.
- run_mode 1 (cluster): `nb_submit = min(cluster_size, nb_event//<per-job event divisor>)`.
- (Both divisors read at cri.py:1916-2034.)
- nb_submit in {0,1} → single `call_systematics([input,output]+opts,...)` (cri.py:1932-1936).
- Else: splits event ranges, runs `bin/internal/systematics.py` per job with `--start_event`/`--stop_event`/`--lhapdf_config`/`--result=./log_sys_<i>.txt`, `-O` if not __debug__; concatenates `tmp_*` outputs with `cat`. On cluster exception → falls back to run_mode 0 retry (cri.py:1977-1990).
- **Cross-section re-aggregation** (cri.py:1992-2023): parent re-reads each `log_sys_<i>.txt` cross-section table, multiplies back by per-job event count for `event_norm in {average,unity,bias}` before summing, re-divides by total `nb_event` for `unity`, then a `running=False` `call_systematics` calls `print_cross_sections(all_cross, nb_event, result_file)` for the merged summary. See `parton-systematics-log-report` for the report format.

## Output artefacts
- `Events/<run>/parton_systematics.log` — the result_file (cri.py:1845).
- Per-event `<rwgt>` block weights written into the OUTPUT lhe.

## Cautions
- lhapdf 5 / missing lhapdf → silent no-op via `logger.info`, NOT an error. A pipeline expecting variation weights gets none.
- `--from_card` on NLO without `systematics_arguments` → bare uncaught Exception.
