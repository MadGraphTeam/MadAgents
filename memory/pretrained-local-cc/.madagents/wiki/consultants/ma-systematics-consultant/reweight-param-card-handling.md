---
description: ReweightInterface handle_param_card layer — bridges reweight_card to the ME core — param_card scan iterator (ParamCardIterator), Auto-width resolution, banner card-diff + dup-tag/alphaS warnings, per-f2py-module parameter injection (initialise/change_para/update_all_coup), NLO running-info update.
---

# ReweightInterface param_card handling (handle_param_card)

`$MADGRAPH_INSTALL/madgraph/interface/reweight_interface.py`, v3.7.1, `handle_param_card` (ri.py:802-1047). The layer BETWEEN the command parser (`reweight-interface` page) and the per-event ME evaluation (`me-reweight-evaluation-core` page). Called once per `launch` from `do_launch` (ri.py:541). It (1) obtains the new param_card, (2) detects/expands a scan, (3) resolves Auto widths, (4) computes the banner card-diff and writes the `mg_reweighting` weightgroup header, (5) injects every parameter into each compiled f2py ME module. Returns `(param_card_iterator, tag_name)`.

## Where the new card comes from (ri.py:805-829)
- `rw_dir` = `<me>/rw_me` normally; `<me>/rw_me_<nb_library>` if `second_model`/`second_process`/`dedicated_path` set (ri.py:810-813).
- No `--keep_card` in args → writes the banner's original SLHA to `rw_dir/Cards/param_card.dat`, then interactive edit via `ask_edit_card_static(cards=['param_card.dat'], write_file=False, return_instance=True)`; `card = cmd.param_card` (ri.py:814-825). The interactive `set BLOCK ID VALUE` lines from `reweight_card.dat` are replayed through `self.stored_line`.
- `--keep_card` + `self.new_param_card` set → uses `self.new_param_card.write()` (this is the SCAN re-entry path: `do_launch` scan loop calls `launch --keep_card` with `new_param_card` already set; see below).
- else → reads the file already on disk.

## param_card scan (ri.py:831-852) — the scan: iterator
- Detect: `pattern_scan = re.compile(r'''^(decay)?[\s\d]*scan''', re.I+re.M)`; any `scan` line (or `decay ... scan`) in the new card triggers it.
- **Web guard**: if `self.mother` is not a `CmdShell` (interactive shell) → `raise Exception("scan are not allowed on the Web")` (ri.py:841-842). Scans only run from a real shell.
- Builds `main_card = check_param_card.ParamCardIterator(new_card)` (class at `models/check_param_card.py:931`); `first_card = param_card_iterator.next(autostart=True)`; sets `self.new_param_card = first_card`. The first scan point's card becomes the active `new_card`; the iterator is returned to `do_launch`.
- If `rwgt_name` set, it is suffixed `_0` for the first point (ri.py:845-846).
- **The scan loop lives in `do_launch`** (ri.py:753-766), NOT here: `for i,card in enumerate(param_card_iterator): self.new_param_card = card; self.exec_cmd("launch --keep_card", precmd=True)`. Each scan point is a full re-`launch` (re-enters `handle_param_card` via the `--keep_card`/`new_param_card` branch). `rwgt_name` per point = `<base>_<i+1>` (i+1 because point 0 already ran) (ri.py:759-761). After the loop `rwgt_name` reset to None.
- `ParamCardIterator.iterate` (check_param_card.py:968+): parses `scan id: [list]` via `scan\s*(?P<id>\d*)\s*:\s*(?P<value>[^#]*)`; `eval(def_list)` the bracket expression (a python list/range) — **arbitrary python eval on the scan RHS**; same-`id` scans iterate together (zipped), different ids form the Cartesian product. Bare `scan:` (no id) gets a unique negative key (independent axis).

