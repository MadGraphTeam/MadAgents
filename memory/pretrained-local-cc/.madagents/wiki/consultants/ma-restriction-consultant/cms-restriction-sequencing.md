---
description: How complex_mass_scheme is sequenced around restriction in import_model — CMS applied BEFORE restrict_model, restrict card read twice, flag re-threaded (import_ufo.py:259-322, v3.7.1)
---

# CMS-restriction sequencing seam

This page records how `complex_mass_scheme` (CMS) is threaded through `import_model`
*around* the restriction call. The CMS TRANSFORM itself (`change_mass_to_complex_scheme`)
lives in `$MADGRAPH_INSTALL/madgraph/core/base_objects.py:1863` and is loader/base-object
territory — NOT mine. What is in-slice: CMS must run before restriction, and the restrict
card is read an EXTRA time to seed mass/width classification before restriction proper.

## useCMS decision (import_ufo.py:259-261)
```
useCMS = (complex_mass_scheme is None and aloha.complex_mass) or \
                                                  complex_mass_scheme==True
```
So CMS is on if the explicit flag is True, OR if the flag is unset (`None`) and the global
`aloha.complex_mass` is set. (The flag origin / `aloha.complex_mass` setting is model-loader's
slice; this page records only how the resulting `useCMS` gates the code around restriction.)

## Ordering in the restrict_file branch (263-310)
With a restrict file, the sequence is, IN ORDER:
1. `model = RestrictModel(model)` (273) — re-class the model so restriction methods exist.
2. **CMS applied BEFORE restriction** (275-295). The source comment is explicit (275-276):
   "Change to complex mass scheme if necessary. This must be done BEFORE the restriction."
   - If `useCMS`: FIRST read the restrict card a time with CMS OFF (283-284):
     `model.set_parameters_and_couplings(param_card=restrict_file, complex_mass_scheme=False)`.
     The comment (278-282) says this is so `change_mass_to_complex_scheme` "can know if a
     particle is to be considered massive or not and with zero width or not" — i.e. the
     restrict-card numeric values classify each particle's massive/massless + zero/nonzero-width
     state BEFORE the CMS transform decides which masses become complex. Then
     `change_mass_to_complex_scheme(toCMS=True, bypass_check=allow_qed)` (290).
   - Else (not useCMS): `change_mass_to_complex_scheme(toCMS=False)` (295) — comment (292-294)
     notes this forces the model's `CMSParam` to 0.0 for the correct NWA renormalization
     condition, in case the model's own default is CMS.
3. keep_external auto-detection (297-307) — see restrict-flag-determination.md.
4. `model.restrict_model(restrict_file, rm_parameter=not decay, keep_external=keep_external,`
   `complex_mass_scheme=complex_mass_scheme)` (309-310). The SAME `complex_mass_scheme` flag is
   passed INTO restriction, where `set_parameters_and_couplings` (2407-2409) and the
   companion-`param_*.dat` reload (2495) both receive it again.

## The double (potentially triple) restrict-card read
The restrict card's parameter values are read via `set_parameters_and_couplings` MULTIPLE times
for a CMS load:
- once at 283-284 with `complex_mass_scheme=False` (seed for mass/width classification),
- once inside `restrict_model` at 2407-2409 with the real `complex_mass_scheme` (the values
  restriction's zero/identical detection actually uses),
- and once more at 2495 IF a sibling `param_<name>.dat` exists (companion-card reload, see
  restrict-model-pipeline.md step 16).
The 283-284 read does NOT drive pruning — it only informs the CMS transform. Pruning/merging
operates on the values from the 2407-2409 read.

### Why the pre-read can't drive pruning (mechanism, verified v3.7.1)
`set_parameters_and_couplings` REBUILDS `parameter_dict` and `coupling_dict` from scratch on
every call: `$MADGRAPH_INSTALL/models/model_reader.py:262-270` does
`self.set('parameter_dict', dict([...]))` and `self.set('coupling_dict', dict([...]))`,
wholesale-replacing the dicts. So the 2407-2409 call OVERWRITES whatever the 283-284 pre-read
populated. The two pruning-detection methods read exactly those rebuilt dicts:
`detect_identical_couplings` reads `self['coupling_dict']` (2534), `detect_special_parameters`
reads `self['parameter_dict']` (2620). Hence pruning provably uses the 2407-2409 values, never
the pre-read's. (This is the same "latest call wins / rebuilt not patched" shape as the lead's
config-value-lifecycle pattern — flagged cross-subtree, not restated here.)

What the pre-read DOES feed: `change_mass_to_complex_scheme`
(`$MADGRAPH_INSTALL/madgraph/core/base_objects.py:1863`) reads `width.value`/`mass.value`
(1907, 1914) to classify each particle massive/massless + zero/nonzero-width. Those `.value`
attrs are set by the pre-read (`param.value = float(value)` at model_reader.py:205, and
`param.value = complex(...)` for derived params at 236). So the pre-read's sole consumer is the
CMS transform's classification — exactly the role the source comment (278-282) states.

## No-restrict-file branch (312-322)
When `restrict_file is None` (e.g. `model sm-full`, see restrict-card-resolution.md), there is
NO restriction and NO 283-284 pre-read; CMS is applied directly (`change_mass_to_complex_scheme`
toCMS True/False at 319/322 with `bypass_check=allow_qed`). So the "read restrict card with CMS
off first" step is specific to the restricted path.

## Caution
The 283-284 pre-read uses `complex_mass_scheme=False` HARDCODED regardless of the requested
scheme — it is intentionally the not-yet-transformed view. A reader who assumes "restriction
sees the CMS values" must distinguish: the CMS transform (toCMS=True) mutates the model's
mass/width structure between the pre-read and `restrict_model`, so restriction at 2407-2409
operates on the post-CMS-transform model but with the real `complex_mass_scheme` value. The
ordering (CMS transform strictly before restriction) is load-bearing — reversing it would make
the transform unable to classify massive/massless particles from the restrict-card values.
