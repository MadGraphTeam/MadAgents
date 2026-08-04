---
description: How do_delphes actually gets invoked in a run — auto-chained from do_pythia/do_pythia8 tail (delphes --no_default), the interactive run-config menu auto-resolution, ans_delphes switch, consistency_detector_shower; detector=Delphes+shower=OFF auto-promotes shower (PY8 pref) with NO warning log (only switch-table `Pythia8 ⇐ OFF` render); NLO does not auto-chain
---

# What triggers `do_delphes` (the invocation chain)

`do_delphes` (common_run_interface.py:3367) is the handoff body, but it does not call
itself. Four entry points reach it; this page maps them. (The card-PROVISIONING half —
keep_cards, set_default_detector, the 6843-6864 scripted resolver, availability gate — is on
the delphes-availability-and-card-provisioning page; this page is the INVOCATION half.)

## 1. Auto-chain from the shower step (the common path in a generate_events run)
`$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py`:
- `do_pythia8` (def 4579) ends with, at line 5263-5264:
  ```
  if self.options['delphes_path']:
      self.exec_cmd('delphes --no_default', postcmd=False, printcmd=False)
  ```
- `do_pythia` (Pythia6, def 5320) ends with, at line 5493-5495:
  ```
  self.exec_cmd('pgs --no_default', postcmd=False, printcmd=False)   # 5493 — unconditional
  if self.options['delphes_path']:
      self.exec_cmd('delphes --no_default', postcmd=False, printcmd=False)  # 5494-5495
  ```
So **after a shower finishes, MadGraph tail-calls `delphes --no_default` automatically**
(gated only on `delphes_path` being set). Pythia6 also tail-calls `pgs --no_default`
UNCONDITIONALLY (no path guard — pgs depends on pythia-pgs, see do_pgs-flow page).

### Why `--no_default` makes this safe / silent
`do_delphes` with `--no_default` returns EARLY if `Cards/delphes_card.dat` does not exist
(common_run_interface.py:3378-3380: logs "No delphes_card detected, so not run Delphes",
returns). Same guard in `do_pgs` (2329-2331). So the tail-call is a **no-op unless the
operative card was already provisioned** during the run-config menu (keep_cards) or earlier.
Net: Delphes runs automatically at the end of the shower IFF the user selected the delphes
detector mode (which is what creates `delphes_card.dat`). The card's existence is the switch.

## 2. Interactive Pythia6-era run-config menu — `ask_pythia_run_configuration` (6810)
The "Which programs do you want to run? 0 auto / 1 pythia / 2 pgs / 3 delphes" menu
(6823-6832). Mode '3'/'delphes' is offered ONLY if `delphes_path` is set (6818-6819).
- `mode=='auto'` (6844-6852) resolves to: `pgs` if pythia6 AND `pgs_card.dat` exists
  (6846-8); **elif `delphes_card.dat` exists → `delphes`** (6849-50); else plain pythia.
  So auto picks delphes when a delphes card is already present (and no pgs card on py6).
- Once mode=='delphes', appends `delphes_card.dat` to `cards` (6860), and for delphes2
  (delphes_path has a `data/` dir, 6862) also `delphes_trigger.dat` (6864), then
  `keep_cards(cards, ...)` (6865) — THIS materializes the operative card. After the menu the
  shower runs and its tail-call (entry point 1) finds the card and runs Delphes.

