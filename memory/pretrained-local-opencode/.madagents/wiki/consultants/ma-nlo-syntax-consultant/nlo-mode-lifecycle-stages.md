---
description: The bracket NLO_mode/has_born is a multi-stage lifecycle value — routing classification (extract_process_type) -> parse remap (LoopOption/HasBorn) -> stored on ProcessDefinition -> post-parse command override (do_check/create_loop_induced); no single stage is authoritative, and two stages disagree by name. Identify the stage before answering any "what mode does X end up with" question.
---

# NLO_mode is a multi-stage lifecycle value

`$MADGRAPH_INSTALL/madgraph/interface/{master_interface,madgraph_interface}.py`. v3.7.1 / $MADGRAPH_INSTALL.
Generalizes three instance pages (see Instances) into one principle. Static source-structure claim
(which stages touch the field, in what order); constituent facts were parse/traceback-probed on the
instance pages.

## The principle
The `[...]` bracket does NOT produce one authoritative NLO_mode. The mode a user types passes through
FOUR stages, parsed or rewritten at each. **No single stage's value is the answer for every consumer**,
and stages 1 and 2 can DISAGREE by name. So for any "what NLO_mode / has_born does process X end up
with" question: identify WHICH stage the question is about, then find the LAST stage that fires.

| stage | site | what it does | governs |
|---|---|---|---|
| 1. routing classification | `extract_process_type` master_interface:162-196 | parses bracket FIRST, returns `(type,option,pert_orders)` | which interface (MadGraph/MadLoop/aMC@NLO) handles the line |
| 2. parse remap | `extract_process` madgraph_interface:4862-4877 | re-parses bracket, collapses `option=` -> `LoopOption`/`HasBorn` (one-way) | every post-parse guard in extract_process |
| 3. stored value | ProcessDefinition dict madgraph_interface:5350 | `'NLO_mode':LoopOption, 'has_born':HasBorn` | the field downstream code reads |
| 4. post-parse override | do_check:4414, create_loop_induced:5392 | rewrites the stored NLO_mode | the FINAL mode for check / loop-induced |

## Why no single stage is authoritative (the cases this catches)
- **Stage 1 != stage 2 by NAME.** `extract_process_type` (stage 1) keeps the surface keyword: `[sqrvirt=]`
  -> option `'sqrvirt'`; `[LOonly]` -> `('NLO','LOonly',['QCD'])` (defaults to QCD). `extract_process`
  (stage 2) REMAPS: `sqrvirt` -> `LoopOption='virt'`+`HasBorn=False`; bracket-order `[loonly]` ->
  `LoopOption='LOonly'` + FULL model pert set (not just QCD). So stage 1's LOonly carries `['QCD']`
  while stage 2's carries the model's full perturbation_couplings — the SAME typed bracket yields
  different pert lists at the two stages. (Also the `virtsqr` typo: stage-1 returns `'sqrvirt'`, but
  do_generate:274 tests `'virtsqr'` — a name that no stage produces.) → switcher page + bracket-parse page.
- **Stage 2's keyword dies; only LoopOption/HasBorn survive.** After the 4862-4877 chokepoint the
  typed `option` variable is dead; every guard branches on post-remap `LoopOption`/`HasBorn`, never the
  keyword. sqrvirt-vs-virt survives ONLY through HasBorn. → loopoption-is-the-post-remap-discriminant.
- **Stage 4 overwrites stage 3 unconditionally for two commands.** `do_check` forces stage-3 `'all'`
  -> `'virt'` (4413-4414, "only virt makes sense to check"); `create_loop_induced` forces -> `'noborn'`
  (5392) regardless of the typed bracket. So `check g g > h [QCD]` ends NLO_mode='virt' though stage 3
  stored 'all'; a loop-induced process ends 'noborn' though the bracket may have said 'all'.
  → create-loop-induced-and-noborn-override.
- **Enumerated-complete (v3.7.1):** the ONLY `.set('NLO_mode', …)` sites across the three interface
  files are 4414 and 5392 (grep-confirmed); loop_interface reads NLO_mode (184/187/190 in
  proc_validity) but never sets it. So stage 4 has exactly two override sites.

## perturbation_couplings has a FIFTH touch-point (different field, same principle)
The four stages above track NLO_mode/has_born. The bracket's `perturbation_couplings` field has an
ADDITIONAL post-store mutation that NLO_mode does NOT: `aMCatNLOInterface.do_add` (amcatnlo_interface:
672-673) conditionally OVERWRITES `perturbation_couplings` to the model's full `coupling_orders` when
`not myprocdef['orders'] and nlo_mixed_expansion` (default True). Probe-confirmed: bare `[QCD]` in
loop_sm DISPLAYS as `[ all = QCD QED ]`, not `['QCD']`. It also runs a THIRD bracket parse
(`extract_process_type` at 478, beyond the two on stages 1-2) and bumps orders/squared_orders.
→ `amcatnlo-do_add-perturbation-couplings-overwrite.md`. So "the bracket is parsed TWICE" (older
claim on the switcher page) is really THREE times along the add/generate path, and the FINAL
`perturbation_couplings` is NOT the value extract_process stored. The four-`.set('NLO_mode')`
enumeration above is still complete FOR NLO_mode — this fifth site touches a different field.

## Predictive value beyond the instances
- Any NEW question "what mode does this bracket process become" is answered by walking stages 1->4 and
  taking the last that fires — not by reading the typed keyword. The instance pages each cover ONE stage;
  this page is the only one that says "find the stage first."
- Any FUTURE override added to a command body is, by construction, a stage-4 addition invisible to
  stages 1-3 (they run earlier). The remap (stage 2) guarantees future guards see only LoopOption/HasBorn.
  So both the stage-1/2 name-disagreement and the stage-4-wins ordering will hold for code added later.

## Boundary
This is the lifecycle of the NLO_mode/has_born FIELD through process specification (pipeline stage 2):
routing + parse + store + command-override. What FKS / MadLoop / the Fortran exporter DO with the final
stored value at generation/runtime is fks/madloop/nlo-export/amcatnlo slice. `change_principal_cmd`
mechanics are the Switcher's own.

## Instances (kept — each carries stage-specific detail)
- `switcher-extract-process-type-predispatch.md` — stage 1 (routing parser, its defaults, virtsqr typo).
- `bracket-parse-and-loopoption-mapping.md` — stage 2 parse + stage 3 landing (regex, remap table, order-keyword path).
- `loopoption-is-the-post-remap-discriminant.md` — stage 2's one-way collapse (keyword dies, guards read LoopOption).
- `create-loop-induced-and-noborn-override.md` — stage 4 (the two override sites + decay rejection).
- `amcatnlo-do_add-perturbation-couplings-overwrite.md` — fifth touch-point: the THIRD bracket parse + perturbation_couplings/orders/squared_orders overwrite in amcatnlo do_add.
