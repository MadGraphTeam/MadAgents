---
description: Statistics are wanted in a sparse tail (high-pT, high-mass) by enhancing generation there, not by generating more.
---

# Biased event generation — three-slice fan-out

Bias modules up-weight sparse phase-space regions (high-pT tails, high-mass) at generation time; the enhancement is divided back out so physical distributions and σ are recovered, at the cost of **weighted** output (no unit-weight unweighting). A `bias_module`/`ptj_bias`/custom-bias question is not one slice — split it:

- **run_card knobs + compile/link wiring** → `ma-launch-consultant` `bias-module-wiring.md`. Registration in `banner.py` RunCardLO (`bias_module` default string `'None'`, `hidden`, **no `allowed=` enum**; `bias_parameters` default operative `{}`); card dict syntax; where the module is actually copied/validated/compiled into `libbias.a` (`configure_directory`, *not* treatcards).
- **template BIAS tree + module contract + ptj_bias source** → `ma-output-consultant` `bias-module-output-layout.md`. The `Source/BIAS/{dummy,ptj_bias}/` tree, the `bias_wgt(p, original_weight, bias_weight)` subroutine contract, the `common/bias/` block, the ptj_bias formula, and how params reach Fortran via the header-comment → `bias.inc` path.
- **reweight application + de-biasing + impact_xsec** → `ma-mc-integration-consultant` `biased-event-generation.md`. Bias **multiplies** the integrand before unweighting; the enhancement is divided back out at LHE write/parse; what `impact_xsec` and `requires_full_event_info` really gate.

Dispatch **mc-integration first** when the question is about correctness/weights/σ (it owns the headline inversion below), **launch first** for "how do I turn it on / what's the run_card syntax", **output first** for "how do I write a custom module / what's the built-in formula".

## Headline traps (route the sub-question to the owner; do not answer from the common documentation framing)

1. **`impact_xsec` does NOT "make the reported σ unbiased" — the commonly stated meaning is inverted.** The flag gates whether the per-event bias weight is *written to the LHE* so it can be divided out. `.False.` (ptj_bias) ⇒ a real bias, weight written for de-biasing; `.True.` (dummy) ⇒ bias≡1, no weight written. A runtime guard auto-forces `.False.` when any bias≠1, so a mis-set `.True.` on a real bias would silently drop the de-bias weight → un-recoverable distortion. Owner: `ma-mc-integration-consultant` (source-cited).
2. **LO-only.** `bias_module`/`bias_parameters` are registered only in RunCardLO. The NLO biasing mechanism is the distinct `flavour_bias` (forces `event_norm='bias'`) — do not conflate. Owner: launch / mc-integration.
3. **A bias module is ALWAYS linked.** `bias_module=None` resolves to the shipped `dummy/` identity module (compiled into `libbias.a`); "None" is not "no module", it is the no-op module. Owner: launch.
4. **The `bias_parameters` dict keys ARE the Fortran variable names.** Each entry is injected as a Fortran `key = value` assignment into `BIAS/bias.inc`; the module declares matching locals (e.g. `ptj_bias.f` declares `double precision ptj_bias_target_ptj`). An unknown key (not in the module's `C parameters = {...}` header comment) is WARN-discarded at treatcards, not passed. Owner: launch / output.
5. **Path is `Source/BIAS/`, not `SubProcesses/BIAS/`.** The built-in tree ships at `Template/LO/Source/BIAS/`; runtime lookup resolves `me_dir/Source/BIAS/<name>`. (The BIAS tree lives under Source despite being a per-event runtime hook.) Owner: output.
6. **Output is weighted; downstream tools must handle non-unit weights, and histograms must use event weights** — an unweighted histogram shows the *enhanced* (biased) distribution, not the physical one. Owner: mc-integration.

## Probe-candidates (expensive — cluster or defer)

The physics-visible correctness invariant — a `ptj_bias` run reproduces the unbiased total σ within MC error while enriching the high-ptj tail at smaller de-biased weights — is a **runtime** claim, not settled from source. It needs a `p p > j j` output + two launches (with/without bias) comparing reported σ, the sum of de-biased weights, and tail density. Heavy σ integration → cluster per cluster-submission discipline; recorded as a probe-candidate in the consultant slates, not cached as fact.
