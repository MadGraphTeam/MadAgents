---
description: Operational meaning of suspect-number / numerical-quality indicators — RunStatistics (EPS/UPS/skipped_subchannel), chi2/dof, negative-weight handling, where each surfaces. v3.7.1.
---

# Suspect numbers & numerical-quality indicators (v3.7.1)

Sources: `sum_html.py` `RunStatistics` (36); `gen_ximprove.py` `warnings_from_statistics` (835), `combine_grid` instability-security (722). What the indicators mean operationally.

## RunStatistics (sum_html.py:36) — the MadLoop/run quality dict
Default keys (43-68) include stability counts and reduction-tool usage. Loaded from results.dat XML `run_statistics` node (load_statistics, 109). Key indicators:
- `n_madloop_calls` — total ME evaluations (loop-induced/NLO). If 0, all stability reporting is suppressed (nice_output returns '' at 162; warnings_from_statistics no-ops at 838). So **LO tree processes carry no EPS/UPS numbers**.
- `exceptional_points` (EPS) — points that even quad precision could not rescue. `EPS_fraction = exceptional_points/n_madloop_calls`.
- `unstable_points` (UPS) — points needing rescue. `UPS% = unstable_points/n_madloop_calls` (nice_output 168).
- `skipped_subchannel` — count of subjobs discarded by the instability-security (one large-weight event). Incremented in combine_grid (gen_ximprove.py:761).
- `min_precision`/`max_precision` — note the inversion: smaller PREC value = higher precision, so aggregate uses min/max swapped (93-98).

### EPS thresholds (warnings_from_statistics, 848-852)
- `0.001 < EPS_fraction < 0.01` → `logger.warning` "results might not be trusted".
- `EPS_fraction > 0.01` → `logger.critical` + **raises Exception** (run aborts). So >1% exceptional points is fatal.

### has_warning / get_warning_text (211, 228)
Warning if `skipped_subchannel>0` OR `EPS_fraction > 1e-4`. get_warning_text reports the discarded-event count and the zero-ME PS fraction.

### aggregate_statistics (sum_html.py:75) — how the indicators COMBINE across channels/jobs
The per-channel/per-job RunStatistics are merged into the run total here. The combination rule is **key-specific** (the per-key `if/elif/else` is 91-107) — not everything sums:
- `max_precision` → `min(...)` and `min_precision` → `max(...)` across the stats (93-98). This is the same swap noted below: PREC is a magnitude where *smaller = more precise*, so the run's "best" precision is the min PREC and "worst" is the max PREC. The dict key names are inverted relative to the reduction (the `min_precision` key holds the `max` PREC value).
- `averaged_timing` → **n_madloop_calls-weighted average**: `sum(t_i * calls_i)/sum(calls_i)` (99-104), guarded on `n_madloop_calls>0`. So a channel with more ME calls dominates the reported per-call timing.
- **all other keys** → plain `sum` (else branch, 105-107): `n_madloop_calls`, `exceptional_points`, `unstable_points`, `skipped_subchannel`, the reduction-tool usage counts, etc. are cumulative.
Consequence: the run-level `EPS_fraction = sum(exceptional_points)/sum(n_madloop_calls)` is a call-weighted aggregate, not a per-channel mean — one channel with many calls and few EPS can mask another channel's high local EPS rate in the headline fraction. `skipped_subchannel` at run level is the total discard count across all channels.

## skipped_subchannel — the "large weight discarded" indicator
Set when combine_grid's instability-security fires: a channel with `rel_contrib>1e-8`, `nunwgt<2`, `>1` subjob, and the two largest subjob `th_maxwgt` differing by ratio>1e4. The worst subjob is dropped and its max-weight event archived to `<Pdir>/DiscardedUnstableEvents/discarded_G<G>.dat`. Operationally: "one PS point blew up the integral (usually loop instability); we threw away the offending job to recover." nice_output appends a WARNING line (205-207).

## chi2/dof — cross-iteration consistency
The combined per-channel error (iteration-combination page) folds in `chi2/cross^2 - sigma` over `(step-1)` (gen_ximprove.py:795). A large chi2/dof means iterations disagree beyond their statistical errors — grid not yet converged / unstable integrand. Surfaces in the final `results.dat` and HTML cross-section page.

## Negative-weight fraction (operational)
- LO with a BIAS module or interference/EFT can produce signed weights; `combine_runs.copy_events` (combine_runs.py:183-203) preserves the sign when rescaling and re-unweighting, comparing `abs(new_wgt)` against `random*max_wgt`. The combined `xsec` (signed sum) vs `axsec` (sum of |wgt|) ratio is the practical negative-weight indicator: `xsec/axsec` well below 1 ⇒ large cancellation / negative-weight fraction. (Detailed NLO negative-weight machinery is amcatnlo/fks territory; this slice covers only the LO event-combination sign handling.)

## Cautions
- EPS/UPS are meaningless for LO tree processes (n_madloop_calls==0) — do not expect them in plain LO runs.
- `EPS_fraction>0.01` aborts the run by exception, not just a warning.
- `skipped_subchannel>0` is silent unless you read the log/HTML warnings; the discarded events live under DiscardedUnstableEvents for offline study.
