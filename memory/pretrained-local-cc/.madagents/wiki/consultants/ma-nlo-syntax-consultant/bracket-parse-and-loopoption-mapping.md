---
description: How the [...] perturbation-coupling bracket parses in extract_process; the option= -> LoopOption/HasBorn mapping; the parallel order-keyword path ([all]/[loonly] expansion); only mode; bracket pertOrders are NOT coupling-aliased; _valid_nlo_modes; where the result lands in ProcessDefinition.
---

# Bracket parse and LoopOption/HasBorn mapping

Parser lives in `extract_process`, `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`.
v3.7.1 / $MADGRAPH_INSTALL. Parse-probed (loop_sm); mapping matches source exactly.

## The regex (interface:4852-4854)
```
^(?P<proc>.+>.+)\s*\[\s*((?P<option>\w+)\s*\=)?\s*(?P<pertOrders>(\w+\s*)*)\s*\]\s*(?P<rest>.*)$
```
- `option` = optional keyword before `=` inside the bracket (e.g. `virt` in `[virt=QCD]`). Optional group.
- `pertOrders` = whitespace-separated order names inside the bracket (e.g. `QCD`, or `QCD QED`).
- A sanity pre-pass (interface:4836-4837) inserts spaces around `[` `]` `>` `$` `/` `,` `|` so `[QCD]` glued to the proc still matches.
- The bracket is stripped from `line` after the match: `line = group("proc") + group("rest")` (interface:4876-4877); order parsing continues on the remainder.

## option= -> LoopOption / HasBorn (interface:4856-4877)
Defaults before any bracket: `LoopOption='tree'`, `HasBorn=True` (interface:4857-4858).
If a bracket matched:
- **no `option=`** (bare `[QCD]`): `LoopOption='all'`, HasBorn stays `True` (interface:4873-4874).
- **`option` in `_valid_nlo_modes`**: `LoopOption=option` (interface:4863-4864), then two special overrides:
  - `option=='sqrvirt'` -> `LoopOption='virt'`, `HasBorn=False` (interface:4865-4867).
  - `option=='noborn'`  -> `LoopOption='noborn'`, `HasBorn=False` (interface:4868-4869).
  - (`real`, `virt`, `LOonly`, `only` keep HasBorn=True and LoopOption=option.)
- **`option` NOT in `_valid_nlo_modes`**: raises `InvalidCmd("NLO mode %s is not valid. Valid modes are %s.")` (interface:4870-4872).

`_valid_nlo_modes = ['all','real','virt','sqrvirt','tree','noborn','LOonly','only']` (interface:3035).
Note `'tree'` and `'all'` are in the list but are NOT the bare-bracket default path: bare `[…]` -> `'all'` via the else branch, not via the list. `'tree'` as an explicit option (`[tree=QED=2]`) is used only to set split_orders; perturbation_couplings_list is then emptied (interface:5278-5279).

