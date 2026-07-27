---
description: At shower stage aMC@NLO reads run_card values (parton_shower, nevents, pdlabel, ICKKW, MC masses, ALPHAEW) from the BANNER snapshot frozen in the event file, not the live Cards/run_card.dat — integration-time run() reads the live card; the two read-sources diverge after a post-launch card edit.
---

# Shower stage reads the banner snapshot, not the live run_card

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`.

## The principle (two read-sources for the same run_card value)
A run_card value is consulted at TWO different stages of an aMC@NLO run, and the two stages read from DIFFERENT copies:

- **Integration / validation (`run()`, 1923)** reads the **live `Cards/run_card.dat`**. E.g. `run():1986`: `shower = self.run_card['parton_shower'].upper()`, validated against the fixed 5-name list at 2003; `nevents`/`req_acc` also `self.run_card[...]` (1987-1988).
- **Shower invocation (`run_mcatnlo` 3911, `banner_to_mcatnlo` 4629)** reads the **banner snapshot frozen in the event file**. `run_mcatnlo:3920` reloads `self.banner = banner_mod.Banner(evt_file)`, then `3921`: `shower = self.banner.get_detail('run_card','parton_shower')`. `banner_to_mcatnlo:4633`: `shower = self.banner.get('run_card','parton_shower')`; `pdlabel` (4634), `nevents` (4641), MC masses (4706-4728), `ALPHAEW` (4658-4687), `ICKKW`/`EVENT_NORM`/`DELTA`/`PTJCUT` (4729-4787) — ALL `self.banner.get*('run_card',...)`.

So: **the shower obeys the run_card values as they were at LAUNCH (written into the event-file banner), not the current `Cards/run_card.dat`.** A hand-edit to `Cards/run_card.dat` between launch and shower changes what `run()` would validate but NOT what the shower uses.

## Why this catches more than its instances
- Beyond `parton_shower`: the same banner-read applies to `nevents`, `pdlabel`, `ICKKW` (FxFx flag passed to shower), MC masses, `ALPHAEW`, `DELTA`(mcatnlo_delta), `PTJCUT`(ptj) — every shower-input drawn in `banner_to_mcatnlo`.
- Beyond FxFx: [[fxfx-ickkw3-lifecycle]] covers only `ickkw`; this principle covers any run_card key reaching the shower.
- The two method pages ([[runtime-shell-commands]], [[print-summary-and-event-assembly]]) each state their own banner-read but not the *contrast* with `run()`'s live-card read. The divergence IS the generalization.

## The `do_shower` corollary (sharpest case)
`do_shower` (1529) re-showers an existing `events.lhe`: it builds `evt_file` from the dir arg and calls `run_mcatnlo` directly (1538-1539), which reloads the banner from that file (3920). So **`shower <run>` uses the run_card values from the event file's banner header — never the current `Cards/run_card.dat`.** Editing `Cards/run_card.dat` then `shower`-ing an old run silently ignores the edit.

## Boundary
- This is **read-source** divergence (which stored copy is consulted), orthogonal to the value-*mutation* lifecycle shape (which stage last WROTE the value — that is [[fxfx-ickkw3-lifecycle]] and the lead's config-value-lifecycle playbook). A value can be both mutated across stages AND read from different sources; keep the two axes separate.
- The banner is written at launch by `ask_run_configuration` (the `Banner()` build + card charge, ~5874-5890). To change a shower-stage value you must regenerate (new launch → new banner) or edit the banner inside the event file, not the live card.

## Verification status
Source-verified (the two read-sites are unambiguous: `self.run_card[...]` at 1986 vs `self.banner.get*('run_card',...)` at 3921/4633). The end-to-end behavioral consequence ("a post-launch run_card edit is ignored at shower") is a runtime prediction — structurally certain from the read-sites but not probe-verified through a full launch→edit→shower cycle (needs installed PY8 + a completed aMC@NLO event file). Marked as prediction, not probed fact.
