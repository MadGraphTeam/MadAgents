---
description: NLO card-write validation (RunCardNLO.check_validity / update_system_parameter_for_include) is an INCOMPLETE net — several IR-safety/consistency constraints are not (or imperfectly) enforced at card-write; the hard enforcement is deferred to a downstream stage (fortran `stop`, run() `aMCatNLOError`, shower-time `Exception`, or the compile test-suite). "The card validator will reject X" is the wrong answer for these classes.
---

# NLO card validation is a soft net — real enforcement is deferred downstream

A recurring trap when answering "will the NLO run_card validator reject setting X?": for several classes of bad/unsafe setting, **`RunCardNLO.check_validity` (banner.py:5761) and `update_system_parameter_for_include` (banner.py:5962) pass silently at card-write time, and the error only surfaces later** — at Fortran compile/run (`stop`), at `run()` (`aMCatNLOError`), at shower time (`Exception`), or in the compile test-suite. The card-write validator is a soft net, not the authority. Answering "the card validator will catch it" is wrong for any setting in this class.

This generalizes four independently-source-confirmed instances and catches future ones: whenever someone asks "is setting X validated when the card is written," the default expectation must be "maybe not — find the *enforcing* stage, which is often downstream of card-write."

## The enforcement-deferral instances (all source/probe-confirmed v3.7.1)

1. **Massless-PDG per-particle cut** — [[nlo-cut-block-and-ir-safety]]. The Python guard `if any(pdg in pdg_to_cut for pdg in [21,22,11,13,15]+…)` at banner.py:5977 has a **string-vs-int gap on the dict path**: `pt_min_pdg` keys are strings (`'21'`), the guard tests int membership (`21 in {'21'}` → `False`). Probe: `RunCardNLO()['pt_min_pdg']={'21':50.}; check_validity()` raises **nothing**. Real enforcement is `Template/NLO/SubProcesses/setcuts.f:117` (`pmass==0 → stop 1`) / `:125` (`is_a_lp/lm/j/ph → stop 1`) at run-time. The comment at banner.py:5978 ("this will double check in the fortran code") names the deferral explicitly.

2. **Invalid `parton_shower` name** — [[runtime-shell-commands]], [[shower-reads-banner-snapshot]]. `check_validity` does NOT restrict `parton_shower` to the valid set (probe: `rc['parton_shower']='NOTASHOWER'; check_validity()` raises nothing). The hard reject is at `run()`: amcatnlo_run_interface.py:2005-2008, `aMCatNLOError('%s is not a valid parton shower…')` against the fixed list `['HERWIG6','HERWIGPP','PYTHIA6Q','PYTHIA6PT','PYTHIA8']` (2003).

3. **FxFx (`ickkw==3`) PYTHIA8 plugin** — [[fxfx-ickkw3-lifecycle]] stage 5. Card-write does NOT check for the dedicated JetMatching plugin. The check is a **byte-for-byte file comparison at shower time**: `run_mcatnlo` (amcatnlo_run_interface.py:4023 missing-plugin / 4026 mismatch) raises `Exception("FxFx requires a dedicated plugin…")`.

4. **Pole cancellation** — [[compile-and-tests]]. Not a card setting, but the same shape: there is no card-write check; the enforcement is the compile test-suite. `parse_check_poles_log` (amcatnlo_run_interface.py:5728) fails the run via `aMCatNLOError('Poles do not cancel…')` only when `nfail/(nfail+npass) > 0.1` (>10% of points) — and 0 points tried is warn-only.

## What check_validity DOES enforce at card-write (the contrast)
So the net is not empty — to know whether a given setting is caught early, you must read `check_validity` for THAT key. It DOES hard-reject e.g.: DIS beams (5777), `folding` not in {1,2,4,8} or wrong length (5928), `mcatnlo_delta` without pythia8 (5934), `pineappl`/`reweight_pdf` without lhapdf (5828/5862), >25 PDG-cut keys (5970), negative PDG codes (5972/5974), `dynamical_scale_choice>10`/`lhaid>25` (5900). And it silently AUTO-REPAIRS the FxFx fixed-scale/jet params (5798-5818, stage 2 of [[fxfx-ickkw3-lifecycle]]). The rule is not "card validation does nothing" — it is "card validation is selective; the absence of a check is not the absence of enforcement."

## How to answer the question class
For "will the NLO card validator reject / catch X":
1. Read `check_validity` (and `update_system_parameter_for_include` for the per-particle-cut dicts) for X's key. Don't assume a check exists.
2. If no card-write check, find the **enforcing** stage — `run()` validity block (amcatnlo_run_interface.py:1981-2011), the compile test-suite ([[compile-and-tests]]), the shower invocation ([[fxfx-ickkw3-lifecycle]] stage 5), or the Fortran (`setcuts.f`/`cuts.f`).
3. Beware **string-vs-int / dict-key type gaps** (instance 1): a guard that looks present can be a no-op for the dict path while working for the scalar path (the negative-PDG guard at 5972 uses `int(pdg)` and DOES fire; the membership guard at 5977 does not).
4. The user-visible failure stage and message differ by class: `stop 1` (fortran, at run), `aMCatNLOError` (Python, at `run()`/test), `Exception` (at shower). Cite the stage that matches the question's timing.

## Boundary
- This is about **enforcement TIMING/COMPLETENESS within validation** (card-write net is incomplete; enforcement deferred), distinct from [[fxfx-ickkw3-lifecycle]]'s value-*mutation* across stages and [[shower-reads-banner-snapshot]]'s read-*source* divergence. A setting can be subject to all three axes; keep them separate.
- LO `RunCard.check_validity` is a different method (kinematic-cuts slice owns the LO cut validation); this page is the NLO class only.
- Whether the *deferred* Fortran `stop` actually fires at runtime (instance 1) is a probe-candidate (needs full output+compile+launch); the Python-side silence is probe-confirmed.
