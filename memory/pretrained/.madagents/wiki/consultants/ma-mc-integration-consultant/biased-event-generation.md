---
description: Biased event generation (bias_module) — where the bias multiplies the integrand, how it is divided back out (de-biasing) at LHE write / parse, the impact_xsec / requires_full_event_info / stored_bias_weight common-block semantics, and why output is weighted. impact_xsec is commonly misread as "is σ unbiased"; source shows it gates whether the per-event bias weight is written to the LHE. v3.7.1 LO.
---

# Biased event generation — bias_module (v3.7.1 LO)

Activated by run_card `bias_module` (default `'None'`, hidden; banner.py:4279). Shipped modules under
`$MADGRAPH_INSTALL/Template/LO/Source/BIAS/`: `dummy/dummy.f`, `ptj_bias/ptj_bias.f`.
User-editable default hook: `Template/LO/SubProcesses/dummy_fct.f` (`bias_wgt_custom`, returns 1.0, line 161).

## Where the bias enters — MULTIPLIED into the integrand (not "divides the event weight")
- `madgraph/iolibs/template_files/auto_dsig_v4.inc:166`: `DSIGUU=DSIGUU*CUSTOM_BIAS(PP,DSIGUU,%(numproc)d,1)` (also :412 for the VEC path). The bias factor multiplies the differential cross section BEFORE `UNWGT` (:181). So VEGAS integrates `ME*bias`; events are sampled ∝ `ME*bias`.
- `custom_bias` is defined ONLY in `Template/LO/SubProcesses/reweight.f:1286-1331`; it calls `bias_wgt(p,original_weight,bias_weight)` (:1328) → the module's subroutine. Default run_card 'None' → dummy → `bias_weight=1.0` (reweight.f:1326-27 comment).

## De-biasing — the bias is removed at write/parse so physical σ + distributions are recovered
- The per-event bias weight is stored as the LAST column of the scratch event record; `madevent_combine_events.f:171,269` read it back as `bias_weight`.
- The LHE `XWGTUP` (and scale/PDF weights) already have the bias REMOVED at write time — explicit source comment: lhe_parser.py:3391-3393 "The bias weight … is already removed from the XWGTUP (and scale/pdf weights). That means that in practice this weight is not used."
- NLO extended `<mgrwt>` rwgt record (`NLO_partial.parse`, lhe_parser.py:3282): the record CARRIES the bias in `ref_wgt`/`pwgt`, and `parse` divides it out unless `keep_bias=True` — lhe_parser.py:3399-3401 `self.ref_wgt /= self.bias_wgt; self.pwgt = [p/self.bias_wgt …]`.
- COMMON MISCONCEPTION: "the bias divides the event weight, so physical σ/distributions are preserved after de-biasing." Correct in spirit, wrong in mechanism — the bias MULTIPLIES the integrand at generation, then is DIVIDED OUT at write/parse. There is no "divide the event weight by bias" step in the bias module itself.

## Output is weighted (a consequence of de-biasing)
Events are unweighted against `ME*bias`; de-biased weight ∝ `1/bias`, which varies event-to-event → non-uniform → weighted LHE. This is inherent to bias_module, not routed through an `event_norm` switch.
- DISTINCT mechanism: `flavour_bias` (banner.py:5708-5945) is a separate, NLO-side flavour-enhancement that EXPLICITLY forces `event_norm='bias'` (5943-5945 warning + set). Do not conflate `bias_module` (LO integrand bias, this page) with `flavour_bias`/`event_norm='bias'`.
- PROBE-CANDIDATE: exact per-event XWGTUP formula and whether bias_module forces weighted output (vs unit) — confirm by a run; source read only proves XWGTUP is de-biased, not the numeric normalization.

