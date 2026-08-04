---
description: A decay clause distributes across EVERY matching final-state pdg leg in its enclosing scope (set-based decay_ids + Cartesian combine); NO implicit invisible-decay default; the chain restricts the amplitude to the production-graph × decay topology (same final-state multiset ≠ same amplitude as the inclusive ME).
---

# Clause distribution and amplitude-topology restriction

Source: MG5_aMC v3.7.1. Probe-confirmed. The unifying BINDING rule this page instantiates (binding = paren-scope × set-based pdg-match, read by topology fingerprint) is `decay-binding-is-scope-times-match.md`; this page is the same-clause-distribution + amplitude-topology instance of it.

## (A) One clause distributes across EVERY matching final-state leg of its pdg

A single decay clause `X > ...` decays **every** final-state leg of pdg `X` in the enclosing scope, not one of them. Mechanism (the parser appends ONE decay_process per clause — see comma-parser.md — but the amplitude layer distributes it):

- `DecayChainAmplitude.__init__` collects `decay_ids` as a **set** of decay-incoming pdg ids (`diagram_generation.py:1392-1395`). One `z > e+ e-` clause → `decay_ids = {23}` regardless of how many Z's the core has.
- `trim_diagrams(decay_ids)` (`:1397`) flags **every** core final-state leg whose id is in `decay_ids`: `if leg.get('state') and leg.get('id') in decay_ids: leg.set('onshell', True)` (`:1284-1286`, and the diagram-vertex walk `:1294-1299`). BOTH Z legs get `onshell=True` from the single clause.
- The physical duplication (the decay actually attaching to both Z's, producing the doubled leaf final state) is the Cartesian combine in the HELAS layer (`combine_decay_chain_processes` / `insert_decay_chains` — see combine-decay-chain-layer.md). The single user clause is internally applied to each matching producer.

**Probe** (`generate h > z z, z > e+ e-`): TWO `Decay: z > e+ e-` lines in the log from the single clause; subprocess `P1_h_zz_z_ll_z_ll`; `NEXTERNAL=5`; `leshouche.inc` `IDUP=(25,-11,11,-11,11)` (h + e+e-e+e-, four electrons); `decayBW.inc` has `gForceBW(-1,1)/1/` AND `gForceBW(-2,1)/1/` (both Z s-channel mothers forced-BW=1, leg -3 = Higgs propagator = 0). Confirms the clause hit BOTH Z's.

### Corollary — NO implicit invisible-decay default
There is no "decay one, leave the other as a stable/invisible Z" default. A leg not matched by any clause simply stays a ME external (`onshell=None` → `gForceBW=0`), undecayed in the amplitude. To give the two Z's **different** decays you must write two clauses with distinct products: `..., z > e+ e-, z > mu+ mu-`.

## (B contrast) Distinct-product clauses each bind ONE leg — comma-only is unambiguous there

When two clauses have **distinct** final states, each clause's pdg-match is still set-based, but the two decays are different processes; the combine pairs each distinct decay with one producer. So comma-only (no parens) `generate p p > z z, z > e+ e-, z > mu+ mu-` parses clean — **probe: 10 diagrams, no warning/discard**, identical to the parenthesised `..., (z > e+ e-), (z > mu+ mu-)`. The two clauses are siblings of the core (both decay a core Z), the core HAS two Z's, so both bind — no scoping ambiguity.

Do NOT conflate with the (A) trap: in (A) ONE clause matches BOTH legs (distribution → 4 same-flavour leptons); here TWO clauses each match one (→ e+e-mu+mu-). The discriminator is whether the clause(s) are the same or distinct, not the parens.

(The genuine comma-only **discard** trap is the sub-sub-decay scoping failure — a clause whose parent isn't a core leg, e.g. top-level `..., w+ > l+ vl` against a `p p > t t~` core. That is comma-parser.md §B + onshell-flag-and-decayBW.md case 1; probe-confirmed `Decay information for particle(s) w+,w+ is discarded`. The warning EMISSION is diagram-enumeration's slice.)

## (C) The chain restricts the amplitude to production-graph × decay topology

A chain `generate p p > z z, (z > e+ e-), (z > mu+ mu-)` builds the `q q~ > Z Z` **production** amplitude times spin-correlated Z decays = doubly-resonant ZZ ONLY. It is NOT the inclusive ME with the same final-state multiset.

**Probe diagram counts** (SM) — these integers are SPECIFIC to this ZZ→4ℓ topology and the current model; the durable point is the QUALITATIVE inequality (chain-restricted amplitude ⊊ inclusive amplitude), not the numbers. Derive counts per process by probe:
- Chain `p p > z z, (z > e+ e-), (z > mu+ mu-)`: each `u u~ > z z` core = 2 diagrams (t- and u-channel ZZ production), Z decays attached; `g g > z z` = 0 (no tree gluon-Z coupling). Total 10 across the qq̄ channels.
- Inclusive `p p > e+ e- mu+ mu-`: each `u u~ > e+ e- mu+ mu-` = 24 (adds single-resonant Zγ*, γ*γ*, non-resonant 4-lepton graphs). Total 96.

The chain count is FAR smaller than the inclusive count for the same final-state multiset (e+e-mu+mu-) — different and much larger amplitude. σ differs substantially (~70% per anchored values; the σ-magnitude claim is the phase-space/integration slice, not verified here). The inclusive **enumeration** itself (what graphs the 24 contain) is diagram-enumeration's slice.

**Rule for this slice:** the chain syntax restricts the amplitude to (core production graphs) × (the specified decay topology), spin-correlated. "Same final-state multiset" is NOT "same amplitude." When a user wants the full off-shell/interfering set, they must write the inclusive process, not a chain.
