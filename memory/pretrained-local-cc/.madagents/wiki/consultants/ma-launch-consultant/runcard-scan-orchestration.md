---
description: run_card `scan:` orchestration — detection, RunCardIterator eval/product loop, run-dir naming (run_NN_01..), Events/scan_*.txt summary, and the v3.7.1 MultiCore thread lifecycle (thread-leak is fixed).
---

# run_card `scan:` orchestration (LO)

**Scope:** LO run_card scans — I own the run_card scan LOOP + how run_mode selects/reuses the MultiCore backend + its thread lifecycle. param_card scan PARSE + ParamCardIterator = ma-param-card-consultant; run_mode/nb_core/crash_on_error config keys = ma-interface-consultant.

Scans over a **run_card** value (e.g. `scan:[6500,7000,7500] = ebeam1`). Distinct from param_card scans (ParamCardIterator, ma-param-card slice) though both flow through the same `scanparamcardhandling` decorator.

## Detection + registration
- `RunCard.__setitem__` (banner.py:1122): a string value `.startswith('scan')` registers the key in `self.scan_set` (name→python type of current value) **only when `allow_scan` is True**. `allow_scan` default False (banner.py:977); flipped True while a `RunCardIterator` reads the card (banner.py:6414).
- run_card + param_card cannot BOTH carry a scan simultaneously (banner.py:1518-1519 raises InvalidCmd).
- Web mode forbids run_card scan (security, common_run_interface.py:3748-3750 path in param-card handler; the eval is the reason).

## Orchestration entry (LO)
- `run_generate_events` (madevent_interface.py:2564) is decorated `@common_run.scanparamcardhandling(run_card_scan=True)`. (NLO analog: amcatnlo_run_interface.py:1837.)
- Decorator `new_fct` (common_run_interface.py:7957): line **7980** `if run_card_scan: scan_over_run_card(...)`.
- `scan_over_run_card` (7904): builds `run_card_iterator = RunCardIterator(card_path)` (7911); **if `run_card.scan_set` is empty → just `return original_fct(...)`** (7913-7914) = one normal run. Otherwise loops (7936): per iteration `card.write(card_path)` → `get_next_name` → `set_run_name` → `original_fct` (the full survey/refine/combine body) → `store_entry`. The original card is restored on exit via `restore_iterator` (7917).
- So a run_card scan is **ONE `run_generate_events` call**; the loop re-runs the body on the **same MadEventCmd obj** — no new mg5 subprocess, no new cluster object per point.

## The eval + the loop (RunCardIterator.iterate, banner.py:6450)
- Regex `scan\s*(?P<id>\d*)\s*:\s*(?P<value>[^#]*)` (6453) splits each scanned entry into `id` + `value`.
- **`eval(def_list)`** (6468) on the captured value → any python expression producing a list is accepted (`[6500,7000,7500]`, `range(...)`, list-comprehension, …).
- Keys = scan ids. Bare `scan:` (empty id) gets a **distinct** key each: `key = -1*len(all_iterators)` (6464). Same explicit `scanN:` id groups params under one key.
- **Loop: `itertools.product(*lengths)`** (6483), one `lengths` entry per KEY. Same key → all its params advance with the **shared index `pos`** (6487-6491) = LOCKSTEP/correlated. Different keys → CARTESIAN product. ⇒ multiple bare `scan:` = product; same numbered `scanN:` = lockstep. (CONFIRMED claim.)

## Run-directory naming — CORRECTED
- `scan_over_run_card`: `orig_name = run_name` (e.g. `run_01`); `next_name = orig_name + "_00"` (7934); each iteration `next_name = get_next_name(next_name)` (7940).
- `get_next_name` (banner.py:6572): `rsplit('_',1)`; if trailing token `.isdigit()` → `'%s_%02i' % (name, float(value)+1)`. So `run_01_00`→`run_01_01`→`run_01_02`→…
- **Scan points are named `run_01_01, run_01_02, run_01_03, …`** — NOT `run_01_scan_02`. The `%s_scan_02` fallback (6580) is **unreachable** in the run_card path because `_00` is always appended first → trailing token is always a digit. (Doc claim `run_01_scan_02` is wrong for run_card scans; that form belongs to other naming paths.)

## Summary table
- `result_path` default `pjoin(me_dir,'Events','scan_%s.txt')` (7847). `name = misc.get_scan_name(orig_name, next_name)` (7950) → a bracketed common-prefix form like `run_[01_01-01_0N]`. Summary written to **`Events/scan_<name>.txt`** (7951-7954).
- `write_summary` (banner.py:6516): header row = `run_name` + `param_order` (each `run_card#<param>`) + result keys (`cross(pb)`, `error(pb)`, and any scale/PDF entries from `store_scan_result`); one data row per point. Also writes a per-point **`Events/<run_name>/params.dat`** (6563-6566) listing the scanned param values.

