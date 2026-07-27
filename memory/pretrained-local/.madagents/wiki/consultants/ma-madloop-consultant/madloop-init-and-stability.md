---
description: do_initMadLoop runtime init machinery — init_MadLoop / run_initialization (HelFilter/LoopFilter, nPS/-r/-f, DP→QP fallback) / need_MadLoopInit / MadLoopInitializer helpers (make_and_run, fix_PSPoint_in_check check_sa.f regex-config) + the StabilityCheckDriver.f per-point ME evaluator (madevent_interface.py / Template/loop_material, MG5_aMC v3.7.1). The MadLoopParams runtime-knob reference + SA override + Fortran parser are split out to ./madloop-params-runtime-knobs.md.
---

# MadLoop initialization + stability check

## do_initMadLoop (`$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py` :2722)
Compiles + runs MadLoop on random (RAMBO) PS points to build the helicity and loop filters.
- `check_initMadLoop` (:1088-1106) knobs: `-r`/`--refresh` (delete existing `*Filter*` files in MadLoop5_resources, :2734-2738), `-f`/`--force` (skip the MadLoopParams.dat card edit prompt, :2730-2732), `--nPS=<int>` (override #PS points).
- `:2742-2749` if nPS unset ⇒ `MLCard['CheckCycle']+2`; if below that floor it is hard-raised to it.
- Delegates to `MadLoopInitializer.init_MadLoop(..., subproc_prefix='PV')` (:7627).

## init_MadLoop (:7627-7725)
- Compiles Source: CutTools/IREGI libs if present, then libmodel + libdhelas (:7642-7649).
- Iterates `PV*` SubProcess folders (:7682), submits `run_initialization` per folder via cluster.MultiCore / onecore.
- Failure ⇒ `MadGraph5Error('Failed the initialization of loop-induced matrix element ...')` (:7710).

## run_initialization (:7449-7581) — the DP→QP fallback logic
(The QP routines this fallback switches into are always emitted at output time — `do_output` forces `aloha.mp_precision=True` regardless of format; see ./loop-interface-and-reduction-libs.md.)
- Required filter files: `HelFilter.dat`, `LoopFilter.dat` (:7450). `LoopFilter.dat` dropped if `MLCard['UseLoopFilter']` false; `HelFilter.dat` dropped if `HelicityFilterLevel==0` (:7507-7518).
- Default attempts (a [DP-count, QP-count]-style pair) at :7451 — read fresh. LOOP-INDUCED (no `born_matrix.f`) bumps the attempt counts higher (:7489-7493) because the zero-contribution reference scale is dynamic and needs more points.
- `:7537-7538` QP attempts (negative numbers) are PREPENDED automatically: `[-a for a in attempts] + attempts`. DP tried first (popped from reversed list), QP forced on failure.
- QP attempt (`curr_attempt<0`): sets `CTModeInit=4` (QP mode) and a tighter `ZeroThres`; DP: `CTModeInit=1` (DP mode) and the looser card `ZeroThres` (:7548-7556 — read the two ZeroThres magnitudes fresh).
- Returns `use_quad_prec*(curr_attempt-1)`: positive = #PS in DP, negative = QP (:7581).
- Original MadLoopParams.dat restored afterward (:7577).

## need_MadLoopInit (:7584-7624)
Returns True if any `PV*` folder lacks the required filter files (filter requirement same UseLoopFilter / HelicityFilterLevel logic). Reads `proc_prefix.txt` per folder.

## MadLoopInitializer helpers — compile/run + check_sa.f config (:7335-7447)
The two static helpers underneath `init_MadLoop`/`run_initialization`; also used by the loop check infra (./loop-check-infrastructure.md, which calls `fix_PSPoint_in_check`).
- `make_and_run(dir_name, checkRam=False)` (:7341): the compile+run primitive. DELETES stale `check`, `check_sa.o`, `loop_matrix.o` first (:7347-7350, "time stamps are sometimes not actualized if it is too fast") then `misc.compile(['-j1','check'])` and runs `./check`. `checkRam=True` ⇒ wraps in `misc.ProcessTimer` polling every .2s for `max_rss_memory` (:7368-7385). Returns `(compilation_time, run_time, ram_usage)`; `(None,None,None)` on make or run failure.
- `fix_PSPoint_in_check(dir_path, read_ps=True, npoints=1, hel_config=-1, mu_r=0.0, split_orders=-1)` (:7396): REGEX-rewrites `check_sa.f` in place to configure the standalone driver. This is the bridge that configures both init and the Python stability/timing check:
  - `READPS = .TRUE.|.FALSE.` (read PS from PS.input vs RAMBO) and `NPSPOINTS = <n>` (:7426-7428).
  - `hel_config != -1` ⇒ swaps the ME call to `SLOOPMATRIXHEL_THRES(P,<hel>,...)` (single helicity); else `SLOOPMATRIX_THRES(P,...)` (summed) (:7429-7434).
  - `mu_r>0` ⇒ hardcodes `MU_R=<value>d` (note `e`→`d`); `mu_r==0` ⇒ leaves `MU_R=SQRTS`; `mu_r<0` ⇒ blanks it so param_card value is used (:7435-7439).
  - `split_orders>0` ⇒ `SET_COUPLINGORDERS_TARGET(<n>)` (target squared coupling orders) (:7441-7443).
  - Locates `check_sa.f` from a bare path, a dir, or a `P*_*` subdir (:7408-7419).

## StabilityCheckDriver (`$MADGRAPH_INSTALL/Template/loop_material/Checks/`)
IMPORTANT framing correction: `StabilityCheckDriver.f` is NOT itself the Lorentz-rotation comparison program. It is an INTERACTIVE per-PS-point ME evaluator: reads from stdin a PS point, `CTMODERUN`, `MU_R`, helicity tag (-1=summed), split-order choice; outputs `BORN`, `FIN`, `1EPS`, `2EPS` (the loop/born ratio over a/2π) wrapped in `##TAG#RESULT_START#TAG##` … `STOP` (:118-131).
- The Lorentz-rotation comparison driving it lives in `$MADGRAPH_INSTALL/madgraph/various/process_checks.py` (`format_PS_point`, rotations 0-5: z-axis π/2, π/4, boost, axis permutations, :1411-1439) — that is the check-infrastructure layer, distinct from this Fortran driver.
- `StabilityCheckDriver_loop_induced.f` differs only in output: BORN/1EPS/2EPS hard-zeroed, `FIN`=`MATELEM(1,0)` (unnormalized, no born to divide by), `Export_Format LoopInduced` (verified by diff).

## Runtime knobs — split out
The `MadLoopParams.dat` default-card knob-by-knob reference (MLReductionLib/CTModeRun/MLStabThres/NRotations/ImprovePSPoint/CheckCycle/ZeroThres/HelicityFilterLevel/COLLIER/per-reducer), the SA Collier-first loop-induced override + MadEvent scope trap, the `MadLoopParamReader.f` Fortran parser (hard-stop, dead `DefaultParam()`), and the `!`-comment dual-side mechanism are in ./madloop-params-runtime-knobs.md. The init machinery on THIS page consumes those knobs: `CheckCycle+2` floors the nPS, `CTModeInit`/`ZeroThres` are overridden per DP/QP attempt by `run_initialization`, `UseLoopFilter`/`HelicityFilterLevel` decide which filter files are required.

