---
description: DiagramTag / DiagramTagChainLink — chain-depth-ordered unique tagging used to identify identical diagrams and identical matrix elements across processes
---

# DiagramTag (diagram_generation.py)

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` (v3.7.1).

## Purpose (docstring :46-66)
Tags diagrams "based on objects with some __lt__ measure, e.g. PDG code/interaction id (for comparing diagrams from the same amplitude), or Lorentz/coupling/mass/width (for comparing AMPs from different MEs)." Gives "a unique tag which can be used to identify diagrams (instead of symmetry), as well as identify identical matrix elements from different processes." DiagramTag is the MOTHER class; daughters override the static measure functions to pick what the tag is sensitive to.

## Algorithm (:50-63, __init__ :72-126)
Build chains from external particles inward. Each leg → `DiagramTagChainLink` (end link); each vertex combines incoming-leg links into an internal link tagged by interaction id (`vertex_id_from_vertex` :286). The leg_dict (:77) memoizes the link for each intermediate particle number so a vertex reuses daughter links.
- Last vertex: all legs are incoming (the n→0 vertex), so all its legs go in (:82-85).
- After building, the central vertex is shifted (:103-126) so the LONGEST subchain is as SHORT as possible: repeatedly flip toward the longest chain (`flip_vertex` :300) until the new longest link is not smaller than the current one.

## DiagramTagChainLink (class :325)
- End link (vertex_id=None): `links=(((id,state),number),)`, `vertex_id=(0,)`, `depth=0`, `end_link=True` (:335-341).
- Internal link: links sorted reverse, `depth = sum(child depths) + max(1, len-1)` — so a 4-point vertex contributes depth 2 (:345-348).
- Ordering `__lt__` (:361): 1. depth, 2. len(links), 3. vertex_id[0], 4. recursive measure of links. Handles int/tuple/str vertex_id mismatches explicitly (loop tags can be tuples/strings) (:374-393).
- `__eq__` (:404): end links compare `links[0][0]` only — i.e. the leg NUMBER (`links[0][1]`) is IGNORED in comparison. Internal links compare end_link, depth, vertex_id[0], and child links.

## What is / isn't compared
- `link_from_leg` (:274): final-state particle → `((id, 0), number)` so identical FS particles are identified; initial-state → `((id, number), number)` so identical IS particles are DISTINGUISHED (:278-283).
- "the number is not taken into account in tag comparison, but is used only to extract leg permutations" (:276). `get_external_numbers` (:128/:351) recovers the permutation.
- `vertex_id_from_vertex` (:286): only `vertex_id[0]` enters comparison; [1] stores info not compared; [2] holds shrunk-loop PDGs (:289-298).

## Reconstruction
`diagram_from_tag` (:132) + `vertices_from_link` (:147) rebuild a Diagram from a tag (daughters override `id_from_vertex_id` / `leg_from_link`). `leg_from_legs` (:198) reconstructs an internal leg's PDG by removing daughter PDGs from the interaction PDG list (asserts exactly one remains, :207).

## Seam: ME-identification daughters (helas_objects.py)
The DiagramTag mother is this slice; the docstring's "identify identical matrix elements from different processes" is realized by daughters defined OUTSIDE this slice's file. `IdentifyMETag(DiagramTag)` (`$MADGRAPH_INSTALL/madgraph/core/helas_objects.py:59`) compares leg number/color/lorentz/coupling/state/spin/mass/width/decay/is_part and refuses to combine across `has_mirror_process` / process id / identical_particle_factor / decay chains; `create_tag` (:80) keys it. Daughters `IdentifyMETagFKS` (:237, adds charge) and `IdentifyMETagMadSpin` (:250) specialize it. These tags drive matrix-element grouping during HELAS construction — the daughter internals and their grouping usage are the helas-amplitude slice's, not mine. I own only the mother's tagging algorithm above.

## Cautions
- DiagramTag equality is type-strict: `__eq__` returns False if `type(self) != type(other)` (:307) — comparing a base DiagramTag to a daughter (e.g. an IdentifyME tag) is always unequal. This is WHY ME-identification uses a single daughter type (`IdentifyMETag`) consistently across processes — mixing tag types would silently never match.
- Final-state IS-particle distinction is asymmetric: swapping two identical FS particles gives an equal tag, swapping two IS particles does NOT (by design, for crossing/mirror bookkeeping).
- Depth formula `max(1, len-1)` means n-point vertices are weighted by their valence; do not assume depth == number of vertices.
