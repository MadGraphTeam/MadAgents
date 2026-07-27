---
description: Per-event EVA flux algorithm in ElectroweakFluxDriver.f — where eva_xcut/ievo_eva enter, the mu2min floor auto-raise, vpol/photon-LLA handling, and the QED/neutrino-flavor stop checks. The internals scale-params.md/runtime-pdf-dispatch.md only name.
---

# EVA flux driver internals (ElectroweakFluxDriver.f)

Source: `$MADGRAPH_INSTALL/Template/LO/Source/PDF/ElectroweakFlux.f`, `ElectroweakFluxDriver.f`. Reached from `pdg2pdf.f` (runtime-pdf-dispatch.md) → `eva_get_pdf_by_PID(vPID,fPID,vpol,fLpol,x,mu2,ebeam)`. This page walks what that call actually does — the algorithm scale-params.md's EVA-runtime section and runtime-pdf-dispatch.md only name.

`common/to_eva/ievo_eva,evaorder,eva_xcut` carries the three run-card switches into Fortran (:45).

EVA EW constants (`eva_mz2,eva_mw2,eva_gw2,eva_gz2,eva_ee2,eva_sw2,...`) come from `ElectroweakFlux.inc` (`include` at :47). That .inc is **NOT in the template** — it is GENERATED into `<PROC>/Source/` at output time by `export_v4.py` (:707, from template `iolibs/template_files/madevent_electroweakFlux.inc`), deriving `eva_mz2=eva_mz**2` etc. from the **loaded model**. So the EVA Z/W/photon flux IS model-dependent (MZ/MW/sw2/couplings flow from the model) — the OPPOSITE of PhotonFlux.f's EPA/IWW α, which is a hardcoded literal independent of the model (photon-flux-ion-pdf.md). Do NOT generalize "runtime flux constants decouple from the model": it holds for EPA/IWW α, FALSE for EVA.

## Pre-PDF checks in eva_get_pdf_by_PID (:31-187)
Run in order before any flux is computed (each returns 0 or stops):

1. **x range** (:61-65): `x<1e-8 .or. x>1-1e-8` → print "eva: x out of range", return 0.
2. **fLpol range** (:67-72): `fLpol<0 .or. fLpol>1` → **`stop 1113`**. fLpol comes from `pol(beamid)` (polbeam1/2, see beam-pdf-params.md); unpolarized = 0.5.
3. **vPID select + per-boson mu2min and xcut** (:75-133):
   - `vPID=±12,±14` (ν): `mu2min=eva_mw2`; `|vPol|≠1` → `stop 1214`. (NO xcut.)
   - `vPID=23` (Z): `xMin = eva_mz*eva_xcut/ebeam`; `mu2min=eva_mz2`; if `x<xMin` → **return 0** (the eva_xcut gate); `|vPol|∉{0,1}` → `stop 23`.
   - `vPID=24` (W): `xMin = eva_mw*eva_xcut/ebeam`; `mu2min=eva_mw2`; if `x<xMin` → **return 0**; `|vPol|∉{0,1}` → `stop 24`.
   - `vPID=7,22` (γ): `mu2min` = parent-fermion mass² via `eva_get_mf2_by_PID(mu2min,fPID)`; `|vPol|≠1` → `stop 25`. (NO xcut — photon is massless.)
   - default → "vPID out of range", `stop 27`.
4. **scale floor** (:135-141): if `ievo_eva≠0` (pT² evolution), `mu2min = (1-x)*mu2min` first. Then if `mu2 < mu2min`: **print "muf2 too small. setting muf2 to muf2min" and silently raise `mu2 = mu2min`**. So a μF below the boson mass is auto-bumped UP per event.
5. **QED charge conservation** (:142-151): for `|vPID|=24` (W), `QW=sign(vPID)`; if `|Qf(fPID) - QW| > eva_one` → "QED charge violation", `stop 24`.
6. **neutrino-flavor match** (:152-178): vPID=12 requires fPID=11, -12→-11, 14→13, -14→-13, else `stop 1211/1413/1415`.

## Dispatch to the polarized flux (:180-187)
- `|vPID|∈{7,22}` → `eva_get_pdf_photon_evo`
- `|vPID|∈{12,14}` → `eva_get_pdf_neutrino_evo`
- default (Z/W) → `eva_get_pdf_by_PID_evo`

### eva_get_pdf_by_PID_evo (:194-225) — massive V (Z/W)
Switches on `vpol`: `-1`→`eva_fX_to_vm` (V−), `0`→`eva_fX_to_v0` (V₀, longitudinal), `+1`→`eva_fX_to_vp` (V+). Couplings gg2/gL2/gR2 set by PID; passes `evaorder` (0=LLA,1=LP,2=NLP) through. The longitudinal V₀ branch is the LP/NLP-sensitive one.

### eva_get_pdf_photon_evo (:228-257) — photon
**`tmpevaorder = 0` always** (:245, comment "always use LLA since m_photon = 0") — the photon flux IGNORES evaorder and is always LLA, regardless of the run-card `evaorder`. Only vpol ±1 (no longitudinal photon).

### eva_get_pdf_neutrino_evo (:262-301) — neutrino
fL/fR via `eva_fX_to_fL`/`eva_fX_to_fR`; carries evaorder.

## Cautions
- **eva_xcut only gates Z and W** (massive bosons), not photon or neutrino. With `eva_xcut=1` (default) a Z/W flux is hard-zeroed for `x < MV/ebeam` (recovers 2502.07878); `eva_xcut=0` sets xMin=0 so the cut never fires (recovers 2111.02442). This is the precise meaning of the run-card switch (scale-params.md names it; this is where it bites).
- **μF auto-raise is silent-ish**: μF below the boson mass is bumped to mu2min every event with a stderr print — a μF set far below MW/MZ is effectively overridden, not honored. The `ievo_eva≠0` case lowers the floor to `(1-x)*mu2min`.
- **evaorder is a no-op for photon beams' photon flux** — setting evaorder=1/2 changes Z/W/longitudinal fluxes but not the photon flux. Don't expect an evaorder effect on a γ-only EVA process.
- Multiple `stop` codes (1113/1214/23/24/25/27/1211/1413/1415) are EVA-internal: a crash with one of these is a beam/PID/charge mismatch in the EVA setup, not a generic PDF error. RUNTIME stops — text/codes read from source, not probe-verified here.
