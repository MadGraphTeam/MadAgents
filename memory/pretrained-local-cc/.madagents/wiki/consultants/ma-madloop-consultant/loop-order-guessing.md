---
description: How MadLoop bounds loop-diagram coupling orders — guess_loop_orders / from_squared, WEIGHTED target, +2 perturbed-order rule (loop_diagram_generation.py, MG5_aMC v3.7.1)
---

# Loop order guessing

`$MADGRAPH_INSTALL/madgraph/loop/loop_diagram_generation.py`. Loop generation needs an upper bound on coupling orders or it would generate infinitely; MadGraph guesses one from the born + hierarchy.

## Worked example in source (:598-617) — illustrative; derive the bound per process
The rule is: `target_weighted_order = (largest born weighted order) + 2*max(perturbed hierarchy value)`. The numbers below are for THIS one process only — re-derive per process from its born content and hierarchy, never reuse the integers.
`sm uu~ > dd~ [QCD,QED]`, hierarchy QCD=1, QED=2. Born LO contributions (QED=4),(QED=2,QCD=2),(QCD=4) have summed weighted orders 8,6,4. Largest born weighted order (4) + 2*max(perturbed hierarchy)=2*2=4 ⇒ `target_weighted_order = 8`. Keeps all born, excludes NLO (QED=6) and (QED=4,QCD=2).

## guess_loop_orders_from_squared (:197-216)
Runs only when squared orders other than WEIGHTED are set and not also in `orders`.
- `'>'`-type squared bound ⇒ can't infer, skip (:204).
- value≥0: `orders[order] = value - bornminorder` (:209).
- value<0 with born: `orders[order] = bornminorder + 2*(-value-1)` (leading / N^n term, :216).

## guess_loop_orders (:218-298) — when only WEIGHTED (or nothing) is squared-constrained
- `:225` `max_pert_wgt = max(hierarchy[o] for o in perturbation_couplings)`.
- `:242-244` `min_born_wgt = max(born min WEIGHTED, sum of user amplitude-order weights)`.
- `:249-250` if WEIGHTED not user-set: `squared_orders['WEIGHTED'] = 2*(min_born_wgt + max_pert_wgt)`. (This is why a generated process shows a WEIGHTED squared order you didn't type; see caution.)
- `:258-261` `trgt_wgt` = WEIGHTED - min_born_wgt (positive case).
- `:269-286` per-order max: perturbed order with hierarchy value v≠1 ⇒ `(trgt_wgt-min_nvert-2)/(v-1)`; v==1 ⇒ `trgt_wgt`. Non-perturbed similar with `-2*min_pert`.
- `:292-298` then tighten with born max order (+2 if perturbed) when that is a better bound.

## Enforcing user orders (:718-729)
After guessing, user-specified born orders are re-imposed: perturbed orders get `user+2`; WEIGHTED gets `user+2*min(pert hierarchy)`.

## Loop-induced WEIGHTED (no born) (:776-783)
If no born, no squared/amplitude orders, hierarchy present: `squared_orders['WEIGHTED'] = 2*(loop min WEIGHTED + max(pert wgts) - min(pert wgts))`.

## Caution
- The guessed `squared_orders['WEIGHTED']` is added to the process even though the user did not type it; `generate_diagrams` reverts it at :893 so the nice_string round-trips. But intermediate displays/logs may show it.
- The bound is a heuristic to catch dominant loops; for mixed-order perturbation it can silently drop subleading mixed loops — generate_diagrams emits warning_msg at :736-747 if a non-perturbed order bound is below the born max. (caution, not a runtime claim)
