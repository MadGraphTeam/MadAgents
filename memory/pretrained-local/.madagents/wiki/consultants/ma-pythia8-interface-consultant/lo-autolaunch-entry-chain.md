---
description: LO entry chain into the PY8 shower — launch/generate_events -> shower --no_default -> do_pythia8; launcher-class roles (MELauncher delegates to generate_events; Pythia8Launcher is the standalone main_*.cc compiler, NOT the handoff).
---

# LO auto-launch entry chain into the PY8 shower

How does control actually *reach* `do_pythia8` on a normal `launch` / `generate_events`? The launcher classes in `launch_ext_program.py` are a common misread — the real LO handoff is buried inside `generate_events`, not in a launcher.

## The chain (verified v3.7.1)
1. `launch` => `MELauncher.launch_program` (`launch_ext_program.py:614`). It does **not** itself run MadSpin/Pythia/Delphes. It builds a `MadEventCmd` (or `MadEventCmdShell`, or the `launch_plugin` `MEINTERFACE` if present, `:640-652`) and issues `generate_events <name>` with flags: `-M` if madspin, `-R` if reweight, `--cluster`/`--nb_core=` for mode, `-f` if force (`:670-700`). Cross-section is then read from `SubProcesses/results.dat` (`:706-712`).
2. `do_generate_events` (`madevent_interface.py:2383`) runs the parton-level pipeline, then the downstream-tool chain. The shower step is `self.exec_cmd('shower --no_default', postcmd=False, printcmd=False)` (`:2668`), with the comment "shower launches pgs/delphes if needed". Note it ALWAYS passes `--no_default` here. (Surrounding chain: madanalysis5_parton `:2666` -> shower `:2668` -> madanalysis5_hadron `:2669` -> rivet `:2670`.)
3. `do_shower --no_default` (`:4203`, `:4209-4213`): runs **all** of `_interfaced_showers = ['pythia','pythia8']` (`:2044`); each `exec_cmd`'d (`:4222-4224`). Each self-checks its own card. The `shower_priority` (pythia8>pythia) sort fires **only on the bare `shower` command with no `--no_default` and no explicit shower** (the `else` branch `:4214-4220`) — which is essentially never the auto-launch path. So in the normal launch flow priority is moot; the card-existence gate decides.
4. `do_pythia8 --no_default` (`:4579`): top-of-function gate `:4592-4594` — if `Cards/pythia8_card.dat` absent => **return, silent no-op**. Present => proceeds. (See do-pythia8-handoff.md for everything after this point.) `do_pythia` (Pythia6, `:5320`) has the analogous self-check against `pythia_card.dat`.

So: on a normal launch, PY8 runs iff `pythia8_card.dat` exists in Cards/; Pythia6 runs iff `pythia_card.dat` exists. Both can run (chain runs all interfaced showers); priority only matters for a manual bare `shower`.

## Launcher-class roles (the common misread)
`launch_ext_program.py` launcher classes — what each actually is:
- `MELauncher` (`:584`): the `launch` entry for a MadEvent dir. Delegates to `generate_events` (above). The downstream MadSpin/Pythia/Delphes orchestration is inside `generate_events`/the shower chain, NOT spelled out in `launch_program`.
- `aMCatNLOLauncher` (`:487`): NLO+PS launch entry; routes through the aMC@NLO interface (shower via run_mcatnlo — out of slice, see shower-card-and-routing.md).
- `Pythia8Launcher` (`:718`): **NOT the LO handoff.** It is the standalone Pythia8 *example* runner: `__init__` cd's into `examples/` (`:724`); `prepare_run` globs `main_*_*.cc` files, asks the user which `main` to run, derives a run-name `.log`, and locates the matching `Processes_<model>`/`param_card_<model>.dat` (`:728-787`); `launch_program` runs `make` on the model dir + the per-main Makefile, runs the compiled binary, and pages the cross-section from the log (`:789-815`). This is the C++ standalone-output path (mg5 `output pythia8`), unrelated to MadEvent's `do_pythia8`.

## Caution
The card description "MELauncher … runs MadSpin / Pythia / Delphes sequentially in launch_program" is imprecise — `launch_program` issues a single `generate_events` command; the sequential downstream chain lives in `do_generate_events`. When tracing "how does launch reach PY8", follow `generate_events`, not the launcher body.
