---
description: How check_madanalysis5 resolves event-file inputs (parton LHE vs hadron multi-source), how get_MA5_cmds translates the card into MA5 interpreter command batches, output retrieval (write-side), and gen_crossxhtml results-page detection (read-side glob of MA5 artifacts).
---

# MA5 input resolution + command generation (v3.7.1)

## check_madanalysis5 (common_run_interface.py:2708)
Returns `MA5_options` dict (`MA5_stdout_lvl`, `inputs`).
- `--MA5_stdout_lvl=` parsed to int or `logging.<LVL>` (:2715-2727).
- Parton seed: `MA5_options['inputs']='*.lhe'`; hadron seed: `['fromCard']` (:2734-2739).
- Requires `madanalysis5_path` set AND `<path>/bin/ma5` exists (:2744-2751) else `InvalidCmd("No valid MadAnalysis5 path set")`. Also requires `Cards/madanalysis5_<mode>_card.dat` present (:2760) else raises version-mismatch InvalidCmd.

### Parton input (:2789-2811)
- `--input=` is REJECTED at parton level (:2790) — the run's `unweighted_events.lhe` is used automatically.
- Input = `Events/<run>/unweighted_events.lhe.gz`; gzips the `.lhe` if only the unzipped exists; warns + skips if neither exists.
- Extra run-name args append their own `unweighted_events.lhe.gz`.

