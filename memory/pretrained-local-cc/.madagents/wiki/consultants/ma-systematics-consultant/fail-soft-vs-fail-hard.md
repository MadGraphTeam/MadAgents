---
description: Failure-mode taxonomy of the systematics/reweight subsystem — default is fail-SOFT (degrade/no-op via logger, silent); an enumerable set of preconditions fail-HARD (raise). Plus do_systematics help-text-vs-whitelist option-name traps.
---

# Fail-soft vs fail-hard in the systematics / reweight subsystem

**Principle.** When a precondition is not met, the systematics/reweight subsystem's *default* behaviour is to **degrade or no-op silently** — emit `logger.info`/`logger.warning` (sometimes `logger.critical`) and return, or silently force a parameter to a fallback value — NOT to raise. Only a small, enumerable set of preconditions **fail-hard** (raise an exception). The operational consequence: a pipeline expecting variation weights, PDF-error sets, or NLO-accurate reweighting can get a **quietly different** result with no non-zero exit. Always confirm what was actually produced (`parton_systematics.log`, the emitted `<weightgroup>`s in the output banner) rather than trusting that the requested variation ran.

This generalizes the per-page Cautions sections (`systematics-class`, `do-systematics-entry`, `reweight-interface`, `ew-sudakov-reweight`) into one default expectation, and catches *future* precondition-not-met cases not individually enumerated: assume soft-failure unless the case is in the hard list below.

## Fail-SOFT (degrade / no-op, no exception)
Verified `logger.* + return` / forced-fallback sites:
- **lhapdf 5 / no lhapdf / unlinkable python-lhapdf** → `logger.info(...)` + return, `do_systematics` (cri.py:1791, 1795, 1800). The lhapdf gate is the FIRST check, before any run_card-flag validation.
- **decay process (`ninitial==1`) with `--from_card`** → `logger.warning('systematics not available for decay processes. Bypass it')` + return (cri.py:1869). (Without `--from_card`: hard — see below.)
- **lhapdf pdfsetsdir missing / pdfset download fails** → `logger.warning('... Bypass ...')` + return (cri.py:1878, 1913).
- **LHAPDF python module load fails (non-EVA)** → log 'fail to load lhapdf' + early return, no systematics (sys.py:222-227).
- **both beams non-proton** → `pdf` silently forced to `'central'` (sys.py:113) — a requested PDF error set is NOT computed.
- **dyn=4 (sqrts) with both beams hadronic AND NLO** → silently dropped from the dyn list (sys.py:201-206).
- **GoSam (any non-MadLoop) OLP on NLO reweight** → `logger.warning('Accurate NLO mode only works for OLP=MadLoop ...')`, forced to approximate LO (ri.py:203, 407).
- **`change include_sudakov True`** → silently forces `rwgt_mode='LO'` (ri.py:447); no NLO-accurate ME reweight alongside.
- **`change output`/`rwgt_dir`/`process`/`model` after `launch`** → multicore silently disabled, serial run, no error (cri.py:2054-2083).
- **unknown reweight_card option** → `logger.critical('unknown option! ... Discard line.')`, line silently dropped (ri.py:449).
- **EW-Sudakov event with `|sudrat1|` above the damping threshold** → `logger.info('ERROR: ... too large ...')`, event kept at NOMINAL weight (counted, not reweighted) (ri.py:1339-1349); tally logged at end.
- **model lacks `tadpole`/`ntadpole` block (EW Sudakov)** → `logger.warning('... may give wrong results')`, proceeds anyway (cri.py ~1022-1033).

