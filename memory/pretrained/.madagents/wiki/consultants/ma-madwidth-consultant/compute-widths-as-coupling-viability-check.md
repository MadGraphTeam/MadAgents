---
description: compute_widths partial width + BR is the discriminating viability check for a benchmark whose signal hinges on a mixing/derived-coupling vertex — a tiny partial width / BR=0 is the silent-fail fingerprint of a coupling the benchmark zeroed (directly or via mixing); no near-zero/BR/tiny-total check exists.
---

# compute_widths as the coupling-viability discriminator (v3.7.1)

When a benchmark's signal hinges on a specific decay vertex, the `compute_widths`
partial width + BR for that channel is the cheapest viability check available — it
EXPOSES a coupling the chosen benchmark point zeroed (directly, or via a mixing
matrix), before any chain σ is trusted. A microscopic partial width / vanishing BR
is the silent-fail fingerprint. Confirmed against the MSSM_SLHA2 cascade
χ̃₂⁰→χ̃₁⁰Z (n2 → n1 Z), but the mechanism is model-general: it is the FR-2body
analytic path consuming card-read couplings with no value-floor check.

## The partial width is `eval`'d from a decays.py formula in card-read couplings

For a model that ships `decays.py` (MSSM_SLHA2 does — `models/MSSM_SLHA2/decays.py`,
5.9 MB), the 2-body partial width is the FR analytic path
(`madgraph_interface.py:9885-9915`), NOT the MadEvent survey:
- `model.set_parameters_and_couplings(opts['path'], scale=mass)` (`:9862`/`:9878`)
  reads the param_card and returns the `data` eval namespace.
- `value = eval(expr, {'cmath':cmath}, data).real` (`:9899`) — `expr` is the formula
  string from `decays.py`.

The χ̃₂⁰→χ̃₁⁰Z formula is `Decay_n2`'s `(P.Z,P.n1)` entry
(`models/MSSM_SLHA2/decays.py:653`). Its numerator is built ENTIRELY from
`NN2x3, NN2x4, NN1x3, NN1x4` (and their `complexconjugate`) — bilinears in exactly
the **higgsino columns (3,4) of the NMIX neutralino-mixing matrix**
(`NN<i>x<j>` = NMIX row i, col j). Shape `∝ (NN_i3·NN_j3 − NN_i4·NN_j4 ...)` —
matches the V_454 (`GC_444`/`GC_422`) Z-χ̃₂⁰-χ̃₁⁰ coupling ∝ (N_i3 N_j3 − N_i4 N_j4).

## NMIX is read from the card; MG5 never recomputes it

In `set_parameters_and_couplings` (`models/model_reader.py:58`):
- **External params** (NMIX block) are read straight from the card by LHA
  block+code: `value = param_card[block].get(pid).value` (`:179`), set at `:205`.
  The complex `NN1x3 = Parameter(value='RNN1x3')` (`MSSM_SLHA2/parameters.py:1456-1459`)
  is a derived param whose expression is the real external `RNN1x3` (NMIX) — recomputed
  by `exec`-ing its expr at `:230-236`, but ONLY from the card-read externals.
- **Couplings** recomputed by `exec`-ing `coup.expr` (`:253-256`) from those params.

So a decoupled-μ benchmark (heavy higgsinos → tiny NMIX cols 3,4 for the light
gaugino-dominated n1/n2) feeds tiny `NN*x3/NN*x4` into the formula → microscopic
partial width. MG5 reads the mixing as-is; it never solves the neutralino mass matrix.

## There is NO near-zero / BR / tiny-total check for a colorless particle

**The complete guard inventory falls into exactly TWO families, and NEITHER floors a
colorless particle's physically-tiny width.** Every value-based action on a computed
partial width lives in `do_compute_widths` and is one of:
- **(family 1) Negative-noise clamps** (`:9900-9908`, read the two cut-off literals there):
  a tiny-negative width→0 silent; a larger-negative→0+warning; more negative → raise. These
  guard numerical noise (cancellation giving a slightly-negative width), NOT physical
  smallness — color-blind.
