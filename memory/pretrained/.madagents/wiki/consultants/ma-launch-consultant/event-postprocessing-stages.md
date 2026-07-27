---
description: Launch-time post-unweighting event-modification hooks — boost_events (run_card boost_event lambda, in-place LHE boost) and add_time_of_flight (exponential decay-vertex sampling), their guards and order in run_generate_events.
---

# Event post-processing stages (boost_events, add_time_of_flight)

Two launch-time event-modification stages run AFTER store_events (i.e. after the unweighted LHE exists), between store and the downstream tools. Both rewrite the event file in place. Cites `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (ME), `common_run_interface.py` (CR), `madgraph/various/banner.py` (defaults), v3.7.1.

## Order in run_generate_events (ME 2650-2659)
```
2650  create_plot('parton')
2651  store_events
2652  if run_card['boost_event'].strip() and run_card['boost_event'] != 'False':  boost_events()
2656  reweight -from_cards
2657  decay_events -from_cards
2658  if run_card['time_of_flight'] >= 0:  add_time_of_flight --threshold=<time_of_flight>
```
So boost happens BEFORE reweight/decay; time-of-flight happens AFTER decay (so it can stamp the daughters of MadSpin decays). The call-site boost guard (`boost_event.strip() and != 'False'`) is what actually decides whether `boost_events` runs — distinct from the method's own internal guard.

## boost_events (ME 2679-2716)
- Internal guard: returns immediately if `not run_card['boost_event']` (2681-2682).
- `boost_event` MUST start with `'lambda'` (2684) — it is `eval`'d into a Python filter function. Anything else -> bare `raise Exception` (2689). So the only valid non-False value is a lambda expression.
- **Online-disallowed**: if `not isinstance(self, cmd.CmdShell)` -> `raise Exception("boost not allowed online")` (2685-2686). Boost works only from the interactive/command-line shell, never the web interface.
- Picks the first existing of `unweighted_events.lhe.gz / unweighted_events.lhe / events.lhe.gz / events.lhe` in `Events/<run>/` (2691-2701); raises "fail to find event file for the boost" if none.
- Loops events, calls `event.boost(filter)` (lhe_parser), writes to a TMP file, then `files.mv` back over the original (in-place rewrite, 2704-2716).
- Physics (from the banner.py comment, see below): the boost puts AT REST the sum of 4-momenta of the particles the filter selects. Example `lambda p: p.pid==25` -> Higgs rest frame.

### boost_event default (banner.py:4295)
`add_param("boost_event", "False", hidden=True, include=False, comment="...boost the full event. The boost put at rest the sum of 4-momenta of the particle selected by the filter... example going to the higgs rest frame: lambda p: p.pid==25")`. Hidden param, string default `"False"`, `include=False` (never written to run.inc — pure Python-side, consumed only by boost_events). Default never triggers (guard at 2652).

## add_time_of_flight (CR 2476-2528)
- Invoked as `add_time_of_flight --threshold=<time_of_flight>` from the launch flow (ME 2659); `time_of_flight` is passed as the threshold.
- Gunzips the event file if `.gz`, parses with lhe_parser, writes a `<file>_2vertex.lhe` then `files.mv` back, re-gzips if needed.
- Reads the param_card embedded in the LHE banner `<slha>...</slha>` (2504-2507) to get particle widths.
- **Per particle**: `width = param_card['decay'].get((abs(pid),)).value`; if width nonzero, draws `vtim = c * random.expovariate(width/cst)` and sets `particle.vtim = vtim` only if `vtim > threshold` (2512-2519).
  - `cst = 6.58211915e-25` (hbar in GeV·s), `c = 299792458000` (speed of light in mm/s) (2509-2510). So `vtim` is a proper-decay-length sample in mm: mean length `= c * hbar / width = c * tau`. `random.expovariate(lambda)` draws an exponential with mean `1/lambda = cst/width`, times c gives mm.
  - `threshold` (the run_card `time_of_flight`) is the minimum displacement in mm below which no vtim is stamped (suppresses negligibly-displaced vertices).

### time_of_flight default (banner.py:4213)
`add_param("time_of_flight", <off-sentinel>, include=False)` (banner.py:4213 — read the literal). Default is a negative off-sentinel, `include=False`. The launch guard `time_of_flight >= 0` (ME 2658) means the default (negative) leaves the stage OFF; set it to `0` to stamp all displaced vertices, or to a positive mm threshold to stamp only longer-lived ones.

## Cautions
- `boost_event` is a hidden run_card param that takes a Python lambda string and is `eval`'d — a non-lambda, non-"False" value crashes the run with a bare Exception (ME 2689), and any value crashes if launched online ("boost not allowed online"). It is a shell-only, expert feature.
- time-of-flight stamping runs AFTER decay_events, so MadSpin-decayed daughters get their vtim from the decayed-LHE's banner param_card widths; a width of 0 in that param_card means no vtim for that pid (stable in the sample).
- Both stages rewrite the event file in place (mv over the original); a crash mid-stage can leave a TMP/`_2vertex` file or a half-written event file.
- These are run_card-content params (defined in banner.py — card-slice territory for the param definitions); the launch-time CONSUMPTION (which guard fires, what the stage does) is the launch slice. Boundary: lhe_parser `event.boost` / `expovariate` mechanics and MadSpin decay internals are not this slice.
