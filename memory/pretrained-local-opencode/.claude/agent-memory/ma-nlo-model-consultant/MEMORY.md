## Slice
I own the loop-capable structure of UFO models: what CT declarations a model needs for NLO
(coupling_orders perturbative_expansion, CT_vertices/CT_couplings/CT_parameters, R2/UV/UVmass
types), how MadGraph detects them (LoopModel), bundled-vs-online loop models, and the HEFT
effective-vertex TIR branch. OUT: MadLoop runtime eval (madloop), generic UFO content (ufo),
restriction algorithm (restriction), NLO process syntax (nlo-syntax), EFT power counting (eft),
model installation (installation).

## Core operating principles
- Verify against source for THIS input every dispatch; adopt a scope-matching cached page per
  ma-wiki-as-evidence (sanity-check one file:line) else walk source.
- Source = code + config together: import_ufo.py, loop_base_objects.py, loop_diagram_generation.py,
  the model's coupling_orders.py / CT_*.py, and the TIR template files.
- Pretrained recall is hypothesis only. Loop capability is triggered by perturbative_expansion>0,
  NOT by CT files alone (import_ufo.py:500-502). That sets perturbation_couplings, the ONE list
  gating every loop stage downstream (gauge, generate gate, [all], CT selection) - see
  perturbation-couplings-spine.
- Runtime predictions (diagram counts, warnings, sigma) require a probe before being cached as fact.
- Stay in slice; hand off out-of-slice territory by name, don't answer past competence.

## Recent lessons (FIFO, max 5)
- card-and-count-drift: TWO drift meta-rules. (a) The card's file:line pointers drift -
  is_UVtree/is_R2/is_UVmass/is_UVloop/get_UV live on the Interaction class in core/base_objects.py
  (784-847), NOT loop_base_objects.py as the card says. Verify predicate
  locations against source, never the card. (b) The bundled loop-capable SET+count is install-specific
  and VOLATILE - some builds carry multiple loop-capable EFT models (2HDM/SMEFTatNLO among them),
  others carry only loop_sm; confirm per install with `ls models/`. NEVER a memorized count - live `ls models/` + scan
  coupling_orders.py with the importer's `>0` (import_ufo.py:501), NOT `=1` (misses pe=99). The
  volatile count lives in ONE page (bundled-online-loop-models); every other page POINTS, never
  restates - audit for duplicated counts across AND within pages.
- eft-ct-stub-and-np-not-all: CT-FILE PRESENCE != loop capability - only `perturbative_expansion>0`
  over coupling_orders.py decides (dim6top_LO_UFO ships a CT_couplings stub yet is genuinely LO,
  no CT_vertices.py). And "ALL EFT CT couplings carry NP" is WRONG: SMEFTatNLO mixes NP-carrying
  operator CTs (majority) with NP-less pure-SM-sector CTs (minority); EFT order (NP/DIM6) is NEVER
  perturbed, only QCD. Read splits fresh (counts drift). -> eft-coupling-orders-loop-structure.
- smeftatnlo-restrict-not-ct-gate: SMEFTatNLO `-LO` vs `-NLO` restriction does NOT gate loop
  capability - both import the same coupling_orders.py + CT_vertices.py before RestrictModel runs,
  so both are LoopModels (perturbation_couplings==['QCD']); "restrict_LO prunes CT couplings" is
  FALSE. Real -LO/-NLO diffs: NLO zeroes goldstone/ghost widths + turns off five operators
  (cG/cpG/ctlS3/ctlT3/cblS3), so -NLO is NOT a superset of -LO. -> smeft-at-nlo-loop-structure.
- resume-half-applied-landing: an interrupted authoring run can leave a NEW page on disk but its
  wiring incomplete (missing index line, zero inbound backrefs). RESUME: reconcile file-count vs
  index-count FIRST (a file newer than the index line is the tell), re-source-walk the new page's
  load-bearing cites, finish the index+backref wiring. A landed page is not a done page.

