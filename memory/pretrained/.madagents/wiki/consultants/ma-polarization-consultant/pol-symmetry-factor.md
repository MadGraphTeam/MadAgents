---
description: How the polarization marker enters identical_particle_factor's identical-leg key — polarized/unpolarized (and disjoint-pol) same-PID legs become non-identical (no 1/n! factor); identical-pol legs stay identical — the source mechanism behind check_polarization's "symmetry factor" warning
---

# Polarization and the identical-particle symmetry factor

`$MADGRAPH_INSTALL/madgraph/core/base_objects.py`, `identical_particle_factor`
(method **3742-3755**, v3.7.1; 3757 is the next method `check_expansion_orders`).
Defined on `Process` (class at 2942, ends where `ProcessList` opens at 3804);
inherited by `ProcessDefinition` (3823). Computes the 1/n! denominator for
identical final-state particles.

## The key is polarization-aware (3750)
```
final_legs = [leg for leg in self.get_legs_with_decays() if leg.get('state') == True]  # 3746
identical_indices = collections.defaultdict(int)
for leg in final_legs:
    key = (leg.get('id'), tuple(leg.get('polarization')))   # 3750
    identical_indices[key] += 1
return reduce(lambda x,y: x*y, [math.factorial(val) for val in identical_indices.values()], 1)
```
Two final-state legs are counted as **identical** (and contribute a factorial to the
symmetry denominator) **only if BOTH their PID and their polarization list match**.
The polarization list is the *exact* list as parsed (e.g. `[1,-1]` for `{T}`, `[-1]`
for `{L}`, `[]` for unpolarized).

## Consequences (structurally confirmed, v3.7.1)
Built `Leg` objects directly and compared keys:
- `Z{T}` → key `(23, (1,-1))`; unpolarized `Z` → key `(23, ())` → **different keys**
  → NOT identical → **no 1/2! factor** applied between a polarized and an unpolarized
  Z, even though they are the same physical particle (PID 23).
- `Z{T}` and a second `Z{T}` → both `(23, (1,-1))` → **same key** → counted identical
  → 1/2! factor applied. (This is why `generate e+ e- > 2Z{T}` — which expands to
  `e+ e- > z{T} z{T}`, both legs carrying identical `[1,-1]` — parses cleanly AND
  gets the symmetry factor; the digit-duplication prefix `2` produces two legs with
  the *same* polarization list.)
- `Z{T}` and `Z{L}` (disjoint pols, same PID) → `(23,(1,-1))` vs `(23,(-1,))` →
  different keys → not identical → no factorial between them.

## Why this is the mechanism behind the check_polarization warning
`check_polarization` (3869-3900, see `check-polarization.md`) rejects the ambiguous
mix `p p > Z{T} Z` (same PID, one polarized + one unpolarized) and its critical
message warns: *"you can have issue with symmetry factor (we do not guarantee
[differential] cross-section)"*. The reason is exactly this key:

- A polarized leg `Z{T}` and an unpolarized leg `Z` on the same PID get **distinct
  keys** here, so MadGraph applies **no 1/2! symmetry factor** between them — but they
  are the same particle, so omitting the factor (or applying it, depending on how the
  user intended the unpolarized leg to be summed) gives an ambiguous / unreliable
  differential cross-section. That ambiguity is *why* the syntax is rejected by
  default, not merely a stylistic preference.

So `check_polarization` (gate 5, the prompt) and `identical_particle_factor` (the
symmetry math) are two faces of the same underlying issue: the polarization-aware
identity key does not know how to merge a polarized and an unpolarized copy of one PID.

## Caution / boundary
- The key uses `tuple(leg.get('polarization'))` verbatim — list **order** matters for
  tuple equality. The parser appends in a fixed order (`{T}`→`[1,-1]`, never
  `[-1,1]`), so two `{T}` legs always match; but a hand-built `[1,-1]` vs `[-1,1]`
  would NOT match as identical here. The reverse-render (`pol-allowed-values.md`)
  treats both `[-1,1]` and `[1,-1]` as `{T}`, so display can mask a key mismatch. Not
  reachable from the normal parser (which only emits `[1,-1]`), but a trap if pol
  lists are ever constructed by other code.
- `get_legs_with_decays()` is used, so decay-chain final legs participate; the
  decay-chain expansion itself is the process-syntax slice's territory.
- **Whether the applied (or omitted) symmetry factor is physically correct for a given
  polarized cross-section is amplitude/numerical-slice physics** — this page owns only
  the source fact that the identical-leg key is polarization-aware and what that does
  to the 1/n! count. Route cross-section-correctness questions there.
