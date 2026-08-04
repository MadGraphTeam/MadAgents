---
description: perturbation_couplings is one list set once from perturbative_expansion>0 and the single authority at every downstream loop stage (gauge, generate gate, [all] expansion, CT-vertex selection) - so a model's perturbative_expansion choice deterministically propagates to which CT vertices survive.
---

# `perturbation_couplings` is the spine of loop capability

(v3.7.1, `$MADGRAPH_INSTALL`.) Deeper principle uniting loopmodel-detection,
process-loop-capability-gates, ct-vertex-consumers, and bundled-online-loop-models: a loop
model's capability is carried by ONE list, `perturbation_couplings`, that is set once at
import and is then the SINGLE authority consulted at every later stage. No stage re-derives
it from the UFO; they all read the same list. Knowing this predicts behavior the instance
pages don't each enumerate, because the same list gates them all.

## The list, born once
- **Source of truth:** `coupling_orders.py`. Any order with `perturbative_expansion>0`
  becomes a key of `model['perturbation_couplings']` (import_ufo.py:498-512). A model with
  no such order gets a plain `base_objects.Model` (no list) and is loop-incapable.
- Per-model lists: loop_sm -> `['QCD']`; loop_qcd_qed_sm -> `['QCD','QED']` (pe=99 on both
  orders); 2HDM5F_NLO / 2HDMtII_NLO / 2HDMtypeII / SMEFTatNLO -> `['QCD']`.
- DO NOT carry a bundled count here — it is VOLATILE and has re-shipped wrong. The bundled
  loop-model SET (and whether loop_qcd_qed_sm is in `models/` at all) DRIFTS across builds;
  re-scan with the `>0` predicate (NEVER `=1`, which misses pe=99) per
  bundled-online-loop-models, which is the single source of truth for the live count/status.
  (A prior pass wrongly wrote SIX here; do not restate a count in this page at all — route.)

## The same list gates every downstream stage
Each stage READS `model['perturbation_couplings']` or its copy
`process['perturbation_couplings']` (set verbatim from the validated bracket list at
madgraph_interface.py:5348 -> Process attr base_objects.py:2974). Stages, in order:
1. **Gauge selection** — perturbation_couplings not in `[[],['QCD']]` (i.e. QED/EW) forces
   Feynman gauge, at BOTH import (madgraph_interface.py:5810-5829) and generate
   (loop_interface.py:358-367). QCD-only models exempt.
2. **Generate-time gate** — CheckLoop (loop_interface.py:310-357, the FIRST gate) and the
   later get_combined_legs Gate 1/2 (madgraph_interface.py:5283/5288) both test
   `coupl in model['perturbation_couplings']`. sm-family failures auto-upgrade
   loop_sm->loop_qcd_qed_sm rather than erroring (see process-loop-capability-gates).
3. **`[all]`/`[loonly]` expansion** — literally `' '.join(model['perturbation_couplings'])`
   (madgraph_interface.py:5253). `[all]` = "every order this model declares perturbative",
   model-defined, not fixed QCD+QED.
4. **CT-vertex selection in loop diagram gen** — `process['perturbation_couplings']` is read
   ~30x in loop_diagram_generation.py; the load-bearing CT filters are:
   - set_Born_CT (1226-1228): keep a UVtree CT iff `is_perturbating(perturbation_couplings)`
     AND `orders.keys() ∩ perturbation_couplings != {}`.
   - set_LoopCT_vertices (1348): keep R2/UVmass/UVloop iff `is_perturbating(perturbation_couplings)`.
   (`is_perturbating` returns True if the interaction's `perturbation_type` is None or in
   the list — base_objects.py:775.)

## The consequence the instance pages don't state
The unbroken chain is:
`coupling_orders.py:perturbative_expansion>0` -> `model['perturbation_couplings']` ->
(validate/expand) -> `process['perturbation_couplings']` -> `is_perturbating` + order-
intersection CT filters. So a model author's `perturbative_expansion` choice
DETERMINISTICALLY decides which CT vertices a process can ever pick up: a CT vertex whose
`perturbation_type`/orders fall outside the requested perturbation is filtered at selection,
never reaching a diagram. Catches cases beyond any single instance page: e.g. a model that
marks BOTH QCD and QED perturbative but a process requesting only `[QCD]` -> the QED CT
vertices are filtered at the order-intersection / is_perturbating step (they survive the
import, fail the per-process selection).

## Probe anchor (runtime-predictive tail)
PROBE-VERIFIED (generate-only, loop_sm / loop_qcd_qed_sm):
- `loop_sm; g g > t t~ [QCD]` -> 3 born, 36 virtual, 96 real (QCD CTs selected).
- `loop_sm; a a > t t~ [QED]` -> rejected at CheckLoop: "The current model loop_sm does not
  allow to generate loop corrections of type ['QED']." (QED not in its list).
- `loop_qcd_qed_sm; a a > t t~ [QED]` -> accepted, auto-Feynman, 2 born, 198 virtual, 214
  real (QED in its list -> QED CTs selected).
The exact per-process CT-vertex *count* for a mixed-perturbation model with a single-order
request is not separately probed here; the selection MECHANISM (filter on the list) is
source-confirmed and the accept/reject + diagram-count contrast above is probe-confirmed.

## Boundary
- Static + selection mechanism; predicts WHICH orders gate and WHICH CT vertices are
  eligible, plus the accept/reject outcome. Exact diagram/CT counts for arbitrary
  mixed-perturbation single-order requests need their own probe.
- The bracket PARSING and squared-order weighting are nlo-syntax slice; this page is only
  the perturbation_couplings flow those feed.
- Instance pages kept: they carry the per-stage file:line specifics this page indexes.
