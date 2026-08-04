---
description: How parsed decay-chain syntax (recursive decay_chains ProcessList) drives DecayChainAmplitude recursion depth, separate per-level enumeration, and the syntax round-trip
---

# Decay-chain nesting: parsed syntax → recursive separate enumeration

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py`, `.../base_objects.py`, `.../helas_objects.py` (v3.7.1). Centers the SHAPE of how the comma/paren chain syntax becomes a tree of separately-enumerated amplitudes. Mechanics of `__init__` prohibitions/warnings/trim are in `decay-chain-amplitude.md`; this page is the recursion/structure layer.

## The parsed input is a RECURSIVE container
The parser hands enumeration a `ProcessDefinition` whose `decay_chains` field is itself a list of `ProcessDefinition`s, EACH of which may again carry its own non-empty `decay_chains`:
- `Process['decay_chains']` is a `ProcessList` (`base_objects.py:2970`); `ProcessDefinition['decay_chains']` is a `ProcessDefinitionList` (`base_objects.py:3837`).
- Nesting is unbounded and self-similar: `base_objects.py:3398` `if decay.get('decay_chains'):` proves a decay element can itself hold sub-decays.
- The **parenthesization in the syntax IS the nesting depth.** `input_string()` (`base_objects.py:3395-3401`) reconstructs the chain and wraps a decay in `(...)` IFF that decay itself has sub-`decay_chains` (:3398-3400). So `p p > t t~, (t > b w+, w+ > l+ vl)` ⇒ the `t` decay-Process carries a `w+` sub-decay in ITS `decay_chains`; the flat `p p > t t~, t > b w+, w+ > l+ vl` ⇒ `t` and `w+` are SIBLING top-level decays of the core (the trap — see `decay-chain-amplitude.md` Warning 1).

## Recursion: one DecayChainAmplitude per nesting level
`DecayChainAmplitude.__init__` mirrors the container recursively:
- The core ProcessDefinition is enumerated ONCE into `self['amplitudes']` (`diagram_generation.py:1360-1365`, via `generate_multi_amplitudes`).
- Each immediate decay chain becomes a NESTED `DecayChainAmplitude(process, ...)` appended to `self['decay_chains']` (:1386-1389). That nested constructor in turn enumerates ITS core (the decaying-particle 1→N process) separately and recurses into ITS sub-decays.
- Net: a tree of `DecayChainAmplitude` nodes, each node holding (a) its own level's amplitude list, (b) child `DecayChainAmplitude`s. Depth = paren-nesting depth. **Every level is enumerated INDEPENDENTLY** — the core `p p > t t~`, the `t > b w+`, the `w+ > l+ vl` each run `generate_diagrams` on their own legs; they are never enumerated as one big leglist.

## Two flatten/extract methods walk the tree (consumed downstream)
- `get_amplitudes()` (:1526-1535) recursively flattens core + all descendants into a single flat `AmplitudeList` (extends own, then recurses each child). This is what the cmd layer iterates for counting.
- `get_decay_ids()` (:1508-1520) walks only the IMMEDIATE `decay_chains` (one level), collecting each decay amp's `get_initial_ids()[0]`, deduped via `misc.make_unique`. Distinct from the INLINE `decay_ids` at :1392 (raw `legs[0].get('id')`) — different computation, different consumer (see `decay-chain-amplitude.md`).
- `get_number_of_diagrams()` (:1472-1476) recurses and returns the SUM over the whole tree — NOT the stitched product. The combinatorial core×decay product is computed only downstream.

## Where the levels are COMBINED (boundary — helas slice, not mine)
The separately-enumerated tree is stitched into full matrix elements DOWNSTREAM:
- `HelasMultiProcess.generate_matrix_elements` branches on `isinstance(amplitude, DecayChainAmplitude)` (`helas_objects.py:5870`) and calls `HelasDecayChainProcess(amplitude).combine_decay_chain_processes(combine)` (:5872-5873).
- `combine_decay_chain_processes` (`helas_objects.py` ~:5440+) recurses children first (:5450-5452), then forms the cross product of core diagrams × each FS decay leg's matrix elements (:5467+), applying `identical_decay_chain_factor` (:4581) for symmetry among identical decay chains.
- Cross-process ME identification uses the DiagramTag daughter `IdentifyMETag.create_tag` (:5886) — see `diagram-tag.md` seam. The DiagramTag MOTHER (chain-depth ordering) is mine; the daughter + the combine are helas.

So: my slice ends at "the recursive tree of separate amplitude lists is built, decay legs flagged onshell, warnings emitted." The product, identical-chain factors, and stitched ME count are the helas-amplitude slice's.

## A multiparticle in a decay leg multiplies that level's list (not depth)
If a decay leg is a `ProcessDefinition` (multiparticle in the decay, e.g. `t > b W` where `W` expands, or several FS expansions), that level routes through `generate_multi_amplitudes` (:1361) which `extend`s MULTIPLE amplitudes into the SAME node's `amplitudes` list (:1360) — it widens the node, it does not add a tree level. A plain `Process` decay leg instead `append`s exactly one amp (:1367) and goes through `get_amplitude_from_proc` (which silently drops `diagram_filter`, see `decay-chain-amplitude.md`). Tree DEPTH comes only from sub-`decay_chains`; node WIDTH comes from multiparticle expansion of that level.

## Cautions
- Depth of the `DecayChainAmplitude` tree == parenthesization depth of the syntax, NOT the number of decaying particles. Flat sibling decays (`, t > ..., w+ > ...`) are all depth-1 children of the core; only `(t > ..., w+ > ...)` makes `w+` a depth-2 grandchild.
- `get_decay_ids` is ONE level; `get_amplitudes`/`get_number_of_diagrams` are WHOLE tree. Don't swap them.
- Each level enumerated separately means a dead decay (zero diagrams for an accepted sub-process) raises `NoDiagramException` UNGUARDED and kills the whole chain — see `multiprocess-crossing-mirror.md`. There is no per-level "skip and continue" the way core crossings get `failed_procs` absorption.
- The "combined diagram count" question is always helas — `get_number_of_diagrams` here is a SUM, the user-visible stitched count is the product computed in `combine_decay_chain_processes`.
