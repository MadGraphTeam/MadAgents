---
description: FKS_params.dat template + defaults (IRPoleCheckThreshold, PrecisionVirtualAtRunTime registered in FKSParams.f90 — read there); the real(FKS)-vs-virtual(OLP) IR pole-cancellation check; getpoles pmass-keyed residue; negative-threshold disable at TWO sites; "Poles do not cancel" trigger; root-cause taxonomy (flavor-scheme YES, resonance NO).
---

# FKS IR pole-cancellation check and FKS_params.dat

The core FKS IR-cancellation diagnostic: the single/double 1/eps poles of the
FKS integrated subtraction counterterms (MadFKS) must cancel the poles of the
one-loop virtual (OLP / MadLoop). This is checked at runtime and gated by
parameters in `FKS_params.dat`. v3.7.1.

## FKS_params.dat template + defaults
Template lives at `Template/NLO/Cards/FKS_params.dat` (copied into
`<PROC_DIR>/Cards/`) and `Template/NLO/SubProcesses/FKS_params.dat`. Parsed by
`Template/NLO/SubProcesses/FKSParams.f90` (`FKSParamReader`). Format is
`#ParamName` line then value line.

Defaults set in `FKSParams.f90:DefaultFKSParam` (`:218-`) — read the value fresh at
each cited line, do not recall it (defaults drift across versions):
- `IRPoleCheckThreshold` (`:222`) — relative tolerance for pole cancellation. Read
  the default at `FKSParams.f90:222` / `FKS_params.dat` `#IRPoleCheckThreshold`.
- `PrecisionVirtualAtRunTime` (`:224`) — target MadLoop accuracy at run time (used as
  `tolerance` for `sloopmatrix_thres` once the initial pole check is done,
  `BinothLHA.f:182`). Read the default at `FKSParams.f90:224` / `FKS_params.dat`
  `#PrecisionVirtualAtRunTime`.
- Other registered defaults (read at `FKSParams.f90:218-`): `NHelForMCoverHels`,
  `Virt_fraction`, `Min_virt_fraction`, `QED_squared_selected` / `QCD_squared_selected`
  (`-1` = not-selected sentinel), `use_poly_virtual` (`.true.`).
The card template (`FKS_params.dat`) carries the same defaults with `! Default ::`
comments — read the numeric defaults there rather than caching them here.

Validation on read (`FKSParams.f90:43-51`): both `IRPoleCheckThreshold` and
`PrecisionVirtualAtRunTime` must be `>= -1.0d0`; value `< -1.01d0` → `stop`.
So **-1.0d0 is the minimum allowed value**, and it is the disable sentinel.

## The pole check (BinothLHA.f)
`getpoles` returns the MadFKS single/double pole residues (`madfks_single`,
`madfks_double`); MadLoop returns the OLP poles (`single`, `double` from
`amp_split_poles_ML`). Comparison per split-order (`BinothLHA.f:337-350`):
```
avgPoleRes = (ML + FKS)/2 ;  PoleDiff = |ML - FKS|
cpol = .not.( (PoleDiff_single+PoleDiff_double)/(|avgPoleRes|...) < tolerance*10d0
              .or. ret_code==7 )
if (tolerance.lt.0.0d0) cpol = .false.   ! :348-350 negative disables
```
where `tolerance = IRPoleCheckThreshold/10d0` for the first-PS-point pole check
(`BinothLHA.f:143`). `polecheck_passed = .not.cpol` (set true at `:310`, false at
`:441`). Pole check runs for the first PS point (MC over helicities) or every
point (sum over helicities), skipping MadLoop init points.