## Auto widths (ri.py:854-867)
- After scan expansion: if the lowercased card (past the first `block`) contains `"auto"` → write the card to disk and call `self.mother.check_param_card(path)` to resolve `Auto` widths to computed values, then re-read. (`check_param_card` runs the width computation — delegated to the mother interface, NOT in this slice's code.)
- If `'block' not in new_card.lower()` → `raise Exception(str(new_card))` — malformed card guard (ri.py:855-856).

## Banner card-diff + the mg_reweighting header (ri.py:870-983)
- If `initrwgt` already has a `mg_reweighting` weightgroup, it is split out and existing weight ids parsed; `maxid+1` becomes the next `rewgtid` so new weights don't collide (ri.py:872-887). Mirrors the systematics `get_id` max-scan logic but for the reweight group.
- **Duplicate-tag overwrite** (ri.py:889-896): if `rwgt_name` matches an existing id (for any `type_rwgt` suffix), `logger.warning("tag %s%s already defines, will replace it")` and the old entry is removed — re-launching with the same `--rwgt_name=` REPLACES the prior weight, does not error.
- `card_diff` source (ri.py:921-957):
  - `rwgt_info` option set → diff text = the user's `--rwgt_info=` string verbatim.
  - else, no second_model/dedicated_path → `card_diff = old_param.create_diff(new_param)` (`models/check_param_card.py:560`), the human-readable block/id/old→new diff written into the weight body. **Empty diff** (and no second_process) → `logger.warning(' REWEIGHTING: original card and new card are identical.')` — a no-op reweight warns but proceeds.
  - **alphaS-mismatch warning** (ri.py:931-933): condition is **signed, NOT absolute** — `old sminputs(3) - new sminputs(3) > 1e-3*new` (verbatim ri.py:931, no `abs()`). So it fires only when the OLD card's αs(MZ) exceeds the new card's by >0.1% of new; a new card with a *larger* αs(MZ) than the original does NOT trigger the warning. Body: `logger.warning("We found different value of alpha_s. Note that the value of alpha_s used is the one associate with the event and not the one from the cards.")`, wrapped in `try/except` (any error → `logger.debug` + pass, ri.py:934-936). Confirms the header note: a different αs(MZ) in the new card is IGNORED (event αs used). Just a warning.
  - second_process → diff prefixed with `change process` lines; second_model/dedicated_path → diff = the `change model/process/<key>` directives plus the full new card (ri.py:944-957).
- Weight header lines (ri.py:961-982): `<weightgroup name='mg_reweighting' weight_name_strategy='includeIdInWeightName'>` (or `name='main'` if `output_type != 'default'`); per (tag,suffix): `<weight id='rwgt_<tag><suffix>'>diff</weight>` if tag is a digit, else `<weight id='<tag><suffix>'>diff</weight>`. (Sudakov branch differs — see `ew-sudakov-reweight`.)

## Per-module parameter injection (ri.py:998-1047)
The load-bearing step that actually pushes the new parameters into each compiled f2py ME module. For every `(path,tag)` in `self.f2pylib`, inside `chdir`+muted stdout:
- Picks `param_card = self.new_param_card` for `'rw_me_'` dirs or `tag==3` (the NEW hypothesis module), else the ORIGINAL card (`tag==2`, original-hypothesis module) (ri.py:1003-1006). This is how the same event gets both `w_orig` (orig module) and `w_new` (new module) in `calculate_matrix_element` (`hypp_id` selects the module).
- `module.initialise('../Cards/param_card.dat')` then loops every block/param: `module.change_para('<BLOCK>_<lhacode>', value)`; block scale → `change_para('mdl__<BLOCK>__scale', scale)` (ri.py:1007-1018). `qnumbers` block skipped.
- **NLO running-info update** (ri.py:1020-1046): when `update_running_info` (no model, or `model['running_elements']`), pushes run_card running params into the module: `set_fixed_extra_scale`, `set_mue_over_ref`, `set_mue_ref_fixed`, `set_maxjetflavor`, `set_asmz(sminputs(3))`, `set_nloop(2)`. Failure raises only if a model is set.
- `module.update_all_coup()` recomputes all couplings from the injected params (ri.py:1046). This is where a changed mass/coupling becomes a changed matrix element.

## Cautions
- **Scan RHS is `eval`'d** (check_param_card.py:987) — arbitrary python in `scan: [...]`; blocked on Web but live in a shell.
- **`--rwgt_name=` collision = silent overwrite** (warning only): re-reweighting with a reused name replaces the earlier weight in the banner; no error.
- **Identical card = warning, not skip**: an empty `create_diff` still runs the reweight (emits a weight equal to nominal up to numerical noise) — `logger.warning('original card and new card are identical')`.
- **αs(MZ) change ignored**: only a warning; event αs (`event.aqcd`) is always used in the ME (consistent with `me-reweight-evaluation-core`). The warning's trigger is the *signed* `old-new > 1e-3*new` (fires only when old αs is the larger), NOT a symmetric `|old-new|` — do not read it as a two-sided mismatch check.
- Auto-width resolution is delegated to `mother.check_param_card` (mother interface), not this module — a width set to `Auto` is computed there, not by the reweight ME path.
- RUNTIME claims (emitted warning text, the actual weightgroup bytes, scan-loop weight ids) are read from source, not probe-confirmed; a scan reweight_card launch would confirm the per-point weight ids and the warnings.
