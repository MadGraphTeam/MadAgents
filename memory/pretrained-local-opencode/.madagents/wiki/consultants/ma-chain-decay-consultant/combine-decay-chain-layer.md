---
description: HelasDecayChainProcess.combine_decay_chain_processes — the layer between DecayChainAmplitude and the combined HelasMatrixElement; recursive inner-decay-first combination, corresponding-vs-mismatched decay/fs matching, Cartesian product expansion + double-count removal, insert_decay_chains splice, second overall_orders pruning.
---

# The decay-chain combination layer (helas_objects.py)

Source: MG5_aMC v3.7.1. My other pages cover the parser (`extract_decay_chain_process`), the amplitude tree (`DecayChainAmplitude`), the onshell write (`insert_decay:4386`, see onshell-helas-bridge.md), and the output emission (`write_decayBW_file`). This page is the **combination middle**: how separately-generated core and decay HelasMatrixElements get spliced into the *combined* MEs that carry the onshell s-channel mothers. Statically read; key log line and decayBW.inc probe-confirmed.

## DecayChainAmplitude does NOT combine — it builds core + decays separately
`DecayChainAmplitude.__init__` (diagram_generation.py:1337-1451) only generates the core amplitudes (`generate_multi_amplitudes` for a ProcessDefinition, :1359-1365; or `get_amplitude_from_proc` for a plain Process, :1366-1375) and recursively wraps each decay as its own `DecayChainAmplitude` (:1386-1389). It explicitly notes the combine is deferred: at :1371-1375, for the plain-Process branch it *strips* decay_chains off the core amplitude's process copy "since we haven't combined processes with decay chains yet". The combine is a separate helas-layer pass.

## HelasDecayChainProcess — generates core + decay MEs, then combines
`HelasDecayChainProcess` (helas_objects.py:5341-5424):
- Constructed from a `DecayChainAmplitude` (:5376) → `generate_matrix_elements` (:5401):
  - `decay_ids = dc_amplitude.get_decay_ids()` (:5411) — passed into `HelasMultiProcess.generate_matrix_elements` (:5413-5416) for the CORE so it sets the wf `decay=True` field (helas_objects.py:683-684) and does not merge processes differing only in which legs decay.
  - core MEs → `self['core_processes']` (:5418); each decay chain → its own `HelasDecayChainProcess` appended to `self['decay_chains']` (:5420-5424), popped to save memory.
- The driver (helas_objects.py:5870-5873) calls `combine_decay_chain_processes(combine)` on this object to produce the final ME list.

## combine_decay_chain_processes (helas_objects.py:5427-5643) — the algorithm
Recursive. Per its docstring (:5432-5438):
- If #decay-chains == #decaying final-state particles → apply each decay chain to its corresponding fs particle.
- If they mismatch → all decays for a given particle TYPE are combined (no double counting).

