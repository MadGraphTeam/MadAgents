---
description: Coupling orders under model import — plugin/merged custom orders parse identically; model_orders is VERTEX-derived (get_coupling_orders base_objects.py:1374) not declaration-derived, so a coupling_orders.py-declared-but-unused order (hgg_plugin QED) HARD-ABORTS at the 4942 gate (not silent zero); effective-vertex selection via explicit orders; add-model min-merge premise; expansion_order model cap; decay-chain per-subprocess order independence.
---

# Coupling orders under model import (plugin / merged / effective-vertex)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `extract_process`
unless noted.

## Custom / plugin / merged order names parse identically
`model_orders = self._curr_model.get('coupling_orders')` (`4893`). Any order the
loaded model carries — `HIG`, `HIW`, `NP`, `DIM6`, `FCNC` — is an accepted
amplitude-order name with NO special-casing: the amplitude branch requires only
`name in model_orders or name=='WEIGHTED'` (`4942`), else `InvalidCmd` listing
the valid set (`4943-4944`; that message's PREFIX order is non-deterministic —
see MEMORY). So `HIG=1` is parsed exactly like `QED=1`. No per-model parser code.

### `model_orders` is VERTEX-derived, not declaration-derived (SEAM)
`get_coupling_orders` (`base_objects.py:1374`) returns
`set(sum([list(i.get('orders').keys()) for i in <interactions>], []))` — the set
of order names that appear on the model's **interactions**, NOT the set of
`CouplingOrder` names declared in `coupling_orders.py`. An order declared in
`coupling_orders.py` but carried by NO surviving vertex is therefore ABSENT from
`model_orders`, so the `4942` gate rejects it. The derivation site
(which vertices carry which orders, and how restriction prunes them) is
model-loader/ufo/restriction territory; my slice owns only that the gate reads
this vertex-derived set. (The `aS` that also appears in the valid-set MESSAGE is
not a model order at all — it is a `coupling_alias` key, since the raise uses
`valid = list(model_orders) + list(coupling_alias.keys())`; see
`coupling-aliases.md`.)

### An undeclared/unused order token HARD-ABORTS — it is NOT a silent zero-cap
`if name not in model_orders and name!='WEIGHTED': raise self.InvalidCmd(...)`
(`4942-4944`) is a hard raise with no fallthrough — an order name the loaded
model does not carry does NOT get silently stored as `orders[name]=0`. Contrast
the declared-order `X=0` path (silent, stores `0`, `effective-vertex` section
below). PROBE-CONFIRMED (v3.7.1, generate-only): `import model hgg_plugin`
(standalone) then `generate g g > h HIG=1 HIW=0 QED=0 QCD=0` →
`InvalidCmd: model order QED not valid for this model (valid one are:
HIW, QCD, HIG, aS)` — even though `hgg_plugin/coupling_orders.py` DOES declare a
`QED` `CouplingOrder` (expansion_order=99). QED is rejected because no standalone
hgg_plugin vertex carries a QED order, so it never enters the vertex-derived
`model_orders`. Dropping the `QED=0` token (`generate g g > h HIG=1 HIW=0
QCD=0`) parses to 1 diagram (all three tokens are carried orders). hgg_plugin is
a PLUGIN meant to be `add model`-merged onto a base (sm/BSM) whose QED-carrying
vertices supply the QED order; only on the merged model does the
`... QED=0 QCD=0` command parse. CAUTION: do NOT reason "the model declares
order X in coupling_orders.py, therefore `X=N` is accepted" — acceptance follows
the vertex-derived set, not the declaration.

## Effective-vertex selection: `generate g g > h HIG=1 HIW=0 QED=0 QCD=0`
NOTE: this doc-style command needs `QED` in `model_orders`, so it presumes a
MERGED model (hgg_plugin `add model`-ed onto a QED-carrying base). On STANDALONE
hgg_plugin the `QED=0` token hard-aborts (see the vertex-derivation caution
above); use `generate g g > h HIG=1 HIW=0 QCD=0` there.
`models/hgg_plugin/coupling_orders.py` DECLARES `HIG`/`HIW` (a FINITE
`expansion_order` — read the value there) and `QCD`/`QED` (the `99` no-cap
sentinel) — but declaration ≠ membership in the vertex-derived `model_orders`. Parsing (each via
the back-to-front `order_pattern` loop):
- `HIG=1`: amplitude `=`, value!=0 -> `logger.warning("Interpreting 'HIG=1' as
  'HIG<=1'")` (`4951-4953`), stores `orders['HIG']=1`.
