---
description: LO gridpack creation flow (gridpack=True → warmup survey + create_gridpack tarball) and seed/reproducibility — run.sh arg order, iseed=0 sentinel + auto-reset, gridpack seed determinism. v3.7.1. Complements gridpack-readonly-execution.md (RO execution side).
---

# LO gridpack creation + seed/reproducibility (v3.7.1)

Files: `madgraph/interface/madevent_interface.py`, `madgraph/interface/common_run_interface.py`, `Template/LO/bin/internal/Gridpack/run.sh`. Complements gridpack-readonly-execution.md (which is the RO refine EXECUTION side). This page is the CREATION side + seed semantics.

## Creation: `gridpack=True` → warmup survey + tarball (NOT event gen)
`do_generate_events` branch (madevent_interface.py:2576-2592): when `run_card['gridpack'] in self.true`, MG5 runs a **warmup survey** with hardcoded accuracy / points / iterations and `gridpack='.true.'` (2578-2581 — read the values there), then `combine_events` + `store_events` + `decay_events` + `create_gridpack` (2588-2592). So it optimizes grids and packages a tarball rather than doing a full high-stat event run. NUANCE: the warmup survey DOES run integration and produce some events (combine/store run); the *deliverable* is the tarball, not those warmup events.
`do_create_gridpack` (4164-4200): compiles `gen_ximprove`, prunes non-surviving `G*` dirs (4171-4181), flips `grid_card.dat` `GridRun` flag `.false.→.true.` via sed (4187), `restore_data`/`store4grid`/`clean`/`make_gridpack` (4189-4195), then `gridpack.tar.gz` → `<run_name>_gridpack.tar.gz` (4196-4197). Tarball packages compiled process code + optimized grids.
**SLICE SEAM:** the generate_events warmup branch (2576-2592) and `do_create_gridpack` orchestration are LAUNCH slice (do_create_gridpack is in ma-launch-consultant's list). The `survey`→`gen_ximprove_gridpack.launch()` refine side is mine (see gridpack-readonly-execution.md + refine4grid below).

## Using a gridpack: `./run.sh <nevents> <seed> [gran]`
`Template/LO/bin/internal/Gridpack/run.sh`: positional args parsed at 66-81 — arg0=`num_events`, arg1=`seed`, optional arg2=`gran`; options `-p/--parallel <nprocs>`, `-m/--maxevts <n>` (all arg defaults read at 66-81). Calls `bin/gridrun $num_events $seed $gran $nprocs $maxevts` (86). Output: `Events/GridRun_${seed}/unweighted_events.lhe.gz` → moved to `./events.lhe.gz` (91-97). Run name is literally `GridRun_<seed>` (set at madevent_interface.py:7089). So doc claim "output in Events/GridRun_XXXX" — XXXX is the SEED, and the final artifact is the moved `events.lhe.gz`.

`gridrun` → `GridPackCmd.__init__` (madevent_interface.py:6983): `self.random = seed`, `self.random_orig = seed` (6990-6991). **Requires nonzero seed AND nevents**: raises `MadGraph5Error('Gridpack run failed…')` if not `(me_dir and nb_event and seed)` (7002-7005) — so `seed=0` to a gridpack ERRORS, unlike the launch-path iseed=0 sentinel below.
`GridPackCmd.launch` (7084): `set_run_name('GridRun_%s'%seed)`, `refine4grid(nb_event)` (7110) → builds `gen_ximprove_gridpack(self, {'err_goal':nb_event,'split_channels':True,'ngran':granularity,'readonly':…,'nprocs':…,'maxevts':…})` (7153-7156) and `.launch()`. `save_random()` writes `r=<seed>` to `randinit` (7147-7148, 7021-7025) which Fortran `ranmar.f` reads → seed feeds the actual RNG.
**Gridpack IS directly reproducible per seed argument**: seed is a positional arg, written verbatim to randinit; same seed → identical events, different seeds → independent samples. No auto-reset on the gridpack path.

## `iseed` run_card sentinel (LAUNCH path, do_generate_events)
`configure_run_mode` (madevent_interface.py:6129-6143):
- `iseed != 0`: `self.random = int(iseed)` (6131), then **`reset_iseed_in_run_card()`** (6132).
- `iseed == 0`: if `SubProcesses/randinit` exists, CONTINUE from it (`self.random = int(data[1])`, 6136-6141); else `self.random = random.randint(1, 30107)` (6143).

`reset_iseed_in_run_card` (common_run_interface.py:4931-4942): if iseed≠0, **rewrites run_card on disk setting iseed BACK to 0** so "subsequent runs will use an automatically-generated (independent) seed rather than repeating the same one" (docstring).

The common summary "iseed=0 is a sentinel for auto/fresh seed; fixed positive = reproducible" is correct only with two nuances:
1. A fixed positive iseed IS used verbatim for THAT run (reproducible that run) — but the card is auto-reset to 0 afterward, so re-running does NOT repeat it unless you re-set iseed. Reproduction requires re-setting the seed each time.
2. iseed=0 is NOT purely "fresh random each run": it first tries to CONTINUE the sequence from `randinit` (each run saves `random+3` via update_random 6492 / save_random 6505). Only with no randinit does it draw `randint(1,30107)`. So iseed=0 in a reused dir gives a deterministic-but-advancing sequence (statistically independent successive runs), not an unseeded fresh draw.
- `update_random` (6489-6499): `self.random += 3`; hard cap `30081*30081` else raises.
- python-side RNG seeded separately by `python_seed` (-2 = same as run_card seed; ≥0 = that value; 6145-6155).

## Gridpack output = parton-level LHE, params frozen at creation
run.sh produces `events.lhe.gz` (parton-level LHE) only — no shower/hadronization in the gridpack itself. Model params/grids are baked at creation time (compiled process code + `store4grid`/`make_gridpack` snapshot). Editing param_card after tarball creation does not affect a deployed gridpack. (Downstream shower is a separate step; not in the gridpack.)

## NLO seam (out of my slice — amcatnlo)
NLO does NOT use `gridpack=True`: `grep gridpack madgraph/interface/amcatnlo_run_interface.py` → ZERO hits. NLO uses a MINT-grid workflow driven by `req_acc` (in the NLO `run_card.dat`). Cover the LO side; route NLO-gridpack questions to ma-amcatnlo-consultant.

## Security factor recap (mine, detail in gridpack-readonly-execution.md)
`gen_ximprove_gridpack` (gen_ximprove.py:1826-1833): class constants set no over-generation (`gen_events_security`), a single min-iter, and the gridpack max-iter + event/request caps — read the block at 1826-1833. Exact count met by the `check_events` resubmit loop with `.previous` carry-over, NOT by padding.
