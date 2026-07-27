---
description: You need alternative weights on the same events. A scale/PDF uncertainty band, or a re-evaluation at other params.
---

# Systematics & reweighting — fan-out and owner map

Built against MG5_aMC v3.7.1.

"Systematics / reweighting" is **two independent machineries** that only share the LHE weight container:

1. **The `use_syst` systematics module** — on-the-fly scale/PDF/αs *variation* weights, computed automatically post-integration from the stored event kinematics. Never regenerates events.
2. **The standalone reweight module** (`ReweightInterface`) — recomputes the matrix element at each stored phase-space point for arbitrary param/coupling/mass/width/process changes. Activated by `reweight=ON` or `madevent reweight`.

Both write into each event's `<rwgt>` block and the header `<initrwgt>` group; that shared container is the *only* coupling between them. Route the two separately.

## Owner map (route each sub-question here)

**Systematics module (`use_syst`):**
- **`use_syst` / `systematics_program` / `systematics_arguments` run_card params, the `Systematics` class, ALL flag PARSING (`--mur --muf --pdf --alps --dyn --together --start_event --stop_event`), LHE `<rwgt>`/`<initrwgt>` weight allocation, the lhapdf gate, the retired-SysCalc `sys_*` legacy params** → **ma-systematics-consultant** (the anchor for both machineries).
- **What the `--dyn` integers MEAN** (the consumed `dynamical_scale_choice` values) → **ma-scales-pdf-consultant**. The systematics module owns `--dyn` *parsing*; scales-pdf owns what each integer selects. (LO allowed `[-1,0,1,2,3,4,10]` vs NLO `[-2,-1,0,1,2,3,10]` — `runcard-lo-nlo-value-divergence.md`.)
- **`--alps` / α_s-emission-scale variation — MLM relevance** → **ma-matching-consultant**. `--alps` reweights the `<asrwt>` clustering-node scales, which exist ONLY in matched (`ickkw>0`) output; on a fixed-order run it is a silent no-op.
- **PDF error-set Hessian-vs-MC-replica combination** → framed by **ma-systematics-consultant** (the combination is delegated to LHAPDF's `pdfset.uncertainty()`, invoked from `systematics.py`; NOT the scales-pdf slice — scales-pdf owns only the central-PDF identity `pdlabel`/`lhaid`).
- **LHAPDF library install** → **ma-installation-consultant** (`install lhapdf6`/`lhapdf5`, case-sensitive; operative config key is bare `lhapdf`).

**Standalone reweight module:**
- **Activation (`reweight=ON`, `madevent reweight -f`), `reweight_card.dat` grammar, `change model/process/helicity/output`, mass-reweight `change output 2.0` gate, NLO `store_rwgt_info`+OLP=MadLoop** → **ma-systematics-consultant** (`reweight_interface.py`).
- **The `set BLOCK ID VALUE` value lines inside a reweight_card** → **ma-param-card-consultant**. They reuse the param_card SLHA machinery (`AskforEditCard.do_set` + `ParamCard` + `ParamCardIterator`), not a separate reweight parser.
- **`change model MODELNAME`** (switching UFO models mid-reweight) → primarily systematics (`do_change`), with model-loader for the model-import mechanics if a fetch/convert is implicated.

## Dispatch order

systematics first (anchors both machineries; its return tells you which secondary slices the spec actually implicates), then fan the secondaries the spec names in parallel: scales-pdf for `--dyn` meaning, matching for `--alps`/matched-sample uncertainty, param-card for reweight `set` values, installation for LHAPDF. A bare "turn on scale/PDF systematics with defaults" collapses to systematics alone (defaults compute the 3×3 grid + PDF errorset automatically).

## Doc-myth traps (common write-ups get these wrong; verify against source)

- **"systematics requires lhapdf6" is a SOFT SKIP, not a hard requirement.** With no LHAPDF (or lhapdf5), the systematics path logs an info line and `return`s — empty systematics, no crash, no internal-PDF substitute. So PDF-error-set reweighting *effectively* needs LHAPDF, but a user on lhapdf5 or no-lhapdf gets silent empty weights, not an error. (`systematics.py:~225-227`; `common_run_interface.py:~1789-1800`; corroborated independently by the systematics and installation slices.)
- **Mass reweighting `change output 2.0` fires ONLY for MASS-block changes.** The CRITICAL "mass reweighting requires dedicated lhe output!" raises only when an *external MASS* entry changes (`jac != 1`, LO-only path); couplings, Yukawas, and widths reweight fine under default output. NLO `change_kinematics` never reshuffles, so the gate is LO-specific. (`reweight_interface.py:~1105-1126`.)
- **The reweight_card `set` prefix is OPTIONAL, not forbidden.** The commonly-quoted "not `set param_card` syntax" is loose — `set param_card yukawa 6 X` and bare `set yukawa 6 X` both work (same `card in ['','param_card']` guard). `set width N …` is rewritten to address the **DECAY** block. The addressing is the param_card's either way.
- **Matching uncertainty "vary xqcut/qCut" is MLM(LO)-only.** The recipe (vary `xqcut` by 0.5/2) applies to `ickkw=1` MLM; at NLO/FxFx (`ickkw∈{-1,0,3,4}`) there is no `xqcut` — the merging scale is `shower_card` Qcut. A summary table attributing matching uncertainty to "xqcut/qCut" without scoping it to MLM is incomplete for FxFx. Matching-scale variation CANNOT be done on-the-fly — it needs separate generations (the ME phase space below `xqcut` was never generated).
- **`scalefact` (integration-time scale multiplier, LO-only) ≠ `sys_scalefact` (on-the-fly reweight multiplier).** The advice to "vary `scalefact` in separate runs for interference-dominated σ" is interference-safe precisely because it *re-integrates* rather than reweights. NLO uses `mur_over_ref`/`muf_over_ref` (no `scalefact`). The old `use_syst→scalefact=1` reset is commented out in 3.7.1.
- **Legacy `sys_scalefact`/`sys_pdf`/`sys_alpsfact` still EXIST in the LO run_card** (hidden), feeding the retired SysCalc (`systematics_program='syscalc'`, "code not supported anymore"). `sys_pdf` default is `"errorset"`, not empty. The modern `systematics_arguments` supersedes them.
- **The 7-point scale envelope is a POST-HOC analysis choice, not a generation filter.** Defaults compute the full 3×3=9 mur×muf grid; the 7-point envelope (drop the two anti-correlated combos) is taken downstream. (Shared with `pdf-and-scale-configuration-fanout.md`.)
- **NLO reweighting silently degrades to LO accuracy** without `store_rwgt_info=True` (writes `<mgrwgt>` blocks) or without OLP=MadLoop — a warning, not an error. Interactive `reweight=ON` auto-sets `store_rwgt_info`.

## Runtime confirmations still open (probe-candidates, not source-settled)

Left as named probe-candidates in the consultant subtrees (none block a source-grounded answer): the emitted `<initrwgt>` weightgroup structure + per-event `<rwgt>` id allocation from a real `systematics` run; NLO reweight with `store_rwgt_info`+OLP=MadLoop `<mgrwgt>` emission; `change output 2.0` mass-reweight reshuffled-LHE write; `--dyn 0`/`--dyn 10` KeyError at the label emit (`systematics.py:679` label maps cover only `{1,2,3,4}`); the LHAPDF silent-skip path on an unconfigured environment.
