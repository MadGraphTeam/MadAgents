---
description: How coupling-order constraints flow (or not) from the core to comma-separated decay sub-fragments — @N proc_number stays on the core, overall_orders dropped by parser then re-propagated by amplitude layer AND pruned again on combined diagrams (3 enforcement points), avoid_squared_orders differs core-vs-decay.
---

# Coupling-order constraints through the decay chain

Source: MG5_aMC v3.7.1. This page is the order-constraint half of "parser-acceptance vs amplitude-attachment": the comma parser treats the core and the sub-decays *asymmetrically* for orders, and a second (amplitude-layer) step partially reverses one of those asymmetries. None of comma-parser.md / onshell-* pages covered orders.

## The parser's asymmetry (extract_decay_chain_process, madgraph_interface.py:5661-5749)

Three things the parser does differently for the **core** vs each **sub-decay**:

| | core process | each comma sub-decay |
|---|---|---|
| call site | `extract_process(line[:min_index], proc_number, overall_orders, avoid_squared_orders=True)` (:5690-5691, :5693-5694) | bare `extract_process(line[:min_index])` (:5726) / `extract_process(line)` (:5728) |
| `proc_number` (`@N`) | passed in | **default 0** — not passed |
| `overall_orders` | passed in | **`{}`** — not passed |
| `avoid_squared_orders` | `True` | **`False`** (the default) |

The `@N order=val` overall-orders are parsed only once, against the *whole* line, at the top of `extract_decay_chain_process` (:5666-5679) — the regex `^(.+)@\s*(\d+)\s*((\w+\s*\<?=\s*\d+\s*)*)$` strips a trailing `@N QCD=2 ...` and builds `overall_orders`. That dict and the `proc_number` go to the **core only**. The nested recursion at :5714-5716 also passes neither, so the asymmetry holds at every level.

### What `avoid_squared_orders=True` (core) vs `False` (decay) means
In `extract_process` (madgraph_interface.py:4955-4965): a constrained order written with `==` or `>` (e.g. `QCD==2`) auto-generates a *squared-order* entry `squared_orders[name] = (2*value, type)` **only when `avoid_squared_orders` is False**. So:
- Core of a decay chain (`avoid_squared_orders=True`): `==`/`>` constrained orders do NOT spawn a squared-order. (The squared-order would otherwise apply to the *combined* amplitude, which the decay-chain machinery handles separately — hence suppressed on the core.)
- Sub-decays (`avoid_squared_orders=False`, the default): `==`/`>` in a decay fragment's own order spec WOULD spawn squared orders for that fragment. (A decay's own `==` order constraint is rare, but the path is live.)

This is a genuine core-vs-decay difference baked into the two call sites, not a uniform treatment.

## The amplitude layer re-propagates overall_orders (diagram_generation.py:1380)

The parser dropping `overall_orders` on sub-decays is **not** the final word. In `DecayChainAmplitude.__init__`, the loop over `argument.get('decay_chains')` (diagram_generation.py:1377-1389) does, for each decay process, *before* wrapping it in its own `DecayChainAmplitude`:
```python
process.set('overall_orders', argument.get('overall_orders'))   # :1380
```
So each decay sub-process inherits the **parent's** `overall_orders` at amplitude-build time. Because each child is then wrapped in its own `DecayChainAmplitude(process, ...)` (:1386-1389) whose `__init__` runs the same loop over *its* decay_chains using the `overall_orders` just set, the propagation **cascades recursively down the full decay tree**.

Then `Amplitude.__init__` / generate_diagrams setup (diagram_generation.py:570-577) applies it:
```python
for key in process.get('overall_orders').keys():
    try:    process.get('orders')[key] = min(process.get('orders')[key], process.get('overall_orders')[key])
    except KeyError:  process.get('orders')[key] = process.get('overall_orders')[key]
```
i.e. each order is capped to `min(orders, overall_orders)` per key, adding the key if absent. So the `@N order=val` cap reaches every decay sub-amplitude.

### proc_number does NOT get re-propagated
Line 1380 propagates `overall_orders` only; there is no analogous `process.set('id', ...)` for the sub-decays. So `@N`'s **order constraint** flows to the decays via the amplitude layer, but `@N`'s **proc_number** stays on the core (decays keep id 0). The two halves of `@N QCD=2` travel by different paths.

## Probe confirmation (MG5_aMC v3.7.1)
`generate p p > t t~, (t > b w+, w+ > e+ ve), t~ > b~ w- @1 QCD=2; output` logs:
```
INFO: Trying process: g g > t t~ QCD<=2 @1 QCD=2
INFO: Trying process: t > b w+ QCD<=2 @0 QCD=2
INFO: Trying process: w+ > e+ ve QCD<=2 @0 QCD=2
INFO: Trying process: t~ > b~ w- QCD<=2 @0 QCD=2
```
Every fragment — core and all three decays — carries `QCD<=2` (the overall_orders cap), confirming amplitude-layer re-propagation. The decays show `@0` (proc_number NOT propagated) while the core shows `@1` — confirming proc_number and overall_orders travel by different paths. The `<=` form (not `==`/`>`) is consistent with the overall-orders cap rather than a squared-order. (decayBW.inc for this process: t/w+/t~-side mothers `/1/`, undecayed mother `/0/` — matches onshell-as-single-source.md value-1 nesting case.)

## A THIRD enforcement: combined-diagram prune at splice time (helas_objects.py:3985-4006)
The `@N` overall cap is enforced not only at parse (dropped) and amplitude build (per-fragment `min`, :570-577) but AGAIN on the *combined* matrix element. After `insert_decay_chains` splices all decays, it re-checks every combined diagram's `calculate_orders()` against `overall_orders` and pops any that exceed the cap (helas_objects.py:3985-4002), then renumbers (:4006-4026). So a combined diagram whose core-orders + decay-orders SUM exceeds `@N QCD=k` is dropped at splice time — the per-fragment caps alone don't catch the sum. See combine-decay-chain-layer.md.

## Why this matters for answering questions
- "I put `@1 QCD=2` after a decay chain — does the QCD cap apply to the decays too?" → Yes, via the amplitude layer (diagram_generation.py:1380 + 570-577) AND the combined-diagram prune (helas_objects.py:3985-4002), NOT the parser. The parser hands sub-decays `overall_orders={}`; do not conclude from the parser alone that decays are uncapped. The combined cap applies to the SUM of core + decay orders.
- A *per-fragment* order spec inside a decay (e.g. `t > b w+ QCD=1`) is parsed by that fragment's own bare `extract_process` and lands in its `orders` directly — independent of the overall `@N` cap, which is then `min`-combined on top.
- proc_number (`@N`) is a core-only label for decay chains; don't expect decays to carry the user's process number.
