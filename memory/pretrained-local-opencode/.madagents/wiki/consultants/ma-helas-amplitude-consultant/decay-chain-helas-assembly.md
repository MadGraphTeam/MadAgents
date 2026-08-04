---
description: Decay-chain HELAS assembly — HelasDecayChainProcess.combine_decay_chain_processes, the two chains-populating branches + standalone ordered_for_pol guard (positional / out-of-order-single-each / pooled), insert_decay_chains/insert_decay wf-multiplication, identical_decay_chain_factor, check_equal_decay_processes.
---

# Decay-chain HELAS assembly

Cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (v3.7.1). The HELAS-layer counterpart to `DecayChainAmplitude`: how a production ME and its decay MEs are stitched into one combined ME.

## HelasDecayChainProcess @5341
Two props (default_setup @5347): `core_processes`(HelasMatrixElementList), `decay_chains`(HelasDecayChainProcessList) — recursive (a decay can itself be a decay chain).
- `__init__(DecayChainAmplitude)` @5373 → `generate_matrix_elements` @5401: core MEs built via `HelasMultiProcess.generate_matrix_elements(amplitudes, False, decay_ids)` @5412-5415; each decay chain recursively wrapped. **The positional `False` is `gen_color`, NOT `combine`** — the signature is `generate_matrix_elements(cls, amplitudes, gen_color=True, decay_ids=[], combine_matrix_elements=True, ...)` @5817-5819, so `combine_matrix_elements` is left at its DEFAULT True here and the core MEs ARE deduped via IdentifyMETag like any other multiprocess. What prevents the decaying particle's production from being folded into another ME is `decay_ids` (= `dc_amplitude.get_decay_ids()` @5411), passed through to the ME constructor @5934-5937 — not a combine=False.

