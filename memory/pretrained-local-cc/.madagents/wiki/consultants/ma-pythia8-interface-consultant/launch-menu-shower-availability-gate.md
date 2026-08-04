---
description: The interactive launch ControlSwitch (AskRun) shower menu — what gates Pythia8 being OFFERED, how shower=PYTHIA8/py8 resolves, and default selection. Menu availability checks ONLY pythia8_path, NOT the interface.
---

# Launch-menu shower switch (AskRun ControlSwitch) — availability gate

Covers the interactive `launch` / `generate_events` menu ("Choose the shower/hadronization program"), distinct from the auto-launch `shower --no_default` chain (see lo-autolaunch-entry-chain.md). Class `AskRun(cmd.ControlSwitch)` (`madevent_interface.py:497`), switch key `shower` (`to_control` `:500`).

## What gates Pythia8 being OFFERED in the menu (claim-3 answer)
`check_available_module` (`:516-544`) builds `self.available_module` from config paths:
- `if options['pythia8_path']: available_module.add('PY8')` (`:522-523`) — **the sole gate.**
- `if options['pythia-pgs_path']:` -> `PY6` + `PGS` (`:519-521`).
- Delphes needs PY6 or PY8 present first (`:530-534`); Rivet needs PY8 (`:535-539`).

`get_allowed_shower` (`:560-573`) appends `'Pythia8'` to the menu **iff `'PY8' in available_module`** (`:569-570`), i.e. iff `pythia8_path` is set. So the gating predicate for `shower=Pythia8` being available in the launch menu is:

**`options['pythia8_path']` is truthy (non-empty).**

The menu availability check does **NOT** look at `mg5amc_py8_interface_path` — Pythia8 is offered on `pythia8_path` alone. The interface requirement (if any) is enforced later, inside `do_pythia8` (see claim-2 note below).

## How `shower=PYTHIA8` / `py8` resolves (claim-1 answer)
Canonical switch values are **case-mixed**: `Pythia6`, `Pythia8`, `OFF`, `Not Avail.` (`:566-586`). The launcher-dialog verification value `shower=PYTHIA8` resolves via two independent mechanisms:
- Generic case-fold in `ControlSwitch.set_switch` (`extended_cmd.py:2749-2766`): when the key is not case-sensitive and the raw value isn't in `get_allowed`, it lowercases the allowed list and indexes — `'pythia8'` matches `'Pythia8'`, value normalized to `'Pythia8'` (`:2759-2766`). So `PYTHIA8`, `pythia8`, `Pythia8` all resolve.
- Shortcut aliases in `check_value_shower` (`:588-600`): `py8` / `p8` / `pythia_8` -> `'Pythia8'` (and `py6`/`p6`/`pythia_6` -> `'Pythia6'`), each gated on the module being in `available_module`. NOTE this shortcut list does **not** contain bare `pythia8` — that string only resolves via the set_switch case-fold path above, not here.

## Default selection (set_default_shower `:575-586`)
- `PY6` available AND `Cards/pythia_card.dat` exists -> default `Pythia6` (`:577-579`).
- ELSE `PY8` available AND `Cards/pythia8_card.dat` exists -> default `Pythia8` (`:580-582`).
- ELSE any shower allowed -> `OFF` (`:583-584`); else `Not Avail.` (`:585-586`).
So a bare pythia8_card.dat presence is what makes `Pythia8` the *preselected* default (PY6+its card wins if both present).

## Where the switch value connects to the run
The switch does not itself call `do_pythia8`. `switch['shower']=='Pythia8'` -> `pythia8_card.dat` appended to the kept-cards list (`:6768-6769`), so the default card is copied into Cards/ if absent. The actual shower then runs through `generate_events` -> `shower --no_default` -> `do_pythia8`, whose top-of-function gate is the *presence* of `Cards/pythia8_card.dat` (lo-autolaunch-entry-chain.md). So the menu choice's real effect is guaranteeing the card exists for that later card-existence gate.

## Claim-2 correction: interface is NOT required on the default path
`do_pythia8` interface selection (`:4600-4655`): default (no `--old_interface`) sets `pythia_main = <pythia8_path>/share/Pythia8/examples/main164` (fallback `<pythia8_path>/examples/main164`) (`:4650-4652`). `main164` ships **inside the Pythia8 build**, so the default path needs ONLY `pythia8_path`. `mg5amc_py8_interface_path` is required **only** for `--old_interface` (`:4635-4642`, InvalidCmd if the binary is missing), which is also the automatic fallback when `main164` is not found/compiled (`:4653-4655`, warns then re-calls with `--old_interface`).

So "Pythia8 showering requires BOTH the pythia8 build AND mg5amc_py8_interface" is **outdated for v3.7.1**: the default main164 path requires only the pythia8 build. Both keys are real config keys (`mg5_configuration.txt:77,84`), but the interface is a legacy/fallback dependency, not a hard co-requirement.
