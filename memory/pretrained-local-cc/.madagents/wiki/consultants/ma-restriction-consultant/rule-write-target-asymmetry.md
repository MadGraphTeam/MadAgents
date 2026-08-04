---
description: Deep principle — a restriction mutation emits a declared-side rule_card entry IFF it mutates a user-editable external param; coupling/lorentz/conversion mutations write none. The param_card's (block,lhacode) addressing is the determinant (import_ufo.py v3.7.1)
---

# The rule-write-target asymmetry

Restriction performs many in-memory mutations, but only SOME of them leave a
declared-side trace in `self.rule_card` (param-card-rule.md). This page names the
single determinant of which do, so any "will restriction record a card rule for
mutation X?" question resolves from one test instead of per-mutation recall.

## The principle
A restriction mutation emits a `rule_card` entry **iff it mutates a quantity the
user can edit in the param_card** — i.e. an EXTERNAL parameter addressed by
`(lhablock, lhacode)`. Everything else mutates only the in-memory (operative) model
and records nothing.

## The four rule-writes, all parameter-level (grep-verified v3.7.1)
The ONLY `rule_card.add_*` calls in import_ufo.py:
- `fix_parameter_values` → `add_zero` (3010) / `add_one` (3012) — zero/one EXTERNAL params.
- `merge_iden_parameters` → `add_identical` (2844) / `add_opposite` (2847) — merged EXTERNAL params.

Both operate on `self['parameters'][('external',)]` members carrying `lhablock`/`lhacode`.

## What writes NO rule (verified by grep over each method body)
- **Zero-coupling vertex prune** (`remove_interactions`, 2876-2970): 0 rule_card refs.
- **Identical-coupling merge** (`merge_iden_couplings`, 2780-2824): 0 rule_card refs.
- **Lorentz fusion** (`optimise_interaction`/`add_merge_lorentz`, 3102/3175): none.
- **Auto-width restore** (2467-2475): none — re-marks a DECAY value 'auto' in place.
- **Conversion-time mutations** (Goldstone-vector merge, color-rep walk) in
  `UFOMG5Converter` (461-2039): 0 rule_card refs — that class does not even OWN a
  `rule_card` attribute (only `RestrictModel.default_setup` sets it, 2381), and it
  runs BEFORE any param_card restriction.

## The determinant (the load-bearing WHY)
`ParamCardRule.check_param_card` validates the user's param_card by indexing
`card[block].get(id)` (check_param_card.py:1319+, the `for block, id, ... in self.zero`
loops). A param_card is addressed entirely by `(block, lhacode)` — the external-parameter
scheme. **Couplings are DERIVED, not external: they have no `(block, lhacode)` and never
appear in a param_card.** So a coupling mutation needs no card-side rule (the user cannot
edit a coupling to violate it), whereas every external-parameter mutation needs one (the
user CAN edit that card value and must be caught/corrected). The asymmetry is forced by
what the param_card can address, not by a per-method choice.

## What this catches beyond the instance pages
- Predicts for ANY future restriction-mutation type whether it must emit a rule, from
  one test: "is the mutated quantity a user-editable external param `(block,lhacode)`?"
  A new param-block restriction → yes, emits. A new derived-quantity prune → no.
- Explains why an unrestricted (`-full`) model and a conversion-only step both leave a
  fully free card with no enforcement: no `RestrictModel` pass → no `rule_card` attribute
  → `export_v4.create_param_card` writes no `param_card_rule.dat` (param-card-rule.md).
- Sharpens operative-vs-declared: a coupling prune is purely operative (no declared trace);
  a mass merge is BOTH operative (vertex/particle fields repointed) AND declared (a card rule).

## Boundary — what this does and does NOT cover
- This predicts rule-write PRESENCE, not the merge ALGORITHM. The value-collision shape
  (normalize → collide with sign → keep first → sign-fold → record) is
  value-collision-merge-invariant.md; that page covers couplings AND params symmetrically
  because the algorithm is the same. THIS page is the orthogonal axis: only the param half
  of that shared algorithm reaches the rule_card.
- The `rule` (functional constraint) list is NOT emitted by restriction at all (read-back
  only from a serialized `<rule>` element) — see param-card-rule.md. This principle covers
  the four restriction-GENERATED rule kinds (zero/one/identical/opposite).
- Source-structure invariant; no runtime prediction.

## Instance pages (kept — they carry per-method line detail)
param-card-rule.md (the rule object + five lists), parameter-fixing-and-merging.md
(add_zero/one/identical/opposite call sites), value-collision-merge-invariant.md (the
shared merge algorithm), remove-interactions.md / detect-identical-couplings.md (the
no-rule coupling mutations), goldstone-vector-merge.md / color-rep-walk.md (the no-rule
conversion mutations).
