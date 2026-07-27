---
description: MG launch-menu MadSpin gate — LO vs NLO allowed-mode tables (process-characteristic gating) and the switch-value -> 'set spinmode' card-edit writer
---

# Launch-switch MadSpin gate and switch -> card mapping

This is the MG-side invocation gate that runs BEFORE MadSpin is ever constructed: the
`launch`/`generate_events` interactive switcher decides whether MadSpin is OFFERED and what
spinmodes are selectable, then translates the chosen switch value into a card edit. All in slice
(MG-side invocation/handoff). The deeper NLO `decay_events` mechanics remain the amcatnlo slice.

## The switch label (LO and NLO)
- LO switcher `to_control` entry: `('madspin', 'Decay onshell particles')`
  (`$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py:503`).
- NLO switcher entry: `('madspin', 'Decay onshell particles')`
  (`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py:927`).

## LO allowed-mode table (madevent_interface.py)
`get_allowed_madspin` (:827-836):
```
self.allowed_madspin = ['OFF',"ON",'onshell',"full"]   # :835
```
- Exposes `OFF`, `ON`, `onshell`, `full` at the LO prompt. `ON` = run with the card's existing
  spinmode (default `madspin`); `onshell`/`full` are named-mode overrides. There is NO `none`
  in the allowed list (but `check_value_madspin` still aliases `none` -> `'none'`, see below).
- `set_default_madspin` (:855-863): switch defaults to `'ON'` IFF `Cards/madspin_card.dat` exists,
  else `'OFF'`; `'Not Avail.'` if the MadSpin module is absent. So the mere PRESENCE of a card
  flips the launch default to ON (ties to do_decay_events :4173 silent-skip on missing card —
  see madspin-mg-invocation).
- `check_value_madspin` (:838-850): accepts allowed values case-insensitively; additionally
  aliases `madspin`/`full` -> `'full'`, `none` -> `'none'` (so a typed `none`/`madspin` is honored
  even though not in `allowed_madspin`).

## NLO allowed-mode table — process-characteristic gated (amcatnlo_run_interface.py)
`get_allowed_madspin` (:1305-1325):
- module absent -> `[]`.
- `proc_characteristics['ninitial'] == 1` (a DECAY process, 1->N) -> MadSpin removed from
  `available_module`, allowed = `['OFF']` (if at :1316, `available_module.remove` :1317,
  assign :1318). NLO decay processes cannot MadSpin.
- `'QED' in proc_characteristics['splitting_types']` (EW corrections) -> allowed = `['OFF']`
  (if at :1321, assign :1322). Mirrored by `print_options_madspin` returning literal "No madspin
  for EW correction" (:1106-1110).
- else -> `['OFF', 'ON', 'onshell']` (:1324). NOTE: NLO offers `onshell` but NOT `full` (unlike LO).
  Consistent with `fixed_order` being onshell-only (see madspin-onshell-interface-algorithm) and
  the NLO+MadSpin validation scope.
- `consistency_QED` (:1122+) additionally forces `madspin` into `['OFF','none']` when QED splitting
  present (:1131) — a consistency clamp distinct from the allowed-list gate.

So the LO vs NLO offering asymmetry is: LO = {OFF,ON,onshell,full}; NLO(non-QED,2->N) =
{OFF,ON,onshell}; NLO(QED or 1->N) = {OFF}.

## switch value -> card edit (the writer)
`get_cardcmd_for_madspin(value)` (madevent_interface.py:866-876) returns the pre-card-edit command
list that injects the spinmode into the card BEFORE the user edits cards:
- `'onshell'` -> `["edit madspin_card --replace_line='set spinmode' --before_line='decay' set spinmode onshell"]`
- `'full'`/`'madspin'` -> `... set spinmode full`
- `'none'` -> `... set spinmode none`
- anything else (incl. `'ON'`, `'OFF'`) -> `[]` (no edit).

Key semantics:
- `--replace_line='set spinmode'` OVERWRITES any existing `set spinmode` line in the card; if none
  exists, `--before_line='decay'` inserts it before the first `decay` line. So the switch value
  authoritatively sets the card's spinmode.
- `'ON'` emits NO edit -> the card runs with WHATEVER spinmode it already carries (default
  `madspin` if the card has no `set spinmode`). So "ON" at the prompt is NOT "spinmode=onshell"
  despite the switch label saying "Decay onshell particles" — the label is legacy; ON = the card's
  own mode.
- `'OFF'` emits no edit and (separately) the switch being OFF means do_decay_events is not invoked.

## Cautions
- The switch label "Decay onshell particles" is misleading: selecting `ON` does NOT force onshell;
  it runs the card's spinmode (default `madspin`, the full spin-correlated mode). Only explicitly
  choosing `onshell` writes `set spinmode onshell`.
- NLO silently drops `full` from the menu; a user wanting full spin correlation at NLO will not see
  it offered (only `onshell`).
- A QED/EW-correction NLO process or a 1->N decay process gets MadSpin GATED OFF at the menu — not
  an error, just unavailable. (This is the menu gate; whether a hand-forced card would run is a
  separate question, untested here.)

## Gaps
- The deeper NLO `decay_events` (decay_events for NLO+PS, counter-event handling beyond the onshell
  interface seam) is the amcatnlo slice.
- Whether forcing spinmode via direct card edit bypasses the NLO menu gate is a runtime question
  (probe-candidate), not settled from the switch source alone.