## Practical claims (claim 5)
- **(a) seed**: the scan only rewrites the run_card with the new scan value; `iseed` is unchanged across points. Points get *different* seeds only if `iseed=0` (auto-seed per run — see nevents-iseed-and-zero-events page), NOT because of any scan-specific mechanism.
- **(b) grid reuse**: FALSE at the launch/orchestration level. `scan_over_run_card` calls `original_fct` (a full fresh survey+refine) each point; it carries NO integration grid between points. (Grid reuse is the separate gridpack mechanism.)
- **(c) nevents per point**: the full `run_generate_events` body runs per point ⇒ `nevents` events generated **per point** (unless `nevents` itself is the scanned param).

## Thread-leak — v3.7.1 CORRECTED (was: stale doc claim)
Doc claimed multicore mode leaks unjoined threads → `ulimit -u` exhaustion after ~25-50 sequential launches (fixed 2.9.13/3.4.2). In v3.7.1 the fix IS present, two layers:
1. **`MultiCore.wait()` end** (cluster.py:964-965): `if not self.keep_thread: self.stoprequest.set()`. `keep_thread` default False (cluster.py:672). Setting `stoprequest` makes each worker's `while not self.stoprequest.isSet()` loop (717) exit; the worker then self-removes from `self.demons` (787) → daemon thread terminates. Threads are torn down after **every** wait (not explicitly joined, but they exit; daemon=True at 709). On the next `submit`, `stoprequest.clear()` (795) + `start_demon()` re-create up to `nb_core` workers.
2. **MultiCore reuse** (common_run_interface.py:3687-3692, `configure_run_mode`): a new `MultiCore` is built **only** if none exists or `nb_core` changed; otherwise the existing one is reused. ⇒ one thread pool per session/obj, not per launch.
Combined with the single-obj scan loop above, a run_card `scan:` incurs **no per-point thread-pool spawn**. Conclusion: the "threads not joined → crash after N launches" root-cause is stale; do not repeat it for v3.7.1.

## nestscan / MultiNest — NO core hook (plugin-owned)
- `grep -rn "nestscan\|multinest\|MultiNest\|pymultinest\|nested_sampl"` over `madgraph/` returns **ZERO hits** (v3.7.1). There is NO core launch-side switch, no menu entry, no run_card key, no RunCardIterator branch for nested-sampling/Bayesian scans.
- A `nestscan = ON` launch-menu switch + `multinest_card.dat` + PyMultiNest is entirely **plugin-owned** (MadDM/similar) — out of the launch slice. The core scan machinery is ONLY the grid-scan `RunCardIterator`/`ParamCardIterator` (`itertools.product` over explicit lists), no sampler.

## Scan filename — CORE pattern, not `scan_run_NN.txt`
- `grep -rn "scan_run" madgraph/` returns **ZERO hits**. Core NEVER writes `scan_run_NN.txt` / `output/scan_run_NN.txt`; that pattern is a plugin (MadDM) convention.
- Core writes **`Events/scan_<name>.txt`** where `<name> = get_scan_name(orig,next)` (bracketed common-prefix like `run_[01_01-01_0N]`), from `result_path=lambda obj: pjoin(obj.me_dir,'Events','scan_%s.txt')` (common_run_interface.py:7847) → `result_path(obj) % name` (7951). Per-point run dirs are `run_NN_01, run_NN_02, …` (get_next_name, banner.py:6572-6578).

## Cross-slice
- param_card `scan:` parse + `ParamCardIterator` → ma-param-card-consultant. **Separate class** (`models/check_param_card.py:931`, `class ParamCardIterator(ParamCard)`) — NOT shared code with RunCardIterator (banner.py:6407). Run_card path is selected via the decorator's `run_card_iteratorclass=RunCardIterator` override (default `iteratorclass=ParamCardIterator`). The `scanN:` lockstep / bare-`scan:` cartesian key semantics are implemented independently in RunCardIterator.iterate (banner.py:6453-6491); whether ParamCardIterator replicates them identically is param-card slice's call.
- `run_mode` / `nb_core` / `crash_on_error` config-key semantics → ma-interface-consultant. I own only how `run_mode ∈ {0,2}` selects/reuses MultiCore in cluster.py and the thread lifecycle.
