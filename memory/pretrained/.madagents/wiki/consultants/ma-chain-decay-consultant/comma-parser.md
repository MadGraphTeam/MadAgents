---
description: extract_decay_chain_process — the recursive comma-driven parser that builds a ProcessDefinition with decay_chains; comma-vs-paren scoping; cascade > stays in the core process.
---

# The comma-driven decay-chain parser

Source: `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, MG5_aMC v3.7.1.

## Dispatch — when the decay-chain parser fires
`do_add` / process specification at madgraph_interface.py:3282:
```python
if ',' in line:
    if ']' in line or '[' in line:
        # MadGraph5Error: '[' ']' cannot be used with decay chains
    else:
        myprocdef, line = self.extract_decay_chain_process(line, proc_number=nb_proc)
else:
    myprocdef = self.extract_process(line, proc_number=nb_proc)
```
- The presence of a comma `,` is the sole trigger to enter `extract_decay_chain_process`. No comma → plain `extract_process`, no decay chain.
- Hard incompatibility: a comma together with `[`/`]` (loop / squared-order syntax) raises `MadGraph5Error` (madgraph_interface.py:3283-3289). Decay chains cannot be perturbed or carry squared-order constraints (further checks at :3296-3307).

## extract_decay_chain_process (madgraph_interface.py:5661-5749)
Signature: `extract_decay_chain_process(self, line, level_down=False, proc_number=0)` — "Recursively extract a decay chain process definition... Returns a ProcessDefinition." (:5662-5663)

Step 1 — strip leading process number/orders via `^(.+)@\s*(\d+)\s*((\w+\s*\<?=\s*\d+\s*)*)$` (:5666). Sets `proc_number` and `overall_orders`.

Step 2 — find the first scoping boundary (:5683-5688):
```python
index_comma = line.find(",")
index_par = line.find(")")
min_index = index_comma
if index_par > -1 and (index_par < min_index or min_index == -1):
    min_index = index_par
