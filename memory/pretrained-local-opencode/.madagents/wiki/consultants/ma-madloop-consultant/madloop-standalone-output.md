---
description: MadLoop (ML5) standalone output structure + runtime contract — LoopProcessExporterFortranSA proc_prefix/SubProc naming, SLOOPMATRIX entry points + ANS(0:3,0:*) layout, MadLoop5_resources resolution/SETMADLOOPPATH, OLP_static→libMadLoop.a, do_output vs do_launch roles (MG5_aMC v3.7.1)
---

# MadLoop standalone (ML5) output + runtime contract

Loop process (`... [virt=QCD]`) `output <dir>` in the LoopInterface → a standalone MadLoop (ML5) evaluator directory. NOT a MadEvent integration dir; no born_matrix/event-generation machinery unless loop-induced+MadEvent (separate path, see ./loop-induced-and-has-born.md).

## output → standalone; default format is 'standalone'
- `LoopInterface.check_output(default='standalone')` (loop_interface.py:92) — ML5 default export format is `standalone`. `do_output` (:430) rejects any `_export_format` not in `supported_ML_format` (=standalone/standalone_rw/matchbox, :371; see ./loop-interface-and-reduction-libs.md).
- `do_output` → `ML5export` → `ML5finalize` (:717): does `convert_model` + `_curr_exporter.finalize(...)` — writes/copies the Fortran sources, ps diagrams. **It does NOT compile.** No make/compile call in ML5finalize; the emitted dir must still be built (via `make`, or via `launch`/`check` which invoke make).

## do_launch IS supported for standalone (corrects "output compiles, no launch")
- `do_launch` (loop_interface.py:756): `if not args[0].startswith('standalone'): raise InvalidCmd('ML5 can only launch standalone runs.')` (:766-767) — launch is EXPLICITLY supported (and only) for standalone. Uses `launch_ext.MadLoopLauncher` (:773).
- `MadLoopLauncher.launch_program` (launch_ext_program.py:185): loops `SubProcesses/P*`, runs `MadLoopInitializer.run_initialization` (HelFilter/LoopFilter init), then **`MadLoopInitializer.make_and_run(curr_path)` (:225) — this is the step that COMPILES (make) and evaluates** check_sa at one PS point; parses `result.dat`, prints (fin,born,spole,dpole,me_pow).
- So the real division of labor: **output = write source; launch (or manual `make`) = compile; launch = the built-in evaluate/check step.** The library can also be called directly by user code (see entry points below) after building.

