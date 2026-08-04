---
description: launch_ext_program.py MELauncher/Pythia8Launcher — self.delphes is vestigial; Delphes runs inside MadEventCmd.do_delphes, not the launcher
---

# Launchers in launch_ext_program.py

`$MADGRAPH_INSTALL/madgraph/interface/launch_ext_program.py`

## MELauncher (line 584)
- `__init__` sets `self.pythia = options['pythia-pgs_path']` (592) and
  `self.delphes = options['delphes_path'],` (593 — **note trailing comma → a 1-tuple**).
- **Both `self.pythia` and `self.delphes` are set but NEVER READ** anywhere in this file
  (grep: only the two assignment lines). They are vestigial.
- `launch_program` (614) just builds and runs a `generate_events <name>` command through a
  child `MadEventCmd`. Delphes/PGS are NOT invoked here — they run later inside MadEventCmd
  via `do_delphes`/`do_pgs` (common_run_interface.py) when the run reaches the delphes/pgs
  step. So the real MG→Delphes handoff is `do_delphes`, not this launcher.

## Pythia8Launcher (line 718) — legacy standalone
- Docstring of `prepare_run` (728-729) says "ask for pythia-pgs/delphes run", but the BODY
  (731-787) globs `main_*_*.cc` example files and asks "Select a main file to run:" (752),
  then compiles+runs that standalone Pythia8 example (launch_program 789-815). It does NOT
  prompt for a Delphes/PGS detector mode.
- This is the OLD standalone-Pythia8 external program, distinct from the modern MadEvent →
  Pythia8 integration. No Delphes wiring here.

## Caution
The card description "Pythia8Launcher.prepare_run asks the user to choose pythia-pgs/delphes
run mode" is STALE for v3.7.1 — the docstring suggests it, the code does not. The detector
run-mode choice in modern runs comes from the `generate_events`/`shower` step and the
laststep gating in madevent_interface.py (delphes requires delphes_path, line 1203), not
from this launcher.
