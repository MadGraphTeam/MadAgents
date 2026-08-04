---
description: Process-time loop-capability enforcement - the EARLIEST CheckLoop gate (loop_interface.py validate_model, probe-verified INFO string + sm->loop_qcd_qed_sm auto-upgrade), the later get_combined_legs Gate 1/2, [all]/[loonly] expansion, gauge->Feynman forcing (two sites) for EW/QED-perturbing loop models, and the proc_validity gate whose `if not 'real':` loop-capability block is DEAD (always-False string-truthiness bug, duplicates the live checks).
---

# Process-time loop-capability enforcement

(v3.7.1.) loopmodel-detection covers how a `LoopModel` is *built* at import. This page is
the consumer side: where, at `generate`/`add process` time, MadGraph enforces that the
loaded model actually supports the requested perturbation. Answers "can I run `[QCD]` /
`[QED]` with this model?"

## EARLIEST gate: CheckLoop in loop_interface.py (probe-verified)
The FIRST capability check at generate time is NOT in get_combined_legs — it is the
CheckLoop guard `$MADGRAPH_INSTALL/madgraph/interface/loop_interface.py:310-357`:
```python
if not isinstance(self._curr_model, loop_base_objects.LoopModel) or \
   self._curr_model['perturbation_couplings']==[] or \
   any((coupl not in self._curr_model['perturbation_couplings']) for coupl in coupling_type):
    if loop_type.startswith('real') or loop_type=='LOonly': ...
    else:
        logger.info("The current model %s does not allow to generate"
                    " loop corrections of type %s." % (name, coupling_type))
        ... # SM auto-upgrade OR `elif stop: raise InvalidCmd`
```
- It folds the LoopModel-check AND the perturbation-order-check into ONE condition (310-313).
- The string emitted is `"The current model <name> does not allow to generate loop
  corrections of type <list>."` (loop_interface.py:325-326) — an **INFO log**, NOT the
  get_combined_legs strings below. PROBE-VERIFIED: `import model loop_sm; generate a a > t t~
  [QED]` emits exactly `"The current model loop_sm does not allow to generate loop
  corrections of type ['QED']."`. So when quoting the runtime message a user sees for a
  rejected sm-family perturbation, use THIS string, not the Gate-2 string.

## SM auto-upgrade — validate_model docstring: "Upgrade the model sm to loop_sm if needed"
`validate_model` (loop_interface.py:295) IS the CheckLoop gate body. For an
`sm`/`loop_sm`-named model asked for a perturbation it lacks, CheckLoop does NOT
error — it auto-loads the appropriate SM loop model (loop_interface.py:328-353):
- The model_name is normalized first: `loop_sm` -> strip `loop_` prefix -> `sm` (name[5:],
  :328-329); a bare `sm` stays `sm`. Both then feed the SAME `loop_%(add_on)s%(name)s` swap.
- **RESTRICTION PRESERVED across the upgrade.** The name-family test uses
  `model_name.split('-')[0]` (:329, :331), but the swap re-imports the WHOLE `model_name`
  (restriction suffix included), so `sm-no_b_mass -[QCD]-> loop_sm-no_b_mass`. The suffix is
  present because import_ufo.py:256-257 does `model["name"] += '-' + restrict_name` at load
  (a restricted `import model sm-no_b_mass` yields model name `sm-no_b_mass`). The
  `loop_sm`-prefix strip (name[5:] on `loop_sm-no_b_mass` -> `sm-no_b_mass`) keeps the suffix
  too, so re-upgrading an already-loop model is idempotent. PROBE-CANDIDATE (unprobed): the
  re-import succeeds only if the target restrict file exists — verified present:
  `models/loop_sm/restrict_no_b_mass.dat` exists (also ckm/c_mass/no_masses/no_widths/...),
  so `sm-no_b_mass -> loop_sm-no_b_mass` resolves. A bare-`sm` restriction with NO loop_sm
  counterpart restrict file would fail at the re-import, not at the gate.
- `coupling_type==['QCD']` -> **add_on='' -> re-imports `loop_sm`** ; `['QED']` or
  `['QCD','QED']` -> add_on='qcd_qed_' -> `loop_qcd_qed_sm` (else `MadGraph5Error "The
  pertubation coupling cannot be ..."`, :344-346).
- The swap logs the EXACT info string `"MG5_aMC now loads 'loop_%s%s'."` (:347) — for the
  QCD case literally `"MG5_aMC now loads 'loop_sm'."`. It re-imports via
  `exec_cmd(" import model loop_%s%s", precmd=True)` with history bookkeeping (:351-355) so
  the swap is transparent to the user's command history.
