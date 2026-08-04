---
description: The decay happens after event generation (factorized, spin-correlated) rather than on the generate line.
---

# MadSpin card-configuration fan-out

**When it applies.** Any "set up / configure a MadSpin decay" ask — spinmode choice, `BW_cut`, bare `decay`/cascade grammar, `set madspin_card ...`, supplying a custom `madspin_card.dat` path, a `Branching ratio larger than one` warning, or a `Failed to update dependent parameter` during a MadSpin launch. MadSpin is post-generation factorized decay on an on-shell production ME (keeps spin correlations + NWA BRs; drops off-shell production interference and tails beyond the window).

## Owner map — route each sub-question
- **spinmode value/default/semantics; `do_decay` grammar; the `launch`-triggers-decay rule; custom-card-path content detection** → `ma-madspin-interface-consultant` (`madspin-options`, `madspin-decay-chain-grammar`, `madspin-mg-invocation`).
- **`set <card>` routing in the launch card-edit dialogue** (why `set madspin_card X` is refused, why bare `set spinmode` works but `set BW_cut`/`set seed` don't, dropped-file-path auto-detect) → `ma-interface-consultant` (`card-dialogue-set-update`).
- **`BW_cut` value + the `-1`→run_card `bwcutoff` inheritance sentinel + its distinct-window nature** → `ma-bw-window-consultant` (`bw-madspin-bwcut-inheritance`).
- **BR>1 warning / hard-fail** → `ma-madwidth-consultant` owns the *denominator* (the param_card total width; fix = `compute_widths`); the *numerator* (MadSpin's own decay cross-section) and the warning/`raise` emission are MadSpin-internal → `ma-madspin-interface-consultant`.
- **`Failed to update dependent parameter`** → `ma-param-card-consultant` (`card-editor-update-commands`).

## Load-bearing traps (behavioural shape → consultant page)
- **`spinmode='full'` is NOT a strict alias for `madspin`.** Same launch dispatch, but `madspin` FORBIDS run_card edits (`interface_madspin.py:474-476`, "edition of the run_card is not allowed within normal mode") while `full` permits run_card cuts on the decay ME, and `decay.py` carries `mode=='full'` branches. If a spec needs cuts applied to the decayed ME, the mode is `full`, not `madspin`. → `ma-madspin-interface-consultant/madspin-options`.
- **`set spinmode` reaches the card via a special_shortcut→`do_add` macro, not `set`-routing** — which is exactly why `set madspin_card X` is refused yet bare `set spinmode X` works. Only `spinmode`/`nodecay` have shortcuts (`init_madspin`); `set BW_cut`/`set seed` fall to generic `do_set` → "invalid set command" and are silently dropped (run_card's key is `iseed`, not `seed`). To override `BW_cut`/`seed` reliably, supply a custom `madspin_card.dat` path (classified by content via `detect_card_type`, not by extension). → `ma-interface-consultant/card-dialogue-set-update`.
- **`BW_cut` and the myamp.f on-shell test are two DISTINCT windows.** `BW_cut` is MadSpin's ±(n·Γ) decay-mass-sampling window (`decay.py:534-535`, raw width, floored 0.5 GeV); the run_card `bwcutoff`/`cut_bw` on-shell test is a separate LO-madevent mechanism (Γ_eff, gForceBW/lbw). `BW_cut=-1` inherits the run_card `bwcutoff` VALUE only when the LHE banner carries a run_card (`:251-252`); with no run_card banner it hardcodes 15.0 (`:265-266`) — both land on 15 for a default card. → `ma-bw-window-consultant/bw-madspin-bwcut-inheritance`.
- **`onshell` mode carries an f2py build dependency** the full/madspin path does not (weight evaluated through compiled `all_matrix2py`, `interface_madspin.py:1770/1799`). A spec choosing `spinmode='onshell'` must have f2py available. → `madspin-options`.
- **Cascade parentheses are a recognized grammar token, NOT universally required** — the two-level default card (`decay t > w+ b, w+ > l+ vl`) uses none; `reorder_branch` handles both no-paren and paren sub-decays. The doc-myth "3-level cascade REQUIRES parens / orders-of-magnitude σ error otherwise" is a runtime claim, unconfirmed from source — a probe-candidate, not a fact.

## Cross-ref
The generate-line-chain ↔ MadSpin-decay splice (existing `>`/comma chain's comma-count → append / distribute / hard-reject; `@` grouping collision) lives in `decay-chain-seams.md`, not here. This page is the MadSpin-card knob fan-out; that page is which attachment path a decay takes.