## combine_decay_chain_processes(combine=True) @5427 — the assembler
Recursive. Base case: no decay_chains → return core_processes @5442-5444. Otherwise:
1. Recurse on each decay_chain @5450-5452 → `decay_elements` (list of HelasMatrixElementList per chain).
2. For each core process, find final-state legs whose id matches a decay's initial id (`fs_legs` @5471), bucket leg-numbers/indices by id.
3. **Two `chains`-populating branches `if/elif` @5510-5527, then a standalone `if/else` @5529-5541 sets `ordered_for_pol`.** The branches only fill `chains`; `ordered_for_pol` is NOT set per-branch — it is set solely by the guard `:5529` `if len(fs_legs)!=len(decay_elements) or not chains or not chains[0]:` (→ pooled, False) `else:` (→ True @5541). So "ordered" = "(a) or (b) populated non-empty `chains` AND counts match".
   - **(a) positional** @5510-5518: `len(fs_legs)==len(decay_elements)` AND `all(fs in ids for (fs,ids) in zip(fs_ids, decay_is_ids))` (each fs id is in its positionally-aligned decay's id-set) — each fs leg index pulls `decay_elements[index]`. Guard `:5529` False → `ordered_for_pol=True`.
   - **(b) out-of-order single-each** @5519-5527 (`elif`): `len(fs_legs)==len(decay_elements)` AND every decay element decays exactly one id (`all(len(d)==1)`) AND the multiset of fs ids equals the multiset of decay ids (`sorted(fs_ids)==sorted([d[0]...])`) — covers the reordered case where each chain decays one particle but listed out of fs order; matches `decay_elements` to fs ids by initial-id, not position. Guard `:5529` False (chains populated, counts equal) → still `ordered_for_pol=True`. **Verified distinct from (c):** e.g. `p p > t t~` with `decay_is_ids=[[-6],[6]]`, `fs_ids=[6,-6]` — (a)'s `all(fs in ids)` is False (`6 in [-6]` False), but (b)'s three conditions all hold, so the reordered one-each chain stays ordered and does NOT pool. The pooled-branch comment `:5530-5531` "(e.g. because the order of decays is reversed)" is stale — that reversed case is now caught by (b) and never reaches pooling.
   - **(c) pooled** @5529-5539 (the guard-True body): `len(fs_legs)!=len(decay_elements)` OR `not chains` OR `not chains[0]` — **all** decays for that particle-type are pooled and applied to every leg of that id (`chains=[chain]*len(fs_numbers[fs_id])`, `ordered_for_pol=False`).
4. Double-counting guard @5550-5565: products of chains are deduped by sorting `(process, pol)` via `list_for_sort()` so `(a>bc,a>de)` and `(a>de,a>bc)` collapse to one.
5. Per product: deepcopy core ME (with a model-swap trick @5577-5591 to avoid deep-copying the whole Model), then `matrix_element.insert_decay_chains(decay_dict)` @5609.
6. **Combine identical combined MEs** @5610-5641: if `combine`, build `IdentifyMETag.create_tag(me.get_base_amplitude(), me.get('identical_particle_factor'))` @5611-5613; on tag hit (`me_tags.index(me_tag)`), append the process (via `reorder_process` with stored permutations) instead of a new ME — logs `"Combining process with %s"` @5634. (Distinct from the per-product `"Combine %s with decays %s"` @5594, which is logged unconditionally for EVERY decay product before this combine block, not on a tag hit.)

### Polarization forces combine off @5543-5547
If `not ordered_for_pol` (pooled regime) AND any decayed fs leg carries a polarization, `combine` is set False — the IdentifyMETag can't see the symmetry-breaking from a polarization shift (comment cites `p p > w+{T} w+{0}, w+ > l+ vl`). So polarized decay chains in the pooled regime are kept as SEPARATE MEs.

## insert_decay_chains(decay_dict) @3940 (on HelasMatrixElement)
`decay_dict`: external-leg-number → decay ME. In-place surgery on the production ME:
- Builds `replace_dict[number]` = all mother-less production wfs for that external leg (one per fermion flow) @3957-3959.
- Detects Majoranas across production+decay wfs @3966-3973 (`fermionflow<0` or self_antipart fermion).
- Inserts decays leg-by-leg (sorted) via `insert_decay` @3978-3983.
- **overall_orders pruning** @3985-4004: after insertion, diagrams whose `calculate_orders()` exceed `process.overall_orders` are popped, then surviving diagrams renumbered and their wf-lists rebuilt.
- **Duplicate-wf cleanup** @4031-4069: fires only when `flows>1` OR (`#decay-diagrams>1` AND got_majoranas) — multiple fermion flows / Majoranas create doublet wfs; `update_later_mothers` @4445 rewrites mothers of later wfs to the surviving copy.
- Final renumber: all wfs `number=i+1`, all amps `number=i+1`, then **recompute** each amp's fermionfactor + color_indices @4073-4080, then `identical_decay_chain_factor` @4084.

## insert_decay(old_wfs, decay, numbers, got_majoranas) @4087
Replaces each production wf for one external leg with the decay sub-ME. Algorithm (docstring @4103-4117):
- Forbids polarization on decay initial states @4120-4123 (decay-chain polarization only allowed in production).
- One deepcopy of the decay diagrams **per old_wf** (per fermion flow) @4137-4138; Particle objects re-set to dodge deepcopy @4142-4148.
- Strips the decay's own initial-state (number_external==1) wf @4153-4155 (that leg becomes internal).
- Offsets `number_external` of new decay wfs by `incr_new` and of existing production wfs above the decay leg by `incr_old = nexternal-2` @4160-4179.
- **Multiplies production diagrams by Ndiag** (number of decay diagrams) @4182-4206: each production diagram is cloned `len_decay-1` times, diagram numbers spread as `(n-1)*len_decay + 1 + i`, amplitudes renumbered.
- Per decay diagram, the wfs that directly replace `old_wf` (the production leg) are the **second mother of each decay amplitude**: `final_decay_wfs = [amp.get('mothers')[1] for amp in decay_diag.get('amplitudes')]` @4267 (mother[0] is the decay's initial-state contraction wf, mother[1] is the final wf produced). These are pulled out of `decay_diag_wfs` and fed to `replace_wavefunctions`; the rest are inserted as auxiliary wfs.
- Then recursively replaces the decaying wf (and all wfs/amps having it as mother) with these final wavefunctions, flipping fermion flow where Majoranas require (see fermion-flow-clash-majorana page).

## identical_decay_chain_factor(decay_chains) @4581
Sets `identical_particle_factor` for the combined ME:
- `non_chain_factor` = product of factorials of identical-id counts among **non-decayed** final legs @4607-4617.
- `iden_chains_factor`: groups decay chains by `check_equal_decay_processes` @4629, multiplies `factorial(ident_copies)` per group @4652-4653.
- **Polarization correction** @4639-4647: when a decayed particle's identical copies span DIFFERENT polarizations and were NOT ordered_for_pol, multiplies factorials of per-pol counts and divides by `factorial(total)` — corrects the identical factor for polarization-split decays.
- Final: `non_chain_factor * iden_chains_factor * prod(decay-ME identical factors)` @4655-4659.

## check_equal_decay_processes(decay1, decay2) @5137 (static)
Decides if two single-sided decay MEs are equal for the identical-factor grouping. Cheap bulk checks first (same #legs, #diagrams, identical_factor, total #wfs, same initial id, same sorted fs ids) @5166-5181. Then either a direct `==` if leg-order already matches @5185-5190, else `check_equal_wavefunctions` @5218 — a recursive mother-pdg-matching walk from each amplitude's last mother (the initial-state contraction point). Asserts each ME is a single process with exactly one initial leg @5155-5161. Docstring @5141: MUST be called BEFORE any process combination.

## Cross-cutting
- **Identity keys** (see `identity-keys-purpose-tuned`): this assembler adds TWO more purpose-tuned equivalence relations to the catalogued four — `check_equal_decay_processes` (recursive mother-pdg walk, used ONLY for the identical-particle-factor grouping @4629) and the `ordered_for_pol`/`list_for_sort` pair (polarization-symmetry flag + `(process,pol)`-sorted double-counting dedup @5556-5564). The decay-chain `IdentifyMETag.create_tag` @5611 reuses the standard ME-dedup key. Each is a different property subset; combining on one says nothing about the others (e.g. ME-dedup tag-hit ≠ identical-factor-equal).
- **Mutation lifecycle** (see `helas-me-mutation-lifecycle`): `insert_decay_chains`/`insert_decay` are exactly the decay-insert mutation stage — they renumber every wf/amp in place, so a query's answer is stage-dependent here too.

## Cautions
- `insert_decay`/`insert_decay_chains` MUTATE the production ME in place and renumber every wf/amp — any cached wf number from before is invalid afterward (parallels the Majorana-clash caution).
- The combined ME's `identical_particle_factor` comes from `identical_decay_chain_factor`, NOT `calculate_identical_particle_factor` (the non-decay path). The two paths compute the symmetry factor differently; a decay-chain ME does not go through `process.identical_particle_factor()`.
- Polarized decays in the pooled regime defeat ME-combination AND get a special factorial correction — the simple "factorial of identical counts" intuition is wrong for polarized decay chains.
- The model-swap (`process.set('model', base_objects.Model())` then restore @5577-5591) is a deepcopy-cost dodge; if an exception fires between swap and restore, the core process is left with an empty model.
