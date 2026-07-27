---
description: The constrained_orders (==/>) dict this slice produces is consumed downstream as a per-diagram amplitude FILTER (not a generation-time bound); why == and > also keep an orders[name] entry, and the boundary to diagram-enumeration.
---

# `constrained_orders` consumption — a post-generation diagram filter

THIS slice produces `constrained_orders` (`{name: (value, operator)}`, operator
`'=='` or `'>'`) in `extract_process` (`madgraph_interface.py 4955-4965`). This
page documents the ONE step downstream where that dict is consumed, because the
consumption semantics explain a parse-side decision that otherwise looks
arbitrary, and because the timing (filter, not generation bound) is a non-obvious
trap. The consumption SITE is diagram-enumeration territory; the boundary is
named at the end.

## The consumer (`$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py 856-865`)
`apply_squared_order_constraints(self, diag_list)` runs AFTER the diagram list is
built (`808: res = self.apply_squared_order_constraints(res)`). Its FIRST action,
before any squared-order work:
```python
for name, (value, operator) in self['process'].get('constrained_orders').items():
    res.filter_constrained_orders(name, value, operator)
```
So every `==`/`>` amplitude constraint is applied as a filtering pass over the
already-generated diagrams.

## The filter (`$MADGRAPH_INSTALL/madgraph/core/base_objects.py 2897-2910`)
`filter_constrained_orders(self, order, value, operator)` MODIFIES the diagram
list in place, keeping only diagrams that satisfy the condition on their
AMPLITUDE-level `orders`:
```python
for tested_diag in self:
    if operator == '==':
        if tested_diag['orders'][order] == value:   # keep exact match
            new.append(tested_diag)
    elif operator == '>':
        if tested_diag['orders'][order] > value:     # keep strictly-greater
            new.append(tested_diag)
self[:] = new
```
- `==` keeps diagrams whose `orders[order]` equals `value` exactly.
- `>` keeps diagrams whose `orders[order]` is strictly greater than `value`.
- It reads `tested_diag['orders'][order]` UNCONDITIONALLY (no `.get`) — the order
  key must be present on every diagram, or this raises `KeyError`. (In practice
  diagrams carry every coupling order; relevant only as a hazard pointer.)

## Why the parse keeps `orders[name]` for `==` and `>` (the link back to this slice)
This is the payoff: in `extract_process` the `==` branch ALSO sets
`orders[name]=value` (`4959-4960`, the deliberately-kept `if True:` branch), and
`>` records into `constrained_orders` only. The filter above reads
`tested_diag['orders'][order]` — i.e. it compares against the per-diagram
amplitude order, NOT against the process-level `orders[name]` bound. The
process-level `orders[name]=value` set by the `==` branch is a SEPARATE
generation-level `<=`-style bound that limits which diagrams get generated in the
first place; the `constrained_orders` filter then prunes that set down to the
exact/`>`-satisfying subset. So `QED==2` acts in two stages:
1. `orders['QED']=2` bounds generation (`<=2`-style ceiling on the amplitude).
2. `constrained_orders['QED']=(2,'==')` filters the result to exactly `==2`.
`>` skips stage 1 (no `orders[name]` set), so it relies purely on the
post-generation filter to keep `orders[order]>value` diagrams.

## The non-obvious trap: `==`/`>` are FILTERS, not generation constraints
A user writing `QED==2` might expect the generator to only ever build `QED=2`
diagrams. Source shows otherwise: diagrams are generated under the (`==`-only)
`<=` ceiling, THEN filtered diagram-by-diagram. For `>` there is no ceiling at
all — generation proceeds broadly and the filter does all the work. This is why
`==`/`>` are LO/tree-only (`extract_process 4983-4985`): the per-diagram
amplitude-order filter only makes sense on tree diagrams where each diagram has a
well-defined coupling-order tuple. (The LO-only gate is THIS slice; the *reason*
it must be tree-only is this consumption model.)

## Iteration note (squared side, adjacent)
After the `constrained_orders` loop, `apply_squared_order_constraints` ITERATES
the squared-order filtering (`870-881`) because applying an `==` squared
constraint on one coupling can change what passes on another; the
`constrained_orders` loop above is explicitly NOT iterated (comment `862-863`:
"No need to iterate on this one"). That asymmetry is squared-order /
diagram-enumeration territory; recorded here only as the surrounding context.

## Boundary
THIS slice ends at producing `constrained_orders` (and the companion
`orders[name]` for `==`) in `extract_process`. The filter at
`base_objects.py 2897-2910` and its driver at `diagram_generation.py 856-865`
are diagram-enumeration slice territory — route questions about WHEN in
generation the filter fires, the squared-order iteration, or negative-squared
handling there. What this page adds to THIS slice: the consumption contract that
explains why the `==` branch keeps both a `constrained_orders` tuple and an
`orders[name]` entry, and the fact that `==`/`>` are post-generation diagram
filters rather than generation-time bounds.
