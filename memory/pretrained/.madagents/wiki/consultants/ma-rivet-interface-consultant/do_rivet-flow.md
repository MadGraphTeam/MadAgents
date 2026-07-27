---
description: do_rivet control flow in common_run_interface.py — arg parsing, card resolution/recognition/editor-isolation, analysis list, env setup, HepMC fetch, run_rivet.sh emission, run-now vs postprocess decision, run-sequence wiring (launcher not involved).
---

# do_rivet flow (MG -> Rivet handoff)

`do_rivet(self, line, postprocess=False)` at `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py:2922`.
`postprocess=True` => assemble config + wrapper but do NOT execute; return `[rivet_config, postprocess_RIVET, postprocess_CONTUR]` (3080-3082).

## Argument / card resolution
- `--no_default` => `no_default=True`, suppresses the interactive card edit (2927-2931).
- No run name + no `self.run_name` => use `self.results.lastrun`, else InvalidCmd (2933-2938).
- Banner recovered with level `'pythia'` (comment: must NOT be `'pythia8'`) (2949-2951); `self.run_card = self.banner.get('run_card')` (2953).
- Interactive edit gate: only when `not no_default and '-f' not in line` -> `keep_cards(['rivet_card.dat'])` + `ask_edit_cards(['rivet_card.dat'],'fixed',plot=False)` (2955-2958).
- Missing `Cards/rivet_card.dat`: if `no_default` -> `return None` (silent skip, 2963-2965); else copy `rivet_card_default.dat` -> `rivet_card.dat`, log "No rivet_card found. Take the default one." (2967-2969).
- `rivet_config = banner_mod.RivetCard(Cards/rivet_card.dat)` (2973). When `not no_default`, forces `run_rivet_later=False` (2974-2975) so a manual `rivet` command runs immediately rather than deferring.

## Analysis list -> run_analysis string
- `analysis_list = rivet_config.getAnalysisList(runcard=self.run_card)` (2978). See `analysis-selection.md`.
- Each `MC_*` analysis gets `:ENERGY={rivet_sqrts}` appended (2982-2983).
- Joined comma-separated into `run_analysis` (2984-2985).
- If `"$CONTUR_"` in run_analysis: requires `contur_path/conturenv.sh` else Exception (2986-2988); sources conturenv.sh to get `$CONTUR_USER_DIR`, builds `set_env` sourcing `<contur_user_dir>/analysis-list`, and force-strips `ATLAS_2016_I1469071` via sed (segfault/neutrino-truth concern) (2990-3000).

## Weight name (merging)
- `py8_card = PY8Card(Cards/pythia8_card.dat)` (3003). If `weight_name=="default"`, `setWeightName(runcard, py8card)` (3004-3005). See analysis-selection.md.

## Environment (set_env) — paths from self.options
PATH/LD_LIBRARY_PATH/PYTHONPATH built from `rivet_path`, `yoda_path`, `hepmc_path`, and `fastjet --prefix` (3011-3027). fastjet prefix obtained by running `self.options['fastjet'] --prefix` (3014-3015).

## HepMC fetch (3030-3050)
- Reads `py8_card["HEPMCoutput:file"]`.
- `@`-form splits path; abs => `pjoin(path, run_name)`, rel => `pjoin(me_dir,'Events',path,run_name)` (3033-3038); else `pjoin(me_dir,'Events',run_name)` (3039-3040).
- `"hepmc" in py8_output`: `.gz` => `<run_tag>_pythia8_events.hepmc.gz`, else `.hepmc` (3042-3046).
- `"fifo"` => `PY8.hepmc.fifo` (3047-3048); else MadGraph5Error "HEPMCoutput:file format unknown" (3050).

## Wrapper emission (3052-3069)
- `yoda_file = Events/<run_name>/rivet_result.yoda` (3055).
- `run_rivet = <rivet_path>/bin/rivet --skip-weights -a <run_analysis> -o <yoda_file> <hepmc_file> <rivet_add>` (3056).
- Wrapper `Events/<run_name>/run_rivet.sh`: shebang+set_env, then `sys.executable <run_rivet> &> rivet.log` (3058-3060).
- If `draw_rivet_plots`: appends `rivet-mkhtml` call -> `rivet-plots/` (3061-3064).
- fifo output => wrapper appends `rm <hepmc_file>` (3067-3068).

