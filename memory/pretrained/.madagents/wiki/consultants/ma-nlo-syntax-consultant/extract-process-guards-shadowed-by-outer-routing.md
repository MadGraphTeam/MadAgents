---
description: extract_process's bracket mode/pert-order guards (4871, 5269-5273, 5280-5289) are INNER guards shadowed on the live generate path by EARLIER outer guards — Switcher _valid_nlo_modes (bad OPTION) + aMC@NLO validate_model (non-perturbable ORDER, can also auto-upgrade sm->loop_sm); user sees the OUTER message, inner only on a direct extract_process call.
---

# extract_process bracket guards are shadowed by outer routing guards

`$MADGRAPH_INSTALL/madgraph/interface/{master_interface,amcatnlo_interface,loop_interface,madgraph_interface}.py`.
v3.7.1 / $MADGRAPH_INSTALL.
Generalizes a presence-vs-liveness trap that bit THREE instance-page claims (np-order `[NP]`/`[QED]`,
bracket-parse `[EW]` + `[bogus=QCD]`). This is the lead's `dead-code-liveness` shape: the inner guard
EXISTS and is correct in isolation, but is UNREACHED on the normal `generate`/`add` path.

## The principle
A `[...]` line is validated at TWO layers, and the OUTER layer runs FIRST:
- **OUTER (routing layer)** — runs in the Switcher (`master_interface`) and the chosen interface's
  `do_add` BEFORE `extract_process` is ever called.
- **INNER (parse layer)** — the guards inside `extract_process` (madgraph_interface) that this slice's
  other pages document (4871 invalid-mode, 5269-5273 order_hierarchy sort, 5280-5289 loop-model/
  pert-order membership).

For a bracket line typed at `generate`/`add`, the inner guard is reached ONLY if the outer guard
passed. So when BOTH would reject the same line, **the user sees the OUTER message**; the inner
message is only observable by calling `extract_process` directly (bypassing the Switcher). Several
instance pages probed by a DIRECT `extract_process` call and recorded the inner message as if it were
the user-visible one — wrong for the live path.

## The two outer guards (probe-confirmed)

### 1. Bogus *option* keyword -> Switcher `_valid_nlo_modes` check (NOT extract_process 4871)
`Switcher.do_generate` (master_interface:268-270, raise at **269**) and `do_add` (209-213, raise at
**212**) test `if not nlo_mode in self._valid_nlo_modes` on the routing-parser's classification and
raise
`InvalidCmd("The NLO mode %s is not valid. Please ch[o]se one among: %s")`.
- Probe (`generate u u~ > d d~ [bogus=QCD]`, loop_sm): user sees
  **"The NLO mode bogus is not valid. Please chose one among: all real virt sqrvirt tree noborn LOonly only"**.
- Isolation (`cmd.extract_process('... [bogus=QCD]')`): the DIFFERENT 4871-4872 message
  "NLO mode bogus is not valid. Valid modes are ['all',...]".
- Generate-vs-add wording asymmetry: do_add:212 says "Please **choose**", do_generate:269 says
  "Please **chose**" (typo). Both list the modes space-joined, not as a Python list repr.

### 2. Non-perturbable *pert order* -> aMC@NLO `validate_model` (NOT extract_process 5269-5273/5286)
A bare `[ORDER]` (no `option=`) classifies as nlo_mode=`'all'` -> aMC@NLO `do_add`, which calls
`self.validate_model(proc_type[1], coupling_type=proc_type[2])` (amcatnlo_interface:513) BEFORE
`extract_process` (525). `validate_model` (loop_interface:297-356) tests
`any(coupl not in self._curr_model['perturbation_couplings'] for coupl in coupling_type)` (312-313).
If true and the model is NOT auto-upgradeable, it logs
**"The current model %s does not allow to generate loop corrections of type %s."** (325-326) then
raises `InvalidCmd("The model %s cannot handle loop processes")` (354-356).
Three probes (end-to-end vs isolation):
| input | end-to-end `generate` (USER SEES) | direct `extract_process` (isolation) |
|---|---|---|
| `[NP]` SMEFTatNLO | validate_model "does not allow to generate loop corrections of type ['NP']" + raise "cannot handle loop processes" (loop_interface:325-326/355-356) | 5286 "Perturbation order NP is not among the perturbation orders allowed for by the loop model." |
| `[QED]` SMEFTatNLO | same validate_model message for ['QED'] | (5286, same) |
| `[EW]` loop_qcd_qed_sm | validate_model "...loop corrections of type ['EW']" + raise | 5269-5273 "The loaded model does not defined a coupling order hierarchy for these couplings: ['EW']" |

So the inner guard that fires *in isolation* differs by case (5286 vs 5269-5273 — depends whether the
order is in `order_hierarchy`), but the LIVE-path message is uniformly validate_model's.

## The auto-upgrade twist: validate_model can SILENTLY FIX instead of reject
For `sm`/`loop_sm`-prefixed model names, validate_model does NOT raise — it auto-loads the loop
variant. `generate u u~ > d d~ [QCD]` under `import model sm` prints
**"The current model sm does not allow to generate loop corrections of type ['QCD']."** as an INFO,
then **"MG5_aMC now loads 'loop_sm'."** (loop_interface:328-352) and generation proceeds normally.
So the SAME validate_model branch (325-326) that REJECTS `[NP]`/`[EW]` (non-upgradeable model)
UPGRADES `sm`+`[QCD]`. Consequence: extract_process's loop-model guard (5283 "The current model does
not allow for loop computations.") is effectively UNREACHED on the live bracket path — by the time
extract_process runs, validate_model has either upgraded the model to a LoopModel or already raised.
5283 is reachable only via the base `madgraph_interface.do_add` -> extract_process (3310) path, which
a bracket line never takes (the Switcher routes every bracket to aMC@NLO/MadLoop, switcher page).

## Which guard owns "what the user sees" — the routing rule
- "What error does `generate [X]` print?" -> the OUTER guard (Switcher 268/211 for a bad OPTION;
  validate_model 325-326/355-356 for a non-perturbable ORDER). This is the user-visible answer.
- "What does `extract_process` enforce in isolation / what guard exists at the parse layer?" -> the
  INNER guard (4871 / 5269-5273 / 5286). Real code, correct logic, but shadowed on the live path.
- "Does the model get auto-upgraded?" -> validate_model (loop_interface:310-352), `sm`/`loop_sm` only.

## Boundary
The bracket parse and the inner guards (4871/5269-5273/5283/5286) are my slice. `validate_model`'s
upgrade/raise SEMANTICS and which models it can upgrade are nlo-model slice; cited here only to
establish the live-path rejection point. The Switcher routing that picks aMC@NLO is the switcher
page (my slice, the bracket->interface classification).
