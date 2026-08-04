---
description: The Switcher pre-dispatch layer (master_interface) parses the bracket TWICE — extract_process_type classifies nlo_mode and routes generate/add to MadGraph/MadLoop/aMC@NLO BEFORE extract_process runs; its own LOonly default, no option-validity check, and the virtsqr typo.
---

# Switcher pre-dispatch and extract_process_type (the SECOND bracket parser)

`$MADGRAPH_INSTALL/madgraph/interface/master_interface.py`, class `Switcher`. v3.7.1 / $MADGRAPH_INSTALL.
THE bracket is parsed by TWO independent parsers AT THE
SWITCHER LAYER: `extract_process_type` here (routing) runs FIRST; `extract_process`
(madgraph_interface, my other pages) runs LATER inside the chosen interface's `do_add`.
Along the aMC@NLO add/generate path `extract_process_type` is INVOKED a
THIRD time — `aMCatNLOInterface.do_add` calls `self.extract_process_type` AGAIN (amcatnlo_interface:
478) for its own `proc_type` before calling extract_process (525). Runtime-probe-confirmed
(instrumented `generate u u~ > d d~ [QCD]`, loop_sm: exactly 3 calls at master_interface:266 do_generate,
master_interface:209 do_add, amcatnlo_interface:478 do_add). NOTE: all three are the SAME static
method — `extract_process_type` is defined ONLY on `Switcher` (162); the 478 `self.extract_process_type`
resolves to `Switcher.extract_process_type` via the `MasterCmd` MRO (Switcher first), NOT a separate
aMCatNLOInterface method (that class has no such attribute). So three distinct CALLS of one method,
not three methods. The third call + the perturbation_couplings overwrite it drives are on
`amcatnlo-do_add-perturbation-couplings-overwrite.md`.

## Why this matters: a `[...]` line never reaches the MadGraph-interface do_add directly
`MasterCmd` (master_interface:655) mixes in `Switcher`. Every `generate`/`add`/`check` first hits
`Switcher.do_{generate,add,check}`, which calls `extract_process_type(proc_line)` to classify the
line, switches the principal interface via `change_principal_cmd`, THEN delegates
`self.cmd.do_{generate,add}(...)`. So the bracket mode is read once for ROUTING before
`extract_process` ever re-parses it for the ProcessDefinition.

## extract_process_type (master_interface:162-196) — the routing parser
Static method. Returns `(type, option, pert_orders)`, `type ∈ {'NLO','tree'}`.
- Own sanity pre-pass (169-170): same space-insertion regex as extract_process (4836).
- Own regex (175): `^(.*)(?P<loop>\[(\s*(?P<option>\w+)\s*=)?(?P<orders>.+)?\])(.*)$`.
  Differs from extract_process's `(\w+\s*)*` pertOrders: here `orders` is `.+` (any chars).
- `--`-stripping (177): `re.split(r'\s\-\-', line,1)[0]` — anything after a `␣--` is excluded
  BEFORE the regex, so `[QCD] --no_warning=duplicate` classifies as `[QCD]` cleanly.
- Classification (178-196):
  - `option=='tree'` -> `('tree', 'tree', orders)`.
  - any other `option=` (single token) -> `('NLO', option, orders)` — **NO validity check here**.
    `[bogus=QCD]` returns `('NLO','bogus',['QCD'])`; the invalid-mode rejection happens later in
    `do_add`/`do_generate` (211-213 / 268-270) against `self._valid_nlo_modes`.
  - bare orders `== ['LOonly']` -> `('NLO','LOonly',['QCD'])` — **LOonly defaults to QCD here**,
    distinct from extract_process's order-keyword path (which expands to the FULL model pert set).
  - bare orders, len>0 -> `('NLO','all',orders)`.
  - empty -> `('tree',None,[])`.

### Probed classifications (reproduced from source)
| line | extract_process_type returns |
|---|---|
| `[QCD]` | ('NLO','all',['QCD']) |
| `[virt=QCD]` | ('NLO','virt',['QCD']) |
| `[sqrvirt=QCD]` | ('NLO','sqrvirt',['QCD']) |
| `[noborn=QCD]` | ('NLO','noborn',['QCD']) |
| `[LOonly]` | ('NLO','LOonly',['QCD']) |
| `[LOonly=QCD]` | ('NLO','LOonly',['QCD']) |
| `[bogus=QCD]` | ('NLO','bogus',['QCD']) (rejected later, not here) |
| `[QCD] --no_warning=duplicate` | ('NLO','all',['QCD']) |
| (no bracket) | ('tree',None,[]) |

## The routing tables (per nlo_mode)
`Switcher.do_generate` (260-278):
| nlo_mode | switch |
|---|---|
| all / real / LOonly | aMC@NLO (also pre-builds `self._fks_multi_proc = fks_base.FKSMultiProcess()`, 272) |
| virt / **virtsqr** | MadLoop (274) |
| noborn | (no branch — falls through, no switch) |

`Switcher.do_add` (200-236):
| nlo_mode | switch |
|---|---|
| all / real / LOonly | aMC@NLO (215) |
| virt / sqrvirt | MadLoop (217) |
| noborn | MadLoop->validate_model->MadGraph, then `create_loop_induced` (218-225) |
- `do_add` also has a `NoBornException` fallback (230-236): if the delegated do_add raises
  `fks_base.NoBornException` (FKS found no Born), it auto-switches to loop-induced via
  `create_loop_induced` and prints the 1507.00020 citation banner.

