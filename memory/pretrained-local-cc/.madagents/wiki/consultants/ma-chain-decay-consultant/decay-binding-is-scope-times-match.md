---
description: Unifying principle for the BINDING question — which final-state legs become decay mothers and which subdecays attach/leak/drop is a function of (paren scope) × (set-based pdg-match), decoupled from syntactic acceptance; predict from the topology fingerprint (diagram count / discard-warning cardinality / subprocess suffix / decayBW /1/-line count), never from comma/paren count. The BINDING-axis sibling of onshell-as-single-source's VALUE-axis rule.
---

# Decay-chain binding = (paren scope) × (pdg-match), read by fingerprint

Source: MG5_aMC v3.7.1. This page lifts the BINDING rule out of `clause-distribution-and-topology.md`, `nested-subdecay-paren-taxonomy.md`, and `cautions.md` §2 — each documents ONE binding situation; this states the rule that answers ANY "does this clause bind / to which legs / did a subdecay leak or drop" question, including nesting depths and clause mixtures the instance pages don't individually enumerate.

This is the **sibling axis** of `onshell-as-single-source.md`. That page answers the VALUE question (given an s-channel mother already in the config, what gForceBW integer does it get → trace the last `onshell` writer). This page answers the **BINDING** question one level earlier: which legs become decay mothers at all, and which subdecays attach. A complete decay-chain answer often needs both: binding (here) decides *which* legs are mothers; value (onshell-as-single-source) decides *what each mother's gForceBW is*.

## The principle — two orthogonal inputs, then a fingerprint readout

A decay clause `X > ...` BINDS exactly when its scope contains a final-state leg of pdg `X`. Two independent inputs decide that, and NEITHER is the comma/paren *count*:

1. **Paren scope (which producer-set a clause is matched against).** The parser is purely textual: parens open a nested decay level, commas separate same-level siblings (`extract_decay_chain_process`, madgraph_interface.py:5709-5716 recursion; comma-parser.md). A clause's scope is the core legs of its enclosing level — top-level clauses match the core process's final state; a clause inside `(...)` matches the leaves of THAT paren's decay. Scope is fixed before any pdg comparison.

