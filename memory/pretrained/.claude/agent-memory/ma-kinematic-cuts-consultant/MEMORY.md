## Slice
I own kinematic cuts: run_card cut params (banner.py RunCardLO.default_setup), their
auto-corrections (check_validity), and enforcement (cuts.f PASSCUTS + setcuts.f mapping).
OUT: scales/PDFs, BW window, phase-space integration, NLO cuts, matching mechanism
(I cover only the run-card auto-disable when matching is on), detector/fiducial cuts.

## Core operating principles
- Source is truth (code AND config files MadGraph reads). Verify against source for THIS
  input every dispatch; or adopt a scope-matching cached page (ma-wiki-as-evidence) and
  sanity-check one cited file:line.
- The cut= tag in add_param is card-LAYOUT metadata only, NOT the Fortran enforcement.
- run-card value -> Fortran cut happens in setcuts.f (classification + array fill), not
  in cuts.f. cuts.f only enforces the pre-filled arrays.
- Cut values touched at 3 layers (creation defaulting / parse check_validity / runtime
  setcuts.f); latest wins, run_card text != enforced cut. Trace all 3 before answering
  "why isn't my cut respected?". See cut-value-layer-precedence.
- Cuts skip resonances (pmass>20 GeV) and neutrinos by design — EXCEPT PDG-specific dict
  cuts (pt_min_pdg/mxx_min_pdg/...) which bypass do_cuts and DO cut heavy states (the
  supported way to pt/eta/mass-cut a top/W/Z/H/Z'). See pdg-cuts-and-smin.
- Cuts also set the smin partonic-ŝ integration floor (setcuts.f:528-708, "Define smin
  to") — not just an event filter. And cut values mutate at a 4th place: setcuts.f ERROR
  TRAPS zero xptj/xpta/xptb/xptl/xetamin when the target class is absent.
- pass_point returns .true.; cuts run via PASSCUTS later, not at sampling.

## Recent lessons (FIFO, max 5)
- lo-nlo-cut-param-divergence: hand-authored docs routinely present NLO cut names/defaults
  as "LO". Tells are NAME + convention, not magnitude: pair-mass param is `mmll` at LO vs
  `mll`/`mll_sf` at NLO (RunCardNLO :5611+; setcuts.f:399 SFOS); NLO ships the eta cuts OFF
  (negative sentinel) while LO ships positive eta defaults ON. `set run_card mll` on LO =
  "invalid set command" + suggests mmll (common_run_interface.py:6359). Trigger: any claim
  citing a cut default or a pair-mass name — check which class, then read that class's
  banner.py default fresh before adopting (never carry a number).
- line-citation-drift-in-dense-regions: pages can ship with off-by-1-to-3
  line citations concentrated in the DENSEST source region (banner.py create_default_for_process
  / cut_class / hid_lines :4767-5142); the substantive claims are right but the :NNNN drifts.
  Trigger: deep-verify of any page citing closely-packed add_param/if-block lines. Behaviour:
  re-grep exact line numbers from source, never carry :NNNN forward from an older page.

## Wiki page index
- runcard-cut-params: LO run_card cut parameters — defaults, cut= sub-system tags, hidden flags — as registered in RunCardLO.default_setup (banner.py)
- runcard-cut-validity: RunCardLO.check_validity cut auto-corrections — nhel/maxjetflavor guards, photon-isolation auto-disable, xqcut/matching drjj-drjl zeroing, mmjj reset
- cuts-f-filter: cuts.f PASSCUTS filter sequence and pass_point — NaN/shat/pt/eta/DR/mass/HT/photon-iso order, CUTSDONE memoisation, dummy_cuts hook
- runcard-cut-process-defaults: process-driven cut auto-setting at card creation/write time — create_default_for_process (1->N remove_all_cut, multiplicity matching auto-enable, maxjetflavor auto-set), cut_class classification, writer hid_lines display logic
- cut-value-layer-precedence: cut values touched at 3 layers (creation/check_validity/setcuts.f), latest wins, run_card text != enforced cut — trace all 3 (probe-confirmed: matched p p>j,jj forces ptj/mmjj=xqcut at runtime)
- pdg-cuts-and-smin: PDG-specific dict cuts (pt_min_pdg/mxx_min_pdg/...) lowering + setcuts.f enforcement that BYPASSES the >20GeV do_cuts rule; smin integration-floor derivation; grouped-subprocess consistency hard-abort; ERROR TRAPS; setxqcuts forest mapping
- cut-precondition-auto-disable: precondition-gated cut auto-disable — a cut whose enabling precondition is unmet (superseding feature active: isolation/matching; OR target class absent) is silently ZEROED + warned, not clamped; tell is a "discarded"/"will be ignored" warning (probe-confirmed); distinct from the value-override layer-precedence law
- helicity-mc-machinery: MC-over-helicity runtime path — card nhel/limhel -> ISUM_HEL + GOODHEL pruning (limhel = relative keep-threshold, used only in nhel=0 warm-up), madevent_driver helicity-sum read, hel_recycling/filtering/zeroamp family, nhel=1 auto-set (loop-induced, EVA)
- ordered-ht-wbf-cuts: ordered jet/lepton-pt cuts (jetor AND/OR via cutuse), staged running-HT (ht2/3/4min), inclusive vs jet-only HT (ihtmin incl b-jets, htjmin light only), two WBF/VBF rapidity-gap cuts (xetamin/deltaeta, opposite-hemisphere, <2-jet goto-21 bypass past photon iso) — cuts.f:518-1095 + setcuts.f:488-517
- rapidity-vs-pseudorapidity-in-cuts: cut-variable identity — generic etaX + generic drXY use TRUE LAB-FRAME RAPIDITY (rap=0.5ln((E+pz)/(E-pz))+cm_rap, kin_functions.f:95), ONLY photon-iso cone uses pseudorapidity (iso_getpseudorap, cuts.f:1286); AND ptX enforces transverse MOMENTUM pt despite "Et"/etmin label (et!=pt for massive); all moot for massless classes, bite massive PDG-cut states / asymmetric beams
- custom-cuts-and-nocut: custom_fcts run_card param (list of .f files, edit_dummy_fct_from_file) + dummy_cuts LO sig (P) vs NLO sig (p,istatus,ipdg); no_parton_cut = set run_card nocut macro -> remove_all_cut zeroes every cut=-tagged param (bwcutoff untagged, survives)
- cut-decays-decay-product-exemption: cut_decays=False (default) silently exempts decay-product legs from per-particle fiducial cuts (ptl/etal/drll); comma/chain decay drops them, arrow form keeps them; setcuts.f do_cuts mechanism + anchored sigma
- maxjetflavor-param: run_card maxjetflavor (default at LO :4424 visible / NLO :5736 hidden, read fresh); controls jet-vs-b-jet CUT classification at setcuts.f:217-223 (pdg<=maxjetflavor->is_a_j light jet, maxjetflavor+1..5->is_a_b b-jet; b(pdg5) is b-jet when maxjetflavor<5, light jet when >=5); beam-driven auto-set upward by beam quark flavour at card creation (:4807); guards >6 reject (msg quirk "lower than 5") + ==6 matching reject; flavor-scheme itself is model-side
