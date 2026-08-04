---
description: amcatnlo_interface.do_add re-parses the bracket a THIRD time (extract_process_type 478), runs bracket-mode/pertOrder-keyed guards, and conditionally OVERWRITES perturbation_couplings to the model's coupling_orders + bumps orders/squared_orders — a stage-5 mutation of the fields my bracket parser set.
---

# amcatnlo do_add: the third bracket parse + perturbation_couplings overwrite

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_interface.py`, `aMCatNLOInterface.do_add` (def 452).
v3.7.1 / $MADGRAPH_INSTALL.

amcatnlo_interface defines ONLY `do_add` (no `do_generate`; grep-confirmed) — `generate` and `add`
of any `[...]` line route through Switcher (switcher page) to this `do_add`. So for the normal
NLO `generate`/`add` flow this body runs AFTER `extract_process`, and it MUTATES the fields my
bracket parser set. This is the FIFTH lifecycle touch-point (the four on nlo-mode-lifecycle-stages
all concern NLO_mode/has_born; THIS one mutates `perturbation_couplings`/`orders`/`squared_orders`).

## The bracket is parsed a THIRD time here (amcatnlo_interface:478)
`aMCatNLOInterface.do_add`
calls `proc_type = self.extract_process_type(line)` AGAIN at 478, then `extract_process(self,line)`
at 525. So along the add/generate path `extract_process_type` is INVOKED three times — runtime
probe-confirmed (instrumented `generate u u~ > d d~ [QCD]` on loop_sm: exactly 3 calls):
1. `master_interface.py:266 in do_generate()` — Switcher routing (do_generate delegates to do_add).
2. `master_interface.py:209 in do_add()` — Switcher routing in do_add.
3. `amcatnlo_interface.py:478 in do_add()` — this body's own `proc_type`.
Then `MadGraphCmd.extract_process` (525) re-parses the bracket with its OWN regex (4852) to build
the ProcessDefinition — a fourth bracket parse by a different method.
`proc_type` = `(type, option, pert_orders)` — same tuple shape as the routing parser.

**Method-ownership caveat (probe-confirmed):** the 478 call is NOT a separate
`aMCatNLOInterface` method. `extract_process_type` is a `@staticmethod` defined ONLY on `Switcher`
(master_interface:162) — `grep -rn "def extract_process_type" madgraph/` returns that one site, and
`aMCatNLOInterface.extract_process_type` raises `AttributeError` (no such attribute on that class
standalone; its real MRO is CheckFKS/CompleteFKS/HelpFKS/CommonLoopInterface→MadGraphCmd, none of
which defines it). The 478 `self.extract_process_type` resolves at runtime only because `self` is a
`MasterCmd(Switcher, LoopInterface, aMCatNLOInterface, …)` (master_interface:655) with `Switcher`
FIRST in the MRO; `MasterCmd.extract_process_type IS Switcher.extract_process_type` (probe: True).
So all three invocations run the SAME static method — it is a distinct CALL (third parse), not a
distinct method. Do not describe 478 as "aMCatNLOInterface's own extract_process_type".

## Bracket-mode/pertOrder-keyed guards in do_add (478-527)
| line | predicate (on proc_type from the 478 parse) | effect |
|---|---|---|
| 479-480 | `proc_type[1] not in ['real','LOonly']` | run `check_compiler` (real/LOonly skip — no virtual ME, mirrors the loop-model exemption on the gauge-restriction page) |
| 485-491 | `proc_type[2] != ['QCD'] and proc_type[1] == 'all'` | NLO-EW citation banner: if `'QED' in proc_type[2]` -> "involves NLO EW corrections" + arXiv:1804.10017; else "not SM-QCD corrections at NLO" + same ref. One-shot (`display_expansion` class flag) |
| 508-511 | `self.ewsudakov and not 'QED' in proc_type[2]` | "EW Sudakov corrections might be incomplete" warning |
| 513 | always | `validate_model(proc_type[1], coupling_type=proc_type[2])` (nlo-model boundary) |
| 522-523 | `',' in line` branch: `myprocdef.are_decays_perturbed()` | **`MadGraph5Error("Decay processes cannot be perturbed")`** — a SECOND, DIFFERENT decay-perturbation message |
| 527 | always | `proc_validity(myprocdef,'aMCatNLO_%s'%proc_type[1])` |

### The 522 decay message vs the create-loop page's decay rejection
create-loop-induced page documents `loop_interface.proc_validity` (245) "ML5 cannot yet decay a
core process including loop corrections." for a bracket-on-CORE + decay-chain (`p p > t t~ [QCD],
t > b w+`). The 522-523 guard here is DIFFERENT: it fires inside the `,`-in-line branch (decay chain
present) and raises **"Decay processes cannot be perturbed"** when the DECAY itself is perturbed
(`are_decays_perturbed()` True). For a bracket-on-core/unperturbed-decay, `are_decays_perturbed()`
is False, so 522 does NOT fire and execution reaches `proc_validity` (527) -> the 245 "ML5 cannot
yet decay" message. So which message the user sees depends on WHERE the bracket sits:
- bracket on the DECAY (`p p > t t~, t > w+ b [QCD]`): perturbed decay -> 522 "Decay processes
  cannot be perturbed". **PROBE-CONFIRMED** (loop_sm: `generate p p > t t~, t > w+ b [QCD]` ->
  "str : Decay processes cannot be perturbed"). The end-bound `[QCD]` binds to the decay
  subprocess, so it hits 522, NOT the 247 "ML5 cannot yet decay".
- bracket on the CORE (`p p > t t~ [QCD], t > b w+`): unperturbed decay -> 527 proc_validity -> 245
  "ML5 cannot yet decay a core process including loop corrections." (traceback-probed on create-loop page).

## The perturbation_couplings OVERWRITE + order bumping (amcatnlo_interface:629-674)
After proc_validity, do_add does a substantial pass over the procdef's order fields:
- **squared_orders default (629-632):** if `not myprocdef['squared_orders']`, warn "No squared
  orders... will be guessed" and set `squared_orders[ord]=2*val` from `orders`.
- **per-perturbed-order bump (635-655):** for each `pert in myprocdef['perturbation_couplings']`
  (the bracket's parsed orders), gated `if not nlo_mixed_expansion and pert not in proc_type[2]:
  continue` (637): `orders[pert] += 1` (KeyError -> left unbounded, 644-649) and
  `squared_orders[pert] += 2` (KeyError -> set to 2, 651-655). This is the NLO order-bump.
- **WEIGHTED bump (658-665):** `orders['WEIGHTED'] += max(order_hierarchy[pert])`,
  `squared_orders['WEIGHTED'] += 2*max(...)`.
- **THE OVERWRITE (672-673):**
  ```python
  if not myprocdef['orders'] and self.options['nlo_mixed_expansion']:
      myprocdef['perturbation_couplings'] = list(myprocdef['model']['coupling_orders'])
  ```
  CONDITIONAL on BOTH: no explicit amplitude `orders` AND `nlo_mixed_expansion=True`. When it fires,
  `perturbation_couplings` (whatever the bracket gave) is REPLACED by the model's FULL
  `coupling_orders` — NOT `perturbation_couplings` (note: `coupling_orders` ⊇ `perturbation_couplings`;
  in loop_sm `coupling_orders=['QCD','QED']` but `perturbation_couplings=['QCD']`).

`nlo_mixed_expansion` default = **True** (madgraph_interface:3115).

### `nlo_mixed_expansion` — what the option IS (verified for the study doc's claim-4)
- **Interface-level option, NOT a run_card parameter.** Registered in the mg5
  `options_configuration` dict (madgraph_interface:3115, `'nlo_mixed_expansion':True`), settable via
  `set nlo_mixed_expansion <bool>` (`set2_nlo_mixed_expansion`, madgraph_interface:8267; help at 899/8263).
  It is a persisted mg5_configuration option — NOT read from run_card at run time. It DOES land in
  `proc_characteristics` (read at common_run_interface:1035) so it is recorded per-output-dir.
- **Read at GENERATION time (do_add), so it must be set BEFORE `generate`/`add`.** Three read sites,
  all in `aMCatNLOInterface.do_add`: (a) **637-638** — when False, `if pert not in proc_type[2]:
  continue` SKIPS the order-bump for perturbation orders not in the typed bracket (so False =
  perturb ONLY the bracketed order; True = bump all); (b) **672-673** — the overwrite (gated
  `not orders and nlo_mixed_expansion`); (c) **707** — passed into the `fks_options` dict handed to
  `fks_base.FKSMultiProcess`. Setting it after `generate` has no retroactive effect.
- **The physics semantic ("keep pentagon loops with non-colored particles" / mixed-order loop
  expansion) is OUT OF SLICE** — that behaviour is realized inside `FKSMultiProcess`/MadLoop from the
  707 hand-off (fks + madloop slices). My slice confirms only: it exists, default True, is an
  interface option (not run_card), and is consumed at parse/generation time as above.

## Probe-confirmed (loop_sm, `display processes`)
| input | displayed bracket | squared | overwrite fired? |
|---|---|---|---|
| `generate u u~ > d d~ [QCD]` | `[ all = QCD QED ]` | QCD^2=6 QED^2=0 | YES (orders empty) |
| `generate u u~ > d d~ [real=QCD]` | `[ real = QCD QED ]` | QCD^2=6 QED^2=0 | YES (NLO_mode unchanged, pert overwritten) |
| `generate u u~ > d d~ QED=0 [QCD]` | `[ all = QCD ]` | QCD^2=200 QED^2=0 | NO (explicit QED=0 -> orders non-empty) |

Key takeaways from the probe:
- **Bare `[QCD]` in loop_sm ends up `[ all = QCD QED ]`** — the displayed `perturbation_couplings`
  is `['QCD','QED']`, NOT the `['QCD']` that extract_process stored. The `display processes` brackets
  ARE the final procdef `perturbation_couplings` (display reads `_curr_proc_defs`).
- The overwrite is **NLO_mode-agnostic** (fires for `all` and `real` alike) — it touches
  `perturbation_couplings`, not NLO_mode/has_born.
- ANY explicit amplitude order (e.g. `QED=0`) makes `myprocdef['orders']` non-empty and SUPPRESSES
  the overwrite -> `[ all = QCD ]` (the bracket's value survives). It also shows the bump: default
  `QCD<=99` bumped to `QCD<=100`, `QCD^2` to 200.
- "Setting the born squared orders automatically ... to QED=0 QCD^2<=4" is the born_sq_orders
  auto-set (621 `born_sq_orders = copy(squared_orders)`), printed before the perturbed bump.

## Why this corrects the bracket-parse probe table
bracket-parse-and-loopoption-mapping.md's probe table (`[QCD]`->pert `['QCD']`) is correct AT
extract_process exit (it was probed by calling extract_process directly). It is NOT the final
displayed value once the amcatnlo do_add overwrite runs. That table now carries a CORRECTION note
pointing here.

## Boundary
The MUTATION of the bracket-set fields (`perturbation_couplings`, `orders`, `squared_orders`) at
process-spec time is in-slice (same lifecycle-mutation principle as my NLO_mode pages). WHY EW
corrections need all coupling_orders perturbed, the FKS order-bump physics, `_fks_multi_proc`
construction, and what generation does with the bumped orders are amcatnlo/fks slice. `validate_model`
(513) and `coupling_orders` vs `perturbation_couplings` model semantics are nlo-model slice. The
squared-order/`^2` SYNTAX itself is coupling-order slice.
