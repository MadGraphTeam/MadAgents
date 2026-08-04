---
description: OrganizeModelExpression Stage 2 internals — the regex expression-shortening DSL (complexi/__exp__/cmath/conjg intermediates) and the find_dependencies event-dependent vs compute-once classification.
---

# UFO expression shortening + event-dependence (import_ufo.py, v3.7.1)

`OrganizeModelExpression` (`$MADGRAPH_INSTALL/models/import_ufo.py:2040`) is Stage 2 of the loader (Stage 1 = `UFOMG5Converter`). It takes the raw Python expression STRINGS in `Parameter.value` / `Coupling.value` and (a) rewrites them into shorter forms that introduce reusable intermediate `ModelVariable`s, and (b) classifies each as event-dependent or compute-once. Complements `ufo-loader-pipeline.md` (which only summarized this stage).

## main() order (l.2160)
`get_additional_CTparameters` (loop only) -> `analyze_parameters` -> `analyze_couplings` -> `revert_CTCoupling_modifications` (loop only). Returns `(self.params, self.couplings)`, each a dict keyed by the dependency-tuple.

## Event-dependence: track_dependant (l.2043)
`track_dependant = ['aS','aEWM1','MU_R']` at class level. These are the variables that change per phase-space point; anything depending on them (transitively) must be recomputed event-by-event. Augmented at runtime:
- `analyze_parameters` (l.2133): if `aEWM1` is NOT an external parameter, add `'Gf'` to the tracked set (l.2148-2150) — the Gmu/Gf input-scheme case.
- `mu_eff`: every external parameter in lhablock `loop` except `MU_R` is added (l.2151-2154).
- `__init__` (l.2071-2078): if the model has `all_running_elements`, every element name in every run object joins `track_dependant` (running-coupling models).

## find_dependencies (l.2248)
Splits the expression on `separator = re.compile(r'[+,\-*/()\s]+')` (l.2055) into bare tokens. For each token: if it is in `track_dependant`, add it to the dep set; else if it is a known `all_expr` entry with its own non-empty `.depend`, propagate those deps (skipping the `('external',)` marker). Returns a tuple — empty tuple = compute-once. The result keys the param/coupling into `self.params[deps]` / `self.couplings[deps]`.

**Non-obvious — unknown token = silent constant + a declaration-ORDER hazard** (l.2261-2270). A token that is NEITHER in `track_dependant` NOR a known `all_expr` entry contributes NO dependency and raises NO error — it's silently treated as a constant. AND the `all_expr` lookup requires the referenced expr to be ALREADY registered (`add_parameter` populates `all_expr` as it goes, l.2168-2182). Since `analyze_parameters` walks `self.model.all_parameters` in DECLARATION ORDER (l.2154), an internal param that references another internal param declared LATER in the UFO will not see it in `all_expr` yet -> its transitive event-dependence is silently lost. UFO convention (internal params declared after their dependencies) avoids this; a mis-ordered hand-edited UFO can silently mis-classify a param as compute-once. [static code-path hazard; no runtime error — re-walk a specific mis-ordered model to confirm the dropped-dependence symptom.]

