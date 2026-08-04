---
description: FKSLeg data structure (extra keys), to_fks_leg model population, FKSLegList.sort "n j i" ordering algorithm, and sort_proc.
---

# FKS leg structure and the FKS leg-sort ordering

The FKS i/j conventions and the "Disordered numbers" guard rest on the FKSLeg
keys and the FKSLegList canonical sort. This page is the definition the other
pages assume.

## FKSLeg (fks_common.py:842-894)
`FKSLeg(MG.Leg)` adds eight keys beyond a plain Leg (`default_setup`, `:855-866`):
- `fks` (str): `'n'` normal, `'i'` radiated, `'j'` emitter/collinear-partner.
  Default `'n'`.
- `color` (int): color rep (3, -3, 8, 1). Default 0.
- `charge` (float): electric charge. Default 0.0.
- `massless` (bool): true if `mass=='zero'`. Default True.
- `spin` (int): 2S+1. Default 0.
- `is_tagged` (bool): tagged final state (semi-inclusive/UPC). Default False.
- `is_part` (bool): particle (not anti). Default True.
- `self_antipart` (bool): self-conjugate. Default False.

`filter` (`:875-894`) enforces types: `color`/`spin` int, `charge` float (NOT
int), the four booleans bool. Probed (v3.7.1): `filter('charge', 1)` raises
`PhysicsObjectError`, but `set('charge', 1)` SWALLOWS it — base PhysicsObject
`set` catches the filter exception, prints "Property charge cannot be changed",
returns `False`, and leaves the old value. So a bad-typed `set` fails silently
(value unchanged), it does not propagate.

## to_fks_leg / to_fks_legs (fks_common.py:761-782)
`to_fks_leg(leg, model)` reads the model `particle_dict` to populate
`color=part.get_color()`, `charge=part.get_charge()`,
`massless=(part['mass'].lower()=='zero')`, `spin=part.get('spin')`,
`is_part`, `self_antipart`. The values come from the MODEL, not the leg — so an
FKSLeg's color/charge/spin reflect the imported (possibly restricted) model.
`to_fks_legs` maps it over a leglist → FKSLegList. Inverse: `to_leg`/`to_legs`
(`:739-758`) strip back to plain Legs (keeping only id/number/state/from_group/
polarization).

## FKSLegList.sort (fks_common.py:793-839) — "madfks-optimal" order
Sorting is deterministic and load-bearing (the exporter/MadFKS Fortran assumes
this leg order). Algorithm:
1. **Initial legs first** (`:797-807`): 1 initial → kept; 2 initials → ordered by
   ascending `number` (reversed if out of order). >2 → `FKSProcessError('Too many
   initial legs')`. `<3` initials only; FKS never sorts a >2-initial process.
2. **Final legs: massive before massless** (`:811-814`).
3. Within each mass class, **ascending abs(spin)** (`:815-816`).
4. Within a spin group, when there are 2 initials (`:818-833`): legs whose
   `abs(id)` matches an initial parton's `abs(id)` come FIRST, each such group
   sorted by `id` descending (`reverse=True` → **particle before antiparticle**,
   and — comment `:825-826` — "fks partons as n j i"). Then the remaining legs,
   also `id`-descending.
5. With 1 initial (decay) the spin group is appended as-is (`:834-836`).

The phrase "n j i" means within the final radiated pair the normal/j/i ordering
falls out of the `id`-descending sort; `ij_final` also reverses so **j precedes
i** (see splittings-and-real-generation.md ij_final note).

`sort` mutates IN PLACE (`self[i]=l`, `:838-839`) — it does not return a new list.

## sort_proc (fks_common.py:724-736)
`sort_proc(process, pert)` rebuilds `process['legs']` as a sorted FKSLegList and
**renumbers** `leg['number']=n+1` (1..N) so the leglist is contiguous and
ordered. Also resets `process['legs_with_decays']=MG.LegList()` (`:734`, comment
notes this was needed to pass `test_check_ppzjj`). `FKSProcess.__init__` calls
`sort_proc` on the born before amplitude generation (`fks_base.py:614,620`).

## Why this matters / cautions
- `find_reals` raises `FKSProcessError('Disordered numbers of leglist')` if leg
  numbers aren't 1..N in order (guard `fks_base.py:891`, raise `:892`) — `sort_proc` is what
  guarantees that precondition. A hand-built leglist bypassing sort_proc can trip
  it.
- The "particle before antiparticle" (`id` descending) tie-break is why FKS leg
  order can differ from the user's process-syntax leg order; downstream Fortran
  indices follow the sorted order, not the typed order.
- `charge` must be float — `filter` raises on int, but `set` swallows that and
  silently leaves the value unchanged (probed above). `to_fks_leg` always feeds
  `get_charge()` (float), so this only bites hand-constructed FKSLegs, and bites
  silently (no exception from `set`).
