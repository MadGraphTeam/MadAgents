---
description: SPINUP / tau-polarization / particle-decay handoff — MG writes NO tau/mayDecay/SPINUP keys into the PY8 card; the LHE that carries SPINUP is unweighted_events.lhe.gz via Beams:LHEF. Pythia8's SPINUP-reading and TauDecays:mode are out-of-slice.
---

# SPINUP / tau-decay handoff (MG side)

Scope: what MadGraph writes (or does NOT write) about tau/particle decays and the SPINUP-bearing LHE. Pythia8's own SPINUP-reading algorithm, `TauDecays:mode`, `iTopCopyId`, internal polarization computation = OUT of slice (Pythia8 internals) — GAP/redirect, not cached here.

## MG writes ZERO tau/SPINUP/mayDecay keys
- Default template `Template/LO/Cards/pythia8_card_default.dat` (verified by dumping the whole card) contains NO `15:*`, `mayDecay`, `TauDecays`, `SPINUP`, or `spin`/`decay` token of any kind. Its uncommented entries are only: `Main:numberOfEvents`, `HEPMCoutput:file`, the MLM block (`JetMatching:qCut/doShowerKt/nJetMax`), the CKKW-L block (`Merging:TMS/Process/nJetMax`), `SysCalc:fullCutVariation`, and the commented `!partonlevel:mpi`. (see py8-card-defaults.md for the same list.)
- Whole-tree grep `mayDecay|TauDecays|SPINUP|15:mayDecay` over `$MADGRAPH_INSTALL/madgraph/` returns EMPTY. MadGraph never emits any `15:*` or `mayDecay` line, in the template, in `banner.py` PY8Card `default_setup`, or in `setup_Pythia8RunAndCard` (`madevent_interface.py:4307-4430` writes no decay/tau/spin key).

=> Claim "default pythia8_card sets `15:mayDecay`/`TauDecays:mode`": FALSE. No such default exists.
=> Claim "set `15:mayDecay = no` so PY8 doesn't re-decay a MadSpin tau": that is a pure **user edit** into the "User customized parameters" section of `pythia8_card.dat`, NOT a MadGraph default and NOT MG-templated. It reaches PY8 the same way any user line does — `do_pythia8` overlays `pythia8_card.dat` with `read(..., setter='user')` (`:4666-4669`), so a user `15:mayDecay` survives to the written `.cmd` (PY8Card is permissive; unknown-to-MG keys are passed through as user_set). Whether it actually stops PY8 re-decaying the tau is a Pythia8-internal question (out of slice).

## The only decay-related PY8Card params MG knows are general, hidden, and unwritten by default
`banner.py` PY8Card `default_setup` declares three decay-adjacent params — all `hidden=True, always_write_to_card=False` (written only if user_set/system_set), and NONE tau-specific:
- `Merging:mayRemoveDecayProducts` = False (`banner.py:1988`)
- `PartonLevel:FSRinResonances` = True (`banner.py:2001`)
- `ProcessLevel:resonanceDecays` = True (`banner.py:2002`)
So even the general "let unstable particles decay" toggle (`ProcessLevel:resonanceDecays`) is user-set-only; MG does not touch it in the tau/MadSpin case.

## The SPINUP-bearing LHE reaches PY8 as unweighted_events.lhe.gz
- Single-core / main input: `PY8_Card.subruns[0].systemSet('Beams:LHEF', "unweighted_events.lhe.gz")` (`setup_Pythia8RunAndCard`, `madevent_interface.py:4319`); `Beams:frameType=4` (LHEF) is a hidden always-written default (`banner.py:1925`). The file is materialized/gzipped on demand in `check_pythia8` (`:1444-1447`).
- Parallel path (run_mode 1/2): per-split card uses `Beams:LHEF=events.lhe.gz` (`:4848`). So `events.lhe.gz` is the per-split name; `unweighted_events.lhe.gz` is the run-level input.
- The SPINUP column (MC-selected `nhel`) is a column of THIS LHE (premise, grounded). MG's job is only to point PY8 at the file; PY8 reads the column (out of slice).

## Launcher-path correction
The LO MG->PY8 handoff is `do_pythia8` (`madevent_interface.py:4579`), NOT `Pythia8Launcher` (`launch_ext_program.py:718`). `Pythia8Launcher` is the standalone `main_*.cc` example compiler for `output pythia8` C++ standalone, unrelated to MadEvent event showering (see lo-autolaunch-entry-chain.md). Any "cite the Pythia8Launcher handoff for the LHE input" framing is misdirected — the LHE/Beams:LHEF wiring lives in `do_pythia8` -> `setup_Pythia8RunAndCard`.

## GAP / redirect (Pythia8 internals — NOT verified, NOT cached as fact)
- Whether PY8 re-decays a stable-in-LHE tau depends on PY8 `15:mayDecay` default + `ProcessLevel:resonanceDecays`; PY8-internal.
- `TauDecays:mode`, tau-polarization reconstruction from SPINUP, `iTopCopyId` — Pythia8 internals, redirect to Pythia8 docs, not this slice.
- Whether MadSpin marks the decayed tau as final-state/stable in the LHE it writes -> madspin-interface slice (LHE-writing side), not the PY8 interface.
