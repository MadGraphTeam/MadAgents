## Slice
I own the FKS subtraction scheme in MadGraph: FKS multi/process/real data structures,
real-emission phase-space partitioning, soft/soft-collinear singularity classification,
color-link generation for color-correlated borns, born-real IR linking, and EW-Sudakov-mode
handling. Out of slice: virtual/MadLoop computation, NLO process syntax, NLO Fortran export,
aMC@NLO launch, matching/merging, PDF/scale systematics.

## Core operating principles
- Verify against `$MADGRAPH_INSTALL/madgraph/fks/*.py` for THIS input every time; adopt a
  scope-matching cached page per ma-wiki-as-evidence and sanity-check one file:line.
- Enumerations/defaults drift across versions (this is v3.7.1) — re-read, don't recall.
- Two sections: Source-walked facts (cites) then Implications (DIRECT/INFERRED/HYPOTHESIS).
- Stay in slice; hand off virtual/export/syntax/launch territory by name to the owning slice.
- Soft classification, splitting enumeration, color links, dedup, sudakov dicts live in
  fks_common/fks_base/sudakov — read the function, don't assume the canonical case.

## Recent lessons (FIFO, max 5)
- poles-dont-cancel-taxonomy: "Poles do not cancel" IMMEDIATE cause = MadFKS-vs-OLP pole diff (BinothLHA.f:337-350). GENERAL getpoles mechanism (fks_singular.f:7534): Born×leg color/charge coeffs keyed per-leg on pmass(i).eq.ZERO (:7630/:7655) — massless leg→soft+collinear pole, massive→soft-only. ROOT cause NOT exclusively real/virtual. SCOPED cause (massive-b × 5F-PDF, e.g. import model sm with b massive): g→bb̄ real NOT enumerated (nsoft=0, fks_common.py:279-282) + no collinear-b pole → unmatched ISR sector → error; "never PDF/param" is FALSE. RESONANT-top does NOT cause it (BW peak, integrable, never in getpoles) — that's DR/DS+bwcutoff overlap axis. 4FS fix sound; IRPoleCheckThreshold=-1 MASKS not fixes. FKS_params.dat defaults (read fresh — drift) + disable-at-2-sites + >10% gate → ir-pole-cancellation-and-fks-params.md.
- fks-integration-vars: folding[1,1,1] slots = xi_i,y_ij,phi_i in order (driver_mintMC.f:615-617); S/H events via Hevents flag (add_write_info.f); NLO_mode='real' skips generate_virtuals → no MadLoop (fks_base.py:272-274) but reals still built.

## Wiki page index
- dr-ds-resonance-madstr: DR/DS (Diagram Removal/Subtraction) for resonant real-emission overlap (tt̄/tW) is NOT stock FKS — grep-absence over fks_*.py + NLO run_card; it's the MadSTR install-plugin (interface.py:6484/6503/6631, arXiv:1612.00440, PLUGIN/ empty in 3.7.1). Stock FKS keeps ALL real diagrams; only resonance concept nearby is bwcutoff BW-window (myamp.f, bw-window slice) + cluster.f channel clustering — neither removes overlap diagrams.
- soft-particle-classification: find_pert_particles_interactions IR-singular/soft rule (even-spin massless, degeneracy, ghost filters); per-pert_order recompute; SM probe (light quarks "soft"); BSM no-op order + coupling_orders restriction-dependence (SMEFTatNLO NP=no-op, b/τ massless→soft in 5F).
- splittings-and-real-generation: find_splittings/split_leg/insert_legs/find_reals — real-config enumeration, ij assignment, UPC/lepton/tag carve-outs, 2->1 & decay gates.
- extra-counterterm-and-dedup: generate_reals g/a->qqbar extra-cnt handling, find_reals_to_integrate double-count removal, check_ij_confs SILENT ij dedup.
- color-links: find_color_links/legs_to_color_link_string/insert_color_links color(charge)-correlated borns; need_color/charge_links flag; diagonal link only for massive legs.
- multiprocess-init-and-options: FKSMultiProcess defaults/options (OLP, ewsudakov, init_lep_split, nlo_mixed_expansion, ncores) and born->real->virtual __init__ flow.
- helas-async-generation: FKSHelas* objects, async_generate_real/born/finalize hooks, serial vs ncores path, ewsudakov disables ME combination; async TWO-STAGE combine (parent metag pre-filter + worker full __eq__ + not_combined retry); get_used_lorentz/couplings/processes/nexternal aggregation (extra_cnt OMITTED, per-proc list vs multiproc scalar); logger-silencing during build.
- ew-sudakov: sudakov.py SM-only isospin/goldstone dicts, charge conservation, get_sudakov_amps LSC/SSC amplitude enumeration.
- born-real-linking-and-tags: FKSDiagramTag/link_rb_configs (QCD-only rb_links), find_fks_j_from_i, combine_ij, fks_tag MultiTagLeg/TagLeg.
- fks-process-copy-discipline: FKS process-cloning invariant — shallow-copy process, rebuild legs separately; never copy.deepcopy a whole process (generate_virtuals/generate_reals/sudakov).
- fks-leg-structure-and-sort: FKSLeg keys (fks/color/charge/massless/spin/is_tagged/is_part/self_antipart), to_fks_leg model population, FKSLegList.sort "n j i" order, sort_proc renumber + Disordered guard.
- fksrealprocess-and-real-amps: FKSRealProcess fields + fks_infos config record (i/j/ij/ij_id/underlying_born/splitting_type/need_*_links/extra_cnt_index); generate_real_amplitudes dedup, combine_real_amplitudes merge-by-pdgs.
- silent-real-config-drops: GENERALIZATION — the stages where FKS prunes real (and born) configs (most silent at default log), the madgraph.fks_base/fks_helas_objects DEBUG knob, and the diagnostic for "expected real subprocess/config is missing". Probe-verified check_ij_confs DEBUG-only dedup.
- fkshelasrealprocess-equality: FKSHelasRealProcess __init__ 3 ME-provision modes + __eq__ (ignores fks_infos/charges + per-info ij_id/underlying_born) — the topology-not-flavor match behind within-born dedup and add_process 1-to-1 real merge.
- ir-pole-cancellation-and-fks-params: FKS_params.dat template+defaults, real-vs-virtual pole check (BinothLHA.f/check_poles.f), getpoles pmass-keyed residue (fks_singular.f:7534, massless leg→soft+collinear, massive→soft-only), negative-threshold disable (2 sites), "Poles do not cancel" >10% gate + ROOT-CAUSE TAXONOMY (flavor-scheme YES via missing g→bb̄, resonance NO), 4FS fix rationale, VBF/VBS workaround.
- fks-integration-variables-and-sh-events: xi_i/y_ij/phi_i FKS vars + folding-slot mapping, S-event(n-body)/H-event(n+1-body) decomposition, NLO_mode='real' virt-skip gating.
- fks-me-combination-topology-not-flavor: GENERALIZATION — FKS Helas ME combination matches on TOPOLOGY (IdentifyMETag/ij-shape), folds FLAVOR into per-ME leg-id process lists; probe: p p>tt~ 9 borns->3 MEs. Answers "why N subprocess dirs not M". ewsudakov inverts (no folding).
