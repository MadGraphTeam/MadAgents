---
description: The ordered catalog of every guard/Exception on the LIVE NLO generate/add parse path (Switcher routing -> check_add -> aMC@NLO do_add -> extract_process inner guards), in firing order, each marked LIVE or SHADOWED/DEAD. The single-$ guard, the validity guard, validate_model, the decay guards, and the inner extract_process guards in one sequence. Consolidates the per-guard instance pages into a path-ordered verification-at-parse view.
---

# NLO parse-guard firing order (the verification-at-parse catalog)

v3.7.1 / $MADGRAPH_INSTALL (VERSION 3.7.1, 2026-04-29).
Files: `$MADGRAPH_INSTALL/madgraph/interface/{master_interface,amcatnlo_interface,loop_interface,madgraph_interface}.py`.

This page answers "what gets REJECTED/VALIDATED at process-spec time for an NLO `generate`/`add`,
and IN WHAT ORDER" by walking the LIVE path top-to-bottom. It consolidates guards that the
per-mechanism pages document in isolation (gauge-restriction, shadowed-guards, create-loop,
amcatnlo-overwrite, np-order) into one firing sequence. Each guard is marked **LIVE** (the
user can actually hit it on a `generate [X]`) or **SHADOWED/DEAD** (real code, unreached on the
live bracket path — an earlier guard catches the same case, or the branch is unreachable).

## The live path for a bracketed `generate`/`add`
A `[...]` line NEVER reaches `MadGraphCmd.do_add` directly. The Switcher classifies the bracket
(`extract_process_type`) and routes any real bracket to **aMC@NLO** (all/real/LOonly) or **MadLoop**
(virt/sqrvirt) or **create_loop_induced** (noborn). For the dominant `all`/`real`/`LOonly` route the
order is: Switcher.do_{generate,add} -> aMCatNLOInterface.do_add -> (check_add, then
extract_process_type x1, then extract_process). The guards fire in this order:

### STAGE A — Switcher (master_interface), routing layer (runs FIRST)
| # | guard | line | predicate | raises | LIVE? |
|---|---|---|---|---|---|
| A1 | invalid NLO **option** | do_add 211-213 / do_generate 268-270 (`The NLO mode %s is not valid. Please ch[o]se one among:`) | `nlo_mode not in self._valid_nlo_modes` | InvalidCmd | **LIVE** — shadows extract_process 4870-4872 (4871 "Valid modes are [...]") for a bogus `option=`. do_add says "choose", do_generate "chose" (typo). |

`_valid_nlo_modes = ['all','real','virt','sqrvirt','tree','noborn','LOonly','only']`
(madgraph_interface:3035). A1 is the user-visible invalid-mode message; the inner 4871 is shadowed.
(do_add raise is at **212**, do_generate at **269**.)

### STAGE B — CheckFKS.check_add (amcatnlo_interface), runs at do_add ENTRY (458 calls 118)
| # | guard | line | predicate | raises | LIVE? |
|---|---|---|---|---|---|
| B1 | bare single-`$` | check_add **129** (`'$ syntax not valid for aMC@NLO. $$ syntax is on the other hand a valid syntax.'`) | `'$' in args` (a bare `$` TOKEN in the split arglist) | InvalidCmd | **LIVE** — this is the user-visible single-`$` rejection on the NLO path. |

`do_add` calls `self.check_add(args)` at **458** (before the 476 guard below). `check_add`
(118-129) first strips `--ewsudakov`, calls `super().check_add`, then the 129 `$`-token raise.
Probe-confirmed (loop_sm): both `generate u u~ > d d~ $ g [QCD]` and `add process ... $ g
[QCD]` raise the **129** InvalidCmd; `$$` survives (token is `$$`, not `$`). The `$$` semantics are
diagram-filter slice; the *rejection-at-NLO-parse* is on my path.

| # | guard | line | predicate | raises | LIVE? |
|---|---|---|---|---|---|
| B2 | glued single-`$` (regex) | do_add raise **476**, regex **475** (`'Single $ syntax is not supported at NLO, please use $$'`, MadGraph5Error) | `re.search(r"\b\$\b", line)` | MadGraph5Error | **LIVE** for the GLUED form `d$g` — B1 does NOT shadow it (disjoint inputs). |

