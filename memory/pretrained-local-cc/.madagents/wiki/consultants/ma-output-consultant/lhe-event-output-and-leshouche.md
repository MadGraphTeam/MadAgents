---
description: LHE event output at do_output — get_leshouche_lines builds the ICOLUP/IDUP/MOTHUP DATA statements (leshouche.inc), colorless process zeroes ICOLUP; do_output installs the runtime LHE writer templates (unwgt.f write_leshouche + rw_events.f write_event); LO event file is a LAUNCH-time artefact not an output one (MG5_aMC v3.7.1)
---

# LHE event output and leshouche.inc (ICOLUP color-flow tags)

Two distinct output-time responsibilities feed the LHE `<event>` record:
1. **Generated** at output: `leshouche.inc` (the per-diagram color-flow / ID / mother DATA tables) via `get_leshouche_lines`.
2. **Copied verbatim** at output (copy_template, madevent copies `Template/LO` wholesale — see template-copy-mechanics.md): the runtime Fortran that assembles+formats the LHE record. These are static template files, NOT generated per-process.

## leshouche.inc generation — `export_v4.py`
`ProcessExporterFortranME.write_leshouche_file`/`get_leshouche_lines` (`:936`/`:947`). Emits Fortran DATA statements read at runtime:
- `IDUP(i,iproc,numproc)` from `proc.get_legs_with_decays()` leg ids (`:956`).
- `MOTHUP(1..2,i)` — 0 for initial legs, `i` for final legs (`:961-964`), first subproc only.
- **`ICOLUP(i,cf,numproc)` = the color-flow tags** (LHE particle columns 5-6). Two branches (`:968-993`):
  - **No color basis** (`not matrix_element.get('color_basis')` — colorless process, e.g. pure-EW/lepton final state): writes a single **all-zero** ICOLUP row for each of i∈[1,2] (`:970-974`, `",".join(["%3r"%0]*nexternal)`). This is the "trivial color flow".
  - **Has color basis**: `color_basis.color_flow_decomposition(repr_dict, ninitial)` (`:984-986`) returns one dict per color flow; each becomes a `DATA (ICOLUP(i,cf,...))` row (`:988-993`). `repr_dict[leg] = particle.get_color() * (-1)**(1+state)` (`:980-982`) — the per-leg color rep signed by initial/final state; the color-flow DECOMPOSITION itself is color-decomposition slice's `ColorBasis`.
- Grouped path: `ProcessExporterFortranMEGroup.write_leshouche_file` (`:6840`) loops all MEs in the group, calling `get_leshouche_lines(me, iproc)` with `numproc=iproc` (`:6847`), concatenating tables. Ungrouped uses `numproc=0`.
- Written per-P-dir at `:3751`/`:4487`/`:6421`/`:10155`, then symlinked into `Source/` (`:3802`/`:4551`/`:6498`/`:10202`). See per-pdir-file-inventory.md for where it sits in the emission sequence.

## Runtime LHE writer TEMPLATES installed by do_output (copied, not generated)
- **`Template/LO/SubProcesses/unwgt.f` `write_leshouche`** (`:463`) — assembles the per-particle `jpart(7,nexternal)` record: reads `leshouche.inc` (IDUP/MOTHUP/ICOLUP DATA), fills `jpart(1)=IDUP`, `jpart(2..3)=MOTHUP`, `jpart(6)=status` (+1 final, set −1 for `nincoming` initial legs, `:597-601`), `jpart(7)=helicity` via `get_helicities` (`:607-610`). The ICOLUP color columns `jpart(4)/jpart(5)` are init 0 (`:595-596`) then filled by the `addmothers` call (`:738`, receives selected color-flow index `icol`) — addmothers.f is `write_addmothers` (ProcessExporterFortran base); resonant-mother + color assignment is runtime/launch+color territory. Calls `write_event(lun, pb, wgt, npart, jpart, ...)` (`:861`).
- **`Template/LO/Source/rw_events.f` `write_event`** (`:225`) — formats the `<event>` block. Header line `:281`; per-particle loop `:282-284` writes `ic(1,i)`=ID, `ic(6,i)`=ISTUP, `(ic(j,i),j=2,5)`=MOTHUP1,MOTHUP2,**ICOLUP1,ICOLUP2**, then px/py/pz/E/mass, `0.`=VTIMUP, `real(ic(7,i))`=**SPINUP(helicity)**. Format `:304` `51 format(i11,5i5,5e19.11,f3.0,f4.0)`. The `ic(1..7,*)` column legend is documented at `:234-240`. `write_event_to_stream` (`:136`) is a parallel copy that must be kept in sync (`:229`).

## LO event-file location — LAUNCH artefact, not output
`<PROC_DIR>/Events/run_NN/unweighted_events.lhe.gz` (default run_name `run_01`), e.g. `madevent_interface.py:1372/2662/2691`. **`Template/LO/` ships NO `Events/` dir** — the `run_NN/` subdir and the `.lhe.gz` are created at LAUNCH time (mc-integration/launch slices), not by do_output. do_output only installs the writer templates above. My slice confirms the writer-template location; the event file's existence/path at runtime is launch's.

## Cautions / claim corrections
- "Color-connection details dropped in some formats" is **imprecise**. There is no format switch that drops ICOLUP. ICOLUP is zeroed by a **per-process** property: a colorless matrix element (no `color_basis`) gets all-zero ICOLUP (`export_v4.py:970-974`), identically regardless of exporter. Distinct axis: standalone / standalone_cpp / pythia8 exporters don't produce LHE events at all (no unwgt.f event path) — that is "no event output", not "ICOLUP dropped".
- write_event/write_leshouche are RUNTIME code; do_output only copies them. Their execution semantics (which color flow is sampled per event, jpart color fill in addmothers) are launch/mc-integration/color-decomposition, not output. Output owns only that the template is installed and where the columns are formatted.
- Column mapping is the LHE/LesHouches standard: ID, MOTHUP(2), ICOLUP(2), status, and (via SPINUP field) helicity — verified against the `:234-240` legend and the `:283` write order, NOT recalled.
