---
description: Subprocess grouping mechanics — find_process_classes grouping criterion (incl. process-id discriminator), generate_name P-dir naming, the gpu path (madevent-key group + split_nonidentical_grouping per-ME split + gpu naming), and runtime grouped_mode mutation by set-group-gpu / --me_exporter (MG5_aMC v3.7.1)
---

# Subprocess grouping mechanics (group_subprocs.py)

File: `$MADGRAPH_INSTALL/madgraph/iolibs/group_subprocs.py`. This is the
*mechanics* of grouping; the do_output `group_subprocesses=Auto` *decision* is in
do-output-orchestration.md (`madgraph_interface.py:9257-9287`).

## Entry from export() (`madgraph_interface.py:9430-9466`)
When grouping is on, export() splits `_curr_amps` into decay-chain vs non-decay-chain,
then:
- non-dc: `SubProcessGroup.group_amplitudes(non_dc_amps, grouping_criteria, ...)` (`:9444`).
- dc: `DecayChainSubProcessGroup.group_amplitudes(...)` then `.generate_helas_decay_chain_subproc_groups()` (`:9448-9456`).
- `grouping_criteria = self._curr_exporter.grouped_mode` (`:9439`); if `'gpu'` it is
  remapped to `'madevent'` for the criterion (`:9440-9441`), BUT the groups are then
  re-split by `subproc_groups.split_nonidentical_grouping()` when grouped_mode is `'gpu'`
  (`:9461-9462`). So gpu groups by madevent criterion then splits non-identical MEs apart.
- Each group gets a unique `uid` assigned to `me.get('processes')[0]` (`:9467-9474`).

## group_amplitudes (`group_subprocs.py:421`)
`group_amplitudes(amplitudes, criteria='madevent', matrix_elements_opts={})`:
- asserts criteria in `['madevent','madweight','gpu']`; empty -> `'madevent'` (`:428-431`).
- calls `find_process_classes` to bucket amplitudes, then builds one `SubProcessGroup`
  per class (`:434-449`). Group `number` = the process id of its first amplitude (`:443`),
  `name` = `generate_name(...)` (`:445`).

## find_process_classes — the grouping CRITERION (`:454-516`)
Builds a `proc_class` key per amplitude; amplitudes with an equal key merge into one
P-directory. The key for **madevent** (`:482-489`):
```
proc_class = [ [(p.is_fermion(),) for p in is_parts],          # initial-state: fermion-ness only
               [(p.get('mass'), p.get('spin'),
                 p.get('pdg_code') % 2 if p.get('color') == 1 else 0,   # parity only for colorless
                 abs(p.get('color')), l.get('onshell')) for (p,l) in
                 zip(is_parts+fs_parts, process.get('legs'))],
               amplitude.get('process').get('id'),
               process.get('id') ]
```
So two subprocesses merge iff: same initial-state fermion-ness pattern; for every leg
same (mass, spin, |color|, onshell) AND — only when colorless — same pdg parity; same
amplitude process id AND same process id. The two id components are the discriminator
that pairwise-identical particle content alone does NOT override.
- Probe-confirmed (v3.7.1): single `generate p p > z` -> ONE P-dir `P1_qq_z` holding
  `u u~/c c~/d d~/s s~ > z` merged (processes.dat lists all four). Same particle
  properties + same statement (one process id) -> merged.
- Probe-confirmed: `generate u u~ > z` then `add process d d~ > z` -> TWO P-dirs
  `P1_qq_z`, `P2_qq_z` (same abstracted name, NOT merged). Identical particle properties
  but DIFFERENT process ids (separate statements) -> the `process.get('id')` key
  component keeps them apart.
So "u u~ and d d~ merge" is true only within one multiparticle generate; across
separate generate/add-process statements they split on process id even when the
abstracted P-dir name collides. `e+ e- > z` stays separate from quarks regardless
(colorless leptons carry pdg-parity distinction; different color).
The inline source comment notes how to tune it: add `p.get('is_part')` to distinguish
q from qbar, remove `p.get('spin')` to combine q and g into "j".
- **madweight** key (`:491-496`) keys final-state legs only on (is-b, is-e, is-mu, is-tau)
  + process id — a coarser lepton/b classification.
- **gpu** key (`:498-507`) is like madevent but keeps the full `p.get('pdg_code')`. CAUTION:
  this gpu branch is NOT reached from the do_output export path. `madgraph_interface.py:9439-9441`
  reads `grouping_criteria = self._curr_exporter.grouped_mode` and then, if it is `'gpu'`,
  REMAPS it to `'madevent'` before calling `group_amplitudes` (`:9445`/`:9451`). Grep-confirmed:
  no caller anywhere passes `'gpu'` as the criterion (only export-path caller is :9445/:9451,
  always remapped). So gpu output groups by the MADEVENT key, not the gpu key. The gpu
  fine-graining comes AFTERWARD from `split_nonidentical_grouping` (see below), not from this
  key. Treat the `:498-507` gpu key as dead for the output slice.