- **(family 2) Color-gated QCD-scale floor** (`:9909-9912`, FR path, read the GeV-scale floor
  literal there; reapplied to survey results `:10011-10015`; dead twin commented at
  `:9998-10001`): a positive width below that floor → 0 + warning, **gated
  `particle['color'] != 1`** (i.e. fires ONLY for COLORED states). A neutralino — or ANY
  colorless light state — is `color == 1` → this NEVER fires.

So a small *positive* width survives unflagged iff the particle is colorless: there is
NO positive-smallness guard for `color == 1` anywhere in the engine. This is what makes
the diagnostic below load-bearing — and it generalizes past SUSY mixing to any colorless
light state (an EFT/ALP pseudoscalar, a sterile neutrino) whose true width is below the
colored-only floor (`:9909-9912`): MG5 writes it verbatim, no floor, no warning.

There is **no** branching-ratio computation in this write-back path (the BR shown in
the DECAY block is `partial/total` arithmetic at write time,
`madevent_interface.py:update_width_in_param_card:2998`, not a checked quantity), **no**
zero-partial-width flag, **no** "total width unexpectedly tiny" flag, **no**
mixing-consistency check. `compute_widths` reports whatever the couplings give.
The only caveat ever emitted is the blanket NWA/tree-level warning (`:9826-9828`).

(The MadSpin-side wrapper `common_run_interface.py:7331-7336` DOES warn on
`total/mass < small_width_treatment` or below a hardcoded critical floor (read at :7331-7336)
— but that is a total-width-vs-mass floor on the MadSpin path, not a per-channel/BR check, and not the REPL `compute_widths`
engine path. It would not flag a 2e-4 GeV total on a ~110 GeV neutralino:
2e-4/110 ≈ 2e-6, above the hardcoded critical floor at 7331-7336.)

## Why this is the discriminating artifact (the diagnostic)

`compute_widths n2` on the two benchmarks (computed):
- **GOOD** (higgsino-admixed): Γ(n2) = 0.1163 GeV; χ̃₂⁰→Z χ̃₁⁰ partial = 2.27e-2 GeV,
  **BR 19.5%**; χ̃₂⁰→h χ̃₁⁰ BR 80.5%.
- **TRAP** (decoupled μ=2000): Γ(n2) = 2.0e-4 GeV (~580× smaller); χ̃₂⁰→Z χ̃₁⁰
  partial = 9.33e-6 GeV (**~2400× below GOOD**); BR collapses; residual decays are
  higher-order leakage.

Both runs exit cleanly with a written DECAY block — the TRAP's vanishing Z-channel
partial width / BR is the ONLY in-tool signal that the mixing zeroed the vertex.
Inspect the partial width + BR BEFORE trusting the chain σ: a tiny partial width /
BR is the silent-fail fingerprint of a benchmark-zeroed coupling. The chain σ
downstream is ∝ BR(n2→Zn1) (phase-space slice owns the BR-as-propagator-denominator
mechanism), so a near-zero BR silently produces a near-zero signal cross section with
no error.

## Generalization

For ANY benchmark whose signal hinges on a specific decay vertex (SUSY mixing,
2HDM alignment, any FR formula built from a mixing/derived parameter), the
`compute_widths` partial width + the SLHA DECAY-block BR is the discriminating
viability check. The vertex strength is whatever the card's mixing/derived
parameters give; MG5 evaluates and writes it with no floor, no BR check, no
mixing-consistency check. This is the width-lifecycle instance of the lead
`derived-quantity-staleness` family: a value MG5 uses verbatim from the card with
no consistency guard — except here the "staleness" is a benchmark CHOICE that
zeroes the coupling, not a stale stored number. Cross-link `compute-widths-flow`
(the FR-2body mechanism + value-checks this page reuses) and the lead
`decay-widths-lifecycle` / `derived-quantity-staleness` playbooks.
