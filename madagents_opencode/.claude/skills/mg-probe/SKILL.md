---
name: mg-probe
description: Adversarial runtime probe of a candidate MadGraph setup — write well-formed expectations about what should be true if the spec is correct, dispatch the `ma-probe` agent, read per-expectation results. Use any time you're about to run MadGraph to test a candidate — `/mg-deep-verify` Stage 4, a sanity check after `/mg-setup` builds, a user-asked "does this run cleanly", or debugging a failed launch. Skip when no runtime question exists (pure source-walk questions belong to the consultants).
---

# `/mg-probe`

Source-walking by consultants is the load-bearing verification. The probe is the **runtime** check, dispatched **adversarially**: given a target state of what should be true if the spec is correct, the probe finds where running MadGraph deviates from it.

Frame the dispatch as "find what's wrong with running this," not "confirm the consultant claims." Adversarial framing produces different probes — they try to break expectations, including ones the dispatch did not name.

## Writing well-formed expectations

Expectations come in two kinds, and the list must carry **at least one of the second**:

- **Spec-derived** — what the assembled spec implies should happen ("this `generate` line implies N diagrams"). A spec-derived match only confirms the spec is internally what it claims; a spec that parses and runs but computes the wrong observable still matches its own spec-derived expectations.
- **Target-derived** — what a *correct* setup for the question produces, computed from the physics of the request independently of the assembled spec: the expected signal topology / diagram count for the requested process, the order-of-magnitude σ for the requested observable, non-zero-ness in the kinematically allowed region. The physics regime classification is the natural source. A target-derived expectation is what makes a wrong-but-runnable spec *deviate* — a contaminated form whose σ is orders of magnitude off the physics target contradicts the anchor even though it matches its own spec.

Label each expectation spec-derived or target-derived; a list with only spec-derived expectations tests nothing a wrong spec would fail.

Plain-prose claims about what MadGraph should do, observable by running, file inspection, grep, or launch:

- *"`generate p p > h j j QCD=0, (h > w+ w-, w+ > ta+ vt, w- > ta- vt~)` should produce 87 diagrams, NEXTERNAL=8, IDUP showing tau+ nu_tau tau- nu_tau~, and gForceBW=1 for both W± propagators in decayBW.inc."*
- *"No 'decay discarded' or 'no phase space' warnings in stdout."*
- *"matrix1_orig.f contains zero Yukawa-Hττ vertex calls (no `FFS4.*GC_99.*MDL_MH` hits) — Yukawa channels excluded by chain syntax."*
- *"At bwcutoff=50 with MH=100, σ is non-zero — the BW window covers the W\* phase space."*
- *"The integrator survives `launch` with `block smeft 35 1.0` and `-massless` restriction defaults — no multi-channel crash."*

Describe the **correct state**; the probe is adversarial against it. Don't pre-enumerate failure modes — enumerate what should be true; the probe finds where it isn't. The σ and topology examples above (lines on diagram count and non-zero σ) are target-derived — they encode what a correct setup for the question produces, and they are the ones a wrong-but-runnable spec fails.

If you have no concrete expectations (very rare — even a freshly-built candidate has *"the parser accepts the spec"* and *"`output` succeeds without errors"*), dispatch with the commands alone for a minimal sanity-check report. The probe will not invent expectations.

## Dispatch

Dispatch `ma-probe` with: the assembled commands, the question (for context), the consultant returns (so the probe knows what's already been asserted from source), and the expectation list. The probe stress-tests each, derives further expectations from the target state, and returns per-expectation matches / deviates plus probe-derived deviations (per the agent's card).

Findings are facts; reconciliation is the caller's job.

## Boundaries

- **Probe evidence never overrules a source-walked claim.** When a probe finding contradicts a consultant's source walk, treat it as a contradiction to resolve — re-engage the owning consultant. Do not infer the source walk was wrong.
- **Absence of deviations ≠ correctness.** The probe walks a finite expectation set; silent fails hide in modes not tested. "Probe surfaced nothing" means "no deviation in the tested expectations," not "spec verified."
- **Adversarial framing is the discipline.** Confirmatory wording ("verify the spec runs") yields confirmatory probes. Use the adversarial wording even when you mostly expect things to pass.
- **Launch-cost discipline.** Long-running launches are submitted to the cluster; quick parse-time probes and small-statistics launches run locally. The probe's card carries the threshold.
