---
description: run_rivet_later is the single switch for Rivet run-now vs defer-to-postprocessor — full lifecycle (origins, two run-now overrides, consumption) answering any "will my Rivet run immediately or defer, and why" question.
---

# When does Rivet run now vs defer? (run_rivet_later lifecycle)

The boolean `run_rivet_later` is the SOLE switch deciding whether `do_rivet` executes Rivet synchronously (`misc.call(Events/<run>/run_rivet.sh)`, common_run_interface.py:3091) or defers it to `postprocessing()` (appends run_name to `self.postprocessing_dirs`, 3087). Every "will Rivet run now or later" question reduces to: what is this flag's value at line 3074 (`postprocess_RIVET = rivet_config["run_rivet_later"]`)?

This page unifies the lifecycle scattered across do_rivet-flow.md (sets the flag + overrides), postprocess-and-contur.md (consumes it), and analysis-selection.md / install-and-config.md (default vs template discrepancy). It catches the cross-product the instance pages answer only one slice of.

## Where the value ORIGINATES (three sources, they disagree)
- `banner.py:1568` — `default_setup` initialises `run_rivet_later = False`. This is the value of a `RivetCard()` built with no file (e.g. `rivet_card_default = RivetCard()` at common_run_interface.py:5353).
- `Template/LO/Cards/rivet_card_default.dat:26` — the SHIPPED template carries `run_rivet_later = True`. So a fresh process dir's actual `rivet_card.dat` defers by default. (Probe-confirmed: `RivetCard()` with no file gives False; the template file string is `True`.)
- `init_rivet` fast_rivet shortcut (common_run_interface.py:5346) sets `run_rivet_later True` (plus uncompressed hepmc, no plots, mpi off) — the scan-optimised macro.

KEY non-obvious point: default_setup=False but the on-disk template=True. The flag a run actually sees is the TEMPLATE's True unless the card was edited or an override fires.

## Two overrides FORCE run-now (False), regardless of card value
1. `common_run_interface.py:2974-2975` — `if not no_default: rivet_config['run_rivet_later'] = False`. A MANUAL `rivet RUN` command (typed interactively / via exec_cmd without `--no_default`) always runs now. The post-shower auto-call uses `rivet --no_default` (madevent_interface.py:2670), so `no_default=True` there and the card value is honoured (defers).
2. `common_run_interface.py:3071-3072` — `if ("remove" in py8_output) or ("fifo" in py8_output): run_rivet_later = False`. hepmcremove and fifo HEPMCoutput modes CANNOT be deferred (the hepmc is consumed/streamed immediately), so they always run now.

## Consumption (the branch chosen)
`do_rivet` 3074-3093:
- `postprocess=True` (called from `postprocessing()`): returns `[rivet_config, postprocess_RIVET, postprocess_CONTUR]`, runs nothing (3080-3082).
- else `postprocess_RIVET` truthy: log "Skipping Rivet for now, passing it to postprocessor", append run_name to `postprocessing_dirs`, return (3084-3088) — DEFER.
- else: `misc.call(run_rivet.sh)` — RUN-NOW (3090-3091).

Then `postprocessing()` (madevent_interface.py:2411) re-invokes `do_rivet(..., postprocess=True)` and, if `postprocess_RIVET or postprocess_CONTUR`, calls `rivet_postprocessing` which cluster-submits each deferred `run_rivet.sh` (madevent_interface.py:2433-2434). See postprocess-and-contur.md.

## Decision table (re-executed from the source expressions above)
| invocation | no_default | hepmc output | card flag | outcome |
|---|---|---|---|---|
| scan / launch post-shower point | True | hepmc(.gz) | True (template) | DEFER |
| manual `rivet RUN` | False | hepmc(.gz) | True | RUN-NOW (override 1) |
| any | True | fifo | True | RUN-NOW (override 2) |
| any | True | hepmcremove | True | RUN-NOW (override 2) |
| card edited to False | True | hepmc(.gz) | False | RUN-NOW |

This explains the common surprise: an interactive `rivet RUN` executes immediately even though `rivet_card.dat` says `run_rivet_later = True` — override 1 fires.

## Boundaries
- This governs the control-flow BRANCH chosen (deterministic from the flag; source-verified line-for-line + decision-table re-execution probe). It does NOT cover what happens INSIDE the RUN-NOW branch when Rivet is uninstalled — `run_rivet.sh` would fail at the fastjet `--prefix`/rivet_path env steps (this image ships no rivet; see install-and-config.md). That is a separate runtime claim, not predicted here.
- Contur deferral is SEPARATE: `postprocess_CONTUR = run_contur` (3075), keyed off `run_contur`, NOT `run_rivet_later`. A run with `run_rivet_later=False` but `run_contur=True` still triggers `rivet_postprocessing` via the `postprocess_RIVET or postprocess_CONTUR` gate (madevent_interface.py:2419).

## Instances generalized
- do_rivet-flow.md "Run-now vs postprocess (3071-3093)" — the override + branch side.
- postprocess-and-contur.md "Deferral logic recap" — the consumer side.
- analysis-selection.md / install-and-config.md — the default_setup-False vs template-True discrepancy.
