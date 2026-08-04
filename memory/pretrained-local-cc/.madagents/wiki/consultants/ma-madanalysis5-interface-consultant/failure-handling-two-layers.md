---
description: MG->MA5 interface failure handling splits in two layers — pre-flight gates are no_default-conditional (silent for MG / raise for user); post-launch failures are unconditional (no who-triggered branch) but disposition varies (mostly quiet degrade, one reco-output path hard-raises MadGraph5Error).
---

# MG -> MA5 failure handling: two layers (v3.7.1)

Generalization over the scattered skip/raise mentions in invocation-flow, input-resolution-and-cmds, and driver-execution-mechanics. The deeper rule those instances are facets of: **where in `run_madanalysis5` (common_run_interface.py:3102) a failure occurs decides the policy, not just who triggered it.** All line refs common_run_interface.py.

## Layer 1 — pre-flight gates: `no_default`-conditional
Failures detected BEFORE the MA5 interpreter is constructed branch on `no_default` (set True by `--no_default`, which generate_events always passes; False when a user types the command). MG-triggered -> degrade quietly; user-issued -> hard `InvalidCmd`.
- Missing `Cards/madanalysis5_<mode>_card.dat` (3114-3121): `if no_default: return` (bare silent). User path falls through to 3130.
- `madanalysis5_path` unset OR neither card present (3127-3134): `if no_default: return` else `raise InvalidCmd("You must have MadAnalysis5 available ...")`.
- Empty resolved inputs (3145-3154): `if no_default: logger.warning("No hadron level input found ... Skipping") + return` else `raise self.InvalidCmd("No input files specified ...")`.

## Layer 2 — post-launch failures: UNCONDITIONAL (no no_default branch), mostly degrade but one path RAISES
From interpreter construction onward, `no_default` is NOT consulted — these paths behave identically regardless of who triggered the run. There is no user-vs-MG distinction in Layer 2. The disposition, however, is NOT uniformly "quiet degrade": most paths return/continue, but the reconstruction-output path hard-raises.
- Interpreter construction (3202-3219): `except SystemExit: return`; `except Exception: logger.warning("MA5 fails with: ..."); return`; `if MA5_interpreter is None: return`. (None also returned by get_MadAnalysis5_interpreter on Py3-incompat / import failure — see invocation-flow page.) Bare returns, no no_default check. -> quiet degrade.
- Per-runtag runMA5 failure (3251-3254): `if not runMA5(...): return` — aborts ALL remaining runtags. Only a WARNING in the per-runtag logfile + the caught-exception WARNING. -> quiet degrade.
- **EXCEPTION — reconstruction output missing (3281-3282): `raise MadGraph5Error("MadAnalysis5 failed to produce the reconstructed event file for reconstruction '%s'.")`.** This fires inside the `_reco_*` runtag handler (3256-3301) AFTER runMA5 itself returned success, when the expected `*.lhe.gz`/`*.root` under `<reco_output>/Output/SAF/_reco_events/...` is absent (`len(reco_event_file)==0`). It is a HARD raise that propagates out of run_madanalysis5 — NOT a degrade, and with NO `no_default` guard, so it propagates the same for a user-issued AND a generate_events-issued run. This is the one post-launch path that breaks the "Layer 2 = quiet" expectation.
- Missing PDF/CLs output (3319-3322): `logger.error('MadAnalysis5 failed to create PDF output')` and CONTINUE (non-fatal). -> quiet degrade.
- Missing analysis dir (3332-3335): `logger.error('MadAnalysis5 failed to completed succesfully') + return`. -> quiet degrade.

## Why the split is the load-bearing insight
The non-obvious consequence is asymmetric visibility for a manual user. Running `madanalysis5_hadron` by hand:
- a missing card / unset path / no input -> HARD `InvalidCmd` you cannot miss (Layer 1, user branch);
- an interpreter that fails to construct, or an analysis that crashes mid-load -> SILENT skip / abort with only a WARNING (Layer 2, quiet-degrade paths);
- BUT a reconstruction whose output file goes missing (3281-3282) -> HARD `MadGraph5Error` (Layer 2, the one raising path) — and unconditionally, so generate_events also crashes on it, not just a manual user.
So "MA5 raised, therefore my setup is the problem" and "MA5 produced nothing but didn't raise, therefore it ran fine" are BOTH unsafe inferences — the quiet-degrade paths swallow most post-launch failures the same way for users and for generate_events, while the reco-output path raises for both. Disposition depends on WHICH post-launch path failed, not on who triggered it.

HYPOTHESIS (runtime prediction, NOT probe-verified): the user-visible asymmetry above is read off the branch structure, not observed. `madanalysis5_path` is unset in this install (mg5_configuration.txt:180 = `$MADGRAPH_INSTALL/None`), so a real interpreter-failure-after-pre-flight scenario could not be driven here. The control-flow branches (which line returns vs raises) ARE source-verified; the observable end-user experience is inferred from them. Probe when an MA5-enabled install is available: install MadAnalysis5, run `madanalysis5_hadron` manually with (a) a deleted card, (b) a deliberately broken MA5 interpreter, and confirm (a) raises while (b) only warns.

## Cases this catches beyond the instances
The load-bearing rule is about the `no_default` BRANCH, not the disposition: any NEW failure point added BEFORE interpreter construction is expected to be no_default-conditional (silent for MG / raise for user); one added AFTER is unconditional (no no_default branch) — but its disposition (quiet degrade vs hard raise) is a separate choice the existing code makes both ways (3251-3254 returns, 3281-3282 raises). Do not assume a new post-launch check degrades quietly; check whether it returns or raises. Also catches reasoning about partial output (a Layer-2 quiet abort leaves earlier runtags' PDFs in place; a Layer-2 raise from a reco runtag leaves earlier runtags' outputs in place too but surfaces a traceback) and about why a user's manual MA5 invocation can silently produce nothing.
