---
description: How import_model determines the rm_parameter and keep_external flags passed into RestrictModel.restrict_model, and what each flag changes inside restriction (import_ufo.py v3.7.1)
---

# Restriction flag determination — where rm_parameter / keep_external come from

My other pages (parameter-fixing-and-merging.md, restrict-model-pipeline.md) treat
`rm_parameter` and `keep_external` as GIVEN inputs to `restrict_model`. This page traces
where the caller sets them and what each one changes inside restriction, so a "why did
restriction keep/strip param X?" question resolves to the caller-side decision.

## The two callers (grep-verified v3.7.1)
Only two live call sites of `restrict_model`:
- `models/import_ufo.py:309` (inside `import_model`): `model.restrict_model(restrict_file, rm_parameter=not decay, keep_external=keep_external, complex_mass_scheme=complex_mass_scheme)`.
- `madgraph/interface/madgraph_interface.py:7795`: `self._curr_model.restrict_model(param_card, keep_external=keep_external)` — leaves `rm_parameter` at its default `True`.

(import_ufo.py:457 is a commented-out third site.)

## rm_parameter = not decay (import_ufo.py:309)
`import_model(model_name, decay=False, ...)` — the `decay=` argument flips
`rm_parameter`. `rm_parameter` becomes `simplify` inside `fix_parameter_values`
(2441-2442, `simplify=rm_parameter`):
- `decay=False` (normal load) → `rm_parameter=True` → `simplify=True` → zero/one external
  params that are no longer USED are REMOVED from the model entirely (used ones become
  `0.0`/`1.0` internals). See parameter-fixing-and-merging.md.
- `decay=True` (model loaded for decay-width computation) → `rm_parameter=False` →
  `simplify=False` → `used = special_parameters` (3043): ALL zero/one params are kept as
  `0.0`/`1.0` internal `ModelVariable`s, none removed. The decay machinery needs the full
  parameter set present, so it loads with restriction's pruning of zero/one params disabled.

So the SAME restrict card produces a model with more parameters present when loaded for
decay computation than for a normal generate. (Whether `decay=True` is actually passed for
a given launch is madwidth/model-loader orchestration; this page records only the flag→effect.)

## keep_external — auto-detected for SLHA2 / MSSM (import_ufo.py:296-305)
Right before the `restrict_model` call, `import_model` computes `keep_external`:
```
blocks = model.get_param_block()                # set of external lhablocks (2819-2823)
if model_name == 'mssm' ...:            keep_external = True   # 298-299
elif all(b in blocks for b in
   ['USQMIX','SL2','MSOFT','YE','NMIX','TU','MSE2','UPMNS']): keep_external = True  # 300-301 (SLHA2 signature; needs block 'SL2' — MSSM_SLHA2 has 'MSL2' not 'SL2', so this branch MISSES it)
elif model_name == 'MSSM_SLHA2' ...:    keep_external = True   # 302-303 (this is the branch MSSM_SLHA2 actually hits)
else:                                   keep_external = False  # 304-305
```
`get_param_block()` (2819-2823) exists precisely to collect the external-block set for this
SLHA2 signature test. When True, logs `'Detect SLHA2 format. keeping restricted parameter in the param_card'` (307).

### What keep_external changes inside restriction
- The mssm guard (2398-2399): `if self.get('name')=='mssm' and not keep_external: raise
  Exception`. NOTE the guard tests `get('name')`, set to the model DIRECTORY BASENAME (412), so
  it matches ONLY the v4-style model literally named `mssm` — NOT `MSSM_SLHA2`. For the v4 `mssm`
  model the 298-299 branch forces `keep_external=True`, keeping the guard from firing. For
  `MSSM_SLHA2` the guard is irrelevant (name≠'mssm'); its keep_external comes from the explicit
  `elif model_name=='MSSM_SLHA2'` at 302-303 (the SLHA2-block-signature `elif` at 300 does NOT
  catch it — that test requires block `'SL2'`, and the MSSM_SLHA2 card declares `MSL2`, not
  `SL2`, so the signature `all(...)` is False).
- Identical-parameter merge runs in TWO passes (2444-2452): the first pass is GUARDED by
  `if not keep_external`, the second always runs with the flag. So a `keep_external` load
  skips the first (non-keeping) merge pass. See parameter-fixing-and-merging.md.
- `fix_parameter_values` keep_external=True: external special params are NOT removed even if
  unused (3093-3094).
- `merge_iden_parameters` keep_external=True: non-kept members of a merge group are removed
  from the external list ONLY for MASS/DECAY blocks; for all other blocks the param keeps its
  slot with name blanked + an info note (2851-2857). So a `keep_external` model's param_card
  retains its (now-redundant) rows for non-mass/width merged params — by design, so the SLHA2
  card the user feeds stays structurally intact.

## Why this matters (operative-vs-declared)
`keep_external=True` is the "don't disturb the user's param_card structure" mode: SLHA2/MSSM
cards are large and externally authored, so restriction keeps their external rows present
(blanked/info-noted) instead of deleting them, even though the operative model merges them.
`keep_external=False` (the SM default) freely deletes merged/zeroed external rows. Both still
emit the same rule_card entries (add_zero/one/identical/opposite) — keep_external changes what
is DELETED from the external list, not what RULE is recorded. See rule-write-target-asymmetry.md.

## Caution
- `decay` and `keep_external` are independent: a decay-mode load of a non-SLHA2 model has
  `rm_parameter=False, keep_external=False`. They gate different things (param removal vs
  external-row retention).
- This page's caller-side logic lives in `import_model`, which is model-loader's orchestration
  function; the flag-DECISION and the in-`RestrictModel` EFFECTS are this slice. The broader
  question of when `import_model` is invoked with `decay=True` (which command paths) is
  model-loader/madwidth.
