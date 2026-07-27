---
description: Channel enumeration for N>2 body widths — body_decay int/float semantics, the apx_decaywidth estimator, the precision-driven find_channels_nextlevel loop, and min_br pruning.
---

# Channel enumeration & body_decay semantics (v3.7.1)

## body_decay int vs float — do_decay_diagram (madgraph_interface.py:10130, def line)
`level = float(args['body_decay'])` (10161), `min_br = float(args['min_br'])` (10163).
- **Integer >1** (10195-10206): `find_channels(part, level, min_br)` then collect amplitudes for 2..level. Computes ALL channels up to `level` final particles regardless of error.
- **Float** (10207-10234): `max_level = level // 1` (if <2 → set to 999, effectively unbounded); `precision = level % 1`. First `model.find_all_channels(2)`, collect 2-body; then loop `while part.get('apx_decaywidth_err').real > precision`: increment clevel, stop if `clevel > max_level`, else `find_channels_nextlevel(model, min_br)` + collect + `update_decay_attributes`.
- Default `body_decay` (read at madgraph_interface.py:1803): max_level = its integer part, precision = its fractional part. Default `min_br = (body_decay%1)/5` (madgraph_interface.py:1873).
- Particle with `width == 'zero'` (string) is skipped entirely (10191-10192).

## find_all_channels_smart (decay_objects.py:2856)
Model-level analogue used by some paths: 2-body for all unstable particles first (so 3-body can reuse 2-body widths), then `while part.get('apx_decaywidth_err') > precision: find_channels_nextlevel`, capped implicitly, finishing with a BR update. The 2-body-first ordering matters: higher-multiplicity error estimates reuse lower-level widths.

## find_channels_nextlevel (DecayParticle, decay_objects.py:810)
Extends every existing clevel-1 channel by one more final particle to build clevel channels. Stores both on-shell `(clevel, True)` and off-shell `(clevel, False)` ChannelLists. Widths of channels are accumulated into the mother particle DURING the search; BR/err are NOT computed here (done by update_decay_attributes).

## Approximate width estimator (the stop criterion's input)
- `Channel.get_apx_decaywidth` (decay_objects.py:4479): `Gamma = matrixelement_sq * ps_area * 1/(2M)` (4489-4491). M = |mass of initial particle|.
- `calculate_apx_psarea` (4431): recursive phase-space-area estimate. For 2-body, exact two-body PS formula with a symmetric factor `s_factor` (factorials over identical final-state ids, 4458-4476). For >2-body, recurse from the midpoint with a fudge factor `c_psarea`.
- `c_psarea` (decay_objects.py:3324 — read the literal there) — a constant correction factor for the crude N-body PS integration approximation.
- `get_apx_decaywidth_nextlevel` (4496): estimates the summed width the next level would add (used as numerator of the error ratio).
- `estimate_width_error` (decay_objects.py:437): `apx_decaywidth_err = sum(next-level apx widths at the final level) / apx_decaywidth`; 0 if stable, 1 if apx width still 0. This ratio is what the float-precision loop compares against.

## Channel deduplication — check_repeat + IdentifyHelasTag (decay_objects.py:1103, 4547)
The find_channels docstring step (c) requires that a new channel with identical particles is appended ONLY if not equivalent to an existing one. This is enforced by `check_repeat` (1103): it compares the channel's diagram `tag` against already-stored channels at the same `(clevel, onshell)`, bucketed by total final mass (`mass = 100*sum(final_mass_list)//1`, 1123) for speed. Equal tag + equal mass bucket → `repeat=True` → channel dropped. Prevents double-counting symmetric/identical-particle channels (e.g. the two orderings of a `g g` pair) in the width sum.
- The tag machinery is `IdentifyHelasTag` (4547), a `diagram_generation.DiagramTag` subclass. Its docstring notes channels with DIFFERENT mother particles can be structurally identical helas calls ("t > b w+ and w+ > c s~ are the same") — so the same compiled matrix element is reused across channels/particles. The channel's `helastag` field (3507, 3644) caches this; it drives both dedup and helas-call reuse in the survey output.
- `check_idlegs` (3783) flags whether a vertex has identical legs; sets the channel's `has_idpart` property (find_channels_nextlevel, ~870). `has_idpart` channels are the ones that need the `check_repeat` equivalence test; non-id channels are appended directly.

## min_br pruning
`min_br` (from option, default (body_decay%1)/5) prunes channels whose branching ratio falls below it during enumeration. Integer body_decay → min_br=0 → no BR pruning.

## min_br default: help-text vs code DISCREPANCY
The `compute_widths`/`calculate_decay_widths` help text (madgraph_interface.py:720, repeated 745) states min_br default = "precision (decimal part of the body_decay options) divided by **four**". The actual code (madgraph_interface.py:1873) divides by **5**: `options['min_br'] = (float(options['body_decay']) % 1) / 5`. The CODE is authoritative — the help-text divisor (4) disagrees with the code divisor (5); compute the default from the code formula at :1873, don't trust the help text.

## Cautions
- The apx_decaywidth is an ESTIMATE (crude PS + the `c_psarea` fudge (:3324) + scalarized Lorentz + hardcoded color table — full physics on the apx-matrixelement-estimator page) used only to DECIDE how many body-levels to enumerate; the FINAL width comes from MadEvent survey integration (see compute-widths-flow). Don't quote apx_decaywidth as the physical width.
- The min_br default documented in the help text (÷4) is wrong; code uses ÷5 (see above).
- For a float body_decay with max_level<2 the cap becomes 999 — a slowly-converging particle can enumerate very high multiplicities. The integer-part cap is the guard.
- precision (channel-count stop) ≠ precision_channel (survey integration accuracy; default in the defaults dict at madgraph_interface.py:1802-1804).
