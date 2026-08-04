---
description: MC-over-helicity (nhel==1) inflates per-iteration event budgets by 2**(nexternal//3) (refine max-iter ceiling by 2**(nexternal//2)) — the four code sites + arithmetic. v3.7.1.
---

# MC-over-helicity event-budget multipliers (v3.7.1)

File: `$MADGRAPH_INSTALL/madgraph/madevent/gen_ximprove.py`.

## The principle
When Monte-Carlo-over-helicity is active — the resolved `helicity`/`nhel` integration option equals **1** (sample one random helicity per PS point rather than the exact sum) — every requested per-iteration **event budget is inflated by `2**(nexternal//3)`**, and in the high-precision refine path the **max-iter ceiling is additionally inflated by `2**(nexternal//2)`**. Rationale: each PS point now carries only one helicity, so more points are needed for the same statistical accuracy; the factor grows with the number of external legs.

This is the single rule behind four otherwise-scattered code sites. The gate is always `int(helicity)==1` (or `int(self.nhel)==1`); `nexternal` comes from `proc_characteristics['nexternal']`.

## The four sites (all gated on helicity/nhel == 1)
- **Survey, initial submission** (~968-969): `options['event'] *= 2**(nexternal//3)`.
- **Survey, resubmit_survey** (913-914): `options['event'] *= 2**(nexternal//3)`. Base event (903) is `2**step * opts['points'] / splitted_grid`.
- **Refine increase_precision** (1221-1223): `min_event_in_iter *= 2**(nexternal//3)`; `max_event_in_iter *= 2**(nexternal//2)`. NB the **divergence**: min uses `//3`, max uses `//2`. This is the only site where the ceiling gets the larger `//2` factor.
- **share variant (loop-induced)** inherits the same survey path; refine event arithmetic uses min/max_event_in_iter, so the `increase_precision` multipliers carry through there too.

The helicity option itself is `run_card['nhel_survey']` if present else `run_card['nhel']` (907-908, 962-963) for the survey paths.

## Probe-verified arithmetic (v3.7.1)
Reproduced the verbatim `resubmit_survey` expression (`2**step * points/splitted_grid`, then `* 2**(nexternal//3)` if helicity==1) and the increase_precision multipliers for real `nexternal` values:

| nexternal | event factor `2**(n//3)` | precision max factor `2**(n//2)` |
|---|---|---|
| 4 | 2 | 4 |
| 5 | 2 | 4 |
| 6 | 4 | 8 |
| 8 | 4 | 16 |

The factor lands in the first field of `G<N>/input_app.txt` (the "Number of events" field; template `write_parameter_file` 942-949), so it is directly observable per channel.

## Boundary / cautions
- This is independent of helicity *recycling* (the `get_helicity` discovery + `HelicityRecycler` source transform). Recycling runs regardless of `nhel`; this multiplier fires only on the MC-over-helicity integration mode. See helicity-recycling.md.
- `nhel==1` is MC-over-helicity; `nhel==0` is exact helicity sum (no multiplier). Field meaning confirmed in input_app.txt ("Helicity Sum/event 0=exact").
- The `//3` vs `//2` split (min vs max event-in-iter) at 1221-1223 is deliberate, not a typo: it widens the iteration's event range under MC-helicity.
