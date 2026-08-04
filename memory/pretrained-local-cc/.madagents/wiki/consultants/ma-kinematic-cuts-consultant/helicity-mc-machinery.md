---
description: MC-over-helicity machinery — run-card nhel/limhel become runtime ISUM_HEL + GOODHEL pruning (limhel = relative keep-threshold), the madevent_driver helicity-sum read, hel_recycling/filtering/zeroamp family, and the nhel=1 auto-set triggers (loop-induced, EVA beams)
---

# MC-over-helicity machinery (nhel / limhel runtime path)

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py` (RunCardLO),
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/matrix_madevent_v4.inc`,
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_driver.f`,
`$MADGRAPH_INSTALL/Template/LO/Source/gen_ximprove.f`,
`$MADGRAPH_INSTALL/Template/LO/Source/genps.inc`,
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/refine.sh`. MG5_aMC v3.7.1.

These are the helicity-MC *controls* listed as in-slice on my card (`nhel`, `limhel`).
runcard-cut-params.md only records their REGISTRATION (banner.py:4309/4310) and
runcard-cut-validity.md the nhel∈{0,1} guard (:4504). This page is the RUNTIME
semantics — what the knobs actually do — which none of the other 7 pages cover.

## The knobs (banner.py)
- :4309 `nhel` (include=False, default mode 0=sum). :4310 `limhel` (hidden, default read at
  :4310; comment "threshold to determine if an helicity contributes when not MC over helicity").
- :4504 check_validity: `nhel` must be in [1,0] else InvalidRunCard "can only be '0' or '1'"
  (runcard-cut-validity.md). So the USER-facing card admits only 0 or 1:
  - `nhel=0` → exact sum over ALL helicity combinations every event (no MC).
  - `nhel=1` → Monte-Carlo over helicities, ONE helicity combo sampled per event.
  (The driver also accepts `i>1` = i-per-event and `i=-1` = init mode, but the card guard
  blocks anything but 0/1; those other integers are reachable only internally.)

## The bridge: card nhel → runtime ISUM_HEL
`nhel` (include=False) does NOT go into run.inc as a compiled constant. It is read at
INTEGRATION time and piped to the per-channel madevent driver over stdin:
- gen_ximprove.f:58 `get_integer(...," nhel ",nhel_refine,0)` reads the card value;
  :60 an optional ` nhel_refine ` key overrides it (default = card nhel).
- gen_ximprove.f writes it into the per-job script as `echo "<nhel_refine>" >> input_sg.txt`
  on the `!Helicity` line (:355, also :713/:748/:901/:934 for the gridpack/refine variants).
- refine.sh:52 `echo "%(nhel)s" >> input_sg.txt` is the survey-side equivalent.
- madevent_driver.f:305-327 reads that integer `i` ("Exact helicity sum (0 yes, n=number/event)?"):
  - `i==0` → `isum_hel = 0` ("Explicitly summing over helicities") — the nhel=0 path.
  - `i==-1` → `isum_hel=0; multi_channel=.false.; init_mode=.true.; fixed_*_scale=.true.`
    ("Determining zero helicities") — internal zero-helicity-determination pass, NOT a card value.
  - `i>0` → `isum_hel = i`; registers the DiscreteSampler 'Helicity' dimension
    (DS_register_dimension('Helicity',NCOMB), :322) and `DS_set_min_points(hel_init_points,...)`
    (:326). hel_init_points = `n_grouped_proc*10*2` (export_v4.py:5933) ≈ "10×n_matrix" min
    probes per helicity before the grid is used.
- `ISUM_HEL` lives in `COMMON/TO_MATRIX/ISUM_HEL, MULTI_CHANNEL` (matrix .inc:72-74). It is
  set ONLY in the driver (madevent_driver.f:308/311/319); never assigned in any Template *.f.

## The algorithm: GOODHEL warm-up + LIMHEL pruning (matrix_madevent_v4.inc)
`MATRIX<i>` (the squared-ME) decides which helicity combos to sum each event. `NCOMB` =
all helicity combinations. `GOODHEL(NCOMB)` (common/BLOCK_GOODHEL/NTRY,GOODHEL :41-43) is the
set of helicities deemed to CONTRIBUTE. `NTRY` counts calls; `MAXTRIES` (genps.inc:35 — read
the value there) is the warm-up length.

- **Warm-up (NTRY ≤ MAXTRIES) when ISUM_HEL==0** (:106-145, the `nhel=0` sum path):
  every event loops ALL helicities (:107-117), accumulating `ANS=Σ|T|`. Then (:133-141) any
  helicity with `|TS(I)| > ANS*LIMHEL/NCOMB` is flagged `GOODHEL(I)=.TRUE.` and prints
  `Adding good helicity I, TS(I)/ANS`. So **LIMHEL is a RELATIVE keep-threshold**: a helicity
  whose contribution is below `limhel/NCOMB` of the running total is treated as zero and pruned.
  The small default (read at banner.py:4310) drops only numerically-vanishing helicities. At NTRY==MAXTRIES,
  `ISUM_HEL=MIN(ISUM_HEL,NGOOD)` (:143). Post-warm-up only GOODHEL helicities are summed.
