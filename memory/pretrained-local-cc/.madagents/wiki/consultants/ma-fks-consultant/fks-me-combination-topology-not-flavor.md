---
description: FKS Helas ME combination matches subprocesses on TOPOLOGY (IdentifyMETag / ij-config shape) and folds FLAVOR into per-ME process lists — why the FKS ME/subprocess count collapses below the amplitude-level born count.
---

# FKS ME combination: match on topology, fold flavor into process lists

The single principle behind why the FKS subprocess (matrix-element) count is
*smaller* than the number of amplitude-level born processes:

> FKS Helas ME combination keys every equality test on **topology**
> (diagram structure / ij-config shape), deliberately ignoring **flavor**
> (pdg ids, charges, underlying-born). Flavor-equivalent subprocesses fold into
> ONE `FKSHelasProcess`, and the distinct flavors are kept as separate **process
> pdg-lists** inside that ME (keyed on the leg-id list, which keeps mirror
> processes distinct).

This catches more than the two instance pages individually: it is the answer to
"why do I see N FKS subprocess directories / MEs and not the M I counted from the
born list?" — a question neither fkshelasrealprocess-equality.md (the real `__eq__`)
nor helas-async-generation.md (add_process / `IdentifyMETag` born compare) names on
its own. The collapse is the *joint* consequence of three topology-not-flavor
predicates firing at three granularities.

## The three topology-match predicates (all in fks_helas_objects.py)

1. **Born topology** — `FKSHelasProcess.__eq__` (`:850-863`) compares
   `IdentifyMETag.create_tag(born_me.base_amplitude)` of self vs other ("equal up
   to color links"). Two borns with the same diagram topology but different flavors
   (e.g. `u u~ > t t~` vs `c c~ > t t~`) are equal. (Short-circuited to `return
   False` under ewsudakov, `:861-863` — see helas-async-generation.md.)
2. **Real topology** — `FKSHelasRealProcess.__eq__` (`:1010-1030`) compares the
   real Helas ME and the fks_infos **shape**, skipping `charges`, and per-info
   skipping `ij_id` and `underlying_born` (`:1014-1016,1019-1029`). Same i/j/ij/
   splitting_type/need_*_links, different mother pdg and born pdg list → equal.
   (Detail: fkshelasrealprocess-equality.md.)
3. **Process accounting = leg-id list, NOT the Process object** —
   `add_process` (`:906-913` born, `:930-937` real) appends `oth_proc` only if its
   `[leg['id'] for leg in proc['legs']]` is not already present. Comment `:906/:930`:
   "store pdg lists rather than processes in order to keep mirror processes
   different" — mirrored initial states share the ME but differ in leg-id order, so
   they stay distinct processes within the merged ME.

When (1) declares two borns equal, `add_process` (3) folds `other` in, and it
assumes a **1-to-1 real correspondence** via (2) — a miss RAISES
`FKSProcessError('add_process: error in combination of real MEs')` (`:927-929`).
So the three predicates are coupled: the born topology match is only safe because
the reals line up by topology too.

## Probe-verified (v3.7.1)

`generate p p > t t~ [QCD]`:
- amplitude-level `fksmulti['born_processes']` = **9** distinct FKSProcess borns.
- After `FKSHelasMultiProcess`, `['matrix_elements']` = **3** combined
  `FKSHelasProcess` MEs:
  - one ME holding **1** born-process (the `g g > t t~` topology, distinct), with 5
    real topologies;
  - two MEs each holding **4** born-processes — the four light-quark flavors
    (`u u~`, `d d~`, `c c~`, `s s~ > t t~` and the mirrored `q~ q`) folded by born
    topology match — each with 3 real topologies, and **each real topology carries
    4 process pdg-lists** (the 4 flavors merged by `add_process` keying on leg-id).

So 9 born amplitudes → 3 MEs is exactly flavor-folding: borns differing only in
light-quark flavor collapse to one ME, their reals collapse to one real topology
each carrying the per-flavor process list. The `g g` initial does NOT fold (its
topology is genuinely different), which is why it stands alone.

## Why this is the principle, not just the union

- A user counting born subprocesses and expecting that many FKS subprocess dirs is
  surprised by the collapse. The collapse factor = (number of flavor-equivalent
  borns sharing a topology). To predict it you must know that ALL THREE predicates
  ignore flavor in lockstep — reading any one instance page alone leaves you unable
  to say whether the reals also fold (they do) or whether mirrors fold (they don't).
- The boundary: this is the **non-ewsudakov** combination path. Under
  `ewsudakov=True`, predicate (1) short-circuits to `return False` and NOTHING
  combines — the ME count then equals the born count (inflated). That inversion is
  itself evidence the principle is real: turn off the topology match and the
  collapse vanishes.
- It is QCD/QED-agnostic at the predicate level (the equality tests don't branch on
  perturbation), but the *flavor sets* that fold are model- and process-dependent.

## Cautions / where it does NOT apply
- The collapse is at the **Helas ME** stage, AFTER the amplitude-level pruning
  (silent-real-config-drops.md sites 1–5). Don't attribute a missing subprocess to
  this folding if it was already pruned upstream — folding *merges* survivors, it
  does not *drop* configs (except site 6, the born-no-diagram append guard, which is
  a drop not a fold).
- "Topology" here means HelasMatrixElement/IdentifyMETag equality — same diagrams up
  to relabeling. Two processes with the same external legs but different diagram
  content (e.g. extra s-channel resonance) are NOT topology-equal and will not fold.
- ewsudakov inverts the principle (no folding); the warning
  `'With --ewsudakov, matrix elements will not be combined'` fires per comparison.
