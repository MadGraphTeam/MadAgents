---
description: ColorString memoizes immutable/canonical (the substrate for ALL keying and equivalence); any in-place index/object mutation must invalidate them or operate on a fresh create_copy — names the two trap routines (replace_indices, complex_conjugate) and where a cache-staleness bug would live. complex_conjugate also shares object identity with its source and drops loop_Nc_power.
---

# ColorString immutable/canonical memoize-and-invalidate discipline

`$MADGRAPH_INSTALL/madgraph/core/color_algebra.py`. A cross-cutting principle the
keying/equivalence/simplification pages each touch but none names: **two
lazily-memoized caches on `ColorString` are the substrate for every comparison
and key in the whole color machinery, and any routine that mutates a string's
indices in place must invalidate them — else the next comparison/key is stale.**

## The two caches
- `canonical = None` and `immutable = None` are **class-level defaults**
  (`color_algebra.py:773-774`) — so `if self.immutable:` / `if self.canonical:`
  (`:900,1032`) are always safe even on a never-touched string; they read the
  falsy class default until an instance attribute is set.
- `to_immutable()` computes-once and stores `self.immutable` (`:900-912`).
- `to_canonical()` computes-once and stores `self.canonical` (`:1032-1054`).
- `ColorString.__init__` (`:776-789`) does NOT set them — relies on the class
  default. `create_copy` (`:930-942`) copies coeff/is_imaginary/Nc_power/
  loop_Nc_power but **NOT** immutable/canonical, so a copy starts cache-empty.

## Why it matters — they are the keying/equivalence substrate
- **Basis keys** are `to_immutable()` (colorbasis-value-format page;
  `color_amp.py:294`).
- **All three equivalence predicates** `__eq__`/`is_similar`/`near_equivalent`
  read `to_canonical()` (equivalence-predicates page; `:1056-1089`).
- **Simplification merge** (`ColorFactor.append_str`→`is_similar`) and
  **matrix product caching** (`color_amp.py:594-610`) both key on canonical.

So a stale `immutable`/`canonical` → wrong basis key or wrong merge, silently.

## The invalidation contract (who resets, who is safe by copy)
Two safe patterns; every in-place index mutation uses one of them:

1. **Explicit reset** — routines that mutate indices/objects on an
   already-live string null both caches:
   - `ColorString.product` (`:822-823`): resets both, then `self.extend(other)`.
   - `ColorString.order_summation` (`:1018`): rebuilds via `from_immutable`,
     nulls `self.immutable` (comment: "since the summation indices have been
     modified").
   - `ColorFactor.extend_str` (`:1125-1126`): nulls both before `append_str`.

2. **Operate on a fresh copy** — `replace_indices` is the trap: BOTH
   `ColorString.replace_indices` (`:923-928`) and `ColorObject.replace_indices`
   (`:73-82`) mutate indices but do **NOT** invalidate. They are safe only
   because every caller applies them to a `create_copy` whose caches are empty
   and uncomputed. `update_color_basis` (`color_amp.py:266-267,277`) does
   exactly this: `create_copy()` → `replace_indices(...)`, and only then reads
   `to_immutable` (`:294`) on the copy, so the cache is computed fresh post-mutation.

   `ColorString.complex_conjugate` (`:880-890`) is the **second trap-category
   member** — it mutates objects in place AND does not invalidate, with two extra
   sharp edges (probe-confirmed):
   - **In-place object mutation, shared identity.** It appends
     `col_obj.complex_conjugate()` for each object; `ColorObject.complex_conjugate`
     (`:66-71`) does `self.reverse()` **in place** and returns `self`. So the new
     (conjugate) string and the **original string share the same now-reversed
     ColorObject instances** (`cc[0] is cs[0]` → True). The original's scalar
     fields (coeff/Nc_power/is_imaginary) are unchanged — only its objects are
     reversed.
   - **No cache invalidation.** If `to_immutable()`/`to_canonical()` was called on
     the string BEFORE `complex_conjugate()`, the cache is **stale** afterward:
     probe showed `cs.immutable` still reads the pre-reverse `(('T',(1,2,100,101)),)`
     while the actual object is now `T(2,1,101,100)`. `complex_conjugate` does NOT
     null `immutable`/`canonical`, unlike `product`/`order_summation`/`extend_str`.
   - **Defused at the only live caller.** `ColorMatrix.create_new_entry`
     (`color_amp.py:643-647`) builds `col_str2` **fresh** via
     `from_immutable(struct2)` (empty caches, new objects) and only then calls
     `col_str2.complex_conjugate()`, feeding the result straight into `product`
     (which resets caches). So no staleness bug at runtime — but the trap is real
     for any *future* caller that conjugates an already-keyed/already-canonicalized
     string in place.
   - **CAUTION (cross-slice, loop):** `complex_conjugate` (`:883-884`) constructs
     the new string as `ColorString([], coeff, is_imaginary, Nc_power)` — only 4
     args, **omitting the 5th `__init__` param `loop_Nc_power`**, so the conjugate
     always has `loop_Nc_power=0` (probe-confirmed: original 1 → conjugate 0).
     Harmless at tree level (loop_Nc_power=0 everywhere) but a source-visible drop
     for loop color (madloop slice owns the consequence).

## Cases this catches beyond the instance pages
- Predicts **where a cache-staleness bug would live**: any *future* routine that
  calls `replace_indices` (or otherwise edits indices) on a string that has
  ALREADY had `to_immutable`/`to_canonical` called on it, then re-reads a key or
  compares it — without going through a `create_copy` or an explicit reset.
- Explains why `replace_indices` "gets away with" not resetting (caller
  discipline), unlike `product`/`order_summation`/`extend_str` which can be
  handed live strings.
- Tells you, when debugging a "two structures that should collide don't" or
  "two that shouldn't merge do", to check whether a mutation bypassed the
  invalidation contract — independent of which specific routine produced it.

Instance detail lives on: colorbasis-value-format (to_immutable keys),
equivalence-predicates (the three to_canonical predicates),
canonical-dict-and-simplification (create_copy + replace_indices in
update_color_basis, order_summation), colormatrix (canonical product caching).
