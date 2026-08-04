---
description: Python small_width_treatment warning/error surface in common_run_interface.py — the user-visible FAQ-3053 small-width warnings + <1e-12 error/critical escalation tiers that the hidden run-card knob gates, v3.7.1
---

# small_width_treatment Python warning surface (common_run_interface.py)

Cite `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py`, v3.7.1. My other pages
cover the Fortran reach of `small_width_treatment` (Γ_eff floor in cut_bw/set_peaks, the NWA
jacobian in transpole.f) and its banner.py registration (hidden, default at banner.py:4452,
bw-runcard-knobs.md). This page covers the **Python layer** that turns the same hidden knob
into user-visible warnings at card-check / width-compute time — the thing a user actually
SEES that tells them small_width_treatment is in play. Not derivable from the Fortran pages.

The run-card key is read as `run_card['small_width_treatment']` (the registered LO param).
String checks below are verbatim-confirmed in source (parse-level probe: all five
literal strings FOUND).

## Three warning sites, three thresholds, three severity tiers

### 1. `check_card_consistency` — :6485, warning block :6525-6535
At card-consistency check (before launch). For each param-card width with mass:
- `abs(width/mass) < run_card['small_width_treatment']` → **WARNING** (:6527-6528):
  *"Particle %s with small width detected (%s): See
  https://answers.launchpad.net/mg5amcnlo/+faq/3053 to learn the special handling of that case"*.
  This is the small_width_treatment-gated warning — pointing at FAQ 3053 (the NWA/small-width
  handling explainer).
- elif `abs(width/mass) < 1e-12` → **ERROR** (:6531): *"too small for an s-channel resonance …
  numerical instabilities"* (the hard floor, independent of the run-card value).
- else → no message; `to_sleep=False`. When a warning/error fired and
  `CommonRunCmd.sleep_for_error`, sleeps 5s (:6534-6535).

### 2. `do_compute_widths` — :7292, block :7325-7337
After computing widths (compute_widths command). For each pid, `total/mass` vs threshold:
- `total/mass < small_width_treatment` → **WARNING** (:7332): *"Particle %s with very small
  width (%g): Learn about special handling here:
  https://answers.launchpad.net/mg5amcnlo/+faq/3053"*.
- elif `total/mass < 1e-11` → **CRITICAL** (:7336): *"… Numerical inaccuracies can occur if
  that particle is in a s-channel"* (note: 1e-11 here, NOT 1e-12).
- **NLO fallback (:7327-7329):** `try: small_width_treatment = run_card['small_width_treatment'];
  except Exception: small_width_treatment = 0`. At NLO the key is absent (NLO RunCard doesn't
  register it — bw-runcard-knobs.md), so it falls back to **0** → the small_width WARNING branch
  can never fire at NLO (nothing is `< 0`); only the 1e-11 critical can. Confirms the LO-only
  nature of the knob from the consumer side.

### 3. `static_check_param_card` — :3740 (called from check_param_card :3715), block :3788-3796
At param-card validation. For each width: if `abs(width/mass) < 1e-12` AND the interface has a
`RunCardLO`:
- `if run_card['small_width_treatment'] < 1e-12` → **ERROR** (:3790-3791): *"The width of
  particle %s is too small for an s-channel resonance (%s) and the small_width_treatment
  parameter is too small to prevent numerical issues …"*.
- This is the ONLY site that tests `small_width_treatment` against a constant (1e-12). The
  logic: a sub-1e-12 width is normally rescued by small_width_treatment's Γ_eff floor — but
  if the user ALSO lowered small_width_treatment below 1e-12, the floor can't help, so escalate
  to error. (Non-LO interface → plain error without the small_width_treatment clause, :3793.)

## Why this is load-bearing (the non-obvious part)
- The hidden small_width_treatment default (banner.py:4452 — read it there) is the threshold
  for the FAQ-3053 warning at check_card_consistency / compute_widths: any width with
  `width/mass < small_width_treatment` triggers the
  "small width detected, see FAQ 3053" warning at LO. So the same number that floors Γ_eff in
  the Fortran ALSO sets when the user gets warned — answering "why am I seeing a small-width /
  FAQ-3053 warning?" → because `width/mass < small_width_treatment`.
- Three distinct numeric thresholds across the surface: **small_width_treatment** (default at
  banner.py:4452, the run-card-gated warning), **1e-12** (hard error floor in check_consistency &
  param-card-check, common_run_interface.py:6531/:3790), **1e-11** (critical in compute_widths,
  :7336). They are not the same constant; don't conflate. (The 1e-12/1e-11 are hardcoded at
  those cited lines — read them there; only small_width_treatment is a run-card param.)
- Lowering small_width_treatment SILENCES the FAQ-3053 warning (fewer widths fall below it) up
  to the point where, if pushed below 1e-12, static_check_param_card escalates to an error
  instead. Raising it makes MORE widths warn.

## Boundary
- The Python warning surface is mine (it's the user-facing face of small_width_treatment).
  *What the FAQ-3053 special handling IS* numerically (the Γ_eff floor + NWA σ-reweight) lives
  in my Fortran pages (bw-transpole-nwa-jacobian.md, bw-runcard-knobs.md). *Width computation
  itself* (compute_widths / do_compute_widths internals) is the madwidth slice — I own only the
  small_width_treatment threshold check applied to its output.
- `matrix_madevent_v4.inc:259-260` (and the group/hel variants) merely DECLARE
  `common/narrow_width/small_width_treatment` so the matrix element sees the same common block —
  no new logic, just the block plumbing (recorded so a future grep hit there isn't chased).

## Caution (warning text read from source; firing condition probe-able)
- The warning STRINGS are verbatim from source (parse-level confirmed). WHETHER a given run
  emits them depends on the operative param-card width/mass ratio vs the operative
  small_width_treatment — a runtime condition. Cheap to probe (card-check time, no integration):
  set a width with width/mass < small_width_treatment (its default) and run
  check_card_consistency / compute_widths. Listed as
  a cheap probe candidate; not launched.
