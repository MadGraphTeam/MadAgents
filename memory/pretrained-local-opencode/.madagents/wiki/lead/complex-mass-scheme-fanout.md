---
description: An unstable particle sits in a propagator and its width treatment matters (gauge invariance, threshold, zero width).
---

# Complex-mass scheme (CMS) & width-in-propagator fan-out

**When it applies.** Any question about the complex-mass scheme, fixed-width vs
CMS propagators, gauge invariance of inserting Γ into a propagator, activating
CMS (`set complex_mass_scheme`), `small_width_treatment` / `bwcutoff`, zero-width
s-channel resonances, or the general "how does MadGraph treat widths in
propagators" documentation family.

## Owner map — dispatch by piece

- **CMS activation surface + model transformation** → `ma-model-loader-consultant`.
  `complex_mass_scheme` is a global MG5 **interface `set` option**
  (`madgraph_interface.py:3105`, default `False`; help `:853`), applied at every
  `import model` via `change_mass_to_complex_scheme` (`base_objects.py:1863`:
  masses→`CMASS_*` complex, Yukawas tied to mass, SM EW input scheme auto-swapped
  to (mz,mw,alpha)). It is *recorded* to the `proc_characteristics` file at
  output (`banner.py:1761`, in the **`ProcCharacteristic`** class) and read back
  at launch as `force_CMS`. `set complex_mass_scheme True` on a loaded model
  triggers a full self-re-import (`:8054`). `check cms` runs a CMS gauge test
  (`madgraph_interface.py:4636/4670`).
- **UFO declaration side** → `ma-ufo-consultant`. Default `sm` needs **no**
  dedicated CMS model, `-cms` restriction, or special particle attribute at LO —
  CMS runs on generic mass/width Params, gated only by runtime `aloha.complex_mass`.
  The `CMSParam` gate (governs the UVCT `real(...)` prefix in loop UFOs) is
  **absent from every shipped model**; `loop_sm` CT files carry nothing
  CMS-specific (physically-correct CMS-at-NLO needs the online `loop_qcd_qed_sm`,
  not on a default install → probe-candidate).
- **Propagator/width at phase-space integration** → `ma-phase-space-consultant`
  (the sampling BW map is a **fixed real-width** change of variables,
  `transpole.f:52-54`; CMS leaves channels/`set_peaks`/`gForceBW` **byte-identical**)
  **+ `ma-bw-window-consultant`** (`small_width_treatment` floor, `bwcutoff`
  on-shell window, zero-vs-tiny distinction).
- **Gauge / NWA / off-shell / near-threshold physics** → `ma-physics-consultant`.
- **Width–mass consistency / `compute_widths`** → `ma-madwidth-consultant`.
- **Near-threshold "comma syntax forces on-shell → ~0 σ"** → `ma-chain-decay-consultant`
  (+ bw-window for the sampling window). Overlaps `offshell-bwcutoff-derivation`,
  `process-line-scope-traps`.

## Doc-myth traps (the corrections)

1. **`complex_mass_scheme` is NOT a run_card parameter.** It appears nowhere in
   the LO or NLO run_card templates — the only registration is
   `banner.py:1761` inside `ProcCharacteristic`. Activation is the `set` option,
   recorded to `proc_characteristics`. (model-loader)
2. **CMS is NOT auto-enabled for NLO.** Opt-in for both LO and NLO; no code forces
   it on for loop/NLO generation. It is applied at import even at LO (rewrites LO
   masses to complex). (model-loader)
3. **CMS is a matrix-element-denominator-only effect** (the `CMASS_*` params,
   `export_v4.py:7317-7411`). Phase-space sampling and channel construction are
   identical with CMS on or off — any claim that CMS reshapes phase-space sampling
   is wrong. (phase-space)
4. **`small_width_treatment` floor + NWA σ-reweight lives in phase-space sampling**
   (`transpole.f:44-47`, `jac*=width/width1`) and the on-shell window
   (`myamp.f:132/330/398`), **NOT in the amplitude propagator denominator** — the
   ME width comes from `coupl.inc` (fixed Γ) untouched. "Replaced for the ME
   evaluation" mislocates it. Default `1e-6`, hidden (`banner.py:4452`). (bw-window)
5. **Tiny-nonzero vs exactly-zero width differ.** `small_width_treatment` rescues
   only *tiny-nonzero* widths. An **exactly-zero** on-shell-capable s-channel hits
   the `swidth>0` guard (`dsample.f:1393`), skips `transpole`, falls to a plain
   power-law `setgrid` grid (`myamp.f:450-456`) — an unregulated `1/(s−M²)` pole,
   fluctuating σ, **silent, no warning**. Always set a physical width for
   s-channel resonances. (bw-window + phase-space)
6. **Small Γ/M ≠ NWA-always-valid.** The Γ/M table is right (top ~0.8% excellent;
   W ~2.6% / Z ~2.7% good-inclusive; H ~0.003%), but the blanket Higgs "excellent"
   is misleading — off-shell `gg→H*→VV` is ~10% of on-shell and is the
   width-bound observable. NWA quality is set by the *observable* + off-shell
   tail, not by Γ/M alone. (physics)
7. **No automatic width recompute on a mass edit.** Widths are regenerated only by
   explicit `compute_widths` or the literal `auto`/`auto@NLO` DECAY sentinel
   (`common_run_interface.py:3743`); a numeric width is used verbatim, no
   consistency warning — the derived-quantity-staleness principle. BR>1 in MadSpin
   is the downstream symptom (guard is MadSpin-internal). (madwidth)

## Return-interpretation hint

The activation surface is what the documentation family gets most wrong. If a
return frames `complex_mass_scheme` as a run_card line, or CMS as
"automatically on for NLO," it is stale — the source truth is a `set` option
recorded in `proc_characteristics`, opt-in for both orders.

## Cross-refs

`offshell-bwcutoff-derivation`, `derived-quantity-staleness`,
`decay-widths-lifecycle`, `runcard-lo-nlo-value-divergence`,
`process-line-scope-traps`.
