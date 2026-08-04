---
description: How the default_unset_couplings option silently caps every unconstrained model coupling once any order constraint is set in extract_process.
---

# `default_unset_couplings` — silent capping of unconstrained couplings

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `extract_process`
`4970-4980`, fired AFTER the per-constraint `while order_re` loop and BEFORE the
LO-only / squared-but-no-orders / assembly blocks.

## What it does (`4970-4980`)
```python
if self.options['default_unset_couplings'] != 99 and (orders or squared_orders):
    to_set = [name for name in self._curr_model.get('coupling_orders')
              if name not in orders and name not in squared_orders]
    if to_set:
        logger.info('the following coupling will be allowed up to the maximal '
                    'value of %s: %s' % (self.options['default_unset_couplings'],
                    ', '.join(to_set)), '$MG:BOLD')
    for name in to_set:
        orders[name] = int(self.options['default_unset_couplings'])
```
- Gate: fires ONLY when (a) the option `!= 99` AND (b) at least one order OR
  squared order was set on this process. A process with NO order constraints is
  untouched.
- For every model coupling not already in `orders` and not in `squared_orders`,
  it writes `orders[name] = N` (the option value). i.e. it converts "unset"
  couplings into an explicit `<= N` amplitude bound.
- Logged at INFO with `$MG:BOLD`: `the following coupling will be allowed up to
  the maximal value of N: <coupling list>`.

## The sentinel: `99 == infinity`
- Default value `99` (`3112`: `'default_unset_couplings': 99, # 99 means infinity`).
- `99` is the OFF sentinel — the gate `!= 99` skips the whole block, so by
  default unconstrained couplings stay genuinely unbounded (MadGraph picks the
  natural leading order). The number 99 is not itself written anywhere; it just
  means "do nothing here."
- Registered as a valid set-option (`3032`, in the `_valid_options`-style list)
  and settable at runtime via `set default_unset_couplings N`
  (`set2_default_unset_couplings`, `8183-8191`). Stored as `int`.

## CAUTION: silent physics change (PROBE-CONFIRMED)
This is the non-obvious trap. Once the user sets the option non-99, declaring
ANY single order constraint silently bounds EVERY other coupling — which can
delete the dominant production mode without an error.

Probe (sm, v3.7.1), script `set default_unset_couplings 0` then
`generate p p > t t~ QED=2`:
```
Interpreting 'QED=2' as 'QED<=2'
the following coupling will be allowed up to the maximal value of 0: QCD
INFO: Trying process: g g > t t~ QCD=0 QED<=2 @1
INFO: Trying process: u u~ > t t~ QCD=0 QED<=2 @1
```
- Only `QED=2` was typed, yet `QCD=0` was injected onto every subprocess.
- `g g > t t~ QCD=0` survives in the trial list (QCD=0 forces a pure-EW path),
  and the surviving kept processes are the EW `q q~ > t t~` ones — the standard
  QCD `t t~` production (`QCD=2`) is silently excluded.
- The only on-screen signal is the INFO line; there is no warning or error.

## Interaction with this slice's other mechanisms
- Writes into `orders` only (never `squared_orders` / `constrained_orders`), so
  the injected bounds are plain `<=` amplitude orders. They participate normally
  in everything downstream (e.g. the squared-but-no-orders fallback at `4994`
  will NOT fire afterwards because `orders` is now non-empty).
- A coupling already squared-constrained is in `squared_orders` so it is NOT
  re-bounded here (the `name not in squared_orders` guard).
- `WEIGHTED` is NOT a `coupling_orders` key, so it is never auto-set by this
  block (it iterates `self._curr_model.get('coupling_orders')`, not the
  parser's WEIGHTED whitelist).

## Boundary
The option's CONSUMPTION inside order parsing is this slice. What "the natural
leading order" would have been absent the cap (i.e. the diagram-level coupling
powers) is diagram-enumeration / model territory; this page only documents that
the cap is applied and what value lands in `orders`.
