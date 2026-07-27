---
description: Per-P-dir file inventory written by generate_subprocess_directory — ME ungrouped (:4399) single-ME files vs MEGroup (:6213) per-ME + group-level files; output owns the emission SEQUENCE, content owned per-slice (MG5_aMC v3.7.1)
---

# Per-P-dir file inventory (generate_subprocess_directory)

File: `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py`. The exporter's
`generate_subprocess_directory` is what writes the `.f`/`.inc`/`.dat` files into each
`SubProcesses/P*_…/`. This page is the output-time EMISSION inventory (which writer fires,
producing which file, in which exporter). The CONTENT of each file is owned by the named slice;
output owns only that the file is emitted here and the order.

## Ungrouped ME path — `ProcessExporterFortranME.generate_subprocess_directory` (`:4399`)
One matrix element per P-dir. Writes (in order, `:4435-4532`):
- `driver.f` (`write_driver`, `:4435`) — n_grouped_proc=1.
- `matrix.f` OR `matrix_orig.f` (`:4440-4446`): forks directly on `self.opt['hel_recycling']`
  (simpler than the MEGroup fork — no template_matrix here). recycling-on -> `matrix_orig.f`.
- `auto_dsig.f` (`:4448`), `configs.inc` (`:4452`, returns s_and_t_channels + nqcd_list),
  `config_nqcd.inc` (`:4457`), `config_subproc_map.inc` (`:4461`), `coloramps.inc` (`:4465`),
  `get_color.f` (`:4470`), `decayBW.inc` (`:4474`), `dname.mg` (`:4478`), `iproc.dat` (`:4482`),
  `leshouche.inc` (`:4486`), `maxamps.inc` (`:4490`), `mg.sym` (`:4497`), `ncombs.inc` (`:4501`),
  `nexternal.inc` (`:4505`), `ngraphs.inc` (`:4509`), `pmass.inc` (`:4514`), `props.inc` (`:4518`),
  `symswap.inc` (`:4527`), `symfact_orig.dat` (`:4531`), `matrix.ps` (EPS, gated `:4535`).
- `link_files_in_SubProcess(Ppath)` (`:4547`) symlinks shared SubProcesses files into the P-dir.

## MEGroup path — `ProcessExporterFortranMEGroup.generate_subprocess_directory` (`:6213`, production default)
A SubProcessGroup -> one P-dir holding MULTIPLE matrix elements. Per-ME loop writes index-suffixed
files; then group-level files. Distinct from ungrouped:
- Per-ME (loop): `matrix%d_orig.f` + `template_matrix%d.f` (recycling on) OR `matrix%d.f`
  (recycling off) — the `:6283` fork keyed via `proc_characteristic['hel_recycling']`
  (see no-helrecycling-two-mechanisms.md); `auto_dsig%d.f`; `matrix%d.ps` (EPS, `:6359`).
- Group-level (once): `auto_dsig.f` via **`write_super_auto_dsig_file`** (the multi-ME dispatcher,
  not present ungrouped), `coloramps.inc`, `get_color.f`, `config_subproc_map.inc`, `configs.inc`,
  `config_nqcd.inc`, `decayBW.inc`, `dname.mg`, `iproc.dat`, `leshouche.inc`, `maxamps.inc`,
  default `mg.sym` (`write_default_mg_sym_file`, not the real-symmetry `mg.sym`),
  **`mirrorprocs.inc`** (initial-state mirror map — group-only), **`processes.dat`**
  (`write_processes_file` — lists all merged subprocesses, group-only), `ncombs.inc`,
  `nexternal.inc`, `ngraphs.inc`, `pmass.inc`, `props.inc`, `symswap.inc`, `symfact_orig.dat`,
  **`symperms.inc`** (group-only).
- So the MEGroup tell on disk: index-suffixed `matrix1.f`/`auto_dsig1.f`/`matrix1.ps`, plus a single
  group-level `auto_dsig.f` (super), `mirrorprocs.inc`, `processes.dat`, `symperms.inc` — none of
  which appear in an ungrouped P-dir.

## Slice ownership of the CONTENT (output emits, others own)
- `decayBW.inc` content (booldict, gForceBW emission) — **chain-decay slice**; output only invokes
  `write_decayBW_file(writer, s_and_t_channels)` here.
- `configs.inc`/`config_subproc_map.inc`/`props.inc`/`leshouche.inc` channel/propagator mapping —
  diagram/helas-amplitude territory (built from the matrix element's diagrams).
- `coloramps.inc`/`get_color.f` — color-decomposition slice.
- `matrix*.f` HELAS call lines — helas-amplitude slice's objects, emitted via the HelasCallWriter
  (see export-phase-helas-writer.md).
- `driver.f`/`combine_events.f`/`addmothers.f`/`dname.mg`/`auto_dsig*.f` — the run-driver Fortran;
  output emits, runtime/launch slice consumes.
This page asserts only the EMISSION (which file, where, by which writer) — not the content.

## Cautions
- `write_driver` here uses `n_grouped_proc=1` (ungrouped) vs the actual group size (MEGroup) — the
  driver's helicity-combination loop differs by path.
- `combine_events.f`/`maxconfigs.inc`/`maxparticles.inc` are written in FINALIZE (`:4666-4681`,
  dir-level), NOT in generate_subprocess_directory — they are per-output, not per-P-dir.
- File set drifts across versions; read the `:4435-4532` / `:6213+` blocks for the current list
  rather than trusting this catalog verbatim.
