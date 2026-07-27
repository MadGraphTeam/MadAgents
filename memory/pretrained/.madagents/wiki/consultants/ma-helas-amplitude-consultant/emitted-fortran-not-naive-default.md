---
description: Cross-cutting principle — the HELAS-layer's emitted matrix_*.f / configs.inc / JAMP content is fixed by the chosen writer + flag + gauge + runtime-survey + model-hierarchy, NOT by a naive form derivable from source defaults; predicting emitted output from source alone is unsound, read the generated file.
---

# Emitted Fortran is writer/flag/gauge/survey-determined, never a naive source default

Cites `$MADGRAPH_INSTALL/madgraph/iolibs/helas_call_writers.py`, `.../core/helas_objects.py`, `.../iolibs/export_v4.py`, `.../madevent/hel_recycle.py`, `.../madevent/gen_ximprove.py` (v3.7.1).

## The principle
The HELAS output layer does not emit a single canonical Fortran form. The content written into `matrix_*.f` (per-wf/per-amp CALLs, JAMP sums) and `configs.inc` is **selected at emission time** by a combination of: which call-writer subclass the exporter instantiated, the writer's boolean flags, the gauge, a runtime survey product, and the model's order-hierarchy completeness. **Reasoning about what the generated Fortran says by predicting it from a "naive" form (or from a source default value) is unsound** — the actual content can differ in width values, array layout, coefficient form, index ordering, or even whole CALLs being absent. The reliable move is to **read the generated file** (and, for survey-dependent content, to launch first).

This is a THIRD, output-layer trap, orthogonal to the two in-memory cross-cutting pages:
- identity-keys-purpose-tuned: which property subset an in-memory *comparison* uses.
- helas-me-mutation-lifecycle: a *query*'s answer depends on lifecycle *stage*.
- THIS page: the *emitted file* depends on writer/flag/gauge/survey/model — the on-disk Fortran ≠ a naive source-default prediction.

## The instances (each individually verified; this page lifts the common discipline)
1. **zerowidth_tchannel — t-channel widths rewritten to ZERO.** `FortranUFOHelasCallWriter` defaults `options['zerowidth_tchannel']=True` (@343); `get_wavefunction_call` @288-292 regex-rewrites `, fk_<width> ,` → `, ZERO ,` (skip `fk_ZERO`) for any t-channel wf. So the emitted CALL carries ZERO regardless of the param_card width. (helas-call-writers page.)
2. **hel_sum — the `W(1,i,H)` array layout.** `format_helas_object` @1038 appends a helicity index `H` to W/AMP arrays iff `hel_sum` (default False @1030). The same ME emits a different array shape depending on the flag the exporter passed. (helas-call-writers page.)
3. **split_amps gauge suffix — CombineAmp / CombineAmpS / CombineAmpFD.** `split_amps` @850-857 (hel_recycle.py) picks the suffix from `spin` and `gauge` (default 'U' @386); spin-2 / spin-3/2 **raise** instead of emitting. The emitted CombineAmp variant is gauge-dependent. (helicity-recycling-output page.)
4. **Nc=3 substituted into JAMP coefficients.** `coeff()` @2288 (export_v4) collapses the `(ff, frac, imaginary, Nc_power)` tuple into ONE rational with `Fraction(Nc_value=3)**Nc_power` — the emitted JAMP coefficients are concrete numbers, not symbolic in Nc; an Nc≠3 study cannot re-read the Fortran. (jamp-and-config-exporter-integration page.)
5. **split-order index positions depend on model order_hierarchy.** `sort_split_orders` @4992 sorts split-order indices by `order_hierarchy` ONLY if every split order has a hierarchy entry; a missing order falls back to insertion order and silently changes the emitted index layout. (split-orders-and-exporter-helpers page.)
6. **helicity-recycler optimized routine is a runtime survey product.** `good_hels`/`bad_amps`/`bad_amps_perhel` come from a `madevent_forhel` survey (gen_ximprove @232-234/@288); the optimized `matrix_optim.f` content (which helicities/amps survive) cannot be predicted from source — requires a launch. (helicity-recycling-output page.)

## Why it catches MORE than the instances
- It predicts the same trap for **any** emission knob added to this layer in future: a new call-writer subclass, a new boolean flag, a new gauge mode, a new optimization level, a new model with an incomplete hierarchy. Read the constructor / generated file; never quote a "default" emission.
- Two distinct sub-modes it unifies: **flag/gauge/model-determined** (instances 1-5: deterministic but option-selected, so read the *generated file*) and **runtime-survey-determined** (instance 6: non-deterministic from source, so *launch* then read). Both defeat source-only prediction; the remedy differs (read file vs run-then-read).

## Boundary (not this page's slice)
This is about emission divergence only. The *algebra* behind any emitted value is elsewhere: color coefficients / ColorMatrix = color-decomposition slice; the ALOHA routines the CALLs target = aloha slice; BW/width semantics = bw-window/mc-integration slices; per-event helicity MC = mc-integration slice. This page owns only "the emitted form is option/survey-selected, don't predict it from a default."

## Caution
When asked "what does matrix_*.f / configs.inc say for this process", the honest answer pins the writer + flags + gauge + (for the recycled routine) the survey. "The default emits X" is a hypothesis until the generated file is read; for survey-dependent content it is unknowable without a launch.
