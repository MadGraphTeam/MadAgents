---
description: The Python-2 to Python-3 UFO auto-conversion — what triggers it (UFOError on import), where the converter lives (do_convert_model), and exactly which in-place patches it applies.
---

# UFO Py2 -> Py3 conversion (v3.7.1)

## Trigger
`models/__init__.py:load_model` wraps any model-import failure in `UFOError` (`$MADGRAPH_INSTALL/models/__init__.py:100-101`). The interface's `do_import` catches it at `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:5791` (`except ufomodels.UFOError as err`): if option `auto_convert_model` is True (default True, set at l.3096) it logs "fail to load model but auto_convert_model is on True. Trying to convert the model" (l.5794, source-verified) and retries (l.5793-5799); else it raises InvalidCmd telling the user to run `convert model <path>` or `set auto_convert_model T` (l.5806). The catch/retry ORCHESTRATION is interface/model-loader slice; the converter mechanics below are the in-slice boundary.

## Converter — do_convert_model (madgraph_interface.py:3483)
NOT a full `2to3`. It is a minimal in-place patch of a few known Py2-isms, done in place with NO success guarantee (the confirmation prompt at l.3492 warns it may break Py2 too). Steps:
1. `object_library.py`: `.iteritems()` -> `.items()` (l.3500); `raise Foo, "msg"` -> `raise Foo("msg")` via regex (l.3502-3503).
2. Copy sm's `write_param_card.py` over the model's (l.3508-3509).
3. `__init__.py`: prepend `import object_library` / `import function_library` if absent (l.3511-3520).

That's the whole transform. It does NOT touch `print` statements, division semantics, or relative-import syntax in particles/couplings/etc. — models needing more than this will still fail after conversion. The conversion writes files in place (model dir mutated on disk), which then invalidates pickle mtime caches.

## Caution
The converter only fixes object_library + __init__ + write_param_card. A genuinely Py2-only UFO (e.g. one using `print "x"` in parameters.py) will not be salvaged by this path. The retry after conversion can still surface UFOError; the user-facing message then points at manual conversion.
