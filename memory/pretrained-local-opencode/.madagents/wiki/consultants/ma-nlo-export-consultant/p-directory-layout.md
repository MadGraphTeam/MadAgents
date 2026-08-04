---
description: P*/V* subprocess directory layout — generate_directories_fks builds P<shell>, generate_virt_directory builds V<shell>, files written + linked, EW-Sudakov variant.
---

# P*/V* SubProcess directory layout (v3.7.1)

`generate_directories_fks(matrix_element, fortran_model, me_number, me_ntot, path, OLP='MadLoop')` — `export_fks.py:472`. One call per born matrix element; builds the P-directory under `SubProcesses/`.

## Directory naming
- Born: `borndir = "P%s" % matrix_element.born_me.get('processes')[0].shell_string()` — `:495`. Created with `os.mkdir`, then `chdir`.
- Virtual: `name = "V%s" % matrix_element.get('processes')[0].shell_string()` inside the P-dir — `generate_virt_directory` `:2445` (base) / `:4908` (optimised).
- NO orderstag/coupling-power suffix in directory names. `shell_string()` is the particle-content shell string only. The orderstag (`get_orderstag`, `:66`) feeds `orderstags_glob.dat` and amp_split indexing, not dir names. The `PB`/`PR`/`PV` scheme mentioned in card docs is a runtime/naming convention, not what `generate_directories_fks` emits — it writes a single `P<shell>` dir per born ME with a nested `V<shell>` for virtuals.

## What generate_directories_fks writes (in the P-dir)
Sequence (`:501`–): `generate_born_fks_files` (born files only — see below; does NOT write orders.inc); if `matrix_element.virt_matrix_element` → `generate_virt_directory`; `write_real_matrix_elements` (`matrix_N.f` per real, `:519`); `extra_cnt_wrapper.f` + per-cnt `born_cnt_N.f` (`:521`-539, 'cnt' template); `write_pdf_calls` (`parton_lum_N.f` per real, or `parton_lum_0.f` if no reals, `:541`); `nFKSconfigs.inc`; `iproc.dat`; `fks_info.inc` (returns split_types, unioned into `proc_characteristic['splitting_types']` `:559`); `leshouche_info.dat`+`leshouche_decl.inc`; `genps.inc`; `configs_and_props_info.dat`+`_decl.inc`; `real_from_born_configs.inc` (`:599` — REAL mapping written only if `splitting_types==['QCD']`, else a `_dummy` with a fixed `max_links`, `:600`-609, read the value there); `maxconfigs.inc`; `real_me_chooser.f`+`parton_lum_chooser.f` (`write_real_wrappers`); `get_color.f`; `nexternal.inc`; THEN orders.inc/a0Gmuconv/rescale/orders.h/amp_split_orders (`:632`-656); `maxparticles.inc`; `pmass.inc`; `draw_feynman_diagrams`; linkfiles.

## What generate_born_fks_files writes (`:2140`, born-only)
The `.inc`: `born_conf.inc`, `born_props.inc`, `born_leshouche.inc`, `born_nhel.inc`, `born_coloramps.inc`, `born_maxamps.inc`. Two ME files via `write_split_me_fks`: `born.f` ('born' template) and `born_hel.f` ('bhel' template), sharing a `born_dict` (`nconfs`, `den_factor_lines`, `ij_lines`, and `skip_amp_cnt` = `goto 999 ! LOonly` when no real_processes, `:2185`-2188). Color/charge-link files `b_sf_NNN.f` (one per `matrix_element.color_links`, `:2216`-2221) + `sborn_sf.f`. Then the EW-Sudakov ME family (`has_ewsudakov.inc`, `ewsudakov_haslo.inc`, goldstone/non-goldstone MEs, numder, wrapper — ewsudakov-me-writers page). NO orders.inc here.

## write_split_me_fks — the born/bhel/real/cnt ME writer (`:1970`)
Single routine for all four ME types; `proc_type` selects the template: `bornmatrix_splitorders_fks.inc` / `born_hel_splitorders_fks.inc` / `realmatrix_splitorders_fks.inc` / `born_cnt_splitorders_fks.inc` (`:2100`-2112). Computes `proc_characteristic['max_n_matched_jets']` = min(max QCD diagram power, max light-colored final partons) for FxFx (`:2000`). `wavefunctionsize` is the larger value if any spin-3/2 or spin-2 particle is present, else the default (`:2025`, read the two literals there). Returns `(ncalls, ncolor, nAmpSplitOrders, nSqAmpSplitOrders)`. JAMP uses split-order form when `split_orders` non-empty (`:2080`).

