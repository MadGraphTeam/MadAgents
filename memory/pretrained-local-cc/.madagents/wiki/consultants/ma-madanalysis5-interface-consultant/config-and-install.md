---
description: madanalysis5_path configuration, the install MadAnalysis5 path, and how MA5 surfaces as an analysis switch / card in the run.
---

# MA5 configuration & install wiring (v3.7.1)

## madanalysis5_path
- Declared default in `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py:650`: `'madanalysis5_path': './HEPTools/madanalysis5'`.
- In `$MADGRAPH_INSTALL/input/mg5_configuration.txt:180`: `madanalysis5_path = $MADGRAPH_INSTALL/None #` — i.e. UNSET in this install (literal `None` sentinel under the install root). Until populated, parton/hadron MA5 are unavailable.
- CONFIG-LOAD NULLING (`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:7440-7448`): at option-load, if `<MG5DIR>/<path>/bin/ma5` is not a file (and `<path>/bin/ma5` isn't either) -> `self.options['madanalysis5_path'] = None` (:7443). If `bin/ma5` DOES exist, it runs `is_MA5_compatible_with_this_MG5(ma5path)` and nulls again (:7448 + `logger.warning`) when a reason is returned. So the `$MADGRAPH_INSTALL/None` STRING is resolved to python `None` here — PROBE-CONFIRMED `MasterCmd().options['madanalysis5_path']` is `None`, not the literal string. Same nulled value closes BOTH the output-time card-creation gate and the run-time path gate.
- Populated by `install MadAnalysis5` (typically -> `HEPTools/madanalysis5`). MELauncher reads `cmd_int.options` into `self.options` (launch_ext_program.py:594), so the path flows from mg5_configuration into the child MadEventCmd.

## Manual set + version-compatibility gate
- `set madanalysis5_path <PATH>` -> `set2_madanalysis5_path` (`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:8563`). Resolves PATH relative to MG5DIR if it is a file there, then runs `misc.is_MA5_compatible_with_this_MG5(ma5path)` BEFORE setting. If that returns a message (incompatible) it `logger.warning`s and DOES NOT set the option — the path is silently left unchanged. Only `None` message -> `self.options['madanalysis5_path']=args[1]`.
- `is_MA5_compatible_with_this_MG5` (`$MADGRAPH_INSTALL/madgraph/various/misc.py:168`): reads MA5 version from `<ma5path>/bin/ma5` (regex `\s*version\s*=\s*["'](.*)["']\s*`), fallback `<ma5path>/version.txt` line `MA5 version :` (:217-228). Uses a custom `version`/`LooseVersion` comparator (:172-208). Returns a non-None reason (path won't activate) for THREE distinct cases:
  - (a) **no MA5 version readable** (:230-232): "No MadAnalysis5 version number could be read from the path supplied ... will not be active in your session."
  - (b) **MG5 too old** (:245-249): running MG5 below its cutoff AND MA5 above its cutoff -> "This active MG5aMC version is too old (vX) for your selected version of MadAnalysis5 (vY) ... Upgrade MG5aMC or re-install MA5 ...". (The two version-boundary constants are hardcoded and version-drift-prone — read them fresh at misc.py:245-255.)
  - (c) **MA5 too old** (:251-255): running MG5 above its cutoff AND MA5 below its cutoff -> "Your selected version of MadAnalysis5 (vX) is too old for this active version of MG5aMC (vY). Re-install MA5 ...".
  - Unrecognised MG5 version (`get_pkg_info` fails) -> returns None at :243-244 (treated as dev version, allowed). MG5 version comes from `get_pkg_info()['version']` (:238-240).
  - Caution: a path pointing at an unreadable/mis-versioned MA5 is rejected at SET time with only a warning — easy to miss why MA5 stays unavailable.

## install MadAnalysis5
- `MadAnalysis5` is in `_advanced_install_opts` — `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:3007-3008` (list also merged into `_install_opts` at :3012).
- Name alias handling at madgraph_interface.py:2966 (`['MadAnalysis5','MadAnalysis']`) and the install-key map `'MadAnalysis5':'madanalysis5'` (:6514). Citation key `'MadAnalysis5':['arXiv:1206.1599']` (:6497) — matches the runtime "Running MadAnalysis5 [arXiv:1206.1599]" status line.
- NOTE (out-of-slice for detail): actual install steps + ROOT/dependency handling belong to the installation slice.

## Analysis switch surfacing (madevent_interface.py)
- The ControlSwitch KEY is `analysis` (NOT `MadAnalysis5`), registered in `AskRun(cmd.ControlSwitch).to_control` at :502 with prompt "Choose an analysis package (plot/convert)". The offered VALUE literal is exactly `MadAnalysis5` (capital M, A). So a script line `analysis=MadAnalysis5` is well-formed — it matches directly at `check_analysis` :766 (`value in get_allowed_analysis()`). The MA5 launch-menu question is `analysis`, one of the AskRun switches (shower/detector/analysis/madspin/reweight).
- `get_allowed_analysis` (:742-761): `MadAnalysis5` appended to the allowed list only if `'MA5' in self.available_module` (:753-754); `'MA5'` is added iff `options['madanalysis5_path']` set (:526-527). If no analysis module available the switch shows `Not Avail.` (set_default :822); otherwise `OFF` is always appended (:758-759).
- Name normalisation (`check_analysis` :763-780, case-insensitive): 'ma5'/'madanalysis5'/'madanalysis_5'/'5' -> 'MadAnalysis5' (:770-771); bare 'ma'/'madanalysis' -> MA5 if available else MA4 (:772-778); anything else -> False (rejected).
- The `analysis` switch auto-selects `MadAnalysis5` if a `madanalysis5_{parton,hadron}_card.dat` exists in Cards/ (set_default_analysis :813-816 elif), but only when MA4+plot_card.dat is not the prior branch (:810-812).
- consistency hook: setting analysis=Rivet with shower!=Pythia8 forces shower->Pythia8 (`consistency_analysis_shower` :794-804); no such coupling for MadAnalysis5.

## Cards lifecycle in the run dir
- `keep_cards`/card listing (madevent_interface.py:6782-6785): `madanalysis5_parton_card.dat` appended when `switch['analysis'].upper()=='MADANALYSIS5'`; `madanalysis5_hadron_card.dat` appended ONLY when analysis==MA5 AND `switch['shower']!='OFF'` (:6784). So with shower=OFF the hadron MA5 card is never offered/kept — parton-only. Both ignore-if-absent (:6865).
- Operative cards: `<PROC_DIR>/Cards/madanalysis5_{parton,hadron}_card.dat`. Outputs land in `<PROC_DIR>/Events/<run>/tag_*_MA5_{PARTON,HADRON}_analysis_*` and full analysis dirs under `HTML/<run>/`.

## Run-level chaining (madevent_interface.py:6377-6393)
`upgrade_tag` maps which downstream levels each starting level enables, e.g. parton enables `madanalysis5_parton` and `madanalysis5_hadron`; pythia8 enables `madanalysis5_hadron`. This governs which MA5 mode is reachable from a given generation level.
