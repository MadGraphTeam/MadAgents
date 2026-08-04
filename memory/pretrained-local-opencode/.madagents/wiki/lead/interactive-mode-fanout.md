---
description: What a command at the mg5 prompt does, or how the REPL/launch dialogue behaves. The surface, not the physics.
---

# Interactive command-surface fan-out

A question about *what an interactive `MG5_aMC>` command does / how the REPL dialogue behaves* is not one slice — the command surface fans across six. Route each command to its owner; do not answer the surface from the canonical mental model (the canonical interactive-mode picture is stale in several concrete places — see traps).

## Owner map (per command)

- **ControlSwitch toggle mechanism, `set`, `help`, `history`, `display` dispatch, `exit`/`quit`/EOF, `.mg5` script-mode parsing** → `ma-interface-consultant` (`extended_cmd.py`: Cmd/BasicCmd/ControlSwitch/CmdFile; `master_interface.py` prompt string). Owns *how* a switch toggles, *how* `set`/`display`/`help` dispatch, script keyword-vs-number resolution.
- **The LO `launch` switch set + the card-editing menu + `open` + run numbering** → `ma-launch-consultant` (`madevent_interface.py` `AskRun`; `common_run_interface.py` `do_open`/`ask_edit_cards`/`find_available_run_name`). Owns *which* switches/cards the LO menu shows and their option strings.
- **The NLO `launch` dialogue** → `ma-amcatnlo-consultant` (`amcatnlo_run_interface.py` `AskRunNLO`). A NLO output launches a *different ControlSwitch class* than LO (see trap 1).
- **`install <tool>`** → `ma-installation-consultant` (`madgraph_interface.py` `_install_opts`/`_advanced_install_opts`, gate `:1358`).
- **`compute_widths <particles>`** → `ma-madwidth-consultant` (`do_compute_widths` `:9801`). (Note the *different* command `calculate_decay_widths` is madevent-REPL-only.)
- **`display`/`check` sub-arguments, `generate`/`output` steps** → `ma-process-syntax-consultant` (`do_display` `:3566`, `do_check` `:4065`).

## Anticipated traps (pointer, not mechanism)

1. **The `launch` dialogue is a different class for LO vs NLO.** LO output → `AskRun` = **5** switches `shower / detector / analysis / madspin / reweight`; NLO output → `AskRunNLO` = **6** switches (adds `order` + `fixed_order`, drops the standalone `detector`, MA5 becomes `madanalysis`). Option strings also differ: at LO `shower = Pythia6|Pythia8|OFF` (**HERWIG7 is NLO-only**, `HERWIG7→HERWIGPP`), `detector = PGS|Delphes|OFF`, `analysis = ExRoot|MadAnalysis4|MadAnalysis5|Rivet|OFF`, `madspin = OFF|ON|onshell|full`. All options are install-gated (`Not Avail.` when the module is absent). `fixed_order=ON` forbids a shower (NLO-only coupling; no LO analogue). Route LO switch set → launch (`../consultants/ma-launch-consultant/launch-menu-switcher.md`), NLO → amcatnlo (`../consultants/ma-amcatnlo-consultant/askrunnlo-dialog-and-showers.md`); the toggle mechanism + consistency-flip → interface + `runtime-and-menu-seams.md`.
2. **`display` subjects are prompt-specific.** `display diagrams` / `display particles` are in the *madgraph*-prompt `_display_opts` (14 subjects) but NOT the *madevent*-prompt list — valid at `MG5_aMC>`, `InvalidCmd` at the run-dir prompt. Do not assume a uniform `display` surface across prompts. → interface `meta-commands-introspection.md`.
3. **`display diagrams` is not a built-in viewer.** It *writes* one `diagrams_<shell>.eps` per subprocess to a temp dir (`draw()` `:3999`), then shells out to the configured `eps_viewer` via `open`; with no viewer configured it prints "no program configured" and the files still exist. No process dir required. → process-syntax `display-command.md`.
4. **`compute_widths` writes, it does not display.** `compute_widths t w+ w- z h` computes total+partial widths and **overwrites the DECAY blocks of a param_card** — by default the *model directory's* shipped `param_card.dat` (`:1862`), printing only status lines, no width table. Point it at `--path=<card>` / redirect with `--output=<card>` to avoid clobbering the model default. Needs only `import model` first (no output dir / generate / user card). → madwidth `compute-widths-flow.md`.
5. **`install` tokens are case-sensitive.** The gate is a plain `in` with no `.lower()` (`:1358`), so `Delphes`/`MadAnalysis5`/`pythia8`/`lhapdf6` must match case exactly; `delphes`, `Pythia8`, `madanalysis5`, and bare `lhapdf` (only `lhapdf6`/`lhapdf5` exist) all raise `InvalidCmd`. → installation `install-tree-and-target-dirs.md`.

## Return-interpretation hint

The stale canonical picture (4 numeric switches `shower/detector/madspin/analysis`, shower `HERWIG7|PYTHIA8`, `display diagrams` "opens a viewer", `compute_widths` "displays") is wrong on switch count/order, LO option strings, viewer behaviour, and the write-vs-display half. When a return matches source over that picture, the return is right — the corrected facts are cited above with `file:line` in the owning subtrees.

See also: `runtime-and-menu-seams.md` (ControlSwitch consistency-flip, `-O`/`__debug__`, downstream `--no_default` skip), `pipeline-stage-map.md` (stage→slice), `downstream-card-existence-gate.md` (which switch → which downstream card).
