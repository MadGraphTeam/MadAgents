---
description: The simplify iteration engine — ColorString.simplify applies ONE rule per call (single-object before pair), ColorFactor.simplify/full_simplify drive the fixed point, and __copy__=create_copy (real copy, empty caches) is what the whole loop relies on.
---

# The simplify iteration engine (one-rule-per-call + fixed-point loop)

`$MADGRAPH_INSTALL/madgraph/core/color_algebra.py`. How a raw color string is
reduced to canonical simplified strings. The *which-predicate-merges-what* story
is on equivalence-predicates; the *basis-level caching* story is on
canonical-dict-and-simplification. This page is the reduction **engine** under
both.

## ColorString.simplify() applies exactly ONE rule, then returns (`:827-873`)
Two phases, both short-circuit on first hit:
1. **Single-object phase** (`:832-849`): loop objects, call `col_obj.simplify()`.
   First object that returns a non-empty `ColorFactor` wins: build a result
   `ColorFactor` by, for each string in that object's result, `copy.copy(self)`,
   `del` the simplified object (`:842`), `product(second_col_str)` the rule
   result in, `sort()`, append. **Return immediately** (`:849`).
2. **Pair phase** (`:852-871`, only if single phase found nothing): nested loop
   over object pairs `(i1, i1+1+i2)`, try `col_obj1.pair_simplify(col_obj2)` then
   the reverse `col_obj2.pair_simplify(col_obj1)` (`:855-858`). First hit:
   `copy.copy(self)`, `del first_col_str[i1]` then `del first_col_str[i1+i2]`
   (`:865-866`), `product`, `sort`, append; **return** (`:871`).
3. If nothing fired, return `None` (`:873`).

So one `simplify()` call = **at most one rewrite applied**. It does NOT iterate
to a fixed point itself.

CAUTION — the second `del` index (`:866`): `i2` is enumerated over the slice
`self[i1+1:]`, so the second object's absolute position is `i1+1+i2`. After the
first `del first_col_str[i1]` shifts everything down by one, its position
becomes `i1+i2` — which is what line 866 deletes. Correct only because the first
delete precedes it; reordering the two `del`s would corrupt the wrong object.

## ColorFactor.simplify() = one pass over all strings (`:1131-1146`)
For each string: `col_str.simplify()`. If it returned a result, `extend_str` it
(which `append_str`-merges by `is_similar`, summing coeffs); else `append_str`
the original. Then **filter out coeff==0 strings** (`:1145-1146`) — so a pair
that simplifies to opposite-coeff like terms cancels and drops here. One pass =
one rewrite layer across the whole factor.

## ColorFactor.full_simplify() = iterate to fixed point (`:1148-1156`)
```
result = copy.copy(self)
while True:
    ref = copy.copy(result)
    result = result.simplify()
    if result == ref: return result
```
The fixed-point test is `result == ref` on `ColorFactor` (a `list` subclass), so
element-wise `ColorString.__eq__` (strict: coeff + Nc_power + is_imaginary +
canonical — equivalence-predicates page). Iterates until a full pass changes
nothing, **including** coefficients. This is why `__eq__` (not `is_similar`) must
be the terminator: `is_similar` ignores coeff and would "converge" early.

## __copy__ = create_copy is load-bearing (`:88, :944, :1183`)
Every level overrides `copy.copy`:
- `ColorObject.__copy__ = create_copy` (`:84-88`): `globals()[cls.__name__](*self)`.
- `ColorString.__copy__ = create_copy` (`:930-944`): rebuilds the string,
  copying coeff/is_imaginary/Nc_power/loop_Nc_power but **NOT**
  immutable/canonical (the caches) — docstring says stdlib `copy.deepcopy` is
  buggy on the `array.array` subclasses (`:931-932`).
- `ColorFactor.__copy__ = create_copy` (`:1173-1183`): copies each string.

Three consequences the engine relies on:
1. `ColorString.simplify`'s `copy.copy(self)` (`:841,864`) is a real copy, so
   peeling off the simplified object (`del`) does not mutate the original string
   the loop is still iterating.
2. `full_simplify`'s `result`/`ref` are independent objects, so `result == ref`
   compares values, not an alias to itself (which would always be True and exit
   after one pass).
3. Each copy starts with **empty immutable/canonical caches** (create_copy skips
   them) — so the post-`product`/post-`del` re-keying recomputes fresh, never
   stale. This is the same invalidation contract as the
   colorstring-cache-invalidation page, viewed from the copy angle: copy = the
   safe-by-fresh-cache path.

## Why it matters
- Predicts cost: `full_simplify` is O(rewrites) passes, each O(objects^2) for the
  pair phase — relevant when reasoning about why large color bases are slow to
  build, and why `update_color_basis` caches by canonical form to avoid
  re-`full_simplify`ing structurally-identical strings.
- Tells you, if a simplification "didn't happen," to check whether the rule is a
  single-object vs pair rule (single always tried first and short-circuits) and
  whether an earlier single-object rule kept firing first.
