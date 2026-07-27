---
description: __debug__ is False by default in a release mg5_aMC run (auto -O relaunch); a single --debug switch flips install-machinery behavior at 4+ sites AND bumps log level INFO->DEBUG, un-hiding logger.debug/misc.sprint install diagnostics (v3.7.1).
---

# `__debug__` / `-O` as a release-default install switch

## The principle
A default `mg5_aMC` launch re-launches itself under `python -O`, so `__debug__` is **False** at MG5 runtime by default. `--debug` suppresses the relaunch, leaving `__debug__` True. This one flag is a global switch: every `if __debug__:` / `if not __debug__:` gate, `assert`, and `misc.sprint` in the install machinery takes its *release* branch by default, and `--debug` flips all of them at once. When an install/plugin question's answer depends on a `__debug__`-gated branch, the default-run answer is the `False` branch — not the source's apparent `if __debug__:` body.

## The relaunch (cause)
`$MADGRAPH_INSTALL/bin/mg5_aMC:75-78`:
```
if __debug__ and not options.debug and \
    (not os.path.exists(os.path.join(root_path, 'bin','create_release.py')) or options.web):
        command = '%s -O -W ignore::DeprecationWarning -W ignore::SyntaxWarning %s' % (sys.executable, ' '.join(sys.argv))
        ... subprocess.Popen(command, shell=True) ... sys.exit(return_code)
```
- PROBE-CONFIRMED (process table during `mg5_aMC `<script>.mg5``, this image): default run spawns child `python3 -O -W ignore::DeprecationWarning -W ignore::SyntaxWarning .../bin/mg5_aMC ...` → `__debug__` False at runtime.
- `-O` → `__debug__` False / `sys.flags.optimize=1` (probe-confirmed: `python3 -O` vs plain `python3`).
- Precondition: relaunch fires when `create_release.py` is ABSENT (packaged release) OR `--web`. In this image `bin/create_release.py` does not exist (probe-confirmed), so the default relaunch is active. If `create_release.py` were present and `--web` not passed, `__debug__` stays True (the dev/source-checkout case).

## Install-machinery sites the switch governs (each source-walked)
1. **Plugin out-of-bounds keep/disable** — `$MADGRAPH_INSTALL/madgraph/various/misc.py:2160-2166`: out-of-version-bounds plugin → under `__debug__` kept active (error only); else (default release) **disabled**. See `plugin-install-and-version-compat.md`.
2. **Plugin launcher flag** — `madgraph_interface.py:6837`: generated `bin/<name>.py` uses `-tt` under `__debug__`, else `-O -W ignore::DeprecationWarning` (default release). See `plugin-install-and-version-compat.md`.
3. **MadAnalysis5 install failure auto-recovery** — `madgraph_interface.py:6336` (`if not __debug__:`): on a failed default MA5 install, only the **release** run auto-reinstalls with `--no_MA5_further_install --no_root_in_MA5 --force`; the warning text literally tells the user to start with `./bin/mg5_aMC --debug` to PREVENT the re-attempt. So under `--debug` a failed MA5 install is NOT auto-recovered. (Not enumerated elsewhere.)
4. **`misc.sprint` install diagnostics silenced** — `misc.py:1563-1566`: `sprint()` returns immediately when `not __debug__`. Every `misc.sprint(...)` in the install path is therefore SILENT in a default release run — including the `:6680` `misc.sprint('try other mirror', ...)` mirror-fallback trace and the source-server corrupt-line trace. So "you won't see the 'try other mirror' message by default" is a `__debug__` consequence, not a bug. (Not enumerated elsewhere.)

## `--debug` ALSO bumps the log level INFO→DEBUG (the visibility half of the switch)
`--debug` does TWO things at once, and the second one is what un-hides every `logger.debug` install diagnostic:
1. Suppresses the `-O` relaunch → `__debug__` stays True (the branch-flipping half, sites 1-4 above).
2. `bin/mg5_aMC:143-144`: `if __debug__ and options.logging == 'INFO': options.logging = 'DEBUG'`. So a default-`INFO` launch under `--debug` runs at DEBUG log level.
PROBE-CONFIRMED (this image): default `mg5_aMC -f` prints NO "Running MG5 in debug mode" banner and NO `DEBUG:` lines; `mg5_aMC --debug -f` prints the banner AND `DEBUG:` lines (e.g. `DEBUG: set configuration option lhapdf ... [madgraph_interface.py at line 7408]`).
CONSEQUENCE — a UNIFIED "you won't see it by default" rule covering THREE silent-diagnostic install sites that otherwise look like three unrelated mechanisms:
- `misc.sprint(...)` (e.g. `:6679` mirror-fallback trace) — silenced because `not __debug__` returns early (`misc.py:1563-1566`). Un-hidden by `--debug` via half (1).
- `logger.debug(...)` install diagnostics — the env-var advisory at `advanced_install :6440-6480` ("add these to LD_LIBRARY_PATH/PATH", see advanced-install-writeback.md) and the "no model with that name found online" trace (`import_ufo.py`, see online-model-import-trigger.md) — invisible at default INFO. Un-hidden by `--debug` via half (2).
So BOTH the `misc.sprint` traces and the `logger.debug` advisories share ONE switch (`--debug`), even though their gates differ (`__debug__` early-return vs log-level threshold). When advising "you won't see X," the fix is the same: re-run with `--debug`. EXCEPTION — the per-tool sentinel-file validation reset to None (`set_configuration`, mg5-configuration-read-resolve.md) emits NO log call at any level, so `--debug` does NOT surface it; that one is genuinely silent.

## What this catches beyond the instances
The plugin page covers sites 1-2. The principle additionally catches sites 3-4 and any future `__debug__`-gated install branch: when reasoning about a default install/update run, take the `False` branch of every `__debug__` gate, and remember `--debug` flips them together. Conversely, advice that assumes a visible `misc.sprint` trace or an "active despite out-of-bounds" plugin is implicitly assuming `--debug`. AND (extended above) the same `--debug` un-hides `logger.debug` install advisories — so "I never saw the env-var/mirror/no-model-online message" is the default-INFO/`-O` consequence, resolved by `--debug`, NOT a missing message.

## Boundary
- Covers `__debug__`-gated **install-machinery** sites only. Non-install `__debug__` uses (logging level at `bin/mg5_aMC:137,143`; timing diagnostics; `misc.py` traceback verbosity) are other slices' concern — the relaunch fact is shared, but the consequence is theirs to own.
- The plugin version-bound *enforcement* and *launcher* mechanics still live on `plugin-install-and-version-compat.md`; this page owns only the cross-cutting `__debug__`/-O switch and its install-wide reach.
