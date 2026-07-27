---
description: The process-line multiparticle expansion + zero-diagram drop + coherent/incoherent summation seam — extract_process builds MultiLeg 'ids' lists (mine); MultiProcess.generate_multi_amplitudes does the Cartesian expansion and drops zero-diagram combos (diagram-enumeration). v3.7.1.
---

# Multiparticle expansion / zero-diagram drop / coherent-vs-incoherent seam (v3.7.1)

Two behaviours cross the parser → diagram-enumeration boundary: (a) multiparticle expansion drops zero-diagram combos silently; (b) diagrams within one `generate` interfere coherently while separate `generate`/`add process` are summed incoherently. This page pins where the boundary lies.

## What the PARSER (my slice) does — carries ids, does NOT expand
- `extract_process` leg loop (madgraph_interface.py 5043-5242, see particle-name-resolution.md) resolves each token to a list of pdg ids (a multiparticle → many ids; a plain name → one id) and builds `base_objects.MultiLeg` objects each with an `'ids'` list. The final container is a `MultiLegList` → `ProcessDefinition`. **No Cartesian expansion happens at parse time** — the ProcessDefinition holds legs-with-id-lists, not concrete processes.
- So `generate p p > l+ l-` produces ONE ProcessDefinition whose two FS legs carry `ids=[−11,−13]` and `[11,13]` (default `l+ = e+ mu+`, `l- = e- mu-` — **tau EXCLUDED**; only 2×2, not 3×3). The parser never enumerates the combinations. The exact default-multiparticle CONTENT is model-loader's slice — source of truth is `$MADGRAPH_INSTALL/input/multiparticles_default.txt` (`l+ = e+ mu+` / `l- = e- mu-` tau-excluded, whereas `vl = ve vm vt` DOES include tau); read it fresh, don't assume `l±` spans all three generations.

## Where the EXPANSION + DROP happen — `MultiProcess.generate_multi_amplitudes` (diagram-enumeration slice)
`madgraph/core/diagram_generation.py`, `MultiProcess.generate_multi_amplitudes` (classmethod, 1663). Reached from `MultiProcess.get('amplitudes')` (1630-1652) when `do_add` builds the MultiProcess (madgraph_interface.py ~3368). This is **diagram-enumeration territory, not mine** — I own only the ProcessDefinition it consumes.
- **Initial-state Cartesian product**: `for prod in itertools.product(*isids)` (1736), `isids` = per-IS-leg id lists.
- **Final-state Cartesian product**: `for prod in itertools.product(*fsids)` (1764), nested inside IS loop.
- **Final-state double-count dedup** (1762-1771): `red_fsidlist` set keyed on sorted `(id, polarization)` tuple — identical FS multisets are generated once (e.g. avoids double-counting `e+ mu-` vs a symmetric relabel within one FS multiparticle set).
- **Zero-diagram drop** (1887-1904): each surviving combination → `Amplitude` → `amplitude.generate_diagrams(...)`. Then:
  - `except InvalidCmd` → combo appended to `failed_procs` (crossing-symmetry skip list), NOT to amplitudes.
  - success but `if amplitude.get('diagrams'):` FALSE (empty) → `elif not result:` → `failed_procs.append(...)`; **the combo is silently dropped** (never appended to the returned `amplitudes`).
  So `p p > l+ l-`: `e+ mu-` (LFV) yields zero diagrams in the SM → dropped; only same-flavor `e+ e-`, `mu+ mu-` survive (NO `ta+ ta-` — default `l±` is tau-excluded, see above; for tau you'd add it explicitly or use a tau-inclusive multiparticle). **No separate `add process` needed; the drop is automatic and silent** — but the DROP MECHANISM is diagram-enumeration's, not the parser's.
  - Crossing-symmetry reuse (1857-1885) and mirror-process collection (1835-1853) also live here.
- **Total-empty guard** (1906-1912): only if NO combination across the whole product yields any amplitude → `NoDiagramException("No amplitudes generated from process %s...")` (1911) — or re-raises the single stored `InvalidCmd` if exactly one combo failed with one (1908-1909). A *partial* drop (some combos survive) raises nothing.

## Coherent vs incoherent summation (claim 3) — the boundary
- **Within one Amplitude**: its diagrams share one `HelasMatrixElement` → one `|M|²` where diagrams add at amplitude level → **coherent interference**. (HELAS/color territory — helas-amplitude / color-decomposition.)
- **Across Amplitudes** (different surviving multiparticle combos, OR different `generate`/`add process` lines): each is a distinct `Amplitude` in the `AmplitudeList`. `generate` wipes `_curr_amps`, `add process` appends (extract-process-orchestration.md §state-lifecycle). Distinct amplitudes → distinct matrix elements → separate `|M|²`, **summed incoherently** (cross-sections add) at integration time.
- **My slice owns only**: each `generate`/`add process` → one ProcessDefinition → (after enumeration) one-or-more distinct Amplitudes appended to `_curr_amps`. The **coherent-within / incoherent-across statement is a diagram-enumeration + matrix-element + integration fact** (how the AmplitudeList becomes separate subprocess dirs summed at event-generation) — cite the boundary; do not claim the summation mechanism as mine.

## `group_subprocesses` — the grouping knob (interface/output-owned, edge note)
Source-confirmed v3.7.1 (a hand-doc claim: "generation-time MG5 option, NOT run_card, set before generate/output").
- **It is an MG5 interface option, NOT a run_card parameter.** Lives in `options_madgraph` (madgraph_interface.py:3102, default `'Auto'`); in `_set_options` (3019) → settable `set group_subprocesses <val>`. Grep of `banner.py` + `Template/{LO,NLO}/Cards/run_card.dat` finds ZERO `group_subprocesses` key — it never appears in a run_card. So it cannot be set "during launch" via the run_card; setting it there is a no-op.
- **Read at GENERATION/OUTPUT time, not run time.** `do_output` reads it at ~9257 (`if options['group_subprocesses'] in [True,False]: group_processes = ...`; `'Auto'`→default True except the 1-initial multi-subprocess decay case → False, warning at 9280); also read to set `collect_mirror_procs` at 3359/5423. It must be set BEFORE generate/output: set2 logs `'Note that you need to regenerate all processes'` (7972), and the 9280 warning says set it `'to True (before the output of the process)'`.
- **Allowed values: five, not three.** `set2_group_subprocesses` (7948-7970): `auto`/`nlo`/`gpu` are case-insensitively mapped to the strings `'Auto'`/`'NLO'`/`'gpu'`; anything else → `format_variable(.., bool)` so `True`/`False` (and any bool-castable) become Python bools. Doc's "True/False/Auto?" is right but incomplete (also `NLO`, `gpu`).
- **Boundary**: the option registration (`do_set`/options_configuration) is interface-consultant; the output-time read + grouping effect (mirror collection, subprocess grouping in `generate_multi_amplitudes`) is diagram-enumeration/output. It touches THIS seam only because grouping decides how the expanded subprocesses are bundled — the parser (my slice) never reads it.

## Seam summary (route accordingly)
| Step | Owner |
|---|---|
| token → id list, MultiLeg/ProcessDefinition assembly | process-syntax (me) |
| itertools.product expansion of leg id-lists | diagram-enumeration |
| zero-diagram combo drop / NoDiagramException | diagram-enumeration |
| coherent sum within an amplitude | helas-amplitude / color-decomposition |
| incoherent sum across amplitudes (σ add) | mc-integration / output (subprocess combination) |
