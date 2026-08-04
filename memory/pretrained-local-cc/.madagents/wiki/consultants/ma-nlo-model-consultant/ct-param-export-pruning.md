---
description: Export-side CTParameter pruning - build(wanted_couplings)->extract_needed_CTparam->check_needed_param drops CTParams not referenced by the process's used CT couplings (and notused_ct_params) from the written Fortran model; complement to import-side map_CTcoup_CTparam building.
---

# CTParameter export pruning (process directory only carries used CT params)

(v3.7.1, `$MADGRAPH_INSTALL`.) The import side BUILDS `map_CTcoup_CTparam`
(coupling -> [CTparam names], see ctparameter-eps-fin-expansion). This page is the
**export-side complement**: at `output` time the Fortran model writer uses that map to
write ONLY the CTParameters that the process's actually-used CT couplings reference.
A CTParameter present in the UFO but unused by this process is silently dropped from the
generated model files — it never reaches the process directory.

## The pruning chain (`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py`)
1. **build(wanted_couplings)** (7081-7093): the model exporter's entry. If `wanted_couplings`
   is non-empty (i.e. a specific process selected a coupling subset), it calls
   `extract_needed_CTparam(wanted_couplings)` BEFORE `write_all()`.
2. **extract_needed_CTparam** (7528-7557): reads `self.model.map_CTcoup_CTparam`.
   - `self.allCTparameters` = every CTparam appearing in ANY CT coupling (flattened map
     values, deduped, lowercased).
   - `self.usedCTparameters` = CTparams appearing only in the CT couplings whose name is in
     `wanted_couplings` (case-insensitive).
   - If the model has no `map_CTcoup_CTparam` OR `wanted_couplings` is empty -> both set to
     `None`, which DISABLES filtering (everything written). So a full-model export (no
     process) keeps all CTparams; only a process-scoped export prunes.
3. **check_needed_param(param)** (7488-7526): the per-parameter gate, called at every
   parameter-write site (7458, 7477, 7624, 7651, 9672, 9678).
   - Short-circuit (7495-7498): if `allCTparameters`/`usedCTparameters` is `None` or empty
     -> return True (LO model or no-CT NLO model: nothing to filter, write it).
   - Conjugate shorthand (7506-7507): tries both `param` and `param` with a leading
     `conjg__` stripped, so the complex-conjugate alias of a CTparam is matched too.
   - If `param` is NOT a CTparameter at all (not in `allCTparameters`): normally return True
     (ordinary params always written), EXCEPT the `notused_ct_params` drop below.
   - If it IS a CTparameter: return True only iff it is in `usedCTparameters` (i.e. used by
     a wanted CT coupling). Otherwise the write site does `continue` and skips it.

## notused_ct_params: the per-pole base-name decode (7512-7521)
`notused_ct_params` (built import-side at import_ufo.py:1553-1556) lists CTParameters that
appear in NO coupling at all. The export-side check has to map a *pole-expanded* parameter
name (`<base>_FIN_`, `<base>_1EPS_`, `<base>_2EPS_`, or coupling-suffix `_1eps`/`_2eps`)
back to its base to test membership:
```python
if param.endswith(('_fin_','_1eps_','_2eps_')):  limit = -2
elif param.endswith(('_1eps','_2eps')):          limit = -1
else:                                            limit = 0
base = '_'.join(param.split('_')[1:limit])
if base in self.model.notused_ct_params: return False
```
Note `split('_')[1:limit]` also drops the FIRST token (index 0) — it strips a leading
prefix as well as the trailing pole tag to recover the base name used in the
`notused_ct_params` list. So a never-referenced CTparam is dropped at export even though it
isn't a "CTparameter" in `allCTparameters` (it's in neither map value).

## ct_params double-write guard (7642-7651)
In the parameter-recompute block, dependent CT params are collected once into `ct_params`
(7643-7645, gated by `check_needed_param` AND membership in `allCTparameters`), then the
generic `params_dep` loop SKIPS anything already in `ct_params` (7651) — so a needed CT
param is written exactly once in the loop section, not duplicated.

## CAUTIONS (source-visible hazards, NOT runtime claims)
- **Dead attribute:** `coupling_orders_counterterms` is declared at
  loop_base_objects.py:1442 with a detailed docstring but is **never populated or read**
  anywhere in the tree (grep finds only the declaration). Reserved/abandoned; do not chase
  it as a live data path.
- **Latent dict-iteration bug at export_v4.py:6993** in `refactorize`'s duplicate-name
  handler: `for coup, ctparams in self.model.map_CTcoup_CTparam:` iterates the dict
  DIRECTLY (yielding keys = coupling-name strings), then unpacks each string into two vars.
  For a non-empty map this would raise `ValueError`/unpack error unless every key is a
  length-2 string. It is guarded only by `hasattr`, not non-emptiness. Reachable only when
  duplicate (case-insensitive) parameter names force the rename path AND a CT map exists.
  PROBE-CANDIDATE (needs a loop model with case-colliding param names + CT params); not
  yet observed firing. Treat as a hazard pointer, not a runtime prediction.

## Boundary
- Static export-time mechanism: predicts WHICH CTParameters are written / skipped in the
  process-directory Fortran model, by name. It does NOT predict numeric values or that a
  given process actually triggers pruning (that depends on the wanted_couplings set, which
  the diagram-gen / export selection produces). The drop itself is source-confirmed;
  per-process which-params-survive is a probe-candidate.
- Import-side building of map_CTcoup_CTparam / notused_ct_params is ctparameter-eps-fin-
  expansion's territory; this page is only their consumption at output.
