---
description: The UFO model file set — required/optional files, the object_library classes they instantiate, and what each declares (particles, parameters, couplings, lorentz, vertices, orders, decays, propagators, functions).
---

# UFO model file structure (v3.7.1)

A UFO model lives at `$MADGRAPH_INSTALL/models/<name>/`. Files instantiate classes from the model's own `object_library.py`; each class appends itself to a module-global `all_*` list at construction (`$MADGRAPH_INSTALL/models/sm/object_library.py`).

## Required files (loader raises UFOImportError if missing)
Checked in `import_full_model` (`$MADGRAPH_INSTALL/models/import_ufo.py:338-351`). Required: `couplings.py`, `lorentz.py`, `parameters.py`, `particles.py`, `vertices.py`, `function_library.py`. **Optional** (silently skipped if absent): `propagators.py`, `coupling_orders.py`, `decays.py` (decays only requested when `decay=True`).

## object_library classes (`sm/object_library.py`)
- `Particle` (l.66) require_args: pdg_code, name, antiname, spin, color, mass, width, texname, antitexname, charge. spin is 2S+1 (1=scalar, 2=fermion, 3=vector, 5=spin-2, -1=ghost); color in {1,3,-3,8}. `charge` cast to float. `.anti()` builds the antiparticle (l.127), negating quantum numbers; selfconjugate iff name==antiname. `find_line_type` (l.96) picks the Feynman-diagram line from spin/color.
- `Parameter` (l.146): name, nature ('external'|'internal'), type ('real'|'complex'), value, texname; external requires `lhablock`+`lhacode` else raises (l.161).
- `Vertex` (l.168): name, particles (list), color (list of color strings), lorentz (list), couplings (dict keyed `(color_idx, lorentz_idx) -> Coupling`). See `sm/vertices.py`.
- `Coupling` (l.185): name, value (Python expr string), order (dict like `{'QED':2}`). See `sm/couplings.py`.
- `Lorentz` (l.200): name, spins (list, same 2S+1 convention), structure (string DSL, e.g. `'Gamma(3,2,1)'`, `'ProjM(2,1)'`). See `sm/lorentz.py`.
- `Function` (l.214): name, arguments, expression — extends cmath. `sm/function_library.py` ships complexconjugate, re, im, sec, asec, csc, acsc. `__call__` (l.225-230) `exec`s each `arg = value` binding then `eval`s `self.expr` — so a function-library function is evaluated by binding its formal args into the local namespace and evaluating the stored expression string. This is how `complexconjugate(...)`, `sec(...)`, etc. inside parameter/coupling expressions resolve at compute time. The loader copies the raw `ufo_model.all_functions` straight onto the Model (`import_ufo.py:421`, `model.set('functions', ...)`) — functions are NOT shortened or dependency-classified like parameters/couplings.
- `CouplingOrder` (l.234): name, expansion_order, hierarchy, perturbative_expansion (default 0; >0 marks a loop/perturbed order). sm declares QCD(hierarchy 1) and QED(hierarchy 2) in `coupling_orders.py`.
- `Decay` (l.247): particle, partial_widths (dict `(prod1,prod2,...) -> width-expr string`); on construction writes `particle.partial_widths` directly (l.258). **Attachment at load** (`import_ufo.py:426-438`): ONLY when `import_full_model(..., decay=True)` AND `ufo_model.all_decays` is non-empty. The loader then walks `ufo_model.all_particles`, looks up the matching loaded MG5 particle by name (`model['particles'].find_name(name)`, name lower-cased if `not model['case_sensitive']`) and copies `partial_widths` onto it; particles with no UFO `Decay` get `partial_widths = {}`. `decays.py` is added to `files_list_prov` and imported only under `decay=True` (l.342-343), and `decay` is part of the pickle key + `_import_once` tuple — so a decay-aware load and a plain load use different pickles. What MG5 does with `partial_widths` (auto-width computation) is param-card / width-computation territory; the loader's job stops at attaching the dict.
- `FormFactor` (l.262): name, type, value (referenced from lorentz.py via optional `import form_factors`).
- `Propagator` (NOT in sm's object_library — only in propagator-capable models). Among the shipped set only `taudecay_UFO` carries it: `taudecay_UFO/object_library.py` defines `class Propagator`, and `taudecay_UFO/propagators.py` declares the instances (name, numerator, denominator expr strings). (2HDM/EWdim6/heft are NOT in the reliable shipped core and come and go across builds — `ls models/` and see `ufo-shipped-models-and-model-db.md` for the roster.)

## __init__.py and gauge option
`sm/__init__.py` imports each submodule, re-exports the `all_*` lists, and declares the model-level `gauge = [0, 1]` (0=unitary, 1=Feynman supported). decays/build_restrict imported under try/except.

## Loop-capable models
Ship extra files consumed for R2/UV counterterms: `CT_couplings.py`, `CT_parameters.py`, `CT_vertices.py` (see `loop_sm/`). `CT_parameters.py` declares `CTParameter` with a pole dict `value = {0:'...', -1:'...', -2:'...'}` (0=finite, -1=single pole, -2=double pole). What MadLoop does with them is nlo-model/madloop slice.

## Particle count caution
The file declares MORE particles than the loaded model keeps: sm `particles.py` declares explicit `Particle(...)` plus one `.anti()` each (count them), but the loaded model keeps fewer in unitary gauge — Goldstones and ghosts are dropped at load (see `ufo-loader-gauge-and-pickle.md`). The MECHANISM (raw declares more, loader drops gauge-artifacts), not the integers, is the durable fact — re-count per model/gauge.
