---
description: You changed an input other values were computed against, or entered a regime the shipped defaults never assumed.
---

# Derived-quantity staleness — MG5 won't reconcile an input-dependent value for you

Forward-looking generalization over `decay-widths-lifecycle.md` (the WIDTH instance) and `offshell-bwcutoff-derivation.md` (the BWCUTOFF instance). The shared lesson, confirmed independently by madwidth, param-card, bw-window, and phase-space source-walks:

> **A quantity whose correct value depends on the process's masses/widths must be derived or regenerated per-process. MG5 holds a stored or default value, uses it verbatim, and runs cleanly — it performs NO consistency check against the inputs the value depends on, and emits NO warning when the value is wrong for the regime.**

This is *why* "the run completed and gave a σ" is never evidence the σ is right when a mass was edited or an off-shell regime was entered.

## The two confirmed instances

| derived quantity | depends on | how it goes wrong | MG5's silence | fix | owner page |
|---|---|---|---|---|---|
| **particle total width** (`DECAY 25`) | mass + couplings | edit `MASS 25` → the shipped/old `DECAY` is **stale** (computed at the old mass). Feeds the chain-σ BR denominator → σ off by Γ_correct/Γ_stale (anchored ≈4365×), implied BR≫1 | no mass↔width check anywhere; `update_dependent` never rewrites a free-external width; only a literal `auto` triggers recompute | regenerate AFTER the mass edit: `compute_widths`, `DECAY 25 Auto`, `set WH Auto` | `decay-widths-lifecycle.md` |
| **bwcutoff** (BW sampling window) | parent mass, daughter mass+width, daughter decay floor | the **default** clips the off-shell tail; a memorised fixed value fails heavy-top (needs ~59Γ); wrong floor (m_H−m_W) undershoots | silent (~1–3 % σ) or loud (Zero result) by window-overlap geometry; no "your window misses the kinematics" warning | derive bwcutoff ≥ (m_pole − floor)/Γ from the specific propagator | `offshell-bwcutoff-derivation.md` |

The two differ in *kind* — width is MG-computable (it just won't auto-refresh); bwcutoff MG never computes (the user must size the window). But both are **input-dependent values MG5 silently uses without reconciliation**, and both have the same dispatch discipline below.

## Dispatch discipline (what to do on this class)

1. **Trigger recognition.** The moment a setup (a) edits a mass / width / coupling, or (b) enters an off-shell or threshold regime, ask: *what derived value depends on this that MG5 stores or defaults and won't refresh?* Width and bwcutoff are the two known ones; treat a novel input-dependent knob the same way.
2. **Derive/regenerate, never default-or-memorise.** Route the VALUE to the owning slice as a derivation request with the kinematic inputs — do NOT hand the consultant a candidate number to bless (marked-premise discipline would make it validate a memorised value). Width → madwidth; bwcutoff → bw-window.
3. **For setup-only ("don't run MG5") tasks the derivation IS the deliverable** — the σ-feedback loop is deliberately closed, so the derived value must come from physics at write time, with a one-line justification. Do not let a setup-only answer ship a default/memorised value.
4. **Cross-check the consistency MG5 skips.** A physical BR ≤ 1 (BR = Γ_partial/Γ_total) confirms width self-consistency; BR ≫ 1 is the stale-width tell. A non-zero-but-suspiciously-small σ on a decay chain is the bwcutoff-clip tell. These are the checks MG5 itself never runs.

## Relation to neighbouring patterns
- **`config-value-lifecycle-layers.md`** ("I set X but the run did Y") is about WHERE a value is governed across stages. Derived-quantity-staleness is different: the value IS governed by the card/default, but it is stale/wrong **relative to a different input it should depend on**, and nothing tracks that dependency.
- **The "silent regime-wrong default" note** in `offshell-bwcutoff-derivation.md` (the bwcutoff default; sibling `cut_decays=False` in `fiducial-cuts-fanout.md`) is the *default-was-wrong* face of this; the *derived-value-went-stale-after-an-edit* face (width) is the other. Same root: MG5 uses the stored value without reconciling it to the user's intent.
