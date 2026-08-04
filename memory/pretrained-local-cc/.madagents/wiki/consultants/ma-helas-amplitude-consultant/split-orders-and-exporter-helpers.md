---
description: HelasMatrixElement exporter helpers — get_split_orders_mapping (squared-order interference indices), get_used_lorentz/get_used_couplings, color-basis recycling in process_color, get_mirror_processes.
---

# Split-orders mapping and exporter-facing helpers

Cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (v3.7.1). These methods are read by the iolibs exporters, not by generate_helas_diagrams — they shape what the emitted `matrix_*.f` looks like (squared-order arrays, ALOHA routine list, coupling list, mirror leg order).

## get_split_orders_mapping @5038 → (squared_orders, amp_orders)
Drives split-order squared-ME output (e.g. `p p > j j [QCD QED]` interference bins). Returns `(),()` if `process['split_orders']` empty @5065.
- `amp_orders` (via `get_split_orders_mapping_for_diagram_list` @4996): per diagram, `calculate_orders()` + a synthesized `WEIGHTED` = Σ order_hierarchy·power @5013; the tuple of split-order powers is the key, amplitude numbers grouped under it. Example (docstring @5055): dijet → `[((2,0),(2,)), ((0,2),(1,3,4))]` (amp 2 is QCD², amps 1,3,4 are QED²).
- `squared_orders` @5077-5086: all `amp_order[i] + amp_order[j]` (j≤i) interference sums, dedup preserving construction order. Example → `[(4,0),(2,2),(0,4)]`.
- **Ordering is load-bearing** (docstring @5058-5060): the list order dictates the order of the "order indices" in exporter output. `sort_split_orders` @4986 sorts split_orders by `order_hierarchy` BUT only if every split order has a hierarchy entry @4992 — otherwise insertion order is kept. So a model missing an order in its hierarchy changes the emitted index layout silently.

## get_used_lorentz @5092 / get_used_couplings @5104 (per-ME)
- `get_used_lorentz`: for every wf+amp with `interaction_id not in [0,-1]`, append `get_aloha_info()` = `(lorentz_name, conjugate_tag, outgoing)`. This is exactly the set of ALOHA routines the exporter must generate (interaction_id 0 = identity amp, -1 = special, both skipped @5098).
- `get_used_couplings(output=str)`: coupling strings from the same wf+amp set; a leading `-` (minus-one coupling) is stripped @5113 so the bare coupling name is returned. `output="set"` dedups @5115.
- Multiprocess-level `HelasMultiProcess.get_used_lorentz` @5718 / `get_used_couplings` @5728 just union across all MEs via `misc.make_unique`. These feed the single shared ALOHA/coupling generation for the whole output directory.

## process_color @5749 (HelasMultiProcess classmethod) — color-basis RECYCLING across MEs
The color counterpart to ME-dedup. For each surviving ME, builds `colorize_obj` from the base amplitude, then `list_colorize.index(colorize_obj)` @5786:
- **Hit** → reuse the existing `color_basis`+`color_matrix` (logs "Reusing existing color information") @5800-5804.
- **Miss** → build a fresh `ColorBasis`+`ColorMatrix`, append to the shared lists (logs "Processing color information") @5787-5799.
Both stored on the ME @5806-5809. So even two MEs that are NOT identical (distinct IdentifyMETag) can SHARE one color matrix if their colorize objects match — a second, independent recycling axis below ME-dedup. (Color algebra itself is the color-decomposition slice; this is the storage/recycling integration only.)

## get_mirror_processes @5118
If `has_mirror_process`, returns processes with legs 0/1 swapped (both `legs` and `legs_with_decays`) @5126-5132. Used by exporters to write the initial-state-swapped (e.g. `g u` vs `u g`) entry into the subprocess without a second ME. Empty list if no mirror @5122-5123.

## reorder_process @5987 (static) — permutation glue for combined processes
When a new process is folded onto an existing ME (in generate_matrix_elements @5949 and combine_decay_chain_processes @5638), its legs must be reordered to match the surviving ME's external-number convention. Computes `DiagramTag.reorder_permutation(proc_perm, org_perm)` @5995 and applies it to `legs_with_decays`; if no decay chains, also to `legs`. Identity when `org_perm==proc_perm` @5998.

## Cautions
- `get_split_orders_mapping` ordering depends on the model's `order_hierarchy` being complete; a missing order falls back to insertion order and changes emitted index positions — verify against the generated matrix file for an exotic-order model, don't assume hierarchy sorting.
- `process_color` recycling is keyed on the colorize object, independent of IdentifyMETag — color sharing and ME sharing are DIFFERENT equivalence relations (another instance of the identity-keys-purpose-tuned principle, but at the color/ME-storage boundary rather than the wf/tag boundary).
- `get_used_lorentz` is derived live from the current wf/amp set; if called before reuse_outdated_wavefunctions or after a mutation (decay insert, Majorana flip), it reflects whatever wfs exist at that moment.
