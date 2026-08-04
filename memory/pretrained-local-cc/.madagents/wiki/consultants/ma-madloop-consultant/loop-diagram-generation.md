---
description: LoopAmplitude.generate_diagrams orchestration — born/loop generation, L-cut method, order guessing, tagging/filtering pipeline (loop_diagram_generation.py, MG5_aMC v3.7.1)
---

# Loop diagram generation (`LoopAmplitude`)

`$MADGRAPH_INSTALL/madgraph/loop/loop_diagram_generation.py`. `LoopAmplitude(diagram_generation.Amplitude)` at :48. Diagrams split into four containers, NOT the inherited `diagrams`:
- `:61-63` `born_diagrams`, `loop_diagrams`, `loop_UVCT_diagrams` (the last defaults to a DiagramList, the first two to `None`).
- `:69` `has_born` (bool) — decides whether virtual is squared against born or itself.
- `:71` `structure_repository` = `FDStructureList()` — the FD-structures (tree pieces hanging off the loop) shared across diagrams.
- `set('diagrams', …)` (:140) demultiplexes an incoming list into the four containers by class/`type`; `get('diagrams')` (:157) re-concatenates born+loop+UVCT and triggers generation lazily.

## generate_diagrams pipeline (:595-926) — order of operations
1. `:635-642` generate born (`generate_born_diagrams`, :1089, delegates to `Amplitude.generate_diagrams`) unless `has_born` is False.
2. `:658-660` re-set `has_born = born_diagrams!=[]` (born requested but empty ⇒ square loop against itself).
3. `:681-690` if user gave NO orders/squared_orders and there is a born, `choose_order_config` (:176) picks the minimum-weight non-perturbed-order configuration and filters born to it.
4. `:702` `check_factorization` warns if born don't all factorize the same perturbed-order power (real/virt consistency hazard).
5. `:705-729` upper-bound the loop orders: `guess_loop_orders_from_squared` (:197) then `guess_loop_orders` (:218). User-set perturbed orders get +2; WEIGHTED gets +2*min(pert hierarchy). See ./loop-order-guessing.md.
6. `:753` `generate_loop_diagrams` (:1097) — L-cut method, see below.
7. `:764-765` `set_Born_CT` (UVtree + wavefunction renorm) — only if has_born. See ./counterterm-structure.md.
8. `:820-835` `check_squared_orders`: regular (≥0) constraints iterated to fixpoint, then negative (`order^2=-n`) constraints once.
9. `:842-854` TAG every loop diagram (`diag.tag`), drop wavefunction corrections (`is_wf_correction`), vanishing tadpoles (`is_vanishing_tadpole`), and canonical-tag duplicates.
10. `:858` `filter_loop_for_perturbative_orders` — keep only loops whose loop-line particles + at least one loop coupling order are in the perturbed set; also drops loops with exactly one colored leg attached.
11. `:872` `remove_Furry_loops`. See ./furry-and-loop-filters.md.
12. `:878` `user_filter` (off by default).
13. `:881` `set_LoopCT_vertices` (R2/UVmass/UVloop per loop). See ./counterterm-structure.md.
14. `:913` `identify_loop_diagrams` — merge numerically-equivalent loops by `loop_tag`, keeping a representative with a `multiplier` and merged CT_vertices (:928-979).
15. `:917` final logger.info: "Contributing diagrams generated: %d Born, %d(+%d) loops, %d R2, %d UV".

## L-cut loop generation (`generate_loop_diagrams`, :1097-1204)
- Loop diagrams are built by cutting the loop open into two "L-cut" external legs (`loop_line:True`), then running the ordinary tree generator. `:1112-1116` perturbation orders processed QCD, then QED, then alphabetical (for canonical ordering / cross-process merging).
- `:1122-1147` candidate L-cut particles selected via `particle.is_perturbating(order, model)` and not in `forbidden_particles`; ordered whole-spin-no-anti, whole-spin-has-anti, half-spin-no-anti, half-spin-has-anti, each by PDG.
- `:1162-1167` `lcutone`=particle, `lcuttwo`=anti-particle, appended last so `lcuttwo` carries the highest leg number (required by the tagging).
- `:1192-1193` once a PDG is used as L-cut, it (and its anti) are barred from being L-cut again (`lcutpartemployed`) — avoids double counting the same loop content.
- **No loop-size / N-point cap and no "colored-loop-only" restriction in v3.7.1.** The L-cut generator produces loops of any point-count (pentagons, hexagons, ...) and with non-colored loop content (W/Z on quark lines, relevant to VBF/VBS/single-top). The only default loop-content removals are: step 10 perturbative-order filter (:858, drops loops not in the perturbed set + loops with exactly one colored leg), Furry (:872, SM-quark-loop conservative), wavefunction corrections + vanishing tadpoles (:842-854). There is NO artificial pentagon/higher-point discard — inclusion is governed purely by `is_perturbating(order,model)` + the coupling-order bounds. (The historical "v2 discarded these, v3 keeps them" release-note framing is not settleable from v3.7.1 source alone since v2 code is absent; the v3 side — full inclusion — is affirmed by the absence of any such filter.)

## LoopMultiProcess / LoopInducedMultiProcess (:1774-1794)
- `LoopMultiProcess.get_amplitude_from_proc` returns `LoopAmplitude({"process":proc})`.
- `LoopInducedMultiProcess.get_amplitude_from_proc` returns `LoopAmplitude({"process":proc,'has_born':False})` — THIS is the loop-induced flag at the diagram-generation layer: no born, loop squared against itself.