## impact_xsec — COMMON MISCONCEPTION. It gates whether the bias weight is WRITTEN, not "is σ unbiased"
impact_xsec is commonly misread as a boolean "the reported σ is / is not unbiased." Source meaning: impact_xsec (member 2 of common/bias) flags whether the per-event bias weight is recorded in the LHE so it can be un-biased downstream.
- `dummy.f:28-31` + `impact_xsec=.True.`: "Not impacting the xsec since the bias is 1.0. Therefore bias_wgt will NOT be written in the lhe event file. Setting it to .True. makes sure that it will not be written." (dummy_fct.f:146-150 same).
- `ptj_bias.f:54-55` + `impact_xsec=.False.`: real bias → weight IS written so distributions can be de-biased.
- Runtime guard: `madevent_combine_events.f:172` `if(bias_weight.ne.1d0) impact_xsec=.false.` — auto-forced False whenever any event carries bias≠1 (protects against a user mis-setting .True. with a real bias).
- Consumer alias reveals true intent: `reweight.f:1305-1306` reads member 2 as `is_bias_dummy` → "is this a dummy (identically-1) bias." True⇒dummy⇒don't write; False⇒real bias⇒write so it can be divided out.
- So `impact_xsec=.False.` is what ENABLES recovery of the unbiased physical σ (by writing the weight); it is NOT a boolean "the reported σ is unbiased / biased." The intuitive reading "`.True.` ⇒ bias affects reported σ" is backwards: `.True.` means the bias is assumed trivial and its weight is dropped.

## Mandatory common block — name/members/order (correct on the MODULE side; positional aliasing elsewhere)
Module definition (author-facing): `common/bias/stored_bias_weight,impact_xsec,requires_full_event_info`
— confirmed dummy.f:35-36, ptj_bias.f:59-60, dummy_fct.f:155-156. Three members, that order, those names.
CAUTION — Fortran common blocks are POSITIONAL; consumers alias:
- `reweight.f:1306`: `common/bias/bias_weight,is_bias_dummy,requires_full_event_info` (member 2 renamed).
- `madevent_combine_events.f:70,649`: `common/bias/bias_weight,impact_xsec` — only TWO members declared.
Also: member 1 `stored_bias_weight` in the module is vestigial (`data …/1.0d0/`, never assigned in the module body; the real output is the subroutine arg `bias_weight`).

## requires_full_event_info — gates early full-event reconstruction, NOT "info in p"
`reweight.f:1314-1322`: if `.True.`, `custom_bias` calls `write_leshouche(p,-1.0d0,…)` and `write_event_to_stream(...)` EARLY (before `bias_wgt`) to populate colour/helicity/resonance info into the event record/common blocks, and sets `AlreadySetInBiasModule=.True.` → `unwgt.f:575` jumps straight to the write label (`unwgt.f:852` `1123 continue`).
- Momenta `p` are ALWAYS passed to the bias function; what `.True.` gates is the extra per-PS-point reconstruction of colour/helicity/resonances (cost). `.False.` (usual) = momenta only. COMMON MISCONCEPTION: that `.True.` makes "the info available in `p`" — it mislabels the channel; the reconstructed colour/helicity/resonance info goes into the event record, not into `p`.

## Negative weights vs bias
`madevent_combine_events.f:216` `if (wgt.lt.0d0) has_negative=.true.`. Dividing by bias_weight (which is ≥0, e.g. `(ptj/target)^power`, ptj_bias.f:96) never flips sign — negative weights come from ME/PDF, orthogonal to biasing.

## bias.inc — where run_card params reach the module
`bias_parameters` run_card dict (banner.py:4280, `include='BIAS/bias.inc'`) is written to `SubProcesses/bias.inc`, which `ptj_bias.f:74` `include '../bias.inc'` reads to set `ptj_bias_target_ptj` / `ptj_bias_enhancement_power`. `bias.inc` is GENERATED (absent until output/compile).

## PROBE-CANDIDATE (physics-visible invariant)
A correct `ptj_bias` run with `impact_xsec=.False.` should reproduce the SAME total σ as the unbiased run (within MC error) while placing MORE events in the high-ptj tail at correspondingly SMALLER de-biased weights. One line: run `p p > j j` with/without `bias_module=ptj_bias`, compare reported σ and the tail event density + sum-of-de-biased-weights.
