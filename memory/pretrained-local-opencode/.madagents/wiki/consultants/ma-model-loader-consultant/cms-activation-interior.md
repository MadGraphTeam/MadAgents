---
description: CMS activation SURFACE (global set option, NOT a run_card param; recorded in proc_characteristics; NOT auto-on for NLO; applies at LO too; orthogonal to Lorentz gauge) + change_mass_to_complex_scheme interior — CMSParam flip, CMASS_ synthesis, SM W-mass EW-scheme auto-switch, Yukawa-to-mass tie, full complexification; bypass_check dead in v3.7.1.
---

# CMS activation SURFACE — where `complex_mass_scheme` actually lives (v3.7.1)

**Myth to reject:** `complex_mass_scheme` is NOT a run_card parameter and there is no
`... ! complex_mass_scheme (NLO run card, hidden)` line. It is a **global MG5 interface
option** and is **NOT auto-enabled for NLO** — CMS is an explicit opt-in for both LO and NLO.

- **The real activation knob** = global option `complex_mass_scheme`, default **`False`**
  (`madgraph_interface.py:3105`, `options_madgraph` dict). Set via
  `set complex_mass_scheme True|False` → `set2_complex_mass_scheme` (`:8025-8054`). Help text
  `:853`. This is the ONLY thing that turns CMS on.
- **NLO does NOT force it on.** No code path sets `options['complex_mass_scheme']=True` for
  NLO/loop generation (grep is empty). Doc's "MG5 uses CMS for NLO computations" is a
  convention/recommendation, not an auto-switch. A user must issue `set complex_mass_scheme True`.
- **Threaded into every model import** at `do_import` (`madgraph_interface.py:5789`):
  `import_ufo.import_model(..., complex_mass_scheme=self.options['complex_mass_scheme'], ...)`.
  Applied at import time regardless of LO vs NLO → **CMS rewrites the model's masses to complex
  at LO too** (whether the LO *propagator integration* then uses a complex vs fixed width is
  phase-space/bw-window's slice, not mine).
- **Where it IS written to a file:** the `proc_characteristics` file, via
  `ProcCharacteristic.add_param('complex_mass_scheme', False)` (`banner.py:1761`) — a
  **ProcCharacteristic** (ConfigFile) class, NOT `RunCardLO`/`RunCardNLO` (those start at
  `banner.py:4187`/`5594`). At `launch`, `common_run_interface.py:263` reads
  `self.proc_characteristics['complex_mass_scheme']` back as `force_CMS` and re-imports the model
  with it (`:265`); the reweight/decay reload path uses `self.mother.options[...]` (`:259-261`).
  The CMS flag lives in proc_characteristics, not in any run_card block — do not conflate the two.
- **`set2` side effects** (`:8036-8054`): flips `self.options`, sets module-level
  `aloha.complex_mass` (`:8037`), `aloha_lib.KERNEL.clean()`. If a model is already loaded
  (`self._curr_model`), it triggers a **full re-import** of the current model:
  `self.do_import("model %s" % name, options={'allow_qed_cms':True})` (`:8054`) — the CMS-toggle
  self-re-import, parallel to `set2_gauge`. Idempotent toggles short-circuit with
  "already activated/desactivated" (`:8041-8052`).

## CMS is orthogonal to the Lorentz gauge
Activating CMS does **not** force Feynman/unitary/axial/FD. The only "gauge" it touches is the
EW **input scheme** (Gf,MZ,αEW → MW,MZ,αEW — see below), a naming overlap
(`base_objects.py:1916` comment "change the gauge scheme automatically" = EW scheme). The
loop-model/gauge auto-switch (`do_import:5810-5839`) runs after the import that applied CMS and
does not read the CMS flag — the two knobs are independent (see
`gauge-selection-and-loopmodel-autoswitch.md`).

# CMS activation interior: `change_mass_to_complex_scheme` (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/core/base_objects.py:1863`,
`def change_mass_to_complex_scheme(self, toCMS=True, bypass_check=False)`.

This is the *interior* of the activation boundary that `do-import-model-flow.md`
names. `import_ufo.import_model` calls it on every UFO load (`models/import_ufo.py:290`
restrict branch, `:319/:322` no-restrict branch). My slice owns CMS *activation*; the
conversion algebra here is shared with restriction but the orchestration (when it fires,
with what `toCMS`/`bypass_check`) is mine.

## `toCMS=False` short-circuit (NWA force)
`:1879-1891`: looks up the model parameter `CMSParam` (tries `CMSParam` then
`mdl_CMSParam`, `None` if neither). If `not toCMS`: set `CMSParam.expr='0.0'` if it exists
and **return immediately**. This is why `do_import` (CMS off, the default) still calls
`change_mass_to_complex_scheme(toCMS=False)` — to *force* `CMSParam=0.0` even when the UFO
model defaults to CMS, giving the correct NWA renormalization. No params are synthesized on
this path.

## `toCMS=True` path — the real activation (`:1893` onward)
1. `CMSParam.expr='1.0'` if present (`:1894-1895`) — strips the `real()` prefix from UVCT WF
   renormalization expressions in loop_qcd_qed models.
2. **Per-particle CMASS synthesis** (`:1898-1961`): for each particle, look at its width
   parameter. If width is zero (value `0.0` or name `'zero'`) → skip (`:1903-1908`). Else,
   for non-`ParamCardVariable` widths, wrap expr in `re(...)` (`:1909-1910`). If the particle
   is massive (`mass.name != 'zero'`) or has nonzero width, build a complex mass parameter
   `CMASS_<massname>`:
   - external (ParamCardVariable) mass → `CMASS_M = cmath.sqrt(M**2 - i*M*Width)` (`:1939-1943`).
   - internal mass → `CMASS_M` takes `mass.expr` as complex, and the width is re-expressed
     `width.expr = '- im(M**2)/cmath.sqrt(re(M**2))'` (or a derived `New_width` ModelVariable
     for ParamCardVariable widths, with the external width *removed* from the param_card)
     (`:1944-1959`).
   - Records `to_change[mass.name] = CMASS_name`.
3. **Yukawa re-tie** (`:1965-1989`): every external parameter in LHA block `yukawa` is removed
   and replaced by a `ModelVariable` that *equals the particle's mass* (`CMASS_M` if that mass
   was complexified, else `M`). So Yukawa masses follow the (complex or real) pole mass rather
   than being independent inputs.