- **This is the claim-2 path (PROBE-VERIFIED, parse/generate only, no launch)**: `import model
  sm; generate p p > t t~ [QCD]` emits, verbatim and consecutively, `"The current model sm does
  not allow to generate loop corrections of type ['QCD']."` then `"MG5_aMC now loads 'loop_sm'."`
  then `INFO: Generated 9 subprocesses with 136 real emission diagrams, 11 born diagrams and 124
  virtual diagrams` — i.e. the auto-upgrade fires and generation succeeds on loop_sm. (Applies to
  `[QCD]` virtual OR noborn.) The default `sm` has NO CT_*.py and NO
  `perturbative_expansion` (models/sm has no CT files; models/loop_sm has
  CT_couplings/CT_parameters/CT_vertices.py) so it is not a LoopModel until this swap.
- If QED is requested while not in Feynman gauge, it switches to Feynman FIRST (:335-341,
  sets `_curr_model=None` then `do_set('gauge Feynman')`).
- The `process-loop-capability-gates` "sm auto-allows QCD in *completion*" note (below) is
  only the tab-completion half; THIS is the real generate-time model swap.
- For a NON-sm model that fails the check, the `elif stop` branch raises
  `InvalidCmd("The model %s cannot handle loop processes")` (loop_interface.py:356-357).
- **Loop-induced routes through THIS SAME gate.** The upgrade/reject branch is entered for
  every loop_type EXCEPT `real*` and `LOonly` (:312 `if loop_type.startswith('real') or
  loop_type=='LOonly'`). So `noborn` (loop-induced, e.g. `g g > h h [noborn=QCD]`, HasBorn
  set False at madgraph_interface.py:4868-4869) and `virtual`/`sqrvirt` all require a
  LoopModel that perturbs the requested order — or, for sm-named, trigger the auto-upgrade to
  loop_sm. **Claim-3 mechanism**: loop-induced `[noborn=QCD]` needs a QCD-loop-capable model
  (real internal loop + R2/UV), which loop_sm provides and a tree effective model does not.
- **heft is NOT loop-capable** (not bundled/installed on this build; as the standard
  tree-level Higgs-effective model it has an effective contact `ggh` vertex, no
  `perturbative_expansion`, so it builds a plain `base_objects.Model`, not a LoopModel). A
  `[noborn=QCD]`/`[QCD]` request against heft fails the CheckLoop guard and — heft name does
  not start with `sm` — hits the `elif stop` branch -> `InvalidCmd("The model heft cannot
  handle loop processes")`. heft gives `g g > h` at TREE level via the effective vertex; it
  does NOT give the loop-induced amplitude. (heft's own coupling_orders content is unverified
  here — not installed; the reject mechanism is the LoopModel/`perturbative_expansion` gate,
  which is model-content-independent.)
- Second gauge-forcing block at loop_interface.py:358-367 mirrors the import-time one:
  LoopModel with perturbation_couplings not in `[[],['QCD']]` + non-Feynman gauge ->
  `do_set('gauge Feynman')` if `1 in gauge` else warning. PROBE-VERIFIED: `import model
  loop_qcd_qed_sm; generate a a > t t~ [QED]` logs `"Switching to Feynman gauge because it
  is the only one supported by the model loop_qcd_qed_sm."` and generates (2 born, 198
  virtual, 214 real).

The get_combined_legs gates below are a SECOND, later layer (different file). They still
run; their verbatim strings are real source but are not the message the sm-family path
surfaces. Recorded from source; the get_combined_legs strings themselves remain not-yet-
probed (the CheckLoop gate fires first for the cases probed here).

## Two gates in get_combined_legs / process parsing
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:5280-5289`:
```python
if perturbation_couplings_list and LoopOption not in ['real', 'LOonly']:
    if not isinstance(self._curr_model, loop_base_objects.LoopModel):
        raise self.InvalidCmd(
          "The current model does not allow for loop computations.")
    else:
        for pert_order in perturbation_couplings_list:
            if pert_order not in self._curr_model['perturbation_couplings']:
                raise self.InvalidCmd(
                    "Perturbation order %s is not among"
                    " the perturbation orders allowed for by the loop model.")
```
- **Gate 1** (5281-5283): a tree-level model (not a `LoopModel`) + any bracket
  perturbation → `"The current model does not allow for loop computations."`
- **Gate 2** (5285-5289): a perturbation order not in the model's `perturbation_couplings`
  → `"Perturbation order <X> is not among the perturbation orders allowed for by the loop
  model."` (e.g. `[QED]` against bundled loop_sm, whose perturbation_couplings == `['QCD']`).
- Both gates are SKIPPED when `LoopOption in ['real','LOonly']` (5280): the `[real= ...]`
  and `[LOonly= ...]` syntaxes don't require loop interactions, so a tree model passes.

## [all] / [loonly] expand to the model's full list
5250-5253: if the bracket order is `all` or `loonly`, it is replaced by
`' '.join(self._curr_model['perturbation_couplings'])`. `loonly` additionally sets
`LoopOption='LOonly'`. So `[all]` literally means "every order this model declares as
perturbative" — model-defined, not a fixed QCD+QED.

