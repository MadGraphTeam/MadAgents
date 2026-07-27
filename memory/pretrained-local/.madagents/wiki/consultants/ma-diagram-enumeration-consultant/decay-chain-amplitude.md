---
description: DecayChainAmplitude construction — Loop/MultiProcess branch, perturbed/one-incoming prohibitions, decay-leg onshell flagging, and the two decay warnings
---

# DecayChainAmplitude construction (diagram_generation.py)

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` (v3.7.1). class :1337, `__init__` :1348.

Signature: `__init__(self, argument=None, collect_mirror_procs=False, ignore_six_quark_processes=False, loop_filter=None, diagram_filter=False)`.

## Core-process generation branch (:1352-1375)
Imports `LoopMultiProcess` (:1354). Picks the MultiProcess class:
- `argument['perturbation_couplings']` non-empty → `MultiProcessClass = LoopMultiProcess` (:1356).
- else → `MultiProcess` (:1358).
Then:
- ProcessDefinition → `generate_multi_amplitudes(...)` extends `self['amplitudes']` (:1360).
- plain Process → `get_amplitude_from_proc(...)` appended, then the process's own `decay_chains` are cleared from the copied process (:1371-1375) because chains aren't combined yet.

## Prohibitions enforced per decay chain (:1377-1389)
Iterating `argument.get('decay_chains')`:
1. `process.get('perturbation_couplings')` truthy → `MadGraph5Error("Decay processes can not be perturbed")` (:1379). Forbids perturbed (NLO/loop) decay chains.
2. Sets `overall_orders` from parent, forces `is_decay_chain=True` (:1380-1382).
3. `process.get_ninitial() != 1` → `InvalidCmd("Decay chain process must have exactly one incoming particle")` (:1383-1385).
4. Recurse: each decay chain becomes a nested `DecayChainAmplitude` (:1386-1389). diagram_filter propagates; collect_mirror_procs/ignore_six_quark propagate.

## Perturbed-chain prohibition: my raise is DOUBLY shadowed; the live guard is in amcatnlo_interface (seam)
The enumeration-layer raise at :1379 — `MadGraph5Error("Decay processes can not be perturbed")` ("can not", two words, NO period) — is **defense-in-depth, NOT any guard a user hits**. THREE source strings exist (grep `be perturbed`); only ONE fires on the live path:
- `diagram_generation.py:1379` (MINE): `"Decay processes can not be perturbed"` — "can **not**" (two words), NO period. Dead — never reached.
- `madgraph_interface.py:3297` (MadGraphCmd.do_add): `"Decay processes cannot be perturbed."` — "cannot" (one word), **WITH period**. ALSO effectively dead on the live `generate` path (see why below). Comment :3293 "Redundant with above, but not completely..." flags it as redundant with my raise.
- `amcatnlo_interface.py:523` (aMCatNLOInterface, in the `if ',' in line:` block :520-523): `"Decay processes cannot be perturbed"` — "cannot" (one word), **NO period**. **THIS is the guard the user actually hits.**

WHY :3297 is shadowed too (the key point): a perturbed decay chain REQUIRES `[...]` bracket syntax (perturbation_couplings are populated ONLY from brackets). `master_interface.do_generate` → `extract_process_type` (`master_interface.py:162-196`, `loopRE`) classifies any `[orders]` line as `type=='NLO'` with `nlo_mode='all'` → `change_principal_cmd('aMC@NLO')` (:271-273) BEFORE `do_add` runs. So the command is dispatched to `amcatnlo_interface.aMCatNLOInterface`, whose `do_add` path runs the `:520-523` perturbed-decay guard — `madgraph_interface.MadGraphCmd.do_add` (where :3297 AND the `:3283` bracket-conjunction gate live) is **never entered for a perturbed decay**. The interface switch is the first shadow; my :1379 raise is the third (also never reached).
- `are_decays_perturbed()` (`base_objects.py:3568-3574`) is RECURSIVE — walks `perturbation_couplings` over ALL nesting depths of `decay_chains`. Used identically at :3296 and at `amcatnlo_interface.py:522`. My :1378 check is per-immediate-chain (`process.get('perturbation_couplings')`), but the `__init__` recursion (:1386) reaches deeper levels too.

PROBE-VERIFIED (raw bytes via `cat -A`): `generate p p > t t~, (t > b w+ [QCD], w+ > l+ vl)` prints `The current model sm does not allow to generate loop corrections of type ['QCD'].` then raises `str : Decay processes cannot be perturbed` — "cannot", **NO trailing period** (byte-checked: `...perturbed^[[0m$`). That is the `amcatnlo_interface.py:523` string verbatim, NOT :3297 (which HAS a period) and NOT my :1379 (which is "can not"). The interface switch + `extract_decay_chain_process` parsing are the process-syntax/chain-decay slice; my in-slice fact is only that the enumeration raise at :1379 exists as a redundant, never-reached last line of defense.

SCRIPTED-EXECUTION = INTERACTIVE (probe-verified). The guard fires at process-PARSE time, not launch time: `MasterCmd.do_generate`/`do_add` (`master_interface.py:265-277`) call `extract_process_type` (:162-196) on the raw line and run `change_principal_cmd('aMC@NLO')` (:271) BEFORE dispatching to the interface's own do_generate — this dispatch path is shared whether the line comes from stdin or a `.mg5` script file (`mg5_aMC script.txt`). Probed a single-level (no-parens) chain in a script: `generate p p > t t~, t > w+ b [QCD]` → `The current model sm does not allow to generate loop corrections of type ['QCD'].` then `Error detected in sub-command generate p p > t t~, t > w+ b [QCD]` / `str : Decay processes cannot be perturbed` (byte-checked no period, `...perturbed^[[0m$`). So the emitted string is verbatim (no period), it aborts the failing `generate` sub-command at parse time, and it fires even on non-loop `sm` (the "does not allow loop corrections" note precedes it but the perturbed-decay guard fires regardless — `are_decays_perturbed()` only tests that brackets populated perturbation_couplings, not loop-capability).

## Two cmd-layer-only decay prohibitions with NO enumeration counterpart (seam)
The framing "prohibitions enforced at decay-chain construction" includes guards my `DecayChainAmplitude.__init__` does NOT carry. Beyond perturbed/one-incoming, two further decay-chain prohibitions exist ONLY at the cmd layer (`madgraph_interface.MadGraphCmd.do_add`), never re-checked in enumeration:
- `:3301-3304`: `if myprocdef.decays_have_squared_orders() or myprocdef['squared_orders']!={}: raise MadGraph5Error("Decay processes cannot specify squared orders constraints.")`. `decays_have_squared_orders()` (`base_objects.py:3576-3582`) recurses over nested chains.
- `:3305-3307`: `if myprocdef.are_negative_orders_present(): raise MadGraph5Error("Decay processes cannot include negative coupling orders constraints.")`. `are_negative_orders_present()` (`base_objects.py:3554-3566`) recurses.

UNLIKE the perturbed guard, these two DO fire at `madgraph_interface.py` on the live path: `QED^2==4` / `QED<=-1` carry NO `[...]` brackets, so `extract_process_type` returns `'tree'` and the interface does NOT switch to aMC@NLO → the command stays in `MadGraphCmd.do_add` and reaches :3301/:3305. PROBE-VERIFIED: `generate p p > t t~, (t > b w+ QED^2==4, w+ > l+ vl)` → `str : Decay processes cannot specify squared orders constraints.` (:3303-3304 verbatim); `generate p p > t t~, (t > b w+ QED<=-1, w+ > l+ vl)` → `str : Decay processes cannot include negative coupling orders constraints.` (:3305-3307 verbatim). So the perturbed guard is the special case (it switches interface and lands at amcatnlo_interface.py:523); the squared/negative guards land at madgraph_interface as written.
My `__init__` (:1377-1389) checks ONLY perturbation (:1378) and ninitial==1 (:1383). So "a decay chain with `QED^2==4` or `QCD<=-1`" is rejected upstream of my slice; do NOT attribute these to `DecayChainAmplitude`. (Squared/negative-order SEMANTICS are the squared-order-filter / diagram-filter slices; the prohibition POINT is process-syntax.)

## Decay-leg flagging (:1391-1397)
`decay_ids` = set of initial-state ids of all decay-chain amplitudes (:1392-1395). For each core amplitude: `amp.trim_diagrams(decay_ids)`. This is the source-of-truth for the comma-syntax `onshell=True` outcome: `trim_diagrams` (:1270) sets `leg.onshell=True` on external FS legs whose id is in decay_ids (process legs :1284-1286; diagram legs :1294-1299). That marks which legs carry a decay chain.

## Mirror flag and decay chains: structurally impossible on decay sub-procs (:1352-1389, :1835-1836)
`collect_mirror_procs` propagates UNCHANGED into every nested chain: passed to the core `generate_multi_amplitudes` (:1362) and to each recursive `DecayChainAmplitude(process, collect_mirror_procs, ...)` (:1387). BUT the mirror gate in `generate_multi_amplitudes` requires `collect_mirror_procs AND process_definition.get_ninitial() == 2` (:1835-1836). Every decay sub-process is forced to `ninitial == 1` by prohibition #3 (:1383). So `get_ninitial() == 2` is ALWAYS False for a decay leg → a decay sub-amplitude can NEVER receive `has_mirror_process=True`, regardless of `collect_mirror_procs`. Only the ninitial==2 CORE process can carry the mirror flag. The flag is a core-process property; chain decays are mirror-irrelevant by construction.

## Plain-Process decay leg silently drops diagram_filter (:1366-1370, :1919-1924)
When a decay chain `argument` is a plain `base_objects.Process` (not a `ProcessDefinition` — i.e. no multiparticle in the decay), the `else` branch (:1367) calls `MultiProcessClass.get_amplitude_from_proc(argument, loop_filter=..., diagram_filter=...)`. The base `get_amplitude_from_proc(cls, proc, **opts)` (:1919) absorbs both kwargs into `**opts` and returns `Amplitude({"process": proc})` (:1924) — the opts are DISCARDED for a tree amplitude (docstring :1921-1922 says only loop_filter could matter, "not relevant for a tree amplitude"). So `diagram_filter` does not reach a plain-Process decay leg's generation through this path. (A ProcessDefinition decay leg instead goes through `generate_multi_amplitudes` at :1361 where diagram_filter IS threaded to `generate_diagrams`.)

## DecayChainAmplitude does NOT combine core × decay (boundary)
`DecayChainAmplitude` keeps the core amplitudes (`self['amplitudes']`) and the nested decay amplitudes (`self['decay_chains']`) as TWO SEPARATE lists (default_setup :1342-1346). It never builds the stitched full-process matrix element here. The actual combinatorial stitching (core diagram × each decay-leg diagram) happens DOWNSTREAM in `helas_objects.py`: `HelasDecayChainProcess.__init__` takes a `DecayChainAmplitude` (`$MADGRAPH_INSTALL/madgraph/core/helas_objects.py:5374-5376`), calls `dc_amplitude.get_decay_ids()` (:5411) and walks `get('decay_chains')` (:5420-5423). So:
- `get_decay_ids()` (:1508, returns `get_initial_ids()[0]` per decay amp + `make_unique`) is a method CONSUMED by the HELAS slice (`helas_objects.py:5411`), not by enumeration. It is distinct from the INLINE `decay_ids` built at :1392 (`legs[0].get('id')` directly, for the trim/warning logic) — both target the initial decaying leg id but are computed in different places for different consumers.
- The core×decay stitch, identical-decay-chain factors, and final ME assembly are the helas-amplitude slice's, NOT mine. My slice ends at "the separate core + decay amplitude lists are populated and decay legs flagged."

## Warning 1: decay without matching core particle (:1399-1424)
After removing every decay_id found among core process legs (:1400-1403), any REMAINING decay_ids trigger:
`logger.warning("$RED Decay without corresponding particle in core process found.\nDecay information for particle(s) %s is discarded.\n...This warning usually means that you forgot parentheses in presence of subdecay.\nExample of correct syntax: p p > t t~, ( t > w+ b, w+ > l+ vl)")` (:1409-1414). The `$RED` prefix is a color marker. The unmatched decay amplitudes are then REMOVED from their decay chain; empty chains removed (:1416-1424). So the decay is silently discarded after the warning, not a hard error.

## Warning 2: particle decaying to itself (:1426-1443)
For each decay amplitude, if the abs(initial-state id) appears in the abs FS ids, the process is "bad" (:1428-1437). If any: `logger.warning("$RED Decay(s) with particle decaying to itself:\n<processes>\nPlease check your process definition carefully.")` (:1440-1443). This is only a warning — the process is NOT removed.

## Cautions
- Prohibition #1 (perturbed) and #3 (one incoming) raise hard errors and abort generation; #2 (overall_orders) and the two warnings do not.
- Warning 1's remedy hint is parenthesization — the canonical trap is `p p > t t~, t > w+ b, w+ > l+ vl` (missing parens) where the `w+ > l+ vl` sub-decay has no matching core particle and is discarded.
- Decay-leg `onshell=True` flagging happens at chain construction (`trim_diagrams(decay_ids)`), NOT during the core `generate_diagrams` (which calls trim with empty decay_ids). `trim_diagrams` sets True at two sites with the same meaning: process legs (:1284-1286) and diagram legs (:1294-1299). The `Leg.onshell` field is a tri-state — canonical definition `$MADGRAPH_INSTALL/madgraph/core/base_objects.py:2111` comment "onshell: decaying leg (True), forbidden s-channel (False), none (None)" (default None at :2112). The False value is set elsewhere by the `forbidden_onsh_s_channels` filter (see `generate-diagrams-algorithm.md`, diagram_generation.py:793); downstream consumers of the flag (helas_objects, group_subprocs, export_v4) are out of this slice.
- `collect_mirror_procs`/`ignore_six_quark_processes` default semantics differ from MultiProcess: here `ignore_six_quark_processes` defaults to `False` (a bool) in the signature, vs `[]` in MultiProcess — it is passed through positionally.
- Do NOT expect `has_mirror_process` on any decay sub-amplitude: the mirror gate's `ninitial==2` test can never pass for a ninitial==1 decay leg, even though `collect_mirror_procs` is propagated into the nested chain. The mirror flag is a core-process-only property under chain decay.
- A plain-Process (non-multiparticle) decay leg silently DROPS `diagram_filter` via the `**opts`-swallowing `get_amplitude_from_proc` (:1924). If a user expects a diagram filter to prune a decay sub-process and the decay has no multiparticle, it does not reach that leg. (Filter SEMANTICS are the diagram-filter slice; the drop POINT is in-slice.)
- `DecayChainAmplitude` is NOT the combined matrix element — it is two parallel amplitude lists. Anyone asking "how many diagrams does `p p > t t~, (t > b w+, w+ > l+ vl)` have as a stitched process" needs the HELAS slice; `get_number_of_diagrams` (:1472) here returns the SUM of core + each decay's diagram counts, NOT the product (the combinatorial blow-up is computed downstream).
