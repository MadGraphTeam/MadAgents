---
description: Scripted non-interactive aMC@NLO execution — the launch-flag semantics (-p/-x/-o/-r), the manual-gridpack batch workflow (nevents=0 integration-only + only_generation event jobs), the events.lhe.gz artefact, and the shared-me_dir concurrency hazard.
---

# Scripted non-interactive NLO execution + launch-flag parsing

`$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py`. The scripted-NLO / batch-gridpack workflow: launch-flag semantics and the manual two-phase substitute for the (absent) NLO gridpack. Entry is `./bin/aMCatNLO` → `aMCatNLOCmd` (this shell). Sibling pages: [[integration-driver-mint-loop]] (the MINT loop these flags steer), [[runtime-shell-commands]] (do_launch chain), [[ask-run-configuration-mode-resolution]] (mode from switches).

## Launch flag definitions (`_launch_parser`, 5950-5973) — verbatim help + consumer
All four verified against the `add_option` help strings AND the code that reads `options[...]`:

- **`-p` / `--parton`** (5962) help: *"Stop the run after the parton level file generation (you need to shower the file in order to get physical results)"*. Consumer: run_generate_events shower gate (1875) fires `run_mcatnlo`+MA5 only when `mode not in {LO,NLO,noshower,noshowerLO}` AND `not options['parton']`. So `--parton` = **produce the parton-level LHE, skip the shower.**
- **`-x` / `--nocompile`** (5957) help: *"Skip compilation. Ignored if no executable is found"*. Consumer: `compile_dir` (5457-5461) — `if all(exe exists for p_dir) and options['nocompile']: return`. So it skips compile **only when every subprocess exe already exists**; otherwise it compiles anyway.
- **`-o` / `--only_generation`** (5965) help: *"Skip grid set up, just generate events starting from the last available results"*. Consumer (event modes, 2024-2034): `create_jobs_to_run(only_generation=True)` unpickles `SubProcesses/job_status.pkl` instead of rebuilding (2158-2180), then the MINT loop does `if options['only_generation'] and mint_step < 2: continue` (2033) — **skips step 0 (Setting up grids) + step 1 (Computing upper envelope), jumps to step 2 (Generating events)** off the existing grids.
- **`-r` / `--reweightonly`** (5959): skip integration+event-gen, reweight the latest event files only.
- Also: `-f/--force` (use cards as-is, no edit), `-c/--cluster`, `-m/--multicore`, `-n/--name`, `-R/--reweight`, `-M/--madspin`. Identical option set on `_generate_events_parser` (5987+).

## Manual-gridpack batch workflow — the correct NLO substitute
There is **no NLO gridpack**. `gridpack` is a param of **RunCardLO only** (banner.py:4212, inside RunCardLO 4187-5593); **RunCardNLO (5594-6406) has no `gridpack` param**, and `amcatnlo_run_interface.py` contains **zero `gridpack` references** (grep-confirmed). So `gridpack=True` is meaningless/unsupported for an aMC@NLO output. The two-phase manual pattern replaces it:

- **Phase 2 (integrate once, no events):** `launch` with `set run_card nevents 0` + `set run_card req_acc 0.01`. In event mode (aMC@NLO/aMC@LO) the MINT loop hits `if mint_step+1==2 and nevents==0: self.print_summary(...); return` (2040-2042) — runs steps 0+1 (grids + upper envelope), stops **before** event generation → grids only, no LHE. `req_acc 0.01` is REQUIRED here: `nevents==0 and req_acc<0` raises `aMCatNLOError('Cannot determine the required accuracy ... 0 events requested. Please set "req_acc" ... between 0 and 1')` (1989-1993). `req_acc` (event-mode, run_card['req_acc'], 1988) is the MINT requested-accuracy stopping criterion (drives per-job upper-envelope target `req_acc2_inv=1/req_acc²`, 2711+). NOTE: this is `req_acc`, NOT `req_acc_FO` — the FO fixed-order loop binds req_acc_FO (see [[integration-driver-mint-loop]]).
- **Phase 4 (per-job event generation on batch nodes):** `./bin/aMCatNLO launch --parton --nocompile --only_generation` with per-job `set run_card iseed $TASK_ID`. Each flag verified above: parton-level stop, skip compile (exes exist from phase-2 build), skip grid setup and generate off the pickled grids.

## Per-job proc-dir copy — required by shared-me_dir state
Running several jobs concurrently in ONE `me_dir` races on **per-directory shared state**: `update_random_seed` reads+rewrites `SubProcesses/randinit` (1913-1920) — a single shared seed file, so concurrent jobs clobber each other's seed (defeating the per-job `iseed $TASK_ID` intent); `SubProcesses/job_status.pkl` (only_generation restart pickle, 2158-2180); per-channel `res_<step>.dat` and the G*-dir `events.lhe`; plus the base-class RunWeb lock (`aMCatNLOAlreadyRunning`, 919). So the advice "each batch job needs its own unpacked proc-dir copy" is sound. HYPOTHESIS-level (source shows the shared files; not probed with a real concurrent run).

## Artefact filename — events.lhe.gz
aMC@NLO / aMC@LO / noshower event modes write the final parton-level file to **`Events/<run_name>/events.lhe.gz`** (3881, 2995, 4558-4561; the `run()` assert at 1858 hardcodes this path). NOT `unweighted_events.lhe.gz` — that name is the LO madevent framework's. (Transient exception: `do_plot` briefly moves it to `unweighted_events.lhe` and back, 1557-1564 — a plotting quirk, not the artefact.) So NLO → `events.lhe.gz`, distinct from LO madevent's `unweighted_events.lhe.gz`.

## Boundary
LO gridpack creation (`do_create_gridpack`, `bin/madevent`) is the **launch slice** (madevent_interface.py); I confirm only the NLO-side *absence* of gridpack support. The AskRunNLO launch dialogue itself (order/fixed_order/shower switches, LO AskRun vs NLO AskRunNLO difference) is [[askrunnlo-dialog-and-showers]].

## Probe-candidates (expensive — not run)
- `./bin/aMCatNLO launch --help` inside a real NLO output (confirm the parser help renders as read).
- Full two-phase workflow (`p p > t t~ [QCD]`): phase-2 nevents=0 grids-only, then `--parton --nocompile --only_generation` event job — confirm no LHE after phase 2, events.lhe.gz after phase 4, and only_generation skips grid steps in the log.
- Concurrent same-me_dir launches to confirm the randinit/job_status.pkl race empirically.
