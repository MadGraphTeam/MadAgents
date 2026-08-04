## Slice
I own phase-space integration setup: ICONFIG channel construction (configs.inc/symfact.dat/gensym),
per-channel propagator mappings (BW/collinear/soft via gen_s+transpole, set in myamp set_peaks),
gForceBW/cut_bw/OnBW per-event accept-reject, genps.f momentum generation, madevent_driver.f
orchestration, and DiscreteSampler channel-selection scaffolding (combine_grid.py).
Out of slice: VEGAS iteration/point counts & convergence (mc-integration), bwcutoff window semantics
(bw-window), NLO/FKS phase space, launch/cards/cluster, helicity recycling at event time.

## Core operating principles
- Verify against source for THIS input every dispatch; adopt a scope-matching cached page per
  ma-wiki-as-evidence (sanity-check one cite), else walk source. Pretrained MG recall is hypothesis.
- Source = code + the config/generated files MG reads (configs.inc, decayBW.inc, props.inc,
  symfact.dat, run/param cards). A claim about generated-file content is a source claim — read it.
- s/t classification is ONE fact (branch's first daughter = incoming leg => t-channel) re-derived at
  configs.inc (SPROP!=0<=>s, TPRID!=0<=>t, mutually exclusive/branch), set_peaks tsgn, map_invarients,
  one_tree; predicts mapping+var-count+itmax bump from one configs.inc read (st-channel-classification-invariant).
- Channel count = symfact.dat positive entries + BW subdivisions (dconfig fractional codes), NOT raw
  configs.inc MAPCONFIG count (use_config<=0 are symmetry mirrors, never integrated).
- Mapping (spole/swidth biasing) is distinct from enforcement (cut_bw on-shell reject); never conflate.
- Don't extend into bwcutoff-window details or VEGAS counts — name the boundary, hand off.

## Recent lessons (FIFO, max 5)
- export_v4-multi-copy: write_configs_file_from_diagrams/write_symfact_file/write_symmetry have 3
  exporter-class copies; LO output uses the ProcessExporterFortranME copies (configs ~5415, symfact
  6149, symmetry 5989), NOT the base-class ones. Trigger: citing export_v4 writers — pick the ME copy.
- cms-invariant-fixed-width-psmap: the phase-space BW map is FIXED-real-width, CMS-invariant. transpole
  pole>0 is y=pole+width*tan(width*z) (transpole.f:52-54), width=swidth=prwidth*prmass/stot, prwidth the
  real energy-independent model width. prmass/prwidth are double precision (genps.f:1867-1868) — cannot
  carry complex mass. write_props_file has NO complex_mass branch, emits abs(real mass/width)
  (export_v4.py:2117-2125); grep myamp/genps/transpole for complex|cmass|running = empty. So CMS changes
  ONLY the HELAS propagator denominator, never gForceBW/set_peaks/channel construction. Γ=0: swidth=0 gate
  skips BW, routes to setgrid power-law grid (myamp.f:452-458), no transpole div-by-zero. Trigger: any
  "does CMS/running-width change phase space" or zero-width-resonance-mapping question.
- discrete-unbias-timing-not-uniform: per-event MC discrete choices (subprocess/channel/helicity) all
  stay unbiased, but the unbias TIMING differs — select_grouping does WGT*=SUMPROB/SELPROC inline
  (super_auto_dsig_group_v4.inc:209-212), but sample_get_discrete_x does NOT touch wgt, storing
  hel_jacobian for matrix<i> to divide out later (dsample.f:1239-1242). Don't write a unified
  "draw-then-unbias-inline" generalization — it over-claims. Trigger: channel/hel selection synthesis.
- coemission-proof-is-caller-seam: to prove two generated files (configs.inc SPROP + decayBW.inc
  gForceBW) are co-emitted from ONE structure, cite the CALLER, not the producer — ME
  generate_subprocess_directory returns one s_and_t_channels from write_configs_file (export_v4.py:4453)
  and hands the SAME var to write_decayBW_file (:4475) + write_props_file (:4519). SPROP keys leg's id,
  gForceBW keys SAME leg's onshell (both vert.get('legs')[-1], :5525/:5533 vs :5891/:5894) — two attrs
  of one Leg. get_s_and_t_channels (helas_objects.py:1966) only CARRIES onshell (mother.get('onshell')),
  origin is upstream diagram-gen (base_objects.py:2112 default None). Trigger: any "shared-structure /
  same-pass co-emission" claim — name the caller seam + the leg attribute, don't stop at the producer.

## Wiki page index
- iconfig-channel-structure: ICONFIG channels from diagrams — output-side find_symmetry grouping + 4-vertex config exclusion, configs.inc tables, survey-side gensym/symfact.dat, BW-subdivision dconfig code, syntax->channel seam (one config per flattened chain diagram via get_s_and_t_channels; onshell flag rides leg into configs.inc+decayBW.inc in one pass).
- propagator-mappings-gen_s-transpole: s/t-channel change-of-variable mappings (BW, t 1/sqrt, 1/x, 1/x^n) via gen_s+transpole, driven by set_peaks spole/swidth + props.inc. Map is FIXED-real-width (not running/complex); CMS is ME-side only (props.inc real-abs, prmass/prwidth double precision, no complex in myamp/genps/transpole); Γ=0 degenerates BW->setgrid power-law, no div-by-zero.
- bw-resonance-rate-normalization: a gForceBW=1 forced s-channel resonance scales sigma as 1/Gamma_total — param-card DECAY width feeds BOTH the BW sampling (set_peaks->transpole) and the propagator iMGamma (VVS1_3); no BR<=1 reconciliation, stale total width silently rescales sigma (probe: b b~ > h,(h>w+w-)).
- gforcebw-cut_bw-onshell: gForceBW (decayBW.inc) semantics and cut_bw/OnBW per-event accept-reject in myamp.f.
- genps-momentum-generation: genps.f scaffolding — f_get_nargs, x_to_f_arg, gen_mom, one_tree (s/t + ping-pong), gentcms, get_channel_cut bias, map_invarients (Minvar + nb_tchannel).
- driver-and-channel-selection-sampling: madevent_driver.f orchestration (Program DRIVER, lbw decode, nb_tchannel itmax bump) + combine_grid.py DiscreteSampler grids.
- bw-subdivision-dconfig-roundtrip: the base-3 dconfig BW-subdivision code round-trips survey enCode -> driver DeCode -> G-dir -> myamp lbw gate under a shared ncode digit-count contract.
- rambo-flat-phasespace: RAMBO flat/democratic generator (rambo.py) — used by the standalone `check` command, NOT by integration; contrast with single-diagram-enhanced genps.f.
- st-channel-classification-invariant: s/t classification is one fact (first daughter = incoming leg) re-derived at configs.inc/set_peaks/map_invarients/one_tree — predicts mapping + var-count + itmax bump for ANY config; predicate not byte-identical across sites.
- single-diagram-enhancement-amp2-weight: ANS=ANS*AMP2(CHANNEL)/XTOT enhancement weight in generated matrix<i>.f (amp2=|diagram amps|^2, get_channel_cut multiplied in the XTOT loop) + grouped-subprocess prepare_grouping_choice/select_grouping PDF-weighted selection in auto_dsig.f. SMEFT pure-quadratic-bin crash 'All amp2 are zero but not the total ME' STOP 1 (sde_strat=1 uses filled amp2, all-zero when only EFT amps remain) -> fix sde_strategy=2 (amp2 REPLACED by propagator denominator, never consults amp2 array); banner auto-set forces pure-lepton/proton DY back to strat 1.
- beam-shat-rapidity-flux-genmom: gen_mom initial-state half — x1/x2/tau/eta sampling, s(-nbranch)=shat, cm_rap, flux assembly across the five beam regimes (pp GENCMS, dressed-ee/ISR, lpp==9 dummy, single-beam, no-PDF); the int-var->incoming-momenta side of x_to_f_arg.
- alpha-channel-selection-fortran: the Fortran per-event ICONFIG draw (sample_get_config cumulative alpha) + why the Ohl/Pittau alpha adaptation is DISABLED in v3.7.1 (psect accumulation commented out); standard configs==1 job returns mincfig, no draw.
- cut-phasespace-seam: where fiducial cuts bite LO integration — passcuts gate at dsample.f:181 (upstream of ME), cut-fail stores zero-weight point into VEGAS grid, CUTSDONE caching, cut-derived smin NOT a tau lower bound in standard pp (GENCMS TAUMIN=0; only dsqrt_shat caps from above), nb_pass_cuts/none_pass abort, dead pass_point.
- nconfigs-one-per-gdir-invariant: the standard per-G-dir job runs nconfigs==1 (driver inits =1, only mincfig<0 map-all mode bumps it) — one root → trivial channel draw (iconfig=mincfig), nb_tchannel computed + itmax bump, every map-all-only branch (alpha adaptation/psect) unreachable; predicts per-event channel/itmax behavior for ANY process.
