---
description: The parton_shower run_card parameter — NLO-only (RunCardNLO, no LO analogue), code default HERWIG6, allowed-list ['HERWIG6','HERWIGPP','PYTHIA6Q','PYTHIA6PT','PYTHIA8'] enforced at run() not card-write, bidirectional switch↔card propagation (force-mode skips the shower→card auto-set), and the shower_mc→montecarlocounter.f MC@NLO-subtraction linkage.
---

# `parton_shower` — the NLO shower-selection run_card parameter

## NLO-only (claim: LO cards have no parton_shower — TRUE)
`add_param('parton_shower', 'HERWIG6', fortran_name='shower_mc')` appears at `$MADGRAPH_INSTALL/madgraph/various/banner.py:5668`, inside `class RunCardNLO(RunCard)` (5594). Grep of the `RunCardLO` body (banner.py:4187–5593) for `parton_shower` returns **0** hits; no occurrence in `madevent_interface.py` or the LO `run_card.dat` template. So `parton_shower` is a RunCardNLO-only key — the LO run_card has no shower-program selector (LO shower choice is made only in the `AskRun` launch dialog, not written into the LO card).

## Code-level default = HERWIG6 (claim: TRUE)
Class default is `'HERWIG6'` (banner.py:5668). **Caveat — the written per-process card may differ:** `create_default_for_process` flips it to `PYTHIA8` (banner.py:6123) when the process is FxFx-eligible (multi-multiplicity, all extra legs jets → matching=True, also sets ickkw=3, fixed scales False, jetalgo=jetradius=1). So the class default is HERWIG6 but a generated run_card for an FxFx-eligible process ships PYTHIA8. Read the actual card, not the class default, before claiming the shower ([[runcardnlo-defaults-and-ickkw]]).

## Allowed values (claim list is exact) — enforced at run(), NOT at card-write
Valid set = `['HERWIG6', 'HERWIGPP', 'PYTHIA6Q', 'PYTHIA6PT', 'PYTHIA8']`. The `add_param` at 5668 carries **no `allowed=` list**, so `RunCardNLO.check_validity` does NOT reject a bad shower name at card-write. Enforcement is at runtime in `aMCatNLOCmd.run()`:
- `amcatnlo_run_interface.py:2003`: `shower_list = ['HERWIG6', 'HERWIGPP', 'PYTHIA6Q', 'PYTHIA6PT', 'PYTHIA8']`; `2005` raises `aMCatNLOError` if `parton_shower.upper()` not in it.
- `2011`: `PYTHIA6PT` + `proc_characteristics['has_fsr']` → raises ("PYTHIA6PT does not support processes with FSR").
This is a soft-net instance ([[nlo-card-validation-is-a-soft-net]]): the shower-name error surfaces at launch, not card-write. (HERWIG7 is a dialog alias, normalised to HERWIGPP by the `answer` property — it is NOT a distinct run_card value; the card carries HERWIGPP.)

## Switch ↔ card propagation is bidirectional; the shower→card auto-set is INTERACTIVE-ONLY
Two directions between the `AskRunNLO` `shower` switch and `run_card['parton_shower']`:
- **card → switch (default seed):** `set_default_shower` (1244) seeds `self.switch['shower'] = self.run_card['parton_shower']` (1254, 1278). The dialog's default shower is whatever the card says.
- **switch → card (override):** picking a shower emits a card-edit command. `get_cardcmd_for_shower` (1295) returns `['set parton_shower %s' % self.switch['shower']]` (1299) for any non-OFF value; `ControlSwitch.get_cardcmd` (extended_cmd.py:2598-2607) aggregates it; `ask_run_configuration` passes it as `first_cmd` to `ask_edit_cards` (amcatnlo_run_interface.py:5869, 5872). So choosing `shower=PYTHIA8` in the dialog runs `set parton_shower PYTHIA8` on the run_card BEFORE the banner charges the card (5877-5884) → the banner snapshot also gets PYTHIA8.

**Claim "shower=PYTHIA8 AUTOMATICALLY overrides parton_shower" — TRUE in interactive mode, with a force-mode caveat.** The `ask_edit_cards(first_cmd=...)` call is inside `if not options['force'] and not self.force:` (5871). In `-f`/scripted/force mode `ask_edit_cards` is skipped, so the `set parton_shower` from the shower switch is **never applied** — `get_cardcmd()` at 5869 is computed then discarded (grep confirms first_cmd is used only at 5872). Consequence: under `launch -f`, the run_card's own `parton_shower` value governs (validated at run():2003); a mismatched `shower=` launch option does not rewrite it. In scripted mode set `parton_shower` in the run_card directly.

## parton_shower drives the MC@NLO subtraction (claim: TRUE — structural linkage)
`fortran_name='shower_mc'` (5668) writes `shower_mc = '<PARTON_SHOWER>'` into the generated run-card include. In Fortran: `run.inc:67-68` declares `character*10 shower_mc` / `common /cMonteCarloType/shower_mc`. `montecarlocounter.f` (the MC@NLO Monte-Carlo counterterms subtracted from S-events so the shower doesn't double-count) branches on `shower_mc`:
- shower scale `qMC` per program (`montecarlocounter.f:3348-3351`: HERWIG6/HERWIGPP use `xi_i_fks/2*sqrt(...)`, PYTHIA6Q `sqrt(-xtk)`, etc.),
- dead-zone / ipartner assignment per program (1157-1187, 401),
- FSR/ISR handling (1102 PYTHIA6PT special-case).

So `parton_shower` selects **which shower's MC counterterms** are computed — the subtraction is shower-specific and MUST match the shower the events are actually fed to. **Physics-correctness note (route to physics / probe, not asserted here):** a parton_shower ≠ actual-shower mismatch means the subtracted MC counterterms don't correspond to the shower's real emission probability → incorrect MC@NLO result (double-count or over-subtraction). The montecarlocounter.f internals themselves are fks / nlo-export territory; the in-slice bridge is the `fortran_name` mapping (5668) + the `run.inc` common block.

## Verification status
The NLO-only default, allowed-list, run()-time enforcement, and montecarlocounter.f linkage are source-verified at the cited lines. The bidirectional switch↔card propagation is source-verified (1299 → 2606 → 5872); the force-mode skip is source-grounded (the 5871 guard is explicit) but the end-to-end behavioral consequence ("`launch -f shower=PYTHIA8` leaves a HERWIG6 card unchanged") is a runtime prediction — structurally certain, not probe-confirmed through a full scripted launch. The mismatch → wrong-physics consequence is a physics claim, not source-asserted.
