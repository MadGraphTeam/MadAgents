---
description: EW-Sudakov ME-writer subsystem — goldstone/non-goldstone ME files, QED+2 power, Z→Chi(250) imag-power, numder param-renorm scheme (alphaMZ vs Gmu), python dispatcher.
---

# EW-Sudakov ME-writer subsystem (v3.7.1)

Beyond the slimmed `generate_directories_fks` (`ProcessExporterEWSudakovSA:5104`, covered in p-directory-layout) and the python dispatcher (`:5067`), the Sudakov matrix-element Fortran is written by a family of writers in `ProcessExporterFortranFKS` (the base class — these methods live there, not on the EW-Sudakov subclass), driven from the dir-generation loop at `export_fks.py:2230-2275`.

## The per-subprocess ME files written (:2234-2275)
- `has_ewsudakov.inc` (`write_has_ewsudakov`) — flags whether process was generated with Sudakov MEs.
- `ewsudakov_haslo.inc` (`write_ewsud_has_lo`) — returns `has_lo`, threaded into the wrapper.
- For each `sudakov_matrix_elements` of `type=='goldstone'` (`:2240`): `ewsudakov_goldstone_me_<j+1>.f` (`write_sudakov_goldstone_me`) + `numder_ewsudakov_goldstone_me_<j+1>.f` (`write_numder_me`).
- If `matrix_element.ewsudakov`: `numder_born.f` (`write_numder_me(ime=None)`, `:2253`).
- For each `type!='goldstone'` (the interferences, `:2258`): `ewsudakov_me_<j+1>.f` (`write_sudakov_me`). Its `base_amp` field: 0 → born (`born_me`); ≥1 → `sudakov_matrix_elements[base_amp-1]` (`:2263-2266`).
- `ewsudakov_wrapper.f` (`write_sudakov_wrapper`, `:2271`).

## goldstone splitorders template (ewsudakov_goldstone_splitorders_fks.inc)
`template_files/ewsudakov_goldstone_splitorders_fks.inc` → subroutine `EWSDK_GOLD_ME_%(ime)d`. Key facts from the template body:
- Comment: "With respect to those at the born, the **QED power is increased by 2**" — matches `write_orders_file:1348` appending born_orders with QED+2 for ewsudakov (amp-split-and-orderstag page).
- Declares two extra amp_split arrays beyond orders.inc's `amp_split`/`amp_split_cnt`:
  - `double complex amp_split_ewsud(amp_split_size)` / `common /to_amp_split_ewsud/`.
  - `double complex amp_split_ewsud_LO2(amp_split_size)` / `common /to_amp_split_ewsud_LO2/`.
- Uses helpers `GETORDPOWFROMINDEX_SDKG%(ime)d`, `orders_to_amp_split_pos`, `orders_equal` for LO2 order matching; `iden = %(den_factor)d` averaging factor.

## Z → Goldstone (Chi) replacement: get_sudakov_imag_power (:2868)
The Sudakov approximation replaces Z bosons with their goldstone (Chi, **pdg 250**). The result is `base * conj(sudakov)`; the power of `i` is `base_ids.count(250) - other_ids.count(250)` — the difference in the number of Chi's between base ME and sudakov ME. So PDG 250 is the Goldstone-Chi marker used to count the imaginary-unit exponent.

## numder — parameter renormalisation derivative (write_numder_me :3056)
Numeric derivative for parameter renormalisation. `ime=None` → born (`mename='SBORN_ONEHEL'`, `hell='hell,'`); else the goldstone ME (`mename='EWSDK_GOLD_ME_<ime+1>'`).
**Scheme selection is keyed on the MODEL NAME, not a flag** (`:3070`):
- `'Gmu' not in self.model.get('name')` → uses `ewsudakov_numder_me_alphamz.inc` and warns "should be done in the alpha(MZ) scheme".
- else → `ewsudakov_numder_me_gmu.inc`, warns "should be done in the Gmu scheme".
So the renormalisation scheme is inferred from whether the model name contains the string "Gmu".

## python dispatcher (write_python_wrapper :5068, ewsudakov_pydispatcher.inc)
Written in EW-Sudakov `finalize` (call at `:5066`) to `bin/internal/ewsud_pydispatcher.py`. Builds a PDG→subfolder map from `self.dirstopdg`: `pdir_list`, `pdg2sud` (pdg-tuple → `import_lib('<dir>')`), `pdgsorted` (sorted-final-state pdg-tuple → unsorted). `get_pdg_tuple(pdgs,nincoming,sortfinal)` (`:5089`) keeps incoming unsorted, sorts outgoing only if sortfinal.

## a0Gmuconv / rescale (NOT Sudakov-only — all NLO, :638-646)
`generate_directories_fks` (NOT `generate_born_fks_files`; the latter is `:2140-2275`) writes `a0Gmuconv.inc` (`write_a0gmuconv_file:1159`, called `:639`, returns `startfroma0`) and `rescale_alpha_tagged.f` (`write_rescale_a0gmu_file:1184`, called `:644`) for the alpha0↔Gmu conversion of tagged photons. These writes sit at `:638-646` in the P-dir loop, right after the orders.inc/write_orders_file block (`:632-636`). Checks `mdl_aewgmu`/`mdl_aew` model params. General FKS born material, listed here because it is the alpha-scheme sibling of the Sudakov numder scheme. (`generate_born_fks_files` writes only born_*/color-link/EW-Sudakov-ME files and ends at :2275 — a different enclosing def.)

## Cautions
- Scheme detection by substring "Gmu" in the model name is fragile — a Gmu-renormalised model not named with "Gmu" silently gets the alpha(MZ) template (and the alpha(MZ) warning). Runtime/model-dependent — verify the loaded model name.
- PDG 250 (Goldstone Chi) is hardcoded in get_sudakov_imag_power; the Z→Chi mapping depends on the model defining 250 as the neutral goldstone.
- These writers are base-class methods invoked only on the EW-Sudakov path (`matrix_element.ewsudakov`/`sudakov_matrix_elements`); on an ordinary NLO run they don't fire.
