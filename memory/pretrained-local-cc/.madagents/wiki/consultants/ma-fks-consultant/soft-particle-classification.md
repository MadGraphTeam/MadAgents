---
description: How find_pert_particles_interactions classifies IR-singular interactions and soft particles (even-spin massless rule, degeneracy/ghost filters); per-pert_order recompute, BSM-order no-op gate, and coupling_orders restriction-dependence.
---

# Soft-particle / IR-singular interaction classification (and BSM/restriction dependence)

`find_pert_particles_interactions(model, pert_order='QCD')`
(`$MADGRAPH_INSTALL/madgraph/fks/fks_common.py:516`) returns a dict with three
keys: `interactions` (the IR-singular base interactions of order `pert_order`),
`pert_particles` (pdgs of all particles in those interactions), `soft_particles`
(pdgs of the *massless* particles among `pert_particles`).

**Core principle:** the soft/IR-singular set is computed FRESH from the active
model's `interaction_dict` per `pert_order` STRING. "QCD" is just the default
argument — there is nothing QCD-special in the code path; any order string (QED,
NP, DIM6, a new gauge order) runs the identical two gates. The active interaction
list is the *post-restriction* one, so the result is restriction-dependent.

## Selection algorithm (fks_common.py:530-564)
Loops over `model['interaction_dict']`. An interaction is kept only if **all** of:

1. `ii.get('type') == 'base'` — skips counterterm/UV/R2 interaction types (`:534`).
2. `ii.get('orders') == {pert_order:1}` AND `len(ii['particles']) == 3` — exactly
   one power of *only* the perturbed order and exactly a 3-point vertex (`:536`).
   A vertex carrying mixed orders (`{'QCD':1,'NP':1}`, `{'NP':2}`) or a 4-point
   contact FAILS — so an EFT operator vertex is never an FKS soft emitter.
3. **Even-spin massless particle present** (`:539-547`,
   `found_soft_even_spin_particle`): at least one particle with
   `mass.lower()=='zero'` and `spin % 2 == 1`. Spin is stored as 2S+1, so
   `spin%2==1` means spin is *integer* (odd 2S+1 → boson: gluon spin=3, photon
   spin=3, scalar spin=1). Without such a particle the interaction is NOT
   IR-singular. (Variable name "even spin" = bosonic.) A BSM order whose 3-point
   vertices emit only massive bosons or only fermions is NOT IR-singular.
4. **Degeneracy filter** (`:553-557`): after removing one `'zero'` mass entry
   (`ValueError`→skip if none), the remaining masses must be a single value
   (`len(set(masslist))==1`) — so real-emission final state is mass-degenerate
   with the born.
5. **Ghost/goldstone exclusion** (`:557-559`): none of the interaction particles
   (by pdg or anti-pdg) may be in `ghost_list` (built at `:524` from particles
   with `ghost` or `goldstone` true).

## What lands in each list (fks_common.py:561-564,567)
For a kept interaction, every particle pdg → `pert_particles`; particles with
`mass.lower()=='zero'` → `soft_particles`. Both returned `sorted(set(...))`.

## Which pert_orders get classified — the find_reals iteration (fks_base.py)
`find_pert_particles_interactions` is invoked per pert_order; `FKSProcess.find_reals`
(`fks_base.py:868`) decides which orders to iterate (`:884-888`):
- **no born `[orders]`** → `pert_orders = model['coupling_orders']` (`:886`) —
  EVERY coupling order in the model becomes a candidate perturbation (the
  EW/mixed-correction path, "only squared orders are imposed").
- **born has `[orders]`** → `pert_orders = process['perturbation_couplings']`
  (`:888`) — only the explicitly-requested perturbed orders.
Then `for pert_order in pert_orders:` (`:915`) runs splittings per order.
`find_splittings(...,pert)` (`:262`) and the `combine_ij` path (`:465`) each call
`find_pert_particles_interactions` with whatever order string they are handed.