## Wiki page index
- loopmodel-detection: How the importer detects loop capability (perturbative_expansion) and builds LoopModel.
- ct-files-and-vertex-types: The three CT files, R2/UV/UVmass types, UV->UVtree/UVloop split, Laurent unfolding.
- ct-type-string-lifecycle: Layered CT 'type' tag (family/subtype/Neps) assembled by importer, decoded by is_* predicates; one vertex fires multiple predicates.
- ct-vertex-consumers: set_Born_CT (UVtree) vs set_LoopCT_vertices (R2/UVmass/UVloop) in loop diagram gen.
- particle-attached-wavefunction-CT: Loop-UFO renorm CTs attach to PARTICLE objects (particle.counterterm + loop_particles), not only CTVertex; importer synthesizes UVWfct_* couplings, set_Born_CT consumes per leg into LoopUVCTDiagrams; goldstone Feynman-gauge dependence.
- bundled-online-loop-models: Bundled vs online models in v3.7.1; loop-capable bundled set DRIFTS - do NOT carry a count here, live `ls models/` + SCAN coupling_orders.py with >0 NOT =1; loop_qcd_qed_sm bundled-presence flips across builds; _online_model dict.
- heft-tir-vertex-branch: HAS_AN_HEFT_VERTEX per loop group; structural HEFT-vertex rule; CutTools routing.
- ctparameter-eps-fin-expansion: CTParameter -> per-pole _2EPS_/_1EPS_/_FIN_ internal params; treat_couplings rewrites CT coupling exprs to per-pole dicts; double-pole coupling rejected vs 2EPS CTParam OK.
- process-loop-capability-gates: Process-time loop-capability enforcement - CheckLoop (earliest gate = validate_model body, probe-verified INFO string + sm->loop_qcd_qed_sm auto-upgrade), later get_combined_legs Gate 1/2, [all]/[loonly] expansion, two-site gauge->Feynman forcing; PLUS proc_validity gate w/ the DEAD `if not 'real':` block (always-False string-truthiness bug, dups the live checks; grounds lead process-verification-fanout "validate_model:513"=amcatnlo call site / def loop_interface.py:297).
- perturbation-couplings-spine: perturbation_couplings is one list (set from perturbative_expansion>0) gating every loop stage - gauge, generate gate, [all] expansion, CT-vertex selection; probe-anchored.
- ct-param-export-pruning: Export-side CTParameter pruning (build->extract_needed_CTparam->check_needed_param drops unused CTParams from written model); notused_ct_params base decode; coupling_orders_counterterms dead attr; 6993 dict-iter hazard.
- ct-diagram-gen-pass-mechanics: CT diagram-gen pass ordering + EXPOSURE gate - generate_ref_dict excludes UV/R2/UVCT by default, set_Born_CT exposes UVCT via actualize_dictionaries toggle + UVCT_SPECIAL synthetic-order double-generate; filter_loop_for_perturbative_orders is a 3rd order filter discarding impure-order loops with a WARNING; pass order 765->858->881.
- ct-generation-reuses-tree-machinery-via-revertible-mutation: GENERALIZATION over ct-diagram-gen-pass-mechanics + ctparameter-eps-fin-expansion + ct-vertex-consumers - no bespoke CT walker; CT gen/import temporarily MUTATE shared model/UFO state (UVCT_SPECIAL synthetic order + widened vertex dict; rewritten coupling value-dicts) so the ordinary tree machinery is reused, then REVERT. Three sites (set_Born_CT 1236-1277; treat_couplings 1548-1549/revert 2100-2113; actualize_dictionaries toggle); none try/finally-wrapped -> exception-unsafe (mid-bracket raise leaves shared state corrupted). Static mechanism, not runtime numerics.
- loop-model-regscheme-and-functions: Non-CT-vertex loop-UFO content - lhv HV/FDH scheme switch (model-internal, no CLI), MU_R LOOP-block renorm scale special-cased PS-dependent at export, and the dim-reg-safe loop-function vocab (reglog/cond/recms/...) parser-recognized + declared as Fortran intrinsics.
- smeft-at-nlo-loop-structure: SMEFTatNLO loop structure - QCD-only pe, NP power counting in CT coupling order dicts (most CTs NP=2, a minority NP-less SM-sector; read splits fresh), NO CT_parameters.py (renorm in UVGC pole dicts), restrict_LO/NLO/no4q hazards.
- eft-coupling-orders-loop-structure: Cross-model EFT loop pattern - EFT order (NP/DIM6) never perturbed, only QCD; NP rides in CT coupling order dicts; dim6top_LO_UFO is a bundled vestigial-CT-stub LO model (CT presence != loop capability); online EFT models (EWdim6/TopEffTh/heft) install-dependent.
- bsm-nlo-2hdm-loop-structure: Bundled 2HDM-family NLO loop models (BSM not EFT) - QCD-only, pure QCD/QED CT order dicts (no BSM order); the CT_parameters.py dichotomy (loop_sm is the ONLY bundled loop model with CTParameters; the other four encode renorm as CT_couplings pole dicts; two __init__ skip-mechanisms both caught by importer hasattr guard :549/:595).
