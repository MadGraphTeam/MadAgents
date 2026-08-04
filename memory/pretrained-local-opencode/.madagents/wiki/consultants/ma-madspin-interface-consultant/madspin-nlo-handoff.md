---
description: MadSpin at NLO — the two distinct fixed_orders, the NLO launch-switch gate (OFF/ON/onshell, QED-split blocks it), fixed_order counter-event handling is onshell-only, frame_id forced to the NLO frame
---

# MadSpin ↔ aMC@NLO handoff

NLO decay attachment reuses the SAME dispatch as LO: `do_decay_events` at
`$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py:4169` (there is NO NLO override —
grep `def do_decay_events` finds only this one). aMC@NLO invokes it via
`self.exec_cmd('decay_events -from_cards')` at `amcatnlo_run_interface.py:1864`. So the card
templating, option handoff, and banner round-trip are identical to LO (see madspin-mg-invocation).

## TWO distinct `fixed_order` — do not conflate
1. **aMC@NLO launch-dialog switch `fixed_order`** (`amcatnlo_run_interface.py:925` "No MC@[N]LO
   matching / event generation"). ON = fixed-order (fNLO) parton-level computation, no event
   generation, no matching. This is the amcatnlo slice, NOT a MadSpin option. When this switch is
   ON there are (conceptually) no unweighted events in the normal sense — you get grouped
   fNLO events.
2. **MadSpin card option `fixed_order`** (`MadSpin/interface_madspin.py:72`, default `False`,
   comment "to activate fixed order handling of counter-event"). This is the MadSpin-side flag that
   tells MadSpin to read the input LHE as EVENT GROUPS (fNLO event + its counter-events).

These are independent knobs with the same name in different files.

## MadSpin card `fixed_order` is ONSHELL-ONLY
- `post_fixed_order` (interface_madspin.py:121) emits two warnings when set True (:125-126):
  "Fix order madspin fails to have the correct scale information. This can bias the results!" and
  "Not all functionalities of MadSpin handle this mode correctly (only onshell mode so far)."
- SOURCE-CONFIRMED: every `self.options['fixed_order']` branch lives in the onshell path only —
  `run_onshell` (def :1373, ends :1577): :1410, :1417, :1530, :1542, :1553, :1557; and
  `get_maxwgt_for_onshell` (:1636-1695): :1662. NO `fixed_order` branch exists in `run_bridge`
  (spinmode none) or the full/madspin launch path. So the warning is literally true.
- What it does (:1410-1418): `orig_lhe.eventgroup = True`, then per iteration `event = event[0]`
  takes the representative event of each group. Counter-events ride along in the group.

## NLO launch-switch gate for MadSpin (amcatnlo_run_interface.py)
- `get_allowed_madspin` (:1305): visible values = `['OFF','ON','onshell']` (:1324). Distinct from
  the LO switch (which offers full).
- **QED corrections block MadSpin**: if `'QED' in proc_characteristics['splitting_types']` →
  `allowed = ['OFF']` (:1321-1322). EW-correction NLO cannot use MadSpin.
- **Decay process (1→N) removes MadSpin**: `ninitial==1` → `available_module.remove('MadSpin')`,
  `allowed=['OFF']` (:1316-1319).
- `set_default_madspin` (:1351): ON iff a `madspin_card.dat` already exists, else OFF.
- Switch value → card `set spinmode` write, via `get_cardcmd_for_madspin` (:1361):
  - `onshell` → `set spinmode onshell` (:1365)
  - `full`/`madspin`/ON → `set spinmode madspin` (:1367)  [ON maps to madspin, NOT onshell]
  - `none` → `set spinmode none` (:1369)
  Each is an `edit madspin_card --replace_line='set spinmode' --before_line='decay'` card-edit.
- `check_value_madspin` (:1327) alias map for out-of-visible-list input: `madspin`/`full`→`'full'`,
  `none`→`'none'` (:1346-1349). So `none` and `full` are reachable by typing them even though not
  in the visible `['OFF','ON','onshell']`.

## frame_id forced to the NLO frame at NLO
`do_import` (interface_madspin.py:256-260): for `RunCardLO` input, `frame_id` inherits
`run_card['frame_id']`; for the NLO branch (else, i.e. RunCardNLO) `frame_id` is FORCED to a fixed value.
frame_id is the polarization-frame id (default at MadSpinOptions.default_setup :77; the NLO forced value at :260 — read both fresh).

## spinmode at NLO — summary
- All four spinmodes (full/madspin/none/onshell) exist in the option enum regardless of order
  (interface_madspin.py:69 `allowed=['full','madspin','none','onshell']`); the LO/NLO distinction is
  in what the LAUNCH GATE surfaces and which mode handles fNLO counter-events.
- NLO gate surfaces OFF/ON(→madspin)/onshell; none/full reachable by alias.
- For decaying fixed-order (fNLO) event files with counter-events, ONLY onshell handles
  `fixed_order` correctly.
- By DEFAULT the NLO madspin card carries `fixed_order=False` — `do_decay_events` does not set it,
  and `get_cardcmd_for_madspin` only writes `set spinmode`. So the standard NLO+PS (MC@NLO) MadSpin
  run does not use the fixed_order counter-event grouping unless the user opts in. (INFERRED that the
  MC@NLO event-file structure vs fNLO-group structure is what makes fixed_order opt-in only —
  the eventgroup mechanism is source-clear; the LHE-structure mapping is amcatnlo/lhe_parser
  territory.)

## Boundaries (not my slice)
- Whether MadSpin "preserves spin correlations" / the physics of decaying between fixed-order and
  shower — decay.py internals + physics slice. Interface only confirms the mechanism exists and runs
  post-generation.
- Comma-chain decays (`p p > t t~, t > w+ b [QCD]`) rejected in the generate line at NLO —
  nlo-syntax / chain-decay slice. MadSpin is the post-generation alternative.
- The fNLO-vs-MC@NLO event-file structure that eventgroup reads — amcatnlo slice.
