---
description: Systematic base-vs-optimized FKS exporter divergence — which methods the optimized default re-defines vs inherits, the direction of every divergence (optimized adds TIR/COLLIER, relaxes base raises), and the verification move before asserting any per-method behavior on the default NLO path.
---

# Base vs optimized FKS exporter divergence (v3.7.1)

## The principle
The default NLO exporter is `ProcessOptimizedExporterFortranFKS` (`export_fks.py:4693`), NOT the base `ProcessExporterFortranFKS` (`:91`). The optimized class **re-defines** several methods rather than extending them, so base behavior does not transfer to the default path. Before asserting what a method does for a real `output` run, locate the override first.

Two systematic directions, confirmed across every overridden method:
- **Optimized ADDS reduction-library awareness** — TIR linking, COLLIER-aware banner, TIR interface/coef specs. The base (unoptimized loop) path has none of it.
- **Optimized RELAXES base safety-raises** — where the base raises on a missing prerequisite, the optimized just proceeds.

## Override map (which methods diverge)
- `copy_fkstemplate` — base `:98`, optimized override `:4707`. DIVERGES.
- `generate_virt_directory` — base `:2429`, optimized override `:4908`. DIVERGES (optimized links DHELAS `coef_specs.inc` + TIR interface; base is TIR-free).
- `finalize` — optimized `:4700` exists but just delegates: `ProcessExporterFortranFKS.finalize(self,...)`. SAME behavior.
- `generate_directories_fks` — base `:472` only (optimized inherits; EW-Sudakov re-overrides at `:5104`). SAME on the optimized path.
- `write_orders_file` (`:1239`), `get_orderstag` (`:66`), the orders/amp_split writers — base-only, inherited unchanged.

So the divergence is confined to `copy_fkstemplate` and `generate_virt_directory`; everything else on the default path runs the base code. The inverse trap is real too: do NOT assume the optimized class overrides something it actually inherits (`finalize` delegates back; `write_orders_file`/`generate_directories_fks` are base code on the default path).

## Confirmed divergence facets (copy_fkstemplate)
Each is a concrete instance of "optimized adds TIR/COLLIER or relaxes a base raise":
- **collier_available** context for MadLoopCommons.f: base hardcodes `False` (`:218`); optimized uses `self.tir_available_dict['collier']` (`:4878`). Only the optimized path can emit a COLLIER-aware banner.
- **TIR linking**: optimized loops `self.all_tir` → `link_TIR` (`loop_exporters.py:1910`); ninja needs `libavh_olo` or raises (`:4785`). Base links only CutTools.
- **mp_coupl.inc / mp_coupl_same_name.inc**: optimized-only link from Source/MODEL → SubProcesses (`:4883`); absent in `[real=]` mode (files not present).
- **Running dir** (`model["running_elements"]`): base RAISES if `Template/Running` absent (`:247`); optimized just `shutil.copytree` (`:4901`).
- **FKS_params NHelForMCoverHels=-1** regex edit (`:227`-232): present in BASE only; optimized override does NOT repeat it. (Direction exception — this is base-side setup the optimized drops; verify on the default path before asserting, probe-candidate.)

## The verification move
Question of the form "does the NLO output do X?" on a default run → (1) is X owned by `copy_fkstemplate` or `generate_virt_directory`? If yes, read the optimized override (`:4707` / `:4908`), not the base. (2) Otherwise it is base code inherited unchanged — read the base def. EW-Sudakov (`ProcessExporterEWSudakovSA`, `:5056`) adds a third layer that re-overrides `generate_directories_fks` and `finalize`.

## Instances generalized
- copy-fkstemplate-and-scaffolding.md — the per-facet collier/FKS_params/Running/mp_coupl details (kept).
- exporter-class-hierarchy.md — the MRO note and per-class override list (kept).
