---
description: The parent<->child interface-stack invariant (extended_cmd.py) — MG5 REPLs nest via define_child_cmd_interface (self.child/self.mother); every cross-interface operation walks this chain — DOWNWARD child-first (error report, quit, command exec, flag propagation), UPWARD mother-first (script stored-line bubble-up, non-interactive-abort detection, widget delegation). Generalizes the per-method cascades on command-loop / script-mode / ask / controlswitch pages.
---

# The interface-stack chain (cross-cutting invariant)

## Principle
MG5/madevent REPLs nest into a doubly-linked **parent<->child stack**. `Cmd.__init__`
(937-938) sets `self.child=None`, `self.mother=None`; `define_child_cmd_interface`
(`extended_cmd.py:1061`) links a sub-interface: `self.child=obj; obj.mother=self`, and
propagates `inputfile`/`haspiping`/`allow_notification_center` DOWN to the child (1065-1081).
The **active interface is the deepest child** (the leaf with `self.child is None`).

Every cross-interface operation walks this chain in ONE of two directions. This single
invariant predicts behavior the per-method pages document only as local cascades — and
predicts it for nestings none of them name (MadSpin/reweight/MadWeight sub-interfaces, 3-deep
stacks, question widgets reached from any depth).

## Downward (child-first) — operations act at the LEAF
Each opens with `if self.child: return self.child.<same method>(...)`, recursing to the leaf
before doing any work:
- `nice_error_handling` (1327-1328), `nice_user_error` (1399-1400), `nice_config_error`
  (1436-1437): the **leaf interface reports the error**, not the interface the user typed at.
  (This is why the probe on optimize-mode-debug-divergence.md saw the error text come from the
  active sub-interface.)
- `do_quit` (1811-1812): `if self.child: self.child.exec_cmd('quit '+line); return` — quit is
  forwarded DOWN to the leaf, which performs the actual stop.
- `exec_cmd` (1588-1589): `if self.child and child: current_interface=self.child` — an internal
  command executes in the active child, not the parent.
- flag propagation in `define_child_cmd_interface` (1078-1081): `inputfile`/`haspiping` pushed
  down so a freshly-spawned child inherits the parent's interactive/script mode.

## Upward (mother-first) — operations bubble toward the ROOT
- **script stored-line bubble-up**: `store_line` (1307-1308) writes to `self.mother.store_line`;
  `get_stored_line` (1314-1316) reads `self.mother.get_stored_line()` first. So a child's
  unmatched script line surfaces in the PARENT's command loop (the `import_command_file` drain).
  ControlSwitch does the same for a bare `set ...` at a question (`self.mother_interface.store_line`,
  2530). (Detailed on script-mode-answer-resolution.md.)
- **non-interactive-abort detection walks UP**: `nice_user_error` (1421-1429) returns True
  (abort) if `self.use_rawinput==False or self.inputfile`, ELSE consults `self.mother.use_rawinput`
  then `self.mother.mother.use_rawinput` (up to 2 ancestors). Same pattern in `nice_config_error`
  (1479-1483). A deeply-nested child thus discovers it is in `-f`/script mode by asking its
  ancestors — so a user error in a sub-interface aborts the whole scripted run.
- **quit unwind**: after the leaf stops, `do_quit`'s `elif self.mother:` branch (1814-1822)
  detaches (`self.mother.child=None`) and, for `quit all`, recurses UP (`self.mother.do_quit('all')`);
  a numeric `quit N` climbs N levels by decrementing.
- **question-widget delegation**: `SmartQuestion.mother_interface` (2147) / ControlSwitch
  `mother_interface` (2488) point at the spawning interface; widgets read `self.options` from it
  (2516) and route `check_answer_in_input_file`/`store_line` back up to it (2240-2241, 2530).

## Boundary / what it does NOT cover
- Pure intra-interface dispatch (`do_X` on the active leaf with no child) does not walk the chain.
- The MULTIPLE-INHERITANCE multiplexer in master_interface.py (`MasterCmd(Switcher, LoopCmd,
  amcatnloCmd, CmdShell)`) is a DIFFERENT mechanism: there is ONE object whose `self.cmd` swaps
  class via `change_principal_cmd` — not a child/mother chain. The LO<->NLO switch does NOT spawn
  a child (master-multiplexer-plugins.md). The chain here is for genuinely SEPARATE interface
  objects (MadSpin, reweight, MadWeight, launched sub-runs) linked at runtime.
- This is a control-flow/structural invariant (method-dispatch direction), not a runtime-output
  prediction; its observable consequence (leaf-reports-error) is the part probe-confirmed
  elsewhere.

## Instances generalized
- command-loop-machinery.md: do_quit cascade, error-handler child recursion (framed per-method).
- script-mode-answer-resolution.md: store_line/get_stored_line mother-walk (framed as script detail).
- ask-question-widgets.md / controlswitch-widget.md: mother_interface widget linkage (framed as
  widget construction).

See also: command-loop-machinery.md, script-mode-answer-resolution.md, master-multiplexer-plugins.md
(the multiplexer contrast in Boundary).
