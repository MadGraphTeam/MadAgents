---
description: The coupling_alias machinery (EW<->QED, aS, aEW) and the =2* squared-order doubling rule in extract_process.
---

# Coupling-order alias machinery

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `extract_process`
`4891-4926`. `model_orders = self._curr_model.get('coupling_orders')` (`4893`).

## Alias table construction (`4894-4907`)
Driven by which orders the loaded model declares:

- If `'EW' in model_orders`:
  - if `'QED' not in model_orders`: `coupling_alias['QED']='EW'`,
    `coupling_alias['QED^2']='EW^2'` (`4896-4897`).
  - if `'aEW' not in model_orders`: `coupling_alias['aEW']='EW^2=2*'` (`4899`).
- elif `'QED' in model_orders`:
  - `coupling_alias['EW']='QED'`, `coupling_alias['EW^2']='QED^2'`
    (`4901-4902`).
  - if `'aEW' not in model_orders`: `coupling_alias['aEW']='QED^2=2*'`
    (`4904`).
- If `'QCD' in model_orders` and `'aS' not in model_orders`:
  `coupling_alias['aS']='QCD^2=2*'` (`4905-4907`).

Note the EW/QED branch is `if/elif` — a model with BOTH EW and QED declared
gets no EW<->QED alias entries at all (takes the EW branch, but QED is present
so no alias added there either; aEW alias still added if absent).

## Rewrite at parse time (`4918-4926`)
```python
if name in coupling_alias:
    name = coupling_alias[name]
    if name.endswith('=2*'):
        name = name[:-3]
        value *= 2
    logger.info("change syntax %s=%s to %s=%s to correspond to UFO model convention", ...)
```
- Plain aliases (`QED`->`EW`, `EW`->`QED`, `QED^2`->`EW^2`, ...) just rename.
- The `=2*` suffix aliases (`aS`, `aEW`) strip `=2*` AND double the value:
  user `aS=N` becomes `QCD^2=2N`. i.e. `aS` is a squared-order alias for QCD at
  double value (a power of alpha_s = 2 powers of g_s).
- Logged via `logger.info("change syntax ...")` at info level.

## Consequence for which dict it lands in
After alias rewrite, the (possibly renamed) `name` re-enters the normal
dispatch. So `aS=2` -> name `QCD^2`, value 4 -> goes to `squared_orders['QCD']`.
`aEW=1` -> `EW^2`/`QED^2` value 2 -> squared order on the EW/QED basename.

## CAUTION: plain amplitude alias is stored under the ORIGINAL name
For a PLAIN (non-`=2*`) amplitude alias the rewritten name is used only for
VALIDATION, then overwritten back to the original. Trace `QED=2` in a model
that has `EW` but not `QED`:
1. `4916`: name=`QED`, value=2.
2. `4918-4926`: alias rewrite -> name=`EW` (no `=2*`, value stays 2).
3. `4927`: `EW` is not `^2` -> amplitude branch.
4. `4942-4944`: validity check uses name=`EW` (passes, EW is in model_orders).
5. **`4948`: `name = order_re.group('name')` RE-READS the regex -> name back to
   `QED`.** `4949` re-reads value too.
6. `4954`: `orders['QED'] = 2` — stored under the ORIGINAL alias key, not `EW`.

So plain amplitude aliases validate against the model order but land in `orders`
keyed by the alias the user typed. (The `=2*` aliases `aS`/`aEW` never hit this:
they rewrite to a `^2` name and take the squared-order branch at `4927`, which
does NOT re-read name/value, so their doubling survives. Squared-order plain
aliases like `QED^2`->`EW^2` also keep the rewritten `basename` since `4928`
derives `basename` from the already-rewritten `name`.) Pretraining would not
predict this asymmetry between the amplitude and squared branches.