`Switcher.do_check` (239-258): all->MadLoop; real-> raises InvalidCMD ("Mode [real=...] not valid
for checking"); virt/sqrvirt->MadLoop.

## Import-time switch masks the routing for loop models (do_import 280-292)
`Switcher.do_import` switches the interface AT MODEL-IMPORT time: a `LoopModel` with non-empty
`perturbation_couplings` -> `change_principal_cmd('aMC@NLO')` (283-286). Probe-confirmed:
`import model loop_sm` leaves `current_interface == 'aMC@NLO'` before any generate.
Consequence: in the normal loop-model workflow the interface is ALREADY loop-capable, so a
missing per-command switch is masked.

## CAUTION: the `virtsqr` typo in do_generate (274) — latent, masked in normal flow
`do_generate` branch 274 tests `nlo_mode == 'virt' or nlo_mode == 'virtsqr'`, but
`extract_process_type` returns `'sqrvirt'` (not `'virtsqr'`) for `[sqrvirt=QCD]`. So
`generate ... [sqrvirt=QCD]` does NOT match the MadLoop-switch branch in do_generate.
`do_add` (217) spells it correctly (`'sqrvirt'`). This is a generate-vs-add asymmetry.
- Probe-confirmed (loop_sm): both `generate g g > h [sqrvirt=QCD]` and
  `add process g g > h [sqrvirt=QCD]` produce identical "0 Born, 4 loops, 2 R2, 0 UV" — the typo
  does NOT bite, because do_import already switched to aMC@NLO (the import-time switch above
  masks it). The typo would only matter if a `generate [sqrvirt=QCD]` ran while still in the
  MadGraph interface against a loop model — an edge case I did not hit.
- Recorded as a source-visible hazard, not a runtime-failure claim.

## Bracket + decay-chain (comma): WHICH guard fires depends on bracket CLASSIFICATION, not placement
Probe-confirmed (loop_sm and sm-auto-upgrade). The `loopRE` (175)
`^(.*)[...](.*)$` prefix is greedy and `.` matches commas/parens, so a `[...]` ANYWHERE in the
line (core production OR inside a `(... )` sub-decay) is seen. extract_process_type classifies
BOTH placements of a REAL `[QCD]` identically: `('NLO','all',['QCD'])` (probed both). So a real
perturbation bracket ALWAYS switches to **aMC@NLO** (do_add 215 / do_generate 271) regardless of
where the bracket sits — neither placement reaches `MadGraphCmd.do_add`.

Consequence: the "cunjunction" gate (`madgraph_interface.py:3283-3289`,
`"…cannot be used in cunjunction with decay chains."`) is in `MadGraphCmd.do_add`, reached ONLY
when the Switcher routes to the MadGraph interface — i.e. when the bracket classifies as
`type='tree'`. An **empty/whitespace-only bracket** `[]`/`[ ]` classifies `('tree',None,[])`
(orders empty) → switch to MadGraph (227/277) → 3283 fires. Probe-confirmed: `generate p p > t t~
[] , t > b w+` raises the cunjunction message. A real `[QCD]` core bracket does NOT.

Two perturbed-decay-chain cases, traced (instrumented, raw traceback):
- **Core-production bracket** `e+ e- > t t~ [QCD], t > b w+` (loop_sm or sm→auto-upgrade): switches
  to aMC@NLO; trace `master:278 do_generate → madgraph_interface:4820 do_generate → master:229
  do_add → amcatnlo_interface:527 do_add (proc_validity) → loop_interface:246` →
  **`InvalidCmd : ML5 cannot yet decay a core process including loop corrections.`** The decays are
  NOT perturbed (the CORE is), so amcatnlo:522 `are_decays_perturbed()` is False; `proc_validity`
  (amcatnlo:527 → loop_interface:245 `proc['decay_chains']` non-empty) fires FIRST.
- **In-decay bracket** `p p > t t~, (t > b w+ [QCD], w+ > l+ vl)`: switches to aMC@NLO; trace
  `master:229 do_add → amcatnlo_interface:523 do_add` → **`Decay processes cannot be perturbed`**
  (NO trailing period). Here amcatnlo:522 `are_decays_perturbed()` IS True (the SUB-decay carries
  the bracket), so 523 fires BEFORE reaching proc_validity (527).

So for a perturbed decay chain the user-visible message is amcatnlo_interface:523 (in-decay) or
loop_interface:247 (core-bracket) — NEVER `madgraph_interface:3296-3297`
(`"Decay processes cannot be perturbed."` WITH period) and NEVER `:3283-3289` ("cunjunction"),
because a REAL bracket never reaches MadGraphCmd.do_add. `:3296-3297` and `:3283-3289` are
shadowed live (reached only via a `type='tree'` route, i.e. empty bracket for 3283; 3296 is dead
for any real bracket since its branch is the `else` of the `[`/`]` test). The `:3283-3289`
"cunjunction" gate is owned by ma-process-syntax (MadGraphCmd.do_add tree path); the operative
NLO-path messages (523, 247) are reached via my Switcher route.

## Boundary
`extract_process_type` (the bracket->nlo_mode classification) and the bracket-presence routing
are my slice — they are bracket parsing. WHICH interface does what at generation/runtime
(FKSMultiProcess construction, MadLoop standalone, aMC@NLO launch) is amcatnlo/madloop/fks
slice. `change_principal_cmd` mechanics are the Switcher's own (lead routing pages names this the
"Switcher pre-dispatch layer"). `create_loop_induced` is treated on
`create-loop-induced-and-noborn-override.md`.
