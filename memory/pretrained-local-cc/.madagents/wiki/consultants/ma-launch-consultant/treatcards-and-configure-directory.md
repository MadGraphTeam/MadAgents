---
description: treatcards (.inc generation) and configure_directory — run.inc/param_card.inc/MG5_param.dat writing, LO vs shared common_run treatcards split, ninitial==1 beam zeroing, lhapdf/bias compile setup.
---

# treatcards and configure_directory

## Two do_treatcards implementations
- **Shared** `common_run_interface.py:do_treatcards(self, line, amcatnlo=False)` (923): inherited base. Writes run.inc via `run_card.write_include_file(opt['output_dir'])` (960); MadLoopParams (962-968); param_card.inc from the ufomodel default (970-993). The `amcatnlo` flag adds lhapdf set-name conversion (950-959) and forces final-state widths to zero unless `--keepwidth` (995+). This is the NLO-flavored path.
- **LO override** `madevent_interface.py:do_treatcards(self, line, mode=None, opt=None)` (3175): the one used for LO `launch`. Modes `param`/`run`/`all`/`loop`.
  - `check_param_card` rejects unresolved `Auto` widths (3207).
  - param mode (3209-3265): MSSM special-cases to `Source/MODEL/MG5_param.dat` via `convert_to_mg5card` (3212-3218); else runs the ufomodel `write_param_card.py` to get the default card (3240-3262); writes `param_card.inc` via `param_card.write_inc_file` (3265).
  - run mode (3268-3343): obtains/caches `self.run_card`; `cluster.modify_interface(self)` (3274-3275); **ninitial==1 zeroes lpp1/lpp2/ebeam1/ebeam2** (3276-3280); validates/copies the bias module and reconciles `bias_parameters` against the module's declared defaults (3284-3339); writes run.inc via `run_card.write_include_file(opt['output_dir'])` (3343).
  - loop mode (3346-3481): loop-induced MadLoopParams tuning (HelicityFilterLevel=1, CheckCycle=4, MLReductionLib by nhel, MLStabThres by nexternal, etc.) — madloop slice owns the physics; this writes `SubProcesses/MadLoop5_resources/MadLoopParams.dat` and triggers `initMadLoop` if model/MadLoop params changed.

## configure_directory (6050-6223)
"All action require before any type of run." Called by survey/refine.
- Early-out (6068-6072): if `self.configured >= time_mod` and run_card/random already set, only re-applies `cluster.modify_interface` and returns. So treatcards/compile only re-run when run_card.dat or param_card.dat is newer than last config.
- MSSM MG5_param.dat conversion (6084-6089); `check_nb_events()` caps events at 1M (6092; the cap test/value is `check_nb_events` 6477-6483: if `nevents>1000000`, perl-rewrites the card to `1000000 = nevents`, warning "Limiting number to 1M. Use multi_run for larger statistics.").
- PDF setup (6098-6127): sets make_opts pdlabel1/2 for eva/iww/edff/chff; for `pdlabel=='lhapdf'` links lhapdf and copies the lhaid set (6111-6116); for dressed leptons (lpp in [3,4]) copies lepton densities (6122-6127).
- Random seed (6129-6155): `iseed != 0` -> use it and reset in run_card; else read `SubProcesses/randinit`; else random. Python seed from `python_seed`.
- `ickkw==2` -> CKKW matching treatment (6156-6158).
- **`self.do_treatcards('')`** (6166) -> writes param_card.inc + run.inc.
- Compiles `Source` (`make all`, 6171-6172); refreshes bias dependencies and compiles bias module (6176-6206); writes proc_characteristics (6208-6209); clean-compiles subprocs if bias module changed (6211-6217).

## Outputs (your runtime-artefact slice)
- `<PROC_DIR>/SubProcesses/run.inc` (via write_include_file into output_dir, typically Source then propagated).
- `<PROC_DIR>/Source/param_card.inc`, `Source/MODEL/MG5_param.dat` (MSSM).

## Cautions
- ninitial==1 (decay/width) launches silently force lpp/ebeam to 0 in run mode — beam settings in the run_card are ignored for 1->N.
- configure_directory's mtime early-out means editing a card via something that does not bump mtime (or editing .inc directly) can be ignored; the recompile is gated on run_card.dat/param_card.dat mtime only.
- `check_nb_events` caps nevents at 1M inside configure_directory (rewrites the run_card to `1000000 = nevents`); larger statistics need `multi_run`.
