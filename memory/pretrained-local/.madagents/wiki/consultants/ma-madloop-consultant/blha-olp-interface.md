---
description: BLHA one-loop-provider interface — OLE_order.lh/.olc order+contract files, OLP config (MadLoop default / GoSam), internal-vs-external Fortran driver split (BinothLHA.f sloopmatrix_thres vs BinothLHA_OLP.f OLP_Start/OLP_EvalSubProcess), virt_wgts ordering, output_dependencies (MG5_aMC v3.7.1)
---

# BLHA OLP interface + output_dependencies

How MadFKS obtains the one-loop (virtual) matrix element: either MG5's own MadLoop (internal, the default) or an external OLP through the Binoth-Les-Houches-Accord (BLHA) interface.

## OLP selection (`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`)
- `_OLP_supported = ['MadLoop', 'GoSam']` (:3038). Default `'OLP': 'MadLoop'` (:3090). Set via `set OLP GoSam` (:8592 `set2_OLP`, help :8578). GoSam is the ONLY supported external OLP in v3.7.1 — no OpenLoops entry despite the help text mentioning "e.g., GoSam, OpenLoops" (:8595).
- Guard: cannot `set OLP` != MadLoop together with `low_mem_multicore_nlo_generation` under python3 (:8757-8758, :8603).

## BLHA order + contract files (`$MADGRAPH_INSTALL/madgraph/iolibs/export_fks.py`)
Two-file handshake:
- **`OLE_order.lh`** — the ORDER file, written BY MG5 for the OLP. `write_lh_order` (:2545, `OLP='MadLoop'` default arg) emits a generic BLHA1 order file (:2591-2605): `MatrixElementSquareType CHaveraged`, `CorrectionType <perturbation>` (e.g. `QCD`), `IRregularisation CDR`, `AlphasPower`, `AlphaPower`, `NJetSymmetrizeFinal Yes`, `ModelFile ./param_card.dat`, `Parameters alpha_s`, then `# process` lines `<in-pdgs> -> <out-pdgs>`. Written at :508 / :2285.
- **`OLE_order.olc`** — the CONTRACT file, returned BY the OLP (the answer to the order). Linked into SubProcesses (:2353-2359); its existence checked before proceeding (:2395 error "OLE_order.olc in ..."). At runtime the launcher stages it as an input file (`amcatnlo_run_interface.py:5171-5172`).

## Internal vs external Fortran driver (`$MADGRAPH_INSTALL/Template/NLO/SubProcesses/`)
The per-PS-point virtual eval lives in one of two mutually-exclusive files:
- **`BinothLHA.f`** — the INTERNAL MadLoop path (default). Calls `sloopmatrix_thres(p, virt_wgts, tolerance, accuracies, ret_code)` (:144, :187) and the single-helicity `sloopmatrixhel_thres` (:215) — MadGraph's OWN entry points (loop_matrix.f), NOT standard BLHA subroutines. This is the "BLHA-inspired but internal" architecture: MadFKS talks to MadLoop through a native call, not through `OLP_EvalSubProcess`.

### The `tolerance` argument = MadLoop runtime precision target (FKS_params.dat knobs)
`tolerance` is the `PREC_ASKED` passed to `sloopmatrix_thres` — the relative accuracy MadLoop must reach; if the DP result is worse, MadLoop escalates DP→QP internally (see loop-matrix-runtime-driver). Its value depends on which BinothLHA.f branch runs:
- **Initial-pole-check phase** (:143): `tolerance = IRPoleCheckThreshold/10d0`.
- **Steady-state eval** (:182, the `else` branch + both `mc_hel` paths): `tolerance = PrecisionVirtualAtRunTime`.
Both are read from `Cards/FKS_params.dat` (`PrecisionVirtualAtRunTime` default at FKS_params.dat:36; `IRPoleCheckThreshold` default in the same card — read both fresh, magnitudes drift). The runtime IR-pole check compares `PoleDiff` against `tolerance*10d0` (:346-348, :443) — i.e. **10× looser** than the precision target (matches the FKS_params.dat:31-34 comment). Setting `PrecisionVirtualAtRunTime = -1d0` (sentinel) uses the OLP's own default precision AND disables the runtime pole check (:351 `if (tolerance.lt.0.0d0)`).
- **Direction trap (inverted):** "increase `PrecisionVirtualAtRunTime` to re-evaluate flagged points at higher precision" is BACKWARDS. `tolerance` is a target accuracy — a SMALLER numeric value demands better accuracy ⇒ more DP→QP escalation ⇒ higher precision. To force higher-precision re-evaluation you DECREASE the value (toward a smaller magnitude); increasing it LOOSENS the requirement. Tightening the virtual precision is the right remedy for unstable points; only the arithmetic direction (increase vs decrease) is the pitfall.
- **`BinothLHA_OLP.f`** — the EXTERNAL OLP path (GoSam etc.), standard BLHA1 subroutines:
  - `OLP_Start(filename//Char(0), ierr)` in `BinothLHAInit` (:128) with `filename='OLE_order.olc'` (:126) — initializes the OLP from the contract file; `ierr==0` ⇒ init failed ⇒ stop.
  - `OLP_EvalSubProcess(proc_label, p, mu_r, alpha_S, virt_wgts)` (:67) — evaluates one subprocess.

## virt_wgts ordering (BOTH paths, verified `BinothLHA_OLP.f:67-71`, comment :60-61)
`virt_wgts(1..4)` = **(double pole 1/eps², single pole 1/eps, finite, Born |M|²)**:
```
double   = virt_wgts(1)   ! 1/eps^2 coefficient
single   = virt_wgts(2)   ! 1/eps   coefficient
virt_wgt = virt_wgts(3)   ! finite part
born     = virt_wgts(4)   ! Born |M|^2
```
Comment: "virt_wgts contains finite part, single and double pole and the Born." MadLoop returns already in CDR scheme (no DR→CDR conversion needed; the DRtoCDR path :137 is dead for MadLoop, :77). Pole cancellation is cross-checked against MadFKS's own `getpoles` at IRPoleCheckThreshold (:87-116, FKS_params.dat), stopping after nbadmax failures.

## output_dependencies (`madgraph_interface.py`)
- `_output_dependencies_supported = ['external', 'internal', 'environment_paths']` (:3039). Default **`'external'`** (:3094). Set via `set output_dependencies <mode>` (:8628).
- Governs how the process dir links to reduction/loop dependencies (CutTools, StdHep, etc.): `external` = symlink to the MG5 install copies (default); `internal` = compile local copies inside the process dir (needed for a self-contained/portable output — `amcatnlo_run_interface.py:5567-5597` makes StdHep + CutTools locally only under `internal`); `environment_paths` = resolve via environment paths.

## Cautions
- The internal path is NOT literally BLHA: it never calls `OLP_Start`/`OLP_EvalSubProcess`. Only `BinothLHA_OLP.f` (external OLP) uses those. Do not claim MadFKS↔MadLoop goes through standard BLHA subroutines. (verified)
- `write_lh_order` is labelled "generic" (:2547) — the order file content is OLP-agnostic; a real external OLP integration edits it per the OLP's needs.
