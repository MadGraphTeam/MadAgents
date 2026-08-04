---
description: The mdl_ prefix RENAMES model parameters (change_parameter_name_with_prefix, NOT aloha_prefix) at import; fixed exclusion list as/mu_r/zero/aewm1/g; param_card keyed by lhablock+lhacode and STRIPS mdl_ from comment, so a prefix toggle never breaks card matching. BSM/EFT Wilson coeffs become mdl_cX.
---

# The `mdl_` prefix: parameter renaming at import (v3.7.1)

`--noprefix` in `do_import` drives **two distinct mechanisms** off one flag
(`madgraph_interface.py:5781`, `prefix = not '--noprefix' in args`):

1. `aloha.aloha_prefix = 'mdl_'` / `''` (`:5783`/`:5785`) — prefixes ALOHA-generated
   **wavefunction/HELAS routine** names. Module-level. (Covered in do-import-model-flow.md.)
2. `prefix` arg threaded into `import_ufo.import_model(prefix=prefix)` (`:5788`) → renames the
   model's **parameters** (the names that index couplings/masses and surface in
   `display parameters` and as the param_card comment). THIS page owns mechanism #2.

The two are independent code paths sharing the `--noprefix` flag; #1 touches HELAS output,
#2 touches the parameter graph.

## Where the parameter rename happens
`import_full_model` (`models/import_ufo.py:328`): `if prefix is True: prefix='mdl_'` (`:334-335`);
after the UFO→MG5 conversion and Organize step, `if prefix:` →
`model.change_parameter_name_with_prefix()` (`:440-442`). So renaming is part of the
**uncached UFO read** — the pickle stores the already-prefixed model, and the pickle-validity
check (`:378-397`) inspects whether the first non-excluded param starts with the requested
prefix to decide reuse vs `reload from .py file`.
- NB the pickle-check uses its OWN exclusion `['as','mu_r','zero','aewm1']` (`:382`,
  NO `'g'`), DISTINCT from the rename list at `base_objects.py:1658`
  (`['as','mu_r','zero','aewm1','g']` — same set plus `'g'`). The two lists are NOT identical —
  don't conflate them. (Verified `:382` and `:1658` v3.7.1.)

## `change_parameter_name_with_prefix` — `base_objects.py:1627`
- Default arg `prefix='mdl_'` (`:1627`).
- **Fixed exclusion list** (`:1658`): `value in ['as','mu_r','zero','aewm1','g']` → NOT prefixed
  (compared lowercased, `:1657`). So `aS`, `MU_R`, `zero`, `aEWM1`, `G` keep their bare names
  even under the default prefix. Already-`mdl_`-prefixed names are skipped (`:1660-1661`).
- For every other parameter: `change[param.name] = 'mdl_'+param.name`; `param.name` reassigned
  (`:1664-1667`).
- **Case-duplicate handling** (`:1631-1646`, `:1669-1676`): if two params collide when
  lowercased (e.g. `Mh` vs `mh`), they get `mdl_<lower>` and `mdl_<lower>__2`, `__3`, …
  (the `__%d` suffix, `:1672-1673`). The `prefix=='' and not duplicate: return` early-out
  (`:1648-1649`) means `--noprefix` STILL renames case-colliding params to disambiguate.
- After building `change`, a chunked regex (1000 names at a time, `:1697-1700`) substitutes the
  new names through every param `.expr` (except `external`, `:1703-1704`), every coupling expr,
  form-factor values, particle mass/width name strings, and running_elements (`:1702-1731`).
  Also rewrites `parameter_dict` keys (`:1683-1686`) and `map_CTcoup_CTparam` for loop models
  (`:1688-1694`).

## Probe-confirmed parameter-naming effect (BSM/EFT)
`import model SMEFTatNLO-NLO; display parameters` → Wilson coefficients show as **`mdl_Lambda`,
`mdl_cpDC`, `mdl_cp`, `mdl_ctG`, `mdl_ctZ`, …** under `('external',)`. With `--noprefix` the same
display shows bare **`Lambda`, `cpDC`, `cp`, `ctG`**. The exclusions hold under default:
`G = 2*mdl_sqrt__aS*...` (bare `G`, not `mdl_G`) and `aEWM1 = 1/mdl_aEW` (bare `aEWM1`), while a
DIFFERENT internal param `mdl_aEW` IS prefixed — confirming `aewm1`/`g` are the excluded NAMES,
not a class. (UFO def: `models/SMEFTatNLO/parameters.py` — `cpDC = Parameter(name='cpDC',
lhablock='DIM6', lhacode=[2])` etc.; the rename mutates only `.name`, never `lhablock`/`lhacode`.)

## The param_card is keyed by LHA block+code, NOT by the prefixed name
`ParamCardWriter.write_param` (`models/write_param_card.py:239-272`):
- comment name `info = param.name`, then **`if info.startswith('mdl_'): info = info[4:]`**
  (`:246-247`) — the `mdl_` is STRIPPED from the trailing `# comment`.
- the line is emitted as `  <lhacode> <value> # <info>` (`:265-267`), keyed by the numeric
  `lhacode` under its `Block <lhablock>` header.

So the card bytes for a Wilson coefficient are e.g. `  2 6.108140e-01 # cpDC` under
`Block DIM6` — **never `mdl_cpDC`**. Restrict cards are the same format (probe of
`models/SMEFTatNLO/restrict_NLO.dat`: `Block SMINPUTS` / `2 1.166370e-05 # Gf`, bare `Gf`).
Card reading (`set_parameters_and_couplings` → ParamCard) matches on block+lhacode
(`base_objects.py:1972` uses `yukawa.lhacode[0]`), not on the parameter name.

## CAUTION — corrects the naive "prefix toggle breaks a hand-edited card"
A prefix toggle (`--noprefix` vs default) does **NOT** break param_card matching: the card was
**never** keyed by the `mdl_` name — it is keyed by `lhablock`+`lhacode`, and the writer strips
`mdl_` from the only place a name appears (the comment). A param_card hand-edited under one
prefix mode reads identically under the other. What the toggle DOES change:
- the model-internal parameter name (`display parameters`, error messages, generated Fortran
  parameter identifiers, and any `set <paramname> <value>` interface command — `set mdl_cp 0.5`
  vs `set cp 0.5`).
- whether a user's external SCRIPT/restrict reference by NAME (rare) resolves.
Mixed-prefix loads in one session are still discouraged (aloha_prefix is module-level), but the
breakage story is about names-in-code, not card bytes.

## Boundary
- The param_card WRITING (ParamCardWriter formatting, block ordering, dependent-param blocks)
  and the operative param_card-value precedence are param-card / output slice.
- `merge_iden_parameters` setting `param.info` for restriction-merged params
  (`import_ufo.py:2837`/`:2857`, which then becomes the card comment instead of the name)
  is the restriction algorithm — restriction slice.
- UFO parameter declarations (`name`, `lhablock`, `lhacode`, `nature`) are ufo slice. This page
  owns only: WHEN the rename fires, WHAT it excludes, and that the card is name-agnostic.
