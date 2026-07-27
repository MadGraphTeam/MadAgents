---
description: The three color-string equivalence predicates (__eq__, is_similar, near_equivalent) built on to_canonical — what each compares and which coalescence step each drives across the basis/factor/matrix/color-flow machinery.
---

# Equivalence predicates: __eq__ vs is_similar vs near_equivalent

`$MADGRAPH_INSTALL/madgraph/core/color_algebra.py`. All three are
`ColorString` methods built on `to_canonical()`; the differences govern when two
color strings are treated as "the same" and merged. Getting which predicate is
in play wrong leads to wrong reasoning about why terms do/don't coalesce.

## to_canonical (`:1022-1054`) — the shared substrate
Index-renames a string's immutable form so the **first index encountered is 1,
the next new one 2, ...** (`:1036,1045-1047`), then **sorts** the object list
(`:1051`). So strings that differ only by index *names* (not relative positions)
share one canonical tuple. Caches into `self.canonical` (`:1032-1033,1053`) — set
once, so combining routines that mutate indices reset `canonical`/`immutable`
first (e.g. `ColorFactor.extend_str` `:1124-1126`). Returns `(canonical_tuple,
replaced_indices)`; callers compare only `[0]` or call `==` on the whole.

## The three predicates, strongest to weakest

| predicate | line | compares | ignores |
|-----------|------|----------|---------|
| `__eq__` | `:1056-1065` | coeff **and** Nc_power **and** is_imaginary **and** to_canonical | nothing |
| `is_similar` | `:1072-1078` | Nc_power, is_imaginary, to_canonical | **coeff** |
| `near_equivalent` | `:1080-1089` | per-object name + **sorted** indices | coeff, Nc_power, is_imaginary, index *order within an object* |

- **`__eq__`** is the strict full-equality. Used by `ColorFactor.full_simplify`
  (`:1148-1156`) as the fixed-point test (`result == ref`) — iteration stops only
  when nothing, including coefficients, changed.
- **`is_similar`** is "same structure, possibly different coefficient." It is the
  merge key for `ColorFactor.append_str` (`:1107-1114`): if an existing string
  `is_similar`, the new one is folded in via `ColorString.add` (`:875-878`),
  which simply **sums the coeffs** (`self.coeff = self.coeff + other.coeff`).
  This is how `simplify()` collapses like terms into one string per structure.
- **`near_equivalent`** (`:1080-1089`) is the loosest: it compares only object
  **names** and the **sorted** index multiset per object — it does NOT require
  matching index order, Nc_power, is_imaginary, or coeff. Used only in
  `get_color_flow_string` (`color_amp.py:423-425`) as the leading-N tie-break:
  if more than one string survives at max Nc_power and they are NOT all
  `near_equivalent`, it hard-errors "More than one color string with leading N
  coeff". So it answers "are these the same flow up to harmless reordering?"

## Why the ladder matters (coalescence map)
- **Basis keys** collide when `to_immutable` matches (sorted) — that is the
  raw-structure level, below even canonical (colorbasis-value-format page).
- **`ColorFactor.simplify`/`full_simplify`** merge by `is_similar` (sum coeffs),
  terminate by `__eq__`. So during simplification two strings with the same
  structure but opposite coeffs merge to coeff 0 and are dropped
  (`:1144-1146`, `coeff != 0` filter).
- **ColorMatrix product caching** (`color_amp.py:594-610`) keys on the canonical
  form of the concatenation — same canonical → reuse the simplified product.
- **Color-flow LC extraction** uses `near_equivalent` to permit a degenerate set
  of leading-N strings as long as they are reorderings of one another.

## Trap
Do not conflate `is_similar` with `__eq__`: `append_str` deliberately uses
`is_similar` (coeff-blind) so it CAN merge `2*X` and `3*X` into `5*X`. If it
used `__eq__` those would be distinct and never combine. Conversely the
`full_simplify` loop must use `__eq__` or it would "converge" while coefficients
are still changing.
