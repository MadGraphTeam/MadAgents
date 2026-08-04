---
description: ColorMatrix — cross-product matrix of color structures (struct1 x conj(struct2)), build_matrix symmetry optimization, fixed-Nc and inverted matrices, fix_summed_indices, Nc_power_min/max truncation, line denominators/numerators for Fortran output.
---

# ColorMatrix

`$MADGRAPH_INSTALL/madgraph/core/color_amp.py:537-762`.

`ColorMatrix(dict)`: keys `(i1, i2)` index color-basis structures; values are
simplified `ColorFactor`s = the inter-structure factor. Holds two companion
dicts: `col_matrix_fixed_Nc` (Nc substituted, default Nc=3) and
`inverted_col_matrix` (keyed by the fixed-Nc value → list of (i1,i2)).

## __init__ (`:549-568`)
One or two bases. If only one given, `_col_basis2 = _col_basis1` and the matrix
is built `is_symmetric=True` (upper triangle only). Options: `Nc=3`,
`Nc_power_min`, `Nc_power_max`. CAUTION (`:553-555` docstring): the min/max Nc
power constraint is applied **only at the end** — it does NOT speed up the
calculation; it is a Leading-Color *truncation of the stored result*, not an
optimization. (When/whether LC truncation is activated at run time is a
numerical/madloop-slice question.)

## build_matrix (`:570-631`)
Double loop over sorted basis keys. Per (struct1, struct2):
- `fix_summed_indices(struct1, struct2)` (`:591`, classmethod `:713-748`):
  renames struct2's summed (negative, count==2) indices to avoid collision with
  struct1's indices — assumes internal summed indices are negative.
- canonicalizes the concatenation and **caches** per canonical_entry
  (`:594-610`) so identical products are computed once.
- `create_new_entry` (`:633-675`): `col_str.product(col_str2.complex_conjugate())`
  (`:647`) — the matrix is struct1 times the **complex conjugate** of struct2 —
  then `ColorFactor([...]).full_simplify()` (`:661-662`). `__debug__` assert
  (`:648-656`) checks no index appears >2 times. Then Nc_power_min/max filtering
  (`:665-670`) and `result.set_Nc(Nc)` (`:673`) for the fixed-Nc value.
- symmetric: stores both (i1,i2) and (i2,i1) (`:613-631`).

## Fortran-output helpers
- `get_line_denominators` (`:693-703`): per-row LCM of the fixed-Nc fraction
  denominators (uses `lcmm`/`lcm`, `:750-761`).
- `get_line_numerators` (`:705-711`): numerators scaled to a common denominator.
  These produce the integer color-matrix data written into `color.inc`/matrix
  Fortran (output-slice territory; this slice produces the numbers).
- `__str__` (`:677-691`): prints only the **real part** ([0]) of the fixed-Nc
  matrix as fractions.

## Integer CF + DENOM rendered into matrix.f (seam with output)
`col_matrix_fixed_Nc[(i1,i2)][0]` is a Python `Fraction` (real part of the
fixed-Nc factor) with `.numerator`/`.denominator`. This slice OWNS the
rational→integer clearing; the export writes the DATA statements.
- `get_line_denominators` (`color_amp.py:693-703`): per-row LCM of the row's
  Fraction denominators.
- `get_line_numerators(i, den)` (`:705-711`): row numerators rescaled to common
  `den` (`num*den/den_i`).
- **DENOM selection** (`iolibs/export_v4.py:1259`, `get_color_data_lines`):
  `denominator = max(get_line_denominators())` — a single INTEGER scalar for the
  whole matrix, the common denominator that clears every rational CF entry. So
  the true interference coefficient is `CF/DENOM`. This is a color-algebra
  common denominator, **NOT** initial-state color averaging — that averaging is
  the separate `get_den_factor_line`/`get_denominator_factor()` (IDEN),
  helas-amplitude/physics territory.
- **Symmetric packing + off-diagonal ×2** (`export_v4.py:1265-1282`): for the
  self-product (symmetric) case only the upper triangle is emitted (`min_k=index`),
  and every off-diagonal numerator is doubled at write time:
  `(1 if k==index and pos==0 else 2)*int(i)` (`:1281`). The doubling lets the
  matrix.f loop count each off-diagonal once yet reproduce the full symmetric
  double sum. Asymmetric (two distinct bases) writes the full row, no doubling.
- **matrix.f consumption (helas-amplitude slice owns this)**: v3.7.1 emits a
  packed loop, `CF(NCOLOR*(NCOLOR+1)/2)`:
  `DO I; DO J=I,NCOLOR: ZTEMP += CF(CF_INDEX++)*JAMP(J); MATRIX += REAL(ZTEMP*DCONJG(JAMP(I))); MATRIX/=DENOM`.
  Not the older full `sum_{i,j} CF(j,i)*JAMP(j)*conjg(JAMP(i))` double loop.

### Worked example — ONE topology, derive per process for anything else: `g g > t t~`
Do NOT reuse these numbers as a class recipe. The color-flow count (matrix
dimension), the CF numerators, and DENOM are ALL process-specific — derive each
per process via the recipe above: basis size from the external color content
(colorbasis-value-format / colorize page), `DENOM = max` row-LCM
(`get_line_denominators`), off-diag ×2 only in the symmetric self-product case.
Worked here for `g g > t t~` (Nc=3): 2 color flows → 2×2
`[[16/3,-2/3],[-2/3,16/3]]` (diag `<C|C>=C_F·4·2/2=16/3`; off
`Tr(T^aT^bT^aT^b)=-(N^2-1)/(4N)=-2/3`). Row-LCM denominators `{3,3}` → `DENOM=3`.
Numerators row0 `[16,-2]`, off-diag ×2 → `CF=[16,-4,16]`. Generated DATA:
`Denom/3/`, `(CF(I),I=1,2)/16,-4/`, `(CF(I),I=3,3)/16/`. DENOM is the rational
common denominator, not initial-state color averaging.

## set_Nc (`color_algebra.py:946-963, 1158-1163`)
`ColorString.set_Nc` raises if non-trivial color objects remain (`:952-953`);
returns `(coeff*Nc^power, is_imaginary)`. `ColorFactor.set_Nc` returns a tuple
`(real_sum, imaginary_sum)` summing strings by `is_imaginary`.