## generate_name — P-directory naming (`:231-293`)
Builds the human-readable group name (becomes `P<number>_<name>` on disk). Per leg, with
massless particles abstracted to class letters (for madevent/non-gpu/non-madweight):
- massless fermion, colored (color != 1) -> `"q"` (both initial and FS; FS uses spin==2).
- massless fermion, colorless, odd pdg -> `"l"` (initial) ; FS massless colorless spin-2:
  charge 0 -> `"vl"`, else `"l"`.
- massless fermion, colorless, even pdg (initial) -> `"vl"`.
- everything else -> the literal particle name with `~`->`x`, `+`->`p`, `-`->`m`.
- initial vs FS separated by `"_"` (`:259`).
- polarization tags appended to FS legs: `[-1,1]`/`[1,-1]`->`T`, `[-1]`->`L`, `[1]`->`R`,
  else the raw polarization digits (`:285-292`).
- decay chains recurse: `name += "_" + generate_name(dc, criteria)` (`:290-291`).
gpu and madweight criteria skip the abstraction and use raw particle names (`:240-247`).
This is why a P-dir is named e.g. `P1_qq_z` — `u u~`, `d d~`, etc. all map to `qq`.

## The gpu path: madevent-key grouping + per-ME split + gpu naming (`:573`)
`split_nonidentical_grouping` (`group_subprocs.py:573`) runs when `grouped_mode == 'gpu'`
(`madgraph_interface.py:9459-9462`), AFTER the madevent-key grouping. It splits each group
so that EACH matrix element becomes its own group (`new_group['matrix_elements'] = [new_me]`),
then renames each via `generate_name(..., criteria='gpu')` — i.e. raw particle names, no
q/l/vl abstraction. So gpu output = (madevent-key groups) -> (one ME per group) -> (raw-name
P-dirs). The per-ME granularity and the raw naming both come from HERE, not from the
find_process_classes gpu key.
- Probe-confirmed (v3.7.1): `set group_subprocesses gpu` + `generate p p > z` ->
  `P1_ddx_z` and `P1_uux_z` — the single madevent group (all quarks) split into u-type vs
  d-type, named with raw names (`d d~`->`ddx`, `u u~`->`uux`), both keeping the `P1_` group
  number. Contrast the plain-madevent probe above which kept all quarks in one `P1_qq_z`.

## Effective grouped_mode is mutated at runtime — not the static class attr (`:7976`, `:9504`)
The grouping criterion is `self._curr_exporter.grouped_mode`, but this is mutated to `'gpu'`
at runtime by two independent triggers, so the EFFECTIVE criterion is not the exporter
class's static `grouped_mode` (= `'madevent'` for ProcessExporterFortranMEGroup, export_v4.py:6201):
- **Class-level** (`madgraph_interface.py:7976-7978`): `set group_subprocesses gpu` mutates
  the CLASS attr `export_v4.ProcessExporterFortranMEGroup.grouped_mode = 'gpu'` (persists
  across instances until reset to `'madevent'` at :7979). This is the SIMD/CUDA-madevent
  vectorization path.
- **Instance-level** (`madgraph_interface.py:9504-9505`): when a second exporter exists
  (`--me_exporter`, the CPP/CUDA matrix element alongside Fortran madevent), `export()` forces
  `self._curr_exporter.grouped_mode = 'gpu'` before generate_matrix_elements.
Both make the do_output grouping take the gpu path (madevent-key group + per-ME split + gpu
naming) even though the factory built a plain ME-group exporter. So `--me_exporter=cpp` or
`set group_subprocesses gpu` changes P-dir layout/naming vs a vanilla `output madevent`.

## SubProcessGroup container (`:122`)
Holds `amplitudes`, lazily-computed `matrix_elements` (via `generate_matrix_elements`
on first `get`), `mapping_diagrams`/`diagram_maps` (for super-config.inc), `amplitude_map`.
The exporter's `generate_subprocess_directory(subproc_group, ...)` (ME group: export_v4.py
`:6195` class, the grouped-mode P-dir writer) consumes one SubProcessGroup per P-dir.

## Cautions
- The criterion is keyed on PARTICLE PROPERTIES from the model, not on PDG identity for
  colored states — a restricted/BSM model with non-standard masses or color reps will
  group differently. Verify per model, not from the SM expectation.
- gpu path groups by the MADEVENT key then re-splits per-ME with gpu naming (see the gpu-path
  and runtime-mutation sections above); do not assume gpu P-dir layout matches madevent, and
  do not attribute the difference to the find_process_classes gpu key (it is dead for output).
- Same particle properties do NOT force a merge across separate generate/add-process
  statements — the process-id key components keep them apart (probe-confirmed above).
- Whether two subprocesses actually end up in one P-dir is a RUNTIME outcome of this
  criterion over the specific amplitude set — a probe-candidate, not predictable from
  reading alone for a novel process.
