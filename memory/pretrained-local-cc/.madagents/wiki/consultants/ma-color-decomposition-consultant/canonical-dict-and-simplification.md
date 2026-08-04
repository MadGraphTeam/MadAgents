---
description: update_color_basis simplification reuse via _canonical_dict caching, the coeff-stripping/re-multiplying trick, the class-level vs instance-level _canonical_dict shadow, and order_summation for K6 sextets.
---

# update_color_basis: simplification + canonical caching

`$MADGRAPH_INSTALL/madgraph/core/color_amp.py:240-306`.

For each (color-chain, color-string) from a diagram's colorize dict:
1. `canonical_rep, rep_dict = col_str.to_canonical()` (`:249`) — index-renamed
   canonical form (`color_algebra.py:1022`) so structurally-identical strings
   (differing only by index names) share a cache slot.
2. **Cache hit** (`:253`): copy the stored simplified `ColorFactor`, replace
   indices back via `_invert_dict(rep_dict)` (`:277`), then multiply each
   string's coeff by `col_str.coeff` (`:280-281`) — because the cache stores the
   result with the original overall coeff **stripped** (see below). Then
   `.simplify().simplify()` twice (`:286`) — comment (`:282-285`) says up to two
   traces can appear at NLO so two passes canonicalize trace ordering.
3. **Cache miss** (`:254-271`): build `ColorFactor([col_str])`, `full_simplify()`
   (`:259`), `order_summation()` each string (`:263`), then store a copy with
   indices reverted (`:267`) AND the overall `col_str.coeff` **divided out**
   (`:269-270`) so the cache is coeff-agnostic.

Result strings appended to the basis as the 6-tuple (see
colorbasis-value-format page).

## CAUTION — class-level vs instance-level `_canonical_dict`
`_canonical_dict = {}` and `_list_color_dict = []` are declared at **class
level** (`color_amp.py:51,54`) but `__init__` (`:344,347`) ALSO assigns
fresh per-instance copies. So a normally-constructed `ColorBasis()` has its own
caches; the class-level dicts act as fallbacks/defaults. If you ever bypass
`__init__` you'd share the class dict across instances — a source-visible
footgun. `LoopColorBasis` inherits the same pattern.

## order_summation (`color_algebra.py:964-1020`)
Only fires if the string contains `K6`/`K6Bar` (sextet Clebsch-Gordan)
(`:986-991`, early return otherwise). When present: moves K6/K6Bar to the end,
reverses the order of the other factors, renames summation indices increasing
from -10000, and canonicalizes K6(a,i,j)→K6(a,j,i) if j>i. Comment (`:967-976`):
needed so equivalent sextet strings are recognized — otherwise the color basis
is **degenerate** (same physics, multiple keys). Pure-triplet/octet processes
never trigger it.
