---
description: Squared-order (^2) and negative-order constraints are rejected in a comma decay-chain line (MadGraph5Error), plus the [/]-with-comma rejection; the two distinct guard sites (do_generate path, NOT extract_process) and why avoid_squared_orders is a separate mechanism.
---

# Decay-chain squared-order rejection

A comma decay-chain line (`p p > t t~, t > b w+`) CANNOT carry squared-order
(`^2`) or negative-order constraints. This is enforced in the `do_generate` /
`do_add` command path (`madgraph_interface.py`), NOT inside `extract_process`,
and NOT by `avoid_squared_orders` (that flag does something else — see below).

## Two guard sites, both fire on a comma line

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, inside the
`if ',' in line:` block (comma ⇒ decay chain present):

1. **`[`/`]` with comma (`3282-3289`)** — earliest guard. If a comma line also
   contains `[` or `]`:
   ```
   The '[' and ']' syntax cannot be used in cunjunction with decay chains.
   This implies that with decay chains:
     > Squared coupling order limitations are not available.
     > Loop corrections cannot be considered.
   ```
   `raise MadGraph5Error`. (sic: "cunjunction".) This blocks the NLO-bracket /
   loop-squared route through decay chains before the procdef is even built.

2. **explicit `^2` in core or any sub-decay (`3301-3304`)** — after
   `extract_decay_chain_process` builds the procdef:
   ```python
   if myprocdef.decays_have_squared_orders() or \
                               myprocdef['squared_orders']!={}:
       raise MadGraph5Error("Decay processes cannot specify "+\
                                 "squared orders constraints.")
   ```
   - `myprocdef['squared_orders']!={}` — the CORE process carries a `^2` order
     (e.g. `p p > t t~ QED^2==2, t > b w+`).
   - `decays_have_squared_orders()` (`base_objects.py 3576-3582`) — recurses the
     `decay_chains` list; returns True if ANY sub-decay procdef has non-empty
     `squared_orders` (e.g. `p p > t t~, t > b w+ QCD^2==2`).
   Adjacent guards in the same block: `are_decays_perturbed()` →
   "Decay processes cannot be perturbed." (`3296-3297`);
   `are_negative_orders_present()` → "Decay processes cannot include negative
   coupling orders constraints." (`3305-3307`).

## Why `avoid_squared_orders` is NOT the enforcement mechanism

`extract_decay_chain_process` calls `extract_process(..., avoid_squared_orders=True)`
for the core AND recursively (`5691`/`5694`). But `avoid_squared_orders` only
suppresses the AUTO-SPAWN of a doubled squared order from an amplitude `==`/`>`
(`4958`/`4965`, `equals-interpretation-and-strict-equality.md`). It does NOT stop
an EXPLICIT `^2` token from populating `squared_orders` — the `^2` branch
(`4927-4940`) ignores `avoid_squared_orders` entirely. So an explicit
`X^2==N` in a decay context DOES land in `squared_orders`, and that is exactly
what the `3301-3304` guard catches at command time. The two mechanisms are
orthogonal:
- `avoid_squared_orders` — silently prevents the `==`/`>` DERIVED squared order
  (so a chain sub-process `NP==1` does not spawn `NP^2==2`).
- `3301-3304` guard — loudly rejects a USER-WRITTEN `^2` (or a core `^2`).

## Scope / boundary
- The `^2` PARSE itself (into `squared_orders`) is this slice; the command-time
  rejection at `3282-3304` is the do_generate/do_add dispatch, also reachable
  from this slice's view since it gates whether a parsed squared order survives.
- The comma-scoping / recursive decay extraction (`extract_decay_chain_process`,
  `5661+`) is chain-decay slice; here only as the producer of the `decay_chains`
  list that `decays_have_squared_orders()` walks.
- Physics reason (a decay's rate/interference is factorized per-sub-process, so a
  squared-ME order on the full chain is ill-defined) is physics-consultant's; the
  source fact is the flat prohibition.

PROBE-CANDIDATE (not yet run): confirm `generate p p > t t~, t > b w+ QCD^2==2`
emits `MadGraph5Error: Decay processes cannot specify squared orders
constraints.` and that `p p > t t~ QED^2==2, t > b w+` (core `^2`) hits the same
line via the `myprocdef['squared_orders']!={}` disjunct.