## Run-now vs postprocess (3071-3093)
- `py8_output` containing "remove" or "fifo" forces `run_rivet_later=False` (3071-3072) — cannot postprocess hepmcremove/fifo.
- `postprocess_RIVET = run_rivet_later`; `postprocess_CONTUR = run_contur` (3074-3075).
- chmod +x run_rivet.sh (3077).
- `postprocess=True` => return triple, no exec (3080-3082).
- else if `run_rivet_later` => log "Skipping Rivet for now, passing it to postprocessor", append run_name to `self.postprocessing_dirs`, return (3084-3088).
- else => `misc.call(['Events/<run_name>/run_rivet.sh'], cwd=me_dir)` runs Rivet now (3090-3091).

## Run-sequence wiring
- In `run_generate_events`, after shower/MA5: `self.exec_cmd('rivet --no_default', postcmd=False, printcmd=False)` at madevent_interface.py:2670 — runs AFTER `shower` (Pythia8) and `madanalysis5_hadron`. The `--no_default` means: no card -> silent skip.
- Full per-point post-shower order (madevent_interface.py:2666-2671): `madanalysis5_parton --no_default` -> `shower --no_default` (Pythia8 launches pgs/delphes if needed) -> `madanalysis5_hadron --no_default` -> `rivet --no_default` -> `store_result`. So Rivet is the LAST hadron-level analysis step in each point.
- `postprocessing()` is a SEPARATE call after `run_generate_events()` returns (madevent_interface.py:2406). In scan mode the per-point `rivet --no_default` calls only EMIT wrappers (run_rivet_later defaults True); the actual deferred Rivet/Contur execution happens in `postprocessing()` once all points are showered. See postprocess-and-contur.md.

## do_rivet arg parsing (2925-2953)
- `--no_default` stripped from args, sets `no_default=True` (2927-2931).
- No args + no `self.run_name` -> use `self.results.lastrun` else InvalidCmd (2933-2938).
- If `self` has no `run_card` attr yet: `set_run_name(name, level='rivet', reload_card=True)` + `configure_directory(html_opening=False)` (2940-2946) — the standalone `rivet RUN` entry path.
- `help_rivet` (madevent_interface.py:339-344): `rivet [RUN] [--run_options]`; options `-f`, `--tag=`, `--no_default`. `complete_rivet = complete_pgs` (madevent_interface.py:2027).

## Card recognition + editor isolation (card-type wiring)
- `detect_card_type` (common_run_interface.py:1168-1275): rivet_card.dat has NO banner/MGVersion header; it is identified solely by the `run_rivet_later` token (search list 1226, branch 1274-1275). A rivet card lacking that key would be mis-detected as 'unknown'.
- `keep_cards(['rivet_card.dat'], ignore=['*'])` (called at 2957; def 3997-4019): isolates the rivet card for the interactive edit — moves every OTHER check_card to dot-hidden `.<card>.dat`, and ensures rivet_card.dat is present (restores from `.rivet_card.dat`, else copies `rivet_card_default.dat`). rivet_card.dat is in the `check_card`/`keep_cards` set (4005) and the `keep_cards` need-card set passed by do_rivet.
- `init_rivet(cards)` (5338-5357): gates on `get_path('rivet', cards)` (def 5109-5142) — the Rivet menu/shortcut only initialises when rivet_card.dat is in the card set. Sets `has_rivet`, registers the `fast_rivet` special shortcut, builds `rivet_card`/`rivet_card_default`/`rivet_vars`. Triggered by `'rivet'` in `to_init_card` (4956). See postprocess-and-contur.md for fast_rivet contents.

## launch_ext_program.py — NOT involved (negative fact)
- `grep -ci rivet|contur|yoda madgraph/interface/launch_ext_program.py` == 0. Despite the consultant card listing it as an area, the launcher has NO Rivet path. The entire MG->Rivet handoff lives in `common_run_interface.do_rivet` + `madevent_interface` (postprocessing + run-sequence wiring). Don't look in launch_ext_program.py for Rivet behaviour.
