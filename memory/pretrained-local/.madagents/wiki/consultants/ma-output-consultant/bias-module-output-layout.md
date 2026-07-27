---
description: Biased event generation — the Source/BIAS/ template tree output lays down (dummy + ptj_bias), the bias_wgt subroutine contract, the /bias/ common block, and where custom modules are looked up. NOT SubProcesses/BIAS.
---

# Bias-module output layout (biased event generation)

The BIAS machinery is a **Source-tree** artefact copied verbatim into the process dir by
`copy_template` (whole `Template/LO` copy — see template-copy-mechanics.md). Facts below are
source-grounded against v3.7.1.

## Path — Source/BIAS, NOT SubProcesses/BIAS
Sometimes assumed to land at `SubProcesses/BIAS/`; it is `Source/BIAS/`. The template lives at
`$MADGRAPH_INSTALL/Template/LO/Source/BIAS/` → lands at `<PROC_DIR>/Source/BIAS/`.
Two built-in modules, each its own subdir with a `<name>.f` + `makefile`:
- `Source/BIAS/dummy/{dummy.f,makefile}`
- `Source/BIAS/ptj_bias/{ptj_bias.f,makefile}`

Runtime lookup corroborates the path: `madevent_interface.py:3286` builds `bias_module_path =
pjoin(me_dir,'Source','BIAS', basename(run_card['bias_module']))`. (That do_treatcards block is
launch/run_card territory, not output — cited only to pin the path.)

## The bias_wgt contract (module-intrinsic; holds in both built-in templates)
Mandatory subroutine name is **`bias_wgt`**.
- `ptj_bias.f:21`: `subroutine bias_wgt(p, original_weight, bias_weight)`; `:32` `double precision p(0:3,nexternal)`.
- `dummy.f:6,15`: same name but arg typed `double precision p(*)` (looser); dummy just calls
  `bias_wgt_custom(p,...)` (`dummy.f:42`) — that custom hook maps to `SubProcesses/dummy_fct.f`
  (`banner.py:4199` `"bias_wgt_custom": SubProcesses/dummy_fct.f`).

## Mandatory /bias/ common block (verified ptj_bias.f:51-60, dummy.f:25-36)
```
double precision stored_bias_weight   ! data /1.0d0/
logical impact_xsec, requires_full_event_info
common/bias/stored_bias_weight,impact_xsec,requires_full_event_info
```
- `impact_xsec`: `.False.` in ptj_bias (bias distributions only, weight written to LHE), `.True.`
  in dummy (bias≡1, weight NOT written).
- `requires_full_event_info`: `.False.` in both (no color/resonance/helicity needed).

## ptj_bias physics (ptj_bias.f)
- Loops externals, `ptj(i)=sqrt(px^2+py^2)` only where `is_a_j(i)` (jet flag from
  `common/to_specisa/` :64-69); takes `max_ptj` over them = hardest-jet pT (:80-90).
- If no jet (`max_ptj<0`) → `bias_weight=1.0d0` (:91-94).
- Formula (:96-97): `bias_weight = (max_ptj/ptj_bias_target_ptj)**ptj_bias_enhancement_power`.

## Parameters — declared in a header COMMENT, injected via bias.inc
- Names + defaults live in the `C  parameters = {...}` header comment (`ptj_bias.f:17-18`):
  keys `ptj_bias_target_ptj` and `ptj_bias_enhancement_power` — read their default values fresh at `ptj_bias.f:17-18`.
- In-body they are plain local `double precision` (`:43-44`), given values by
  `include '../bias.inc'` (`:74`) → resolves to `Source/BIAS/bias.inc`.
- `bias.inc` is written from run_card: `banner.py:4280`
  `add_param('bias_parameters', {'__type__':1.0}, include='BIAS/bias.inc', hidden=True)`;
  `bias_module` param at `banner.py:4279` default `'None'`.
- Runtime parse of the header comment: `madevent_interface.py:3302-3339` (regex
  `c\s*parameters\s*=\s*{` :3305), then merges run_card `bias_parameters`, warning on unsupported keys.

## Build
- `madevent_makefile_source:57-58`: `libbias.$(libext): BIAS/dummy` → only **dummy** built by
  default into `libbias`; a non-dummy module named in run_card is compiled by MG5aMC directly at
  run time (comment :56). Each makefile has a `requirements` target that must echo `VALID`
  (checked `madevent_interface.py:6197-6203`).

## Custom-module contract (run_card `bias_module` = dir path)
Custom dir must contain `makefile` + `<basename>.f` (`madevent_interface.py:3292`); it is
`copytree`'d into `Source/BIAS/<basename>` (`:3296`). The `.f` must define `bias_wgt` with the
`/bias/` common block and a `C parameters = {...}` header for any tunable params.

## Not the bias module
`flavour_bias` (`banner.py:5709`, NLO run_card) is a SEPARATE flavour-enhancement machinery — not
the bias-module system.

## Easy-to-miss nuances
- The path is `Source/BIAS/`, not `SubProcesses/BIAS/` (`madevent_interface.py:3286`).
- `dummy.f` types the momentum arg `p(*)`, not `p(0:3,nexternal)` as in `ptj_bias.f`.
- Parameter defaults live in a `C parameters = {...}` header comment (not a Fortran declaration)
  and are injected via `bias.inc`.
