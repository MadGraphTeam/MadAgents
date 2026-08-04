---
description: Reaching the nevents target — "fail to reach target" (unweighting-side, post-integration, σ still valid), do_multi_run (MULTIPLIES statistics N×nevents, NOT nevents/N; LO-only), and the low-unweighting-efficiency channel warning. Plus sde_strategy launch-side plumbing (default registered banner.py:4458).
---

# Reaching the nevents target (fail-to-reach, multi_run, efficiency)

Cites `$MADGRAPH_INSTALL/madgraph/various/lhe_parser.py` and `.../interface/madevent_interface.py`, `.../madevent/gen_ximprove.py`, `.../various/banner.py` (v3.7.1).

## "fail to reach target" = UNWEIGHTING failure, post-integration (VERIFIED)
Two emit sites, BOTH inside `EventFile.unweight()` (lhe_parser.py:441, the final unweighting/reweighting loop), NOT integration:
- `lhe_parser.py:548` `"fail to reach target %s"` — the accept-weight `max_wgt` has converged (can't be lowered further) yet `nb_keep < event_target`; loop breaks.
- `lhe_parser.py:611` `"fail to reach target event %s (iteration=%s)"` — the `for...else` after all `nb_try` reweighting passes (bound registered at lhe_parser.py:529 — read fresh) still short of target.
Called from `do_combine_events` (madevent_interface.py:3883/3922, `AllEvent.unweight(..., event_target=self.run_card['nevents'])`) and the partial path (7297/7316). This runs AFTER survey+refine (integration) complete.

DIAGNOSIS: the message means integration succeeded and the cross-section is valid — only the unweighting could not extract enough unit-weight events to fill `nevents`. `nb_event < run_card['nevents']` then triggers the low-event warning (madevent_interface.py:3929). The reported σ is unaffected; the deficit is a statistics/efficiency problem (max event weight vs available weighted events), not an integration error. Doc claim (claim 1) = CORRECT.

REMEDY the message itself suggests via the warning at 3929-3935: raise integration statistics (more survey/refine points) so more weighted events exist to unweight, or `multi_run` (below).

## Related: low-efficiency channel warning (integration-side, VEGAS)
`gen_ximprove.py:1612` `"Channel %s/%s has a very low efficiency of unweighting. Might not be possible to reach target"` — emitted DURING refine (gen_ximprove), a forecast that a channel's unweighting efficiency is so low the target may be unreachable. Distinct from the post-integration lhe_parser messages; the efficiency LOGIC is mc-integration/phase-space territory (gen_ximprove), I only note where it fires.

## do_multi_run MULTIPLIES statistics (NOT nevents/N) — LO-only (VERIFIED)
`do_multi_run` (madevent_interface.py:3084). Loop `for i in range(nb_run)` (3106) calls `generate_events %s_%s -f` (3108) with **NO nevents override** → each sub-run generates the FULL `run_card['nevents']` (event_target=nevents at 3884). Total events = **N × nevents**, then merged via `bin/merge.pl` (3128) into `Events/<run>/unweighted_events.lhe.gz`; cross-sections combined inverse-variance-weighted (3114-3117).
- Doc claim (claim 2) "each generating nevents/N" is **WRONG** — it is the OPPOSITE: multi_run is the tool to EXCEED a single run's statistics, precisely the remedy pointed to by the 1M cap: `"Limiting number to 1M. Use multi_run for larger statistics."` (madevent_interface.py:6479). A single generate_events is hard-capped at 1M (nevents rewritten to 1000000, 6476-6483); multi_run N gets N×(up to 1M).
- **LO-only = CONFIRMED**: `def do_multi_run` exists only in madevent_interface.py:3084; `grep -c "def do_multi_run" amcatnlo_run_interface.py` = 0. NLO (amcatnlo) has do_generate_events (1705) but no multi_run.
- Invocation: `launch <PROC_DIR> -i` then `multi_run N [run_name]` (help_multi_run 416); `multi_run 1` warns to use generate_events (3091). Also supports a param_card `scan:` iterator loop (3158-3171, re-invokes `multi_run N -f` per scan point, summary → Events/scan_<name>.txt).

## sde_strategy — launch-side plumbing (VERIFIED; semantics = phase-space)
Run_card param: `add_param('SDE_strategy', <default>, allowed=[1,2], fortran_name="sde_strat", ...)` at **banner.py:4458** — read the registered default there (a doc-myth asserts 2; verify at the coordinate). Comment: `"1" means full single diagram enhanced (hep-ph/0208156), "2" use the product of the denominator`. `fortran_name="sde_strat"` → written to `SubProcesses/.../run.inc` at treatcards and consumed by the Fortran integrator. banner.py default-post-processing may auto-set the strategy: pure-leptonic final state → strategy 1 (4996-5014), `$` diagram-filter syntax forces strategy 1 (4774, 5055-5059); else strategy 2 in some branches (4988/4996). Integration SEMANTICS (what strategy 1 vs 2 does to channel weights) is phase-space's slice — I confirm only the run_card→run.inc plumbing and the coordinate.
