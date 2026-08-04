---
description: ColorBasis dict structure — keys are immutable color structures, value is a list of per-diagram contribution tuples; field-by-field meaning and the docstring/code drift.
---

# ColorBasis dict structure (keys + value tuple)

`ColorBasis(dict)` — `$MADGRAPH_INSTALL/madgraph/core/color_amp.py:41`.

## Keys
Each key is an **immutable color-string representation** produced by
`ColorString.to_immutable()` (`color_algebra.py:892`):
`((name1, indices1), (name2, indices2), ...)` where `name` is the color-object
class name (`'T'`, `'Tr'`, `'f'`, `'K6'`, `'ColorOne'`, ...) and `indices` a
tuple of ints. The list is **sorted** (`color_algebra.py:909`) so equivalent
structures collide on the same key. An empty color string with non-zero coeff
becomes `(("ColorOne",()),)` (`color_algebra.py:906-907`).

**Key = structure ONLY; prefactors are dropped.** `to_immutable` stores just
`(class_name, tuple(indices))` per object (`color_algebra.py:903-904`) — it does
**NOT** encode `coeff`, `is_imaginary`, `Nc_power`, or `loop_Nc_power`. Those four
scalar prefactors live exclusively in the per-diagram value 6-tuple (below), not
in the key. The inverse `from_immutable` (`color_algebra.py:914-921`) therefore
rebuilds a coeff-1, Nc_power-0, real, loop_Nc_power-0 ColorString — the round-trip
**loses all prefactors by design**. This is why `ColorMatrix.create_new_entry`
(`color_amp.py:641-644`) can rebuild basis structures from keys for the product:
it only needs the structure; the magnitudes come from the stored value tuples.

## Value
The value is a **list** of contribution tuples (one per (diagram, color-chain)
that lands on this structure). Each tuple is built at `color_amp.py:297-302`:

```
(index, col_chain, col_str.coeff, col_str.is_imaginary, col_str.Nc_power, col_str.loop_Nc_power)
```

| field | meaning | source |
|-------|---------|--------|
| `index` | diagram index (passed into `update_color_basis`) | `color_amp.py:240,297` |
| `col_chain` | tuple of per-vertex color-part indices chosen in `colorize` | key of colorize_dict, `color_amp.py:247` |
| `coeff` | `fractions.Fraction` overall coefficient of this simplified string | `color_algebra.py:766` |
| `is_imaginary` | bool — string carries factor of i | `color_algebra.py:767` |
| `Nc_power` | integer power of Nc | `color_algebra.py:768` |
| `loop_Nc_power` | extra Nc power from closed-fermion-loop traces (0 at tree level) | `color_algebra.py:772` |

## Docstring drift (CAUTION)
The class docstring (`color_amp.py:42-48`) lists the value tuple as 5 fields
`(diag,(c1,c2,...),coeff,is_imaginary,Nc_power)` and omits `loop_Nc_power`. The
actual code appends a **6th field** `loop_Nc_power` (`color_amp.py:302`). Trust
the code, not the docstring. `__str__` (`color_amp.py:368`) prints only 5 of
the 6 fields (drops loop_Nc_power), which can mislead when eyeballing output.

## Append-not-overwrite
Multiple diagrams/chains contributing the same color structure are appended to
the same list (`color_amp.py:303-306`, try/except KeyError → append vs create).
So one key → many contributions is normal; the runtime sums them with the
helicity amplitudes (storage/integration is helas-amplitude slice territory).
