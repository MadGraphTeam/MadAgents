---
description: UFOError recovery path in do_import — auto_convert_model retry via 'convert model', the InvalidCmd guidance when auto-convert is off, and do_convert_model's confirmation prompt being silently skipped on the auto-convert path.
---

# UFOError → auto-convert recovery (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:5791-5806`,
inside the UFO branch `try:` wrapping `import_ufo.import_model(...)`.

Trigger: `import_ufo.import_model` raises `ufomodels.UFOError` (typical cause: a
Python-2-only UFO model that fails to import under py3).

On catch:
1. `model_path, _, _ = import_ufo.get_path_restrict(args[1])` (`:5792`) — resolve the on-disk model path (strips any `-restriction`).
2. **If `self.options['auto_convert_model']`** (default `True`, `:3096`) (`:5793-5804`):
   - `logger.info("fail to load model but auto_convert_model is on True. Trying to convert the model")`.
   - `self.exec_cmd('convert model %s' % model_path, errorhandling=False, printcmd=True, precmd=False, postcmd=False)` (`:5796`) — runs the py2→py3 conversion in place on the model directory. [convert-model internals are not this slice's source; this slice owns the dispatch.]
   - `logger.info('retry the load of the model')`.
   - Build `tmp_opt = dict(self.options)` with `tmp_opt['auto_convert_model'] = False` (`:5798-5799`) so the retry will NOT loop.
   - Under `misc.TMP_variable(self, 'options', tmp_opt)` re-run the ORIGINAL line: `self.exec_cmd('import %s' % line, ...)` (`:5800-5802`).
   - If the retry itself raises any `Exception` → `raise err` (re-raise the original UFOError) (`:5803-5804`).
3. **Else (auto_convert_model False)** (`:5805-5806`):
   - `raise self.InvalidCmd('UFO model not python3 compatible. You can convert it via the command \nconvert model %s\nYou can also type "set auto_convert_model T" to automatically convert all python2 module to be python3 compatible in the future.' % model_path)`.

## The `convert model` target (`do_convert_model`, :3483)
`do_convert` (`:3474`) dispatches `do_convert_<sub>`; `do_convert_model` (`:3483`) does the
in-place py2→py3 edits (`.iteritems()`→`.items()`, `raise X, "msg"`→`raise X("msg")`, etc.,
`:3497+`). Its **confirmation prompt is silently skipped on the recovery path**: the guard is
`if not ('-f' not in args or self.options['auto_convert_model']):` (`:3491`).
**CORRECTED truth-table** (the `-f` term was previously stated backwards here — re-derived
and probe-emulated): the prompt fires when `('-f' not in args or auto_convert)` is False,
i.e. when **`-f` IS PRESENT AND `auto_convert_model` is False** — the single case below:

| args | auto_convert | prompt fires? |
|------|--------------|---------------|
| no `-f` | False | NO |
| no `-f` | True  | NO |
| `-f`    | False | **YES** |
| `-f`    | True  | NO |

So the prompt is effectively **dead unless the user explicitly passes `-f`** (an inverted-
`-f` quirk in MG itself — `-f` normally *suppresses* prompts; here it is the only thing that
*enables* this one). The recovery dispatch calls `convert model <path>` with NO `-f` (page
top, `:5796`) → top-left/right cells → prompt never fires regardless of auto_convert. Net:
auto-convert mutates the model directory on disk **without asking the user**.
**CORRECTION:** a manual `convert model <path>` with auto_convert OFF does **NOT** prompt
either (no `-f` → top-left cell) — the previous claim that it "DOES prompt" was wrong-
direction. Only `convert model <path> -f` with auto_convert off prompts.

## Cautions
- The retry re-dispatches the FULL original `line` (preserving any `-restriction`, `--noprefix`, `-modelname`), not just `model_path`. So the restriction/prefix/options chosen by the user survive the conversion retry.
- `convert model` mutates the model directory on disk (in-place conversion); a subsequent import in a fresh session will hit the already-converted py3 files.
- The retry's failure mode masks the conversion error and surfaces the ORIGINAL UFOError, not the post-convert error — diagnosing a conversion that "didn't help" needs running `convert model` manually.
