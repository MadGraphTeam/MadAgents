---
description: The run must proceed with nobody at the prompt. A script, a forced launch, a gridpack, a seeded reproducible run.
---

# Scripted non-interactive execution — fan-out

A `.mg5` script (`mg5_aMC my_script.mg5`) drives the same pipeline as the REPL but with every dialogue pre-answered. Questions about it fan across the stage owners plus the config/seed slices. Route by the sub-question; the traps below are the load-bearing part — each points at the owning consultant's page, which carries the mechanism.

## Owner map (route by sub-question)
- **Script structure / how the file is read / comment handling** → `ma-interface-consultant`. Real reader is `import_command_file`; `CmdFile` is dead Py2 code (do not cite it as the reader).
- **`launch`/`launch -f`/`--force`, survey→refine flow, output-dir layout (`run_01`, `run_02`, …), banner, gridpack create/restart** → `ma-launch-consultant` (core owner).
- **ControlSwitch launch dialogue (shower/detector/madspin switches), pre-edited card auto-detect** → `ma-launch-consultant` (menu) + `ma-interface-consultant` (ControlSwitch mechanism).
- **`run_mode` / `nb_core` / cluster backend** → `ma-interface-consultant` (these are `mg5_configuration.txt` keys — see footgun 1).
- **Reproducibility / `iseed` / `randinit` / gridpack seed** → `ma-mc-integration-consultant`.
- **NLO scripted run, NLO launch flags, NLO "gridpack"** → `ma-amcatnlo-consultant` (see footgun 6).
- **run_card values referenced in the script (defaults, `lhaid`, cut names)** → `ma-scales-pdf-consultant` (scales/PDF/`lhaid`) + `ma-kinematic-cuts-consultant` (cuts); pin LO-vs-NLO class first (`runcard-lo-nlo-value-divergence.md`).
- **`compute_widths` in a script** → `ma-madwidth-consultant` (see footgun 4).
- **`decay` line inside the launch block (MadSpin)** → `ma-madspin-interface-consultant`.
- **`import model` auto-upgrade message on an NLO bracket** → `ma-nlo-model-consultant` (sm→loop_sm).

## Footguns (verified this axis; mechanism lives in the cited consultant page)
1. **`run_mode` / `nb_core` are NOT run_card parameters.** They are `mg5_configuration.txt` keys (or `set run_mode`/`set nb_core` at the interface). Writing them into a run_card does nothing. → `ma-interface-consultant` config-system page.
2. **Gridpack `cd madevent; ./run.sh` is WRONG.** `make_gridpack` packs `run.sh` at the archive ROOT beside `madevent/` (`Template/LO/bin/internal/make_gridpack:12` `tar -cf gridpack.tar madevent run.sh`). Correct invocation is `./run.sh <nevents> <seed>` from the extraction root. → `ma-launch-consultant` gridpack page.
3. **A fixed `iseed` is reproducible only per single run.** MG auto-resets `iseed` to 0 in the run_card after a run, so a re-launch from the same dir does NOT repeat. The gridpack `run.sh <nevents> <seed>` path is the clean reproducible entry. → `ma-mc-integration-consultant`.
4. **`compute_widths` writes/overwrites the param_card but prints NO widths+BR table to screen.** Do not expect a table in script output; read the card. → `ma-madwidth-consultant`.
5. **An unknown `lhaid` fails silently** — `get_pdf_id` falls back rather than erroring, so a typo'd LHAPDF id silently changes the PDF. → `ma-scales-pdf-consultant`.
6. **NLO has no `gridpack=True`.** The LO gridpack (a self-contained event-gen archive) has no NLO analogue; NLO reproducible/batch generation is a manual MINT-grid workflow (grid-setup phase then event phase). → `ma-amcatnlo-consultant`.

## Compute routing
Any scripted run that is high-statistics, NLO, or a parameter sweep is compute-heavy → the dispatch must direct the worker to submit via the cluster (per `cluster-submission.md`), not run on the launch node. A gridpack build + high-stat generation especially.
