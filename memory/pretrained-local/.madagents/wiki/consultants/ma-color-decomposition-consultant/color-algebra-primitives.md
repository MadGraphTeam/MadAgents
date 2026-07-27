---
description: color_algebra.py primitive classes (ColorObject base, T/Tr/f/d, Epsilon/EpsilonBar, sextet K6/K6Bar/T6, ColorOne) and the container classes ColorString/ColorFactor — what each represents and its simplify/pair_simplify rules; incl. sextet use_symmetry dead-code and the T6.new_index -10000 global counter.
---

# color_algebra.py primitives

`$MADGRAPH_INSTALL/madgraph/core/color_algebra.py`. SU(N) color algebra.
Convention: T_f = 1/2 (per 0909.2666), so f = -2i(Tr(abc)-Tr(cba)) and
delta8 = 2 Tr (`color_algebra.py:563-567`).

## ColorObject base (`:32-89`)
Subclass of `array.array('i', ...)` (integer index array). Methods all
subclasses share: `simplify()` (single-object rules, default None),
`pair_simplify(other)` (two-object contraction, default None),
`complex_conjugate()` (default reverses index order), `replace_indices`,
`create_copy`. New color objects MUST inherit this (`:33-34`).

## Generators / traces
- **T** (`:212-299`): fundamental generator chain; last two indices are the
  open (anti)triplet indices `(i,j)`. Rules: `T(a,b,c,i,i)=Tr(a,b,c)` (`:227`);
  `T...T` index contraction `T(a,i,j)T(b,j,k)=T(a,b,i,k)` (`:256-261`); Fierz
  `T(a,x,b,...)T(c,x,d,...)` (`:263-287`). Conjugate reverses both groups
  `T(a,b,c,i,j)*=T(c,b,a,j,i)` (`:289-298`). A 2-index `T(i,j)` is a triplet
  delta3.
- **Tr** (`:94-173`): closed trace. `Tr()=Nc` (`:108-111`), `Tr(a)=0`
  (`:102-105`), cyclic-orders from min index (`:114-117`), and the
  `Tr(a,x,b,x,c)` and Tr-Tr / Tr-T Fierz pair rules (`:119-171`).
- **f** (`:304-333`): structure constant, exactly 3 indices; simplify →
  `-2I Tr(a,b,c)+2I Tr(c,b,a)` (`:318-333`).
- **d** (`:338-353`): subclass of f; simplify → `2 Tr(a,b,c)+2 Tr(c,b,a)`.

## Epsilon / EpsilonBar (`:359-559`)
Totally antisymmetric 3-index tensors over triplets / antitriplets. Have
analytic-rule flags `rule_eps_T`, `rule_eps_aeps_sum`, `rule_eps_aeps_nosum`
(`:362-365`); the nosum variant is "not compatible with LC rules" and is
toggled off via `TMP_variable` during color-flow extraction
(`color_amp.py:409`). `simplify` antisymmetrizes by sorting indices with parity
(`:392-404`, `perm_parity` `:373-390`). `pair_simplify` does eps*T,
eps*epsbar → delta products. Conjugation swaps Epsilon↔EpsilonBar (`:512-516`,
`:555-559`).

## Color sextet (`:569-755`)
- **K6 / K6Bar** (`:569-682`): Clebsch-Gordan mapping triplet pair ↔ sextet,
  3 indices `(m,i,j)`. `assert len(args)==3` in `__init__` (`:579,655`).
  `K6 K6Bar` pair rules (`:591-636`): same first index → `1/2(T T + T T)`
  triplet split; index-pair matched → `delta6(m,n)` = `T6(m,n)`; and
  `delta3·K6`/`delta3·K6Bar` contractions absorb a 2-index `T` into the K6.
- **CAUTION — `use_symmetry` is dead at runtime.** Both `K6.use_symmetry` and
  `K6Bar.use_symmetry` default `False` (`:573,649`) and are **never set True
  anywhere** (only refs are the def + the `if self.use_symmetry` guard). So the
  per-object `simplify` rule "K6(m,i,j)=K6(m,j,i) if j>i" (`:581-586,657-662`)
  ALWAYS returns `None` — it is dead code. The sextet index-order
  canonicalization that actually fires is in `ColorString.order_summation`
  (`color_algebra.py:1011-1013`), not here. So do NOT expect a lone `K6.simplify()`
  to reorder indices; only the basis-level `order_summation` does.
- **T6** (`:684-755`): sextet trace/delta. `assert 2<=len<=3` (`:693`).
  `delta6(i,i)` (2 equal idx) → `1/2 Nc^2 + 1/2 Nc` = `1/2 Nc(Nc+1)`
  (`:700-708`); `T6(a,i,j)=2 K6 T K6Bar` (`:710-724`); 2-index `T6` is delta6
  with `pair_simplify` rules `delta6·delta6`, `delta6·K6`, `delta6·K6Bar`
  (`:726-755`).
- **CAUTION — `T6.new_index` is a class-level mutable counter** (`:687`, starts
  `-10000`). `T6.simplify`'s `T6→K6 T K6Bar` expansion mints 3 fresh summed
  indices `ii,jj,kk` from it and does `T6.new_index -= 3` (`:713-718`) ON THE
  CLASS. So sextet-internal summed indices land in the **-10000 band** — which
  is exactly the band `order_summation` renames (`<= -10000`,
  `color_algebra.py:1002`); the two are designed to match. The counter never
  resets between diagrams/builds (monotonically decreases over a session); it's
  a global-state footgun like the `_canonical_dict` class shadow, but harmless
  for correctness because `order_summation` renumbers. Unit tests reset it
  explicitly (`tests/unit_tests/core/test_color_algebra.py:274`), evidence it's
  stateful.
- **ColorOne** (`:178-206`): the color identity (no indices); simplify →
  coeff-1 empty string.

## Containers
- **ColorString** (`:760-1089`): list of ColorObjects (implicit product) +
  `coeff` (Fraction), `is_imaginary`, `Nc_power`, `loop_Nc_power`. Key methods:
  `product` (`:807-825`, multiplies coeffs, ADDS Nc_powers, handles i*i=-1),
  `simplify` (single then pair rules, `:827-873`), `to_immutable`/`from_immutable`
  (basis keys, `:892-921`), `to_canonical` (index-renamed compare form,
  `:1022-1054`), `set_Nc`, `complex_conjugate`, `order_summation`. `__eq__`
  compares coeff+Nc_power+is_imaginary+canonical (`:1056-1065`).
- **ColorFactor** (`:1094-1183`): list of ColorStrings (implicit SUM).
  `simplify` (one pass + merge similar via `append_str`, `:1131-1146`),
  `full_simplify` (iterate to fixed point, `:1148-1156`), `set_Nc` →
  (real, imag) tuple (`:1158-1163`).