## Linked files (in generate_directories_fks, linkfiles list `:675`, `ln` loop `:772`)
ATTRIBUTION: the linkfiles block is in `generate_directories_fks` (`:472`), NOT in `generate_born_fks_files` (which ends ~:2275). The `ln('../'+file,'.')` loop is at `:772`-773. A large list from SubProcesses-level into each P-dir: FKS core (`fks_singular.f`, `fks_Sij.f`, `fks_powers.inc`, `genps_fks.f`, `symmetry_fks_v3.f`), drivers (`driver_mintMC.f`, `driver_mintFO.f`), `splitorders_stuff.f`, `orderstags_glob.f` (`:711`), `orderstag_base.inc`+`orderstags_glob.dat` (`:763`-764), scale/cut/reweight files, fastjet (`fastjetfortran_madfks_*.cc`, `fjcore.cc`), pythia8/dire wrappers, `sudakov.f`, `check_sudakov*.f`, `momentum_reshuffling.f`, etc. `param_card.dat` symlinked from `../../Cards/` (`:774`). makefile = symlink to `../makefile_fks_dir` (`:777`).
- `BinothLHA.f` symlink target depends on path: `../BinothLHA.f` if virt present (`:779`); `../BinothLHA_OLP.f` if OLP!='MadLoop' (`:781`); else `../BinothLHA_user.f` (`:783`).
- `ewsudakov_functions.f` appended if `matrix_element.ewsudakov` else `_dummy` (`:767`-770).
- Appends borndir to `subproc.mg` via `append_to_file`+`write_subproc` (`:788`-790). Then `gen_infohtml.make_info_html_nlo(dir_path)` per P-dir (`:795`).

## generate_virt_directory (V-dir)
Creates `MadLoop5_resources/` in the P-dir, then `V<shell>/`. Writes `loop_matrix.f` (via `write_loop_matrix_element_v4`, optimized def `loop_exporters.py:2060` / unoptimized `:1050`), `born_matrix.f` (`write_bornmatrix`), `nexternal.inc`, `pmass.inc`, `ngraphs.inc`, draws `loop_matrix.ps`+`born_matrix.ps`. Optimised version (`:4908`) also: links DHELAS `coef_specs.inc` into the V-dir (`:4946`); writes `global_specs.inc` (`write_global_specs`, `:4995`); writes `unique_id.inc` hardcoding `UNIQUE_ID=1` (`:4997`-4999, aMCatNLO always one process per V-dir). Links its own `coupl.inc`/`mp_coupl*.inc`/`coef_specs.inc`/MadLoop files (`:5001`+).

## EW-Sudakov generate_directories_fks (:5104)
Slimmed: writes born files, real MEs, extra_cnt_wrapper, iproc.dat, fks_info.inc, leshouche, genps.inc, nexternal.inc, orders.inc+amp_split_orders.inc, maxparticles.inc, pmass.inc; draws diagrams; links a SHORT linkfiles list (`:5213`) incl `sa_ewsudakov.f`, `sub_f2py_ewsudakov.f`, `sa_ewsudakov_dummyfcts.f`, `ewsudakov_functions.f`, `momentum_reshuffling.f`, `splitorders_stuff.f`, `setscales.f`, `orderstag_base.inc`, `orderstags_glob.dat`. No full madevent driver set.
- OMITTED vs base: no `generate_virt_directory` call, no `write_pdf_calls`/parton_lum, no `nFKSconfigs.inc`, no `configs_and_props`, no `real_from_born_configs`, no `maxconfigs.inc` (commented out `:5176`-5178), no orders.h/a0Gmuconv/rescale_alpha_tagged.
- orders.inc here uses plain `FortranWriter` (`:5188`) vs base's `FortranWriter90` (`:635`).

## Cautions
- `finalize` discovers P-dirs by `proc[0]=='P'` listdir (`:915`) — anything starting with P in SubProcesses is treated as a subprocess dir for jpeg/html.
- V-dir is nested INSIDE the P-dir, not a sibling. Virtual matrix element only emitted when `matrix_element.virt_matrix_element` is truthy ([LOonly]/[real=] modes skip it).
