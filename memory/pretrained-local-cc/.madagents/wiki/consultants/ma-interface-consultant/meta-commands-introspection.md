---
description: Introspection & file meta-commands (madgraph_interface.py / madevent_interface.py) — do_display variable/run_name/results, do_convert_model (py2->py3 UFO patch), do_tutorial (logger toggles), do_open/check_open (export-dir resolution + card auto-copy), do_load (unpickle model/processes), do_edit_cards (entry into AskRun).
---

# Introspection & file meta-commands

The introspection/file meta-layer of the LO and madevent interfaces. (The config-system
commands do_set / do_save / do_display-options live on config-system.md.)

## do_display (3566) — non-options subjects
`display variable <expr>` evals expr as GLOBAL/LOCAL/EXTERNAL and pages via `pydoc.pager`
(base extended_cmd 1918, madgraph 3566 extends).
`_display_opts` DIFFERS by interface (all validated in `check_display`):
- base `extended_cmd` (893): `['options','variable']` only.
- **madgraph** (2991-2994): the full list `['particles','interactions','processes','diagrams','diagrams_text','multiparticles','couplings','lorentz','checks','parameters','options','coupling_order','variable','modellist']`. So `display diagrams` (madgraph do_display 3573 → `self.draw(' '.join(args[1:]))`, optional out-path arg) and `display particles` (3576) are madgraph-only subjects — NOT available at the base/madevent prompt.
- madevent (2049): `['run_name','options','variable','results']` — `display run_name` lists Events/*/*_banner.txt runs+tags; `display results` → `do_print_results`.
(`display options` itself is the config read-side — config-system.md.) `check_display` rejects any `args[0]` not in `self._display_opts + ['model_list']` (967-968). It ALSO gates on model/process state: `if not self._curr_model` → `InvalidCmd("No model currently active, please import a model!")` (971-972); `processes`/`diagrams` need `_curr_amps` or `_fks_multi_proc` (975); `checks` needs prior check results (977). So every model-inspection subject below is MADGRAPH-prompt-only AND requires a model imported first.

### madgraph model-inspection subjects — what each actually PRINTS (do_display 3576+)
Verified against v3.7.1. The model-inspection subjects exist as tokens in `_display_opts` (2991-2994): `particles`, `interactions`, `multiparticles`, `parameters`, `modellist`, `coupling_order` (the token IS singular `coupling_order`).
- **`display particles`** (bare, 3576-3599): prints NAMES ONLY — a count, then `name/antiname` pairs for non-self-conjugate particles, self-conjugate names on the next line, plus an un-physical (non-propagating) count. It does NOT print PDG IDs / masses / spins. To get PDG+mass+spin+full props use the ARGUMENT form **`display particles <name|PDG>`** (3601-3611) → `particle.nice_string()`. So "display particles lists PDG/mass/spin" is true only of the per-particle argument form, not the bare list.
- **`display parameters`** (3676-3701): groups by "parameter type" (the `_curr_model['parameters']` dict keyed by dependency-tuple). External params (key `('external',)`) are sorted FIRST via `key_sort` returning -1 (3682-3683), each group under a `parameter type: <key>` header — so internal and external ARE listed separately, external first. Internals (have `.expr`) print `name = expr = value`; externals print `name = value` (3691-3700).
- **`display interactions`** (bare, 3613-3628): count + numbered vertex list (particle names, `order=n`, type), paged via `pydoc.pager`. `display interactions <n>` shows one vertex.
- **`display multiparticles`** (3711-3714): the `_multiparticles` label dict (`p`, `j`, `l+`, …).
- **`display coupling_order`** (3716-3720): the model's `order_hierarchy` as `name : weight = w`, weight-sorted.
- **`display modellist`** (3875+, accepts BOTH `modellist` and `model_list`): a `name | restriction | comment` table of every model under `MG5DIR/models` + `$PYTHONPATH` (dirs with `particles.py`) plus the online DB (`_online_model2`, populated here). Not a loaded-model inspector — a catalog of what is importable.
Also present: `processes`, `diagrams` (→ `self.draw`), `diagrams_text`, `couplings`, `lorentz`, `checks`, `options`, `variable`.

## do_convert_model (3483)
`do_convert_model <model_dir> [-f]` — in-place py2→py3 patch of a UFO model: rewrites
`object_library.py` (`.iteritems()`→`.items()`, old `raise X, "msg"` → `raise X("msg")`),
copies sm's `write_param_card.py`, ensures `__init__.py` imports object/function_library. Gated
by `auto_convert_model` option (default True) — when False and no `-f`, asks y/n first (warns it
can break the model under py2). The `do_import` model-loader triggers this automatically when it
hits a py2-only model; manual command is the escape hatch.

## do_tutorial (3971)
Toggles tutorial loggers by setLevel. `args[0]` in `{MadGraph5: logger_tuto, aMCatNLO:
logger_tuto_nlo, MadLoop: logger_tuto_madloop}` → INFO (others ERROR). Any other arg (incl.
`stop`/empty) → all to ERROR ("Thanks for using the tutorial!"). Tutorial text lives in
`tutorial_text*.py` modules (imported 82-84). `logger_tuto.info(..., '$MG:BOLD')` is the in-band
hint mechanism (also `Need help here? type 'help'` in SmartQuestion).

## do_open (madgraph 9098) — open a file with the OS viewer
`do_open <name>` → `check_open` resolves the real path, then `launch_ext.open_file(path)`
(delegates to the desktop opener; the `automatic_html_opening` option gates auto-opens
elsewhere, not this manual command). `check_open` (madgraph 1668) is the non-obvious bit:
- `./name` → must be an existing file, used verbatim.
- bare `name` with NO prior `output`/`launch` (`self._done_export` empty) → must be an
  existing file or `InvalidCmd("No command output or launch used...")`.
- otherwise resolves against the LAST export dir `self._done_export[0]`: tries
  `<path>/name`, then `<path>/Cards/name`, then `<path>/HTML/name` (1689-1694). So
  `open param_card.dat` finds it under `Cards/` without a path.
- AUTO-COPY: if the name contains `_card.dat` and the file is absent, it copies the
  matching `_card_default.dat` → `_card.dat` and opens that (1696-1697) — opening a card
  that was never generated materializes it from the default. madevent_interface has its own
  `check_open` (madevent 1050) with the same export-dir shape.

## do_load (madgraph 7679, "Not in help") — the do_save counterpart
`do_load model <file>` / `do_load processes <file>` unpickles via
`save_load_object.load_from_file` (7688) — the inverse of `do_save model`/`do_save processes`
(which pickle via `save_to_file`, config-system.md). `load model` distinguishes a UFO model
(has `parameters` → `_model_v4_path=None`) from a v4 model (resolves `_model_v4_path` via
`import_v4.find_model_path`, 7694). Restores `_curr_model`/`_curr_amps` from a prior save —
the persistence round-trip for the in-memory model/process state.

## do_edit_cards (madevent 2320) — card-editing entry into the AskRun widget
`do_edit_cards` is a thin madevent meta-command: `check_generate_events(args)` → mode, then
`ask_run_configuration(mode)`. The COMMAND dispatch + the fact it drives the AskRun
ControlSwitch card-editing menu is in-slice (see controlswitch-widget.md); the
`ask_run_configuration` body (which cards, defaults, downstream effects) is the launch slice's.

## do_quit (madevent) — the run-cleanup override chain
madevent's own `do_quit` (madevent_interface 6508) is a one-line delegate to
`common_run.CommonRunCmd.do_quit` (common_run_interface 3926), which is the run-cleanup layer:
unless `force_run`, removes the `RunWeb` lock file (`me_dir/RunWeb`); `store_result()`;
`update_status('', level=None)`; `gen_card_html()`; THEN `super().do_quit(line)` — the
`extended_cmd.Cmd.do_quit` cascade (command-loop-machinery.md). Aliases `do_EOF`/`do_exit`.
`__del__` (3953) also tries to remove `RunWeb` as a backstop unless `stop_for_runweb`/`force_run`.
So quitting a madevent run is NOT just a loop-stop — it tears down the web lock, flushes results,
and regenerates the HTML. NOTE the import is dual-named (`internal.common_run_interface` in
MADEVENT-standalone mode 61, `madgraph.interface.common_run_interface` in full-MG5 80) — same
class, two import paths depending on whether running from a process dir or the MG5 tree.

## SmartQuestion in-question `do_help` (extended_cmd 2250) — help typed AT a question
Distinct from the interface-level `do_help` above: a SmartQuestion widget has its OWN `do_help`
(2250) bound because the widget IS a `BasicCmd`. Typing `help` at a question lists the valid
answer Options (`list_completion(text, self.allow_arg)`) and the available commands
(`BasicCmd.completenames`), filtered by an optional prefix. This is the "Need help here? type
'help'" affordance (the tutorial-logger hint emits the same suggestion). ControlSwitch overrides
it with the per-switch help (controlswitch-widget.md).

See also: config-system.md (do_set/do_save/do_display-options); controlswitch-widget.md (the
AskRun widget do_edit_cards drives + ControlSwitch do_help); command-loop-machinery.md
(do_help/do_history/do_quit base meta-commands + the extended_cmd do_quit cascade madevent's
override ends in).