### Supported input formats (banner.py:5155-5163)
- `_default_parton_inputs = ['*.lhe']` (:5156) — parton MA5 consumes LHE only (and MG5 hard-wires the run's `unweighted_events.lhe.gz`, rejecting `--input=`).
- `_default_hadron_inputs = ['*.hepmc', '*.hep', '*.stdhep', '*.lhco', '*.root']` (:5155) — the hadron card's default input globs. This is the MG5-handoff confirmation of the format list HepMC/StdHEP/LHCO/ROOT(+LHE via priority for `unweighted_events.lhe*`). MG5 itself only PRODUCES `.lhe` (parton) and Pythia8 `.hepmc/.hep` (hadron); `.lhco`/`.root` are Delphes/external-supplied files the card may name.
- `is_reconstructible` (:5161-5163): a path is reconstructible (needs MA5 fast-sim reco) unless it ends `.lhco[.gz]` or `.root[.gz]` — those two are treated as ALREADY-reconstructed inputs (`lhco_input`/`root_input` branches, :5196-5201, :5498-5501), the rest (hepmc/hep/stdhep/lhe) go through reconstruction.

### Hadron input (:2813-2859)
- `store_result()` first so Pythia8 .hep files are registered.
- Sources: `--input=a,b,...` if given, else the card's `inputs` (read from the hadron card, default `_default_hadron_inputs` above).
- Each tag: absolute file/fifo taken as-is; otherwise glob in `Events/<run>/` (+`.gz`), preferring files containing the run_tag AND 'EVENTS', and always preferring `unweighted_events.lhe*`.
- CAUTION: if nothing resolves, `MA5_opts['inputs']==[]` -> run_madanalysis5 (3145) warns "No hadron level input found ... Skipping" under no_default, else raises.

## get_MA5_cmds (banner.py:5429)
Translates card -> list of `(runtag, [MA5 command strings])`, one tuple per MA5 sub-run.
- Prepends `import <UFO_model_path>` if given (:5456). The caller ALWAYS supplies it: `run_madanalysis5` passes `UFO_model_path=pjoin(me_dir,'bin','internal','ufomodel')` (common_run_interface.py:3169) — i.e. the run's OWN copied UFO model dir under the process directory, not the original `import model` location. So every MA5 sub-run begins `import <me_dir>/bin/internal/ufomodel`. Also fixed at the same call: `submit_folder=me_dir/MA5_<MODE>_ANALYSIS` and `run_dir_path=me_dir/Events/<run>` (:3167-3168).
- `import <file> as <dataset>` per input; dataset name = basename before first '.'; for `unweighted_events` it uses the run-name dir (:5459-5469).
- >1 input -> `set main.stacking_method = superimpose` (:5489).
- `submit <submit_folder>_<tag>` ends each batch (:5492).
- Reconstruction blocks (:5509): per reconstructible input (not lhco/root), import as reco_events, set output file (.lhe.gz or .root), submit `reco_<name>_<i>`. fifo inputs used at most once (warn_fifo).
- Analyses (:5537): parton -> `UFO_load + inputs_load + commands + submit`. hadron -> for each named reconstruction (+lhco_input/root_input), import the reconstructed outputs (lhe outputs forced via `set main.mode = parton`), then commands + submit `<name>_<reco>`.
- Recasting (:5558): writes recasting card to `<run_dir>/<tag>_<folder>_recasting_card.dat`, imports inputs as 'signal', `set main.recast.card_path=...`, submit 'Recasting'.

## Output retrieval (run_madanalysis5, common_run_interface.py:3256-3338)
- Per runtag, MA5 writes to `me_dir/MA5_<MODE>_ANALYSIS_<runtag>/`.
- `_reco_*` runtags: locate the produced `.lhe.gz`/`.root`, move analysis dir to `HTML/<run>/...`, symlink reco event file into `Events/<run>/`.
- `RECASTING`: target `Output/CLs_output_summary.dat` -> copied as `Events/<run>/<tag>_MA5_CLs.dat`.
- Normal analysis: target `Output/PDF/MadAnalysis5job_0/main.pdf` -> copied as `Events/<run>/<tag>_MA5_<mode>_analysis_<runtag>.pdf`; missing pdf logs "failed to create PDF output" (non-fatal).
- Whole `MA5_<MODE>_ANALYSIS_<runtag>` dir moved into `HTML/<run>/`. Banner updated with the card (:3353).

## Results-page detection (the READ-side of the output artifacts) — gen_crossxhtml.py
Distinct from the WRITE-side above (run_madanalysis5 copying outputs): `AllResults`/`OneTagResults.check_status` in `$MADGRAPH_INSTALL/madgraph/madevent/gen_crossxhtml.py` GLOBS the run dir to decide MA5 ran and to surface it on the run HTML page. Status keys are appended into per-level lists.
- Result lists init (:764-767): `self.madanalysis5_hadron=[]`, `self.madanalysis5_parton=[]`; both in the ordered status levels (:775).
- PARTON detection (level `madanalysis5_parton`/`all`, :840-855): globs `<tag>_MA5_parton_analysis_*.pdf` -> `'ma5_plot'`; `<tag>_MA5_PARTON_ANALYSIS_*/Output/HTML/MadAnalysis5job_0/index.html` -> `'ma5_html'`; `<tag>_MA5_PARTON_ANALYSIS_*/history.ma5` -> `'ma5_card'`; if any of those present -> `madanalysis5_parton.append('done')`. NOTE: parton results are stored into `self.parton` (the partonic level), per the comment "We also trigger parton for madanalysis5_parton because its results must be added to self.parton" (:805-806).
- HADRON detection (level `madanalysis5_hadron`/`all`, :856-874): `<tag>_MA5_hadron_analysis_*.pdf` -> `'ma5_plot'`; `<tag>_MA5_HADRON_ANALYSIS_*/Output/HTML/MadAnalysis5job_0/index.html` -> `'ma5_html'`; `<tag>_MA5_CLs.dat` file -> `'ma5_cls'` (the recasting CLs output); `'ma5_card'` -> globs `<tag>_MA5_PARTON_ANALYSIS_*/history.ma5`.
- CAUTION (source-visible, likely copy-paste bug): the HADRON `ma5_card` detection (:872-873) globs `<tag>_MA5_PARTON_ANALYSIS_*/history.ma5` — the PARTON analysis dir, NOT `_MA5_HADRON_ANALYSIS_*`. So a hadron-only run's `history.ma5` would not be detected for the `ma5_card` status under hadron. Cosmetic (affects only the results-page status tag, not whether the analysis ran or its PDFs); recorded as a pointer, not a runtime claim.
- These artifact NAMES are the read-side mirror of the write-side paths in the Output-retrieval section above (`Events/<run>/<tag>_MA5_<mode>_analysis_<runtag>.pdf`, `<tag>_MA5_CLs.dat`, the `MA5_<MODE>_ANALYSIS_*` dirs moved under HTML/<run>/).

## Accepted command flags per mode (from completion functions)
The tab-completion functions enumerate the full accepted argument surface (the canonical accepted-flag set, distinct from the behaviour described above):
- PARTON `complete_madanalysis5_parton` (madevent_interface.py:1962-1987): `-f`, `--MA5_stdout_lvl=`, `--no_default`, `--tag=`. NO `--input=` — consistent with the parton `--input=` rejection (check_madanalysis5:2790). First positional arg completes from run dirs containing `unweighted_events.lhe[.gz]`.
- HADRON `complete_madanalysis5_hadron` (common_run_interface.py:2889-2916): adds `--input=` to the parton set: `-f`, `--MA5_stdout_lvl=`, `--input=`, `--no_default`, `--tag=`. `--input=` completes from `_default_hadron_inputs + ['path']`; first positional completes from run dirs containing any `_default_hadron_inputs` glob.
- `--MA5_stdout_lvl=` completes to `logging.{INFO,DEBUG,WARNING,CRITICAL}` or `90` (both modes).
- `--tag=` parsed in check_madanalysis5 (common_run_interface.py:2765-2768): stripped from args, passed to `set_run_name(..., level='madanalysis5_<mode>')`.

## fifo caution
A `.fifo` input can be consumed by only the FIRST MA5 analysis/reconstruction; later sub-runs skip it with a one-time warning ("Only the first MA5 analysis/reconstructions can be run on a fifo") — banner.py:5479, mirrored by used_up_fifos in run_madanalysis5:3268.
