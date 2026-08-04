---
description: proc_validity (loop_interface.py:211, called at do_add:527) — the NLO add-time re-validation hook; live checks + the dead `if not 'real':` branch that disables the loop-model/gauge re-checks.
---

# `proc_validity` — NLO add-time process re-validation hook

`aMCatNLOInterface.do_add` calls `self.proc_validity(myprocdef, 'aMCatNLO_%s' % proc_type[1])` at `$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_interface.py:527` — *after* `extract_process`/`extract_decay_chain_process` builds `myprocdef`, *before* the order re-validation logic (533+, see [[do-add-nlo-order-revalidation]]). `proc_validity` is defined in `CommonLoopInterface`: `$MADGRAPH_INSTALL/madgraph/interface/loop_interface.py:211` (`def proc_validity(self, proc, mode)`). This is a re-validation the LO tree-level parser does NOT perform.

`mode` here is `'aMCatNLO_all'` / `'aMCatNLO_real'` / `'aMCatNLO_LOonly'` (`proc_type[1]`). At 217: `tool = 'MadLoop' if mode.startswith('ML5') else 'aMC@NLO'` → for the aMC@NLO add path, `tool='aMC@NLO'` and `mode` does NOT start with `'ML5'`.

## LIVE checks (fire on the aMC@NLO path) — loop_interface.py
- `222`: empty/falsy `proc` → `InvalidCmd("Empty or wrong format process, please try again.")`.
- `227-229`: if existing amps and `self._curr_amps[0].get_ninitial() != proc.get_ninitial()` → `InvalidCmd("Can not mix processes with different number of initial states.")`. (Re-validation that successive `add process` lines share initial-state count — 1→N decay cannot be mixed with 2→N.)
- `239-243`: `ProcessDefinition` + `mode=='ML5'` multiparticle-label reject — **NOT** on the aMC@NLO path (mode is `'aMCatNLO_…'`, not literal `'ML5'`).
- `245-247`: `proc['decay_chains']` → `InvalidCmd("ML5 cannot yet decay a core process including loop corrections.")`. **Fires on aMC@NLO path** (guard is unconditional on mode). A `,`-decay-chain where the CORE has loop corrections is rejected here. (Distinct from the do_add:522 `are_decays_perturbed()` reject which targets perturbed DECAY legs; this targets the presence of a decay chain at all when loops are on the core — but note do_add only sets `decay_chains` via `extract_decay_chain_process`, and the do_add:522-523 guard already rejects perturbed decays first.)
- `249-252`: `proc.are_decays_perturbed()` → `InvalidCmd("The processes defining the decay of the core process cannot include loop corrections.")` — unconditional on mode, fires on aMC@NLO path (a second perturbed-decay net after do_add:522).
- `254-256`: `not proc['perturbation_couplings'] and mode.startswith('ML5')` — ML5-only, NOT aMC@NLO path.
- `277-283`: `rate_proc_difficulty(proc, mode)` (def at loop_interface.py:153); when `proc_diff` exceeds the difficulty threshold literal (read at 277-283) → `logger.warning` "appears to be of challenging difficulty, but it will be tried anyway." Non-fatal.
- `285-291`: **v3.1-syntax ambiguity re-check** — if `perturbation_couplings AND orders AND not squared_orders` and any order value not in `{0,99}`: builds an ambiguity message (paper 1804.10017 syntax dropped since v3.1.0; "replace QED→aEW, QCD→aS"), and if `not self.options['acknowledged_v3.1_syntax']` → **raises `Exception`** telling the user to `set acknowledged_v3.1_syntax True --global`. This is a hard crash the LO parser never does — it guards against the old aS/aEW-as-QCD/QED order syntax being misread.

