---
description: `add model PLUGIN` orchestration — do_add dispatch to add_model, the BASE__PLUGIN merged-dir cache (reused unless --recreate/--output), and the usermod.UFOModel.add_model merge rules (particle PDG-match + zero-mass wins/else-raise, external-param block+id merge no-value-check, coupling-order MIN of hierarchy AND expansion_order, vertex dedup by particles+lorentz+color+ORDER, loop-model-plugin prohibition). Distinct from `import model` (single UFO load).
---

# `add model PLUGIN` — plugin-UFO merge (v3.7.1)

`add model <plugin>` MERGES a plugin UFO into the currently-loaded base model, writes a
combined model dir, and re-imports it. Distinct from `import model` (loads ONE UFO). All in
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` (dispatch) +
`$MADGRAPH_INSTALL/models/usermod.py` (merge engine).

## Dispatch: `do_add` → `add_model` (`madgraph_interface.py`)
- `do_add` at `:3260`: `if args[0]=='model': return self.add_model(args[1:])`. (Note: the
  master_interface `do_add` wrapper at `master_interface.py:200` only NLO-switches on
  `args[0] in ['process','timing','profile']` — `model` falls through to the base `do_add`.)
- `add_model(self, args)` at `:3400`:
  - `model_path = args[0]`; flags: `--recreate` (`:3404`), `--keep_decay` (`:3407`),
    `--output=DIR` (`:3410`, forces `recreate=True` and empties `restrict_name`).
  - **Merged-dir name** (`:3416-3420`): with no `--output`, `output_dir =
    MG5DIR/models/<base>__<plugin>` where `<base>=basename(curr_model modelpath)`,
    `<plugin>=basename(model_path)`. The `restrict_name` of the current model is captured
    (`:3418`) and re-appended after re-import (`:3463-3464`).
  - **Reuse cache** (`:3422-3441`): if `output_dir` exists AND not `recreate` →
    `logger.info('Model already created! Loading it from %s')` and just `import model
    <output_dir>[-restrict]` (`:3432`); on failure restores the previous model and raises
    `"Invalid Model! Please retry with the option '--recreate'."` (`:3439`). With `--recreate`
    (or `--output`) the existing dir is `shutil.rmtree`'d first (`:3424`).
  - **Build** (`:3443-3456`): `base_model = deepcopy(usermod.UFOModel(base modelpath))`;
    `identify = dict(a.split('=') for a in args if '=' in a)` (particle-identification map,
    e.g. `add model X uc=u`); `base_model.add_model(path=model_path,
    identify_particles=identify)`; `base_model.write(output_dir)`.
  - `--keep_decay` (`:3458-3460`) copies the base model's `decays.py` into the merged dir.
  - **Re-import** (`:3466-3471`): `import model <output_dir>[-restrict] [--modelname]`
    (`--modelname` iff the history's `full_model_line` had `modelname`). So after `add model`
    the operative model is the RE-IMPORTED merged dir — full `do_import` tail runs.

## Merge engine: `usermod.UFOModel.add_model` (`usermod.py:960`)
`UFOModel.__init__(modelpath, addon='__1')` (`:51`) — the collision-rename suffix defaults to
**`__1`** (`:115`), NOT the plugin name. (The plugin NAME only appears in the merged DIRECTORY
name `base__plugin`, `madgraph_interface.py:3419`.) Merge steps (`add_model:960`):

- **Plugin validity gates** (`:972-982`): plugin must have `all_orders` (`:973`, else
  USRMODERROR); particle mass/width must be objects not strings (`:976`);
  **loop-model plugin PROHIBITED** — any order with `perturbative_expansion` truthy →
  `raise USRMODERROR('Add-on model can not be loop model.')` (`:980-982`). (The BASE may be
  anything; only the added-on plugin is barred from being a loop model.)
- **Coupling orders** (`add_coupling_order:796`, called `:984-985`): an order present in BOTH
  takes the **MINIMUM of hierarchy** (`:802-806`) AND the **MINIMUM of expansion_order**
  (`:807-811`), each with a warning. New orders are appended.
- **Particles** (`add_particle:575`, via identify map `:1044-1045`): matched by NAME then by
  PDG. Same name + same PDG (or an explicit `identify`) → merged via
  `check_mass_width_of_particle` (`:596-598`). Same name, DIFFERENT PDG (no identify) → plugin
  particle RENAMED `name__1` and both kept, with a warning (`:607-611`).
  - **Mass/width reconciliation** (`check_mass_width_of_particle:626`): if the two names
    differ — if the mapping is already known-equivalent, OK; **elif base mass name is `zero`
    → adopt the plugin's mass** (`:633-634`); **elif plugin mass is `zero` → keep base's**
    (`:635-636`); **else (both non-zero, different, non-equivalent) → RAISE USRMODERROR**
    (`:637-644`). So the rule is *"zero yields to non-zero; two conflicting non-zero masses
    are an ERROR"* — NOT a blanket "nonzero mass wins". Width handled the same (`:645+`).
- **External params** (`add_external_parameter:660`): same NAME but different block/lhacode →
  plugin renamed `name__1`, mapping stored in `old_new` (`:670-689`; extra warning if the
  base's same-named param is `internal`). Same BLOCK+LHACODE (even under different names) →
  **MERGED into one** (plugin name → base name via `old_new`), **with NO value comparison**
  (`:696-709`). For `mass`/`decay` blocks the lhacode PDG is remapped through `identify_pid`
  first (`:692-694`). Otherwise appended as a genuinely new external (`:735-738`).
- **Internal params** (`add_internal_parameter:740`): same name + same value → no-op; same
  name + different value → plugin renamed `name__1` and its expression rewritten through
  `old_new` (`:746-759`).
- **Vertices** (`add_interaction:844`): docstring "This is UNCONDITIONAL! ... now weaken if
  both interaction are exactly identical." Dedup key = **sorted particle PDGs + lorentz
  structure + color + coupling ORDER** (`:875-919`):
  - All couplings match an existing same-PDG vertex on (lorentz, color) AND coupling
    EXPRESSION → the vertex is **skipped** (`return` at `:919`).
  - Same particles/lorentz/color and same coupling ORDER but DIFFERENT coupling expression →
    ALSO **skipped**, with warning `"Did NOT add interaction ... same particles/lorentz/color/
    coupling order BUT did not manage to ensure that the coupling is the same"` (`:906-913`).
  - Only a vertex differing in particles/lorentz/color STRUCTURE falls through and is
    **added** (`:921-926`).
  - So "near-duplicates both kept" is WRONG: a vertex matching on (particles, lorentz, color,
    ORDER) is dropped even if its coupling VALUE differs. What distinguishes keep-vs-drop is
    the structure+order, not the coupling expression.

## Cautions
- The merged model is CACHED as `models/<base>__<plugin>[-restrict]`; a second `add model`
  of the same pair silently REUSES it unless `--recreate`/`--output` — so edits to the plugin
  UFO between runs are NOT picked up without `--recreate`.
- `add model` re-imports the merged dir through the normal `do_import` tail, so ALL import-time
  rewrites (CMS, restriction/multiparticle flavour scheme, gauge, `mdl_` prefix) re-apply — see
  `import-time-model-rewrites.md`.
- Merge is order-sensitive for name collisions (plugin objects get the `__1` suffix, base keeps
  its name). Value conflicts on external params are silently merged (base wins the name); mass
  conflicts on same-PDG particles either resolve via zero-yields-to-nonzero or ERROR.
- Restriction-file content, UFO object semantics, and coupling-order physics meaning are
  ufo/restriction-slice; this page owns only the add-model ORCHESTRATION + merge mechanics.
