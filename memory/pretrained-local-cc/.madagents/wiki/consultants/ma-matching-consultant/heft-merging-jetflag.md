---
description: HEFT/hgg-vertex models and LO merging — model 'limitations' force ickkw=0, and the jet-flagging change so effective-vertex jets are excluded from matching.
---

# HEFT / effective-vertex merging jet-flag handling

## proc_characteristic limitation gate (RunCardLO.create_default_for_process, `$MADGRAPH_INSTALL/madgraph/various/banner.py`)
- @5048-5053: if `'MLM' in proc_characteristic['limitations']`: if `dynamical_scale_choice==-1` set it to `3`; if `ickkw==1` logger.critical "MLM matching/merging not compatible with the model! You need to use another method to remove the double counting!"; then forces `ickkw=0`.
- @5061-5066: if `'fix_scale' in proc_characteristic['limitations']`: forces `fixed_ren_scale=1`, `fixed_fac_scale=1`, and the same `ickkw=0` force (+critical log if it was 1).

So a model flagged with the 'MLM' limitation cannot run LO MLM matching: MadGraph silently disables ickkw (critical log only at auto-detect time).

## UpdateNotes provenance
`$MADGRAPH_INSTALL/UpdateNotes.txt:954-955`: "OM: Change in LO maching for HEFT (or any model with hgg vertex) in the way to flag jet that should not take part in the matching/merging procedure." Line 1402: "Fixed a crash in some HEFT merging case." Line 1468: `add model hgg_plugin` adds the effective operator.

## Physics
Models with an effective `hgg` (Higgs-gluon) vertex produce gluons from the effective vertex that must NOT be clustered as QCD radiation in the MLM kt-clustering — otherwise double-counting/mis-flagging. The fix changes which final-state jets get flagged as matchable so effective-vertex legs are excluded.

## Where the 'MLM' limitation is set (output-time, per-matrix-element)
Settled from source (`$MADGRAPH_INSTALL/`):
- `madgraph/core/base_objects.py:1100`: `self['limitations'] = []` — a **model**
  field, default empty; comment "MLM means that the model can sometimes have issue
  with MLM/default scale." So the model declares whether it is MLM-suspect.
- `madgraph/iolibs/export_v4.py:4779-4792`: at output time, `'MLM'` is appended to
  `proc_characteristic["limitations"]` ONLY if BOTH:
  (a) `'MLM' in self.model["limitations"]` (the model flag above), AND
  (b) the matrix element actually USES a gluon-attached non-QCD vertex — loops
  `model.get('interactions')`, finds a vertex with a gluon (pdg 21), skips it if a
  color-singlet leg is present (`1 in colors → continue`), and if the vertex has
  NO `'QCD'` order AND one of its couplings is in `matrix_element.get_used_couplings()`,
  flags `'MLM'`.
- **Refinement of "model-flagged":** the limitation is NOT blanket per-model. A
  model can carry `'MLM'` in its limitations yet a specific process that does NOT
  use the effective (non-QCD) gluon coupling will NOT get the flag — gate (b) is
  per-matrix-element on the couplings actually used. So whether ickkw is force-zeroed
  is process-dependent even within an MLM-flagged model.

## Cautions
- The 'MLM' limitation is determined by `proc_characteristic['limitations']` (set at output time per the block above). Whether a given HEFT process carries it is process/model-specific (depends on which couplings the ME uses) — VERIFY per input by inspecting the generated `proc_characteristics` file, not from this page.
- ickkw is force-zeroed only at auto-detect (create_default_for_process). A user who later hand-edits ickkw=1 into the run_card for such a model would not re-trigger this gate; check_validity does NOT re-test the 'MLM' limitation.
- Probe-candidate (still open, runtime only): the SOURCE gate is now settled above (model flag + per-ME non-QCD gluon coupling). What remains launch-only: does a specific HEFT ggF + jets process trip gate (b) in practice, and the verbatim runtime critical-log text. Not verified by launch in this study.
