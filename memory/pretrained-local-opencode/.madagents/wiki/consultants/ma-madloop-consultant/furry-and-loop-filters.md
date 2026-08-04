---
description: Loop-diagram filters — Furry-theorem removal, wavefunction/tadpole drops, user_filter and loop_filter syntax (loop_diagram_generation.py / loop_base_objects.py, MG5_aMC v3.7.1)
---

# Furry theorem + loop filters

`$MADGRAPH_INSTALL/madgraph/loop/loop_diagram_generation.py`.

## remove_Furry_loops (:314-344)
Conservative — only removes loops guaranteed zero AND SM-like, to avoid BSM false zeros. A loop diagram is discarded iff ALL hold (:330-334):
- odd number of photons (pdg 22) attached to the loop,
- number of gluons (pdg 21) attached ∈ {0,2},
- every attached leg is a photon or gluon,
- the loop line is an SM quark: `abs(loop_line_pdgs[0]) in range(1,7)` and all loop lines share that |pdg|.
Requires diagrams already TAGGED (raises MadGraph5Error otherwise, :324-326). Emits a `logger.debug` count of discarded diagrams (:341-344) — debug level, not warning.

## Wavefunction / tadpole drops (loop_base_objects.py LoopDiagram)
Applied in generate_diagrams :848-849, BEFORE Furry:
- `is_wf_correction(struct_rep, model)` (:479-504): a 2-line loop (bubble) with exactly one current off each side, at least one side external, OR a 1-line tag with two structs one external. Dropped (external-leg self-energies are handled by wavefunction renormalization in set_Born_CT, not as explicit loop diagrams).
- `is_vanishing_tadpole(model)` (:463-477): a tadpole (single tag, :451) is vanishing if it has ≤1 structure (absorbed by vev renorm) or the loop particle is massless.
- `is_tadpole` (:451), `is_fermion_loop` (:438) helpers.

## filter_loop_for_perturbative_orders (:496-539)
Keeps a loop only if (a) every loop-line particle is perturbating in some requested order, (b) at least one loop coupling order is in `perturbation_couplings`, and (c) NOT exactly one colored leg attached to the loop (:531-535, single-colored-leg loops are dropped). Warns once via `logger.warning` if any loop is dropped for impurity (:528-530).

- **`allowedpart`** (:501-506) = PDGs of every model particle `p` with `p.is_perturbating(order, model)` True for some order in `perturbation_couplings`. `is_perturbating` (base_objects.py:388-407) = "appears in a `base`-type interaction whose `orders` dict has exactly ONE key = this order" (multi-order vertices skipped, :401-402, so e.g. a SUSY γ-g-squark QED=1 QCD=1 vertex does NOT make the photon count as QCD-perturbating). So for `[QCD]`, `allowedpart` = colored particles (quarks+gluon); **W, Z, γ, H carry no pure-QCD vertex ⇒ NOT allowed in a QCD loop line.**
- The keep test (:525-526): `diag.get_loop_line_types() - set(allowedpart) != set()` (any loop-line particle outside allowedpart) OR `pert_loop_order == set([])` (no loop coupling order in the perturbed set) ⇒ discard. Not N-point specific — applies to bubbles/triangles/boxes/pentagons alike.

### Doc-claim corrections (verified v3.7.1)
- **The discard warning is NOT pentagon-specific.** A hand-doc claim that `[QCD]` "filters out pentagon diagrams containing non-QCD particles (W,Z,γ,H)" over-narrows: the filter keys on loop-LINE particle content + loop coupling order for EVERY loop topology, independent of leg count. There is no pentagon/N-point predicate anywhere in the filter.
- **Two distinct warnings, exact strings:**
  - the ACTUAL-filter warning, `filter_loop_for_perturbative_orders` :510-513: `"Some loop diagrams contributing to this process are discarded because they are not pure (QCD)-perturbation.\nMake sure you did not want to include them."` — note literal parens `(QCD)` (`'+'.join(perturbation_couplings)`), fired once when a loop is actually dropped.
  - the ORDER-GUESS heuristic warning, `generate_diagrams` :736-739: `"Some loop diagrams contributing to this process might be discarded because they are not pure (QCD)-perturbation.\nMake sure there are none or that you did not want to include them."` — `','`-joined, fired when the smart order-bounds MIGHT have excluded mixed-order loops (before generation). Different message, different trigger; don't conflate.
