---
description: The runtime AUTO-width detection trigger — static_check_param_card regex-detects DECAY <pid> auto[@NLO] at card-edit time and dispatches static_compute_widths → the compute_widths engine, plus the too-small-width s-channel-resonance warning thresholds.
---

# Runtime AUTO-width detection trigger (v3.7.1)

All citations `madgraph/interface/common_run_interface.py` unless noted. This page owns how a `DECAY <pid> auto` line in the operative param_card actually TRIGGERS a width computation at launch/card-edit time — the runtime counterpart to the restriction restore loop (`autowidth-restriction-callback`, which puts the `auto` string back into the card) and the MadSpin wrapper (`compute-widths-flow`, the `do_compute_widths` at 7301). This is the canonical "AUTO width gets computed when you finish editing the cards" mechanism, and it is distinct from the bare REPL `compute_widths` (which requires explicit particle args and does NOT auto-scan — see compute-widths-flow particle-selection section).

## static_check_param_card (3740) — the auto-detect + dispatch
Called via `check_param_card` (3719) during the runtime card-validation flow. Two-stage regex over the raw param_card text:
- `pattern_scan = re.compile(r'''^(decay)?[\s\d]*scan''', re.I+re.M)` (3742) — scan blocks (handled by a ParamCardIterator, not our slice).
- `pattern_width = re.compile(r'''decay\s+(\+?\-?\d+)\s+auto(@NLO|)''', re.I)` (3743) — the AUTO-width detector. Same regex as the MadSpin wrapper (7301) and the SMWidth-routing regex (nlo-smwidth-width-path): one capture for the pid, one optional `@NLO` suffix.
- `pdg_info = pattern_width.findall(text)` (3757). If non-empty AND `run=True` (3758-3759):
  - `logger.info('Computing the width set on auto in the param_card.dat')` (3760).
  - `has_nlo = any(nlo.lower()=="@nlo" for _,nlo in pdg_info)` (3761) — ANY `auto@NLO` line flips the whole call to `--nlo` (3763-3766: `if not has_nlo: line=...` else `line = '%s --nlo' % ...`). So a single `@NLO` pid routes the entire dispatch to SMWidth (nlo-smwidth-width-path); the engine is NOT chosen per-pid.
  - `CommonRunCmd.static_compute_widths(line, interface, path)` (3767) — dispatch.
- If `run=False` (card-editing not yet finished, 3768): logs only the deferred-computation notice ("Those will be computed as soon as you have finish the edition of the cards. ... you can type \"compute_wdiths\"" — note the typo `compute_wdiths` is in the source, 3769-3772) and does NOT compute. So the actual compute fires on the `run=True` validation pass, after the user finishes editing.

## static_compute_widths (3805) — the factory dispatch
Tries, in order, to reach a compute-widths engine:
- `isinstance(interface, CommonRunCmd)` (3809) → append `path` to the line (3810-3811) and call `interface.do_compute_widths(line)` (3812) — the runtime wrapper (2428), which builds a child `MasterCmd` and forwards `compute_widths <particles> --opts` to the real LO/NLO engine (compute-widths-flow). THIS is the live launch path.
- Fallbacks (3819-3838): `do_compute_width` (sic, singular) attr (3819); an `interface.mother` (3821); or, if not in MADEVENT (3823), spin up a fresh `MasterCmd` and `cmd.exec_cmd(line, model=model)` (3838).
- `raise Exception('fail to find a way to handle Auto width')` (3845) if none apply.

So the runtime AUTO trigger always funnels to the same `compute_widths` engine on compute-widths-flow — the regex detection is the only thing this layer adds over the REPL path.

## Too-small-width s-channel-resonance warning (3776-3799) — AFTER computation
Once widths are populated, `static_check_param_card` walks `card['decay']` and warns on widths that are too small to be a stable s-channel resonance:
- Skip `width == 0` and missing-mass pids (with a `logger.warning('Missing mass in the lhef file ...')`).
- `if mass and abs(width/mass) < <floor>:` (3788, read the literal there) → `logger.error('The width of particle %s is too small for an s-channel resonance (%s)...numerical instabilities')` (3791/3793). The threshold is a dimensionless `width/mass` floor (read at :3788).
  - If the interface has a `RunCardLO` run_card AND `small_width_treatment` is below that same floor (3790-3791): a sharper error noting small_width_treatment can't rescue it. Otherwise (3793) the generic too-small error.
- `if CommonRunCmd.sleep_for_error: time.sleep(5)` (3794-3796) — a deliberate 5 s pause so the error is seen.

This is a DOWNSTREAM CONSUMER of the computed width (does the width support an s-channel BW), not part of the computation — it is at the slice edge. The `small_width_treatment` run_card parameter and the BW s-channel numerics are the bw-window / run-card slices; we own only that the auto-width pipeline's OUTPUT is what this check reads.

## Distinct from the other two too-small-width checks
Three different small-width warnings live in this file — do not conflate:
1. **static_check_param_card** (3788, here): `width/mass` below the floor literal at :3788 after auto-detect/compute, s-channel-resonance framing.
2. **MadSpin wrapper do_compute_widths** (7331-7336): after computing, `total/mass < small_width_treatment` (run_card) → warn; below a hardcoded critical floor (read at 7331-7336) → critical. (compute-widths-flow page.)
3. **A third at 6527-6530** (`abs(width/mass) < small_width_treatment` at 6527, then a hardcoded floor at 6530) in another card-check path. Same s-channel-resonance error text.
They share the resonance-instability message but differ in threshold (a hardcoded literal at :3788 / :6530 vs `small_width_treatment` vs a hardcoded critical literal at 7331-7336 — read each at its cited line) and trigger context.

## Cautions
- **The runtime trigger is regex-on-text, not a model-attribute scan.** It reads the raw `DECAY <pid> auto[@NLO]` lines from the param_card file; a model whose card has been rewritten to a numeric width (already computed) shows no `auto` lines and triggers nothing. The `auto` string must survive in the WRITTEN card for the runtime trigger to fire — which is exactly what the restriction restore loop guarantees (autowidth-restriction-callback).
- **Any single `auto@NLO` line routes the WHOLE dispatch to `--nlo`** (3761-3766) — the EW-scheme/SMWidth engine, total-width-only, BR table wiped (nlo-smwidth-width-path). Mixing `auto` and `auto@NLO` pids in one card sends all of them through SMWidth, not just the `@NLO` one.
- **`run=False` defers, does not skip.** During interactive card editing the detector only logs the deferred notice; the compute fires on the post-edit `run=True` pass. A user who never completes the edit flow gets no width.
- The source contains a literal typo `compute_wdiths` in the deferred-notice text (3772) — harmless, but don't expect a clean command name in that log line.

## Boundary
- The `compute_widths` engine itself (two-stage FR/MadEvent, survey, write-back): compute-widths-flow.
- The `--nlo`/SMWidth branch the `@NLO` suffix selects: nlo-smwidth-width-path.
- How `auto` survives restriction into the written card (so this regex can find it): autowidth-restriction-callback.
- `small_width_treatment` run_card semantics and the s-channel BW numerics the warning guards: bw-window / run-card slices (we own only that our pipeline's output feeds the check).
- The scan-block handling (`pattern_scan`): the param-card / scan slice, not ours.
