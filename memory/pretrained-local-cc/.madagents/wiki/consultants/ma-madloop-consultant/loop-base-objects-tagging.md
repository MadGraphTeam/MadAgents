---
description: LoopDiagram tagging algorithm (canonical_tag, L-cut choice, mirror/cyclic, loop_tag for cross-process ME identification) + LoopUVCTDiagram/LoopModel/DGLoopLeg/FDStructure objects (loop_base_objects.py, MG5_aMC v3.7.1)
---

# Loop base objects — tagging + structures

`$MADGRAPH_INSTALL/madgraph/loop/loop_base_objects.py`. The data structures behind loop diagram generation, plus the canonical-tagging algorithm that drives `identify_loop_diagrams` (same-process loop merging) and cross-process ME identification. Complements ./loop-diagram-generation.md (which cites `tag`/`is_*` from the pipeline view) with the tagging algorithm itself.

## LoopDiagram(base_objects.Diagram) — :36
Two distinct tags (default_setup :50-84):
- `tag` (:59): `[(Leg,[Structure_IDs],VertexID), …]` — full loop structure, cut & ordered as generated. Carries Leg/Vertex objects.
- `canonical_tag` (:66): `[(LegPDG,[Structure_IDs],VertexID), …]` ordered in a canonical unambiguous way — "what allows for diagram selection". Integers only (light to store).
- `type` (:71): positive PDG of the (particle, not anti) L-cut particle; 0 for born/R2/UV. Predicate `type>0` ⇒ a true loop (R2 are negative type — see loop-color-basis.md).
- `multiplier` (:76): count of numerically-identical merged loops (e.g. closed massless quark loops).
- `CT_vertices` (:79): the R2/UVmass/UVloop CTVertices (see ./counterterm-structure.md).
- `contracted_diagram` (:84): the loop-shrunk-to-a-point Diagram, built lazily by `get_contracted_loop_diagram`.
- Class var `cutting_method='optimal'` (:48) — 'optimal' (recycling-optimized) vs 'default'; process_check flips it for the permutation check command.

## The tagging algorithm
`tag(struct_rep, model, start_in, end_in, synchronize=True)` (:601-670):
1. Collects non-loop external legs; defaults `start/end` to the two L-cut leg numbers (:616-618).
2. `process_next_loop_leg` (:713) walks the loop building `tag` and FDStructures into `struct_rep`.
3. Picks the canonical cut: `cutting_method=='optimal'` ⇒ `choose_optimal_lcut`; `=='default'` ⇒ `choose_default_lcut` (:643-653).
4. Writes `self['tag']=canonical_tag`, then `canonical_tag` (PDG form) = `[[t[0]['id'],t[1],t[2]] for t in canonical_tag]` (:666).
5. If `synchronize`, `synchronize_loop_vertices_with_tag` rebuilds the vertex list (:659-661).

`choose_optimal_lcut` (:527-562): cut just before the combined structure with smallest WEIGHT, then choose direction toward the next-smallest weight — maximizes loop-wavefunction recycling in open-loops. `compute_weight` (:514-525) S(i): positive, distinct per external-leg set, super-additive. Special cases: len 1 (tadpole) returns as-is; len 2 (bubble) picks direction by larger `abs(id)`; len≥2 by `rev_weights[1]<weights[1]`.

`choose_default_lcut` (:564-599): cyclic-rotate so the lowest structure ID is first (`make_canonical_cyclic` :1256), compare against the `mirrored_tag` (:1275, reverses loop flow / swaps part↔antipart direction), keep the one with lower structure ID in 2nd position. Removes redundant bubble mirrors like `[a W- a]` vs `[W+ a W-]` via the `abs(id)` rule (:592-597).

