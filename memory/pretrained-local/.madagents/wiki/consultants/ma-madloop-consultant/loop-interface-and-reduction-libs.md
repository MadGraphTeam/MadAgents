---
description: LoopInterface REPL (do_output/launch/check/add), reduction-library installer + AskLoopInstaller defaults, proc validity/gauge rules (loop_interface.py, MG5_aMC v3.7.1)
---

# LoopInterface + reduction libraries

`$MADGRAPH_INSTALL/madgraph/interface/loop_interface.py`.

## REPL commands (`LoopInterface`, :369)
- `do_output` (:430): only `standalone`/`standalone_rw`/`matchbox` (`supported_ML_format` :371); a non-matching `_export_format` raises InvalidCmd (:452-454). (`matrix` is NOT a supported ML output format — it appears only in a dir-existence guard at :456, not in `supported_ML_format`.) Always outputs quad-precision routines (`aloha.mp_precision=True`, :449-450) for unstable-point recovery — this QP emission is the ENABLER for the init-time and runtime DP→QP fallbacks documented in ./madloop-init-and-stability.md (you can't recover an unstable point in QP if the QP routines were never compiled). Calls `ML5export` (:609 → builds `LoopHelasProcess`) then `ML5finalize` (:717).
- `do_launch` (:756): ML5 can ONLY launch `standalone` runs (:766-767); uses `launch_ext.MadLoopLauncher`.
- `do_check` (:778): parses `[...]` perturbation orders; `QED` present ⇒ `validate_model(coupling_type='QED')`; `stability`/`profile` take a statistics count as 2nd arg (:800-802).
- `do_add` (:815): extracts `--loop_filter=`; picks `LoopMultiProcess` if `perturbation_couplings!=[]` else plain `MultiProcess` (:898-901).

## proc_validity (CommonLoopInterface :211-291) — what ML5 rejects
- decay chains (:245), perturbed decays (:249), multiparticle labels in standalone ML5 (:239-243).
- empty `perturbation_couplings` in ML5 ⇒ "do tree-level in default MG5" (:254-256).
- perturbation order not in model's allowed orders (:263-268).
- `:270-275` perturbation couplings not in `[[],['QCD']]` ⇒ requires Feynman gauge.
- difficulty score ≥100 ⇒ "challenging difficulty" warning (`rate_proc_difficulty` :153, color-charge based: singlet 2, triplet 3, sextet 4, octet 6; -6 for virt-only / real-only).

## validate_model / gauge (:297-367)
- Auto-upgrades `sm`→`loop_sm` (QCD) or `loop_qcd_qed_sm` (QED / QCD+QED) (:329-352).
- QED corrections force Feynman gauge (`loop_qcd_qed_sm` is Feynman-only) (:333-337, :358-364).

## Reduction libraries
`install_reduction_library` (:511-604): triggered on first loop output if ninja lib absent (:517). Prompts `AskLoopInstaller`.
- `AskLoopInstaller` (:930): `required=['cuttools','iregi']`; `order=['cuttools','iregi','ninja','collier','golem']`; `bypassed=['pjfry']`.
- Default codes (:952-956): ninja=`install`, collier=`install`, golem=`off`, cuttools/iregi=`required`. ninja & collier marked `(recommended)` in the question (:1020). If no `cmake` ⇒ collier forced `off` (:961-962).
- Offline ⇒ ninja/collier switch to `local` (offline tarball installer), golem `fail` (:957-960).

### Vendor inventory (verified v3.7.1)
- `$MADGRAPH_INSTALL/vendor/CutTools/` (OPP) — BUILT: `includects/libcts.a` present.
- `$MADGRAPH_INSTALL/vendor/IREGI/` (TIR) — BUILT: `src/libiregi.a` present.
- `$MADGRAPH_INSTALL/vendor/ninja.tar.gz` (OPP, recommended), `collier.tar.gz` (TIR, recommended), `oneloop.tar.gz` (aux for Ninja). NOT pre-extracted.
- CutTools+IREGI are the self-contained bundled fallback; Ninja/Collier require the install step.
- GoSam: external OLP via `Template/loop_material/OLP_specifics/GoSam/`, `OLP='gosam'`.