```
`min_index` = earliest of comma or close-paren. The **core process** is `line[:min_index]` (everything before the first comma/paren), parsed by `extract_process(..., avoid_squared_orders=True)` (:5690-5694). If no boundary, the whole line is the core.

Step 3 — `while index_comma > -1` loop (:5698-5739) walks each comma-separated decay:
- Slice off everything up to and including the comma: `line = line[index_comma + 1:]` (:5699).
- Empty remainder → `break` (:5700-5701).
- **Parenthesised sub-chain**: if the next non-space char is `(` (:5709), strip it and **recurse** `extract_decay_chain_process(line, level_down=True)` (:5714-5716). This is the nested decay-chain mechanism.
- **Special case** (:5703-5708): a leading `(` with a matching `)` but NO comma inside the parens → the parens are stripped and the content is spliced inline (a parenthesised single decay with no further chain is just flattened).
- **Flat decay**: otherwise parse `line[:min_index]` (up to next comma/paren) with `extract_process` (:5719-5728).
- Each parsed decay is appended: `core_process.get('decay_chains').append(decay_process)` (:5730).

Step 4 — `level_down` bookkeeping (:5732-5745) consumes the matching `)` and raises `InvalidCmd("Missing ending parenthesis for decay process")` when a nested level lacks its close-paren.

Returns `(core_process, line)` — `line` is the unconsumed remainder, used by the caller's recursion.

## Comma-vs-paren scoping (the core rule)
- A **comma** separates a parent from its decay at the SAME hierarchy level: `p p > t t~, t > b w+` — `t > b w+` decays the `t` of the core.
- **Parentheses** open a NESTED level: `p p > t t~, (t > b w+, w+ > l+ vl)` — the `w+ > l+ vl` decays the `w+` produced inside the `t` decay, not a core leg. Recursion via `level_down=True` is what binds the inner decay to the inner producer.
- The parser is purely textual: it scans for the earliest `,` or `)`, splits there, and recurses on `(`. It does NOT consult the model to decide scope — scope is determined by the comma/paren structure alone.
- **Scoping vs distribution are orthogonal.** The comma/paren structure decides *which scope* a clause lives in; within that scope a single clause then distributes across EVERY matching-pdg final-state leg (set-based `decay_ids`, not paren count). Comma-only `..., z > e+ e-, z > mu+ mu-` is unambiguous (distinct products, each binds one Z); comma-only `..., w+ > l+ vl` after `p p > t t~` is DISCARDED (parent not a core leg). See clause-distribution-and-topology.md for the distribution rule, the no-implicit-invisible-default corollary, and same-multiset ≠ same-amplitude.

## The cascade `>` does NOT enter this function
`>` is the ordinary process arrow handled inside `extract_process` (the core-process parser). `extract_decay_chain_process` never splits on `>`; it splits on `,`/`)`/`(`. Every `a > b c` fragment (core or decay) is handed whole to `extract_process`. So the cascade operator lives entirely in the core-process amplitude layer; the comma layer only orchestrates which fragments are core vs decay and how they nest.

## How the sub-decay STRING is built and handed off (textual mechanics)
The parser never re-tokenizes a `>` fragment; it carves substrings and hands each whole to `extract_process`. The carving is purely string-index arithmetic:
- **Core string**: `line[:min_index]` where `min_index` = earliest `,`/`)` (:5690). Handed to `extract_process(..., avoid_squared_orders=True)`.
- **Each flat decay string**: after `line = line[index_comma + 1:]` (:5699), the decay is `line[:min_index]` to the next `,`/`)` (:5726), else the whole remainder (:5728). NO `avoid_squared_orders` flag on the sub-decay call — only the core gets it.
- **Paren-strip for a nested sub-chain**: `line = line.lstrip()[1:]` (:5712) drops the leading `(`, then recurse. The recursion's returned `line` is the unconsumed tail.
- **Special-case inline splice** (:5703-5708): a `(...)` with NO comma inside is flattened by string concatenation `'%s %s' % (line[par_start+1:index_par], line[index_par+1:])` (:5707) — the parens vanish and the content is spliced back into `line` as if never parenthesised. So `(t > b w+)` with no inner chain is identical to `t > b w+`.
- **Multiparticle / coupling-order / `@N` in a decay fragment**: the parser does NOT interpret these — they ride inside the carved substring and are resolved by `extract_process` when it parses that fragment (multilabel expansion, order parsing). The comma layer is blind to fragment content beyond `,`/`(`/`)`. (Order/`@N` propagation across core-vs-decay is the orders-through-decay-chain.md slice; the `@N`/orders at the FRONT of the whole line are stripped first at :5666-5680 into `proc_number`/`overall_orders`.)

## Parser-acceptance vs amplitude-attachment
This function only builds the `ProcessDefinition` tree (textual acceptance). Whether a decay actually attaches to a diagram leg — and thus whether `onshell=True` gets set — is decided later in `DecayChainAmplitude` (see `onshell-flag-and-decayBW.md`). Concretely (diagram_generation.py:1391-1424, v3.7.1): `DecayChainAmplitude.__init__` collects `decay_ids` = the incoming-leg id of every decay amplitude (`legs[0].id`, :1392-1395), calls `trim_diagrams(decay_ids)` (:1397) to flag matching CORE final-state legs `onshell=True` (trim_diagrams:1286 on process legs, :1299 on diagram vertex-legs), THEN validates: any `decay_id` not found on a core leg (:1400-1403) triggers the RED "Decay without corresponding particle" warning (:1409-1414) and **removes** that decay amplitude/chain (:1416-1424). A syntactically accepted decay whose parent particle never appears as a core final-state leg is thus discarded, not merely unflagged. Probe: `p p > t t~, t > b w+, w+ > e+ ve` (flat, no parens) warns + discards w+ (8 diagrams); the parenthesised `p p > t t~, (t > b w+, w+ > e+ ve), t~ > b~ w-` parses clean (10 diagrams). See cautions.md §2.