Step by step:
1. **End recursion** when no decay_chains (:5442-5444) — return `core_processes`.
2. **Recurse inner decays first** (:5450-5452): `decay_elements.append(decay_chain.combine_decay_chain_processes(combine))`. A sub-decay's own subdecays (e.g. `t > b w+, w+ > e+ ve`) are combined *before* the parent splice. Probe-confirmed by the nested log `Combine t > b w+ ... with decays w+ > e+ ve` printed BEFORE the outer `Combine g g > t t~ ... with decays t~ > b~ w-, t > b w+`.
3. **Pop each core process** (:5467-5469) and find its decayed final-state legs `fs_legs` (:5471-5472, those whose id matches some decay's initial id).
4. **Per unique fs id, pick the chains** (:5494-5567):
   - **corresponding case** (:5510-5518): `len(fs_legs) == len(decay_elements)` and each fs id is in the matching decay's ids → use the decay element at the same index for each fs particle. `ordered_for_pol = True`.
   - **out-of-order single case** (:5519-5527): same count, each decay has exactly one id, sorted ids match → match by id across reordered decays.
   - **fallback / mismatched** (:5529-5538): count differs or no chains found → `chain = sum of all decays whose initial id == fs_id`, broadcast to every leg of that id (`chains = [chain]*len(fs_numbers[fs_id])`); `ordered_for_pol = False`.
5. **Polarization guard** (:5543-5547): if not ordered-for-pol and any fs particle carries a polarization, set `combine = False` (cannot merge across pol-shifted symmetry). [polarization-syntax interaction — defer pol semantics to that slice.]
6. **Cartesian product + double-count removal** (:5550-5568): `itertools.product(*chains)`; a sorted (process, str(pol)) key in `red_decay_chains` skips the duplicate `(a>bc,a>de)` vs `(a>de,a>bc)` orderings.
7. **Apply to core** (:5572-5609): for each product over `decay_lists`, deepcopy the core ME (with a model-stash trick to avoid copying the whole model, :5577-5591), build `decay_dict` (leg number → decay ME), log `"Combine <core> with decays <...>"` (:5594-5599), then `matrix_element.insert_decay_chains(decay_dict)` (:5609) — the splice that sets onshell=True (see onshell-helas-bridge.md insert_decay:4386).
8. **Identity merge** (:5610-5641): if `combine`, build `IdentifyMETag` (:5611-5613); identical combined MEs are merged (processes appended with reordered external numbers); only MEs with both processes AND diagrams are kept (:5624-5626).

## insert_decay_chains does a SECOND overall_orders prune (helas_objects.py:3985-4006)
After splicing all decays, `insert_decay_chains` re-checks the *combined* diagrams against `overall_orders` and pops any whose total `calculate_orders()` exceed the cap (:3990-4002), then renumbers diagrams/wfs (:4006-4026). This is distinct from — and downstream of — the amplitude-layer `min(orders, overall_orders)` cap documented in orders-through-decay-chain.md (diagram_generation.py:570-577). So the `@N QCD=2` overall cap is enforced TWICE: once per-fragment at amplitude build, and again on the combined diagram set after splicing. A combined diagram whose core-order + decay-orders sum exceeds the cap is dropped here.

## Probe (MG5_aMC v3.7.1)
`generate p p > t t~, (t > b w+, w+ > e+ ve), t~ > b~ w-; output`:
- Log shows the recursive combine: inner `Combine t > b w+ ... with decays w+ > e+ ve` then outer `Combine g g > t t~ ... with decays t~ > b~ w-, t > b w+` (and the nested `Decay:` tree).
- `SubProcesses/P1_qq_ttx_t_bwp_wp_lvl_tx_bxwm/decayBW.inc`: `GFORCEBW(-1..-3,1)/1/` (t, w+, lepton-side mothers from the splice), `GFORCEBW(-4,1)/0/` (undecayed mother). Matches onshell-as-single-source.md value-1 nesting case — confirming the combine layer's insert_decay:4386 onshell=True is what reaches decayBW.inc.

## Multiparticle in a decay clause: Cartesian expand + silent no-diagram skip
A decay clause with a multiparticle label (e.g. `..., z > l+ l-` with `l+`/`l-` = {e,mu,ta}) is a decay `ProcessDefinition`; its amplitudes are generated by the SAME `MultiProcess.generate_multi_amplitudes` (diagram_generation.py) that expands the core. The label content is Cartesian-expanded into candidate leg-multisets; each candidate is generated independently. A candidate that yields no diagram is SILENTLY dropped — `generate_multi_amplitudes` appends it to `failed_procs` and `continue`s (diagram_generation.py:1889-1906: `except InvalidCmd: failed_procs.append(...)`, and the `elif not result: failed_procs.append(...)` no-diagram branch), raising `NoDiagramException` ONLY if EVERY candidate fails (`if not amplitudes:` :1907-1912). So a physically-disallowed decay channel inside a multiparticle expansion produces neither a diagram nor a warning — MG5 does not validate physical allowedness, it just enumerates and keeps what has ≥1 diagram. The surviving per-clause decay MEs then feed the Cartesian combine above (:5550). Boundary: the enumerate-and-skip mechanism itself (`generate_multi_amplitudes`/`failed_procs`/`NoDiagramException`) is diagram-enumeration's slice; what this slice owns is that a DECAY clause's multiparticle rides that mechanism and the surviving decays combine Cartesian-wise into the chain.

## Why this matters
- "Why do my multiple decay channels for the same particle all appear?" → the mismatched-count fallback (:5529-5538) combines ALL decays of that id; the Cartesian product (:5550) expands every combination. Number of combined MEs is a product over per-leg chain choices.
- "I gave decays out of command-line order — did they still attach right?" → yes, the out-of-order single case (:5519-5527) and id-matching fallback handle it; attachment is by particle id, not textual order. (Consistent with combine_decay_chain_processes' docstring.)
- The onshell s-channel mother that decayBW.inc reports is created in THIS layer (insert_decay), not in the parser or DecayChainAmplitude. To trace a gForceBW value, the splice is the operative step.
