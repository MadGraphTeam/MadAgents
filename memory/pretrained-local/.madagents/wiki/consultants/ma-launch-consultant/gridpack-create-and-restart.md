---
description: gridpack lifecycle — warmup branch in run_generate_events, do_create_gridpack (store4grid/make_gridpack, grid_card GridRun toggle), do_restart_gridpack (resubmit channels by precision).
---

# Gridpack creation and restart

Cites: `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (v3.7.1).

## How a gridpack gets made
Triggered when `run_card['gridpack']` is true. In `run_generate_events` (2576-2592) the warmup runs survey with a hardcoded `gridpack_opts` list (accuracy / points / iterations / gridpack='.true.') built at **2578-2581** — read the literal opts fresh there; they override `_survey_options`, so gridpack integration quality is fixed by this hardcoded set, not the run_card survey settings. Then `combine_events` -> `store_events` -> `decay_events -from_cards` -> `create_gridpack`. No refine stage.

## do_create_gridpack (4164-4200)
- `update_status('Creating gridpack')`; compiles `../bin/internal/gen_ximprove` (4169).
- Prunes G-dirs: any `G*` directory under each P-dir NOT in `get_Gdir()` is `shutil.rmtree`'d (4171-4181). (Guards against non-dir names starting with `G`, ref madgraph5/madgraph4gpu#947.)
- `check_combine_events(args)`; default `run_tag='tag_1'` (4185-4186).
- Flips `grid_card.dat` GridRun to `.true.` via in-place sed (4187-4188).
- Runs internal scripts in `me_dir`: `restore_data <run>`, `store4grid <run> <tag>`, `clean`, `make_gridpack` (4189-4195).
- Moves `gridpack.tar.gz` -> `<run>_gridpack.tar.gz` (4196-4197).
- Flips GridRun back to `.false.` (4198-4199); `update_status('gridpack created', level='gridpack')`.

So the deliverable is `<PROC_DIR>/<run_name>_gridpack.tar.gz`. The GridRun toggle in `Cards/grid_card.dat` is set true only for the duration of packing.

## Tarball layout + using the gridpack (make_gridpack + Gridpack/run.sh)
`Template/LO/bin/internal/make_gridpack` builds `gridpack.tar` from exactly two top-level members: a `madevent/` dir (the proc-dir contents) **plus `run.sh` at the archive root** (lines 8-18: `mkdir madevent; cp bin/internal/Gridpack/run.sh ./; mv $FILES madevent; tar -cf gridpack.tar madevent run.sh`). do_create_gridpack then renames it to `<run>_gridpack.tar.gz`.
- **Usage** (`Template/LO/bin/internal/Gridpack/run.sh`): `tar xzf <run>_gridpack.tar.gz` then `./run.sh <num_events> <seed> [granularity]` from the extraction root — NOT `cd madevent`. run.sh checks `if [[ -d ./madevent ]]` (29) and drives `madevent/bin/gridrun` (86). A hand-doc's "`cd madevent; ./run.sh`" is WRONG: run.sh lives beside `madevent/`, not inside it.
- **Args**: positional `[num_events] [seed]` (2 args) or `[num_events] [seed] [granularity]` (3). Second positional IS the random seed (claim TRUE). Options `-p/--parallel <nprocs>` and `-m/--maxevts <n>` (defaults drift-prone; **registration site not recorded on this page — needs a coordinate before quoting a value**, read from the do_create_gridpack option parser). gridrun call: `gridrun $num_events $seed $gran $nprocs $maxevts` (86).
- **Output**: gridrun writes `madevent/Events/GridRun_<seed>/unweighted_events.lhe.gz`; run.sh then moves it to `./events.lhe.gz` at the extraction root and (in the non-`./madevent` branch) purges Events/Cards/P*/dat/randinit (91-97). So the LHE lands in `GridRun_<seed>` (the dir is named by the seed value, not an arbitrary index) and the final artifact is `events.lhe.gz`.

## Gridpack limitations (claim 8)
- Params (param_card) are frozen at creation — VERIFIED by construction (the whole proc dir incl. Cards is tarred; run.sh does no card re-read). To change params you rebuild the gridpack.
- Parton-level only: run.sh -> gridrun produces `events.lhe.gz` only; no shower/detector step. VERIFIED (run.sh 86-97).
- LO `gridpack=True` is the LO madevent path; NLO uses a different MINT-grid mechanism (amcatnlo slice) — see restart/NLO seam below. VERIFIED by ownership (this flow is LO madevent_interface only).
- "100MB-several GB" size range is empirical/runtime, not a source constant — HYPOTHESIS.

## do_restart_gridpack (2332-2376)
Syntax: `restart_gridpack --precision=<value> --restart_zero`.
- Collects current results and relaunches channels not completed, optionally completed ones worse than a precision threshold, and/or zero-result channels.
- `check_survey(args)`; `gensym = gen_ximprove.gensym(self)` (2347).
- Parses `--precision=` (default `min_precision`, value at 2349-2357) and `--restart_zero` (default `resubmit_zero=False`) (2349-2357). **CONFIRMED BUG (Py3):** the `--precision=` parse at 2353 is `line[s:].split(1)[0]` — `str.split(1)` with an int arg raises `TypeError: must be str or None, not int` (probe-verified inline). So `restart_gridpack --precision=<value>` crashes before `resubmit`; only the default `min_precision` path (no `--precision=` flag) runs. `--restart_zero` is parsed by substring test (2356) and is unaffected.
- `gensym.resubmit(min_precision, resubmit_zero)` (2360) — gensym (mc-integration/phase-space slice) does the channel-level resubmission.
- `monitor(...html=True)`; `sum_html.make_all_html_results(self)` -> cross/error; `print_results`; then `decay_events -from_cards` and `create_gridpack` (2361-2376). NO combine_events/store_events (commented out, 2373-2374).

## Cautions
- A gridpack's integration quality is fixed by the warmup's hardcoded `gridpack_opts` (accuracy/points/iterations, literals at 2578-2581 — read fresh), independent of run_card survey settings.
- `restart_gridpack` rebuilds the gridpack at the end (create_gridpack) but skips the combine/store steps that a fresh run does; its job is channel resubmission + repack, not full event regeneration.
- The grid_card GridRun flag is left `.false.` after packing; if create_gridpack errors mid-way the card could be left in `.true.` state.