## shorten_expr — the contraction DSL (l.2276)
Four regex substitutions applied in order; each `shorten_*` callback registers a NEW intermediate `ModelVariable` via `add_parameter` (dedup'd by name) and returns the short token. The point is to factor repeated sub-expressions so they're computed once.

1. **`complex_number`** (l.2048, `complex(re,imag)`): `shorten_complex` (l.2290) evaluates real/imag; if exactly `complex(0,1)` -> registers a single shared `complexi` ModelVariable and returns `complexi`. Otherwise leaves `complex(re,imag)` intact.
2. **`expo_expr`** (l.2049, `x**n`): `shorten_expo` (l.2303) -> token `x__exp__n` (the exponent's `.`/`+`/`-` are mangled to `_`/``/`_m_`; e.g. `MZ**2` -> `MZ__exp__2`, `x**-1` -> `x__exp___m_1`). A pure-digit base gets an `nb__` prefix to avoid starting with a digit. `cmath`-prefixed bases are left as `x**n` (not shortened).
3. **`cmath_expr`** (l.2050, `cmath.op(x)` with op usually sqrt/sin/cos/tan): `shorten_cmath` (l.2325) -> token `op__x` (e.g. `cmath.sqrt(2)` -> `sqrt__2`).
4. **`conj_expr`** (l.2052, `complexconjugate(x)`): `shorten_conjugate` (l.2342) -> token `conjg__x`, type forced `complex`.

`search_type` (l.2357) returns the recorded type of a known expr, else defaults `'complex'`. These intermediate names (`complexi`, `MZ__exp__2`, `sqrt__2`, `conjg__yu33`, …) are what you see in the generated Fortran/Python parameter files — they originate HERE, not in the UFO.

PROBE-CONFIRMED (in-process `import_ufo.import_model('sm')`): the loaded sm Model's parameter set contains `mdl_complexi`, `mdl_MZ__exp__2`, `mdl_MZ__exp__4`, `mdl_cw__exp__2`, `mdl_ee__exp__2`, `mdl_G__exp__2`, … — i.e. the `complexi`/`__exp__` intermediates, carrying the restriction-default `mdl_` prefix. (sm under restrict_default: 17 particles, 52 params, 56 interactions.)

## analyze_parameters / analyze_couplings split
- **External** params become `base_objects.ParamCardVariable` (name, value, lhablock, lhacode, optional scale) — read from the param_card, never shortened (l.2156-2160).
- **Internal** params and ALL couplings get `shorten_expr` + `find_dependencies`, then a `ModelVariable`. Couplings are always typed `'complex'`; internal params keep their declared type (l.2225-2228).

## Dict-valued couplings: dropped in tree mode, pole-expanded in loop mode (l.2199-2228)
A coupling whose `.value` is a Python **dict** (a Laurent series `{0:..., -1:..., -2:...}`) is handled by mode:
- **Loop model** (`self.perturbation_couplings` non-empty): each non-`'ZERO'` `coupling.pole(poleOrder)` for `poleOrder in 0..2` becomes a `copy.copy` of the coupling with `.value` set to that pole's expr; for `poleOrder != 0` the name gets a **lowercase** `"_%deps"%poleOrder` suffix (l.2214 -> `_1eps`/`_2eps`; the `for coupling` loop header is l.2206).
- **Tree model** (no perturbation): `couplings_list = [c for c in ... if not isinstance(c.value, dict)]` (l.2226) — dict-valued couplings are SILENTLY FILTERED OUT entirely. So a tree-mode load of a model carrying dict-valued (Laurent) couplings drops them with no error. (A value-TYPE decision at load, no number read — instance of `ufo-loader-keys-on-value-strings-not-numbers.md`.)

## Two distinct eps/FIN naming conventions — UPPER for params, lower for couplings
`pole_dict = {-2:'2EPS', -1:'1EPS', 0:'FIN'}` (`import_ufo.py:60`). PROBE-CONFIRMED exact.
- **CTPARAMETER pieces** (`get_additional_CTparameters`, l.2115-2133): iterate `pole in range(3)` = 0,1,2 but name with `pole_dict[-pole]` (l.2124) — the **`-pole` SIGN FLIP** maps idx 0->`FIN`, 1->`1EPS`, 2->`2EPS`. Suffix is `<name>_FIN_` / `<name>_1EPS_` / `<name>_2EPS_` — UPPERCASE, trailing underscore. Same pattern at l.553 (load_model EPS/FIN redefine) and l.1497.
- **CT-COUPLING pole pieces** (analyze_couplings suffix at l.2214; CT-vertex path `ufo-ct-vertex-loading.md` l.1635): suffix `_1eps` / `_2eps` — lowercase, no trailing underscore, finite piece unsuffixed.
So `_1EPS_` (param) and `_1eps` (coupling) are DIFFERENT objects with DIFFERENT conventions — do not conflate. The `-pole` flip is only in the param path; the coupling path uses `poleOrder` directly.

## Dead code: add_coupling (l.2184-2196)
`OrganizeModelExpression.add_coupling` references `self.coupling[...]` (SINGULAR) which is never assigned (the instance attribute is `self.couplings`, plural, l.2069). PROBE-CONFIRMED `'self.coupling[' in source`. It is NEVER CALLED — `analyze_couplings` inlines the add logic (l.2237-2247); if `add_coupling` were ever invoked it would `AttributeError`. Don't cite `add_coupling` as the coupling-registration path; the live path is the inline block.

## shorten_expr failure = critical + re-raise (l.2280-2287)
The four substitutions are wrapped in `try/except Exception: logger.critical("fail to handle expression: %s ...", expr, type(expr)); raise`. A malformed expression STRING does not load silently — it HALTS the load with a critical log and the original exception. [runtime critical text — probe before quoting verbatim.]

## aS-without-QCD warning (l.2234-2236)
In `analyze_couplings`, if a coupling's shortened expr depends on `aS` but the coupling's `order` dict has no `'QCD'` key:
`logger.warning('coupling %s=%s has direct dependence in aS but has QCD order set to 0. Automatic computation of scale uncertainty can be wrong for such model.', ...)`
Non-obvious: this is a soft warning, not an error — the model still loads. It flags a scale-variation mismatch (the QCD coupling-order weight wouldn't track the actual aS dependence). [runtime warning text — confirm via probe before quoting as fired output]

## Caution
The intermediate-variable names are a loader artifact: a stale `py3_model.pkl` may carry an OLD shortening of an expression even if the UFO `.value` strings were edited — the mtime/version_tag check (see `ufo-loader-gauge-and-pickle.md`) is what protects against that, not any re-parse of the expression.