## DEAD branch — `if not 'real':` (loop_interface.py:257) — the trap
Line 257 reads literally `if not 'real':`. `'real'` is a non-empty string literal → always truthy → `not 'real'` is **always False**. The ENTIRE block 257-275 is therefore **dead on every call** (probe-confirmed: `not 'real'` → `False`, `bool('real')` → `True`). That dead block contains what LOOK like the core NLO model/gauge re-validations:
- `258-261`: loop-model requirement (`not isinstance(self._curr_model, LoopModel) or not perturbation_couplings` → "current model does not allow for loop computations").
- `263-268`: missing perturbation-order check (`p_order not in model.perturbation_couplings` → "Perturbation orders … not among the perturbation orders allowed for by the loop model").
- `270-275`: the non-`[[],['QCD']]` gauge re-check ("MadLoop can only work in the Feynman gauge for these. Please set the gauge to Feynman").

**None of these fire via `proc_validity`.** Anyone reading this method top-to-bottom would conclude aMC@NLO re-checks the loop-model adequacy and the Feynman-gauge requirement at add-time here — it does not. The real loop-model upgrade / adequacy enforcement is `validate_model` (loop_interface.py:297), called separately at `do_add:513` — that is the **nlo-model slice's** territory (loop_sm upgrade, perturbation_couplings vs model). The `[[],['QCD']]` Feynman-gauge predicate also lives on the model-load / coupling-order seam, not here. Do not cite proc_validity:270 for "where the gauge gets checked" — that line is dead.

## `validate_model` does NOT error on `import model sm` — it AUTO-UPGRADES (claim-1 correction)
Docstring (297-298): "Upgrade the model sm to loop_sm if needed". For a tree `sm` + `[QCD]` process, validate_model (do_add:513) does **not** raise "Cannot find the model" or any error — it transparently re-imports the loop model:
- `310-313`: model is not a LoopModel (or lacks the requested perturbation order) → enters the upgrade block.
- `331` sm branch: for `coupling_type==['QCD']` → `add_on=''` → `347/352`: `logger.info("MG5_aMC now loads 'loop_sm'.")` and `self.exec_cmd("import model loop_sm", precmd=True)`. For `['QED']`/`['QCD','QED']` → `add_on='qcd_qed_'` → loads `loop_qcd_qed_sm` (and forces Feynman gauge, 333-337). So `generate p p > t t~ [QCD]` after `import model sm` **succeeds** via silent loop_sm swap — the LO idiom of importing `sm` is auto-corrected, not rejected.
- The ONLY hard error is a **non-sm, non-loop tree model** that cannot be upgraded: `354-356` `raise self.InvalidCmd("The model %s cannot handle loop processes" % model_name)` (fires when `stop=True`; the do_add:513 call defaults stop=True). That text is "cannot handle loop processes", NOT "Cannot find the model".
- `real`/`LOonly` loop_types (314-322) don't even upgrade — they just `logger.info` a caveat and proceed on the tree model.

So claim "`import model sm` for NLO gives a Cannot-find-the-model error" is **wrong on both counts**: sm auto-upgrades (no error), and the non-upgradeable-model error is worded "cannot handle loop processes". The loop-model REQUIREMENTS/what loop_sm provides (R2+UV) are nlo-model's slice; the do_add:513 gate + auto-upgrade OUTCOME + error text are the amcatnlo interface path.

## Relationship to do_add order re-validation
`proc_validity` (527) is the STRUCTURAL re-validation (initial-state count, decay-chain/loop, syntax-ambiguity); the order/squared-order re-validation and perturbation bump (533-673) come AFTER it. See [[do-add-nlo-order-revalidation]] for the order logic. The two are sequential add-time gates.

## Cautions
- The `if not 'real':` always-False guard (257) is a textbook dead-code-liveness trap: the loop-model/gauge re-checks are present but unreachable via proc_validity. Treat any "proc_validity rejects non-Feynman gauge / inadequate loop model" claim as INFERRED-and-wrong until the reachable enforcement site (validate_model:513 → nlo-model slice) is named.
- The v3.1-syntax Exception (291) is gated on the `acknowledged_v3.1_syntax` option — a machine that has run `set acknowledged_v3.1_syntax True --global` once will never see it. So its firing is install-state-dependent, not purely process-dependent.
- proc_validity is shared with the ML5/MadLoop interface; several of its branches (multiparticle-label 239, perturbation-required 254) are ML5-only and never fire on the aMC@NLO add path. Mode-gate every branch before attributing it to aMC@NLO.
