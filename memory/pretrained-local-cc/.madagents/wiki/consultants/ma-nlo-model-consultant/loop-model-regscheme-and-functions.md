---
description: Non-CT-vertex model content a loop UFO must carry - the regularization-scheme params (lhv HV/FDH switch, MU_R renorm scale in LOOP block, MU_R special-cased as PS-dependent at export) and the dim-reg-safe loop-function vocabulary (reglog/cond/recms/...) the UFO expression parser recognizes and export declares as Fortran intrinsics.
---

# Loop-model regularization-scheme params + loop-function vocabulary

(v3.7.1, `$MADGRAPH_INSTALL`, model = loop_sm.) Beyond the three CT files
(ct-files-and-vertex-types) and the `perturbative_expansion` flag (loopmodel-detection),
a loop-capable UFO must carry TWO further kinds of non-vertex content that CT expressions
depend on. Neither is in a tree UFO. This page records both, plus how the export consumes
them.

## (a) Regularization-scheme parameters

`$MADGRAPH_INSTALL/models/loop_sm/parameters.py`:
- **`lhv`** (18-22): `Parameter(name='lhv', nature='internal', type='real', value='1.0',
  texname=r'\lambda_{HV}')`. Comment above it (16): "# Loop related parameters". This is the
  't Hooft-Veltman vs FDH regularization-scheme switch (`\lambda_{HV}`): `1.0` = HV scheme,
  `0.0` = FDH. It is used ONLY inside CT expressions (e.g. `R2_3Gg
  value='Ncol*G**3/(48.0*cmath.pi**2)*(7.0/4.0+lhv)'`); occurrence counts drift —
  `grep -c lhv CT_couplings.py CT_parameters.py`.
  `grep lhv` over `madgraph/loop/*.py` returns NOTHING: MadGraph source never reads `lhv`;
  it is a pure model-internal scheme dial. Switching to FDH means editing the UFO value.
- **`MU_R`** (48-55): `Parameter(name='MU_R', nature='external', type='real', value=<default>,
  lhablock='LOOP', lhacode=[1])`. The renormalization scale. External, in the `LOOP` param-
  card block, code 1 (read the default at `parameters.py:48-55`, or the `LOOP` block of a
  generated `param_card.dat` — drift-prone number). Referenced in CT_parameters.py's UV logs
  (`...reglog(MT**2/MU_R**2)...`; count via `grep -c MU_R CT_parameters.py`).

## MU_R is special-cased throughout the export (PS-dependent)

`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py` treats MU_R like `aS` (recomputed per
phase-space point), unlike any ordinary external param:
- **6886** `PS_dependent_key = ['aS','MU_R']` — the docstring (6882-6885) calls these "the
  only variables the user is allowed to change by himself for each PS point. If he changes
  any other, then calling UPDATE_AS_PARAM() ... will not correctly account for the change."
- **7272-7273** MU_R gets its own Fortran common block: `double precision MU_R, all_mu_r` /
  `common/rscale/ MU_R, all_mu_r` (and `common/MP_rscale/ mp_MU_R` for quad precision,
  7297-7298).
- **7444** `is_valid = lambda name: name.lower() not in ['g','mu_r','zero'] ...` — MU_R is
  excluded from generic param handling alongside the strong coupling and ZERO.
- **9724-9726** comment: "it is hardcoded that only AS and MU_R can by dynamically changed by
  the user so that we only update those ones." `update_params_list` = ext params whose name
  is in `PS_dependent_key` (9728-9729). `update_as_param2(mu_r2,as2,...)` (7962) sets
  `MU_R = DSQRT(mu_r2)` when mu_r2>0 (7983).

So a loop UFO's MU_R is the renormalization scale the FKS/MadLoop runtime varies per event;
declaring it external in the LOOP block is the requirement that wires it to the param card,
and the export's PS-dependent special-casing is what lets it be recomputed per PS point.

