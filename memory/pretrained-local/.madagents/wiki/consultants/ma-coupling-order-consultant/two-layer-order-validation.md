---
description: Coupling-order constraints are validated in two layers — parse-time InvalidCmd inside extract_process (Layer A) and post-build MadGraph5Error in the do_add/do_generate caller (Layer B); auto-squared-order propagation decides which layer catches a given input.
---

# Two-layer validation of coupling-order constraints

The three dicts this slice fills (`orders`, `squared_orders`, `constrained_orders`)
are checked in TWO distinct layers, with different owners, different exception
classes, and different scan logic. A constraint can be accepted at parse time and
still die later — or die at parse and never reach the second layer. This page
names the principle that ties the scattered checks together; the deeper trap is
that *which layer fires depends on the auto-squared-order propagation*, so the
same "two negative orders" intent can hit either layer depending on the operator.

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` unless noted.

## Layer A — parse-time, inside `extract_process`, raises `InvalidCmd`
Fires while the `while order_re` loop / assembly runs (`4914-5332`):
- Squared-order type not in `_valid_sqso_types` (`4933-4935`).
- Amplitude-order type not in `_valid_amp_so_types` (`4945-4947`).
- `=` -> `<=` reinterpretation warnings (`4936-4939` sqso, `4951-4953` amp) —
  see `equals-interpretation-and-strict-equality.md`.
- `constrained_orders` (`==`/`>`) at non-tree LoopOption (`4983-4985`):
  `"Amplitude order constraints (for not LO processes) can only be of type <=, ..."`.
- At most ONE negative SQUARED-order value (`5330-5332`):
  `"At most one negative squared order constraint can be specified."` — counts
  `sqorders_values` ONLY (the squared dict), not amplitude `orders`.

## Layer B — post-build, in the `do_add`/`do_generate` caller, raises `MadGraph5Error`
Runs AFTER `extract_process` returns the ProcessDefinition, scanning the dicts
this slice filled:
- Combined single-negative ceiling (`do_add 3342-3346`, `do_generate 5414-5418`):
  scans `orders` values AND `squared_orders` values TOGETHER; >1 negative ->
  `"Negative coupling order constraints can only be given on one type of coupling
  and either on squared orders or amplitude orders, not both."`
- Decay squared-order ban (`do_add 3301-3304`): any squared order in a decay
  process -> `"Decay processes cannot specify squared orders constraints."`
- Decay negative-order ban (`3305-3307`) via
  `ProcessDefinition.are_negative_orders_present()`
  (`$MADGRAPH_INSTALL/madgraph/core/base_objects.py 3554-3566`) — scans
  `orders`+`squared_orders` and recurses into decay_chains.
- 1->N interference-with-decay warning (`3348`, not an error): single initial
  state + non-empty squared_orders -> "interference term with decay not 100% validated".

## The non-obvious interaction: propagation decides the layer (PROBE-CONFIRMED)
An amplitude `==`/`>` AUTO-SPAWNS a doubled squared order (`4957-4958`, `4964-4965`;
see `equals-interpretation-and-strict-equality.md`). So a negative amplitude `==`/`>`
ALSO becomes a negative squared order, pushing it into Layer A's squared-only
counter. A negative amplitude `=`/`<=` does NOT spawn a squared order, so it stays
orders-only and only Layer B's combined counter can catch it. Probes (sm / loop_sm,
v3.7.1), each verbatim:
- `generate p p > t t~ QED^2==-1 QCD^2==-1` (two squared negatives)
  -> Layer A `InvalidCmd: At most one negative squared order constraint can be specified.`
- `generate p p > t t~ QED==-1 QCD^2==-1` (amplitude `==` spawns QED^2=-2, so two
  squared negatives) -> SAME Layer A `InvalidCmd` (NOT the "...not both" message —
  the `==` propagation moved it into the squared counter).
- `generate p p > t t~ QED=-1 QCD^2==-1` (amplitude `=` stays orders-only; one
  squared negative) -> Layer A passes (1 squared), Layer B fires:
  `MadGraph5Error: Negative coupling order constraints can only be given on one
  type of coupling and either on squared orders or amplitude orders, not both.`
- `generate p p > t t~ QED==2 [QCD]` -> Layer A
  `InvalidCmd: Amplitude order constraints (for not LO processes) can only be of type <=, not '=='.`

## Boundary
Layer A sites are THIS slice (inside extract_process). Layer B enforcement SITES
live in `do_add`/`do_generate` and decay-chain handling — caller/decay-chain
territory — but they scan the dicts THIS slice produces, so the *origin* of every
value is here. When a constraint is "accepted but later rejected," check which
layer: if it survived parse, the failing check is Layer B downstream.

## Why this is a generalization, not a restatement
`negative-order-values.md` names the two-layer split for NEGATIVES only.
The `=`->`<=`, type-validation, and LO-only checks appear as isolated single
lines in `order-parsing-overview.md` / `equals-interpretation-and-strict-equality.md`
with no statement that they are the parse-time half of a two-layer scheme, nor
that decay bans are the same scheme re-applied downstream. The propagation-decides-
the-layer interaction appears in NO existing page and is the load-bearing trap.