## 3. Interactive detector-switch command — `ans_delphes` (madevent_interface.py:698)
Handler for typing `delphes` / `delphes=on|off` at the launch switch menu ("old mode to
activate Delphes", comment 697). CORRECTION (v3.7.1): this lives in
`madevent_interface.py`, in class `AskRun(cmd.ControlSwitch)` (class def line 497) — NOT in
`common_run_interface.py` and NOT in the base `common_run` class (grep: neither `ans_delphes`
nor `consistency_detector_shower` appears in common_run_interface.py). It is part of the
MadEvent interactive launch-switch UI; the NLO path's switch UI is separate. To find it,
grep madevent_interface.py, not common_run.
- If `'Delphes' not in self.available_module` → `warning('Delphes not available. Ignore
  commmand')` and return (702-704). [availability gate is check_available_module — see
  availability page.]
- `value is None` (user typed bare `delphes`): `set_all_off()` then **forces a shower on** —
  `switch['shower']='Pythia6'` if `'PY6' in available_module` else `'Pythia8'` (708-711) —
  and `switch['detector']='Delphes'` (712). So selecting Delphes auto-enables a shower.
- `=='on'` → recurse as None (714); `=='off'` → `set_switch('detector','OFF')` (716).

## 4. Consistency enforcement — `consistency_detector_shower` (madevent_interface.py:720)
Cross-key consistency callback for the switch system (same class `AskRun`, madevent_interface.py
— NOT common_run, see section 3 correction). When detector is set:
- `vdetector=='PGS' and vshower!='Pythia6'` → return `'Pythia6'` (force PY6) (727-728).
- `vdetector=='Delphes' and vshower not in ['Pythia6','Pythia8']` → return `'Pythia8'` if
  PY8 available, elif `'Pythia6'` if PY6, else `raise Exception` (729-735).
So the switch framework REFUSES Delphes-without-a-shower (raises if neither Pythia
available) — the structural reason Delphes always has showered input. Mirrors the
availability gate (Delphes only added to available_module if PY6 or PY8 present).

### Is the shower auto-promotion SILENT? (detector=Delphes + shower=OFF)
Setting detector=Delphes while shower=OFF DOES auto-promote the shower and Pythia8 runs —
but there is NO `logger.warning`/`logger.info` announcing "shower forced on". The mechanism:
- `consistency_detector_shower` (madevent_interface.py:729) returns the replacement value
  `'Pythia8'` (PY8 preferred, elif PY6, else `raise Exception`); it does NOT log.
- The generic ControlSwitch driver `check_consistency` (extended_cmd.py:2795) stores the
  replacement in `self.inconsistent_keys` (:2919); it logs nothing except a `debug` (:2827)
  or a `critical` on 50-step non-convergence (:2909) — neither fires here.
- The promotion is COMMITTED at read-out: `answer` property (extended_cmd.py:2713-2726)
  does `out.update(self.inconsistent_keys)` → the returned switch has shower='Pythia8'.
- VISIBILITY is purely the interactive switch TABLE re-render: `color_for_value`
  (:2937-2941) renders the conflicting row as `Pythia8 ⇐ OFF` (double-left-arrow, the
  OFF in yellow); the plain-text summary path (:3218-3219) prints `Pythia8 < OFF`.
So: NOT truly silent in interactive mode (the switch table visibly shows the flip with an
arrow marker before the user confirms), but NO warning-level log line — a `-f`/scripted
caller that never eyeballs the table gets the promotion with no textual notice.
CAUTION: which shower is chosen is entry-path-dependent — the consistency callback prefers
PY8 (:730); the bare-`delphes`-typed `ans_delphes` path (:708) prefers PY6 if available.
"Promotes to Pythia8" holds only when PY8 is the resolved shower, not universally.

## Caution — NLO does NOT auto-chain
grep for `exec_cmd('delphes`/`pgs --no_default` in amcatnlo_run_interface.py → EMPTY
(v3.7.1). The NLO shower steps do not tail-call Delphes. On the NLO path Delphes is reachable
only via explicit `delphes` command / `--laststep=delphes` dispatch into the inherited
do_delphes (which then hits the NLO check_delphes override + signature-mismatch caveat — see
nlo-amcatnlo-delphes-path page). Do not assume an NLO generate_events produces Delphes ROOT
output the way an LO run does.

## Caution — Pythia6 PGS tail-call is unconditional
do_pythia line 5493 calls `pgs --no_default` with NO `pgs_path`/availability guard (unlike
the delphes guard at 5494). It is still a no-op when `pgs_card.dat` is absent (do_pgs 2329
early-return), but it always EXECUTES the command (logs "No ... card detected"). Cosmetic,
not a failure.