## loop_tag — cross-process ME identification
`build_loop_tag_for_diagram_identification(model, FDStrut_rep, use_FDStructure_ID_for_tag=False)` (:269-359): builds the `loop_tag` on the ContractedVertex. "what is used by MG5_aMC to decide if two processes have *exactly* the same matrix element and can be identified" (:273-275). For each canonical_tag element it captures:
- loop particle: `(spin, color, self_antipart, mass, width, is_part)` — `is_part` ADDED beyond IdentifyMETag because it gives the loop-flow direction (:286-297).
- FDStructure tagging: by struct ID only when `use_FDStructure_ID_for_tag=True` (within-process loop identification); otherwise EMPTY because the rest of the DiagramTag already probes structures (:299-330). Consequence noted in source: a loop attached to structs (1,2,3,4) vs (1,4,3,2) shares the same DiagramTag (order not in loop_tag) — fine for process identification only (:308-316).
- interaction tagging: `(sorted couplings items, str colors, lorentz)` — model-ID-independent so `gdd~` and `gss~` interactions identify (:332-345).
- plus `sorted(get_loop_orders(model).items())` appended (:357-358).

`get_contracted_loop_diagram` (:361+): shrinks loop to a `ContractedVertex` with special id `-2` (so info is read from `loop_info` not a model interaction, :393-398). `type<=0` returns a plain copy (:367-368).

## Other LoopDiagram helpers
- `get_loop_orders(model)` (:1234), `get_loop_lines_pdgs` (:1307), `get_pdgs_attached_to_loop(structs)` (:1313), `get_starting/finishing_loop_line` (:1208/1215), `get_loop_line_types` (:1225), `get_nloopline` (:506).
- predicates `is_fermion_loop` (:438), `is_tadpole` (:451), `is_vanishing_tadpole` (:463), `is_wf_correction` (:479), `get_CT` (:428) — covered operationally in ./furry-and-loop-filters.md / ./counterterm-structure.md.

## LoopUVCTDiagram(base_objects.Diagram) — :1323
UVtree + wavefunction-renorm CTs (NOT attached per-loop; standalone diagrams). `get_UVCTinteraction` (:1369), `calculate_orders` (:1379) sums vertex orders + UVCT_orders into coupling_orders + WEIGHTED. See ./counterterm-structure.md.

## LoopModel(base_objects.Model) — :1415
- Adds `perturbation_couplings` (list of order strings, :1433) — the defining extra key over a tree Model.
- `coupling_orders_counterterms` (:1442): dict order→`(loop_particles, counterterm, laurent_order)`.
- `map_CTcoup_CTparam` (:1448-1449): coupling→CTparameter-names map (NOT a dict key, attribute only). Preserved on copy from another LoopModel (:1423-1427).
- `actualize_dictionaries(useUVCT=False)` (:1468-1478): regenerates `ref_dict_to0/to1`; `useUVCT=True` ⇒ `generate_ref_dict(useR2UV=False,useUVCT=True)` — THIS is the dict refresh set_Born_CT calls when injecting the fake UVCT_SPECIAL order (see ./counterterm-structure.md).
- `change_electroweak_mode` (:1486-1491): HARDCODED `bypass_check=True` at :1487 — the EW-scheme guard ("can not change EW scheme for model handling EW correction") is dead code, the check never fires. (caution)

## DGLoopLeg / FDStructure / FDStructureList
- `DGLoopLeg(base_objects.Leg)` (:1496): generation-only Leg with extra `depth` (:1516). `convert_to_leg` (:1536) strips it back to a plain Leg.
- `FDStructure` (:1550): ordered VertexList tree piece hanging off the loop; `id`, `external_legs`, `canonical` tuple, `binding_leg`. `is_external` (:1564) true when `canonical` is a single (·,0) element (a bare external leg). `generate_vertices` (:1653).
- `FDStructureList` (:1771): `get_struct(ID)` (:1780) lookup; the `structure_repository` shared across loop diagrams (LoopAmplitude :71).

## Cautions
- `change_electroweak_mode` bypass at :1487 means the EW-scheme-change safety check for EW-correction models is unconditionally skipped. (caution, not a runtime claim)
- `tag` MUST run before Furry filter / identification — the pipeline tags at generate_diagrams :842 before :872 Furry (see ./loop-diagram-generation.md, ./furry-and-loop-filters.md); calling Furry on untagged diagrams raises.
