---
description: Negative coupling-order values as the N^(-I+1)LO term selector, and the four parse/storage mechanisms a negative value triggers.
---

# Negative coupling-order values

A negative coupling-order value is not an error — it is a deliberate selector
for a sub-leading term in the order expansion. The four scattered mechanisms in
the parse all stem from this one meaning, so this page names the principle and
ties them together (instances live across `order-parsing-overview.md`, plus one
site that no existing page covers).

## Physics meaning (help text, verbatim)
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` `615-616`:
> a negative value `COUP^2==-I` refers to the `N^(-I+1)LO` term in the
> expansion of the COUP order.

So `QED^2==-1` -> the (-1+1)=0 -> LO term; `QED^2==-2` -> NLO term; etc. The
negative value indexes how many orders below the leading contribution to keep.
This is a squared-order concept (it selects an interference/expansion term).

## The regex admits negatives
The `value` group is `-?\d+` (`4885`), so a leading minus is captured rather
than rejected at parse. Without this the negative-selector syntax would never
reach the dispatch.

## Four consequences once a negative value is stored
All in `extract_process` unless noted; `value` is the parsed integer.

1. **Stored as-is** into `squared_orders[basename]=(value,type)` (`4940`) for a
   `^2` name, or `orders[name]=value` (`4954`) for an amplitude `=`/`<=`. No
   special-casing at store time.

2. **squared-but-no-orders fallback inverts to "leading unknown"**
   (`4994-4999`): when `orders=={}`, `squared_orders!={}` and no perturbation
   couplings, each squared order normally seeds `orders[order]=value` — BUT if
   `value<0` (or type `'>'`), it seeds `orders[order]=99` instead, because a
   sub-leading selector gives no usable amplitude-level bound (cannot know at
   generation time whether a diagram is leading).

3. **Two distinct negative-order ceilings** (both fire, at different layers):
   - **Inside `extract_process` (`5330-5332`)**: after splitting `squared_orders`
     into `sqorders_values`, if >1 squared value is `<0` ->
     `InvalidCmd("At most one negative squared order constraint can be specified.")`.
     This counts SQUARED orders only.
   - **In the caller, after the procdef is built (`do_add` `3342-3346`,
     `do_generate` `5414-5418`)**: scans `orders` values AND `squared_orders`
     values TOGETHER; if more than one combined is `<0` ->
     `MadGraph5Error("Negative coupling order constraints can only be given on
     one type of coupling and either on squared orders or amplitude orders, not
     both.")`. So at most ONE negative value total across both dicts, and you
     cannot put a negative on both an amplitude order and a squared order.
   Net: you can index exactly one sub-leading term, on one coupling, in one dict.

4. **Decay processes reject ALL negative orders** — BOUNDARY: enforced in
   decay-chain handling (`3305-3307`,
   `MadGraph5Error("Decay processes cannot include negative coupling orders
   constraints.")`) via `ProcessDefinition.are_negative_orders_present()`
   (`$MADGRAPH_INSTALL/madgraph/core/base_objects.py` `3554-3566`), which scans
   `orders` + `squared_orders` values (the dicts THIS slice fills) and recurses
   into `decay_chains`. The value originates in this slice's parse; the
   decay-time enforcement is decay-chain territory. Note `3301-3304` likewise
   bans any squared-order constraint in decays — negative-order rejection is the
   stricter sibling rule.

## Why this is a generalization, not a restatement
Three of the four sites already appear in `order-parsing-overview.md` but as
unrelated lines in three different sections (regex / fallback / assembly);
consequence (4) and the physics meaning (`615-616`) appear in NO existing page.
The principle "a negative value is a sub-leading-term selector" is what makes
all four cohere, and it catches the decay-rejection case the instance pages miss.
