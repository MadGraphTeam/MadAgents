---
description: gen_infohtml.make_info_html — the output-time HTML/info.html page, diagram counting from matrix_*.f (orig fallback), and nb_gen_diag feeding proc_characteristic['nb_channel'] (MG5_aMC v3.7.1)
---

# gen_infohtml: the output-time HTML info page

File: `$MADGRAPH_INSTALL/madgraph/iolibs/gen_infohtml.py`. `make_info_html(dir_path)` is a
CLASS whose `__init__` does all the work (`:147-158`). Invoked at OUTPUT time from ME
finalize (`export_v4.py:4719`, `obj = gen_infohtml.make_info_html(self.dir_path)`), NOT at
launch — distinct from the runtime cross-section HTML (`gen_crossxhtml.py`, numerical/launch
slice). This page writes `<PROC_DIR>/HTML/info.html`.

## __init__ flow (`:147-158`)
Builds `self.rep_rule` then `self.write()`:
- `define_meta()` (`:178`): sets a REFRESH meta tag if `SubProcesses/done` exists, else EXPIRES.
- `define_info_tables()` (`:187`) -> `rep_rule['info_lines']`: the per-P-dir diagram table.
- `give_model_info()` (`:161`): links Source/MODEL/particles.dat + interactions.dat if present.
- `check_log()` (`:310`): links `proc_log.txt` if present.
- `write()` (`:320-325`): substitutes `template_text` and writes `<PROC_DIR>/HTML/info.html`.

## Diagram counting and the matrix_orig fallback (`:202-246`)
`define_info_tables` enumerates valid P-dirs = subdirs starting `P` that contain `auto_dsig.f`
(`:202-205`). Per subprocess id it calls:
- `get_diagram_nb(proc, id)` (`:238`): reads `SubProcesses/<proc>/matrix<id>.f`; **if that file
  is absent, falls back to `matrix<id>_orig.f`** (`:244-245`). Counts lines matching the regex
  `Amplitude\(s\) for diagram number (\d+)` (`:243`). So it works for BOTH the recycling-OFF
  layout (plain `matrix1.f`) and the recycling-ON layout (`matrix1_orig.f`, no plain file at
  output time — see no-helrecycling-two-mechanisms.md). This fallback is exactly why the info
  page still counts diagrams on a default (recycling-on) madevent output.
- `check_postcript(proc, id)` (`:301`): links `matrix<id>.ps` only if `matrix<id>.f` exists
  (so the postscript link is absent on a recycling-on output until `matrix1.f` is assembled).

It accumulates two running totals into `rep_rule`:
- `nb_gen_diag` += diagram count per subprocess (`:231`) — number of generated diagrams.
- `nb_diag` += diagram count * number of subprocesses in the group (`:230`).

## The output -> proc_characteristic feedback (`export_v4.py:4722-4725`)
ME finalize reads the returned object's count back into the process characteristics:
- `nb_channel = obj.rep_rule['nb_gen_diag']` -> `proc_characteristic['nb_channel']` (`:4725`).
- if `online` in flaglist, also writes `<PROC_DIR>/Online` with that number (`:4722-4723`).
So the `nb_channel` field in `SubProcesses/proc_characteristics` is sourced from THIS HTML
generator's diagram count, not computed independently. Probe-confirmed (v3.7.1,
`generate u u~ > z`): `HTML/info.html` written, `proc_characteristics: nb_channel = 1`.

## NLO subclass (`:329`)
`make_info_html_nlo(make_info_html)` overrides `define_info_tables` (does not export
diagrams.html, reads from a file list instead, `:332-445`) — the NLO export path's info page.

## Cautions
- This is OUTPUT-time HTML. Do not confuse with the launch-time cross-section pages
  (`gen_crossxhtml.py` / `sum_html.py`) — those are the numerical/launch slice.
- `nb_channel` in proc_characteristics is the gen_infohtml diagram count, so a model/process
  whose matrix file the regex mis-counts would propagate a wrong nb_channel — the count is a
  parse of the emitted Fortran, not a fresh diagram enumeration.
