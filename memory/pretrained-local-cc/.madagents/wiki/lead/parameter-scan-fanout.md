---
description: The deliverable is a curve or table over a parameter rather than a single point. A sweep across values.
---

# Parameter-scan fan-out (run_card / param_card `scan:` sweeps)

## When this applies
Any request to scan/sweep a parameter across values: `scan:[...]` or `scanN:[...]` in a run_card or param_card, "scan the top mass / a coupling / beam energy", multi-point cross-section tables, correlated vs independent scans, or the classic "many sequential `launch` commands crash with `can't start new thread`" symptom.

## Owner map — dispatch by which card / layer the claim touches
Dispatch **param-card + launch in parallel** (the two card sides own the scan mechanism); add **interface** only when the question touches `run_mode`/`nb_core`/`crash_on_error` or the thread-crash.

- **param_card `scan:`/`scanN:` parse + `ParamCardIterator`** — the `eval()` of the list, lockstep-vs-product semantics, both-cards precedence, per-point `params.dat` + summary table → **ma-param-card-consultant** (`scan-and-auto-detection`).
- **run_card `scan:` loop orchestration** — `RunCardIterator`, scan-point run-dir naming, `Events/scan_*.txt` summary, MultiCore thread lifecycle → **ma-launch-consultant** (`runcard-scan-orchestration`, `cluster-submission-backends`).
- **config keys + interface option** — `run_mode`/`nb_core` are `mg5_configuration.txt` keys (NOT run_card params; set BEFORE `launch`), `crash_on_error` is a pre-launch interface `set` → **ma-interface-consultant** (`config-system`, `command-loop-machinery`).

## Verified traps (doc-myth busters — grounded in the consultant pages cited)
1. **"Error if `scan:` is in both cards" is a MYTH.** No cross-card guard exists. A param-card scan silently **pre-empts** a run_card scan (the run-card-scan branch is reachable only `if not param_card_iterator`); the leftover run_card `scan:` literal is simply skipped. → param-card `scan-and-auto-detection`.
2. **Scan-point run-dir naming is `run_NN_01, run_NN_02, …`** (digit-suffix increment via `get_next_name`), **NOT** `run_NN_scan_02`. The `_scan_NN` fallback is unreachable because a `_00` suffix is always appended first. → launch `runcard-scan-orchestration`.
3. **The sequential-`launch` thread-leak is FIXED in v3.7.1.** `MultiCore.wait()` sets `stoprequest` (gated by `keep_thread`, default False) so daemon workers terminate after each wait, and the pool is reused per session unless `nb_core` changes. Do NOT repeat the stale "unjoined threads exhaust `ulimit -u` after 25–50 launches" root-cause — it does not apply here. → launch `runcard-scan-orchestration` / `cluster-submission-backends`.
4. **"Grid reuse makes later scan points faster" is FALSE at orchestration.** Each run_card scan point runs a full fresh survey+refine; no integration grid is carried between points. → launch `runcard-scan-orchestration`.
5. **Correlated vs independent:** same numbered id `scanN:` on several params → **lockstep** at a shared index (axis length = the group's FIRST list; unequal member lengths are NOT validated → IndexError or silent truncation). Bare `scan:` → each gets a distinct axis → **cartesian product**. → param-card `scan-and-auto-detection`, launch `runcard-scan-orchestration`.
6. **`crash_on_error` default is `False`.** `True` → non-zero exit (mechanism `__debug__`-dependent: `raise` in dev vs `sys.exit(str)` under `-O`); `'never'` → continue past the error. Default-False in NON-interactive mode is a **clean `do_quit('all')` stop (exit ~0)**, not a silent-continue — the "may exit 0 / continue silently" framing conflates modes. It is a pre-launch config `set`, distinct from a card-dialogue `set`. → interface `config-system` / `command-loop-machinery`.

## Return-interpretation hint
A "clean run per point" is NOT evidence the scan swept the intended values. Check the `Events/scan_*.txt` summary row count against the expected combinatorics (cartesian vs lockstep) and the per-point `params.dat`, per the clean-run discipline.
