---
description: drawing.py FeynmanDiagram/FeynmanLine API surface used by user_filter remove_diag — constructor, load_diagram/define_level, vertexList/lineList/initial_vertex, line/vertex attributes, production-vs-decay discriminator, 4-point vertex line count. Verified against v3.7.1.
---

# drawing.py FeynmanDiagram / FeynmanLine API (for diagram inspection / user_filter)

`$MADGRAPH_INSTALL/madgraph/core/drawing.py` (v3.7.1). This is the
diagram-DRAWING core `output` owns (JPEG/EPS emission). A hand-authored
`PLUGIN/user_filter.py remove_diag(diag, model)` can reuse it to introspect a
diagram's topology. The `--diagram_filter` hook + user_filter.py themselves are
diagram-enumeration's, NOT installed here — API-surface facts only below.

## Constructor + drive sequence (all doc claims CONFIRMED)
- `FeynmanDiagram(diagram, model, amplitude=False, opt=None)` — `:681`. Asserts
  `diagram` is a `base_objects.Diagram` (`:690`) and `model` a `base_objects.Model`
  (`:692`). So the 2-arg form `FeynmanDiagram(diag, model)` is valid.
- `draw.load_diagram(contract=True)` — `:744`. Builds `self.vertexList` and
  `self.lineList`; appends border vertices; populates `self.initial_vertex`.
- `draw.define_level()` — `:959`. Assigns `vertex.level` walking out from
  `initial_vertex` (level 0). REQUIRED before reading `vertex.level`, NOT required
  for the production/decay count (see below).
- `main()` `:721` is the full pipeline (load_diagram → define_level →
  find_initial_vertex_position → adjust_position → solve_line_direction). A filter
  needing only topology calls load_diagram (+ define_level if it needs levels).

## Attributes — provenance
Init to `[]` at `:708-710`:
- `self.vertexList` `:708` — all VertexPoint objects (real vertices +
  appended fake border vertices for external legs, `:770`).
- `self.initial_vertex` `:709` — populated at `:777` ONLY for lines with
  `line.state == False` (INITIAL-state legs). CORRECTION to doc: it is NOT "all
  external particle vertices" — final-state externals also get a fake vertex
  (`:778-781`) but are NOT appended here. So `len(initial_vertex)` = number of
  initial-state legs.
- `self.lineList` `:710` — all FeynmanLine objects (initial, final, propagators).

VertexPoint (`:480`, extends base Vertex): `self.lines=[]` `:500` (FeynmanLine
objects at this vertex), `self.level=None` `:501` (int after def_level `:571`;
0 = initial state, set at `:776`). `is_external()` `:581` = `len(self.lines)==1`.

FeynmanLine (`:54`) built via `FeynmanLine(leg)` (`:887`) so attributes come from
the base_objects.Leg dict: `line.id` (PDG; `get_info` uses `abs(self.id)` `:176`),
`line.number` (original leg number), `line.state` (True=final, False=initial).
`line.begin`/`line.end` init to `0` (`:70-71`), reset to VertexPoint via
`def_begin_point`/`def_end_point` (`:93`,`:103`).

## Production vs decay discriminator (CONFIRMED, with ordering caveat)
`len(draw.initial_vertex) < 2` ⇒ decay subprocess (1 initial parton);
`== 2` ⇒ production. Backed by `:783-788`: `if len(self.initial_vertex)==2` is the
2→2/2→N production branch; the `else` (len 1) branch runs `remove_t_channel()`
(a decay has no T-channel). initial_vertex is filled by `load_diagram` at `:777`,
so the count is valid AFTER `load_diagram()` — `define_level()` is NOT required for
this test (it is only required to read `vertex.level`).

## 4-point contact vertex (CONFIRMED)
`len(v.lines) > 3` over `draw.vertexList` catches genuine ≥4-point vertices: each
leg on a vertex adds one FeynmanLine to `vertex.lines` (`add_vertex`→
`def_*_point`→`add_line` `:538`), so a 4-point contact = 4 lines > 3. Caveat: fake
border vertices have exactly 1 line (external), and `contract=True` (default) fuses
non-propagating lines (`_fuse_non_propa_particule` `:760`) which can merge vertices
— read topology after load_diagram with the same contract setting the filter wants.
