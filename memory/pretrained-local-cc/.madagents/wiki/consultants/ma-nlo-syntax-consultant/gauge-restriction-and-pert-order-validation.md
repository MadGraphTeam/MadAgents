---
description: Parse-time guards after the bracket parse — the FD/axial gauge restriction for loop processes, loop-model requirement, tagged-particle rejection, and pert-order validation against the loop model.
---

# Gauge restriction and perturbation-order validation

All in `extract_process`, `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`. v3.7.1.

## Gauge restriction (interface:4879-4880)
Immediately after the bracket parse:
```python
if LoopOption != 'tree' and self.options['gauge'] in ['FD','axial']:
    raise Exception('Gauge %s is only supported/validated for tree level amplitude' % self.options['gauge'])
```
- Fires for ANY non-tree LoopOption (all/virt/real/noborn/sqrvirt/LOonly/only) — i.e. whenever a `[...]` matched without `option=tree`.
- `'FD'` = 4D-Helicity / 't Hooft-Feynman dimensional, `'axial'` = axial gauge. Loops require Feynman or unitary.
- **Where it fires**: inside `extract_process` (pipeline stage 2, process specification), reading the already-stored `self.options['gauge']`. NOT at the `set gauge` call. So `set gauge axial` succeeds; the error only appears when you later `generate ... [QCD]`.
- Raised as bare `Exception`, not `InvalidCmd` — so it is not caught by the usual InvalidCmd handlers; it propagates.
- Default gauge is `'unitary'` (interface options default ~3107), which passes the guard.

## Loop-model requirement (interface:5280-5289)
If `perturbation_couplings_list` non-empty AND `LoopOption not in ['real','LOonly']`:
- model must be a `loop_base_objects.LoopModel`, else `InvalidCmd("The current model does not allow for loop computations.")`.
- each pert order must be in `model['perturbation_couplings']`, else `InvalidCmd("Perturbation order %s is not among the perturbation orders allowed for by the loop model.")`.
Note `real` and `LOonly` are EXEMPT from the loop-model requirement (they need no virtual matrix element).
**LIVENESS CAVEAT (probe):** these 5283/5286 messages are INNER guards SHADOWED on the
live `generate`/`add` path. A bracketed line routes through the Switcher to aMC@NLO `do_add`, whose
`validate_model` (amcatnlo:513) runs BEFORE extract_process (525): for a non-LoopModel it either
AUTO-UPGRADES (`sm`+`[QCD]` -> loads loop_sm, so 5283 never fires) or rejects with
"...does not allow to generate loop corrections of type [...]" (loop_interface:325-326). For a
non-perturbable pert order it raises validate_model FIRST, so 5286 is unreached. 5283/5286 fire only
on a DIRECT `extract_process` call. Full treatment + probe table on
`extract-process-guards-shadowed-by-outer-routing.md`.

## Tagged-particle rejection (interface:5227-5231)
If `LoopOption in ['virt','sqrvirt','tree','noborn']` and a leg is tagged -> `InvalidCmd("%s mode does not handle tagged particles")`. (sqrvirt has already been remapped to LoopOption='virt' by this point, so it is covered via 'virt'.) `all` and `real` allow tagged particles (they go through the MultiTagLeg branch).

## 'all'/'loonly' keyword expansion (interface:5249-5253)
The order-keyword path (lowercased pertOrders `all`/`loonly` -> full model pert set, `loonly`
also sets `LoopOption='LOonly'`) is a parse-mechanics concern, not a guard. Full treatment
(regex interaction, multi-token fall-through, probe table) lives on
`bracket-parse-and-loopoption-mapping.md`. Listed here only because it runs (5249-5253)
between the tagged-particle guard (5227) and the loop-model guard (5280), so it can change
`LoopOption` before the later guards read it.

## constrained-orders guard (interface:4983-4985)
Amplitude order constraints of type `==` or `>` are rejected for non-tree LoopOption: `InvalidCmd("Amplitude order constraints (for not LO processes) can only be of type <=")`. So `[QCD] QED==2` fails; `[QCD] QED<=2` is fine.

## split_orders / loop_optimized_output caution (interface:5290-5296)
If `loop_optimized_output` is False AND LoopOption not in ['tree','real'] AND split_orders non-empty, MG warns split_orders cleared ("MadLoop output will not be able to provide such quantities") and sets `split_orders=[]`. Watch out: requesting per-order ME values under the default-non-optimized loop output silently drops them.

## `check` command also reads bracket pertOrders (interface:4564-4577, in do_check)
The `check` command's gauge-comparison branch (re-parses the same line under both unitary and
Feynman gauge to compare results) is gated `myprocdef.get('perturbation_couplings') in [[],['QCD']]`
(4566). So the dual-gauge check only runs for tree (`[]`) or pure-QCD-perturbed (`['QCD']`) processes;
a non-QCD bracket (e.g. `[QED]`, `[QCD QED]`) skips it. A LIVE pert_couplings-keyed guard (unlike the
dead `[[],['QCD']]` block in loop_interface proc_validity 270-275). The `check` mode routing itself is
Switcher.do_check (master_interface:239-258) — see switcher page.
The FULL do_check body — the NLO_mode `all`->`virt` override (4413), the `check gauge` ENTRY guard
(4428, the other LIVE `[[],['QCD']]` site) and the timing/stability/profile loop-requirement guard
(4421) — is on `create-loop-induced-and-noborn-override.md` (the post-parse-NLO_mode-mutation page).
Three PROCDEF-pert-keyed `[[],['QCD']]` sites: 4428 + 4566 LIVE, proc_validity 270-275 dead. (A bare
grep finds more `[[],['QCD']]` literals — loop_interface 207/360, madgraph_interface 5814/8134 — but
those test `_curr_model['perturbation_couplings']`, the MODEL field, not the process mode.)
