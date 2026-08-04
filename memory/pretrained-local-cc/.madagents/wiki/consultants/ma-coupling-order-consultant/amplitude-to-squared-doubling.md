---
description: The 2N principle — a squared amplitude carries twice the coupling power of the amplitude, encoded in extract_process as a "double the value" rule fired at three syntactic triggers (=2* aliases, == propagation, > propagation).
---

# Amplitude-to-squared coupling-power doubling (the 2N rule)

A squared amplitude carries TWICE the coupling power of the amplitude: an
amplitude with N powers of a coupling g produces |M|^2 with 2N powers. Every
place `extract_process` derives a `squared_orders` entry from an
amplitude-level intent doubles the value. These `*2` coupling-power sites live in
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` (currently 4924,
4958, 4965 — re-run `grep 'value *= 2' / '2 * value'` to confirm the set is
unchanged before relying on the coordinates). This page names the single physical
relationship that makes all three cohere; the per-trigger mechanics live in
`coupling-aliases.md` and `equals-interpretation-and-strict-equality.md`.

## The three doubling triggers (all in `extract_process`)

1. **`=2*` alias doubling (`4922-4924`)** — user writes an alpha-style
   coupling (`aS`, `aEW`). The alias value ends `=2*`; the suffix is stripped
   and `value *= 2`, so `aS=N` -> `QCD^2=2N`, `aEW=N` -> `EW^2`/`QED^2`=2N.
   Physics: one power of alpha_s = g_s^2 = two powers of g_s; the user already
   spoke in squared-amplitude-natural (alpha) units, so the stored squared
   order is double. (Detail page: `coupling-aliases.md`.)

2. **`==` strict-equality propagation (`4957-4958`)** — an amplitude
   `name==value` auto-spawns `squared_orders[name] = (2*value, '==')` (unless
   `avoid_squared_orders`). Physics: requiring exactly N powers in the amplitude
   means exactly 2N in the squared amplitude.

3. **`>` propagation (`4962-4965`)** — same auto-spawn with type `'>'`:
   `squared_orders[name] = (2*value, '>')`.
   (Triggers 2-3 detail page: `equals-interpretation-and-strict-equality.md`.)

## Why this is one principle, not three coincidences

All three carry the SAME relationship — the squared ME has double the coupling
power of the amplitude — applied at different entry points:
- Trigger 1: the user expressed the constraint in alpha (squared) units; MG
  converts the alpha-power to its g-power-squared = 2N.
- Triggers 2-3: the user expressed an amplitude equality/floor; MG DERIVES the
  squared-amplitude equality/floor at 2N.

So `aEW=1` and `EW==1`-followed-by-its-spawn both land a squared order at 2 on
the EW basename — the same 2N arithmetic reached two ways. The numeric match
(both produce `2`) is not a coincidence; it is the one physical fact stated
twice in the grammar.

## Boundary — this is a STORED-VALUE claim, not a runtime prediction
The 2N rule governs what integer lands in `squared_orders` at parse time. It
makes no claim about diagram counts or cross sections. The downstream
consequences of those stored values (e.g. a doubled-negative squared order
deciding which validation layer fires) are probe-confirmed in
`two-layer-order-validation.md`; this page is the parse-side root they share.

## Coverage beyond the instances
A future alpha-style alias (any `coupling_alias` entry ending `=2*`) or a future
amplitude operator that derives a squared order would route through this same
2N rule. The principle catches them without a new page; the instance pages,
scoped to today's `aS`/`aEW`/`==`/`>`, would not.