- **Discarding does NOT break the [QCD] IR-pole check.** The intuitive worry ("incomplete pole bookkeeping → poles do not cancel") is inverted: a loop with a W/Z/γ/H line is genuinely NOT part of the QCD perturbative order — it belongs to the [QED]/EW correction. The [QCD] virtual poles cancel against the [QCD] real emission + PDF collinear counterterms (FKS slice); the dropped EW loops carry no QCD IR singularity that the QCD reals would need to cancel. Keeping them would be the inconsistency. INFERRED from the filter's order-purity criterion; the pole-cancellation bookkeeping itself is fks/amcatnlo territory. Affects VBF `p p > h j j QCD=0 [QCD]`, VBS, single-top t-channel — real processes, correct behavior.

### nlo_mixed_expansion feeds this filter (cross-slice seam → amcatnlo/fks)
`nlo_mixed_expansion` (default True; banner.py:1770, madgraph_interface.py:3115) is a coupling-order-EXPANSION control, but "which loops are kept" and "coupling-order expansion" are the SAME mechanism from two sides — it sets the `perturbation_couplings`/`orders` that `filter_loop_for_perturbative_orders` then consumes:
- `amcatnlo_interface.py:672-673`: if `nlo_mixed_expansion` AND no explicit `[orders]`, `perturbation_couplings = list(all model coupling_orders)` → EW particles become allowed in loop lines.
- `fks_base.py:371-374`: mirror at born-process level — `nlo_mixed_expansion` False ⇒ `myproc['orders']=loop_orders` (pin loop to born's pure order); True + empty orders ⇒ `myproc['perturbation_couplings']=all coupling_orders`.
- So a process with EXPLICIT orders (e.g. `QCD=0 [QCD]`) keeps `perturbation_couplings=[QCD]` regardless, and W/Z loops are dropped as above. The "v2 discarded / v3 keeps pentagons with non-colored particles" release framing reduces to: whether QED is in `perturbation_couplings` (governed by nlo_mixed_expansion + explicit orders), not a hard-coded pentagon rule. Not settleable from v3.7.1 source alone (v2 absent); v3 side affirmed by absence of any N-point filter.

## user_filter + loop_filter (:375-494, get_loop_filter :346-373)
- OFF by default: `user_filter` returns immediately unless `edit_filter_manually=True` is hand-set OR a `filter` string is passed (:385-387).
- `loop_filter` string is supplied via `add process ... --loop_filter='<expr>'` (parsed in loop_interface.py do_add :838-849) or to `LoopAmplitude(loop_filter=...)`.
- The expression is `eval`'d (lowercased) against a namespace exposing `n` (#loop lines), `loop_pdgs`, `struct_pdgs`, `loop_masses`, `struct_masses`, `id` (:363-368). Return-falsey ⇒ diagram removed.

## `diagram_filter` is a no-op (API) / parse-error (command) in the loop path (v3.7.1)
`LoopAmplitude.generate_diagrams(self, loop_filter=None, diagram_filter=None)` (:595) accepts a `diagram_filter` argument (inherited-signature compatibility with the tree `Amplitude`), but it is NEVER referenced in the loop body — grep shows :595 is the only occurrence in loop_diagram_generation.py. Loop-diagram filtering goes ONLY through `loop_filter`/`user_filter`. `LoopMultiProcess`/`LoopInducedMultiProcess` (loop_diagram_generation.py:1774, :1787) do NOT override `MultiProcess.generate_diagrams`, which at diagram_generation.py:1892 calls `amplitude.generate_diagrams(diagram_filter=diagram_filter)` on the `LoopAmplitude` — so a programmatic caller passing `diagram_filter=` to a LoopMultiProcess gets it threaded all the way to :595 and silently dropped (API-level no-op).

BUT on the user-facing COMMAND path, `--diagram_filter` on a bracket process is NOT a silent no-op — it is REJECTED at parse time. The `--diagram_filter` extraction lives only in the base MadGraph `do_add` (madgraph_interface.py:3247), which is bypassed for any `[...]` bracket: master_interface `do_add` (:200-225) routes `[QCD]`→aMC@NLO iface, `[virt]/[sqrvirt]`→MadLoop/loop_interface iface, `[noborn]`→`create_loop_induced`. None of loop_interface/amcatnlo/fks `do_add` extracts `--diagram_filter` (loop_interface :835-849 strips only `--loop_filter=`), so the trailing `--diagram_filter` token survives into the process line and is parsed as a particle. PROBE-CONFIRMED (v3.7.1, mg5_aMC run): `generate g g > h [QCD] --diagram_filter` AND `generate g g > h h [noborn=QCD] --diagram_filter` both fail with `InvalidCmd: No particle --diagram_filter in model`. So a user who tries `--diagram_filter` on a loop/NLO process gets a hard error, not silent pruning-less behavior. The silent-drop no-op is reachable only via the Python API, not the REPL.
