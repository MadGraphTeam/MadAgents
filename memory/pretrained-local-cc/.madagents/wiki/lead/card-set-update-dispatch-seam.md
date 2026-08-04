---
description: Editing a card by typing set/update at the interactive launch dialogue rather than by writing the card file.
---

# Card-editing `set` / `update` — dispatch-vs-semantics seam

When a task edits a card in the interactive `ask_edit_cards` dialogue (`set <param> <value>`, `update <block>`, `set <block> <param> <value>`), two different slices own two different halves. Split the dispatch or you route the whole thing to the wrong expert.

## The split

- **Command SURFACE** (how the keystroke is parsed/dispatched, what the dialogue accepts, tab-completion, `update`/`set`/`done`/`open` grammar) → **`ma-interface-consultant`** (`common_run_interface.py` `ask_edit_cards` / `do_set` / `do_update`; `extended_cmd.py` SmartQuestion). Consultant page: `../consultants/ma-interface-consultant/card-dialogue-set-update.md`.
- **Parameter SEMANTICS + legality** (what the value means, its allowed range/type, its default, whether the value is physically/regime-valid) → the **owning card slice** for that parameter (run_card knob → scales-pdf / kinematic-cuts / matching / systematics / launch; param_card entry → param-card; width → madwidth). The interface consultant does *not* own whether `dynamical_scale_choice = 7` is legal — the scales-pdf slice does.

Mark the cross half as a premise when you dispatch: to interface, *"Given (premise) the value's legality is owned elsewhere — describe only how the dialogue dispatches the keystroke"*; to the card slice, *"Given (premise from interface) the dialogue passes the value through un-validated at set-time — is this value legal, and what does it mean?"*.

## Trap 1 — two-layer validation (set-time pass-through → write-time check/revert)

An interactive `set` in the card dialogue does **not** validate at keystroke time: the dialogue path calls the card setter with `raiseerror=False`, so an out-of-range or misspelled value is accepted silently and stored. Validation is **deferred to banner write-time** (`banner.py` `check_validity` on the RunCard), where an illegal value **WARNs and reverts to the default** rather than raising. Consequence for dispatch: *"I set X in the dialogue and it took, but the run used the default"* is **not** an interface bug and **not** a card-corruption bug — it is `check_validity` silently reverting an invalid value. Route the "why did my set not stick" question to the **owning card slice's write-time validator**, not to interface (interface only confirms the set-time pass-through). This is the `config-value-lifecycle-layers` pattern specialized to the card dialogue — latest layer (write-time check) governs over the earlier (set-time store).

## Trap 2 — `update <block>` reveal is LO-run_card-only

`update <block>` (e.g. `update mlm`, `update ecut`, the block-reveal that exposes a hidden parameter block) is defined on the **LO `RunCardLO`** class only. The **NLO `RunCardNLO`** class exposes only a small `update` set (`[ion_pdf, RUNNING]`), so `update mlm`/beam-pol/most-block reveals are **unavailable at an NLO run_card dialogue**. When a task says "reveal/enable block B via `update`", first pin the card class (LO vs NLO output) — the same command name has a different (and much smaller) reach at NLO. This is a specific instance of the broader `runcard-lo-nlo-value-divergence` trap (the LO and NLO run_cards are different classes with different surfaces); pin the class before quoting any `update`/default behaviour.

## Trap 3 — special-shortcut macros dispatch here, values live elsewhere

Card-dialogue macros like `no_parton_cut` and `pbpb` (heavy-ion) are `special_shortcut` entries: the **macro dispatch** (the keyword→action mapping in the dialogue) is interface/launch surface, but the **values each macro writes** are owned by the value's slice (e.g. `pbpb` beam/PDF settings → scales-pdf; `no_parton_cut` → `remove_all_cut`, and note bwcutoff *survives* it → kinematic-cuts + bw-window). Don't let the macro's convenience hide the owning slice — route "what does macro M actually set" to the slice that owns the written values, not to interface.

See also: `interactive-mode-fanout.md` (the broader REPL command surface + the LO-vs-NLO **launch** dialogue class split), `config-value-lifecycle-layers.md` (the set→parse→runtime latest-layer-governs precedence this specializes), `runcard-lo-nlo-value-divergence.md` (the value/name divergence behind trap 2).