### Help text under-documents the accepted modes (interface:640-646 `help_generate`, 685-691 `help_add`)
The user-facing `help generate`/`help add` lists ONLY `all=`, `virt=`, `real=` as the `<NLO_mode=>`
("'all=' by default if absent", 640). It does NOT mention `noborn=`, `sqrvirt=`, `LOonly=`, `only=`,
`tree=` — all of which ARE in `_valid_nlo_modes` (3035) and parse-accepted by the 4863 check. So the
help text is a STRICT SUBSET of what the parser accepts; do not infer the accepted-mode set from
`help`. Worse, the help advises loop-induced users ("i.e. loop-induced like g g > z, please use the
'virt=' NLO mode", 644-646) — but the actual v3.7.1 loop-induced path is `noborn=` /
NoBornException -> create_loop_induced (create-loop-induced page), and `virt=` gives a bare MadLoop
standalone with HasBorn=True (no real-emission, not an integrable loop-induced σ). The help is stale
relative to the parser; trust `_valid_nlo_modes` + the 4862-4877 remap, not the help string.

## Parse-probed mapping (model loop_sm) — value AT extract_process EXIT, NOT final
This table is the procdef state immediately after `extract_process` returns (stages 2-3 of the
lifecycle). For the `add`/`generate` flow routed through aMC@NLO, the amcatnlo `do_add` runs a
LATER pass that conditionally OVERWRITES `perturbation_couplings` (and bumps orders/squared_orders)
— see `amcatnlo-do_add-perturbation-couplings-overwrite.md`. Do NOT read this table as the final
displayed `perturbation_couplings`.
| input | NLO_mode | has_born | perturbation_couplings (at extract_process exit) |
|---|---|---|---|
| `[QCD]` | all | True | ['QCD'] |
| `[virt=QCD]` | virt | True | ['QCD'] |
| `[real=QCD]` | real | True | ['QCD'] |
| `[noborn=QCD]` | noborn | False | ['QCD'] |
| `[sqrvirt=QCD]` | virt | False | ['QCD'] |
| `[LOonly=QCD]` | LOonly | True | ['QCD'] |
Invalid: `[bogus=QCD]` -> in ISOLATION (direct extract_process) raises 4871-4872 `"NLO mode bogus is
not valid. Valid modes are ['all','real',...]"`. But END-TO-END `generate [bogus=QCD]` is rejected
EARLIER by the Switcher's own `_valid_nlo_modes` check (master_interface:268-270 do_generate / 211-213
do_add) with DIFFERENT wording: `"The NLO mode bogus is not valid. Please chose one among: all real
virt sqrvirt tree noborn LOonly only"` (probe-confirmed, loop_sm). So the 4871 message is
shadowed on the live path — the Switcher validity check fires before extract_process. (Same
isolation-vs-live-path split as the `[EW]`/`[NP]`/`[QED]` cases below — see switcher page for the
268-270 routing-validity guards.)

**Displayed value after a full `generate` (probe, loop_sm):** bare `[QCD]` in loop_sm DISPLAYS as
`[ all = QCD QED ]` (NOT `['QCD']`) after a full `generate`, because amcatnlo do_add (673) overwrites
`perturbation_couplings` to the model's `coupling_orders` (`['QCD','QED']`) when no explicit `orders`
were given and `nlo_mixed_expansion=True` (default). `[real=QCD]` likewise -> `[ real = QCD QED ]`.
Suppressed by ANY explicit amplitude order: `generate ... QED=0 [QCD]` keeps `[ all = QCD ]`. So the
table above is correct at the parser boundary but the amcatnlo path mutates it; route
final-`perturbation_couplings` questions to the amcatnlo-overwrite page.

## `@N` process-number tag coexists with the bracket (parsed FIRST, interface:4843-4848)
Inside `extract_process`, `@N` is stripped BEFORE the bracket regex runs:
```python
proc_number_pattern = re.compile(r"^(.+)@\s*(\d+)\s*(.*)$")   # 4844
proc_number_re = proc_number_pattern.match(line)
if proc_number_re:
    proc_number = int(proc_number_re.group(2))                # 4847
    line = proc_number_re.group(1)+ proc_number_re.group(3)   # 4848 — @N removed from line
```
So for `p p > t t~ [QCD] @0` the `@0` is consumed at 4848, leaving `p p > t t~ [QCD] `, and only THEN the bracket
regex (4852-4854) sees a clean bracket. `[QCD]` and `@N` on the same line are orthogonal — the bracket sets
LoopOption/HasBorn, `@N` sets the ProcessDefinition's process number (used to group multiplicities). No conflict,
no ordering restriction between them. (`@N` line-stripping also occurs in the pre-dispatch classifiers at 5486/5666
and the caller passes `proc_number=nb_proc` at 3310 — the value is settled multiple times, but the coexistence with
the bracket is guaranteed here at 4844.) `@N` VALUE semantics (process-number grouping) are process-syntax slice;
my slice fact is only the parse-ordering coexistence.

