---
description: PRINCIPLE — apx_decaywidth (and apx_br / apx_decaywidth_nextlevel) is consumed ONLY by control-flow gates and diagnostic displays, never by the param_card write-back; the verbose channel dump's "(width = ...)" is the estimate, not the partial width.
---

# apx_decaywidth is a gate, not a width (v3.7.1)

All citations `mg5decay/decay_objects.py` unless noted. This page lifts the recurring caution that lives as a one-line warning on three instance pages (channel-enumeration-bodydecay, channel-to-amplitude-bridge, apx-matrixelement-estimator: "Don't quote apx_decaywidth as the physical width") into the underlying principle, and enumerates EVERY apx consumer so the trap is caught wherever it appears — including consumers no instance page names.

## The principle
`apx_decaywidth` and its derivatives (`apx_br`, `apx_decaywidth_nextlevel`) are the crude analytic estimate (equal-energy-sharing |M|^2 + the `c_psarea` PS fudge (decay_objects.py:3324) + hardcoded color table — see apx-matrixelement-estimator). They exist to make CONTROL-FLOW decisions and to populate DIAGNOSTIC output. **None of them ever reaches the param_card width.** The written width comes exclusively from the MadEvent survey `_results.dat` value via `collect_decay_widths` → `update_width_in_param_card` (madevent_interface.py:2983-2995): `result = float(results.strip().split(' ')[0])` is read from the subprocess survey output — apx_decaywidth is a different variable on a different object (the `mg5decay` Channel) and is structurally absent from that data path.

## Every apx consumer is a gate or a display — the complete list
1. **Enumeration-depth stop** (float body_decay): `while part.get('apx_decaywidth_err') > precision` — find_all_channels_smart (2918, 2923); estimate_width_error (437-456) builds `apx_decaywidth_err = Σ(nextlevel apx) / apx_decaywidth`. Decides HOW MANY body-levels to enumerate. (channel-enumeration-bodydecay)
2. **Channel-level min_br prune** during find_channels_nextlevel — prunes channels below min_br using the apx ratio.
3. **Amplitude-level min_br prune** (group_channels_2_amplitudes, 1185-1196): `br = amp.apx_decaywidth / part.apx_decaywidth`; `if br.real < min_br: remove`. Drops whole final-state subprocesses BEFORE the survey. (channel-to-amplitude-bridge)
4. **Amplitude ORDERING** (1198): `get_amplitudes(clevel).sort(key=lambda x: x['apx_decaywidth'].real, reverse=True)`. Sorts subprocesses largest-estimate-first — affects survey order/display, not physics. (NOT on any instance page before this generalization.)
5. **Self-referential off-shell propagator** (get_apx_fnrule, 4288-4289): a channel's own `apx_decaywidth` is the Breit-Wigner width in the denominator `1/((q^2-m^2)^2 + m^2*apx_decaywidth^2)` when estimating an off-shell sub-channel. The estimate feeds its own next-level estimate. (apx-matrixelement-estimator covers the formula; called out here as a consumer.)
6. **Diagnostic display** (Channel.nice_string, 3540-3542): on-shell channels print `" (width = %.3e)" % self['apx_decaywidth']`; off-shell print `" (est. further width = %.3e)" % self['apx_decaywidth_nextlevel']`. DecayAmplitude diagnostic output (4853) prints `apx_br`. **This is the user-facing trap:** a verbose channel/amplitude dump shows `(width = 1.2e-03)`, which is the ESTIMATE, not the surveyed partial width that lands in the card. (NOT on any instance page before this generalization.)

## What this catches beyond the instances
The instance pages each warn "don't quote apx_decaywidth as the width" in the context of one mechanism (the stop loop, or the min_br prune, or the estimator math). The principle catches:
- **The sort (4)** — a future "why are my subprocesses ordered like that / does the order mean priority" question: ordering by estimate, no physics meaning.
- **The nice_string `(width = ...)` display (6)** — a future "the compute-widths verbose log prints a width per channel, is that my partial width?" question. Answer: NO, that printed number is `apx_decaywidth`, the estimate; the partial width is the post-survey value in the written param_card's BR lines. These two can differ by an order of magnitude (the estimator is a crude guess by construction — apx-matrixelement-estimator).
- **The completeness bound:** because min_br pruning (2,3) is on the ESTIMATE, a channel whose crude estimate undershoots min_br is dropped and NEVER surveyed even if its true BR would exceed min_br. So the estimator's accuracy bounds which channels get a physical width at all — the gate is load-bearing for completeness, not just speed.

## Boundary
- The estimator's internal physics (energy-flow model, color table, Lorentz scalarization): apx-matrixelement-estimator page.
- The enumeration loop / body_decay semantics: channel-enumeration-bodydecay page.
- The channel→subprocess grouping: channel-to-amplitude-bridge page.
- The survey integration that DOES produce the width, and the write-back: compute-widths-flow page.
This page owns only the cross-cutting claim: apx is a gate/diagnostic everywhere, never the written width.
