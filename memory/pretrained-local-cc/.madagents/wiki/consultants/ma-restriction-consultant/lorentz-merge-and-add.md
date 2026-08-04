---
description: optimise_interaction / add_merge_lorentz / add_lorentz — fusing two lorentz structures sharing a coupling and adding a new lorentz structure during restriction (import_ufo.py v3.7.1)
---

# Lorentz structure merging and addition

## optimise_interaction (3102)
Called once per interaction in the pipeline (2436-2437). Goal: if the SAME coupling (up to sign) is used for two different lorentz structures under the SAME color structure, fuse those lorentz structures into one so the coupling appears once.
- Builds `to_lor` keyed `(color, abscoup)` → list of `(lor_index, coeff)` where coeff is the +/- sign (3107-3113).
- Only keys with >1 lorentz are optimised (3117-3123); early-return if none.
- Lazy-init `self.defined_lorentz_expr`, `self.lorentz_info`, `self.lorentz_combine` from current lorentz list (3125-3131).
- Guard (3142-3144): all members must share the same `spins`, else `logger.warning('not all same spins for a given interactions')` and skip.
- Builds sorted names `u<lorentz>`/`d<lorentz>` (u = coeff +1, d = coeff -1) (3146-3149), looks up or creates merged lorentz via `add_merge_lorentz`, removes the old `(color,lor)` couplings, appends the new lorentz, and points the surviving coupling at the new lorentz index (3158-3171).

## add_merge_lorentz (3175)
- Derives a base name from the longest common prefix of the member names (skipping the leading u/d), else `'LMER'` (3179-3188); appends an incrementing suffix unique in `lorentz_info`.
- New structure = sum of `u`-member structures minus `1.*(...)` of each `d`-member structure (3197-3199).
- spins from first member; formfactors concatenated (3200-3204).
- Calls `add_lorentz(new_name, spins, new_struct, formfact)`.

## add_lorentz (3214)
Constructs a new lorentz object of the same class as `self['lorentz'][0]` with given name/spins/structure (+ optional formfactors), appends to `self['lorentz']`, calls `self.create_lorentz_dict()`. Returns `None`.
Used both by restriction-driven merging and whenever restriction needs a lorentz structure that did not exist in the original UFO.

## Caution
`add_lorentz` returns `None`, but `add_merge_lorentz` stores that None into `self.lorentz_info[new_name]` (3210) — subsequent `lorentz_info[new_name].get('spins')` would fail. In practice a merged name is reused via `self.lorentz_combine` (3152-3154) before its lorentz_info is dereferenced for spins, but this is a source-visible fragility to watch if the same merged structure is needed for a further nested merge.
