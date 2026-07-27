---
description: You want a subset of the amplitude (resonant vs non-resonant, signal vs background vs interference, a peak removed).
---

# Diagram filtering & selection — fan-out

"Select/remove diagrams", "separate resonant from non-resonant", "isolate signal/background/interference", "forbid an on-shell resonance", "keep only s-channel Z", "custom diagram filter" — all live here. A single such request routinely spans several slices; route each sub-question by ownership, do not answer the operator semantics yourself.

## Owner map (by sub-question)

| Sub-question | Owner |
|---|---|
| `/ $ $$ > >` operator semantics, parse map, summary table, `$`-resonance, Z/γ split | **ma-diagram-filter-consultant** |
| `bwcutoff` window, on-shell test, which operators use it, decay-chain-vs-`$` σ direction | **ma-bw-window-consultant** |
| Decay-chain resonance isolation, `onshell`→`gForceBW`, chain-vs-`$` complementarity | **ma-chain-decay-consultant** |
| Squared coupling-order binning at TREE level (`NP^2==N`, `<=`, `constrained_orders` vs `squared_orders`) | **ma-coupling-order-consultant** |
| Squared-order `==`/`>` REJECTION at NLO, `[noborn=]`, loop-induced `[QCD]` | **ma-nlo-syntax-consultant** |
| `--diagram_filter` CLI flag parse/placement, `check gauge`/`check lorentz` | **ma-process-syntax-consultant** |
| `--diagram_filter`/`remove_diag` HOOK effect, `Diagram`/`Vertex`/`Leg` fields, `NoDiagramException`, per-decay application | **ma-diagram-enumeration-consultant** |
| `drawing.FeynmanDiagram`/`FeynmanLine` API used inside `remove_diag` | **ma-output-consultant** |
| `loop_sm_modif` / custom `NP`-order model for signal/bkg/int | **ma-eft-consultant** |
| MadSTR plugin install, `--mode=`, version gate | **ma-installation-consultant** |
| DR/DS resonance-overlap schemes at NLO | **ma-fks-consultant** |
| Is a filtered diagram subset gauge-invariant? (physics judgment, NOT source) | **ma-physics-consultant / -reviewer** |

## Dispatch ordering

1. **Resonant-vs-non-resonant ask** → diagram-filter (`$`/`$$`) + chain-decay (decay chain) + bw-window (`bwcutoff`) together; the three interlock (see traps 3–4).
2. **Signal/bkg/interference ask** → coupling-order (tree squared-order binning) + nlo-syntax (if loop-induced/`[QCD]` — the `==`/`>` rejection changes the whole recipe) + eft (the model must DECLARE the tag order) + physics (interference sign/size).
3. **`--diagram_filter` plugin ask** → process-syntax (flag strip + placement) + diagram-enumeration (hook + data structure) + output (drawing API). **First `ls PLUGIN/user_filter.py`** — the flag only arms a bool; without the user function, generation errors.
4. **Model/plugin-dependent asks** (`loop_sm_modif`, MadSTR) → **shell-check the install first** (`ls models/`, `ls PLUGIN/`). These are frequently ABSENT; an absent model/plugin makes the specifics a GAP, not a dispatchable fact. Route `install` (installation) or record the gap.

## Recurring doc-myth traps (pointers, not restated facts)

Each corrected fact lives in the named consultant's subtree — dispatch to confirm for the live input.

1. **`$` is a silent-fail trap.** `$ z` KEEPS the Z diagram (marks `onshell=False`); it does NOT remove it. Only `$$`/`/` remove diagrams. → diagram-filter.
2. **`/` prunes INTERNAL propagators only** (s- and t-channel), never external legs. → diagram-filter.
3. **`bwcutoff` is the Les-Houches TAG window;** enforcement for non-forced (`gForceBW=0`) legs is a hardcoded `5×Γ`, not `bwcutoff`. So "bwcutoff never affects full-process σ" is oversimplified (a residual effect is not excluded — a runtime probe). → bw-window.
4. **`$` uses `bwcutoff`; `$$` and `/` do not.** Decay-chain writes `onshell=True`→`gForceBW=1`, `$` writes `onshell=False`→`gForceBW=2` (opposite sense, shared flag). Chain and `$` are NOT additive complementary regions — interference is lost, and that is a PHYSICS statement, not what the flag does. `$ t t~` on `p p > t t~` directly is a **no-op** (no internal top propagator); the complementarity only holds against the expanded final state (`p p > w+ b w- b~ $ t`). → chain-decay / bw-window.
5. **`NP^2==2` isolates its `|M|²` bin via `squared_orders`, NOT `constrained_orders`** (a common conflation: the squared-`==` bin filter vs the amplitude-`==` per-diagram filter). Tree-level `<=` squared-order works in a single run; the bin↔order map depends on the model's per-insertion power `p` (read `coupling_orders.py`, never memory). → coupling-order.
6. **Squared-order `==`/`>` are rejected at NLO** (`amcatnlo_interface.py:542`) — only `<=` survives, and the check is model-agnostic and pre-amplitude, so it hits loop-induced `[QCD]` too. Isolation must use cumulative `<=` runs + subtraction. → nlo-syntax.
7. **Stock `loop_sm` declares only QCD/QED (no `NP`)** — `loop_sm_modif` is an EXTERNAL manual download, not bundled and not in the online-model DB. Its "NP tags HVV / p=1" claims are unverifiable without fetching it. Do not assume any EFT/HEFT/SMEFT model is present — `ls models/` first. → eft.
8. **`--diagram_filter` is position-INDEPENDENT** (a standalone whitespace-delimited token stripped in `do_add`). The "No particle --diagram_filter in model" error is a GLUING failure (`--diagram_filter,` fused to a comma), not a positional rule. Flag alone only arms a bool; needs `PLUGIN/user_filter.py:remove_diag`. LO-ONLY — `LoopAmplitude.generate_diagrams` ignores it. → process-syntax + diagram-enumeration.
9. **`leg['state']` means final(True)/initial(False), NOT s/t-channel** — the s/t reading is only the specialization for internal propagator legs (`get_nb_t_channel`). The `leg['number']<3` t-channel heuristic is WRONG. → diagram-enumeration.
10. **MadSTR:** `install MadSTR` is a built-in install target (not only a manual GitHub copy); the load-time version gate (`is_plugin_supported`) means a plugin declaring `maximal ≤ 3.6.x` under a default `-O` launch of `--mode=MadSTR` on v3.7.1 exits with "not supported". DR/DS is entirely plugin-provided — stock FKS has NO removal/subtraction code. → installation + fks.

## Return-interpretation hints

- A consultant that returns "all claims hold, no new page needed" ran a **confirmation pass** (its subtree already grounds the topic) — that is a completed dispatch, not a skipped one.
- **Gauge-invariance of a filtered subset** is a physics judgment (ma-physics + `check gauge` at runtime), never a source-mechanics fact — the operators do not test it. Do not let a source consultant adjudicate whether a subset is physically meaningful.
- Model/plugin-dependent claims often come back as GAPS in this deployment; treat an absent model/plugin as "verify by install", not "unsupported".
