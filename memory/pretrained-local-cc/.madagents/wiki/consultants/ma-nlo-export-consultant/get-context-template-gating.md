---
description: get_context contextual booleans (LoopInduced/ComputeColorFlows/AmplitudeReduction/TIRCaching/MadEventOutput) + FortranWriter ## preprocessor — how loop-template code blocks are gated, plus optimized/loop-induced overrides and set_group_loops.
---

# get_context template-gating mechanism (v3.7.1)

The loop exporters do NOT have one template per mode. They have ONE set of `.inc` templates carrying `##`-prefixed preprocessor directives, and `get_context(matrix_element)` returns the boolean dict that decides which directive-guarded blocks survive. This is the central "which code path does the loop V-dir emit" switch — it sits upstream of nearly every conditional write in `loop_exporters.py`.

## The mechanism (FortranWriter side)
`writers.FortranWriter.writelines(lines, context={}, ...)` (`file_writers.py:96`) — if `len(context)>0`, calls `preprocess_template` (`:113`-114).
`preprocess_template(input_lines, context={})` (`file_writers.py:124`) processes lines starting with `##` (`:126`). For an `##if` directive it does `eval(preproc_command.group('body'), globals(), context)==True` (`:163`) — the directive body is a **Python expression `eval`'d against the context dict**. So the context booleans are literally evaluated as Python in the template. A bad expression raises ("python expression '%s' ... given the context %s", `:166`).

So: exporter computes `get_context(me)` → passes it as `context=` to `writer.writelines(file, context=...)` → FortranWriter eval's the `##if` bodies → only matching blocks are written.

NB the SAME FortranWriter preprocessor mechanism is fed by a DIFFERENT, smaller context dict elsewhere: `copy_fkstemplate` passes `context={'collier_available': ...}` to MadLoopCommons.f (`export_fks.py:218` base / `:4878` optimised — see copy-fkstemplate-and-scaffolding.md). It is the same `##if` eval path (`file_writers.py:163`), not the 5-boolean get_context dict. `export_v4.py` (LO output, out of slice) also uses `writelines(context=...)`. So "context=" passing is the general preprocessor hook; get_context is just the loop-V-dir caller of it.

## get_context — base (loop_exporters.py:791, LoopProcessExporterFortranSA)
Returns a boolean dict (the keys enumerated below), derived in a chain (the derivation is the non-obvious part):
- `LoopInduced = not matrix_element.get('processes')[0].get('has_born')` (`:805`). A process with no born is loop-induced. Also OR-accumulated into `self.has_loop_induced` (`:806`).
- `ComputeColorFlows = self.compute_color_flows or LoopInduced` (`:808`). Loop-induced FORCES color-flow computation.
- `AmplitudeReduction = LoopInduced or ComputeColorFlows` (`:811`). Comment: "just to make the contextual conditions more readable." (Given the line above, this is effectively `ComputeColorFlows`.)
- `TIRCaching = AmplitudeReduction or n_squared_split_orders>1` (`:814`). TIR caching is on if reducing at amplitude level OR >1 squared split-order combo. `n_squared_split_orders` read from `matrix_element.rep_dict['nSquaredSO']`, falling back to a default if missing (`:800`-803, read the literal there).
- `MadEventOutput = False` (`:815`) on the standalone base.

## get_context — optimized override (loop_exporters.py:1795, LoopProcessOptimizedExporterFortranSA)
`super().get_context()` then ADDS (`:1799`-1813):
- `ninja_supports_quad_prec` = `misc.get_ninja_quad_prec_support(self.ninja_dir)`, or `False` on AttributeError (`:1803`-1807).
- `<tir>_available` for each `tir in self.all_tir` = `self.tir_available_dict[tir]` (`:1809`-1810). Raises MadGraph5Error if a `tir` is not in the interfaced TIR-name set (`:1812`, read the names there).

## get_context — loop-induced override (loop_exporters.py:3075, LoopInducedExporterME)
`super().get_context()` then forces `context['MadEventOutput'] = True` (`:3080`) — flips the loop ME templates into MadEvent-integration mode. (Also on exporter-class-hierarchy.md.)

## What the booleans gate (Python-side decisions, optimized class)
Beyond the `##`-template blocks, get_context also drives Python branches:
- `set_group_loops` (`:2038`): `group_loops = (not get_context(me)['ComputeColorFlows']) and has_born`, unless `forbid_loop_grouping` (`:2043`-2047). So loops with shared denominators are grouped ONLY when not computing color flows AND there is a born — i.e. loop-induced/color-flow processes never group loops.
- `compute_color_flows.f` written only if `get_context(me)['ComputeColorFlows']` (write_loop_matrix_element_v4 `:2153`).
- `tir_cache_size.inc` written only if `get_context(me)['TIRCaching']` (`:2169`).
- GOLEM `loop_induced_sqsoindex` = `''` if `AmplitudeReduction` else `',SQSOINDEX'` (write_GOLEM_interface `:2329`).
- write_global_specs writes a MadEvent-only block only if `get_context(me)['MadEventOutput']` (`:2643`).
- HELASCALLS split (`:2970`) and CT/TIR/COLLIER/GOLEM interface writers all pass `context=get_context(me)` to writelines (`:2212`/`:2276`/`:2315`/`:2351`).

## Cautions
- `get_context` is RE-CALLED at every use site (it is cheap and stateless except for the `self.has_loop_induced` OR-accumulate at `:806`). It is not cached in a field; if `matrix_element.rep_dict['nSquaredSO']` changes between calls, `TIRCaching` can change. The comment at `:795`-799 notes nSquaredSO must be set in `write_loopmatrix` before the first call or it falls back to the default (`:800`-803).
- The `##` directives are Python `eval`'d (`file_writers.py:163`) — a typo in a template directive body or a context key the template references but get_context didn't set raises a hard error at write time, not silently. The optimized override deliberately seeds `<tir>_available` so templates can test `golem_available` etc.
- `AmplitudeReduction == ComputeColorFlows` in practice (both equal `compute_color_flows or LoopInduced` once you substitute `:808` into `:811`). The two names exist for template readability; don't assume they can diverge.
- Standalone base has `MadEventOutput=False`; only LoopInducedExporterME (and its Group/NoGroup leaves) flip it True. A plain NLO virtual V-dir is NOT MadEventOutput.