- `HIW=0`, `QED=0`, `QCD=0`: amplitude `=`, value==0 -> SILENT (no warning,
  the `value != 0` guard at `4951` is false), stores `orders[..]=0`.
- Net: `orders={HIG:1, HIW:0, QED:0, QCD:0}`. Selecting `HIG<=1` while forbidding
  any QED- or QCD-carrying vertex isolates the effective ggH (HIG) vertex and
  excludes the QCD/QED loop or tree paths. All four are ordinary amplitude
  caps; the "effective vertex" is an emergent consequence of the caps, not a
  parser mode.

## `expansion_order` model cap (SEAM — diagram-enum consumes, mutates `orders`)
`Process.check_expansion_orders` (`base_objects.py:3757-3785`), run during
generation:
```python
tmp = [(k,v) for (k,v) in expansion_orders.items() if 0 < v < 99]
for (k,v) in tmp:
    if k in orders:
        if v < orders[k]: ... orders[k] = v      # cap down, with warning
    else:
        orders[k] = v                            # inject cap even if unset
```
- Only bites when the model set `0 < expansion_order < 99` for an order
  (default is `-1` per order, `base_objects.py:1233-1234` -> no cap; hgg_plugin's
  finite `HIG`/`HIW` cap DOES bite — read the value in `coupling_orders.py`).
- Consequence for the effective vertex: even without an explicit `HIG`,
  `expansion_order['HIG']` (its finite cap) injects `orders['HIG']=<that cap>`
  (the `else` branch), so the model builder caps HIG insertions automatically.
- This is a POST-PARSE silent mutation of the `orders` dict THIS slice filled;
  it is diagram-enumeration's site, not mine. It is also why `QED=99` does not
  override a low per-order model ceiling (only the WEIGHTED heuristic — see
  `split-orders-and-weighted.md`).

## `add model` merge takes the MINIMUM (PREMISE — model-loader/ufo owns)
`models/usermod.py:add_coupling_order` (`796-814`): when a merged model
redeclares an existing order name, both `hierarchy` (`802-806`) and
`expansion_order` (`807-811`) collapse to `min(existing, incoming)`, each with a
`logger.warning('... use the minimal value ...')`. A `perturbative_expansion`
order also gets forbidden at NLO (`812-814`). CONSEQUENCE for this slice: the
merged `expansion_order` (a min) feeds `check_expansion_orders` above, so a low
value from either model can cap — hence suppress — plugin vertices in
generation. The merge SITE is model-loader/ufo territory; cited here only as the
premise that sets the numbers my downstream seam consumes.

## Coupling orders in DECAY CHAINS are per-subprocess independent
`extract_decay_chain_process` (`5661`) parses each `>` subprocess with its OWN
recursive `extract_process` call, each producing its own
`orders`/`squared_orders`/`constrained_orders` dicts:
- Core process: `extract_process(..., avoid_squared_orders=True)` (`5690-5694`)
  — so `==`/`>` on the core does NOT auto-spawn a doubled squared order.
- Each decay: `extract_process(line)` (`5726`/`5728`), default
  `avoid_squared_orders=False`.
- An UNCONSTRAINED decay (e.g. `, h > mu+ mu-`) gets an empty `orders` -> no
  cap -> the `QED`-order Yukawa vertex is found. `default_unset_couplings`
  arms only when THAT subprocess's parse set an order, so an unconstrained
  decay is not silently capped either.
- Explicit orders on a parenthesised decay `(h > mu+ mu- QED=1 HIG=0 HIW=0)`
  are stored in THAT decay's dicts only; they do not leak to the core or to
  sibling decays. Constraint scoping is strictly per-subprocess.
- NOTE: `overall_orders` (trailing `@N QED=0 ...`) is a separate restricted
  channel (only `=`/`<=`, no `^2`/`==`/`>`/negatives) stored verbatim, not
  merged into these dicts — see `order-parsing-overview.md`.