### FxFx multi-multiplicity: `[QCD]` on EVERY line, distinct `@N` per line — parse-probed (loop_sm)
Standard FxFx merged sample:
```
generate    p p > t t~   [QCD] @0
add process p p > t t~ j [QCD] @1
add process p p > t t~ j j [QCD] @2
```
Each multiplicity carries its OWN `[QCD]` bracket -> each becomes an independent full-NLO ProcessDefinition
(LoopOption='all', HasBorn=True: born+real+virt generated per line). Parse-probed the first two lines: both parse
cleanly, `@1` propagates to every subprocess of the 2nd multiplicity (`g g > t t~ g QCD^2=8 QED^2=0 @1`), 1st
multiplicity generated a full born+real+virtual set across its subprocesses (exact diagram counts are a one-off
probe artifact — derive per process, do not cache). `@0` is the default proc_number so it does
NOT print a suffix; `@1`+ do. The bracket is per-line: omitting `[QCD]` on one `add process` would make THAT
multiplicity tree-level (LoopOption='tree'), breaking the merge — the requirement that every FxFx multiplicity
bracket is a parse/semantics fact (each line is parsed independently by extract_process). Whether FxFx *merging*
(ickkw=3) actually requires uniform NLO across multiplicities is matching/amcatnlo slice — my slice confirms only
that each `[QCD]`-bracketed line independently yields a full-NLO procdef and that `[QCD] @N` coexist.

Squared-order note (my known trap): MG5 AUTO-sets born squared orders with the `<=` operator — consistent with only
`<=` surviving at NLO. The VALUE is NOT a reusable constant: it is the born-side amplitude order for that coupling
DOUBLED (`squared_orders[ord]=2*val`, amcatnlo:631-632), so it is process-dependent — derive it per born topology,
never reuse a number (e.g. `QCD^2<=4` for `t t~` follows from born QCD order 2; a different born gives a different
cap). The load-bearing fact is the OPERATOR (`<=`), not the integer. Standard FxFx needs no explicit squared-order
constraint; if a user added `QCD^2==N`/`>N` it would be rejected at NLO by amcatnlo:542 (see np-order page). Not a
blocker for the plain multi-jet FxFx setup.

## The order-keyword path — a SECOND, distinct entry (interface:5249-5253)
Separate from the `option=` keyword path above. After the bracket parse, the *pertOrders*
content (not `option=`) is inspected:
```python
if perturbation_couplings.lower() in ['all', 'loonly']:   # 5250
    if perturbation_couplings.lower() in ['loonly']:       # 5251
        LoopOption = 'LOonly'                              # 5252
    perturbation_couplings=' '.join(self._curr_model['perturbation_couplings'])  # 5253
```
- Fires only when the ENTIRE pertOrders string (lowercased) is exactly `all` or `loonly` — i.e. a single bare keyword inside the bracket, e.g. `[all]`, `[loonly]`, `[LOonly]`. A multi-token pertOrders like `[loonly QCD]` does NOT match (`.lower()=='loonly qcd'` not in the set) and falls through to the order-hierarchy sort, which then raises InvalidCmd on the bogus `loonly` "coupling".
- Effect: replaces pertOrders with the model's FULL `perturbation_couplings` list. For `loonly` it ALSO sets `LoopOption='LOonly'` (this is how a lowercase order-keyword sets LoopOption — distinct from the 4863 option= path).
- `[all]` does NOT set LoopOption here; LoopOption was already `'all'` from the bare-bracket else branch (4874) since `[all]` has no `option=`.

### Parse-probed (model loop_qcd_qed_sm, pert_couplings=['QCD','QED'])
| input | NLO_mode | pert |
|---|---|---|
| `[QCD]` (bare bracket) | all | ['QCD'] |
| `[all]` (order-keyword) | all | ['QCD','QED'] |
| `[QCD QED]` | all | ['QCD','QED'] |
| `[loonly]` / `[LOonly]` (pertOrder) | LOonly | ['QCD','QED'] (full set) |

**Bare `[QCD]` != `[all]`.** Both give NLO_mode='all', but `[all]` perturbs EVERY coupling
order the loop model supports while bare `[QCD]` perturbs only QCD. They coincide only in
single-perturbation models (e.g. loop_sm, where pert_couplings==['QCD']).

## `only` mode — parse-accepted, no special remap, no downstream handler
Parse-probed (loop_sm): `[only=QCD]` -> NLO_mode='only', has_born=True, pert=['QCD'].
Identity remap (4864, not sqrvirt/noborn), so HasBorn stays True. `'only'` is in `_valid_nlo_modes`
(3035) so it parses cleanly and stores NLO_mode='only'. BUT: no `'only'` branch exists in the
post-remap guards inside extract_process, nor in the core/export consumers checked
(base_objects.py, helas_objects.py, export_v4.py). It flows through every guard as a generic
non-tree LoopOption (trips the 4879 gauge guard, the 4983 constrained-order guard, the 5280
loop-model requirement — `only` is NOT in the ['real','LOonly'] exemption). What `only` actually
*does* at generation/export time is nlo-export/fks slice territory; from the parser's view it is
an accepted-but-unspecialized mode. Verify per-use before relying on it.

