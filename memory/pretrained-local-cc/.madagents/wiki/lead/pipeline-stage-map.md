---
description: Lookup, not a sweep match. Which slices own which pipeline stage, from model-load through the downstream tools.
---

# Pipeline stage -> owning slices

Dispatch behaviour only. MadGraph facts live in `../consultants/<name>/`. Confirm one cited file:line before adopting a consultant page as evidence.

**1. Model loading** (`import model`, gauge, CMS, restriction, multiparticles)
- `ma-model-loader-consultant` — `do_import`, gauge bit (0=unitary default, 1=Feynman), loop-model auto-switch, CMS, `aloha_prefix` (mdl_ default / `--noprefix`), V4↔UFO branch, `auto_convert_model` recovery, `add_default_multiparticles` (p/j 4-vs-5-flavour decided *after* restrict file read).
- `ma-ufo-consultant` — UFO file set (particles/vertices/couplings/lorentz/parameters/propagators/coupling_orders/decays + CT_* loop files), object_library classes, loader pipeline (`UFOMG5Converter`/`OrganizeModelExpression`), pickle cache (unitary→`py3_model.pkl`, Feynman→`_Feynman`, FDG→`_FDG`), Py2→Py3 scope.
- `ma-restriction-consultant` — `RestrictModel` 16-step pipeline (in-memory only, never rewrites param_card), zero/identical coupling detection (1e-13), 0/1 external→internal, mass/width→ZERO, keep_external (MSSM), auto-width restore sentinel, Goldstone-vector merge (FD gauge value 3 only), `ParamCardRule` at `models/check_param_card.py`.

**2. Process specification** (`generate`/`add process`)
- `ma-process-syntax-consultant` — `extract_process` parse pipeline, `>` validation (error from `check_process_format`), particle-name resolution, multiparticle expansion, `!a!` tagged photons (FKS/NLO-only), `@N`, `define`, `check`.
- `ma-chain-decay-consultant` — comma-driven `extract_decay_chain_process`, comma-vs-paren scoping, parser-acceptance≠amplitude-attachment trap, the `onshell` tri-state → `decayBW.inc` `gForceBW` (None→0/True→1/False→2). `>` cascade stays in `extract_process`, never enters the comma parser.
- `ma-coupling-order-consultant` — `QED=`/`QCD=`/`NP=`, `^2`, `==`/`<=`/`>`, EW↔QED/aS/aEW aliases (`=2*` doubling), `=`→`<=` reinterpretation warning, WEIGHTED, `constrained_orders`, `split_orders`. Tree-level only. `set default_unset_couplings N` is a silent-physics knob — once any order is set it injects `<=N` on every otherwise-unconstrained coupling (so `=0`+`QED=2` silently drops standard QCD production); route "my QCD diagrams vanished after setting an order" → `../consultants/ma-coupling-order-consultant/default-unset-couplings.md`.
- `ma-diagram-filter-consultant` — `/` (forbidden particle), `$` (forbidden onshell s-channel → `onshell=False`→`gForceBW=2`), `$$` (drop topology), `> >` (required s-channel). Shares the `onshell` field with chain-decay.
- `ma-polarization-consultant` — `{T,L,R,A,G,H,Q,W,S,±N,0..3}` parse, spin=2s+1, T/A/G/H/Q/W/S spin-1-only, L→-1 (warns; use 0 for longitudinal), 0 rejected for scalars/fermions, `check_polarization` per-PID helicity-overlap.

**3. Diagram generation + ME representation**
- `ma-diagram-enumeration-consultant` — `Amplitude`/`MultiProcess`/`DecayChainAmplitude`, `reduce_leglist`, `DiagramTag` chain-depth tagging, `has_mirror_process`, crossing reuse (disabled by s-channel filters/decay-chain/diagram_filter/loop), `NoDiagramException`, perturbed-decay-chain prohibition.
- `ma-helas-amplitude-consultant` — `HelasMatrixElement`/`HelasWavefunction`/`HelasAmplitude`/`HelasDiagram`, optimization 1 vs 0, wavefunction recycling, `IdentifyMETag` dedup, `CanonicalConfigTag`, Majorana flow clash, helicity-recycling rewrite (`matrix_orig.f`→`matrix_optim.f`).
- `ma-color-decomposition-consultant` — `ColorBasis` (6-tuple; docstring drift says 5), `ColorMatrix`, `colorize()`, ColorOne fallback, color-algebra primitives (T/Tr/f/d/Epsilon/K6 sextet), leading-N flow.
- `ma-aloha-consultant` — `AbstractALOHAModel`/`AbstractRoutine`, `compute_aloha_high_kernel`, multi-target writer hierarchy (Fortran/QP/Loop/C++/GPU/Python), Lorentz primitives, propagator numerators + gauge flags, PLY parser, HELAS naming.

**4. Code output** (`output <dir>`)
- `ma-output-consultant` — `do_output`, `ExportV4Factory` exporter selection, `Template/LO` copy, spin>3 hel_recycling auto-disable, JPEG(needs gs)/EPS/HTML, `UFO_model_to_mg4` finalize, P1N Lorentz augmentation. Hel-recycling output state is *two* mechanisms (finalize P1N flaglist gate vs exporter `hel_recycling` opt) that diverge under `--me_exporter`; don't treat `--me_exporter` as a flat "recycling off" — `../consultants/ma-output-consultant/no-helrecycling-two-mechanisms.md`.