## (b) The dim-reg-safe loop-function vocabulary

`$MADGRAPH_INSTALL/models/loop_sm/function_library.py` adds two loop-specific `Function`
objects the tree sm lacks (loop_sm's file is longer than tree sm's for exactly these):
- **`cond`** (40-42): `arguments=('condition','ExprTrue','ExprFalse')`,
  `expression='(ExprTrue if condition==0.0 else ExprFalse)'`. The CT-expression conditional
  (used to branch on a mass being zero vs nonzero: `cond(MC,0.0,...)` = "0 if MC==0 else ...").
  Occurs in CT_parameters.py (`grep -c "cond(" CT_parameters.py`).
- **`reglog`** (44-46): `arguments=('z')`, `expression='(0.0 if z==0.0 else cmath.log(z))'`.
  The dim-reg-SAFE log: `reglog(0)=0` instead of `-inf`, so a massless-limit log term drops
  cleanly. Occurs in CT_parameters.py (`grep -c "reglog" CT_parameters.py`).
- (sm has only complexconjugate/re/im/sec/csc/asec/acsc; loop_sm adds cond+reglog.)

### The parser recognizes a FIXED loop-function grammar
`$MADGRAPH_INSTALL/madgraph/iolibs/ufo_expression_parsers.py` lexes these as dedicated
tokens (regex `(?<!\w)<name>(?=\()`), NOT generic function calls: `reglog` (97), `reglogp`
(100), `reglogm` (103), `recms` (106), `cond` (109), `arg` (112). Fortran translation rules:
- `reglog(X)` -> `reglog(DCMPLX X)` double prec (421), `mp_reglog(CMPLX(X,KIND=16))` quad (728).
- `cond` -> emits `condif`/`cond` to `to_define` (379-382); `recms` -> `recms` (384-387).

### Export declares them as Fortran intrinsics
`export_v4.py:8475-8500` `model_functions.inc`: a model `Function` whose name is in the
built-in set is NOT re-emitted (it's "already handle by default", 8478). The built-in set
(8479-8483): `complexconjugate, re, im, sec, csc, asec, acsc, theta_function, cond, condif,
reglogp, reglogm, reglog, recms, arg, grreglog, regsqrt, B0F, b0f, sqrt_trajectory,
log_trajectory`. The .inc then declares each as `double complex` (8488-8499) plus `mp_*`
quad-precision counterparts (8503-8520 when `opt['mp']`). Only NON-built-in model functions
go into `additional_fct` and get user-emitted.

So the loop-function vocabulary is a fixed MadGraph-side contract: a loop UFO writes its CT
expressions in terms of `reglog`/`cond`/`recms`/etc., and MadGraph supplies the matching
Fortran (`double complex reglog`, etc.) at output. `regsqrt`, `grreglog`, `B0F`,
`sqrt_trajectory`, `log_trajectory` are in the built-in list but unused by loop_sm — they
support other loop models' renormalization expressions.

## Cautions
- `lhv` is model-internal: MadGraph never reads it, so there is no command-line FDH/HV
  switch — the scheme is fixed by the UFO's `lhv` value (1.0 in loop_sm = HV). Don't tell a
  user to "set the scheme in a card"; it is baked into the model.
- MU_R's PS-dependent special-casing means a hand-set MU_R in the LOOP block is OVERWRITTEN
  per phase-space point by the runtime scale machinery (update_as_param2). The LOOP-block
  value is effectively a default/initialization, not the per-event scale. (The runtime scale
  choice itself is scales-pdf / FKS slice territory — this page only records the export-side
  PS-dependent flag.)
- These are STATIC source facts (param declarations, parser grammar, .inc declarations).
  They predict WHICH params/functions a loop UFO must carry and how they're emitted, not
  runtime numerics. The MU_R per-event overwrite is source-confirmed at the export site;
  whether a given run varies it is a runtime/scales question, not asserted here.
