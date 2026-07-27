---
description: export() phase — HelasCallWriter selection by exporter.exporter (v4/cpp/gpu/plugin), the 1->N decay zerowidth_tchannel override, and how matrix_*.f gets its HELAS calls (MG5_aMC v3.7.1)
---

# export() phase: HelasCallWriter selection and matrix_*.f emission

`self.export(...)` runs between copy_template and finalize. File:
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` (the `export` method,
grouping at `:9430`, helas-writer selection at `:9363`, subprocess loop at `:9631`).

## HelasCallWriter selection (`:9363-9379`)
`self._curr_helas_model` is chosen by the exporter's `exporter` class attr (NOT the
user format string directly):
- exporter has truthy `helas_exporter` attr -> `exporter.helas_exporter(model, options=...)`
  (plugin/SIMD override, takes precedence) (`:9363-9364`).
- `exporter == 'cpp'` -> `CPPUFOHelasCallWriter` (`:9366`).
- `exporter == 'gpu'` -> `GPUFOHelasCallWriter` (`:9368`).
- `exporter == 'v4'`:
  - MG4 v4 model path -> `FortranHelasCallWriter` (`:9371`).
  - UFO (normal) -> `FortranUFOHelasCallWriter(model, options=options)` (`:9376`).
- else -> raises `'unable to associate an helas format'` (`:9379`).
A second `_me_curr_helas_model` is built the same way if `_me_curr_exporter` differs
(`:9382-9398`); if the two exporters share `.exporter`, the writer object is reused.

### The 1->N decay zerowidth override (`:9373-9375`)
For the v4/UFO branch:
```
options = {'zerowidth_tchannel': self.options['zerowidth_tchannel']}
if self._curr_amps and self._curr_amps[0].get_ninitial() == 1:
    options['zerowidth_tchannel'] = False
```
So for a **decay process** (`get_ninitial() == 1`) `zerowidth_tchannel` is forced FALSE
regardless of the user's option — a 1->N process has no t-channels, so the zero-width
t-channel treatment is irrelevant and disabled. This is silent and decay-only.

## matrix_*.f emission path
The chosen `_curr_helas_model` is passed as `fortran_model` into the exporter's
`generate_subprocess_directory(subproc_group/me, fortran_model, ...)` (`:9631`, `:9637`).
Inside, `write_matrix_element_v4(writer, matrix_element, fortran_model, ...)` (ME group:
export_v4.py around `:4763`; SA `:3048`; MW `:3816`) calls
`fortran_model.get_matrix_element_calls(matrix_element)` to turn the HelasMatrixElement
into the Fortran wavefunction/amplitude call lines written into `matrix_*.f`.
- The HelasMatrixElement OBJECT (its wavefunctions/amplitudes) is the helas-amplitude
  slice's product; this slice owns only the *emission* of those objects to Fortran.

## HelasCallWriter hierarchy (`iolibs/helas_call_writers.py`)
- `HelasCallWriter` (`:38`) base; `FortranHelasCallWriter` (`:357`, MG4 v4 models);
  `UFOHelasCallWriter` (`:967`); `FortranUFOHelasCallWriter` (`:1020`, the normal madevent/SA
  Fortran path); `FortranUFOHelasCallWriterOptimized` (`:1348`, used when optimization on —
  this is where helicity-recycling-aware call emission lives, recycling ALGORITHM owned by
  mc-integration slice); `CPPUFOHelasCallWriter` (`:1608`); `GPUFOHelasCallWriter` (`:1742`);
  `PythonUFOHelasCallWriter` (`:2045`).
- `:118` (export_v4.py) installs a global
  `HelasCallWriter.customize_argument_for_all_other_helas_object` hook at import.

## Cautions
- Selection is on `exporter.exporter` (a class attr), not the user's `output <format>`
  string — a plugin can set exporter='cpp'/'gpu'/'v4' or provide helas_exporter and thereby
  change which writer is used. Read the exporter class, not the CLI word.
- The 1->N zerowidth override keys on `_curr_amps[0]` only; a mixed batch where the first
  amplitude is a decay would force it off for the whole output. Edge case — verify if a
  single output mixes 1->N and 2->N amps (uncommon).
