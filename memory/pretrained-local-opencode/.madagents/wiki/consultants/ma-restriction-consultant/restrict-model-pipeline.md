---
description: RestrictModel.restrict_model step ordering and the operative-vs-declared model state it produces (import_ufo.py v3.7.1)
---

# RestrictModel.restrict_model — step ordering

`class RestrictModel(model_reader.ModelReader)` at `$MADGRAPH_INSTALL/models/import_ufo.py:2365`.
Docstring (2366-2371) states the three rules: zero-coupling vertices thrown away;
external params with zero/one input → internal; identical coupling/mass/width → single one.

Entry: `restrict_model(param_card, rm_parameter=True, keep_external=False, complex_mass_scheme=None)` (2390).
Step order as coded:

1. `2398-2399`: if model name == "mssm" and not keep_external → `raise Exception` (mssm must be restricted with keep_external).
2. `2401-2403`: store `self.restrict_card`; re-`set('particles', ...)` to resync particles/interactions.
3. `2407-2409`: `set_parameters_and_couplings(param_card, complex_mass_scheme=..., auto_width=self.modify_autowidth)` — computes all numeric param/coupling values from the restrict card. Auto-widths collected via the callback (see autowidth-restore.md).
4. `2412-2417`: simplify conditional (`if`) statements in UFO expressions using restrict-card default values — `detect_conditional_statements_simplifications` (2665-2707) builds a `parsers.UFOExpressionParserPythonIF(model_definitions)` and constant-folds `if` branches against the restrict-card defaults, returning `(param, new_expr)` pairs for NON-external params (external skipped, 2680-2681) and for ALL couplings; `apply_conditional_simplifications` (2646-2663) writes them back into `param.expr`/`coupl.expr`. Effect: downstream zero/identical detection sees the simplified exprs, so a coupling whose `if` collapses to 0 under the restrict defaults becomes prunable.
5. `2420`: `locate_coupling()` → builds `self.coupling_pos` = {coupling_name → [vertex | (particle, ct_key)]}.
6. `2422`: `detect_identical_couplings()` → returns `(zero_couplings, iden_couplings)`.
7. `2425`: `remove_interactions(zero_couplings)` — drop/trim vertices+counterterms losing a zero coupling.
8. `2428-2429`: `merge_iden_couplings` for each identical group (rewrites vertex coupling names, tracking +/- sign).
9. `2432-2433`: accumulate zero couplings into `self.del_coup`, `remove_couplings(self.del_coup)` cleans the coupling list.
10. `2436-2437`: `optimise_interaction` per interaction — fuse two lorentz structures sharing one coupling (creates merged lorentz, see lorentz-merge-and-add.md).
11. `2440-2442`: `detect_special_parameters()` → `(null, one)` external params; `fix_parameter_values(...)` replaces them with 0.0/1.0 internals or removes.
12. `2444-2452`: `detect_identical_parameters()` + `merge_iden_parameters` — run once without keep_external (only if not keep_external), then again WITH keep_external flag. Two passes.
13. `2457-2461`: magic-value un-escaping in `parameter_dict`: `9.999999e-1 → 1`, `0.000001e-99 → 0` (these values are used in restrict cards to AVOID being treated as zero/one).
14. `2467-2475`: restore auto-width — for external DECAY params whose lhacode was collected in `self.autowidth`, set value back to `'auto'`.
15. `2478-2489`: rebuild `coupling_orders` cache; warn if some coupling order lost all couplings ("will not be valid anymore for this model").
16. `2491-2496`: if a sibling `param_<...>.dat` exists (param_card replacing 'restrict'→'param'), re-load default values from it.

## Operative vs declared
After this runs, `_curr_model` holds the OPERATIVE model: pruned vertices, zero/one params turned internal, masses/widths merged, auto-width restored. The DECLARED model is the unrestricted UFO (re-importable). The restriction modifies the IN-MEMORY model only; it does NOT rewrite the param_card. The `self.rule_card` (ParamCardRule) accumulated during steps 11-12 is what later validates the user-edited param_card. See param-card-rule.md.

## Model-load-time constraint (hard rule)
Restriction runs at import time (`import_model` → `restrict_model` at `import_ufo.py:256-257`).
It modifies `_curr_model` in memory — prunes vertices, converts 0/1 externals to internals, merges
identical couplings/masses/widths. A parameter removed or converted during restriction is GONE from
the operative model; a post-load `set <param> <val>` or param_card edit cannot resurrect it. The
param_card is consumed AGAINST the restricted model, not the unrestricted one. Fix is always
model-load-time: import the correct restricted variant or supply a custom restrict card.

## Naming convention
`restrict_FOO.dat` in model X → import tag `X-FOO`. The tag is the filename stem minus `restrict_`
and `.dat` — no transformation, no synonym, no alternate spelling. Source: `import_ufo.py:get_path_restrict`
lines 218-220 (tag extraction + file path), line 257 (model name append). Inventing a tag that does not
match a shipped file stem is a hallucination. `sm-no_b_mass` is the tag for `restrict_no_b_mass.dat`,
NOT `sm-no_lepton_masses` (which would require `restrict_no_lepton_masses.dat` — absent).