**5. Card configuration**
- `ma-param-card-consultant` — `ParamCard`/`Block`/`Parameter`, SLHA1↔SLHA2, operative-source chain (UFO→restriction→output→user→runtime), `do_treatcards`→`param_card.inc`, `ParamCardIterator`, restriction sentinels (`9.999999e-1`→1, `0.000001e-99`→0).
- `ma-scales-pdf-consultant` — `lpp1/2`, `ebeam`, `pdlabel`/`lhaid`, `fixed_ren/fac_scale`, `dynamical_scale_choice` (allowed `[-1,0,1,2,3,4,10]`; =10 parses but Fortran-stops; =5 source-handled but run-card-rejected), `scalefact`, EVA/iEVA/EDFF/CHFF/IWW densities, αs path. `dynamical_scale_choice=-1` (CKKW) computes μR/μF in `reweight.f`/`setclscales` from clustered pt² → `../consultants/ma-scales-pdf-consultant/ckkw-clustering-scale-resolution.md`; heavy-ion beam-mass in `beam-mass-stot.md`.
- `ma-kinematic-cuts-consultant` — run_card cut params + `cuts.f` PASSCUTS; the run-card→Fortran mapping is in `setcuts.f`, not `cuts.f`; photon-isolation auto-disables pta/draj; `maxjetflavor>6` reject, `==6`+matching reject; xqcut/auto_ptj_mjj in two layers (banner.py parse + setcuts.f runtime, Fortran authoritative). **PDG-specific cuts (`pt_min_pdg`/`eta_*_pdg`/`mxx_min_pdg`) BYPASS `do_cuts` and DO fire on >20 GeV resonances** — the supported way to cut a top/W/Z/H/Z′ → `../consultants/ma-kinematic-cuts-consultant/pdg-cuts-and-smin.md` (also owns the smin partonic-ŝ floor). Cut-variable identity surprise (rapidity vs pseudorapidity) → `rapidity-vs-pseudorapidity-in-cuts.md`; see also fiducial-cuts-fanout.md.
- `ma-bw-window-consultant` — `bwcutoff`, `small_width_treatment`, `cut_decays` (read each default at its `banner.py` registration); `cut_bw` in `myamp.f` (two windows: a `bwcutoff×Γ_eff` window for LH-tag+forced/decay legs vs a smaller hardcoded-factor×Γ_eff window otherwise — read the factor in `myamp.f`). "`bwcutoff` only affects forced legs" is *incomplete* — two unconditional Regime-A sites act on ordinary s-channels → `../consultants/ma-bw-window-consultant/bw-bwcutoff-scaling-regimes.md`.

**6. Integration / event generation** (`launch`)
- `ma-launch-consultant` — `do_launch`/`survey`/`refine`/`combine`/`treatcards`/`compile`/`create_gridpack`, cluster backends, `bin/madevent`/`bin/generate_events`, gridpack warmup overrides, second-refine threshold (0.9).
- `ma-phase-space-consultant` — ICONFIG, `configs.inc` (MAPCONFIG/IFOREST/SPROP/TPRID), BW/collinear/soft/1-over-s mappings (`set_peaks`/`gen_s`/`transpole`), `gForceBW` activation at integration, `genps`/`x_to_f_arg`, `sde_strat`, RAMBO. Owns the cut↔integration seam — see fiducial-cuts-fanout.md.
- `ma-mc-integration-consultant` — VEGAS (`combine_grid`/`DiscreteSampler`/`Bin_Entry`), `combine_runs`, `gen_ximprove`, helicity recycling (`HelicityRecycler`/DAG, 0.1 threshold), HepMC parsing, EPS/UPS suspect indicators, negative-weight fraction.
- `ma-interface-consultant` — REPL infra (`extended_cmd.py`, `ask`/`SmartQuestion`/`ControlSwitch`/`CmdFile`), `mg5_configuration.txt` (template wins over user file for uncommented keys), `set`/`save options`/`display`, tab completion, plugin loading via `-m`.

**7. Downstream tools** (interface/handoff only — tool internals out-of-slice)
- `ma-madspin-interface-consultant` — `MadSpinOptions` (BW_cut resolves in `do_import`; spinmode full/madspin/none/onshell; max_weight; fixed_order), `do_decay`/`do_launch`, `launch -M`, `do_decay_events`, restart-from-LHE. Launch-side BW_cut abort only `>100`.
- `ma-pythia8-interface-consultant` — `do_pythia8` (default `main164`, `--old_interface` legacy), matching translation (`qCut=1.5*xqcut`), `pythia8_card_default.dat`, `PY8Card`, `ShowerCard`, HEPMCoutput.
- `ma-delphes-interface-consultant` — `do_delphes` (delphes2-vs-3 by `Delphes/data/` presence), cards (delphes_card_default==CMS; pgs_default==LHC), run_delphes3 STDHEP/HepMC by extension, default produces only `.root`, legacy `do_pgs`.
- `ma-madanalysis5-interface-consultant` — `do_madanalysis5_parton`/`_hadron` → one `run_madanalysis5` driver, `MadAnalysis5Card` `@MG5aMC` tags, shipped default cards parse to `skip_analysis=True`, `madanalysis5_path` unset in this install.
- `ma-rivet-interface-consultant` — `do_rivet`, `RivetCard.getAnalysisList` (`[default]` → curated MC_* set), Contur branch (pp + LHC equal-beam only), postprocess/run_contur. Rivet/yoda/contur not installed.

**Install/build** — `ma-installation-consultant` — `do_install`, `install update`/`looptools`, `convert_model`, source-server (`--source=ucl|uiuc`; uiuc points at INFN-Milan), `vendor/` offline tarballs, plugin version bounds enforced at *load* time (flips on `__debug__`/`-O`).
