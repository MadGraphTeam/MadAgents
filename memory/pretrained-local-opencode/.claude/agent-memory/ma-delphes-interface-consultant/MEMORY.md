## Slice
I own the MG↔Delphes interface: how MadGraph invokes Delphes (do_delphes), delphes_path
config, Delphes/PGS/trigger card templates + which variants are which, the LHE/HepMC→Delphes
handoff scripts, and legacy PGS (do_pgs). OUT: Delphes detector internals (jets, b-tag,
isolation, resolutions), Pythia8 shower, MA5/Rivet, MadSpin, NLO, Delphes install/ROOT compat.

## Core operating principles
- Verify against source for THIS input every time; adopt a scope-matching cached wiki page
  per ma-wiki-as-evidence (sanity-check one cited file:line) instead of re-walking.
- Source = code + config + card files together. A claim about card content is a source claim
  — read the file, don't recall.
- Stay in slice: per-module Delphes card parameters (resolutions, b-tag) are Delphes internals
  — name the boundary, don't answer. I own what the card files ARE and how MG selects/copies them.
- Runtime predictions (log text, output filenames produced) need a probe before being fact.
- The operative card's EXISTENCE is the detector on/off switch — `Cards/delphes_card.dat`
  (resp `pgs_card.dat`) present ⇒ the step runs; absent ⇒ silent no-op at every entry point.
  There is NO separate enabled flag. Most-asked class ("did Delphes run / why skipped"); see
  operative-card-existence-is-the-detector-switch page for the 5 gating facets + NLO caveat.

## Recent lessons (FIFO, max 5)
- regex-findall-not-substring: a missing comma concatenating two to_search elements does NOT
  let them match individually — re.findall emits only whole-alternative matches. Don't assume
  "OR-joined regex still matches substrings". Verify with a probe script before calling a bug
  benign-for-reason-X.
- diff-all-variants: when claiming card variants "differ", run diff -q on EACH against default,
  not just the obvious pair. delphes_trigger_CMS is byte-identical to default (only ATLAS
  differs) — was wrongly lumped with ATLAS.
- launcher-stale: card claimed Pythia8Launcher.prepare_run picks delphes/pgs mode; source
  (v3.7.1) shows it selects a main_*.cc file. self.delphes in MELauncher is vestigial
  (set, never read). Trust source over card description.
- grep-file-AND-class-before-attributing: a page cited ans_delphes/
  consistency_detector_shower to common_run_interface.py + "base class common_run" — both
  actually in madevent_interface.py class AskRun(ControlSwitch). Before asserting a function's
  file OR its enclosing class/inheritance, grep `def <name>` AND `^class` to confirm; the
  common_run<->madevent split is a recurring attribution trap.

## Wiki page index
- do_delphes-flow: do_delphes control flow — card copy, delphes2-vs-3 detection (data/ dir), prog dispatch, banner, LHCO gap.
- run-delphes-scripts: run_delphes (delphes2) vs run_delphes3 wrappers — which Delphes binary per input ext; root2lhco commented out.
- card-templates-and-defaults: Delphes/PGS/trigger inventory; default==CMS (delphes card+trigger) / default==LHC (pgs) → unedited run silently uses CMS/LHC geometry; delphes_path config default; PLUS `set delphes_card` accepts ONLY presets {default,atlas,cms} (case-sensitive), any other value → INVALID no-op — no lhc/trigger/per-param edits.
- delphes-path-config-and-install-token: delphes_path default is './Delphes' (NOT empty), resolves via mg5_path/MG5DIR join to bundled Delphes dir (exists) → set by default on bundled install; config line 172 commented but code dict default (653) fills it; three-leg gate (path-resolves / shower-present / card-exists); install token exact = 'Delphes' (install-slice). CORRECTS "default empty".
- do_pgs-flow: legacy PGS detector flow — compile, run_pgs, LHCO banner, ExRoot root conversion.
- card-type-recognition: detect_card_type tag strings classifying delphes_card/delphes_trigger/pgs_card; missing-comma bug makes ParticlePropagator+<mg5proccard> DEAD tags (live: ExecutionPath/Treewriter, <MGVersion>).
- launch_ext-launchers: MELauncher/Pythia8Launcher — self.delphes vestigial; real handoff is do_delphes not the launcher.
- check_delphes-input-resolution: which pythia/pythia8 output feeds Delphes (handoff input), priority order (STDHEP before HepMC, gz before plain), two copy-paste .gz path bugs in the one-arg branch.
- delphes-availability-and-card-provisioning: upstream of do_delphes — check_available_module gates Delphes on a shower; set_default_detector + auto-resolver pick detector; keep_cards creates operative delphes_card.dat from _default (lazy, not at output).
- nlo-amcatnlo-delphes-path: NLO path inherits do_delphes but overrides check_delphes (STDHEP-only glob+gunzip, no HepMC); nodefault kwarg signature mismatch (static fact); run_delphes3 absent from NLO template (CONFIRMED filesystem fact, not probe).
- delphes-trigger-chain-from-shower-step: what INVOKES do_delphes — auto tail-call from do_pythia/do_pythia8 (delphes --no_default, no-op unless card exists), interactive run-config menu auto-resolution, ans_delphes (forces shower on), consistency_detector_shower (refuses Delphes w/o Pythia); NLO does NOT auto-chain. NB ans_delphes/consistency_detector_shower live in madevent_interface.py class AskRun (NOT common_run). ALSO: detector=Delphes+shower=OFF auto-promotes shower (PY8 pref via callback, PY6 pref via bare-delphes ans_delphes) — committed by ControlSwitch.answer merging inconsistent_keys (extended_cmd.py:2713-2726), NO warning log; interactive switch table renders `Pythia8 ⇐ OFF` (color_for_value :2937-2941) so not truly silent, but -f caller gets no textual notice.
- operative-card-existence-is-the-detector-switch: PRINCIPLE — existence of Cards/delphes_card.dat (resp pgs_card.dat) is THE gate deciding whether the detector step runs at every entry point (shower tail-call, set_default_detector, auto-resolver, do_delphes body); keep_cards materializes it. Runtime no-op/runs consequence INFERRED not probed.
- card-identity-substring-routers: PRINCIPLE — card identity resolved by substring at TWO routers on DIFFERENT keys (detect_card_type on CONTENT, Banner.add on FILENAME); rename breaks banner-tag, header-strip breaks content-detect; predicts the two-disagree bug class.
- delphes-card-banner-lifecycle: how delphes_card/trigger live in the run banner — registry tables, Banner.add filename substring routing, recover_banner strips prior detector cards at pythia/pgs/delphes level, do_delphes appends operative card; LHCO-banner consume path commented out.
- delphes-plot-and-lhco-output: OUTPUT half of do_delphes — create_plot('Delphes') triple-gate (madanalysis_path+td_path+plot_card.dat), legacy plot_events/td pipeline on <tag>_delphes_events.lhco, root2lhco commented tail → default delphes3 yields ROOT only (no LHCO, no plots).
