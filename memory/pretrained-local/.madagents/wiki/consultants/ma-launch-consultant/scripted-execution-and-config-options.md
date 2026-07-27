---
description: Non-interactive (.mg5 script) launch mechanics — run_mode/nb_core config-vs-dialog seam, card-path auto-detect in the launch dialog, EOF/done terminators, banner filename, gridpack run.sh usage.
---

# Scripted execution and run-config options

Cites `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py` (CR), `madgraph/interface/madevent_interface.py` (ME), Template scripts (v3.7.1).

## run_mode / nb_core — config option, set BEFORE the launch dialog
- Defaults (CR options dict): `run_mode` at 686, `nb_core` at 691 (read the literals fresh; `nb_core` default is `None` = auto/all-cores). The `# run_mode = …` / `# nb_core = …` lines in `input/mg5_configuration.txt` (123, 164) are commented — the operative default is the code default (686/691), which equals the commented example.
- Meaning: `run_mode` 0=single machine / 1=cluster / 2=multicore (config comment 121-122).
- **These are mg5/shell options, NOT card parameters.** The launch card-editing dialog `AskforEditCard.do_set` (CR 5868) recognizes ONLY: special_shortcut macros, qcut/showerkt, explicit card names (run_card/param_card/pythia8_card/madspin_card/MadLoop_card/…), and card parameters via pname2block. There is **no `run_mode`/`nb_core` branch and no delegation to the mother interface** (grep of 5998-6360 shows only card-name branches). So `set run_mode 2` typed inside the launch block falls through to `logger.warning('invalid set command %s')` (CR 6182 / 6359), emitting "WARNING: invalid set command" (source-read; a cheap probe would confirm the exact emitted line).
- Correct place: set `run_mode`/`nb_core` at the mg5_aMC prompt (or in `mg5_configuration.txt` / via `save options`) BEFORE `launch`. The shell-level `do_set` that DOES handle them is `CommonRunCmd.do_set` (CR 3536; run_mode branch 3571-3575 calls `configure_run_mode`, nb_core 3585-3594). That is the `madevent`/`generate_events` shell `set`, distinct from the in-dialog `AskforEditCard.do_set`.
- `configure_run_mode(mode)` (CR 3656-3690): mode 1 -> cluster (reads `cluster_type`), mode 2 -> multicore. Cluster types (config 128): `[pbs|sge|condor|lsf|ge|slurm|htcaas|htcaas2]` — the commonly-cited `condor/sge/slurm/lsf/pbs` set is a correct but INCOMPLETE subset (omits ge, htcaas, htcaas2).

## Card-path auto-detect inside the launch dialog
`AskforEditCard.default` (CR 7202) handles a line that is not a known command:
- If `os.path.isfile(line)` (7220) or `me_dir/line` exists (7223) -> `copy_file(line)`, then `value='repeat'` (re-prompt).
- `copy_file` (CR 7693): `detect_card_type(path)` inspects file **content** (not filename), then `files.cp(path, self.paths[card_name...])` into the right Cards/ slot and `reload_card`s it. Unknown content -> `'Fail to determine the type of the file. Not copied'` (7713). A recognized **banner** file is split into its component cards via `split_banner` (7719). A URL (http/www/https) is fetched to a tempfile and copied the same way (7226-7240); `.lhco[.gz]` routes to MadWeight inputfile (7699-7708).
- So dropping a pre-edited card path in the launch block auto-routes by content — VERIFIED.

## Dialog terminators / EOF
`AskforEditCard.default` (CR 7216-7217) explicitly excludes `'0'`, `'done'`, and the token `'EOF'` from both the open-file and copy-file branches — they are terminator tokens, not filenames. The question ends on done/0/empty (postcmd). Reaching **EOF in a script** is caught by the cmd base's `do_EOF`/postcmd and terminates the dialog like `done` (so a script that omits `done` does not hang) — the EOF->done routing itself is `extended_cmd.py` (interface slice); the launch dialog only needs to see the terminator. SEAM: EOF/CmdFile mechanics = ma-interface-consultant; the terminator handling in the card dialog is confirmed here.

## Banner filename
Banner is written to `Events/<run_name>/<run_name>_<run_tag>_banner.txt` (CR 2365, 3356, 3424, 4270; banner.py 733). Default tag is `tag_1`, so first run -> `Events/run_01/run_01_tag_1_banner.txt`. (The agent-card's "Runtime artefacts" note `banner_<run_name>_banner.txt` is the WRONG shape — actual is `<run>_<tag>_banner.txt`.) Cross-section is printed to stdout (`print_results_in_shell`) AND stored in the banner. Run naming run_01, run_02, … via `find_available_run_name` (see launch-flow-orchestration page).

## Recompilation skip within a session
Each `bin/mg5_aMC script.mg5` is an independent process starting fresh (interface slice owns process lifecycle). Within one process, a second `launch`/compile to the same proc dir skips rebuild via `do_compile`'s mtime early-out (see treatcards-and-configure-directory page). This is a compile-time optimization, not per-session state that survives across `mg5_aMC` invocations.

## Cautions
- Putting `set run_mode`/`set nb_core` AFTER `launch` (among the card `set` lines) silently no-ops with "invalid set command" — the value the run uses is whatever was set at mg5/config level before launch. Classic scripted-launch footgun.
- Card-path drop relies on content sniffing; a malformed/edited card that no longer matches `detect_card_type` heuristics is silently "Not copied" (only a warning), and the run proceeds with the ORIGINAL card.