2. **Set-based pdg-match within that scope (which legs the clause hits).** `DecayChainAmplitude.__init__` collects `decay_ids = set(...)` of decay-incoming pdg ids (diagram_generation.py:1392-1395). `trim_diagrams(decay_ids)` flags **EVERY** in-scope final-state leg whose id ∈ decay_ids `onshell=True` (:1284-1286 process legs, :1294-1299 diagram walk) — so ONE clause distributes across ALL matching legs (the `h > z z, z > e+ e-` → both Z's case). A leg matched by NO clause stays `onshell=None` (NO implicit invisible-decay default). An id in decay_ids matched by NO in-scope core leg is **discarded** with the RED "Decay without corresponding particle… forgot parentheses" warning and the amplitude/chain is removed (:1399-1424).

**Two miss-modes; the discard-warning is set-membership-gated, so same-type misbinding is SILENT.** The warning at :1409-1414 fires only for ids STILL in `decay_ids` after the loop at :1400-1403 removes every id that matches SOME core final-state leg. Two distinct failure modes of an un-parenthesised flat subdecay:
- **(a) no core leg of that type** → id survives :1403 → RED warning + amplitude removed (:1416-1424). E.g. `p p > t t~, t > b w+, w+ > e+ ve` — id 24 absent from core {6,-6}, discarded (cautions.md §2, probe-confirmed 8 diagrams).
- **(b) a DIFFERENT particle of the same type IS a core leg** → id removed at :1403 → warning SUPPRESSED, and `trim_diagrams` (already run at :1397, BEFORE the check) has flagged that core leg `onshell=True`. So the subdecay binds to the core-produced particle, not the one you meant, with **no warning**. Reachable e.g. `p p > t t~ w+, t > b w+, w+ > e+ ve` — the flat `w+ > e+ ve` binds the *produced* core w+ (id 24 ∈ core), not the w+ from t's decay. Genuinely silent: matching is position-blind set membership (`leg.get('id') in decay_ids`, :1285/:1402), the code has no notion of "which" w+. Fix is parens to scope the inner w+ under t.

**Acceptance is decoupled from binding.** The parser accepts a clause textually (it builds the ProcessDefinition tree) long before `DecayChainAmplitude` decides binding. So "it parsed / ran clean (exit 0)" is NOT evidence a clause bound. The three binding outcomes — **bind** (matched in scope), **leak** (some but not all of a multi-clause nested block matched, partial-attach), **drop** (no in-scope match, discarded) — are all reachable from syntactically-valid input.

## The fingerprint — read the topology, never the syntax

Because acceptance ≠ binding, you cannot predict binding by counting commas/parens. The OPERATIVE readouts (all probe-confirmed in the instance pages, MG5_aMC v3.7.1):

The readouts are RELATIVE — read a form against the *fully-bound* form of the SAME topology, never against a remembered absolute integer. Absolute diagram/leaf/`/1/`-line counts are topology-specific; derive them per process (probe), do not cache a number.

| Readout | Derivation rule (relative to the fully-bound form of the SAME topology) |
|---------|-------------------|
| **Diagram count** | each unbound (leaked/dropped) mother removes its decay sub-graph → FEWER diagrams than fully-bound; the *decrement per unbound mother* is what discriminates bind/leak/drop, not any absolute value. (Example — this one topology only: nested `h>tt` fully-bound=8, one top leaked=7, both dropped=6; derive per process for anything else. nested-subdecay-paren-taxonomy.md.) |
| **Discard-warning cardinality + plural/singular** | how many ids dropped and via which paren shape — one plural warning listing all ids (comma-only flat) vs one singular warning per id (inner-paren-no-outer); presence at all = a drop happened (clause-distribution §B note; nested-paren forms 3/4/5). |
| **Subprocess-dir suffix** | which decays attached — a `_<mother>_<products>` segment appears for each BOUND decay, absent for a leaked/dropped one (`_t_bwp_tx_bxwm` both tops, `_t_bwp` one=leak, `_h_ttx` none). Encodes legs_with_decays (legs-with-decays.md). |
| **decayBW.inc `/1/`-line count** | exactly one `/1/` per bound decay mother — so one fewer `/1/` line per unbound mother relative to the fully-bound form (decayBW-artefact.md, nested-paren form 3). Production/off-shell propagators are `/0/`. |

To answer ANY binding question: fix each clause's scope from the paren structure, set-match it against that scope's final-state pdgs, then CONFIRM with the RELATIVE diagram-count/warning/suffix/decayBW fingerprint against the fully-bound form. Never assert binding from the command line alone, and never from a remembered absolute count.

## Decision procedure

1. **For each clause, determine its scope** — top-level (matches core final state) or inside a paren (matches that paren's decay leaves). Recursion depth = paren nesting.
2. **Set-match the clause's incoming pdg against in-scope final-state legs.** Matched (≥1 leg of that pdg in scope) → binds, distributing to ALL such legs. Unmatched → discarded with warning, parent stays a leaf.
3. **Same-pdg clauses distribute; distinct-product clauses each bind their producer.** `z>ee` alone on a 2-Z core → both Z's same decay (4 same-flavour leptons); `z>ee, z>mumu` → one each.
4. **Confirm by fingerprint** (diagram count / warning cardinality / suffix / decayBW `/1/` count) — never by comma/paren count.

## Boundary (what this page does NOT own)
- The **gForceBW value** a bound mother gets → onshell-as-single-source.md (trace the last onshell writer; collisions with the `$` filter).
- The **helas combine mechanics** that physically attach a bound decay → combine-decay-chain-layer.md / onshell-helas-bridge.md.
- The **warning-text emission** itself (`logger.warning` formatting/location) → diagram-enumeration slice.
- The **σ consequence** of bind-vs-leak-vs-drop and same-multiset-≠-same-amplitude magnitude → phase-space / integration slice.
- The form-6 open-paren `InvalidCmd : No particle (t` reject → process-syntax tokenization slice.

## Instances this generalizes (kept — they carry the specific probes)
- clause-distribution-and-topology.md — same-clause distribution across all matching legs; no-implicit-default; distinct-product clauses; same-multiset ≠ same-amplitude.
- nested-subdecay-paren-taxonomy.md — the 6/7/8-diagram surface-form table for nested `h>tt`, incl. the 7-diagram partial-LEAK.
- cautions.md §2 / onshell-flag-and-decayBW.md case 1 — the flat-subdecay DROP (discard + warning) mechanism.
