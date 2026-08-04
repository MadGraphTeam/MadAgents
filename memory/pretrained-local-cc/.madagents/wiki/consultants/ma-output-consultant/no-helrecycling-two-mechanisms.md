---
description: Output-time helicity recycling has TWO independent suppression mechanisms (finalize P1N flaglist gate vs exporter hel_recycling opt) with different triggers and consumers (MG5_aMC v3.7.1)
---

# Helicity recycling: two independent output-time suppression mechanisms

Answering "will this madevent output carry recycling?" requires checking BOTH of the
mechanisms below. They have different triggers and different consumers, and a single
output can have them disagree (recycling Lorentz routines emitted at finalize while the
exporter's own recycling opt is off). This is my slice's *trigger/disable* view; the
recycling ALGORITHM is the mc-integration slice.

## Mechanism 1 — finalize P1N flaglist gate
- Consumer: `madgraph_interface.py:9707` — augments `wanted_lorentz` with `P1N`/`out=-1`
  duplicates so ALOHA generates recycling variants. Fires for `madevent`, non-LoopAmplitude,
  when `'no_helrecycling'` NOT in flaglist.
- ONLY two producers of `'no_helrecycling'` in flaglist (grep-confirmed: only `append` sites
  in the file):
  - `:9125-9126` explicit `--hel_recycling=False` arg.
  - `:9140-9141` `any(spin > 3 ...)` (spin-3/2 value 4, spin-2 value 5 in 2S+1 convention).
- This is the gate that decides whether the *generated Lorentz routine set* carries the
  recycling variants.

## Mechanism 2 — exporter `hel_recycling` opt
- Consumer: `export_v4.py:4214-4216` (`ProcessExporterFortranME.__init__`) reads
  `opt['output_options']['hel_recycling']`; later used at `:4440` / `:6277-6283`.
- Default differs by class: `ProcessExporterFortranME.default_opt` has `hel_recycling: False`
  (`:4196`); `ProcessExporterFortranMEGroup` (the production default) has `True` (`:6206`).
- Fed from `line_options` (do_output `:9144`) -> `cmd_options` -> factory `opt['output_options']`
  (`export_v4.py:9870`). So any `--hel_recycling=...` in args reaches this opt.

### Mechanism 2's two OUTPUT-VISIBLE consequences (MEGroup.generate_subprocess_directory `:6277-6325`)
At `:6277` MEGroup writes `proc_characteristic['hel_recycling'] = self.opt['hel_recycling']`
(KeyError -> False, also forces opt False at `:6280`). Then per matrix element a hard fork at `:6283`:
- **recycling ON** (`:6283-6312`): emits **`matrix%d_orig.f`** (`:6284`) AND **`template_matrix%d.f`**
  (`:6310`, built from the `_hel.inc` dedicated template). NO plain `matrix%d.f` at output time —
  the runnable `matrix%d.f` is assembled from `_orig` + template by the recycling pre-processor later
  (mc-integration slice, compile/launch).
- **recycling OFF** (`:6317-6325`): emits a plain **`matrix%d.f`** directly.
- Probe-confirmed (v3.7.1, `generate u u~ > z`): default output -> `P1_qq_z/matrix1_orig.f` +
  `template_matrix1.f`, `proc_characteristics: hel_recycling = True`. With `--hel_recycling=False`
  -> `P1_qq_z/matrix1.f`, `hel_recycling = False`. So the P-dir matrix-file NAMING is an
  output-visible tell of Mechanism 2's state.

So Mechanism 2's two consumers are: the `proc_characteristic['hel_recycling']` field (read by the run
interface) AND the matrix-file naming fork (orig+template vs plain). Mechanism 1 (P1N flaglist) is
orthogonal — it governs the ALOHA Lorentz routine SET, not these matrix files. Under `--me_exporter`,
Mechanism 2 is off (plain matrix files, field False) while Mechanism 1 still fires (P1N routines present).

## The trap: --me_exporter feeds Mechanism 2 only, NOT Mechanism 1
`--me_exporter=<name>` appends `--hel_recycling=False` to **args** at `:9131-9132`, BUT the
flaglist test at `:9125` already executed ABOVE that line. So me_exporter's append:
- DOES reach `line_options` (`:9144` reads the mutated args) -> Mechanism 2 off.
- DOES NOT reach flaglist -> Mechanism 1's `:9707` P1N gate STILL fires.

Extracted-logic check of the exact `:9121-9145` block:
- `output madevent --me_exporter=cpp` (SM, spins {1,2,3}): `flaglist == ['me_exporter=cpp']`
  (no `no_helrecycling`), `line_options['hel_recycling'] == False`. P1N block at `:9707` fires.
- `output madevent --hel_recycling=False`: `flaglist == ['no_helrecycling']`. P1N suppressed.
- spin>3 model (e.g. graviton, spin value 5): `flaglist == ['no_helrecycling']`. P1N suppressed.

## Doc-myth corrections (troubleshooting-doc claims, source-verified v3.7.1)
- **No file named `matrix_optim.f`.** grep of the whole tree: zero hits. Recycling-ON emits
  `matrix%d_orig.f` (`:6284`) + `template_matrix%d.f` (`:6310`); the runnable `matrix%d.f` is
  assembled later. A "Line truncated" compile error naming `matrix_optim.f` is mis-named — the
  optimized matrix file is `matrix%d.f` (assembled) / `matrix%d_orig.f` (as emitted).
- **`hel_recycling` is BOTH a run_card param AND an output-time flag — different jobs.**
  - Output-time flag `--hel_recycling=False` (do_output `:9125`) is the GENERATION toggle:
    OFF → plain `matrix%d.f` emitted, no `_orig`/template, no recycling code compiled.
  - run_card `hel_recycling` (`banner.py:4454`, RunCardLO, **hidden, include=False, default True**)
    is a RUNTIME deactivation only — comment: *"allowed to deactivate helicity optimization at
    run-time --code needed to be generated with such optimization--"*. It does NOT prevent
    generation/compilation; the recycling Fortran is still emitted and compiled.
  - CONSEQUENCE: the troubleshooting-doc fix "set `hel_recycling=False` in the run_card" does NOT
    cure an output/compile-time `Line truncated`, because the offending code is still generated and
    built. The compile-error fix is the OUTPUT-TIME flag: regenerate with `output ... --hel_recycling=False`.
- **>132-char line risk is not a normal-writer artifact.** `file_writers.FortranWriter` sets a
  continuation-wrap column (read it at `file_writers.py:201,349`) and `split_line` auto-wraps, so
  writer-emitted Fortran cannot exceed the 132-char Fortran fixed-form limit.
  A genuine "Line truncated" would come from code that BYPASSES FortranWriter (verbatim template
  copies / recycler-preprocessor output — mc-integration slice), not from the output exporter's own writes.

## Why this catches more than the instance pages
do-output-orchestration documents the three arg-level triggers; finalize-and-model-conversion
documents the single `:9707` consumer. Neither alone answers "does `--me_exporter=cpp` on an
SM process still emit P1N recycling Lorentz routines?" — the answer (yes, via Mechanism 1,
even though Mechanism 2 is off) lives in the gap between them. The principle: an output's
recycling state is the pair (flaglist gate, exporter opt), not a single boolean; check both
and expect them to diverge under `--me_exporter`.