## Fail-HARD (raise) — the enumerable exceptions
- **LO without `use_syst=True`** → `SystematicsError` (sys.py:173).
- **NLO without `store_rwgt_info=True`** → `SystematicsError` (sys.py:183).
- **decay process WITHOUT `--from_card`** → `InvalidCmd` (cri.py do_systematics).
- **EVA misconfiguration** (no e/mu beam, or EVAxDIS wrong beam) → `SystematicsError` (sys.py:141, 152, 160).
- **`pdlabel` in {none, chff, edff}** → `SystematicsError('Systematics not supported ...')` (sys.py:165).
- **invalid `systematics` option syntax** → `InvalidCmd` (cri.py:1813; see sub-trap below).
- **individual error-set called with LHAGLUE number not LHAPDF name** → `Exception` (sys.py:255).
- **NLO `--from_card` with no `systematics_arguments` in run_card** → bare `raise Exception` (sys.py:1416).
- **EVA pdfrwt x1/x2 count mismatch; stored-vs-computed disagreement; unknown EVA vPol; unknown CLI arg** → `SystematicsError`/`Exception` (sys.py:993, 1008, 1101, 1115, 1349).
- **double-Sudakov reweight** (tag already present) → `logger.critical(...)`+return on the event side (ri.py:633); `sys.exit(1)` on the header-emit side (ri.py:973).
- **ME reweight: original ME = 0** → `raise Exception("Invalid matrix element for original computation (weight=0)")` (ri.py:1169).
- **NLO ME reweight on mixed QCD+QED Born** (`not ispureqcd`) → `raise Exception('NLO reweighting does not support mixed expansion mode...')` (ri.py:1381).
- **final state absent from new model + `allow_missing_finalstate=False`** (default) → `logger.critical(...)`+`raise Exception` (ri.py:1574). **Message-inversion trap**: the critical text says use `change allow_missing_finalstate False` to zero such weights, but the code zeros only when the option is **True** (ri.py:1571) — the suggested fix names the wrong boolean. To zero-out (soft) instead of crash: `change allow_missing_finalstate True`.

Rule of thumb: the hard set is "**the events were generated wrong**" (missing use_syst/store_rwgt_info, unsupported pdlabel, EVA self-inconsistency) plus a few outright user-syntax errors. Everything *environmental* (lhapdf absent, pdfset undownloadable, OLP wrong, decay process) tends to fail SOFT.

## Sub-trap: `do_systematics` help-text vs whitelist option names
The `help systematics` text advertises option names the command's own validation whitelist does NOT accept; copying them verbatim raises `InvalidCmd`:
- `--only_beam=` and `--ion_scaling=` — advertised (cri.py:1721-1722), parsed by systematics.py's subprocess arg-parser (sys.py:1339, where `only_beam` is cast to int), but ABSENT from the `do_systematics` whitelist (cri.py:1814). Reach the class only via direct API / the per-job `bin/internal/systematics.py` subprocess (multicore path).
- `--remove_weights=` / `--keep_weights=` (with the trailing 's') — advertised (cri.py:1718-1719) but the whitelist and tab-completion accept only `--remove_wgts=` / `--keep_wgts` (cri.py:1754-1755, 1814).

Probe (option-whitelist boundary, replicating the cri.py:1813-1814 `startswith` check): `--only_beam=0`, `--ion_scaling=True`, `--remove_weights=all`, `--keep_weights=` → all INVALID; `--mur=0.5,1,2`, `--pdf=errorset`, `--from_card` → accepted. Confirms the advertised-but-rejected names raise.

Source oddity (noted, narrow): the subprocess arg-parser at sys.py:1341 matches the misspelled key `ion_scalling` (double-l) for the bool branch, so `--ion_scaling=` passed to the subprocess would miss the bool cast and fall to the list branch. Edge case; only relevant on the direct-API/subprocess path.

## How to use this page
- When asked "will <X precondition failure> error out or silently degrade?": default answer is **degrade** unless X is in the hard list. State which.
- When asked why expected variation weights are missing from an LHE: the prime suspects are the SOFT no-op paths (lhapdf 5/absent, pdfset download fail, non-proton beam forcing central, OLP≠MadLoop forcing LO) — none of which would have surfaced as an error.
- When a user reports `InvalidCmd` from a `systematics` option they "copied from the help": check the help-vs-whitelist sub-trap.