**B1 and B2 catch DISJOINT single-`$` forms** — neither shadows the other for its own targeted input:
- B1 (`'$' in args`) fires only on a **space-separated** `$` token: `> d d~ $ g`. The regex `\b\$\b`
  does NOT match this (probe: `re.search(r'\b\$\b','... $ g')` is None), so B2 would not have caught it.
- B2 (`re.search(r"\b\$\b", line)`) fires only on a `$` glued **between two word chars**: `d$g` /
  `a$b`. `'$'` is not a standalone arglist token there, so B1's `'$' in args` is False — B1 MISSES it.
- A `$` adjacent to a non-word char like `~` (`d~$g`) hits NEITHER guard (no `$` token, `~` breaks
  the `\b`); it passes both and reaches the diagram-filter parser.
- `$$` hits neither (`\b\$\b` does not match `$$`); double-`$` survives.

Probe-confirmed (loop_sm): `generate u u~ > d d~ $ g [QCD]` -> **B1** InvalidCmd (129);
`generate u u~ > d d~ g d$g [QCD]` -> **B2** MadGraph5Error (476, "Single $ syntax is not supported
at NLO, please use $$"); `generate u u~ > d d~ $$ g [QCD]` -> generates (3 born/66 real/18 virt).
B2 has a DIFFERENT message and exception type (MadGraph5Error, not InvalidCmd). The preceding
comment (474) "convert the single $ to $$ automatically" IS stale — the code RAISES, never converts.
So B2 is a LIVE guard for a narrow (unusual/malformed) input, NOT a dead one; the only "shadowing"
is that the COMMON space-separated `$ particle` form is owned by B1.

### STAGE C — aMCatNLOInterface.do_add body (after the 478 re-parse)
`proc_type = self.extract_process_type(line)` at **478** (the THIRD bracket parse;
amcatnlo-overwrite + switcher pages). Then, in order:
| # | guard | line | predicate | raises/effect | LIVE? |
|---|---|---|---|---|---|
| C1 | compiler check skip | 479-480 | `proc_type[1] not in ['real','LOonly']` | runs `check_compiler` (real/LOonly skip — no virtual ME) | LIVE (not a reject; mirrors loop-model exemption) |
| C2 | NLO-EW citation banner | 485-491 | `proc_type[2] != ['QCD'] and proc_type[1]=='all'` | logs banner (QED in orders -> "NLO EW corrections" arXiv:1804.10017; else "not SM-QCD") one-shot | LIVE (banner, not reject) |
| C3 | EW-Sudakov warning | 508-511 | `self.ewsudakov and 'QED' not in proc_type[2]` | warns Sudakov incomplete | LIVE (warning) |
| C4 | **validate_model** | **513** | always called `validate_model(proc_type[1], coupling_type=proc_type[2])` | rejects non-perturbable ORDER ("...does not allow to generate loop corrections of type [...]", loop_interface:325-326 -> raise 354-356) OR **auto-upgrades** sm->loop_sm | **LIVE** — shadows extract_process 5269-5273 + 5283/5286. The user-visible non-perturbable-order message. nlo-model owns its semantics. |
| C5 | perturbed-decay reject | **522-523** | `',' in line` branch: `myprocdef.are_decays_perturbed()` True | MadGraph5Error("Decay processes cannot be perturbed") | **LIVE** — fires when the DECAY carries the bracket (`p p > t t~, (t > b w+ [QCD])`). |
| C6 | proc_validity (decay-on-core) | **527** | always `proc_validity(myprocdef,'aMCatNLO_%s'%proc_type[1])`; inside, loop_interface:245-247 `proc['decay_chains']` non-empty | InvalidCmd("ML5 cannot yet decay a core process including loop corrections.") | **LIVE** — fires when the CORE carries the bracket + an (unperturbed) decay chain (`p p > t t~ [QCD], t > b w+`). C5 did NOT fire (decay unperturbed), so C6 is reached. |
| C6a | squared-order `<=`-only | **542** | a squared_order constraint is not of `<=` type | MadGraph5Error("The squared-order constraints passed are not '<='. ...not supported at NLO") | **LIVE** — at NLO only `<=` squared-order constraints allowed (parallels D2 for amplitude orders). |
| C6b | auto-order undetermined | **550** | `find_optimal_process_orders` cannot determine orders | MadGraph5Error("Process orders cannot be determined automatically.") | **LIVE** — fires in the no-explicit-order auto-determination block (529-561). |
| C6c | auto-order negative | **559** | auto-determined qed/qcd order < 0 | MadGraph5Error("Automatic process-order determination lead to negative constraints:") | **LIVE** — e.g. bare `[QCD]` in SMEFTatNLO (qed=-1); explicit order required (np-order page). |
| C7 | perturbation_couplings OVERWRITE + order bump | 629-674 | overwrite gated `not myprocdef['orders'] and nlo_mixed_expansion` (default True); bump iterates perturbation_couplings | mutates pert/orders/squared_orders | LIVE (mutation, not reject) — amcatnlo-overwrite page. |

C5 vs C6: which decay message the user sees depends on WHERE the bracket sits (bracket-on-decay ->
C5; bracket-on-core -> C6). Both shadow the base `madgraph_interface.do_add` "cunjunction" guard
(3283-3289) and the 3296-3297 "Decay processes cannot be perturbed." (WITH period) — both base
guards are DEAD for a real bracket (the Switcher never routes a real bracket to MadGraphCmd.do_add).
create-loop + switcher pages carry the full decay-guard treatment.

### STAGE D — extract_process inner guards (madgraph_interface), run at 478->525->extract_process
`extract_process` is called at **525** (`MadGraphCmd.extract_process(self,line)` for the non-decay
branch; for a decay line `extract_decay_chain_process` is used at 521). Its inner guards, in order:
| # | guard | line | predicate | raises | LIVE? |
|---|---|---|---|---|---|
| D0 | option->LoopOption/HasBorn remap + invalid-option | 4856-4877 (raise 4870-4872) | `option not in _valid_nlo_modes` | InvalidCmd "NLO mode %s is not valid. Valid modes are [...]" | **SHADOWED** by A1 (Switcher) for bogus option on the live path; LIVE only on a DIRECT extract_process call. |
| D1 | **gauge FD/axial** | predicate **4879**, raise **4880** | `LoopOption != 'tree' and self.options['gauge'] in ['FD','axial']` | bare `Exception` "Gauge %s is only supported/validated for tree level amplitude" | **LIVE** — fires for ANY non-tree bracket; reads stored gauge, not at `set gauge`. gauge-restriction page. |
| D2 | constrained-orders `==`/`>` | predicate **4983**, raise **4984** | `constrained_orders and LoopOption != 'tree'` | InvalidCmd "Amplitude order constraints (for not LO processes) can only be of type <=" | **LIVE** — `[QCD] QED==2` fails, `[QCD] QED<=2` OK. |
| D3 | squared-orders-without-pert fill | 4994 | `orders=={} and squared_orders!={} and not perturbation_couplings` | fills orders from squared_orders (LO-only path) | LIVE (not a reject; only when no bracket) |
| D4 | tagged-particle | **5227-5231** | `LoopOption in ['virt','sqrvirt','tree','noborn']` and a leg tagged | InvalidCmd "%s mode does not handle tagged particles" | **LIVE** (the 'sqrvirt' literal is dead — already remapped to 'virt'); all/real allow tags. |
| D5 | all/loonly keyword expansion | 5250-5253 | `perturbation_couplings.lower() in ['all','loonly']` | expands pert to full model set; loonly sets LoopOption='LOonly' | LIVE (mechanic, not guard) |
| D6 | order_hierarchy sort | 5266-5273 | split_orders sort KeyError | InvalidCmd "The loaded model does not defined a coupling order hierarchy for these couplings:" | **SHADOWED** by C4 (validate_model) for a non-perturbable bracket order on the live path; LIVE on a direct call (e.g. `[EW]` in isolation). |
| D7 | tree= empties pert list | 5278-5279 | `LoopOption=='tree'` | `perturbation_couplings_list=[]` | LIVE (the `[tree=QED=2]` split_orders-only path) |
| D8 | loop-model requirement | **5280-5289** | `perturbation_couplings_list and LoopOption not in ['real','LOonly']` -> model must be LoopModel (5283) and each pert in model['perturbation_couplings'] (5286) | InvalidCmd (5283 / 5286) | **SHADOWED** by C4 (validate_model auto-upgrades sm->loop_sm or rejects non-perturbable order) for the live path; LIVE on a direct extract_process call. |
| D9 | split_orders / loop_optimized warning | 5290-5296 | `not loop_optimized_output and LoopOption not in ['tree','real'] and split_orders!=[]` | warns + clears split_orders | LIVE (warning, silently drops per-order ME values). |
| D10 | store on ProcessDefinition | 5336-5352 | always | `'NLO_mode':LoopOption`, `'has_born':HasBorn`, `'perturbation_couplings':...`, `'split_orders':...` | LIVE (the parse result lands here). |

## Summary: which guards a user actually hits on `generate [X]` (LIVE), in order
A1 (bad option, Switcher) -> B1 (spaced `$`, check_add 129) / B2 (glued `d$g`, do_add 476) ->
[D0..D10 inside extract_process at 525:
D1 FD/axial gauge 4879/4880, D2 `==`/`>` constraint 4983/4984, D4 tagged particle 5227, D9 split_orders warn,
D10 store] -> C4 (non-perturbable order / auto-upgrade, validate_model 513) -> C5/C6 (perturbed/
decayed) -> C6a/b/c (squared-order/auto-order, 542/550/559) -> C7 (pert-couplings overwrite + bump).
NOTE the nesting: C4/C5/C6 are in do_add and C5/C6 + the D-guards both run *via* the 525
extract_process call (D-guards fire INSIDE extract_process, which do_add invokes at 521/525 — so the
D-stage gauge/constraint/tagged guards actually fire DURING C5/C6's extract step, before C6a+). The inner extract_process guards that DUPLICATE an outer
check are SHADOWED: D0 (by A1), D6 + D8 (by C4). They are correct code, reachable only by a DIRECT
`extract_process`/`extract_process_type` call, never on a Switcher-routed `generate`/`add`.

## Dead / shadowed guards on this path (the verification-at-parse "false friends")
- **B2** (do_add 476 MadGraph5Error single-`$`) — **NOT dead**: B1 and B2 catch
  DISJOINT single-`$` forms (B1 = spaced `$ g` token; B2 = glued `d$g`). B2 is LIVE for the glued
  form. Only the COMMON spaced form is owned by B1. Comment 474 ("convert automatically") IS stale —
  code raises, never converts.
- **D0** (extract_process 4870-4872 invalid-option) — shadowed by A1 (Switcher validity).
- **D6** (5269-5273 order_hierarchy) + **D8** (5283/5286 loop-model/pert-membership) — shadowed by
  C4 (validate_model). 5283 also unreachable because validate_model upgrades sm->loop_sm first.
- **base `madgraph_interface.do_add` decay guards** (3283-3289 "cunjunction", 3296-3297 "Decay
  processes cannot be perturbed." WITH period) — dead for a real bracket (never routed to
  MadGraphCmd.do_add). Live decay rejections are C5 (522, NO period) / C6 (245).
- **loop_interface.proc_validity 257-275** (`if not 'real':`) — unreachable dead block (`not 'real'`
  is always False); its loop-model/gauge restriction is enforced live only via D8 (shadowed) /
  validate_model. create-loop page.
- **'sqrvirt' literal in D4** (5227 set) — dead; sqrvirt already remapped to 'virt' at 4866.

## Boundary
The bracket parse, the routing classification, and the guards that read the bracket-set fields at
process-spec time are my slice. `validate_model` (C4) SEMANTICS + which models it upgrades are
nlo-model slice; `$$`/`$` diagram-filter SEMANTICS are diagram-filter slice (I own only the
NLO-path single-`$` rejection point); FKS/MadLoop/exporter use of the stored NLO_mode/has_born is
fks/madloop/nlo-export slice; the `==`/`<=` amplitude-constraint syntax is coupling-order slice.
