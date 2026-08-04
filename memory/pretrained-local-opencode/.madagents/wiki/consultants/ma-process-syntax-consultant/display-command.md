---
description: do_display sub-arguments enumeration + validation (check_display), and the key `display diagrams` mechanic — writes .eps files then shells out to `open` (NO built-in viewer). v3.7.1.
---

# The `display` interactive command (`do_display`)

`madgraph_interface.py:3566 do_display(self, line, output=sys.stdout)`. Reports internal
state (model content, generated processes, config). Arg-validated by `check_display` (959).

## Sub-argument enumeration — `_display_opts` (2991-2994, verbatim v3.7.1)
```
['particles', 'interactions', 'processes', 'diagrams',
 'diagrams_text', 'multiparticles', 'couplings', 'lorentz',
 'checks', 'parameters', 'options', 'coupling_order', 'variable',
 'modellist']
```
`check_display` (967) accepts `_display_opts + ['model_list']` (so both `modellist` and
`model_list` work). Anything else → `InvalidCmd('Invalid arguments for display command: %s')`.

Per-arg behaviour in `do_display` (each an `elif args[0]==...`):
- **diagrams** (3573) → `self.draw(' '.join(args[1:]))` — see mechanic below. Gated (975): needs `_curr_amps` or `_fks_multi_proc` else `InvalidCmd("No process generated...")`.
- **diagrams_text** (3707) → `pydoc.pager` of each amp's `nice_string()` (ASCII diagram dump, no file).
- **particles** (3576 bare / 3601 named) → prints particle names (part/antipart split) or `nice_string()` for a named/pdg particle; unknown → `InvalidCmd('no particle %s in current model')`.
- **interactions** (3613 bare / 3630 by-index / 3640 by-particle) → `pydoc.pager` of the interaction list / one interaction / interactions containing given particles.
- **processes** (3703) → `print(amp.nice_string_processes())` for each `_curr_amps`. Gated same as diagrams (975).
- **multiparticles** (3711) → prints every label in `self._multiparticles` via `multiparticle_string`.
- **parameters** (3676) → `pydoc.pager` of model parameters grouped by type (external first).
- **couplings** (3721 bare / 3747 named) → coupling list, or a named UFO coupling's `nice_string()`. V4 model → "No couplings information available in V4 model".
- **coupling_order** (3716) → prints `order_hierarchy` sorted by weight.
- **lorentz** (3761) → UFO lorentz structure(s); prints `dir(ufomodel.lorentz)` bare, or one `nice_string()`.
- **checks** (3778) → `pydoc.pager` of stored `_comparisons` / `_cms_checks` (results of prior `check` runs). Gated (977): empty → `InvalidCmd("No check results to display.")`.
- **options** (3823) → MadGraph / MadEvent / Configuration option tables (marks "(user set)").
- **variable** (3872) → delegates to base `Cmd.do_display` (dumps a python attribute); needs exactly 2 args (980).
- **modellist / model_list** (3875) → available model list.

`check_display` also hard-requires `self._curr_model` (971) → "No model currently active, please import a model!" for ALL sub-args.

## `display diagrams` mechanic — writes .eps, then `open` (NOT a built-in viewer)
`display diagrams` → `draw()` (3999). PROBE-CONFIRMED v3.7.1 (`import model sm; generate p p > t t~; display diagrams`):
1. `check_draw` (984): if no dir arg, appends `tempdir.name` (a temp dir) — **no process directory or `output` needed**; requires `_curr_amps` else "No process generated".
2. For each amplitude, builds `filename = pjoin(args[0], 'diagrams_'+shell_string+'.eps')` (4033) and **writes an EPS file** via `draw.MultiEpsDiagramDrawer(...).draw()` (4047-4057). Logs `"Wrote file <path>"`.
3. Then `self.exec_cmd('open %s' % filename)` (4059) — shells out to the interface `open` command, which uses the **configured `eps_viewer`** from `mg5_configuration.txt`.

Probe output (bare `display diagrams`, 5 subprocesses): wrote `<tmpdir>/diagrams_1_gg_ttx.eps`, `..._uux_ttx.eps`, etc. (one per subprocess), each followed by `open <file>` → with no viewer set: `"Not able to open file ... since no program configured. Please set one in ./input/mg5_configuration.txt"`. Generation proceeds regardless (the open failure is non-fatal).

### Doc-correction
"`display diagrams` opens a viewer" is IMPRECISE/WRONG as stated. Reality: it **generates one .eps file per subprocess** (to a temp dir by default), then **attempts to launch the externally-configured eps viewer** via the `open` command. No built-in/interactive viewer exists; if `eps_viewer` is unset nothing opens (files are still written). It does NOT require an existing process directory (writes to temp). `output`-time JPEG/EPS diagram drawing is a separate path (output slice, `drawing.py`); this is the ad-hoc REPL draw.

## Cross-refs
- `check` command → check-command-validators.md (`do_check` 4065, `_check_opts` 2999-3000, `check_check` 998).
- Diagram-drawing internals (`MultiEpsDiagramDrawer`, `drawing.py`) are the output/drawing slice's; I own only the `do_display` dispatch + parse.
