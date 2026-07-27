---
description: Post-integration LO stages — do_combine_events(+_partial), do_combine_iteration, do_store_events, do_compile — turning per-channel G-dir results into unweighted LHE, banner write, cleanup, low-event warning.
---

# Combine / store / compile stages

Cites `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (v3.7.1). These are the stages run after survey+refine in `run_generate_events`; survey/refine themselves are on survey-refine-and-thresholds.

## do_combine_events (3770-3947)
Turns per-channel `G*/events.lhe` into the run's `unweighted_events.lhe(.gz)`.
- `check_combine_events`; `update_status('Combining Events', level='parton')` (3776-3777).
- Gridpack short-circuit: if `run_card['gridpack']` and `isinstance(self, GridPackCmd)` -> delegates to `GridPackCmd.do_combine_events` (3780-3781).
- **Banner write** (3784-3797): recovers/loads the banner, `add_generation_info(cross, nevents)`, `change_seed(random_orig)`, writes `Events/<run>/<run>_<tag>_banner.txt`. So the per-run banner is authored here (combine), not at store time.
- If `run_card['gridpack']` truthy: returns after banner write — no unweighting (3800-3801).
- **max_G** = `ulimit -n` minus 40 (open-fd budget), 2500 if unlimited, 80 on error (3813-3823). Governs whether the combine is chunked.
- `remove_empty_events(Gdirs)` drops channels with no events (3834).
- **Two regimes:**
  - `len(Gdirs) >= max_G` (3837-3899): split G-dirs into `nb_chunk` chunks (multiple of 2*nb_core, >=10 dirs/thread), each unweighted on its own MultiCore thread via `do_combine_events_partial` (subprocess to `bin/internal/madevent_interface.py combine_events_partial`), then the partial LHEs are `AllEvent.add`-ed and a final `AllEvent.unweight` produces `unweighted_events.lhe`, gzipped. Partials cleaned up.
  - else (3900-3927): single-pass — read each `G*/results.dat` (sum xsec/xerru/axsec), `AllEvent.add(events.lhe, ...)`, one `AllEvent.unweight` -> gzip. If `gridpack` or `nevents==0`, just removes `events.lhe` without adding.
- `unweight(... trunc_error=1e-2, event_target=nevents, normalization=event_norm, proc_charac=...)` (3883-3886 / 3922-3925): unweighting target is `run_card['nevents']`, normalization is `run_card['event_norm']`.
- **Low-event warning** (3929-3935): if `nb_event < nevents`, logs "failed to generate enough events" + five suggestions: flip `sde_strategy` to `1 + sde_strategy % 2`, set `hard_survey` to 1 or 2, reduce nevents, check for integrable singularities, regenerate with another gauge (try FD).
- `results.add_detail('nb_event', nb_event)` (3939). Then `correct_bias()` if a real bias_module or `custom_fcts` is set (3941-3944). `to_store.append('event')` (3947).

## do_combine_events_partial (3950-3991)
Worker for the chunked combine. Args `output banner_path cross G1 G2 ...`.
- `preprocess_only=True` (called inline before submission, 3867): just sums xsec/xerru/axsec over the chunk and returns `(output, sum_xsec, rms_xerru, sum_axsec)` WITHOUT unweighting.
- Otherwise (the subprocess): computes a per-chunk `nb_event = max(min(|1.01*nevents*sum_axsec/cross|, nevents), 10)` (3987) — proportional event target for the chunk, floor 10 — then unweights the chunk's events.lhe to `output`.

## do_combine_iteration (3744-3764)
Not-in-help debug command: `combine_iteration Pdir Gdir S|R step`. Sets run name "tmp", `configure_directory(html_opening=False)`, then for `S` builds a `gensym` (survey opts) and `R` a `gen_ximprove_share` and calls its `combine_iteration(Pdir, Gdir, step)` (gen_ximprove internals are numerical/phase-space slice). Used to re-combine a single iteration of one channel by hand.

## do_store_events (4059-4160)
Archives parton-level results into `Events/<run>/` and cleans G-dirs.
- `check_combine_events`; `update_status('Storing parton level results', level='parton')`. Makes `Events/<run>/` and `HTML/<run>/`.
- If `results.current['nb_event']==0` and not gridpack: warns "No event detected. No cleaning performed!" and points at `cd Subprocesses; ../bin/internal/combine_events` to recover (4084-4087). Otherwise per G-dir:
  - removes `events.lhe` (4092-4093);
  - `log.txt` handling driven by `run_card['keep_log']`: keep/move to `<run>_log.txt` unless "none" (delete) or "minimal" (leave in place but not renamed) (4107-4117);
  - removes `ftn25` "to ensure reproducible runs" (4131-4132).
- `gen_card_html()` updates index.html (4135).
- Moves/gzips `Events/<run>/{events.lhe,unweighted_events.lhe}` to `.gz` (4143-4152). Note: a stray `events.lhe`/`unweighted_events.lhe` directly in `Events/` (not the run subdir) logs "File ... exists BAAAAD" but is NOT moved (4146-4147).
- `update_status('End Parton', level='parton', makehtml=False)`.

## do_compile (5720-5732)
Bare directory recompile. `ask_run_configuration(mode='parton')`, reloads `run_card`, `configure_directory(html_opening=False)`, then per P-dir compiles `gensym` and `madevent_forhel`. (Has a leftover `misc.sprint(Pdir)` debug print per P-dir, 5729.) Not part of the normal launch sequence — a manual "rebuild the executables" command.

## Cautions
- The per-run banner (`<run>_<tag>_banner.txt`) is written during **combine**, not store; a run that errors after refine but before combine leaves no banner.
- The chunked-combine path (>= ~ulimit_fd-40 channels) unweights in parallel chunks then re-unweights the merged partials — a two-stage unweighting whose per-chunk targets are proportional (floor 10), distinct from the single-pass path's one global unweight.
- `store_events` deletes `ftn25` and (unless keep_log keeps them) per-channel logs; after store, channel-level grids/logs needed for a manual re-combine are gone.
- "No event detected. No cleaning performed!" is the recovery hook: store deliberately skips cleanup on zero events so `bin/internal/combine_events` can be re-run by hand.
