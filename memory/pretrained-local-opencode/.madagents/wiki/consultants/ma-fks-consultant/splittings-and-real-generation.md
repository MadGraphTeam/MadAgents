---
description: find_splittings/split_leg/insert_legs and FKSProcess.find_reals — enumerating real-emission configurations, ij assignment, UPC/lepton/tag carve-outs.
---

# Splitting enumeration and real-emission generation

## find_splittings (fks_common.py:255)
Enumerates valid soft splittings of one external `leg`. Steps:
- Only if `leg['id'] in dict['pert_particles']` (`:265`).
- Loops `dict['interactions']`; pops the (anti)particle of the leg from a copy of
  the interaction's particles; requires ≥1 remaining `soft_particle` (`nsoft>=1`,
  `:282`).
- Calls `split_leg` to build daughter legs, then applies carve-outs:
  - **Tagged final state** (`:286-290`): if leg is tagged and final, the daughters
    must include the same id as the leg (same-PDG check) else skip.
  - **UPC** (`:292-298`): a tagged *initial* non-photon leg may not produce a
    final-state photon daughter — i.e. only `γ → f f̄` initial splitting survives.
  - **init-lepton flag** (`:303-304`): if `include_init_leptons` is False, skip
    splittings producing an initial-state lepton.

## split_leg (fks_common.py:338)
- **Final-state** leg (`:344`): exactly one splitting; daughters get the
  interaction's other particles; `ij_final` assigns i/j.
- **Initial-state** leg (`:352`): two splittings if the two daughter partons
  differ, else one. The initial daughter keeps `fks:'j'`, the radiated one
  `fks:'i'` (anti-pdg of the other parton).

## ij_final (fks_common.py:375)
Assigns i/j to a final-state pair. The radiated **i** is the massless
self-conjugate boson, OR (anti-particle when partner is particle and combined
spin is even). **NOTE: convention is j before i** — pair is reversed so j is first.

## insert_legs (fks_common.py:395)
Builds the real leglist: removes `ij`, inserts leg `j` (split[0]) in its place,
inserts `i` (split[1]) at the end of the group of legs sharing i's color/charge
representation. Color key is `'color'` for QCD, `'charge'` for QED (`:400-405`).
The deepcopy at `:407` is flagged "crucial".

## FKSProcess.find_reals (fks_base.py:868)
Builds `self.reals[i]` = list of real-emission dicts from splitting born leg i.
Key gates:
- If `pert_orders` empty: uses `model['coupling_orders']` when born has no
  `orders`, else born `perturbation_couplings` (`:884-888`).
- **2→1 processes** (`len(leglist)==3`, non-decay): final-state legs skipped —
  only initial-state singularities mapped, because final-state mapping preserves
  shat which is impossible in 2→1 (`:910-914`).
- **Decay processes** (one initial leg): no initial-state splittings (`:917`).
- **init-lepton**: if `init_lep_split` False and ≥1 initial lepton, only split
  initial leptons (`:921-923`).
- **UPC** (`ninit_tag>0`): forbids final-state splitting unless both initials are
  photons; forbids initial-photon splitting; forbids initial-fermion QCD
  splitting (`:927-929`).
- Each split records `extra_mothers` per pert order via `find_mothers`
  (`:937-939`) — used for g/γ → q q̄ counterterm handling in generate_reals.

## Order/mother helpers (fks_common.py)
- **find_orders(amp)** (`:239`): max coupling order per coupling across the amp's
  diagrams, but only counts an order if `value!=0` OR it appears in
  `process['orders']`. Used in `generate_virtuals` (`fks_base.py:354`) and the
  async path (`fks_helas_objects.py:298`) to set per-coupling max loop orders when
  `nlo_mixed_expansion` is False.
- **find_mothers(leg1, leg2, model, pert, mom_mass)** (`:309`): for each base
  interaction containing leg1,leg2 (anti-pdg for final state, pdg for initial),
  returns the third particle pdg; filtered to `mom_mass` if given. Feeds
  `extra_mothers` in `find_reals` (`fks_base.py:938`) → the g/γ→qq̄ counterterm
  machinery (extra-counterterm-and-dedup.md).
- **get_qed_qcd_orders_from_weighted(nexternal, hierarchy, weighted)** (`:53`):
  inverts the weighted-order count to (QED,QCD) using `n_vertices=nexternal-2` and
  `weighted=qed_w*QED+qcd_w*QCD`. Pure arithmetic helper; not called within fks/
  (consumed externally by the order bookkeeping).

## Cautions
- `find_reals` raises `FKSProcessError('Disordered numbers of leglist')` (guard
  `:891`, raise `:892`)
  if leg `number` is not 1..N in order — the born must already be sorted (this is
  what `sort_proc` guarantees; see fks-leg-structure-and-sort.md).
- The extra-mother machinery (combine_ij counterterms) lives in
  `generate_reals`; see extra-counterterm-and-dedup.md.
