---
description: How RestrictModel detects zero and identical couplings, including the small-value zero thresholds and sign/coupling-order grouping (import_ufo.py v3.7.1)
---

# detect_identical_couplings — zero + identical detection

`detect_identical_couplings(self, strict_zero=False)` at `$MADGRAPH_INSTALL/models/import_ufo.py:2525`.
Iterates `self['coupling_dict']` (name → complex numeric value), keys sorted.

## Zero detection (2549-2558)
- `value == 0` → zero coupling.
- not strict_zero and `abs(value) < 1e-13` → treated as zero (logged "coupling with small value ... treated as zero").
- not strict_zero and `abs(value) < 1e-10` → RECURSE with `strict_zero=True`. I.e. if ANY coupling is in the ambiguous 1e-13..1e-10 band, the whole detection re-runs in strict mode (only exact 0 counts as zero). This guards against accidentally zeroing couplings that are merely small.

## Identical detection (2560-2594)
- `limit_to_6_digit(value)` (2539-2546) rounds real and imag parts to ~`|log10|+10` digits — a value-normalisation so near-equal couplings collide.
- Groups by value; a coupling equal to `-1*existing` is grouped with sign coeff -1 (`dict_value_coupling`).
- For each multi-member value, **regroups by coupling order** (`get_coupling_order`, 2596): only couplings sharing the SAME coupling order are merged together (2579-2589). So two couplings with identical numeric value but different orders (e.g. QED vs QCD) are NOT merged.
- First coupling in a group is forced to positive sign (2587-2588).

Returns `(zero_coupling, iden_coupling)` where iden_coupling is a list of groups, each group a list of `(name, coeff)` with coeff in {+1,-1}.

## merge_iden_couplings — the substitution (2780-2816)
Detection only groups; `merge_iden_couplings(couplings)` (pipeline step 8, 2428-2429) does the rewrite per group.
- `main = couplings[0][0]`, `assert couplings[0][1] == 1` — the first member (forced positive in detection) is the survivor; the rest go onto `self.del_coup` for later removal (2789-2791).
- For each non-survivor, walk its vertices (via `coupling_pos`) and replace the vertex coupling entry with `get_new_coupling_name(main, coupling, value, coeff)` (2800-2804); counterterm entries replaced with bare `main` (2812-2815).

## Interaction-set consequence: identifier collapse, not vertex deletion
Identical-coupling merging does NOT change the number of vertices or which particles interact — every interaction that referenced a non-survivor coupling keeps its `(color,lorentz)` entries, just rewritten to point at the survivor's `GC_X`/`-GC_X` name. The net effect on interaction content is purely a SHRINK of the distinct-coupling-identifier set: N numerically-equal couplings collapse to 1 (the survivor), the other N-1 land on `self.del_coup` and are dropped from `self['couplings']` by `remove_couplings` (pipeline step 9, 2432-2433). Contrast with `remove_interactions` (zero couplings), which CAN delete a whole vertex when it loses its last coupling. Merging never empties a vertex — it substitutes one live name for another, so the vertex always retains a coupling. This is why the aloha/coupling-export stage sees fewer distinct `GC_*` to generate after restriction, but the diagram topology set is unchanged by the merge step.

## get_new_coupling_name — sign-folding (2748-2777, @staticmethod)
Maintains the invariant `main == coeff * coupling` and returns whichever of `GC_X` / `-GC_X` makes the substituted vertex value equal the ORIGINAL value. coeff ∈ {-1,+1}; both `main` and the stored `value` may carry a leading `-`. The four-case logic (2762-2777) flips or keeps the sign so sign correctness survives merging two opposite-sign couplings. This is why an opposite-sign (coeff -1) merge does not silently flip a vertex's sign — the substituted name absorbs it.

## Caution
The 1e-13 / 1e-10 thresholds are absolute, not relative to coupling magnitude. A genuinely tiny physical coupling (< 1e-13) is silently dropped as zero. The strict_zero recursion only changes the 1e-13..1e-10 band handling, not the < 1e-13 cut.
