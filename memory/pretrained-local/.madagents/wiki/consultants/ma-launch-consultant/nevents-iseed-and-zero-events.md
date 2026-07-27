---
description: Event-generation run_card params the launch flow consumes — nevents and iseed (0-sentinel = auto-seed from randinit), their registration coordinates, and the nevents==0 "integration-only" behavior (LHE discarded at combine_events, xsec still computed).
---

# nevents, iseed, and nevents==0

Cites `$MADGRAPH_INSTALL/madgraph/various/banner.py` and `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (v3.7.1).

## Template defaults — read fresh at coordinate
- `nevents` default: LO `RunCardLO.default_setup` `add_param("nevents", …)` at **banner.py:4214**; NLO `RunCardNLO` at banner.py:5615. Read the literal at the coordinate. Template line `%(nevents)s = nevents ! Number of unweighted events requested` (Template/LO/Cards/run_card.dat:26).
- `iseed` default: `add_param("iseed", …)` at **banner.py:4215** — the default is the auto-seed sentinel (`0 = assigned automatically`, per template comment `%(iseed)s = iseed ! rnd seed (0=assigned automatically=default)`, run_card.dat:27). Read the literal at the coordinate.
- No `check_validity` constraint on nevents — nevents=0 (or any int) is accepted silently; no positive-value guard (grep confirms only the two add_param lines in banner.py).

## iseed==0 "automatic" semantics (VERIFIED — configure_directory, madevent_interface.py:6129-6143)
- `if run_card['iseed'] != 0`: `self.random = int(iseed)`, then `reset_iseed_in_run_card()` and pin `self.configured` mtime (6130-6135). So a NONZERO iseed is the fixed offset, and is reset in the card.
- `elif SubProcesses/randinit exists`: read `self.random` from it (6136-6141) — this is how consecutive iseed=0 runs get DIFFERENT seeds: randinit persists the last offset (`save_random` writes `r=%s`, madevent_interface.py:6503-6506; also 7023), so the sequence advances across runs.
- `else`: `self.random = random.randint(1, 30107)` (6143) — first run in a fresh dir with iseed=0 and no randinit yet. NON-reproducible (Python `random` unseeded at this point).
- `update_random()` adds 3 to `self.random` per survey/refine call (madevent_interface.py:6489-6494); errors if `> 30081*30081`. Seed offset logged "Using random number seed offset = %s" (3499).
- Gridpack special-case: `iseed` is replaced by `gseed` (default registered banner.py:1820/4442; substitution at banner.py:4524-4526).
- `python_seed` default is the "follow iseed" sentinel (registered banner.py:4218; consumed madevent_interface.py:6146-6155) — read the sentinel value fresh.

## Seed is CONSUMED-ONCE — reproducibility trap (VERIFIED — reset_iseed_in_run_card, common_run_interface.py:4931-4942)
`reset_iseed_in_run_card` (shared LO/NLO, in `CommonRunCmd`) does more than "reset the object": when `iseed != 0` it sets `self.run_card['iseed'] = 0` AND **rewrites `Cards/run_card.dat` on disk** (`self.run_card.write(run_card.dat, template=run_card.dat)`, 4941-4942). Docstring is explicit: "reset it to 0 … subsequent runs will use an automatically-generated (independent) seed rather than repeating the same one."
- Consequence: a fixed `iseed=N` in the card is a ONE-SHOT. After the run, the on-disk card reads `iseed=0`. Re-launching the SAME directory does NOT reproduce — it falls to the auto branch (randinit → advanced seed). To repeat a σ you must RE-SET `iseed=N` before every launch.
- This is deliberate anti-footgun design (avoids identical statistics across a multi-run loop), but it means "I set iseed and it changed back to 0" is expected, not a bug.
- The reset writes the run_card BEFORE survey/refine/combine, so the run's banner (written at combine time from `self.run_card`) records `iseed=0`, NOT the value the user typed. The actually-used seed offset lives in the "Using random number seed offset" log line + `SubProcesses/randinit`, not in the banner's iseed field. [banner-faithfulness of the recorded seed = PROBE candidate; ordering inferred from reset-then-run, not run-traced.]

## Reproducibility policy (what to pin for a repeatable numerical σ)
- Set a NONZERO `iseed` in the run_card **for every launch** (it self-clears to 0 after use). `iseed=0` = deliberately non-reproducible.
- The seed advances `+3` per survey/refine call within one launch, so the seed→result map is deterministic only per full launch, not per stage.
- For gridpacks the knob is `gseed` (passed to `run.sh <nevents> <seed>`), not `iseed`.
- `python_seed` (default = the "follow iseed" sentinel, banner.py:4218) governs the Python-side unweighting RNG; leave it at that sentinel so the whole chain keys off one seed.
- Same nonzero iseed reproduces σ only if the rest is fixed too (model/param_card/run_card cuts/scales/PDF, MG version, and — because auto-seed reads randinit — a clean/identical `SubProcesses/randinit` state).

## nevents==0 — "integration only, no LHE" (LOAD-BEARING, VERIFIED)
Doc claim: "Setting nevents=0 runs integration only (no event generation): grids computed but no LHE produced." **CORRECT in substance, with a mechanism correction: it is NOT survey-only, and the discard happens at combine_events, not by skipping refine.**

Flow with nevents=0 (regular branch, run_generate_events 2593-2622):
1. `survey` runs normally (2597).
2. `nb_event = run_card['nevents']` = 0 (2599); `refine 0` STILL runs (2601). Second `refine 0 --treshold` also runs if xsec nonzero (2618-2620). So survey AND refine both execute — integration grids ARE refined. (Interpretation of err_goal=0 by gen_ximprove is mc-integration/phase-space territory; see boundary.)
3. `combine_events` runs (2622). Inside `do_combine_events`, the non-partial branch loops G-dirs and for each accumulates `sum_xsec/sum_xerru/sum_axsec` from `results.dat` (3905-3907), then:
   - **`if run_card['gridpack'] or run_card['nevents']==0:` -> `os.remove(Gdir/events.lhe); continue`** (3909-3911). Every G-dir's partial `events.lhe` is deleted and NOT added to `AllEvent`.
   - With nevents==0 all G-dirs skip, so `len(AllEvent)==0` -> `nb_event = 0` (3919-3920); the `AllEvent.unweight(...)`+gzip block is NOT reached. **No `unweighted_events.lhe(.gz)` is written.**
   - Same discard branch in `do_combine_events_partial` (3975-3977).
4. `nb_event < run_card['nevents']` -> `0 < 0` is False, so the "failed to generate enough events" warning (3929-3935) does NOT fire.
5. `results.add_detail('nb_event', 0)` (3939). `print_results_in_shell` still shows the CROSS SECTION (2623) — xsec is computed and reported; only the event file is absent.

Net: nevents=0 => survey+refine compute grids & cross-section, combine discards all partial events, zero unweighted events, no LHE file, no error. Downstream store_events/plots/shower run over an empty event set.

## Boundaries
- What `refine 0` / `err_goal=0` actually does to the number of integration points (does gen_ximprove treat 0 as relative-precision or event-target) is mc-integration/phase-space (`gen_ximprove`) territory, not launch. Launch guarantees only that refine is *invoked* with 0 and that combine discards.
- The 1M upper cap (`check_nb_events`, nevents>1000000 rewrite) is a separate row on launch-time-runcard-overrides.
