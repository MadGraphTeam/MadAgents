---
description: Full surface-form taxonomy of nested sub-decay parenthesisation (H>tt, each t>bW): 6/7/8-diagram outcomes by paren placement, discarded-warning cardinality, subprocess suffix + decayBW.inc fingerprint, incl. the 7-diagram partial-leak mode.
---

# Nested sub-decay parenthesisation — the full surface-form taxonomy

Source: MG5_aMC v3.7.1. Probe-confirmed (`import model sm`, target spec
`p p > z h, (z > e+ e-), (h > t t~, (t > b w+), (t~ > b~ w-))`).

The OUTER paren around a decay is the load-bearing element that scopes/binds its
sub-decays. This page enumerates EVERY surface form for one nested sub-decay
(`h > t t~` with each top further decaying) and its outcome. The three
discriminators are: **diagram count (6/7/8)**, the **`Decay information for
particle(s) … is discarded` warning** (presence + cardinality), and the
**subprocess-dir suffix**. (For the mechanism — why a sub-decay binds or is
discarded — see comma-parser.md §B, onshell-flag-and-decayBW.md case 1, cautions.md §2.)

## The six surface forms (probed verbatim)

| # | Surface form (after `..., (z > e+ e-),`) | Diag | Warning | Subproc suffix |
|---|------------------------------------------|------|---------|----------------|
| 1 | `(h > t t~, (t > b w+), (t~ > b~ w-))` (doubly-nested) | **8** | none | `…_h_ttx_t_bwp_tx_bxwm` |
| 2 | `(h > t t~, t > b w+, t~ > b~ w-)` (outer paren, inner commas) | **8** | none | `…_h_ttx_t_bwp_tx_bxwm` |
| 3 | `(h > t t~, (t > b w+, t~ > b~ w-))` (outer correct, inner paren groups BOTH) | **7** | once, singular `t` | `…_h_ttx_t_bwp` (NO `_tx_bxwm`) |
| 4 | `h > t t~, t > b w+, t~ > b~ w-` (comma-only, no outer paren) | **6** | once, plural `t,t` | `…_h_ttx` |
| 5 | `h > t t~, (t > b w+, t~ > b~ w-)` (inner paren only, no outer) | **6** | TWICE, singular `t` each | `…_h_ttx` |
| 6 | `h > (t t~, t > b w+, t~ > b~ w-)` (open paren after `h >`) | — | `InvalidCmd : No particle (t in model` | no output |

### Forms 1 & 2 — the valid equivalents (8 diagrams)
The OUTER paren on `h > t t~` scopes the sub-decays to the H-decay level; whether
the two top sub-decays are each separately parenthesised (form 1) or just
comma-separated inside the outer paren (form 2) is irrelevant — **both bind both
tops, 8 diagrams, identical subprocess suffix `_t_bwp_tx_bxwm`, identical combine
block.** `decayBW.inc`: FIVE lines — `GFORCEBW(-1..-4,1)/1/` (Z, H, t, t̄ mothers
forced-BW) + `GFORCEBW(-5,1)/0/` (production-graph propagator). The inner
`(t > b w+)` with no further chain is flattened inline by the parser's
special-case splice (madgraph_interface.py:5703-5708), so form 1 ≡ form 2.

### Form 3 — the 7-diagram PARTIAL-LEAK (most pernicious)
`(h > t t~, (t > b w+, t~ > b~ w-))`: the outer paren correctly scopes to the
H-decay, but the inner paren groups BOTH top sub-decays into ONE recursed block.
That inner block's recursion has core `t > b w+` (final-state legs b, w+) and a
SIBLING decay `t~ > b~ w-`; the inner core has no `t~` leg, so the `t~` sub-decay
is discarded by the missing-core-parent rule (diagram_generation.py:1399-1424).
**Only ONE top binds** → 7 diagrams; warning fires ONCE, singular `t` (one id
left in decay_ids); subprocess suffix `_t_bwp` WITHOUT `_tx_bxwm`. `decayBW.inc`:
FOUR lines — `GFORCEBW(-1..-3,1)/1/` (Z, H, the ONE bound top) + `GFORCEBW(-4,1)/0/`
(production propagator), i.e. exactly ONE fewer `/1/` line than the valid form.
This is the trap: it looks correctly parenthesised, runs clean (exit 0), produces
a topologically-real ME with one top fully showered and the OTHER as an ME-level
external — only the diagram count / suffix / decayBW fingerprint reveal the leak.

### Forms 4 & 5 — the full drop (6 diagrams)
With NO outer paren on `h > t t~`, both `t > b w+` and `t~ > b~ w-` are siblings
of the TOP-LEVEL core (`p p > z h`), which has no t/t̄ final-state leg → both
discarded. Both top sub-decays become ME-level externals → 6 diagrams, suffix
`_h_ttx` (no top decay at all). The two forms differ only in warning shape:
- Form 4 (comma-only): ONE warning, plural `Decay information for particle(s) t,t is discarded.` (both ids reported in one call).
- Form 5 (inner paren grouping both, no outer): the inner paren recurses, so each discarded sub-decay is reported separately → warning fires TWICE, each singular `t`.

So **warning cardinality + plural-vs-singular distinguishes form 4 from form 5
even though both yield 6 diagrams.** An inner paren without an outer paren does
NOT rescue the binding — it only changes how the discard is reported.

### Form 6 — loud parser reject (tokenization)
`h > (t t~, t > b w+, …)`: the `(` immediately after `>` makes `(t` the first
token of the core-process fragment handed to `extract_process`, which fails model
lookup → `InvalidCmd : No particle (t in model`. No output. The token-level
reason (`(t` is not a model particle name) is process-syntax / tokenization
slice's territory — cross-reference, do not claim the message. From this slice's
view: a paren may NOT open a core-process fragment; it may only follow a comma to
open a nested decay level.

## Discriminator summary (operative takeaway)
The absolute diagram counts (6/7/8) and the suffix strings below are SPECIFIC to this `p p > z h`, `h > t t~` topology — they are NOT a lookup table for other processes. The transferable rule is RELATIVE: each unbound top removes one diagram AND one `/1/` line versus the fully-bound form, whatever that form's count is. Derive the fully-bound count per topology (probe); read leak/drop as decrements from it. See decay-binding-is-scope-times-match.md.

For THIS topology, same final-state intent gives FOUR distinct outcomes by paren placement:
- **8 diag + no warning + `_t_bwp_tx_bxwm`** = both tops bound (correct; forms 1, 2).
- **7 diag + 1 singular `t` warning + `_t_bwp`** = ONE top leaked (form 3 — verify this when a nested chain "ran clean" but the σ/topology looks off).
- **6 diag + warning (`t,t` once OR `t` twice) + `_h_ttx`** = both tops dropped (forms 4, 5).
- **`InvalidCmd : No particle (t in model`** = paren opened a core fragment (form 6).

Never count commas/parens to predict binding — read the diagram count, the
discard warning cardinality, the subprocess suffix, and confirm with decayBW.inc
(`/1/` lines = bound mothers). See cautions.md §2 for the discard mechanism and
onshell-as-single-source.md for the decayBW value rule. This page is the nested-`h>tt`
surface-form instance of the general BINDING rule in
decay-binding-is-scope-times-match.md (binding = paren-scope × pdg-match, read by
fingerprint) — the 6/7/8-diagram outcomes are exactly its bind/leak/drop trichotomy.
