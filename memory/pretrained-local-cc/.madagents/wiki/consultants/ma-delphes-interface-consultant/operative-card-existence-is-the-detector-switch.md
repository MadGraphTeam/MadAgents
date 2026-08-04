---
description: PRINCIPLE — the existence of the operative Cards/delphes_card.dat (resp pgs_card.dat) file is THE gating condition at every entry point that could run Delphes/PGS; there is no separate detector on/off boolean
---

# The operative card file IS the detector switch

## Principle
Across every MG code path that could run Delphes (or legacy PGS), the **existence of the
operative `<PROC_DIR>/Cards/delphes_card.dat`** (resp `pgs_card.dat`) is the single gating
condition that decides whether the detector step runs. There is no independent detector-enabled
flag that the card-existence merely reflects — the file's presence on disk IS the switch, at the
shower tail-call, the interactive default, the auto-resolver, and the do_delphes/do_pgs body
itself. To enable Delphes you must get a `delphes_card.dat` onto disk (selecting the detector in
the menu is just the path that materializes it via `keep_cards`); to disable it you remove/hide
the card. This is the unifying mechanism behind the four scattered entry points and explains why
"selecting Delphes" and "a Delphes card exists" are operationally the same thing.

## The gating facets (all source-confirmed, v3.7.1)
Each is one read of the gate; the principle is their union plus future entry points.
1. **Shower tail-call** — `do_pythia8`/`do_pythia` tail-call `delphes --no_default`; `do_delphes`
   with `--no_default` early-returns ("No delphes_card detected, so not run Delphes") if
   `Cards/delphes_card.dat` is absent (common_run_interface.py:3378-3380). So the auto-chain is a
   no-op unless the card exists.
2. **do_delphes body** — copies `delphes_card_default.dat` → `delphes_card.dat` if missing (and
   not no_default), else under no_default early-returns (common_run_interface.py:3400-3406).
3. **Interactive default** — `set_default_detector` sets the launch-switch detector to 'Delphes'
   only if `'Delphes' in available_module` AND shower!='OFF' AND `Cards/delphes_card.dat` already
   exists; else falls to OFF (madevent_interface.py:667-669). Fresh proc dir → OFF (chicken/egg).
4. **Auto-mode resolver** — `ask_pythia_run_configuration` auto mode: `pgs` if py6 AND
   `pgs_card.dat` exists, **elif `os.path.exists(...delphes_card.dat)` → mode='delphes'**, else
   plain pythia (madevent_interface.py:6846-6852). The same function serves the interactive menu
   and the scripted/`self.force` path.
5. **keep_cards materializes the card** — once mode=='delphes' the card name is appended to
   `cards` and `keep_cards` copies `delphes_card_default.dat` → `delphes_card.dat`
   (common_run_interface.py:4019-4020). THIS is the act that flips the switch on.

## Upstream of card-existence
Two preconditions sit above the file gate (see delphes-availability-and-card-provisioning):
- `delphes_path` must be set (check_delphes raises InvalidCmd otherwise; the shower tail-call is
  itself gated on `if self.options['delphes_path']`).
- `check_available_module` adds 'Delphes' to `available_module` only if PY6 or PY8 is present
  (madevent_interface.py:530-532) — no shower ⇒ Delphes silently unavailable, card or not.

## Runtime consequence — INFERRED, not probe-confirmed
INFERRED from the gates above: an LO `generate_events` run produces Delphes ROOT output IFF a
`delphes_card.dat` is on disk at shower-end, and is a silent no-op otherwise. NOT probe-verified
in this environment — a full probe needs `delphes_path` set, built Delphes binaries, and a Pythia
shower (delphes_path is unset by default here; only a `Delphes/` dir is present). Treat the
"runs/no-op" behavior as inference from the gating reads, not as observed runtime fact, until probed.

## Caveat — NLO
The shower-tail-call facet (1) does NOT apply on the NLO path: amcatnlo_run_interface.py has no
`exec_cmd('delphes --no_default')` tail-call (NLO does not auto-chain — see
delphes-trigger-chain-from-shower-step and nlo-amcatnlo-delphes-path). On NLO the card still
gates the inherited do_delphes body (facet 2), but the run does not reach do_delphes automatically.

## Instance pages (kept)
delphes-trigger-chain-from-shower-step (facets 1,3,4), do_delphes-flow (facet 2),
delphes-availability-and-card-provisioning (facets 3,5 + upstream), card-templates-and-defaults
(what the _default the card is copied from actually contains — CMS geometry).
