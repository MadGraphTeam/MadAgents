---
description: ALOHA's per-process selective entry point compute_subset (the actual production path) vs whole-model compute_all, the explicit_combine branch, and the aloha.loop_mode global side-effect lifecycle. Companion to build-pipeline.md (compute_all-only).
---

# compute_subset — the production ALOHA entry point

Cites `$MADGRAPH_INSTALL/aloha/create_aloha.py` and the MG output exporters, v3.7.1. `build-pipeline.md` documents `compute_all` (whole-model). In a real `output`, MadGraph almost never calls `compute_all` — it calls `compute_subset(wanted_lorentz)` with only the Lorentz routines the process needs. This page is that path.

## Which entry point the exporter actually calls
All three exporters gate on `wanted_lorentz`: non-empty → subset, empty → whole-model fallback.
- Fortran: `export_v4.py:1062-1065` — `if wanted_lorentz: compute_subset(wanted_lorentz) else: compute_all(save=False)`. Model built at `:1056` WITHOUT a `write_dir`, so `AbstractALOHAModel.main()` (and its dead load/save, see build-pipeline.md) never runs in production; `add_Lorentz_object(model.get('lorentz'))` (`:1059`) injects dynamically-created Lorentz first.
- C++/standalone: `export_cpp.py:382-388` — builds the model with `explicit_combine=True`, then same subset/all gate (`:386`/`:388`, fallback uses `custom_propa=True`).
- `madgraph_interface.py:9183-9185` — same gate (fallback `custom_propa=True`).
- `wanted_lorentz` originates in the helas-amplitude slice (`helas_objects.py:1853,3047` assemble "the necessary information to compute_subset"). The CONTENT of `wanted_lorentz` is that slice's; ALOHA only consumes it.

## compute_subset algorithm (`:971`)
Input `data` = list of `(list_l_name, tag, outgoing)` tuples.
1. `look_for_symmetries()` only (`:981`) — NO `look_for_conjugate` / `look_for_multiple_lorentz` scan; conjugation + combine are driven per-request by the tags instead.
2. **Resets `aloha.loop_mode = False`** at entry (`:984`) — see lifecycle below.
3. **`outgoing == -1` expansion** (`:991-996`): a `-1` outgoing means "do for every outgoing leg" (used for `P1N` hel-recycling); the tuple is replaced by one per leg `1..len(spins)`.
4. **Tag normalization** (`:1004-1010`): integer tags → `C%s` conjugate tags; non-P string tags kept; P-tags appended LAST (stable ordering). `conjugate = tuple(int(c[1:]) for C-tags)`.
5. Builds `request[l_name][conjugate] = [(outgoing,tag),...]` (`:1016-1023`).
6. Per `(l_name, conjg)`: sort routines rising by outgoing (symmetry needs rising order, `:1041-1045`); `compute_aloha(builder, routines=...)` directly if no conjg, else `define_conjugate_builder(conjg)` first (`:1046-1054`). `external` Lorentz just records the routine name (`:1028-1034`), no codegen (see build-pipeline.md external path).
7. **Multiple-Lorentz combine pass** (`:1057-1097`) — the explicit_combine branch (below).

## explicit_combine — inline add_combine vs separate combined routine
The multiple-Lorentz (same color id + same coupling order) combination has two realizations, selected by `self.explicit_combine`:
- **NOT explicit (default Fortran)** (`:1068-1075`): fold into the existing single routine via `self[(name+tags, outgoing)].add_combine(list_l_name[1:])`. No extra file — the matrix element passes `COUP1..COUPn` at CALL time and the one routine sums them. (If the routine isn't present, asserts the Lorentz is `external`.)
- **explicit (`:1076-1097`)**: build a `CombineRoutineBuilder(l_lorentz)` and `compute_aloha` it → a SEPARATE combined-routine file emitted by the writer's `write_combined` (writer-lowering-mechanics.md). The C++ exporter ALWAYS sets `explicit_combine=True` (`export_cpp.py:382`); the Fortran path is inline unless forced explicit by a loop tag.

### CombineRoutineBuilder (`:679`)
Subclass of `AbstractRoutineBuilder`. `__init__` (`:683`) takes a LIST of Lorentz; builds the combined expr as `' + '.join('Coup(i+1) * (lor.structure)')` (`:699-701`) — the per-Lorentz coupling weighting baked symbolically into ONE kernel. `name = combine_name(l_name[0], l_name[1:], None)` (`:694`). This is the source of the `COUP1..COUPn` header args in `write_combined`.

## aloha.loop_mode — global side-effect lifecycle (caution)
`aloha.loop_mode` is a MODULE global (aloha/__init__.py), not per-routine, and it is MUTATED as a side effect of two query/build calls:
- `compute_subset` RESETS it to `False` at entry (`:984`), then SETS it `True` (plus `self.explicit_combine = True`) the moment any request carries a loop tag `L*` (`:1011-1014`).
- `AbstractALOHAModel.get_info('rank',...)` (`:824-825`) FORCE-SETS `aloha.loop_mode = True` if any tag starts with `L` — so merely querying a loop routine's rank flips the global. Called from `helas_objects.py:1019` (helas-amplitude slice) for loop max-rank.
- The Fortran exporter brackets the call: saves `old_loop_mode` and RESTORES `aloha.loop_mode = old_loop_mode` after `write` (`export_v4.py:1074`). So the flip is intended to be transient, but any code reading `aloha.loop_mode` BETWEEN the flip and the restore sees the loop value. When predicting a routine's layout (momentum_size 2 vs 4, see writer-hierarchy.md), confirm whether you are inside a loop-tagged compute_subset window, not just the model's nominal gauge.

## Cautions
- `compute_subset` does NOT run the model-wide conjugate/multiple-lorentz scans — it trusts the per-request tags. A routine's conjugation/combine here is request-driven, so the same model can yield a different routine set than `compute_all` would (subset is exactly what `wanted_lorentz` asks for, nothing speculative).
- The dead `load()` (`create_aloha.py:796` `return False` before any file check) means `aloha.pkl` is never reloaded; `compute_subset` recomputes every time. `save=False` on the `compute_all` fallback path also skips the pickle. So there is no cross-`output` ALOHA caching at this layer.
- Whether a specific process emits an inline-combine vs explicit-combined FILE is a runtime consequence of `explicit_combine` (target-dependent: C++ always explicit, Fortran inline-unless-loop). To assert which files appear in `<PROC_DIR>/Source/DHELAS/`, probe (cheap `output` of a multi-Lorentz vertex) rather than claim from reading.
