---
description: Deep principle — RestrictModel's coupling-merge and parameter-merge are one algorithm (normalize value, collide with sign coeff ±1, keep first, sign-fold the redirect, record the rule); explains why sign-folding + rule_card exist (import_ufo.py v3.7.1)
---

# The value-collision-merge invariant

RestrictModel merges identical couplings (detect-identical-couplings.md) and identical
parameters (parameter-fixing-and-merging.md) with the SAME algorithm over different objects.
This page names the shared shape so any merge-path question resolves from one frame, and
explains WHY the sign-folding and rule_card machinery exist.

## The five-step shape (both paths)
1. **Normalize the numeric value.** Couplings: `limit_to_6_digit` rounds real/imag to
   `abs(round(log10))+10` digits (import_ufo.py:2539-2546). Parameters: raw value from
   `parameter_dict`, but FIRST skip the magic escapes `[0,1,0.000001e-99,9.999999e-1]` and
   the `decay` block (2724-2727). Couplings have NO escape skip.
2. **Collide against a value→members map keyed WITH sign.** If `value` already a key →
   append `(name, +1)`. Else if `-value` (couplings: `-1*value`; params: `(block,-value)`)
   is a key → append `(name, -1)`. Else new singleton. Couplings: 2562-2570. Params:
   2731-2738. Identical structure, coeff ∈ {±1}.
3. **Keep the FIRST member as survivor, forced positive.** Couplings: if `tmp3[0][1]==-1`
   flip the whole group's coeffs (2587-2588), then `merge_iden_couplings` asserts
   `couplings[0][1]==1` (2782-ish). Params: first kept (2825+).
4. **Redirect every reference through a SIGN-FOLDING rewrite** that preserves
   `survivor = coeff * member`. Couplings: `get_new_coupling_name(main,coupling,value,coeff)`
   (@staticmethod, 2747-2777) returns `GC_X` or `-GC_X` so the substituted vertex value
   equals the ORIGINAL value — four-case sign logic handles leading `-` on both `main` and
   stored `value`. Params: new internal `ModelVariable(name,'factor*expr','real')` carries
   the coeff as `factor` (2859-2860).
5. **Record the redirect** so the operative merge stays reconcilable with the declared card.
   Couplings: non-survivors → `self.del_coup`, later `remove_couplings`. Params: coeff +1 →
   `rule_card.add_identical`, coeff -1 → `rule_card.add_opposite` (2843-2848).

## Why sign-folding exists (the load-bearing consequence)
Two quantities with values `v` and `-v` merge into ONE survivor. Without step 4, every
reference to the `-v` member would now read `+v` — a silent sign flip in a vertex coupling
or a parameter expression. The coeff ∈ {±1} threaded from collision (step 2) through the
rewrite (step 4) is exactly what absorbs that flip. So an opposite-sign merge is safe:
`get_new_coupling_name` emits the negated name, `add_opposite` records the negation rule.
This is the single most non-obvious thing about restriction merging — the merge is
value-collision, but sign-correctness is preserved by carrying the sign as data.

## Why the rule_card exists (operative-vs-declared bridge)
Restriction never rewrites the param_card; it mutates the in-memory (operative) model and
records what it did. The parameter-merge's `add_identical`/`add_opposite` (and the
zero/one path's `add_zero`/`add_one`) populate `self.rule_card` (param-card-rule.md) so the
DECLARED card the user later edits is validated against the OPERATIVE merge — e.g. editing
one of two merged masses to differ from its partner is caught at param-card-check time.
Every merge thus produces both an operative mutation AND a declared-side rule.

## Boundary — what this principle does and does NOT catch
- **Catches:** the IDENTICAL-merge half of both coupling and parameter restriction, and
  predicts that any future "merge identical X by input value" path would share the shape.
- **Shares only the front-half with zero/one detection:** `detect_special_parameters` /
  zero-coupling detection normalize the value (step 1) then decide FATE (prune / turn
  internal), not merge. Steps 2-5 are merge-specific.
- **Does NOT extend to Goldstone-vector merge or color-rep walk:** those collide on
  PHYSICAL attributes (mass + spin-3 uniqueness; T(...)/Identity(...) color tensors), not on
  numeric input value, and they run at conversion time in UFOMG5Converter, not in
  RestrictModel. See goldstone-vector-merge.md / color-rep-walk.md.
- **Coupling vs parameter asymmetries to remember:** couplings collide on rounded COMPLEX
  value with no escape skip; parameters collide on `(lhablock, value)` real input and skip
  the four magic/special values + the decay block. Couplings regroup by coupling-order
  before merging (QED≠QCD never merge, 2580-2589); parameters key on lhablock instead.

## Caution
This is a source-structure invariant (no runtime prediction). The two instance pages carry
the per-method line detail and stay authoritative for specifics; this page is the frame.
