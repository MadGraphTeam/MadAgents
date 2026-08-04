---
description: Bundled vs online vs FeynRules-only EFT models in MG5_aMC v3.7.1; NO EFT UFO ships under models/ on a stock install (dim6top/SMEFTatNLO must be fetched), the _online_model dict, each model's power-counting variable, and the taudecay_UFO EFT-order false positive.
---

# Bundled / online / FeynRules-only EFT models (v3.7.1)

## Bundled under `$MADGRAPH_INSTALL/models/` — STOCK ships no EFT UFO; distributed EFT models are session-specific
Stock v3.7.1 ships NO EFT UFO — always `ls models/` before answering "which EFT model do I use".

**The distributed EFT models (SMEFTatNLO, SMEFTsim_*, dim6top_*) are MANUALLY-PLACED, not bundled — they
come and go from `models/` across sessions. `ls models/` EVERY session; never assume a prior session's roster.**
Both states occur across installs: present on some (source-walked from them when present), absent on
others (`ls models/` → only stock, e.g. `sm, loop_sm, MSSM_SLHA2, taudecay_UFO, hgg_plugin`; no `*smeft*`/`*dim6*`).
A "not on disk" return is correct, not a failure. The model-specific facts on smeftsim-anchored-taxonomy-and-gaps.md
and the smeftatnlo-* pages were source-verified WHEN the model was present; they hold for that model version
whenever it IS on disk — re-resolve each cited `models/<MODEL>/...:line` against the actually-installed copy first.
(A separate `tests/input_files/SMEFTatNLO_running/` test tree may exist independently — the RUNNING-enabled
variant, NOT importable as a `models/` model and distinct from the distributed `models/SMEFTatNLO/`; may be present independently of the `models/` tree.)

## How to obtain `dim6top_LO_UFO` / `SMEFTatNLO`
- **Neither is a hardcoded `_online_model` key** (dict below has no `dim6top*`/`SMEFTatNLO`).
- `import model dim6top_LO_UFO` / `import model SMEFTatNLO` falls through to the **runtime model-DB
  fetch** (`models/import_ufo.py:import_model_from_db()`, ~line 135) when the name isn't local —
  downloads the tarball from `madgraph.phys.ucl.ac.be` / `madgraph.mi.infn.it` into `models/`.
  (Fetch mechanics are out-of-slice = installation / model-loader; entry points only, see bottom.)
- Or **manual FeynRules download** + unpack under `models/` (author-site variants).
Either path lands the UFO on disk; only then are the per-insertion / restrict-card facts below re-verifiable.

**Trap — `taudecay_UFO` carries an `EFT` order but is NOT a dim-6 SMEFT model.** On a stock install a
live grep for EFT-flavoured order names (`coupling_orders.py` `name=`) finds only `taudecay_UFO`
(**EFT**) among bundled models (`template_files/` skeleton also declares `EFT`); `dim6top_LO_UFO`
(DIM6+FCNC) and `SMEFTatNLO` (NP) appear only after they are fetched. The `taudecay_UFO` `EFT` order
(expansion_order=99, hierarchy=1) labels effective **tau-decay form-factor** vertices — its 8 EFT
couplings are `F0/F1/F2 * Gf * ...` (a Fermi-theory effective-Lagrangian description of τ decay),
with **no `Lambda` cutoff and no Wilson-coefficient blocks** (lhablocks: CKMBLOCK, taudecay, MASS,
SMINPUTS, DECAY). It is a false positive for "dim-6 operator EFT" — do NOT route a SMEFT/dim-6
question to it. The two dim-6 EFT models are dim6top_LO_UFO and SMEFTatNLO only — **neither on disk
until fetched** (see above). (template_files/ also declares an `EFT` order — it is the UFO skeleton, not a usable model.)

## Online (downloadable via `import model <name>`)
`_online_model` dict at `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:2894-2909`. EFT-flavoured keys:
- `EWdim6:['full']` — EW dim-6 operators (import `EWdim6-full` for full operator set; UpdateNotes:1689).
- `heft:['ckm','full','no_b_mass','no_masses','no_tau_mass','zeromass_ckm']` — Higgs Effective Theory.
- `TopEffTh:['']` — top-quark EFT.
NLO-SM baselines also online: `loop_qcd_qed_sm`, `loop_qcd_qed_sm_Gmu`.
`_online_model2 = []` (madgraph_interface.py:2910) is filled at runtime from the DB on `display modellist`.

## FeynRules-only (manual download + place under models/)
`SMEFTsim_*` (Warsaw basis), `SMEFTatNLO_*` variants beyond the bundled one, `dim6top_*` variants,
HISZ/SILH-basis variants. Not in `_online_model`; user must fetch from FeynRules / authors and unpack into `models/`.

## Online-fetch mechanics (out-of-slice = installation; entry points only)
`models/import_ufo.py:get_model_db()` (line 104) downloads `models_db.dat` from
`madgraph.phys.ucl.ac.be` / `madgraph.mi.infn.it` (or `$MG5aMC_WWW`).
`import_model_from_db()` (line 135) matches `model_name` to a tarball link, downloads to `models/` (line 174).

## Per-insertion increment is model-specific — READ coupling_orders.py + couplings.py
**These facts were source-walked from each model's `coupling_orders.py`/`couplings.py` when present; the
model can be absent on a given install (`ls models/` first). Re-verify per install — re-walk the SPECIFIC
fetched model version before relying on them, and treat as install-blocked whenever the model is not on disk.**
- `dim6top_LO_UFO/couplings.py`: every DIM6-carrying coupling uses `'DIM6':1` (increment +1).
- `SMEFTatNLO/couplings.py`: every NP-carrying coupling uses `'NP':2` (increment +2; written
  `'NP':2` no space — grep `"'NP': ?[0-9]+"` to confirm only `:2` appears). Zero `Lambda**4`, zero `'NP':4`.
  `SMEFTatNLO/coupling_orders.py`: `NP = CouplingOrder(expansion_order=2, hierarchy=1)`; QCD has `perturbative_expansion=1` (NLO).
- `dim6top_LO_UFO/coupling_orders.py`: declares `QCD, QED, DIM6, FCNC` (all `expansion_order=99`).
Never assume the increment — different EFT UFOs differ (DIM6=+1 here, NP=+2 here).
