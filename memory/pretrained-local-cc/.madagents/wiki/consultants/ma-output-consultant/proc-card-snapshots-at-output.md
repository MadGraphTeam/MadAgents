---
description: Output-time process-card snapshots — procdef_mg5.dat (MG4-template, written in export()) vs Cards/proc_card_mg5.dat (MG5 history, finalize()) vs SubProcesses/subproc.mg + the madevent.tar.gz gate (MG5_aMC v3.7.1)
---

# Process-card snapshots written at output time

A madevent output writes THREE distinct process-record files, in two different
output phases and two different formats. They are easy to conflate — same "proc card"
idea, different producers, different content, different consumers. Files:
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` and
`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py`.

## 1. `SubProcesses/procdef_mg5.dat` — MG4-template, written in export()
- Producer: `do_output`/`export()` at `madgraph_interface.py:9645-9651`, gated on
  `self._generate_info` being truthy AND the exporter having `write_procdef_mg5`:
  ```
  if self._generate_info and hasattr(self._curr_exporter, 'write_procdef_mg5'):
      card_path = pjoin(self._export_dir,'SubProcesses','procdef_mg5.dat')
      self._curr_exporter.write_procdef_mg5(card_path,
                          self._curr_model['name'], self._generate_info)
  ```
- `self._generate_info` is the FIRST generated process line (set at
  `madgraph_interface.py:4815`, `:5395`, etc., from the `generate` command). So this
  file carries only the first process string + its couplings, NOT the full history.
- Producer routine: `ProcessExporterFortran.write_procdef_mg5` (`export_v4.py:488`).
  Fills `template_files.mg4_proc_card.mg4_template` / `process_template` — the legacy
  MG4 proc_card.dat format, with `# Begin PROCESS`/`# Begin MODEL`/`# Begin MULTIPARTICLES`
  TAG blocks. Splits out `coupling=...` tokens into a separate coupling block.
- Purpose (docstring `:489`): "so that all the Madevent Perl scripts of MadEvent4 are
  still working properly for pure MG5 run." The header itself WARNS it is NOT a valid
  MG4 proc_card and will not reproduce MG5 results.
- Probe-confirmed (v3.7.1, `generate u u~ > z`): `SubProcesses/procdef_mg5.dat` present,
  header "WARNING: This Files is generated for MADEVENT (compatibility issue)",
  body `u u~ > z   #Process`, `end_coup`/`done`, `# Begin MODEL` -> `sm`.

## 2. `Cards/proc_card_mg5.dat` — MG5 command history, written in finalize()
- Producer: ME finalize at `export_v4.py:4727-4730` (SA at `:2647-2650`, MW at `:3633-3636`),
  `history.write(pjoin(self.dir_path,'Cards','proc_card_mg5.dat'))`.
- `history` is the full MG5 command log (set...; generate...; define...; output...). Content
  is the MG5_aMC banner + every `set` (group_subprocesses, gauge, zerowidth_tchannel, ...),
  all `define` multiparticle lines, and the `generate`/`add process` statements.
- This is the file a user re-runs (`mg5_aMC proc_card_mg5.dat`) to REPRODUCE the output.
- Probe-confirmed (v3.7.1, `generate u u~ > z`): `Cards/proc_card_mg5.dat` present, banner
  "VERSION 3.7.1", carries `set group_subprocesses Auto`, `set gauge unitary`,
  `generate u u~ > z`, `define p = ...`, etc. DIFFERENT content from procdef_mg5.dat.

## 3. `SubProcesses/subproc.mg` — the P-dir list, appended per subprocess
- Producer: each P-dir's `generate_subprocess_directory` appends its dir name via
  `files.append_to_file(<subproc.mg>, self.write_subproc, subprocdir)` (ME `:4556-4559`,
  MEGroup `:6509-6512`). `write_subproc` (`:6185-6191`) just writes `subprocdir + "\n"`.
- So `subproc.mg` is the newline-separated list of P-dir names (one per group/subprocess).
- Probe-confirmed: `generate u u~ > z` -> `subproc.mg` contains the single line `P1_qq_z`.

## The madevent.tar.gz gate — keyed on subproc.mg existence
- ME finalize (`export_v4.py:4742-4747`): `if os.path.exists(SubProcesses/subproc.mg)` then
  removes any existing `madevent.tar.gz` and runs `bin/internal/make_madevent_tar` (cwd=dir).
- So the archive is built ONLY if subproc.mg exists (i.e. at least one P-dir was written).
  An output that generated zero subprocesses writes no subproc.mg and no madevent.tar.gz.
- Probe-confirmed: `generate u u~ > z` -> `madevent.tar.gz` present.

## Cautions
- procdef_mg5.dat carries only the FIRST process (`_generate_info`); a multi-`add process`
  output's full process set is in proc_card_mg5.dat (history) and processes.dat
  (per-P-dir, per-pdir-file-inventory.md), NOT in procdef_mg5.dat. Probe-confirmed (v3.7.1,
  `generate u u~ > z; add process d d~ > z`): procdef_mg5.dat PROCESS block holds ONLY `u u~ > z`,
  while subproc.mg lists BOTH `P1_qq_z`+`P2_qq_z` and proc_card_mg5.dat carries both the generate
  and the add-process lines. The `_generate_info` is set unconditionally by `do_generate` (:4815)
  but only `if not self._generate_info` by add process (:5395), so add process never overwrites it.
- The two "proc card" files are NOT interchangeable: procdef_mg5.dat is for the legacy
  perl scripts (SubProcesses/), proc_card_mg5.dat is the re-runnable MG5 history (Cards/).
- standalone/standalone_cpp paths differ: SA writes Cards/proc_card_mg5.dat (history) but
  the C++ path's finalize does NOT (see standalone-cpp-output-flow.md).