## Bracket pertOrders are NOT coupling-aliased (asymmetry with order constraints)
`coupling_alias` (interface:4891-4907, e.g. EW->QED when the model defines QED, or QED->EW when
it defines EW) is applied ONLY inside the order-constraint parsing loop (referenced 4918-4943).
It is NEVER applied to `perturbation_couplings`. The bracket's pertOrders are validated directly
against `model['perturbation_couplings']` (5286) and fed to the `order_hierarchy` sort (5266-5268)
with no aliasing.
Parse-probed (loop_qcd_qed_sm, coupling_orders=['QCD','QED'], so EW->QED alias is
active for constraints):
- `[QED]` -> OK, pert=['QED'].
- `[EW]`  -> rejected — `EW` is NOT aliased to `QED` for the bracket, even though `QED=2`
  *constraints* would accept `EW=2`. **WHICH guard fires depends on the path (same shadowing as `[NP]`/`[QED]` in SMEFTatNLO, np-order page):**
  - **End-to-end `generate u u~ > d d~ [EW]`** (probe-confirmed): bare `[EW]` routes nlo_mode=`'all'`
    -> aMC@NLO `do_add`, whose `validate_model(coupling_type=['EW'])` (amcatnlo:513) rejects FIRST
    with "The current model loop_qcd_qed_sm does not allow to generate loop corrections of type
    ['EW']." (loop_interface:325-326) then raises `InvalidCmd("The model ... cannot handle loop
    processes")` (354-356). **The user-visible message — `extract_process` is never reached.**
  - **`extract_process` in ISOLATION** (direct call): THEN it fails later, at the `order_hierarchy`
    sort, with "The loaded model does not defined a coupling order hierarchy for these couplings:
    ['EW']" (5269-5273). Probe-confirmed both ways. The "[EW] -> order_hierarchy
    sort 5269-5273" holds only for a DIRECT extract_process call; the live path is shadowed
    by validate_model (presence-vs-liveness). The order_hierarchy / 5286 guards are real but unreached
    on the normal `generate` path for a non-perturbable bracket order.
Boundary: the alias *definition/semantics* are coupling-order slice; the fact that it does NOT
reach bracket pertOrders is my slice. Use the model's exact `perturbation_couplings` names inside
`[...]`. `validate_model` semantics are nlo-model slice (cited here only for the live rejection path).

## Where it lands: ProcessDefinition (interface:5336-5352)
The parsed values are stored on the constructed `ProcessDefinition`:
- `'has_born': HasBorn`
- `'NLO_mode': LoopOption`
- `'perturbation_couplings': perturbation_couplings_list`
- `'split_orders': split_orders`
ProcessDefinition defaults (`$MADGRAPH_INSTALL/madgraph/core/base_objects.py`): `has_born=True` (2987), `NLO_mode='tree'` (2990).
`NLO_mode` is validated against the interface's `_valid_nlo_modes` (base_objects:3091-3094) — single-sourced list.

## sqrvirt vs virt vs noborn — the source-visible distinction
All three can share `LoopOption='virt'` or set HasBorn=False, but they are distinct states:
- `virt=`: NLO_mode='virt', has_born=True.
- `sqrvirt=`: NLO_mode='virt', has_born=**False** (loop-squared).
- `noborn=`: NLO_mode='noborn', has_born=False (loop-induced).
Rendering proof (base_objects:3351-3355 `nice_string`): a `^2` suffix is appended to the mode in the printed `[...]` exactly when `has_born==False and NLO_mode!='noborn'`. So `sqrvirt` prints as `[ virt^2= QCD ]` while `virt` prints `[ virt= QCD ]` and `noborn` prints `[ noborn= QCD ]` (no `^2`). This is how the two HasBorn=False modes stay distinguishable downstream.
