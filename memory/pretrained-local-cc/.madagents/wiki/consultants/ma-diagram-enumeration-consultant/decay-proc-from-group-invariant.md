---
description: The decay-process invariant — from_group=None marks the initial leg as last-to-cluster (artificial A=A vertex); the full set of source sites that must agree
---

# Decay-process `from_group=None` invariant (diagram_generation.py + base_objects.py)

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` and `.../base_objects.py` (v3.7.1).

## The invariant
A *decay process* is one with `ninitial == 1` that is (or becomes) `is_decay_chain`. Its diagram generation is bound by ONE invariant:

> **The single incoming (decaying) leg must be the LAST wavefunction clustered**, so generation terminates with an artificial `A=A` (1=1) vertex. That terminal vertex is required for the result to be usable as a decay-chain leg downstream.

The mechanism carrying the invariant is a **tri-state `Leg.from_group`** marker. Normal legs are `True`/`False`; the decaying initial leg is set to the third state `None`, which means "do not let me be clustered until everything else is gone." `Leg.from_group` default is `True` (`base_objects.py:2110`); the tri-state is created at generation time, not stored.

This page is the generalization of the local pieces in `generate-diagrams-algorithm.md`, `reduce-leglist-recursion.md`, `decay-chain-amplitude.md`, `multiprocess-crossing-mirror.md` — those describe one site each; this page is the complete site-set that must agree, including sites no instance page links into the decay narrative.

## Two distinct flags — don't conflate
- `is_decay_proc` = `process.get_ninitial() == 1` — a LOCAL bool computed inside `generate_diagrams` (:674). Drives the recursion + post-filter special cases.
- `is_decay_chain` = a persistent Process field (default `False`, `base_objects.py:2967`) set True at decay-chain construction (:1382). Drives the cross-amplitude / order-search / crossing-reuse special cases.
Both ultimately protect the same invariant but fire in different code regions; `find_optimal_process_orders` and `cross_amplitude`/process-rebuild key on `is_decay_chain`, the core recursion keys on `is_decay_proc`.

## The full site-set (all must agree)
SET — the marker:
1. `generate_diagrams` builds a custom `ref_dict_to0` allowing only the initial leg's n->0 identity and sets `leglist[0].set('from_group', None)` (:680-684).
2. `DecayChainAmplitude.__init__` sets `process.set('is_decay_chain', True)` per decay chain (:1382).

PRESERVE — keep the marker alive through reduction:
3. `merge_comb_legs` flips non-group legs' `from_group` to False **except when it is None** — `if cp_entry.get('from_group') != None:` (:1233-1236). A change here would clobber the marker mid-recursion.

CONSUME — recognize the marker:
4. `can_combine_to_0` decay-chain path: `any(leg.get('from_group') == None for leg in self)` AND ids in `ref_dict_to0` (`base_objects.py:2267-2274`). This is the gate that fires the n->0 closure only once the initial leg is the last one standing.

ACCOMMODATE the artificial vertex — post-generation:
5. `required_s_channels` filter excludes the **last TWO** vertices for decay procs (`lastvx = -2` at :723), because the artificial 1=1 vertex sits after the real top vertex. (Non-decay uses `lastvx = -1`.) — *site not in any instance page's decay narrative.*
6. Final id==0 vertex glue is SKIPPED when `is_decay_chain` (`if not process.get('is_decay_chain')` :814) — decay procs deliberately KEEP the artificial final vertex; non-decay procs glue it away.

PROPAGATE `is_decay_chain` through process copies:
7. `find_optimal_process_orders` early-returns (no order search) for single-incoming non-decay-chain procs (:1978-1980), and when it DOES search it builds a trial Process carrying `is_decay_chain` (:2081-2082) so the search respects the invariant. — *site not in any instance page's decay narrative.*
8. `cross_amplitude` / crossing-reuse: successful-crossing reuse is DISABLED for `is_decay_chain` procs (:1860) — each crossing regenerates so the artificial vertex is rebuilt correctly rather than copied.

## Why it's an invariant, not a list of features
Sites 1+3+4 form a closed loop: set the marker → preserve it through every reduction step → consume it as the last-clustering gate. Break any one and the initial leg gets clustered early, the A=A vertex never forms, and the diagram is unusable as a decay leg — **silently**, with no error (the recursion just produces ordinary diagrams). Sites 5-8 then exist only to accommodate the artificial vertex that 1+3+4 produce. So the gate "does a new decay code path respect the invariant?" catches more than enumerating the eight sites: any FUTURE site that reduces legs, copies a decay Process, or post-filters decay diagrams must also respect the marker.

## Boundary (out of this slice)
- Decay-chain *syntax* (`,` / `(...)`) parsing → chain-decay slice.
- What `onshell=True` (the decay flag set by `trim_diagrams`) MEANS to downstream HELAS/output → helas-amplitude / output slices. The marker discussed here (`from_group=None`) is a DIFFERENT field from `onshell`; see `decay-chain-amplitude.md` for `onshell`.

## Cautions
- `from_group=None` (clustering order) and `onshell` (decay flag) are separate `Leg` fields with separate lifecycles — do not conflate. `from_group` is enumeration-internal and transient; `onshell` is set later by `trim_diagrams(decay_ids)` at chain construction and persists downstream.
- The `!= None` / `== None` comparisons (sites 3,4) are intentional identity-style checks against the tri-state; rewriting them as truthiness (`if not from_group`) would break, since `from_group=False` is a legitimate non-None state.
