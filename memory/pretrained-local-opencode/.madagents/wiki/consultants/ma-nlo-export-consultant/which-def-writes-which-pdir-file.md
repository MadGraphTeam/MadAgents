---
description: Enclosing-def attribution for P-dir files — generate_directories_fks calls generate_born_fks_files then keeps writing; orders.inc/a0Gmuconv/rescale/linkfiles/OLE_order are NOT born-files-method writes.
---

# Which def writes which P-dir file (v3.7.1)

## The principle
`generate_directories_fks` (`export_fks.py:472`) is the P-directory-loop method. At `:502` it calls `generate_born_fks_files` (`:2140`, a SEPARATE method) for the `born_*` files — **then continues writing many more files in its own body after the call returns**. So any P-dir file beyond the born/color-link/EW-Sudakov-ME set is attributed to `generate_directories_fks`, NOT `generate_born_fks_files`. The trap: the two method names sound interchangeable and `generate_born_fks_files` "looks like" where born-process files are written, so a file written 130 lines after the born-call gets mis-cited to it.

This caught a recurring slip in MY OWN reasoning (three instance pages independently mis-attributed, then corrected) — it predicts the correct enclosing def for any file in this 1600-line method, including ones the instances never named.

## The boundary (source-confirmed)
- `generate_born_fks_files` `:2140`-`:2275` (ends `:2275`). Genuinely writes there: the `born_*.inc` (`born_conf/props/leshouche/nhel/coloramps/maxamps`), `born.f`/`born_hel.f` (write_split_me_fks), color/charge-link `b_sf_NNN.f` + `sborn_sf.f`, and the EW-Sudakov ME family (`has_ewsudakov.inc`, goldstone/non-goldstone MEs, numder, wrapper). Attribute THESE to `generate_born_fks_files`.
- Everything else in the P-dir is `generate_directories_fks` (after the `:502` call):
  - `OLE_order.lh` (NJET branch, after born-call).
  - `orders.inc` via `write_orders_file` (`:634`).
  - `a0Gmuconv.inc` via `write_a0gmuconv_file` (`:639`), `rescale_alpha_tagged.f` via `write_rescale_a0gmu_file` (`:644`).
  - `amp_split_orders.inc`, `orders.h`.
  - the entire `linkfiles` block + `ln` loop (`:675` / `:772`-773), `param_card.dat` symlink (`:774`), makefile symlink (`:777`), `BinothLHA.f` symlink (`:779`-783).
  - `subproc.mg` append (`:788`-790), `make_info_html_nlo` (`:795`).
  - and the `generate_virt_directory` CALL (V-dir is the virt method's territory, not the born method's).

## The third method (don't confuse it in)
- `generate_virt_directory` (base `:2429` / optimised `:4908`) owns the V-dir files (`loop_matrix.f`, `born_matrix.f`, `coef_specs.inc`, `global_specs.inc`, `unique_id.inc`). It is CALLED from `generate_directories_fks` but its writes are attributed to itself.

## The EW-Sudakov variant
`ProcessExporterEWSudakovSA.generate_directories_fks` (`:5104`) is a SEPARATE slimmed override of the loop method — it writes a reduced set (born files, real MEs, orders.inc via plain `FortranWriter` not `FortranWriter90`, short linkfiles). When the dispatch is EW-Sudakov, read `:5104`, not `:472`.

## The move
"Which method writes file X in the P-dir?" → if X is a `born_*`/color-link/sudakov-ME file, it's `generate_born_fks_files` (`:2140`-2275). If X is anything else in the P-dir (orders, scheme-conversion, linkfiles, OLE_order, the V-dir call), it's `generate_directories_fks` (`:472`, after `:502`). V-dir file → `generate_virt_directory`. EW-Sudakov run → the `:5104` override. Don't infer the enclosing def from the file's name resembling "born".

## Three altitudes of the same trap
The enclosing-def discipline applies at THREE altitudes, ascending:
1. **born-method vs dir-loop** (THIS page): a P-dir file written after the `:502` born-call is `generate_directories_fks`, not `generate_born_fks_files`.
2. **virt-method vs dir-loop** (THIS page): V-dir files are `generate_virt_directory` even though it's CALLED from the dir loop.
3. **interface vs export_fks** (interface-driven-exporter-methods.md): the SubProcesses-level aggregates (`procdef_mg5.dat`, `initial_states_map.dat`, `pineappl_maxproc.*`, `orderstags_glob.dat`, `coef_specs.inc`) are written by `amcatnlo_interface.py` calls (`:994`-1011) AFTER the dir loop; the dir loop only SYMLINKS them down (they appear in its linkfiles list as symlink targets, not writes).
Proximity in the call tree / appearance in a linkfiles list is never write-attribution at any altitude — check the def range.

## Instances generalized (kept)
- amp-split-and-orderstag.md — orders.inc/write_orders_file attribution (kept).
- ewsudakov-me-writers.md — a0Gmuconv/rescale attribution (kept).
- p-directory-layout.md — the full write-sequence + linkfiles-block attribution note (kept).
- interface-driven-exporter-methods.md — the third (interface-level) altitude (kept; carries the interface-driven method surface).