## "Poles do not cancel" trigger
The standalone `check_poles` executable (`Template/NLO/SubProcesses/check_poles.f`)
drives the check with `IRPoleCheckThreshold` as `tolerance_default` (`:90`); a
user-entered negative tolerance falls back to the default (`:117-121`). Per point
(`check_poles.f:250-262`):
```
if (tolerance.lt.0.0d0) then
   write(*,*) 'PASSED', tolerance          ! negative → unconditional PASS
else if (polecheck_passed) then 'PASSED' else 'FAILED', nfail++
```
Python parses `check_poles.log`: `parse_check_poles_log`
(`amcatnlo_run_interface.py:5726-5750`) — if `nfail/(nfail+npass) > 0.1` →
`raise aMCatNLOError('Poles do not cancel, run cannot continue')` (`:5746`).
So the failure gate is **>10% of tested points failing**, each failure decided
against `IRPoleCheckThreshold`.

## Negative-threshold disable — TWO sites (VBF/VBS workaround)
`set FKS_params IRPoleCheckThreshold -1.0d0` disables the check at both:
1. `BinothLHA.f:348-350` — negative tolerance forces `cpol=.false.` (poles
   declared cancelled at the integration level).
2. `check_poles.f:250-251` — negative tolerance forces `'PASSED'` for every point.

This is the known workaround for processes (VBF/VBS with pentagon diagrams carrying
non-QCD internal particles W/Z/γ/H) where MG filters some UV-finite pentagon
contributions (<1% effect) that nonetheless spoil an exact pole cancellation,
tripping the check spuriously. Disabling is safe there because the missing piece
is genuinely negligible and finite. (The pentagon-filtering itself is a
diagram-generation/MadLoop-side action — confirm the filter mechanism with
madloop; the FKS-side fact is the disable sentinel and its two enforcement sites.)

## What the FKS pole residue actually IS (getpoles, fks_singular.f:7534)
`getpoles(p,xmu2,double,single,fksprefact)` builds `madfks_single/double` as the
**integrated-counterterm (I-operator) poles**, NOT from any real-emission diagram.
It is `sborn`(Born) × per-external-leg color/charge pole coefficients
(`c(aj)` soft/double, `gamma(aj)` collinear/single from `common/fks_colors/`,
`:7555-7556`). The residue loops external legs (`:7623-7637` QCD, `:7653-7666`
QED) and is **keyed per leg on `pmass(i).eq.ZERO`**:
- **massless leg** (`pmass(i).eq.ZERO`, `:7630`/`:7655`) → contributes BOTH the
  soft double pole (`contr2-=c(aj)`) AND the collinear single pole
  (`contr1-=gamma(aj)`).
- **massive leg** (`else`, `:7633-7634`/`:7662-7663`) → contributes ONLY the soft
  single pole (`contr1-=c(aj)`); NO collinear pole.

Two consequences that settle the taxonomy below:
1. The FKS pole side is a function of {Born, external-leg masses, color/charge},
   evaluated at the Born phase-space point. A **resonant propagator inside a real
   diagram never enters getpoles** — resonances are not soft/collinear and produce
   no 1/eps pole. (Mirrors the Python side: `find_splittings` enumerates only
   soft/collinear splittings via `soft_particles`, splittings-and-real-generation.md.)
2. The collinear (single) pole of an initial parton is emitted **iff that parton is
   massless**. This is the same massless-keying as the Python soft classification
   (soft-particle-classification.md, `fks_common.py:516-567`).

## Root-cause taxonomy of "Poles do not cancel" (corrects a common myth)
**Immediate mechanism is ALWAYS** `madfks_{single,double}` ≠ OLP `{single,double}`
(BinothLHA.f:337-350). That much is true. But the ROOT CAUSE is NOT exclusively a
real/virtual generation bug — the claim *"always real/virtual, never a PDF or
param issue"* is FALSE, because the FKS pole side (getpoles above) depends on
**external-leg masses**, which must be coherent with the PDF flavor scheme and the
model's mass assignments:

- **Flavor-scheme incoherence — REAL cause (massive b × 5F PDF).** With a 5-flavor
  PDF the b-density is generated by DGLAP `g→bb̄`, so the ISR collinear-b pole must
  be present and cancel. But if the model keeps b MASSIVE (`import model sm`, b in
  `pmass≠ZERO`): (a) getpoles emits NO collinear-b single pole for the b leg
  (`:7633`), and (b) `find_splittings` does NOT enumerate the `g→bb̄` real config —
  the gluon-split interaction pops the gluon, remaining `[b,b̄]` give `nsoft=0`
  because massive b ∉ `soft_particles` (`fks_common.py:279-282`) → no `g→bb̄`
  counterterm. `b→bg` (b radiates a gluon) IS still enumerated (`nsoft` counts the
  massless gluon). The result is an unmatched initial-state collinear sector →
  poles do not cancel. **A PDF/flavor choice absolutely causes this error.** (This
  is my cached flavor-scheme mechanism; see also lead flavor-scheme-coherence-nlo.)
- **param-card path.** getpoles keys on `pmass` (from the loaded model / masses).
  A mass set inconsistently relative to how the OLP loop treats that leg shifts the
  FKS pole coefficients — so a mass/param incoherence can also trip it. Less common
  than the flavor-scheme case but not excluded.
- **Genuine real/virtual bug** (the "always real/virtual" case) — a filtered/missing
  finite pentagon (VBF/VBS above), an OLP inconsistency, etc. Real, but ONE cause
  among several, not the only one.

### Resonant top propagators do NOT cause "Poles do not cancel" (myth correction)
A frequently-stated cause — *"b-initiated reals like `b g > w+ w- b` contain
on-shell top propagators (`b g > t w-, t > w+ b`) absent at Born; these resonant
contributions have IR singularities the virtual doesn't match, breaking FKS"* — is
**false on FKS mechanics**:
- An on-shell top propagator is a **Breit-Wigner resonance** (integrable, regulated
  by Γ_t, clipped by `bwcutoff` in phase space), NOT a soft/collinear singularity.
  It produces NO 1/eps pole and never enters getpoles or the OLP pole comparison.
- FKS does NOT require real singular limits to "arise from Born topologies." It
  enumerates soft/collinear splittings of Born legs and subtracts exactly those
  limits; extra non-singular real structure (a resonance) is simply left un-subtracted
  and is finite — it does not "break the subtraction" or spoil pole cancellation.
- The tt̄/tW (or WW/tW) resonant-overlap in `p p > w+ w-` 5F reals IS a real physics
  concern, but it is a **double-counting / overlap** issue handled by DR/DS
  (MadSTR plugin, dr-ds-resonance-madstr.md) and by `bwcutoff` — a DISTINCT axis
  from pole cancellation. Conflating the two is a common error.

**So the resonant-top mechanism and the flavor-scheme mechanism
(massive-b × 5F-PDF missing g→bb̄) are DISTINCT — and only the latter actually
produces "Poles do not cancel."**

## Fix = 4-flavor scheme — FKS-side rationale is SOUND
Switching to 4FS (redefine `p`/`j` to exclude b, `maxjetflavor=4`, 4F PDF, diagonal
CKM) restores coherence on the FKS side: b is massive AND not a beam parton, so
there is no `g→bb̄` PDF/DGLAP counterterm to cancel and no b-initiated collinear
sector — getpoles' massless set = {u,d,s,c,g} matches the PDF's active flavors and
the b never needs a collinear pole. Note the slice split: `maxjetflavor` is a
run_card knob read Fortran-side at runtime (ma-kinematic-cuts / amcatnlo owns it);
the massless/soft classification is driven by the MODEL's b-mass at generation time
(soft-particle-classification.md); diagonal CKM is a param-card/model matter. FKS
enforces NONE of this coherence itself — it is a whole-spec invariant the user must
set consistently. `IRPoleCheckThreshold=-1` MASKS the symptom (declares PASS with
uncancelled poles, §"Negative-threshold disable"); it does NOT fix it — integrating
an amplitude whose 1/eps poles do not cancel yields a regulator/scheme-dependent,
physically meaningless finite remainder (INFERRED from the pole structure; the
"abnormally large NLO K-factor" symptom is a runtime/physics observation, not a
source fact).
