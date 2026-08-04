---
description: EFT operator running (RGE) support in MG5_aMC v3.7.1 — UFO all_running_elements hook, model get_running grouping, the conditional RUNNING run_card block; dormant for bundled EFT models.
---

# EFT operator running (RGE) machinery (v3.7.1)

UpdateNotes.txt:262-263 (3.4.0, 06/05/22): "Allow to have EFT operator to run for some special UFO
model (quite restricted class of running are supported -- corresponding to EFT running --)". This is
the source-side machinery behind that note. It is an EFT-NLO-adjacent capability: a UFO can declare
that some of its (Wilson-coefficient / parameter) couplings run with scale, and MG threads an extra
renormalization scale through the run.

## Model-side hook: `all_running_elements`
`$MADGRAPH_INSTALL/models/import_ufo.py:524-525`:
```
if hasattr(self.ufomodel, 'all_running_elements'):
    self.model.set('running_elements', self.ufomodel.all_running_elements)
```
The feature is ENTIRELY opt-in by the UFO. A model enables running only by shipping an
`all_running_elements` attribute (a `running.py` / `Running` object set in the UFO). If absent,
`running_elements` defaults to `[]` (base_objects.py:1098) and every downstream branch below is skipped.

**Dormant for the models involved here** — grep of `$MADGRAPH_INSTALL/models/*/*.py` finds NO
`all_running_elements` declaration (checked when SMEFTatNLO was on disk; SMEFTatNLO and sm have no `running.py`).
NB: `SMEFTatNLO`/`dim6top_LO_UFO` are NOT bundled in stock v3.7.1 (must be fetched — see
bundled-eft-models); the point stands that the fetched EFT models do NOT run their operators; the capability ships
in the framework but needs a running-enabled UFO (e.g. a SMEFT UFO that declares `all_running_elements`).

## Model methods (base_objects.py)
- `Model.get_running(used_parameters=None)` (def line 1488): returns a list of correlated parameter
  sets that must run **together**. It walks `self["running_elements"]`, and for each element's
  `run_objects` collects parameter names, **removing `aS`** (lines 1500-1502 — aS running is handled by
  the standard QCD machinery, separately). Sets sharing a parameter are merged (lines 1505-1508). If
  `used_parameters` is given, only sets touching a used parameter survive (lines 1512-1515).
- `Model.get_all_running_coupling()` (line 1519): `all_running_type = ['aS'] + self.get_running()`
  (line 1523) then returns every coupling whose order-tuple contains a running type.
- `Model.is_running_coupling(name)` (line 1530): cached membership test against the above.
- Restriction/merge path also rewrites running element values: base_objects.py:1729-1731
  (`for el in self['running_elements']: el.value = rep_pattern.sub(...)`) — running elements are
  substituted alongside masses/widths when parameters are renamed.

## run_card-side: the conditional `RUNNING` block
`$MADGRAPH_INSTALL/madgraph/various/banner.py`:
- LO block: `running_block = RunBlock('RUNNING', template_on=..., template_off="")` at line 4022.
- NLO block: `running_block_nlo = RunBlock('RUNNING', ...)` at line 5592.
- Template (lines 4012-4020) — header "CONTROL The extra running scale (not QCD)" / "Such running is
  NOT include in systematics computation", three parameters:
  - `fixed_extra_scale` — `! False means dynamical scale`
  - `mue_ref_fixed`     — `! scale to use if fixed scale mode`
  - `mue_over_ref`      — `! ratio to mur if dynamical scale`
- The block is appended to the run_card's `display_block` **only when the model has running elements**:
  - LO `RunCardLO`: banner.py:5100-5103 `if model['running_elements']: self.display_block.append('RUNNING')`.
  - NLO `RunCardNLO`: banner.py:6066-6069 same guard.
So `fixed_extra_scale`/`mue_ref_fixed`/`mue_over_ref` appear in the generated run_card ONLY for a
running-enabled UFO. For SMEFTatNLO/dim6top they are absent.

## Export-side consumption
`get_running` is consumed at `iolibs/export_v4.py:7916` (`running_block = self.model.get_running(self.used_running_key)`)
to write the running parameter blocks into the generated Fortran. (Fortran-emission internals are
nlo-mechanics territory; cited here only to bound where the EFT-running model data is used.)

## EFT-slice takeaways
- The "extra running scale" is a SECOND renormalization scale (mu_e, distinct from mu_R/QCD) at which
  the running Wilson coefficients are evaluated — fixed (`fixed_extra_scale=True`, value `mue_ref_fixed`)
  or dynamical (ratio `mue_over_ref` to mu_R). It is explicitly excluded from systematics reweighting.
- This whole path is gated on the UFO; do not promise EFT running for a model that lacks
  `all_running_elements`. Check the UFO for that attribute before claiming a process runs its operators.
- aS is always excluded from `get_running`'s correlated sets — its running is the ordinary QCD path,
  not the EFT-running path.

## Boundary
- Whether/how to use a running scale physically is ma-physics-consultant's call. R2/UV counterterm
  declarations and Fortran emission of the running blocks are nlo-model / nlo-mechanics slices.
- This page covers the EFT-running *enablement and run_card surface*; not yet probe-verified end to end
  (no running-enabled UFO installed). Treat the run_card-block-appearance prediction as source-derived
  but unprobed until a UFO with `all_running_elements` is loaded.