- **MC mode (ISUM_HEL≠0, ISUM_HEL==1 → 1 hel/event)** (:146-159, the `nhel=1` path):
  genps picks `HEL_PICKED` from the DiscreteSampler 'Helicity' grid (genps.f:63-64,
  `sample_get_discrete_x(wgt,hel_picked,iconfig,'Helicity')`), the ME evaluates that ONE
  combination, `ANS = T*hel_jacobian` (:156). During grid initialization
  (DS_get_dim_status('Helicity')==0) it still loops all and calls `DS_add_entry('Helicity',I,T)`
  (:112) to build the importance-sampling grid, then negates HEL_PICKED (:123) so dsample
  doesn't double-count.
- After either path, one helicity is selected for the unweighted event by a CDF draw
  `R=XRAN1*ANS` (:160-172, SELECTED_HEL).

## hel_recycling family (banner.py:4453-4457) — separate optimization, also my slice
- :4454 `hel_recycling` True (hidden, include=False): "allowed to deactivate helicity
  optimization at run-time — code needed to be generated with such optimization". The v3.x
  per-helicity recycling (reuse wavefunction blocks across helicities); a RUN-TIME OFF switch
  for code that was GENERATED with the optimization.
- :4455 `hel_filtering` True: "filter in advance the zero helicities when doing helicity per
  helicity optimization." (pre-prune zero-contribution helicities before the run).
- :4456 `hel_splitamp` True: split aloha amplitude calls in two under per-hel optimization.
- :4457 `hel_zeroamp` True: drop zero amplitudes from the computation under per-hel optimization.
- These four have NO check_validity logic in RunCardLO (grep: only the registrations) — they
  are consumed at code-GENERATION / runtime, not parse-corrected. Distinct mechanism from
  nhel/limhel (which choose sum-vs-MC); these choose WHETHER the generated code recycles
  helicity wavefunctions. NOTE banner.py:1768 has a SEPARATE `hel_recycling` False on a
  different class (not RunCardLO) — do not conflate.

## nhel auto-set triggers (create_default_for_process)
`nhel` is force-set to 1 (MC over helicities) at card CREATION in three cases:
- :4781 `proc_characteristic['loop_induced']` → `nhel=1`. (Loop-induced has many helicities;
  MC is the default. Docstring :4770 "loop_induced -> MC over helicity".) Already noted in
  runcard-cut-process-defaults.md's create_default docstring; runtime meaning is HERE.
- :4855 / :4864 / :4879 EVA (effective vector-boson approx) beams — when W/Z appear in a
  beam (`lpp=±3` e-EVA, `±4` mu-EVA, pdlabel 'eva') the code sets `nhel=1` because the EVA
  PDF is helicity-dependent and summing is not the intended mode. (Beam/pdf semantics are
  scales-pdf slice; the nhel auto-set itself is the MC-over-helicity control I own.)

## Cautions
- `nhel` is include=False → it is NOT in run.inc and NOT a compiled constant. Editing it does
  not require recompilation; it takes effect at the next survey/refine because it is piped via
  input_sg.txt at integration time (gen_ximprove.f:355 / refine.sh:52). Contrast limhel, which
  IS in run.inc (run.inc:114-115 common/to_limhel/) and reaches the matrix file via its
  `include 'run.inc'` (matrix .inc:23) as the symbol `LIMHEL`.
- LIMHEL is a RELATIVE threshold (`ANS*LIMHEL/NCOMB`), not an absolute pt-like cut. Raising it
  prunes MORE helicities (faster, approximate); the small default (banner.py:4310) prunes only vanishing ones.
  It is consulted ONLY in the nhel=0 (ISUM_HEL==0) warm-up branch (:135) — in MC mode the
  DiscreteSampler grid handles helicity weighting, limhel is not used.
- MAXTRIES (genps.inc:35) is the warm-up length for building GOODHEL; the first MAXTRIES events
  per channel sum all helicities regardless of GOODHEL. `reset_cumulative_variable()` at
  NTRY==MAXTRIES+1 (:119) discards the warm-up bias from the accumulated cross-section.
- `print *,'Adding good helicity ...'` (:138) is a VERBATIM stdout line in the nhel=0 warm-up
  — observable trace that the GOODHEL pruning ran. (Runtime text predicted from source, not
  probe-verified.)
- This is the LO/madevent path. NLO (driver_mintMC.f:579 `isum_hel=0`) and loop-induced
  (matrix_loop_induced_*.inc — note loop-induced GOODHEL is indexed by proc_id) are adjacent
  but the amcatnlo/loop specifics are out of this LO slice.
