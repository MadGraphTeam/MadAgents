---
description: User-facing run/config management commands distinct from the launch flow — do_remove (level-filtered run deletion, banner-protected), do_save (persist changed options to me5_configuration), do_edit_cards (open card editor), do_print_results (reprint a stored run's xsec).
---

# Run / config management commands

The shell commands a user runs to manage runs and config OUTSIDE the survey->refine->combine launch flow. Cites `$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` (ME) and `common_run_interface.py` (CR), v3.7.1.

## do_remove (ME 5500-5648) — level-filtered run deletion
`remove <run|all> [tag] [parton|pythia|pgs|delphes|channel|banner|all] [--tag=]`. `check_remove` parses run/tag/mode.
- **`remove all`** (5509-5523): iterates every `Events/*/*_banner.txt`, recursively `remove`s each run. BUT if a literal run named `all` exists it refuses ("A run with name all exists. So we will not supress all processes."). A missing/cleared run is caught and skipped.
- **Banner is PROTECTED by default** (5542): the delete list excludes any file with `banner` in its name. A plain `remove <run>` deletes parton/pythia/etc. output but KEEPS the banner, then logs "The banner is not removed. In order to remove it run: remove <run> all banner" (5642-5644). The banner is only deletable in `banner` mode.
- **Level filtering** (5561-5573): `all` deletes everything; otherwise files are filtered so only the named levels (pythia/pgs/delphes/parton) are removed. Removing parton when the tag matches the first result also pulls in `events.lhe.gz`/`unweighted_events.lhe.gz`/`plots_parton.html` and warns "Be carefull that partonic information are on the point to be removed." (5543-5560).
- **Channel/SubProcess cleanup** (5597-5617): `channel` or `all` mode also globs and deletes `SubProcesses/<run>*` (and one/two levels deeper) — the per-channel job files.
- **banner mode** (5619-5641): with a tag, removes `<run>_<tag>_banner.txt` and `results.delete_run(run, tag)`. Without a tag, REFUSES if any non-banner output still exists (`MadGraph5Error: Some output still exists for this run. Please remove those output first. Do for example: remove <run> all banner`); only when the dir is banner-only does it `shutil.rmtree` the whole run dir + `results.delete_run(run)`.
- Confirms via `self.ask` (default 'y') unless `self.force`; `os.remove` else `shutil.rmtree` fallback per entry. Keeps the HTML index in sync via `results.delete_run`/`results.clean` (5647) + `update_status`.

## do_save (ME 2276-2315) — persist changed options
`save options [filepath] [--auto] [--all]`. NOT in help. Writes only options whose live value differs from the configuration default:
- always: `options_configuration` (the mg5_configuration-level keys).
- unless `--auto`: also `options_madevent` (ME-specific keys).
- `--all`: also `options_madgraph` (MG5 core keys); WITHOUT `--all` (and not `--auto`), a changed madgraph option is NOT written and instead logs "The option %s is modified [...] but will not be written... run 'save options --all'".
- Default target: `Cards/me5_configuration.txt` (per-process config), or an explicit filepath arg. So `save options` persists the current session's deltas into the process's local config; it does NOT touch the global `input/mg5_configuration.txt` unless that path is named.

## do_edit_cards (ME 2320-2327) — open the card editor standalone
Thin wrapper: `check_generate_events(args)` -> mode, then `ask_run_configuration(mode)` and returns. So `edit_cards` reuses the SAME launch-menu switcher (`ask_run_configuration`, launch-menu-switcher page) that `generate_events` uses — including the card-presence-driven default selection and `keep_cards` hiding — but stops before any integration. Useful to pre-stage cards / re-run the menu without launching.

## do_print_results (CR 2532-2579) — reprint a stored run's results
`print_results [run] [tag] [--path= --mode=w|a --format=full]`. Reads from `self.results` (the in-memory/HTML results db), dispatches to `print_results_in_shell` (no path) or `print_results_in_file` (path) — both on the monitor-status page. With NO run arg, dumps EVERY run/tag (mode flips 'w'->'a' after the first). `tag` may be a 1-based digit index or a tag string; `InvalidCmd` if run_name unknown. This is the after-the-fact "show me run X's cross-section/width again" command; it recomputes nothing, just reformats stored OneTagResults.

## do_banner_run — see launch-entrypoints-and-html page
`banner_run <banner>` restores cards from a saved banner (deleting any current downstream cards first) and re-enters `generate_events`. Documented on launch-entrypoints-and-html.

## Cautions
- `remove <run>` does NOT delete the banner; users expecting a clean wipe must use `remove <run> all banner`. And `remove all` silently no-ops if a run is literally named "all".
- `remove <run> banner` (no tag) hard-errors if other output remains — banner removal is gated behind removing everything else first (prevents orphaning the only metadata for live output).
- `save options` writes to the PROCESS-LOCAL `Cards/me5_configuration.txt` by default, not the global config; and a changed core-madgraph option is silently dropped unless `--all`.
- `edit_cards` runs the full launch menu (consistency rules, card hiding, auto-selection by card presence all apply) — it is not a passive editor; deselecting a tool here hides its card just as in a real launch.
