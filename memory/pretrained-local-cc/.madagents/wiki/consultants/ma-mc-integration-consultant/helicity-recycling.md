---
description: Runtime helicity recycling — gensym.get_helicity orchestration (madevent_forhel threshold, ZEROAMP/Good-Helicity parsing) + HelicityRecycler source-to-source Fortran transform (MathsObject DAG). v3.7.1.
---

# Helicity recycling (v3.7.1)

Two pieces: (1) `gensym.get_helicity` in `gen_ximprove.py` discovers which helicities/amplitudes are numerically zero at runtime; (2) `hel_recycle.py` `HelicityRecycler` rewrites the matrix-element Fortran to skip them.

## gensym.get_helicity (gen_ximprove.py:124) — discovery
For each subprocess:
1. Compile + run `gensym` to get `nb_channel` (157).
2. Compile `madevent_forhel`; create `Hel/input_app.txt` from a hardcoded template (`'<npoints> 1 1 \n <threshold> \n 2\n 0\n -1\n -%s\n' % nb_channel`, gen_ximprove.py:175). The template's **first field is the #PS points probed** and the **second field is the relative threshold** below which a helicity/amplitude contribution is treated as numerically zero (consumed by the Fortran `madevent_forhel`, not by Python). Both are hardcoded literals — **read the current values fresh at line 175; do not cache them** (they can drift across versions).
3. Run `madevent_forhel < input_app.txt`, parse stdout (205-222) for marker lines:
   - `Matrix Element/Good Helicity:` → `all_hel` set of (me_index, hel).
   - `Amplitude/ZEROAMP:` → `all_zamp` (me_index, amp) zero amplitudes.
   - `HEL/ZEROAMP:` → `all_zampperhel` (me_index, hel, amp) zero per-helicity amplitudes.
   - ` GC_` lines with both columns 0 → zero couplings (zero_gc) → warns to use restricted model (224-229).
4. Gated by run_card flags: `hel_filtering` enables helicity filtering (data[0]); `hel_zeroamp` enables zero-amplitude filtering (data[1]); selection cached in `Hel/selection`, skip regeneration if unchanged (263-266).
5. For each `matrix*_orig.f`: if only 1 good helicity, copy orig→optim verbatim (no optimization, 300-303). Else build `HelicityRecycler(good_hels, bad_amps, bad_amps_perhel, gauge)` with `hel_filt/amp_splt/amp_filt` from run_card (`hel_filtering`/`hel_splitamp`/`hel_zeroamp`), generate `matrix*_optim.f`.

## HelicityRecycler (hel_recycle.py:383) — the transform
Source-to-source Fortran transformer. NOT a numerical filter at event time — it produces an optimized `matrix_optim.f` once, then the Fortran integrator uses it.
- Inputs: `good_elements` (good helicities), `bad_amps`, `bad_amps_perhel`, gauge.
- Flags (429-): `hel_filt` (drop helicity combos not in good list), `amp_splt` (split amplitudes per gauge), `amp_filt` (drop zero amplitudes).
- Builds a symbolic DAG of wavefunctions/amplitudes; rewrites HELAS calls so unused helicity combinations and zero amplitudes are not recomputed.

### Symbolic-amplitude DAG
- `DAG` (34): graph of wavefunction nodes; `find_path`, `dependencies`, `kill_old`.
- `MathsObject` (98): base; `nature` ∈ external/internal/amplitude. `good_helicity` classmethod (137): a helicity combo is good iff its external-wavefunction deps are a subset of some `External.good_wav_combs`, and `(hel_number,diag_number)` not in `bad_hel_amp`.
- `External` (194): external wavefunctions, carries `.hel`, `.mg` (leg index), `.get_id()`.
- `Internal` (296): internal (propagator) wavefunctions.
- `Amplitude` (337): vertices; `unfold_helicities` (563) skips amplitudes whose number is in `self.bad_amps` (592, returns '').
- `generate_output_file` writes the optimized matrix file from `template_dict` (helicity_lines, helas_calls, jamp_lines, amp2_lines, ncomb, nwavefuncs).

## Boundary note
The actual numerical comparison `|contribution| < threshold` happens inside generated/compiled Fortran (`madevent_forhel`), which is matrix-element/output territory, not this slice. Static template files under `Template/LO/SubProcesses/` do NOT contain the `ZEROAMP`/`Good Helicity` strings — they are emitted by generated `matrix*.f`. This slice owns the Python orchestration (`get_helicity`) and the Python transformer (`hel_recycle.py`), not the Fortran threshold comparison itself.

## Cautions
- `nhel` run_card flag: nhel==1 means Monte-Carlo-over-helicity (mc_hel path); changes point counts in survey/refine. The recycling discovery above is independent of that and runs regardless. The exact event-budget multipliers (`2**(nexternal//3)`, refine ceiling `2**(nexternal//2)`) and their four code sites are in mc-helicity-event-multipliers.md.
- The zero-contribution threshold is hardcoded in the input_app.txt template (line 175) — not a run_card knob.
- Single-helicity matrix files bypass the recycler entirely (300-303).
