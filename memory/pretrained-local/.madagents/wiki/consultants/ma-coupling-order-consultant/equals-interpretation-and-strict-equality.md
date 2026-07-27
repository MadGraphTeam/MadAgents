---
description: How '=' is reinterpreted as '<=' (with warning), and how strict equality '==' and '>' propagate into constrained_orders + squared_orders.
---

# `=` interpretation and strict-equality (`==` / `>`) propagation

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `extract_process`.

## `=` means `<=` (NOT equality)
Two places, both warn:

- Squared orders (`4936-4939`):
  ```python
  if type == '=':
      logger.warning("Interpreting '%(n)s=%(v)s' as '%(n)s<=%(v)s'" ...)
      type = "<="
  ```
  Note: squared-order `=` warns unconditionally (even value 0).

- Amplitude orders (`4950-4954`):
  ```python
  if type in ['=', '<=']:
      if type == '=' and value != 0:
          logger.warning("Interpreting '%(n)s=%(v)s' as '%(n)s<=%(v)s'" ...)
      orders[name] = value
  ```
  Note: amplitude-order `=` warns ONLY when `value != 0`. `X=0` is silent
  (asking for zero of that coupling is unambiguous).

So in BOTH cases `=` stores the value as an upper bound `<=`. The user must
write `==` to get a strict equality constraint. Warning text (verbatim):
`Interpreting 'X=Y' as 'X<=Y'`.

## Strict equality `==` (amplitude) (`4955-4960`)
```python
elif type == "==":
    constrained_orders[name] = (value, type)
    if not avoid_squared_orders and name not in squared_orders:
        squared_orders[name] = (2 * value,'==')
    if True:#name not in orders:
        orders[name] = value
```
- Records `(value,'==')` in `constrained_orders`.
- AUTOMATICALLY adds a squared-order `name^2 = (2*value,'==')` unless
  `avoid_squared_orders` is True or the basename already has a squared order.
  Rationale: amplitude power N -> squared-amplitude power 2N.
- Also sets `orders[name]=value` (the `if True:` is a deliberately-kept
  always-on branch; the `name not in orders` guard is commented out).

## `>` (amplitude) (`4962-4965`)
```python
elif type == ">":
    constrained_orders[name] = (value, '>')
    if not avoid_squared_orders and name not in squared_orders:
        squared_orders[name] = (2 * value,'>')
```
Same auto-squared-order propagation, type `>`. Does NOT set `orders[name]`.

## `avoid_squared_orders` flag
Default `False` (`4823`). Set `True` by decay-chain extraction calls
(`5691`, `5694`) so chain sub-process `==`/`>` constraints do not spawn
squared orders. Outside decay chains it is False, so `==`/`>` always
generate the doubled squared order.

## LO-only restriction (`4983-4985`)
`constrained_orders` (i.e. any `==` or `>` amplitude constraint) is rejected
when `LoopOption != 'tree'`. So strict equality and `>` are LO/tree-only.

## Application: `QCD=0` VBF isolation idiom (PROBE-CONFIRMED)
`generate p p > h j j QCD=0` (sm) is the canonical pure-EW VBF selection.
Mechanics (line-cited above):
- `QCD` value 0, type `=` -> `orders['QCD']=0`, an UPPER BOUND `<=0` (line 4954),
  NOT a `constrained_orders` `==0`. Because `value==0` the `value != 0` guard
  at 4951 SUPPRESSES the "Interpreting 'QCD=0' as 'QCD<=0'" warning -> silent.
- `<=0` and `==0` select the identical amplitude set here (coupling power is
  non-negative, so "at most 0 QCD vertices" == "exactly 0"), but the STORAGE
  differs: `=` leaves `constrained_orders` empty and spawns NO squared order;
  only `==`/`>` populate `constrained_orders` + a doubled squared order.
- PROBE (sm), example for THIS one topology only (derive counts per process
  elsewhere): `p p > h j j QCD=0` -> all-EW quark-quark t/u-channel W/Z-exchange
  (pure EW VBF); gg-initiated subprocesses (`g g > h g g` etc.) ARE tried but
  yield 0 diagrams (no ggH vertex in sm), so they silently drop. No "Interpreting"
  warning printed (confirms the silent path). The version-stable claim is the
  silent `<=0` storage + the all-EW topology, NOT the specific diagram count.

## heft caveat: `QCD=0` does NOT filter Higgs-effective vertices (PROBE-CONFIRMED)
QCD=0 caps only the QCD power. In `heft`, the effective Higgs-gluon vertices
carry their power under a SEPARATE order `HIG` (declared in
`heft/coupling_orders.py` with a finite `expansion_order` — read the value
there), not QCD: the base g-g-h contact is order `{'HIG':1}` (read at
`heft/couplings.py`, QCD=0); the higher contacts add QCD powers
(`g-g-g-h`={'HIG':1,'QCD':1}, etc.). PROBE: `import model heft; generate g g > h
QCD=0` -> the ggh diagram SURVIVES (its vertex is QCD=0). CONSEQUENCE (the
version-stable point, not a count): `p p > h j j QCD=0` in heft does NOT remove
gluon-fusion-effective topologies (they slip through a QCD-only cut via HIG) ->
heft contaminates a VBF selection where sm would not. This is the coupling-order reason behind the "don't use heft for
VBF" warning; the MODEL-CHOICE physics recommendation itself is eft/model-loader.
