---
description: install command flag surface — what help_install advertises vs complete_install tab-completes vs check_install actually parses; per-tool tarball overrides + --logging auto-injection (v3.7.1).
---

# install command flag surface (advertised vs discoverable vs parsed)

Three independent enumerations of `install` flags exist in `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, and they DISAGREE. Knowing which flags actually do something means reading all three plus the parse path, not just `help install`.

## 1. help_install `:376-394` (the printed help — UNDERSTATES)
`help install` prints ONLY:
- `--force` (overwrite without asking) and `--keep_source` (keep tool sources) — and explicitly only "when installing any of the `_advanced_install_opts`".
- For `update`: `-f` (skip confirmation) and `--timeout=`.
- Syntax line is `install <self._install_opts joined by |>` — so the advanced/HEPTools targets are NOT even listed in the syntax line (only `_install_opts`); `_advanced_install_opts` are named only in the prose paragraph.
NEVER mentioned in help: `--source=`, `--logging=`, the per-tool `--<tool>_tarball=` overrides, MA5's `--no_root_in_MA5`/`--update`/`--with_*`/`--veto_*`. So the help text is a strict subset of what works.

## 2. complete_install `:2951-2980` (tab-completion — richer, still partial)
Tab-completion enumerates, by argument position:
- arg 1 (the target): `_install_opts + _advanced_install_opts`.
- after `update`: `['-f', '--timeout=']`.
- after an `_advanced_install_opts` target: base `['--keep_source','--logging=']`, plus per-tool:
  - `pythia8` → `--pythia8_tarball=`
  - `mg5amc_py8_interface` → `--mg5amc_py8_interface_tarball=`
  - `MadAnalysis5`/`MadAnalysis` → `--no_root_in_MA5`, `--update`, `--madanalysis5_tarball=`, and the cross-product `--with_/--veto_ × {fastjet,delphes,delphesMA5tune}` (6 flags). (`--no_MA5_further_install` is present in source but COMMENTED OUT of the completion list `:2967`.)
  - already-supplied options are filtered out of the suggestions `:2975-2977`.
NOT tab-completed (but still parsed/honored): `--force` (only `--keep_source` is completed, not `--force`), `--source=`.

## 3. check_install `:1325-1361` (the real parse — most permissive)
The actual gate. Option splitting `:1337-1356`:
- For target `update`: `=`-form args → `update_options`; bare args also → `update_options`.
- For any OTHER target: EVERY extra arg (including `--source=`, `--force`, `--keep_source`, `--logging=`, any `--<tool>_tarball=`) goes verbatim into `options_for_HEPToolsInstaller`; then `args` is truncated to `args[:1]`.
So check_install does NOT validate flag NAMES at all — it forwards everything unknown straight to HEPToolInstaller.py (advanced targets) or ignores it (built-in targets). A typo'd flag is silently forwarded, not rejected. Only the TARGET is validated (`:1358-1361`, must be in `_install_opts+hidden_prog+_advanced_install_opts`, with the `startswith('td')` bypass).

## --logging auto-injection `:6645-6646` (advanced path only)
For an `_advanced_install_opts` target, after assembling `add_options`, if no `--logging=` was supplied, do_install appends `--logging=%d % logger.level`. So HEPToolInstaller.py always receives an explicit logging level matching the live MG5 logger (default INFO=20). A user who never types `--logging=` still gets one passed through. (Built-in targets never reach this line — it's inside the `:6635` advanced branch.)

## Practical consequences
- `help install` is a strict UNDERSTATEMENT: `--source=`, `--logging=`, and per-tool tarball overrides all work but are unadvertised. Recommend a user read `complete_install` (tab-complete) for tarball overrides and this page for `--source`/`--force`.
- `--force` works on advanced targets but is neither in help's advanced list emphasis nor tab-completed — only `--keep_source` is completed. Don't infer "not completed ⇒ not supported."
- Unknown/typo flags are NOT rejected at parse time (`check_install` forwards verbatim) — failure, if any, surfaces inside HEPToolInstaller.py, not at the MG5 prompt.
- The `--<tool>_tarball=` overrides (pythia8/mg5amc_py8_interface/madanalysis5) are the offline/pinned-version lever for advanced tools, parallel to the `paths=`/`--ninja_tarball=` lever the vendor offline path uses for built-in reduction libs (see `vendor-and-offline-install.md`).

## Boundary / gaps
- What HEPToolInstaller.py does with a given `--<tool>_tarball=` or an unknown flag is in that externally-refreshed installer script (see `advanced-install-writeback.md` exit-code contract + `install-static-vs-runtime-boundary.md`), not in MG5 source.
- This page owns the FLAG SURFACE (advertised/completed/parsed). The option-BUCKET routing (which bucket an arg lands in) is also noted on `do-install-flow.md` step 1; this page is the discoverability/disagreement angle, that page is the flow.
