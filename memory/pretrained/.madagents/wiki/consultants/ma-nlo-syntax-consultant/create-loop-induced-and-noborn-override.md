---
description: Two post-parse NLO_mode mutation sites that overwrite what the bracket parse set — create_loop_induced forces 'noborn' (loop-induced), do_check forces 'all'->'virt' (check command); plus the bracket-vs-decay-chain rejection (fires in loop_interface.proc_validity, shadowing the base do_add 3283 guard) and proc_validity's dead-code block. Also: no Born-vanishing check for explicit [noborn=] (parser trusts flag; NoBornException detection is fks); the `>` s-channel bracketed form IS parse-accepted where the comma form is rejected. LOAD-BEARING: explicit [noborn=QCD] routes Switcher master:218->create_loop_induced BYPASSING amcatnlo do_add, so the C6a:542 squared-order <=-only reject NEVER fires — ^2==/^2> ARE accepted for explicit [noborn=QCD] (probe: g g>z z QED^2==4 [noborn=QCD] OK) where the SAME order on [QCD] is rejected; create_loop_induced has NO sqorders_types check, only has_born-mix (5408) + negative-order guards. noborn is procdef-GLOBAL (drops genuine Born, probe b b~>h). Mixing loop-induced+has-born rejected by ORDER-DEPENDENT guard (5408 vs Switcher combine-LO/NLO); FKS-first ordering escapes. Decay+^2==N rejected at 3301-3303.
---

# Post-parse NLO_mode mutation sites + bracket-vs-decay rejection path

v3.7.1 / $MADGRAPH_INSTALL.
Files: `$MADGRAPH_INSTALL/madgraph/interface/{madgraph_interface,loop_interface,amcatnlo_interface}.py`.

## Principle: the bracket-parse NLO_mode is not always final
`extract_process` (4862-4877) sets `NLO_mode`/`has_born` from the bracket, but TWO command paths
overwrite `NLO_mode` AFTER `extract_process` returns. The value stored on the ProcessDefinition by
my parser (loopoption-is-the-post-remap-discriminant page) is the value *at parse time*; the
command that called the parser may rewrite it. Both sites are in-slice (they mutate the field my
parser set, at process-spec time). The two sites:
| site | command | mutation | line |
|---|---|---|---|
| create_loop_induced | noborn / NoBornException | force `'noborn'` | madgraph_interface:5392 |
| do_check | `check` | force `'all'`->`'virt'` | madgraph_interface:4413-4414 |

## create_loop_induced forces NLO_mode='noborn' AFTER extract_process (madgraph_interface:5357-5400)
Reached for `[noborn=…]` via the Switcher (`do_add` 218-225 -> `create_loop_induced(line)`), and via
the `NoBornException` fallback (Switcher do_add 230-236) when FKS finds no Born.
- `args = self.split_arg(line)`; strips `--no_warning=duplicate` (5363-5365), `--optimize` (5374-5378),
  `--loop_filter=…` (5380-5387) from the line.
- If no `myprocdef` passed, `myprocdef = self.extract_process(' '.join(args))` (5390) — the normal
  bracket parse runs here.
- **Then unconditionally `myprocdef.set('NLO_mode', 'noborn')` (5392).** So whatever LoopOption the
  bracket parse produced is OVERWRITTEN to `'noborn'` for the loop-induced path. (For `[noborn=…]`
  the parse already gave 'noborn'; for the NoBornException fallback the parse gave 'all', and 5392
  forces it down to 'noborn'.) HasBorn is NOT re-set here — it was already False for `[noborn=…]`
  (extract_process 4868-4869); for the NoBornException fallback path see fks slice for how HasBorn
  ends up.
- This is a post-parse mutation of the field my parser set — relevant because the FINAL NLO_mode on
  the ProcessDefinition for a loop-induced process is 'noborn' regardless of the typed bracket.