4. **Global complexification** (`:1991-2018`): if `to_change` is empty, return. Otherwise build
   a regex over all `CMASS_`-sourced names and, for **every** parameter that is not a
   `CMASS_`/mass/width/`ParamCardVariable`, set `param.type='complex'` and substitute
   `M -> CMASS_M` in its expr (`:2005-2013`); same substitution over all couplings (`:2015-2018`).
   This is the step that makes the whole parameter graph complex.

## SM W-mass EW-scheme auto-switch (the surprising orchestration)
Inside the per-particle loop, **PDG 24 (W) with an internal/ModelVariable mass** triggers an
automatic electroweak input-scheme change BEFORE building its CMASS (`:1915-1928`):
`self.change_electroweak_mode(set(['mz','mw','alpha']), bypass_check=bypass_check)`.
`change_electroweak_mode` (`:1779`) for the `{mz,mw,alpha}` mode:
- Recognizes the standard `MW = sqrt(MZ²/2 + sqrt(MZ⁴/4 - aEW*pi*MZ²/(Gf*sqrt2)))` expr (with
  or without `mdl_` prefix) (`:1828-1838`).
- If matched: promotes `MW` to an **external** `ParamCardVariable` in LHA block `MASS[24]`
  (MW default value at `:1839-1854` if unset — read there), and demotes `Gf` to an **internal** parameter
  `Gf = -aEW*MZ²*pi/(sqrt2*MW²*(MW²-MZ²))` (`:1839-1854`). Returns True.
- If the W mass is already external or the expr doesn't match → returns False → the loop logs
  `'The W mass is not an external parameter ... automatic change of electroweak scheme failed.
  This is not advised for applying the complex mass scheme.'` (`:1923-1928`).

So: **turning CMS on for the SM silently flips the EW input scheme from (Gf, MZ, αEW) to
(MW, MZ, αEW)** — MW becomes a card input, Gf becomes derived. There is also a separate
`mode=='external'` arm (`:1795-1824`) that makes MW and sw2 external (MW/sw2 default values
at `:1795-1824` — read there), but the CMS path only ever calls the `{mz,mw,alpha}` arm.

## `bypass_check` / `allow_qed_cms` is DEAD in the v3.7.1 EW path
`do_import`→`import_model` derives `allow_qed = options.get('allow_qed_cms', False)` and threads
it as `bypass_check` into `change_mass_to_complex_scheme` (`import_ufo.py:285-290`, `:313-322`).
But `change_mass_to_complex_scheme` only forwards it to
`change_electroweak_mode(..., bypass_check=bypass_check)` (`:1920`), and
`change_electroweak_mode(self, mode, **opt)` (`:1779`) **swallows `bypass_check` into `**opt`
and never reads it** (grep for `opt` in `:1779-1862` → only the signature line). So in v3.7.1
`allow_qed_cms` / `bypass_check` has **no runtime effect** on the CMS activation path — the
"QED-CMS sanity check" it was meant to skip is not present in this code path. Don't tell a user
`--allow_qed_cms` changes CMS behavior here; it's a no-op as wired. (The no-restrict else-arm at
`:322` even passes it to a `toCMS=False` call, where it returns before the EW switch is reached.)

## Cautions
- CMS for the SM is not a no-op on the param_card: it **rewrites the EW input scheme** (MW in,
  Gf out). A user who set `Gf` in the card and turns on CMS will find Gf is now *derived*, MW is
  the input. This is decided at import time, invisibly.
- The double param_card read (`set_parameters_and_couplings(complex_mass_scheme=False)` at
  `import_ufo.py:283` before the `toCMS=True` call) is required so this routine can classify
  massive/zero-width particles — see `do-import-model-flow.md`. Without it, the per-particle
  width/mass `.value` checks (`:1904`, `:1912`) would be unpopulated.
- Yukawa parameters are *consumed* by CMS — block `yukawa` externals are removed and tied to the
  mass. A user expecting an independent Yukawa input loses it under CMS.
- Zero-width particles are skipped entirely (no CMASS), so a particle made stable by the
  restriction (`mdl_W...=ZERO`) does not get a complex mass even under CMS.