## SubProcess directory + subroutine prefix naming
- `get_SubProc_folder_name` (loop_exporters.py:510): standalone case (group_number None) → `SubProc_prefix + process.shell_string()`. `SubProc_prefix='P'` (:86). `shell_string(print_id=True)` prepends `"%d_"%id` (base_objects.py:3441-3442), then legs, `>`→`_`. So `g g > z z @42` (id=42) → **`P42_gg_zz`**. (@N→process id is process-syntax's; the dir/prefix consuming it is ours.)
- `get_ME_identifier` (loop_exporters.py:488): standalone (no group) → **`'ML5_%d_'%id`** = `ML5_42_` (:505). [group forms :502/:507 are LoopInduced-MadEvent only.] Written to `proc_prefix.txt` (:1111-1114). All MadLoop subroutines/common blocks carry this prefix (BLHA multi-process-in-one-library requirement, docstring :492-494).

## Entry points (loop_matrix_standalone.inc, optimized template)
Subroutines are `%(proc_prefix)s...` → e.g. `ML5_42_SLOOPMATRIX`:
- `%(proc_prefix)sSLOOPMATRIX(P_USER, ANS)` (:5) — main; sum/avg over color+helicity. (arg is P_USER not P.)
- `%(proc_prefix)sSLOOPMATRIXHEL(P, HEL, ANS)` (:2780) — single-helicity (sets USERHEL, calls SLOOPMATRIX).
- `%(proc_prefix)sSLOOPMATRIXHEL_THRES(P, HEL, ANS, PREC_ASKED, PREC_FOUND, RET_CODE)` (:2806) — single-hel with stability/accuracy control.
- `%(proc_prefix)sSLOOPMATRIX_THRES(P, ANS, PREC_ASKED, PREC_FOUND, RET_CODE)` (:2867) — all-hel with stability control; doc block :2867-2918.
- **Signature note:** `PREC_ASKED` scalar (target rel accuracy, -1=default); `PREC_FOUND(0:NSQUAREDSO)` is an ARRAY not scalar; `RET_CODE=100*H+10*T+U` (H/T/U stability code, see ./loop-matrix-runtime-driver.md).

## ANS (RESULT) array layout — `ANS(0:3, 0:ANS_DIMENSION)`
- Declared `%(real_dp_format)s ANS(0:3,0:ANS_DIMENSION)`, `ANS_DIMENSION=MAX(NSQSO_BORN,NSQUAREDSO)` (loop_matrix_standalone.inc:132, :100-101).
- **First index 0:3** (docs :119-131, :2874 `ANS(3) :: Result (finite, single pole, double pole)`): `0`=Born; `1`=finite (virtual finite part); `2`=single pole 1/ε; `3`=double pole 1/ε². (ANS(0,I) set :704-723 from Born; ANS(1..3,I) are the loop finite+poles.)
- **Second index 0:ANS_DIMENSION** = squared-split-order (coupling-order combination) index; **`J=0` = sum over all contributing split orders** (docs :119-121). Upper bound is MAX of Born and loop NSQSO because the Born can have more split-order combos than the loop (example `u u~ > d d~ QCD^2<=2 QED^2<=99 [virt=QCD]`, :127-129).

## Runtime resource dependency — MadLoop5_resources + SETMADLOOPPATH
At runtime MadLoop must locate `MadLoop5_resources/` (holds `MadLoopParams.dat`, `<prefix>ColorNumFactors.dat`, `<prefix>ColorDenomFactors.dat`, `<prefix>HelConfigs.dat`, HelFilter/LoopFilter, param cards). Created by exporter at loop_exporters.py:416-421; symlinked into each P* dir as `../MadLoop5_resources` (:946 `ln('../MadLoop5_resources')`); dat files written there (:1595-1609).
- Auto-resolution (MadLoopCommons.inc SETMADLOOPPATH, :170-234): tries `./`, `./MadLoop5_resources/`, `../MadLoop5_resources/`, then executable-relative (`getarg(0)`) paths (gridpack readonly), else **`stop`** with "MadLoop5 could not automatically find MadLoopParams.dat" (:227-230) suggesting `CALL setMadLoopPath(/my/path)` before first eval.
- So: run the built exe from inside its `P*` dir (`../MadLoop5_resources` resolves), or `CALL SETMADLOOPPATH(path)` before the first MadLoop call (usage shown commented in check_sa.inc:202-206). Confirmed claim.

## OLP static/dynamic library targets (StandAlone/SubProcesses/makefile)
- `$(OLP)` (=`OLP`, :28) dynamic: `$(FC) -shared $(OLP_PROCESS) -o libMadLoop.$(dylibext)` (:114-115).
- **`OLP_static` (:117-119): `ar rcs libMadLoop.$(libext) $(OLP_PROCESS)` then `mv ... $(MADLOOP_LIB)`.** `MADLOOP_LIB = $(LIBDIR)libMadLoop.$(libext)`, `LIBDIR=$(ROOT)/lib/` (MadLoop_makefile_definitions.inc:9; makefile:11) → **`lib/libMadLoop.a`** (libext=a). Confirmed claim.
- CutTools/IREGI linked statically via `STAT_LIB` WHOLE_ARCH (libcts.a/libiregi.a, :154/:160); Collier linked as a symlinked dynamic lib (:171). LD_LIBRARY_PATH to HEPTools/lib is a plausible need for the dynamic reduction libs (Collier, Ninja-if-shared) but I did not find a hard source requirement in the standalone path — treat as environment caveat, not a verified standalone requirement.
