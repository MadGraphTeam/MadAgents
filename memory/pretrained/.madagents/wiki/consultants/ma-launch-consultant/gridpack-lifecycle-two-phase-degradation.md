---
description: A gridpack is a CLASS substitution + two-phase degradation, not a single run_card flag. Phase A (warmup, outer MadEventCmd, run_card['gridpack'] truthy) special-cases the integration path; Phase B (event gen from the packed gridpack) runs in a different class GridPackCmd that no-ops update_status and forces cluster_mode=0. Locates the whole "why did my gridpack run do X" question class (silent / single-core / different accuracy / no refine / no unweighting) to one of these two phases.
---

# Gridpack lifecycle: two-phase degradation by class substitution

Cites `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (v3.7.1). Probe-verified (see Probe).

## The principle
"Gridpack" is not one run_card switch that tweaks one stage. It is **a class substitution plus a chain of independent degradations spread over two phases**:

- **Phase A — warmup** (build the gridpack). Runs inside the *normal* outer `MadEventCmd` instance, taken because `run_card['gridpack'] in self.true`. The class is unchanged; specific stages are special-cased.
- **Phase B — event generation from the packed gridpack** (`run.sh <nevt> <seed>` inside the extracted tarball). Runs inside a *different class*, `GridPackCmd` (6980), which overrides reporting/cluster behavior wholesale.

So "why did my gridpack run do X" almost always resolves to *which phase, and which override in that phase*. A user who knows only "I set gridpack=True" cannot predict the behavior without this split.

## Phase A — warmup degradations (outer MadEventCmd)
Driver: `run_generate_events` gridpack branch (2576-2592, launch-flow-orchestration page).
- Survey opts **hardcoded** at 2578-2581 (accuracy / points / iterations, plus gridpack=.true.) — overrides `_survey_options` defaults; integration quality is fixed here, not by run_card survey settings. Read the literal opts at the coordinate.
- Sequence survey -> combine_events -> store_events -> decay_events -> create_gridpack. **NO refine stage.**
- `do_combine_events` gridpack short-circuit (3780-3781, 3800-3801, combine-store page): after the banner write it **returns without unweighting** — that is why warmup combine shows `Nb of events: 0`.
- Phase A still uses the normal `update_status`, so it DOES emit `INFO: Combining Events` / `INFO: Storing parton level results` and a `=== Results Summary ===` with a real cross-section.

## Phase B — GridPackCmd degradations (class substitution)
Class `GridPackCmd(MadEventCmd)` (6980); `__init__` (6983) runs the gridpack immediately on construction.
- `self.run_mode = 0` (6989) and `self.options['automatic_html_opening'] = False` (6996).
- **`update_status` -> bare `return`** (7009-7010): silent. No live status logging, no HTML index updates, and the per-stage `INFO: Combining Events` / `INFO: Storing parton level results` lines are *suppressed* (they are emitted by update_status). The Phase-B run prints only bare command echoes `combine_events` / `store_events`.
- **`cluster_mode = 0` forced** (7145, "force single machine") inside the launch method — a gridpack always runs single-core locally, regardless of the configured `run_mode`. The `monitor` mode==0 guard means NO cluster-wait loop, so NO `Idle:/Running:/Completed:` line either.
- `do_combine_events` is itself overridden at the class level (7235).

## Restart phase (do_restart_gridpack, 2332-2376, gridpack-create page)
A third entry, not a third class: `restart_gridpack` resubmits channels via `gensym.resubmit`, then `decay_events` + `create_gridpack`, but **skips combine_events/store_events** (commented out, 2373-2374). And `--precision=<v>` crashes (2353 `split(1)` Py3 TypeError) — only the default min_precision path (no flag) runs.

## What this catches that the instance pages do not
The instances are scattered across launch-flow-orchestration (warmup opts), combine-store-compile-stages (combine short-circuit), monitor-status-and-shell-results (update_status no-op + cluster_mode=0), gridpack-create-and-restart (create/restart). This page is the locator: any of
- "no progress output / no HTML during gridpack" -> Phase B update_status no-op
- "gridpack ignored my run_mode 2 / cluster" -> Phase B cluster_mode=0 forced
- "gridpack used different accuracy / didn't refine" -> Phase A hardcoded opts + no-refine
- "warmup combine said 0 events" -> Phase A combine short-circuit (no unweighting in warmup)
- "combine_events printed without the usual INFO line" -> Phase B vs Phase A update_status difference
- "restart_gridpack skipped combine/store" -> restart entry, combine/store commented out
resolves here without re-deriving. The class-substitution framing also catches FUTURE GridPackCmd overrides: any method GridPackCmd overrides degrades Phase B silently relative to a normal run — check the class body, not the run_card.

## Probe (v3.7.1, a simple 2->1 process, gridpack=True) — mechanism confirmed
Structural observations (session-specific numbers dropped — they carry no reusable value; the contrast is the mechanism):
- Phase A warmup (`./bin/generate_events -f`): emitted `Idle/Running/Completed`, `INFO: Combining Events`, `INFO: Storing parton level results`, a `=== Results Summary ===` with a finite cross-section, and `Nb of events: 0` (warmup combine short-circuit), then `create_gridpack` -> `<run>_gridpack.tar.gz`; `grid_card.dat GridRun` left `.false.` after pack.
- Phase B (`run.sh <nevt> <seed>` on the extracted tarball): banner `using 1 processes` (single-core), NO `Idle/Running/Completed` line, NO `INFO: Combining Events`/`INFO: Storing` lines (bare `combine_events`/`store_events` echoes only), `Nb of events` = the requested count written to `Events/GridRun_<seed>/events.lhe.gz`. Confirms update_status no-op + cluster_mode=0.

## Boundary
- NOT the general launch-time-runcard-overrides lens — those gate on process/card characteristics *within one class*; gridpack *swaps the class* (Phase B), a stronger mechanism. Cross-ref, don't merge.
- NOT gensym/resubmit channel internals (mc-integration/phase-space slice).
- The systematics weight block printed during Phase B event gen is systematics-slice territory.