## coupling_orders is restriction-dependent (base_objects.py:1374-1377)
`model['coupling_orders']` = `set(sum of all interactions' order keys)`
(`get_coupling_orders`, `base_objects.py:1374-1377`) — it reflects only orders
that SURVIVE the active restriction. Restricting away an order's couplings removes
it from `coupling_orders`, which silently removes it from the find_reals
perturbation iteration. The restriction card thus controls which orders FKS even
considers perturbing. A `coupling_orders` printed from a restricted model is NOT
the UFO's full order list — verify against the loaded (restricted) model.

## Probed result (SM, v3.7.1)
- QCD `soft_particles = [-4,-3,-2,-1,1,2,3,4,21]` — the gluon AND all massless
  quarks (u,d,s,c ± anti). b,t are massive so absent from soft (present in
  pert_particles). So "soft" is "massless particle in a kept interaction", NOT
  "the radiated boson" — light quarks are soft because the q-q-g vertex passes the
  even-spin-massless (gluon) + degeneracy filters.
- QED `soft_particles = [-13,-11,-4,-3,-2,-1,1,2,3,4,11,13,22]` — photon, light
  charged leptons (e,μ; τ massive→absent), light quarks. pert_particles also
  includes W±, b, t, τ.

## Probed result (BSM, v3.7.1, SMEFTatNLO)
`import_model('SMEFTatNLO')` (default restriction):
- `coupling_orders == ['QCD','QED']` — **`NP` is ABSENT**. Zero interactions carry
  an `NP` order under the default restriction (probed). So with the default card,
  find_reals never even iterates an NP order.
- `import_model('SMEFTatNLO', restrict=False)` → `coupling_orders ==
  ['NP','QCD','QED']`. Now `find_reals` WOULD iterate `'NP'` — but
  `find_pert_particles_interactions(m,'NP')` returns
  `{interactions:[], pert_particles:[], soft_particles:[]}` (probed). An empty
  `pert_particles` makes `find_splittings` short-circuit at the
  `leg['id'] in dict['pert_particles']` test (`fks_common.py:265`) → no splittings,
  no soft singularities. **NP is a no-op perturbation order.**
- QCD soft set in SMEFTatNLO = `[-5..-1,1..5,21]` and QED soft includes `15` (τ):
  **b(5) and τ(15) are MASSLESS** in this 5-flavor NLO model (probed
  `pd[5]['mass']=='ZERO'`, `pd[15]['mass']=='ZERO'`) — so they ARE soft here,
  unlike the default SM where b,t are massive and absent from soft. The soft set is
  MODEL/RESTRICTION dependent, not a fixed `[1,2,3,4,21]`. Same process, different
  real-config count, driven by the model's mass assignments — read the model.

## Cautions
- The even-spin (bosonic) massless requirement means a massless *fermion*-only
  vertex is never IR-singular here — IR singularity is tied to emission of a
  massless boson (gluon/photon). But the massless fermion still lands in
  `soft_particles` because it is the massless member of the (q q g) interaction.
- `interactions` is restricted to `type=='base'`; model files carrying split
  interaction types will not contribute counterterm vertices to FKS soft mapping.
- Generating NLO in a BSM model where the BSM order has NO single-power 3-point
  massless-boson-emitting base vertex (the usual case for EFT operators) means the
  BSM order contributes ZERO real singularities — corrections come only via
  QCD/QED splittings off the BSM-modified born. The BSM order rides in the born/
  loop amplitude (squared-order bookkeeping), not in the FKS subtraction.
- If a BSM model genuinely introduces a NEW massless gauge boson (a new unbroken
  U(1)/SU(N)), its 3-point `{neworder:1}` vertices WOULD pass both gates and create
  a new soft-singular sector — requires the new boson `mass=='ZERO'`, `spin%2==1`.
  This is the only BSM way to get non-QCD/QED FKS singularities.