## sm-named model auto-allows QCD in completion
2078-2083 (and mirror at 2152): when building tab-completion possibilities,
`pert_couplings_allowed = ['all'] + model['perturbation_couplings']` for a LoopModel (else
`[]`), and if `model.get('name').startswith('sm')` then `+ ['QCD']` is appended. Comment
2074-2075: "Automatically allow for QCD perturbation if in the sm because the loop_sm would
then automatically be loaded." This is completion-list only; the hard gates above still run.
The REAL generate-time model swap (sm/loop_sm -> loop_sm / loop_qcd_qed_sm) is the
CheckLoop auto-upgrade documented at the top of this page, not this completion logic.

## order_hierarchy is also required for split orders
5265-5273: every perturbation order and squared-order must have an entry in the model's
`order_hierarchy`, else `InvalidCmd("The loaded model does not defined a coupling order
hierarchy for these couplings: ...")`. A loop model missing a hierarchy entry for a
perturbed order fails here even if perturbation_couplings is correct.

## Gauge forcing for EW/QED-perturbing loop models
`do_import`/`advanced_install` path, 5810-5829: for a LoopModel whose
`perturbation_couplings` is NOT in `[[], ['QCD']]` (i.e. it perturbs EW/QED), when gauge is
unitary/axial:
- if the model's `gauge` list contains `1` (Feynman) → MadGraph auto-switches to Feynman
  (`do_set('gauge Feynman')`), logging "this loop model allows for more than just tree
  level and QCD perturbations."
- if the model has NO Feynman gauge (`1 not in gauge`) → warning "This model does not allow
  Feynman gauge. You will only be able to do tree level and QCD loop computations with it."
So EW-loop models effectively require Feynman gauge; loop_sm (QCD-only) is exempt.
Related: `LoopModel.change_electroweak_mode` (loop_base_objects.py:1486-1491) would block an
EW-scheme change for QED/EW-perturbing models, but is bypassed (`bypass_check=True` hardcoded).

## proc_validity gate + the DEAD `if not 'real':` loop-capability check
`$MADGRAPH_INSTALL/madgraph/interface/loop_interface.py` `proc_validity` (211-270) is a
SEPARATE process-time validity gate (called for ML5 / aMC@NLO, e.g. amcatnlo_interface.py:527
`proc_validity(..., 'aMCatNLO_%s'%proc_type[1])`). Its LIVE checks (222-256): empty process,
mixed initial-state count, ML5 multiparticle-label ban (239-243), decay-chain ban (245-247),
perturbed-decay ban (249-252), and the tree-level redirect "Please perform tree-level
generations within default MG5 interface." (254-256).
- **DEAD BRANCH (257-270):** `if not 'real':` — `not 'real'` is `not <truthy non-empty
  string>` == **always `False`**, so the ENTIRE block 258-270 is unreachable dead code. It
  duplicates (never-firing copies of) the loop-capability check "The current model does not
  allow for loop computations." (258-261), the missing-perturbation-order check (263-268), and
  a gauge/perturbation check (270+). The author clearly meant `if 'real' not in mode:` (cf. the
  CORRECT idiom at 265 `... and not 'real' in mode`). This is a presence≠liveness trap: grepping
  for the loop-capability error string finds a HIT here that never executes. The LIVE
  loop-capability enforcement is CheckLoop (above) + get_combined_legs Gate 1/2, NOT this block.
- So when the lead's cross-subtree `process-verification-fanout` routes a "dead `if not 'real':`
  branch" / "validate_model:513" question here: the dead branch is loop_interface.py:257 (in
  proc_validity), and `validate_model:513` is the amcatnlo_interface.py CALL SITE
  (`self.validate_model(proc_type[1], ...)`), whose def is loop_interface.py:297 (its body IS the
  CheckLoop gate documented at the top of this page). Static-source / dead-code fact, not probed
  (the branch cannot fire, so there is nothing to probe).

## Boundary / cautions
- The bracket PARSING (regex extracting `[pertOrders= ...]`, the `option` keyword) and
  squared-order weighting / WEIGHTED computation are nlo-syntax slice territory; this page
  is only the model-capability checks those feed into.
- ORDER OF CHECKS at generate time: CheckLoop (loop_interface.py:310, probe-verified) fires
  FIRST and is what surfaces the user-visible INFO string + sm auto-upgrade; the
  get_combined_legs Gate 1/2 (madgraph_interface.py:5283/5288) are a later layer with
  different (not-yet-probed) strings. Don't cite the Gate-2 string as the runtime message
  for an sm-family rejection.
- The practical test: a process asking to perturb an order the model's coupling_orders.py
  did not mark `perturbative_expansion>0` is rejected (or, for sm-family, auto-upgraded) at
  generate time, NOT at import.
