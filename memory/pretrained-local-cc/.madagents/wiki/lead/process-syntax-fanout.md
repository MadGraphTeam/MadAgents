---
description: Writing, explaining, or verifying a generate line whose tokens span several features, each with its own owner.
---

# Process-line syntax — token→owner fan-out

A `generate` / `add process` line looks like one object but is parsed into many
independently-owned pieces. Route each token class to its owner; do not answer a
whole line from one consultant unless every token is in that slice.

## Token → owning slice

| Token / feature on the line | Owning consultant | Notes |
|---|---|---|
| `generate` / `add process` orchestration, `>` initial‑final split, particle‑name (`~`,`+`,`-`) resolution, `define`, `@N` process number, `check` command, `display …` | `ma-process-syntax-consultant` | parser entry `extract_process`; `@N` → `ProcessDefinition['id']`; `check`/`display` subject lists live in `_check_opts`/`_display_opts` |
| Built‑in multiparticle **label content** (`p`,`j`,`l+`,`l-`,`vl`,`all`) | `ma-model-loader-consultant` | content defined in `input/multiparticles_default.txt` + `add_default_multiparticles`; b‑in‑p/j is mass‑driven |
| Multiparticle **expansion** into subprocesses + silent zero‑diagram drop | `ma-diagram-enumeration-consultant` | `MultiProcess.generate_multi_amplitudes`; see seam below |
| `QCD=`/`QED=`/`NP=`, `==`/`<=`/`>`, `^2` squared orders, `WEIGHTED` | `ma-coupling-order-consultant` | tree‑level; the WEIGHTED *value* is model‑side |
| Filter operators `/`, `$`, `$$`, and required s‑channel `> X >` | `ma-diagram-filter-consultant` | sets `forbidden_*`/`required_s_channels`; the `> X >` *parse* is a process‑syntax seam, the enumeration effect is diagram‑filter |
| Comma decay chains `, X > …`, parentheses, on‑shell forcing | `ma-chain-decay-consultant` | comma → `onshell` flag → `gForceBW=1`; see decay seam below |
| `[QCD]`/`[virt=…]`/`[noborn=…]` NLO brackets | `ma-nlo-syntax-consultant` | sets `LoopOption`/`HasBorn`; demands a loop model |
| `{0}`/`{T}`/`{L}`/`{R}`/`{±N}` polarization | `ma-polarization-consultant` | external + decay‑chain‑head legs only |

## Anticipated traps (route by symptom)

- **"multiparticle expansion drops combos / interferes"** — the *label→ids* parse is process‑syntax, but the **expansion, the silent partial zero‑diagram drop, and coherent(within‑amplitude)/incoherent(across generate/add‑process) summation are NOT there**. Expansion + drop → diagram-enumeration (`MultiProcess.generate_multi_amplitudes`; `NoDiagramException` fires only when *every* combo is empty — a partial drop, e.g. LFV combos of `p p > l+ l-`, is silent). Coherent sum within one amplitude → helas/color; incoherent σ‑add across separate `generate`/`add process` → mc-integration/output.
- **"`l+` should include tau"** — no. Built‑in `l+`/`l-` are 2‑generation (`e mu`), but `vl` is 3‑generation (`ve vm vt`) — a real asymmetry. Content question → model-loader, not process-syntax.
- **identical‑particle symmetry factor (`p p > z z` → 1/2!)** — do **not** attribute it to `IdentifyMETag`. `IdentifyMETag` is cross‑*process* ME **deduplication** and only *reads* the factor to avoid wrongful merges. The 1/n! is computed by `Process.identical_particle_factor()` (on the Process object) and applied as a denominator in `HelasMatrixElement.get_denominator_factor` → route to `ma-helas-amplitude-consultant`.
- **`$` vs `$$`** — `$` forbids on‑shell s‑channel only (keeps off‑shell tails, `onshell=False`); `$$` removes the whole s‑channel topology (on‑ and off‑shell), t‑channel kept; `/` removes the particle from all *internal* propagators (external legs untouched). Filtering any of these (or subsetting with `> X >`) can break gauge invariance → `check gauge`.
- **`{L}`/`{R}` on a vector** — not "fermions only": on a spin‑1 they give helicity ∓1 (with a warning), NOT longitudinal. Longitudinal is `{0}`. Only `T/A/G/H/Q/W/S` are vector‑only; `{0}` is boson‑only.
- **NLO `[ ]` + comma decay** — hard‑rejected; the reaching (user‑visible) guard is `loop_interface.py:245` ("ML5 cannot yet decay a core process including loop corrections"), which shadows the base conjunction guard. Remedy: `> …` s‑channel form or MadSpin.

## Cross-slice seams referenced here

- **Comma decay chain** spans chain-decay (comma→`onshell`→`gForceBW`), bw-window (`bwcutoff` scales the forced‑BW window: its default × Γ_eff — read the bwcutoff default, see `offshell-bwcutoff-derivation.md`), kinematic-cuts (`cut_decays=False` default silently exempts `from_decay` legs from per‑particle cuts — comma σ ≠ arrow σ). See `decay-chain-seams.md`, `fiducial-cuts-fanout.md`, `offshell-bwcutoff-derivation.md`.
- **Coupling‑order + NLO bracket** precedence: `coupling-order-nlo-bracket-seams.md`.

## Dispatch note

For "verify this whole process line", fan out one focused question per token class
present, in parallel; reconcile. A single line commonly implicates 3–5 slices, and
the silent‑drop / silent‑reassignment traps above do not surface from any single
consultant's happy‑path read.
