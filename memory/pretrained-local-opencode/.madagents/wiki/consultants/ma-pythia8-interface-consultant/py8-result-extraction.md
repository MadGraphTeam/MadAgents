---
description: How do_pythia8 reads matched cross-sections / event counts back from the PY8 log + DJR file into MadEvent results (cross_pythia, cross_pythia8, error_pythia) after the shower runs.
---

# Post-shower result extraction (PY8 log/DJR -> MadEvent results)

After PY8 finishes, `do_pythia8` parses the shower's own output to recover the showered/matched
cross-section and event counts and store them in `self.results`. This is the return leg of the
handoff — the interface artifact is the PY8 log + DJR file, and MadGraph reads them back. All in
`madevent_interface.py`.

## Gate: only for merged runs
- `merged_run_types = ['MLM','CKKW']` (`:4672`). The cross-section/DJR extraction block (`:5168-5231`)
  runs **only if `run_type in merged_run_types`** — i.e. only for MLM (`ickkw==1`) or CKKW
  (`ktdurham>0`/`ptlund>0`). An unmatched `default` run does NOT populate `cross_pythia8`.

## Success check first (`:5155-5158`)
Before any extraction: if `<tag>_pythia8.log` is missing OR `'Inclusive cross section:'` is not in its
**last 20 lines** => `logger.warning('Fail to produce a pythia8 output...')` and **return** (no results
stored). This is the canonical "did PY8 actually run" probe. `self.to_store.append('pythia8')` (`:5165`)
and the merging-plot creation (`create_plot('Pythia8')`, `:5161`) happen just before the merged block.

## sigma_m / Nacc / Ntry — from the log (`:5168-5199`)
- `parse_PY8_log_file(log)` (`:5267`) reads the log **backwards** (`misc.BackRead`). Two regexes:
  - `pythiare` matches the "Les Houches User Process(es)" summary line -> `tried`/`selected`/`generated` + `xsec`/`xsec_error`. `Nacc=generated`, `Ntry=tried`, `sigma_m=xsec*1e9` (PY8 reports mb; ×1e9 -> pb).
  - `pythia_xsec_re` matches the final `Inclusive cross section:` line -> `sigma_m=xsec*1e9` (more reliable when merging skips the last event).
  - `Nacc==0` => InvalidCmd "did not accept any event" (`:5293-5295`). Missing both lines => InvalidCmd (`:5300`).
- Stored: `results.add_detail('cross_pythia', sigma_m)`, `('nb_event_pythia', Nacc)` (`:5181-5182`).
- **Pythia error formula** (`:5188-5193`): `error_m = sqrt((error_LO*Nacc/Ntry)^2 + sigma_m^2*(1-Nacc/Ntry)/Nacc)` where `error_LO` is the parton-level cross-section error; ZeroDivision => `error_m=-1.0`. Stored as `error_pythia`.

## CAUTION: use_syst + old interface zeroes cross_pythia (`:5197-5199`)
If `run_card['use_syst'] AND use_mg5amc_py8_interface`: `cross_pythia` is **overwritten to -1** and
`error_pythia` to 0 — the systematics/old-interface path does not report a single matched xsec this way
(the merged values come from the DJR instead). On the default main164 path this override never fires.

## Matched cross-sections — from the DJR (`:5201-5228`)
- `extract_cross_sections_from_DJR(djr)` (`:5303`): parses `<tag>_djrs.dat` (XML), reads run id=0's
  `<xsection name=...>` nodes -> `{name: [value, error]}`. **DJR values are already in pb** (no ×1e9).
- The names are filtered to keep only **central-parameter** entries with a varying merging scale via regex
  `Weight_MERGING = <float>` (`:5217-5223`) -> dict keyed by *merging scale value*.
- The central scale is `PY8_Card['JetMatching:qCut']` for MLM (`ickkw==1`) else `Merging:TMS` (`:5224-5225`).
  If that scale key is present => `results.add_detail('cross_pythia8', xsec)`, `('error_pythia8', err)` (`:5227-5228`).
- So `cross_pythia8`/`error_pythia8` is the **merged cross-section at the central matching scale**, distinct
  from `cross_pythia` (the inclusive showered xsec from the log).

## Parallel-run aggregation (run_mode 1/2 multi-core)
When parallelized, the per-split logs/DJRs are merged BEFORE the block above (`:4980-5052`):
- log: `sigma_m` summed over splits then **divided by n_added** (averaged) (`:4994-5009`); `Nacc`/`Ntry` summed.
- DJR cross-sections: values summed across splits, errors added **in quadrature** then `sqrt`/n_added (`:5019-5052`).
- The single-core `parse_PY8_log_file` fallback at `:5170-5178` is skipped for parallel runs (can't read one log);
  a `logger.warning('Pythia8 cross-section could not be retreived... set nb_core to 1')` fires instead.

## Boundary
This is the MG-side *read-back* of PY8's reported numbers — in slice. The physics of how PY8 computes the
matched xsec (the CKKW-L/MLM weight, the DJR histogramming) is PY8-internal / matching-algorithm (out of slice).
