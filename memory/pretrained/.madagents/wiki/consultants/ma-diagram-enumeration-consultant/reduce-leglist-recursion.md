---
description: reduce_leglist / combine_legs / merge_comb_legs / reduce_orders — the core N->N-1 leg-reduction recursion that enumerates tree diagrams
---

# reduce_leglist recursion internals (diagram_generation.py)

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` (v3.7.1) unless noted. This is the engine that `generate_diagrams` (see `generate-diagrams-algorithm.md`) drives; that page summarizes it in two lines, this page is the detail.

## reduce_leglist (:959)
Signature `reduce_leglist(self, curr_leglist, max_multi_to1, ref_dict_to0, is_decay_proc=False, coupling_orders=None)`. Recursive: reduces an N-leg list to N-1 by replacing a valid combination with its merged internal particle, recursing until 2 legs remain. Returns `res` = list of lists of `Vertex` objects (each inner list is one diagram's vertices), or `None` if the branch is dead.

Per call:
1. **n->0 closure** (:983-997): if `curr_leglist.can_combine_to_0(ref_dict_to0, is_decay_proc)`, look up the vertex id(s) in `ref_dict_to0[sorted ids]`, build `final_vertices`, and for each pass `reduce_orders` — append `[final_vertex]` to `res` only if orders did not go negative (:994-997). This is how a diagram terminates with its top vertex.
2. **stop at 2** (:1000-1004): if `len==2`, return `res` if non-empty else `None`. (Two legs can't be further reduced; only the n->0 closure above can have emitted anything.)
3. **enumerate combinations** (:1007-1011): `combine_legs` lists all valid leg groupings; `merge_comb_legs` turns each into `(reduced_leglist, vertex_list)` tuples.
4. **per combination** (:1014-1044): skip if any produced internal line is a `forbidden_particles` id (:1017-1021); call `reduce_orders` on the combination's vertex ids and skip the whole recursion if any order < 0 (:1024-1030); else recurse on the reduced leglist and, on a non-None result, cartesian-combine this level's vertices with the sub-diagrams via `expand_list_list` (:1041-1044).

## can_combine_to_0 / can_combine_to_1 (base_objects.py)
- `can_combine_to_1` (`base_objects.py:2250`): needs `minimum_one_from_group()` True AND sorted ids in `ref_dict_to1`. So a combination is valid only if it touches at least one leg flagged `from_group=True` (a leg that was newly produced or is still active) and the model has an n-1->1 interaction for those ids.
- `can_combine_to_0` (`base_objects.py:2258`): normally needs `minimum_two_from_group()` AND sorted ids in `ref_dict_to0`. **Decay-chain special path** (`is_decay_chain=True`, :2267-2274): instead requires that at least one leg has `from_group == None` (the marked initial leg) and the ids are in `ref_dict_to0`. This forces the initial decay leg to be the LAST wavefunction clustered — the mechanism behind the artificial A=A final vertex of decay processes.

## reduce_orders (:1048)
Returns `None` if no `coupling_orders` given (counts as success); else copies the order budget and, per vertex id (skipping id==0 identity vertices, :1063-1065), subtracts that interaction's `orders` from any matching budget entry that is `>=0`; returns `False` the moment any drops below 0 (:1075-1077). Then handles `WEIGHTED` separately (:1078-1086): subtracts `sum(order_hierarchy[c]*n)` over the interaction's orders; `False` if WEIGHTED goes negative. Returns the reduced budget otherwise.
- **Negative constraints are NOT enforced here** — docstring (:1055-1056): "We ignore negative constraints as these cannot be taken into account on the fly but only after generation." A budget entry with value < 0 is skipped by the `>=0` guards. Negative-order semantics are applied post-generation (squared-order path / coupling-orders slice).
- A coupling absent from an interaction's `orders` is NOT treated as a constraint (:1068-1069) — only present-and-nonnegative budgets are decremented.

## combine_legs (:1090)
Recursive enumerator of all allowed groupings. For `comb_length` 2..`max_multi_to1` (:1119), takes every `itertools.combinations(list_legs, comb_length)` (:1127), keeps it if `LegList(comb).can_combine_to_1(ref_dict_to1)` (:1130). For each valid combination it both (a) appends the single-combination reduction and (b) recurses on the remainder after the combination's first element to build multi-combination groupings (:1140-1160). Output: a list of leg-lists where some entries are tuples (the groups to merge) and the rest are plain legs. `max_multi_to1` = the max valence of any n-1->1 interaction in the model (set in `generate_diagrams` as max key length of `ref_dict_to1`).

## merge_comb_legs (:1165)
Turns each combination-list into concrete `(LegList, VertexList)` tuples. For each tuple entry (a group): the replacement leg id(s) come from `ref_dict_to1[sorted group ids]` (:1187-1188), one output list per possible intermediate particle (multiple particles can share the same id-set → multiple internal lines); `number` = min of the group's leg numbers (:1191); **state** = final UNLESS exactly one initial-state leg is in the group, in which case state=False — a t-channel propagator (:1192-1197). For non-group entries it flips `from_group` to False, **except when `from_group is None`** (the decay-chain initial leg) which is left untouched so the decay special-case in `can_combine_to_0` keeps recognizing it (:1231-1238). `get_combined_legs` (:1251) / `get_combined_vertices` (:1264) build the actual Leg/Vertex objects and are the daughter-overridable hooks (LoopAmplitude overrides them).
- At its tail merge_comb_legs flattens each per-combination result with **`expand_list`** (:1241-1242, NOT `expand_list_list`): one call on the reduced leglist, one on the vertex list, so when a single id-set maps to multiple intermediate particles the multiple internal-line variants get expanded into separate concrete leglist/vertex pairs.

## The full LoopAmplitude override surface (5 hooks)
The tree recursion calls five daughter-overridable hook methods so `LoopAmplitude` can reuse the same engine for loop-leg (DGLoopLeg) generation:
- `copy_leglist(legs)` (:950-957): base returns `LegList([copy.copy(leg) for leg in legs])`; LoopAmplitude returns a DGLoopLeg list (DGLoopLegs carry extra loop-generation params). Called once in `generate_diagrams` (:649) to make the working leglist.
- `create_diagram(vertexlist)` (:939-942): base wraps in `base_objects.Diagram({'vertices':vertexlist})`; overloaded by daughters.
- `convert_dgleg_to_leg(vertexdoublelist)` (:944-948): base is a no-op returning `True`; LoopAmplitude converts DGLoopLegs back to Legs.
- `get_combined_legs(legs, leg_vert_ids, number, state)` (:1251) and `get_combined_vertices(legs, vert_ids)` (:1264): build the actual Leg/Vertex objects in `merge_comb_legs`; LoopAmplitude overrides them (also noted above).
These five are the ENTIRE seam between tree and loop enumeration in this engine — LoopAmplitude (madloop slice) subclasses Amplitude and overrides exactly these plus `generate_diagrams`'s `returndiag` path. Out of my slice WHAT the loop overrides do; IN my slice that these are the hook points the tree recursion routes through.

## The two cartesian helpers — expand_list vs expand_list_list (module-level :2145 / :2167)
Distinct roles; the recursion uses BOTH, at different sites — do not conflate.
- **`expand_list`** (:2145): treats a list whose entries are either lists or bare elements; bare elements become singletons, then full `itertools.product` (:2162). `[[1,2],3,[4,5]] -> [[1,3,4],[1,3,5],[2,3,4],[2,3,5]]`. Used only inside `merge_comb_legs` (:1241-1242) to fan a single combination into its multiple-intermediate-particle variants.
- **`expand_list_list`** (:2167): recursive; concatenates lists-of-lists rather than producting elementwise. `[[1,2],[[4,5],[6,7]]] -> [[1,2,4,5],[1,2,6,7]]`. Base case returns `[[]]` for empty/`[[]]` input (:2175-2176). Used in `reduce_leglist` (:1043) to cartesian-combine THIS level's vertex list with the recursively-generated sub-diagram vertex lists. The `[[]]` base case is what lets the deepest recursion contribute an empty tail without killing the product.

## trim_diagrams (:1270) — memory dedup + decay flagging (two layered jobs)
Signature `trim_diagrams(self, decay_ids=[], diaglist=None)`. Default `diaglist=self['diagrams']`; LoopAmplitude passes an explicit list so it trims a given list not the attribute (:1272-1280).
- **Job 1 — object-identity dedup (always runs):** walks every diagram's vertices/legs and replaces each `Leg`/`Vertex` with a shared canonical instance found via `legs.index(leg)` / `vertices.index(vertex)` (:1300-1312). Identical legs/vertices across diagrams become the SAME object in memory — the "reduce legs/vertices used in memory" of the docstring. This is structural sharing, NOT diagram removal; diagram count is unchanged.
- **Job 2 — decay flagging (only when `decay_ids` non-empty):** sets `leg.onshell=True` on external final-state legs whose id ∈ decay_ids, at two sites: process legs (:1284-1286) and diagram legs (:1294-1299). Two subtleties: (a) the diagram-leg path does `leg = copy.copy(leg)` (:1298) BEFORE the index-dedup, so a freshly onshell-flagged leg becomes its own canonical object rather than aliasing an unflagged twin; (b) a per-diagram `leg_external` set (:1290/:1295/:1307) gates the flag to the FIRST occurrence of each leg number — internal propagators that happen to reuse an external number are excluded (`leg.get('number') not in leg_external`). Only genuine external decaying legs get flagged.
- **Three call sites, three roles:** core generation `self.trim_diagrams(diaglist=res)` (:841, empty decay_ids → pure memory dedup, no flag); chain construction `amp.trim_diagrams(decay_ids)` (:1397, the onshell-flag site, see `decay-chain-amplitude.md`); `cross_amplitude` `new_amp.trim_diagrams()` (:2134, re-dedup after renumbering a crossed copy).

## Cautions
- The t-channel determination is purely "exactly one IS leg in the merged group" (:1194) — not a momentum-flow analysis. `number`=min-of-group is what later lets `trim_diagrams` dedup and what s-channel/t-channel filters key on (leg number < ninitial+1 ~ t-channel).
- `reduce_orders` enforces positive budgets and WEIGHTED on the fly but DEFERS all negative constraints; do not assume a negative coupling-order constraint pruned anything during the recursion (coupling-orders slice owns the post-generation handling).
- The decay special-case threads through THREE sites that must agree: `from_group=None` set on the initial leg in `generate_diagrams` (`leglist[0].set('from_group', None)` :684), preserved (not flipped to False) in `merge_comb_legs` (:1236), and consumed in `can_combine_to_0` (`base_objects.py:2267`). A change to any one breaks decay-chain leg ordering silently.
- `combine_legs` is O(combinations) — for high-multiplicity final states this recursion is the cost center of enumeration; `max_multi_to1` caps the per-vertex valence searched.
- After `trim_diagrams` legs/vertices are ALIASED across diagrams (shared objects). Mutating a `Leg`/`Vertex` in one diagram post-trim silently changes every diagram that shares it. The decay-flag path sidesteps this by `copy.copy`-ing before flagging (:1298); other post-trim consumers must assume shared identity.
- `expand_list` and `expand_list_list` are NOT interchangeable — `expand_list` does elementwise product (singletons from bare items), `expand_list_list` does list-of-lists concatenation. Picking the wrong one would silently scramble the vertex-list structure.