## do_check forces NLO_mode 'all'->'virt' AFTER extract_process (madgraph_interface:4407-4414)
`do_check` (def 4065) is a direct `extract_process` consumer: it calls
`myprocdef = self.extract_process(proc_line)` (4407), then:
```python
# For the check command, only the mode 'virt' make sense.
if myprocdef.get('NLO_mode')=='all':            # 4413
    myprocdef.set('NLO_mode','virt')            # 4414
```
- So `check g g > h [QCD]` parses to NLO_mode='all' (bare-bracket else branch) but is rewritten to
  'virt' here — only the virtual is checked. Other modes (virt/real/noborn/sqrvirt/LOonly) are NOT
  rewritten (only the literal `'all'` is caught). HasBorn is NOT touched.
- Caveat: this is the body of MadGraph-interface `do_check`. The Switcher's `do_check`
  (master_interface:239-258, switcher page) routes `all`/`virt`/`sqrvirt` to MadLoop and rejects
  `real`. So a checkable bracket has already been routed to the loop interface; the 4413 override is
  reached after that routing. (`real` is killed at the Switcher before reaching here.)

### do_check bracket-pertOrders-keyed sub-command guards (madgraph_interface:4421-4431)
Two sub-command guards read `perturbation_couplings` (the bracket's parsed orders) directly:
- **timing/stability/profile** (4421-4424): require non-empty `perturbation_couplings`, else
  `InvalidCmd("Only loop processes can have their timings or stability checked.")`. I.e. these
  check sub-modes demand a `[...]` bracket.
- **gauge** (4427-4431): require `perturbation_couplings in [[],['QCD']]`, else `InvalidCmd` (Feynman
  vs unitary gauge comparison only valid when no non-QCD loop propagators are affected). This is the
  LIVE `[[],['QCD']]` gate for the `check gauge` *entry*, distinct from (a) the dual-gauge *re-parse*
  gate at 4566 (gauge-restriction page) and (b) the DEAD `[[],['QCD']]` block in loop_interface
  proc_validity 270-275 (this page, below). Three PROCDEF-pert-keyed `[[],['QCD']]` sites
  (`myprocdef`/`proc['perturbation_couplings']`); two live (4428 entry, 4566 re-parse), one dead
  (proc_validity 270). A bare grep `[[],['QCD']]` returns MORE hits (loop_interface 207/360,
  madgraph_interface 5814/8134) but those test the MODEL's `_curr_model['perturbation_couplings']`,
  a different field — not these process-mode gates.
- `check gauge` also needs the model to expose ≥2 gauges (4433-4435), else InvalidCmd — that is a
  model-capability check (nlo-model boundary), listed here only because it sits in the same guard
  cluster.

## Bracket + decay chain: which guard the user actually sees (NOT the base 3283 guard)
There are THREE distinct guards that reject perturbed/decayed combinations. Traceback-probed which
one fires:

1. **base `madgraph_interface.do_add` (3282-3289):** `if ',' in line: if ']' in line or '[' in line:`
   -> MadGraph5Error "The '[' and ']' syntax cannot be used in cunjunction with decay chains."
   (sic: "cunjunction"). **This guard is SHADOWED for any `[...]` line** — the Switcher routes any
   bracketed line to aMC@NLO/MadLoop first (see switcher page), so the base MadGraph do_add is never
   reached with a bracket+comma line. The "cunjunction" message does not appear in practice.

2. **`loop_interface.proc_validity` (245-247):** `if proc['decay_chains']: raise InvalidCmd("ML5
   cannot yet decay a core process including loop corrections.")` — THIS is the user-visible error.
   Traceback-confirmed: `add process p p > t t~ [QCD], t > b w+` (even under `import model
   sm`) routes Switcher.do_add(229) -> amcatnlo_interface.do_add (def 452; the proc_validity call is at
   527, after the are_decays_perturbed guard at 522-523 which does NOT fire since the *decay*
   t>bw+ is unperturbed) -> proc_validity decay_chains guard (245-247) and
   raises "ML5 cannot yet decay a core process including loop corrections." The `[QCD]` core makes
   `extract_decay_chain_process` build a non-empty `decay_chains`, which 245 rejects.

3. **`are_decays_perturbed()` (base_objects:3568-3574)** is checked in three places
   (madgraph_interface 3296, amcatnlo_interface 522, loop_interface 249) — it recurses through
   `decay_chains` and returns True if any subprocess's `perturbation_couplings` is non-empty. The
   code comments call these "redundant... might be relieved in the future." In the bracket-on-core
   case guard #2 fires first (decay_chains non-empty), so #3 is the backstop for a bracket-on-DECAY
   case were #2 ever relaxed.

`decays_have_squared_orders()` (base_objects:3576-3582) is the parallel recursive check for
`squared_orders` on decay subprocesses (madgraph_interface 3301).

## CAUTION: proc_validity dead-code block (loop_interface:257-275)
`if not 'real':` (257) — `not 'real'` is always `False` (non-empty string is truthy). Confirmed in
python. So the entire 257-275 block is UNREACHABLE dead code, including:
- the LoopModel requirement (258-261),
- the per-order membership check vs `model['perturbation_couplings']` (263-268),
- the restriction `proc['perturbation_couplings'] not in [[],['QCD']]` -> "MadLoop can only work in
  the Feynman gauge for these" (270-275).
Intended guard was almost certainly `if not 'real' in mode:`. The equivalent live enforcement of the
loop-model/pert-order requirement still happens in extract_process (5280-5289, my
gauge-restriction page). The dead block's gauge restriction (`perturbation_couplings not in
[[],['QCD']]`) is NOT a general loop-process restriction in live code — the only LIVE
`[[],['QCD']]` gauge gates are inside `do_check` (4428 `check gauge` entry, 4566 dual-gauge
re-parse, both above). There is no live equivalent of this dead block's "MadLoop only works in
Feynman gauge for non-QCD perturbations" restriction for the ordinary generate/add path; whether
non-QCD loops actually require Feynman gauge at MadLoop runtime is madloop slice, not enforced at
parse time.

## No Born-vanishing verification for explicit `[noborn=…]` (parser trusts the flag)
The parser sets `HasBorn=False` for `[noborn=…]` purely from the keyword (extract_process 4868-4869)
— it does NOT check that the Born amplitude actually vanishes. The explicit-noborn route
(master_interface do_add 218-224) goes STRAIGHT to `create_loop_induced` (5392 forces NLO_mode
'noborn') with NO Born diagram generation at all, so there is genuinely no Born-vanishing gate on
this path. Born ABSENCE is only ever DISCOVERED on the OTHER path: the bare `[QCD]`/'all' route runs
FKSMultiProcess.__init__, whose Born generation catches `NoDiagramException` -> raises
`NoBornException` (fks/fks_base.py:181-188), and master do_add 230-236 then auto-falls-back to
create_loop_induced with the "No Born diagrams found. Now switching to the loop-induced mode." banner.
So: my slice sets the has_born flag; Born-EXISTENCE detection (NoBornException) is **fks slice**
(fks_base.py:181, raise at 183). Doc claim "MG5 does NOT verify the Born vanishes for [noborn=]" is
CORRECT — probe-confirmed the routing (master 218-224 -> create_loop_induced, no Born gen).

## LOAD-BEARING: explicit `[noborn=QCD]` BYPASSES the C6a:542 squared-order `<=`-only reject
The `<=`-only squared-order restriction at NLO (`^2==`/`^2>` rejected) lives ONLY at
`amcatnlo_interface.py:541-542` (grep-confirmed: it is the sole `sqorders_types` `<=`-check in the
interface tree). It is reached ONLY through aMC@NLO `do_add`. Explicit `[noborn=QCD]` does NOT reach
it: the Switcher (`master_interface.py:200-236`) routes `nlo_mode=='noborn'` at **218-225**:
```python
elif nlo_mode == 'noborn':
    ...
    self.cmd.validate_model(self, loop_type=nlo_mode, coupling_type=orders)   # 222
    self.change_principal_cmd('MadGraph', allow_switch)
    return self.cmd.create_loop_induced(self, line, *args, **opts)            # 225 — RETURNS here
```
Line 225 `return`s straight into `create_loop_induced` — the `self.cmd.do_add` (aMC@NLO) at 228 is
never executed, so C6a:542 is skipped. `create_loop_induced` (5357-5420) runs `extract_process`
(which parses `^2==`/`^2>` into `sqorders_types` — `_valid_sqso_types=['==','<=','=','>']`,
madgraph_interface:3036 — all four ACCEPTED at parse) then `set('NLO_mode','noborn')` (5392) and has
**NO `sqorders_types` `<=`-only check**. Its only order guards are the `has_born`-mix (5408, below)
and the negative-coupling-order guard (5410-5416). So a non-`<=` squared order **survives** for
explicit `[noborn=]`.

**Probe-confirmed (loop_sm):**
- `generate g g > z z QED^2==4 [noborn=QCD]` → **ACCEPTED** (0 Born, 28(+12) loops, 8 R2). The `==`
  squared order rides through.
- `generate g g > z z QED^2==4 [QCD]` → **REJECTED**: "The squared-order constraints passed are not
  '<='. Other kind of squared-order constraints are not supported at NLO" (C6a:542).

So the distinguishing predicate is the **typed bracket** (`nlo_mode` at the Switcher), NOT whether the
process is physically loop-induced: `[QCD]` on a gg-only (physically loop-induced) process still
routes to aMC@NLO `do_add` and hits C6a:541 BEFORE FKS/NoBornException, so bare-`[QCD]`-loop-induced
still rejects `^2==`/`^2>` (the `g g > e+ e- mu+ mu- QCD^2==2 [QCD]` case on np-order page). Only the
**explicit `[noborn=]` keyword** takes the create_loop_induced bypass. CORRECTION to the np-order
page's "C6a fires on ANY [...] incl. loop-induced": it fires on the has-born-TYPED `[QCD]` bracket
even when that becomes loop-induced; it does NOT fire on the explicitly-typed `[noborn=]` bracket.

Caveat (coupling-order NAME): the squared-order basename is validated at parse (4929-4932) against
`model_orders+['WEIGHTED']`. `QED^2==4` works (QED is a model order). A doc example like `HZZ^2==2`
would FAIL at parse — `HZZ` is not a coupling_order in the model (it is a vertex/coupling name), not
a squared-order-eligible token. The bypass concerns valid order names only.

Whether the surviving `^2==` bin is CORRECTLY masked/computed at loop-induced runtime
(orders.inc/KEEP_ORDER emission, amp_split) is nlo-export/madloop slice — parse-acceptance is my
slice; I confirm only that it parses and generates diagrams, not that the `==` selection is enforced
numerically. (probe-candidate: launch `g g>z z QED^2==4 [noborn=QCD]` and confirm the σ isolates the
QED^2=4 bin.)

## The `has_born`-mix rejection is ORDER/PATH-dependent (claim: "mixing fails")
Mixing a loop-induced (`has_born=False`) and a has-Born process in one generation DOES fail, but
WHICH guard fires depends on ordering — there is no single "has_born-mismatch" gate:
- **LO (MadGraph `_curr_amps`) then `[noborn=]`** → `create_loop_induced` **5408**:
  `if self._curr_amps and (not isinstance(self._curr_amps[0], LoopAmplitude) or
  self._curr_amps[0]['has_born']): raise InvalidCmd("Can not mix loop induced process with not loop
  induced process")`. Probe-confirmed: `generate u u~ > z g` ; `add process g g > z z [noborn=QCD]`
  → that exact message.
- **`[noborn=]` then `[QCD]`** → the Switcher's `change_principal_cmd(..., allow_switch=False)`
  (allow_switch is False once `_curr_amps` is non-empty, do_add 201-203) → **"Can not combine LO/NLO
  feature."** Probe-confirmed: `generate g g > z z [noborn=QCD]` ; `add process g g > z z g [QCD]`.
- **`[QCD]` FKS (aMC@NLO) then `[noborn=]`** → **NOT rejected** in this ordering (probe:
  `generate u u~ > z g [QCD]` ; `add process g g > z z [noborn=QCD]` — BOTH generate). The FKS Born
  amps are NOT stored in `self._curr_amps`, so the 5408 `_curr_amps` predicate is False and the mix
  slips through. Whether the un-rejected aMC@NLO-FKS + loop-induced combination actually OUTPUTS
  coherently (one process dir, consistent has_born handling) is amcatnlo/fks slice — my slice
  establishes only that the parse-time mix-guard does NOT catch this ordering.

My-slice ownership: the bracket sets `has_born` (extract_process 4868-4869) and `NLO_mode`; the 5408
mix-guard reads them and lives in create_loop_induced (madgraph_interface — the noborn path I own).
The Switcher "combine LO/NLO" guard is switcher-page territory.

## Decay chain + squared-order rejected (claim 4, verified)
`madgraph_interface.py:3301-3303` (inside the decay-chain `do_add` branch): `if
myprocdef.decays_have_squared_orders() or myprocdef['squared_orders']!={}: raise
MadGraph5Error("Decay processes cannot specify squared orders constraints.")`.
`decays_have_squared_orders` (base_objects:3576-3582) recurses `decay_chains` for any non-empty
`squared_orders`; the `or myprocdef['squared_orders']!={}` also catches a `^2` on the CORE line of a
decay-chain process. Probe-confirmed: `generate p p > t t~, (t > b w+ QED^2==2)` → "Decay processes
cannot specify squared orders constraints." (This is the LO decay-chain path; a `[...]`+comma line is
rejected earlier by the bracket-vs-decay guards above, so this squared-order-in-decay guard is the
one that fires on the un-bracketed decay chain.)

## The `>` s-channel form IS accepted at NLO (contrast with the comma form)
`add process p p > t t~ > w+ b w- b~ [QCD]` is NOT a decay chain — no comma, so `proc['decay_chains']`
is empty and the proc_validity 245 guard does NOT fire. **PROBE-CONFIRMED, stronger than parse-only**
(loop_sm, `generate p p > t t~ > w+ b w- b~ [QCD]`): it passes process-spec AND proceeds through the
full NLO generation — born FKS-subtracted MEs for all 9 subprocesses (`g g > t t~ > w+ b w- b~
QCD^2=6 QED^2=4`, `u u~ > …`, …) AND virtual MadLoop MEs for each. So the s-channel `>`-form is
treated as ONE process with required s-channels (off-shell effects retained via the propagators),
NOT a comma decay chain — it survives the guard that rejects the comma form. Contrast: the comma
form `p p > t t~, t > w+ b [QCD]` raises "Decay processes cannot be perturbed" (522) immediately.
The `> >` required-s-channel SEMANTICS are diagram-filter slice; my slice confirms the bracketed
`>`-form generates full NLO born+virt where the bracketed comma-form is rejected.
(Whether integration/event-gen COMPLETES cleanly is a heavier fks/nlo-export/amcatnlo probe-candidate.)

## Boundary
The fields my parser sets (`NLO_mode`, `has_born`, `perturbation_couplings`, `decay_chains`) and the
guards that read them at process-spec time are my slice. WHAT create_loop_induced /
FKSMultiProcess / MadLoop then DO with the forced 'noborn' is fks/madloop/amcatnlo slice.
validate_model (loop_interface:297) semantics are nlo-model slice.
