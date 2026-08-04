---
description: ALOHA routine-build pipeline — AbstractALOHAModel orchestration, builder/routine classes, compute_all, conjugation/symmetry/multiple-lorentz passes.
---

# ALOHA build pipeline (create_aloha.py)

All cites `$MADGRAPH_INSTALL/aloha/create_aloha.py` (v3.7.1).

## Top-level objects
- `AbstractRoutine` (`:59`) — one helicity routine: holds `expr`, `outgoing`, `spins`, `name`, `model`, optional `denom`. `add_symmetry` (`:79`), `add_combine` (`:85`) for multi-Lorentz. `write` (`:91`) dispatches to a writer.
- `AbstractRoutineBuilder` (`:120`) — builds routines from one UFO `lorentz`. Class attrs `prop_lib={}` (`:123`, propagator-expression cache), `counter` (`:124`). `__init__` (`:129`) pulls `lorentz.spins`, `lorentz.structure` into `self.lorentz_expr`; substitutes any `lorentz.formfactors` by regex (`:154-157`).
- `CombineRoutineBuilder` (`:679`) — subclass building combined routines for shared sub-expressions across multiple Lorentz structures (`l_lorentz` list).
- `AbstractALOHAModel(dict)` (`:706`) — model-level container, one per loaded UFO. Keyed `(lorentzname, outgoing) -> AbstractRoutine`. `compute_all` (`:884`), `write` (`:1149`), `save`/`load` (pickle, `:780`/`:794`), `get` (`:806`), `set` (`:879`).
  - **`load()` is DEAD** (`:796` `return False` BEFORE any file check) — `aloha.pkl` is NEVER reloaded; `main()` always recomputes via `compute_all` (`:760-761`), and `save()` failures are silently swallowed (`:791-792`) because nothing reads them back. No cross-`output` ALOHA caching at this layer.
  - **`main()` only runs if `write_dir` passed at construction** (`:748-749`). In production the exporter builds the model WITHOUT `write_dir`, so `main()` (and its dead load/save) never run — the exporter drives `compute_subset`/`compute_all` + `write` directly. The actual production entry point is `compute_subset`, NOT `compute_all` — see compute-subset-production-path.md. This page documents the whole-model `compute_all` path (the fallback when `wanted_lorentz` is empty).
  - `get_info('rank',...)` (`:817`) — loop max-rank query with `cached_interaction_infos` memoization; SIDE-EFFECT: force-sets `aloha.loop_mode=True` if any tag starts with `L` (`:824-825`). Called from helas-amplitude slice (`helas_objects.py:1019`). See compute-subset-production-path.md loop_mode lifecycle.

## compute_all orchestration (`:884`)
1. `look_for_symmetries()` (`:1215`) — identical particles in vertices → reuse one routine.
2. `look_for_conjugate()` (`:1297`) → `conjugate_list` (fermion-flow clashes needing C-conjugation).
3. `look_for_multiple_lorentz_interactions()` (`:1237`) → `self.multiple_lor`.
4. For each `lorentz` in `model.all_lorentz` (filtered to `wanted_lorentz`):
   - skip `-1 in spins` (ghost; `:900` "No Ghost in ALOHA"); `structure=='external'` → record external routine names, skip (`:904`).
   - `routines = [(i,[]) for i in range(len(spins)+1)]` — one per outgoing position (0 = all-incoming/amplitude).
   - if `custom_propa`: add per-particle propagator tag variants (`:912-930`) — `P0`/`P<name>`/`P1N`, vector `P1L/P1T/P1A/P1PS`, fermion `P1P/P1M` (polarised-production / hel-recycling routines).
   - build via `AbstractRoutineBuilder(lorentz, model)`, `compute_aloha(builder, routines=...)` (`:1101`).
   - attach `add_combine` for multiple-Lorentz (`:935`); build conjugate builders via `define_all_conjugate_builder` (`:944`).
5. `save()` if requested.

## Symmetry / multiple-Lorentz keying (which routines reuse/combine)
- `look_for_symmetries` (`:1215`): a vertex leg `i` reuses leg `j<i`'s routine only if SAME pdg, `color==1` (singlet), and for fermions (`spin==2`) SAME slot parity — `i%2 != j%2 → continue` (`:1225`), so an incoming/outgoing fermion slot cannot map to the other. Stored `self.symmetries[lorentz.name][i+1] = j+1` (1-based, max-merged `:1230`).
- `has_symmetries` (`:1280`): recursively chases `symmetries[l_name][outgoing]` to the LOWEST equivalent leg, optionally restricted to `valid_output` — this is the actual "don't regenerate, point to the canonical leg" resolver.
- `look_for_multiple_lorentz_interactions` (`:1237`): only combines Lorentz structures sharing BOTH the same color id AND the same coupling ORDER within a vertex (`key=(id_col, order)`, `:1260`). Result `self.multiple_lor[main] = [tuple of other lorentz names]` keyed on the lowest-index structure (`:1271-1277`); these drive `add_combine` (`:935`).

## Conjugation (Majorana / fermion-flow)
- `_conjugate_gap = 50` (`:52`) — offset added to a spinor index id to mark the conjugated leg.
- `apply_conjugation` (`:196`): wraps kernel as `C(new,old+1) * kernel * C(new+1,old)` (`:226`) implementing `C Γ^T C^{-1}`. For >1 pair or >2 fermions it validates the fermion flow via `aloha_fct.get_fermion_flow` against the canonical pairing (`:207-214`); raises if flow violated with Majorana.

## compute_aloha driver / kernel reuse (`:1101`)
- `compute_aloha(builder, symmetry, routines, tag)` (`:1101`) — the per-Lorentz routine factory. For each `(outgoing, tag)`: `realname = name + ''.join(tag)` (`:1120`); skip if `(realname,outgoing)` already in the model dict (`:1121`). If `has_symmetries` resolves to a lower equivalent leg → no recompute, just `add_symmetry(outgoing)` on the canonical routine (`:1124-1125`); else `builder.compute_routine(outgoing, tag)` and `set` (`:1127-1129`). Default tag = conjugate tags `['C%s'%i for i in builder.conjg]` (`:1111`).
- `compute_aloha_without_kernel` (`:1132`) — same surface but RESETS `builder.routine_kernel=None` before EACH outgoing (`:1144`), so every routine re-parses the Lorentz from scratch (no cross-outgoing kernel reuse). The normal `compute_aloha` path reuses the cached `routine_kernel` across outgoing positions (the perf win); this variant is the independent-compute fallback.

## External routines (`structure=='external'`)
- A Lorentz with `structure=='external'` is NOT generated — its name is recorded (`:904`) and `AbstractALOHAModel.write` (`:1149`) calls `locate_external` (`:1185`) to FIND a hand-written file matching `<base>*_<amp>.<ext>` and COPY it into the output dir (`:1196-1208`). Search order: model's `<language>/` subdir, model dir, then `aloha/template_files/` (`:1192-1193`). Missing → `ALOHAERROR` (`:1203`). So external Lorentz structures bypass ALOHA codegen entirely and rely on a shipped file.

## Routine name / library
- `get_routine_name` (`:664`) and writer-side `get_routine_name` (`aloha_writers.py:1324`).
- `write_aloha_file_inc` (`:1349`), `create_prop_library` (`:1374`) — see propagators page.
