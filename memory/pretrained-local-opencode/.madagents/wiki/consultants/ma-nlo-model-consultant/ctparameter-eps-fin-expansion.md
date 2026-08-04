---
description: How each CTParameter splits into per-Laurent-pole internal params (_2EPS_/_1EPS_/_FIN_), treat_couplings rewrites CT coupling exprs into per-pole dicts, and the double-pole-coupling rejection vs 2EPS-CTParameter support distinction.
---

# CTParameter EPS/FIN expansion

(v3.7.1, `$MADGRAPH_INSTALL`.) A loop UFO's CTParameters carry a Laurent series in
`value` (a dict keyed by pole order). On import each CTParameter is fanned out into
separate internal parameters per non-zero pole, and every CT *coupling* whose expression
references a CTParameter is rewritten into a per-pole dict. This page is the mechanism;
ct-files-and-vertex-types names the files, ct-type-string-lifecycle names the type tag.

## The pole naming map
`$MADGRAPH_INSTALL/models/import_ufo.py:60`:
```python
pole_dict = {-2:'2EPS', -1:'1EPS', 0:'FIN'}
```
Keys are Laurent pole orders (CTParameter dict convention: `0`=finite, `-1`=single pole,
`-2`=double pole). The suffix is `_<tag>_`, e.g. `myCT_FIN_`, `myCT_1EPS_`, `myCT_2EPS_`.

## Per-pole internal parameter creation
`get_additional_CTparameters` (import_ufo.py:2115-2131): for each CTParameter, for
`pole in range(3)` (i.e. orders 0,-1,-2 via `CTparam.pole(pole)`), if that pole is not
`'ZERO'` it copies the CTParameter into a new `internal` parameter named
`'%s_%s_'%(CTparam.name, pole_dict[-pole])` with `value = CTparam.pole(pole)`. So ONE
CTParameter with finite+single+double poles becomes THREE internal params
(`_FIN_`,`_1EPS_`,`_2EPS_`); a zero pole produces no param.

A name-collision guard runs first (import_ufo.py:547-556): if any
`<name>_<tag>_` would clash with an already-defined parameter → `InvalidModel`.

## treat_couplings: CT coupling expr -> per-pole dict
`treat_couplings` (import_ufo.py:1383-1556) scans every coupling. If a coupling's value
string contains a CTParameter, it is rewritten to a dict keyed by pole. Worked example
from the docstring (1386-1395):
```
coupling.value = '2*(myCTParam1 + myParam*(myCTParam2 + myCTParam3))'
  myCTParam1 = {0: ..., -1: ...}; myCTParam2 = {0: ...}; myCTParam3 = {-1: ...}
->
coupling.value = {0:  '2*(myCTParam1_FIN_ + myParam*(myCTParam2_FIN_ + ZERO))',
                  -1: '2*(myCTParam1_EPS_ + myParam*(ZERO + myCTParam3_EPS_))'}
```
For each pole the CTParameter names are regex-substituted to their `_<tag>_` form when
that pole is non-zero, else to `ZERO` (import_ufo.py:1404-1417, 1490-1501). A pole whose
whole expression reduces to zero (`is_value_zero`) yields no dict entry / returns `'ZERO'`
(1503-1516). Constraint on CT coupling expressions referencing CTParams: only `+ - * /`,
each additive term has exactly ONE CTParameter, never in a denominator (comment 1510-1512).

## Two side maps built here
- `map_CTcoup_CTparam` (1535-1536): `coupling_name -> [CTparamName_<tag>_, ...]` — which
  pole-specific CTparams enter each (pole-suffixed) coupling. Pole couplings get name
  suffix `_<n>eps` here too (1532).
- `notused_ct_params` (1551-1556): CTParameters that never appear in any coupling.

## Revert contract (the UFO must be left intact)
treat_couplings stores the original string in `coupl.old_value` and replaces
`coupl.value` with the dict (1541-1548). `revert_CTCoupling_modifications`
(import_ufo.py:2100-2113) restores `old_value`. The dict form exists ONLY between
treat_couplings and `add_CTinteraction`; it is reverted in `OrganizeModelExpression` so a
second pass over the UFO sees the original strings (comment 592-594).

## CAUTION — double pole: CTParameter YES, CT coupling NO
Source-level tension that bites recall:
- A CTParameter MAY have a `-2` (double) pole — `pole_dict` includes `-2:'2EPS'` and
  `get_additional_CTparameters` creates a `_2EPS_` internal param for it (2120-2130).
- But a CT *interaction coupling*'s net double-pole contribution must be ZERO: in
  `add_CTinteraction`, `poleOrder==2` with a non-`'ZERO'` expression → `InvalidModel`
  (import_ufo.py:1611-1620). The error comment explicitly flags it may instead be a
  parsing error in `is_value_zero`.
So "double poles are rejected" is true for the coupling that decorates a CT vertex, NOT
for CTParameters in the abstract. (The physics: UV renormalization here is at most 1/eps;
a surviving 1/eps^2 in a renormalization-constant coupling signals a model error.)

## Boundary
- Static import-time mechanism (string rewriting + param fan-out); predicts param/coupling
  NAMES and the validation errors, not runtime numerics. The `InvalidModel` raise is
  probe-confirmable but recorded here from source, not yet probe-verified.
- The coupling-value rewrite + `old_value` stash + `revert_CTCoupling_modifications` here is
  one of three instances of MadGraph's mutate→reuse→revert design for CT handling; the
  unifying principle (and its exception-unsafety) is in
  ct-generation-reuses-tree-machinery-via-revertible-mutation.
