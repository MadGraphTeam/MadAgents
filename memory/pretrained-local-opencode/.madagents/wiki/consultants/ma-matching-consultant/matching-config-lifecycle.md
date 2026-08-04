---
description: Matching config is applied at THREE lifecycle moments — auto-detect (create_default_for_process, output-time) writes a full scheme-consistent value set from the process; check_validity (write/launch-time) re-checks user edits; the Pythia8 bridge (setup_Pythia8RunAndCard, shower-launch) enforces CKKW cut-selection / Merging:Process / qCut floor and can abort a card that passed check_validity (the both-on CKKW abort). Predicts which hand-edits survive, which get overridden, and where a valid card still aborts.
---

# Matching config lifecycle: auto-detect vs check_validity vs Pythia8 bridge (three moments)

Cross-cutting principle over lo-ickkw-mlm, nlo-ickkw-fxfx, heft-merging-jetflag,
and matching-abort-vs-warn. Each of those describes ONE moment in isolation.
The predictive question this answers: *"I hand-edited the run_card — will MadGraph
keep my value or override it?"* The answer depends on WHICH of two passes the
relevant logic lives in.

## The three moments

**Moment 1 — auto-detect, at `create_default_for_process`** (card-generation /
`output` time). Runs ONCE, when the process directory + run_card are first
written. Called from `madgraph/iolibs/export_v4.py:277` (LO) and
`export_fks.py:807` (NLO). Dispatches to `RunCardLO.create_default_for_process`
(`banner.py:4767`) / `RunCardNLO` (`banner.py:6029`). It inspects the process
structure (`proc_characteristic`, multi-multiplicity jet detection) and, if
matching is detected, writes a FULL scheme-consistent value set into the
fresh card — overwriting the template defaults *before the user ever sees the
card*.

**Moment 2 — `check_validity`** (card-write / launch time). Runs on EVERY card
write/read-back (`banner.py:3591`, inside `write`; comment "ensure that all
parameter are coherent and fix those if needed"). It re-checks the user's
*current* values and silently overrides scheme-inconsistent ones (the
matching-abort-vs-warn warn-tier), or raises (abort-tier).

These are genuinely separate passes at different pipeline stages: output vs
launch. A value set in Moment 1 is just a default the user can later edit;
Moment 2 re-fires on user edits at card-write — but it is NOT the last gate.

**Moment 3 — the Pythia8 bridge** (`setup_Pythia8RunAndCard`,
`madgraph/interface/madevent_interface.py:4307`, reached from `do_pythia8` at
shower-launch time, AFTER Moment 2). A whole class of matching enforcement fires
HERE and at neither Moment 1 nor Moment 2: the entire CKKW cut-selection
(@4491-4503), the `Merging:Process` hard requirement (@4476), `Merging:TMS`
defaulting/abort (@4512-4517), the MLM `JetMatching:qCut` floor (@4408-4415), and
the qCutList/tmsList variation. The decisive evidence that this is a SEPARATE
stage from Moment 2: the CKKW **both-on** mutual-exclusion (ktdurham>0 AND
ptlund>0) **passes `RunCardLO.check_validity` with no exception** (probe-confirmed)
yet **aborts at the bridge** with `InvalidCmd("*both* cuts cannot be
turned on at the same time")` (@4500-4503). So a run-card that is fully valid at
Moment 2 can still abort at Moment 3 — but only on the Pythia8 path
(`generate_events` + shower); a parton-level-only run never reaches Moment 3 and
never sees these checks. (Full branch on ckkwl-durham-lund; abort/warn tiers on
matching-abort-vs-warn.)

## What each moment force-sets (source-confirmed)

Moment 1 — LO when matching detected (`banner.py:4956-4966`): `ickkw=1`,
`xqcut` set to a default merging scale, `drjj=0`, `drjl=0`, `sys_alpsfact`/`--alps`
set to the auto variation set, display mlm+ckkw blocks, `dynamical_scale_choice=-1`
(read the forced literals fresh @4956-4966).
Moment 1 — NLO when matching detected (`banner.py:6116-6122`): `ickkw=3`,
`fixed_ren/fac/QES_scale=False`, `jetalgo=1`, `jetradius=1`,
`parton_shower="PYTHIA8"`.
Moment 1 — model-limitation (`banner.py:5048-5066`): `'MLM'` or `'fix_scale'`
in `proc_characteristic['limitations']` → force `ickkw=0` (HEFT/hgg path).

Moment 2 — LO (`check_validity` @4544-4577): `ickkw!=1`→abort-prompt;
`maxjetflavor==6`→abort; `xqcut>0+ickkw=0`→warn+sleep; `drjj/drjl` zeroed if
`xqcut>0`; `alpsfact` forced 1.0 under use_syst.
Moment 2 — NLO (`check_validity` @5798-5825): FxFx (ickkw=3) forces scales/jet
params; jet-veto (ickkw=-1) forces dynamical_scale_choice=[-1].

## The trap this catches that no instance page does

**A hand-edit that contradicts Moment-1 logic but is NOT re-tested in Moment 2
silently survives.** The clearest case: the `'MLM' in limitations` force-zero
of `ickkw` (HEFT/hgg models) lives ONLY in Moment 1 (`create_default_for_process`
@5048-5053). `check_validity` does NOT re-test the limitation. So a user who
hand-edits `ickkw=1` back into the run_card of a HEFT-limitation model AFTER
output will NOT re-trigger the critical-log / force-zero — Moment 2 passes it
(it only checks `ickkw` value validity, not model compatibility). The
heft-merging-jetflag page notes this for the one case; the lifecycle principle
generalizes it: **any compatibility/structural decision made from
`proc_characteristic` is a Moment-1-only decision and is defeatable by a later
hand-edit.**

Conversely, value-level scheme consistency (FxFx scale forcing, drjj zeroing,
maxjetflavor=6 abort) lives in Moment 2 and re-fires on every edit — those you
CANNOT defeat by hand-editing.

Also caught: the NLO site-default file read is LAST in Moment 1
(`banner.py:6127-6128`, path resolved @5608 to
`$MADGRAPH_INSTALL/internal/default_run_card_nlo.dat` — the @6125 comment says
"input/..." but the real `pjoin(MG5DIR,"internal",...)` is `internal/`), so a
site-level default file overrides even the auto-detect set — another
Moment-1-only override invisible to Moment 2. (LO analogue: `default_run_card_lo.dat`
read @5108-5109, path @4206.)

## How to apply
- "Will my edit stick?" → classify the logic: reads `proc_characteristic` /
  process structure ⇒ Moment-1-only ⇒ a later hand-edit defeats it. Reads only
  run_card param values in `check_validity` ⇒ Moment-2 ⇒ re-fires on every write,
  edit is overridden. Lives in `setup_Pythia8RunAndCard` (CKKW cut-selection,
  Merging:Process/TMS, qCut floor) ⇒ Moment-3 ⇒ fires ONLY on the Pythia8 shower
  path, invisible to a parton-level run and to `check_validity`.
- "My run_card validated but the run still aborted on a matching setting" ⇒ it is
  almost certainly a Moment-3 (bridge) abort: read `setup_Pythia8RunAndCard`, not
  `check_validity`. The both-on CKKW case is the canonical example.
- When verifying a matched run, read the GENERATED card (post-Moment-1) AND
  remember Moment-2 may further override at launch — the effective values are
  what `check_validity` leaves, not what the card-on-disk shows for
  value-level checks.

## Boundary
- This is a control-flow / lifecycle claim (which function runs when), fully
  static-source-grounded — not a runtime-output prediction, so no probe needed
  for the lifecycle itself. The specific force-set values it cites are verified
  in their instance pages (lo-ickkw-mlm, nlo-ickkw-fxfx, heft-merging-jetflag);
  the abort-vs-warn behavior of Moment 2 is probe-verified in matching-abort-vs-warn.
- Shower-card matching params (Qcut/njmax) do NOT follow the two-moment shape:
  `ShowerCard.create_default_for_process` (`shower_card.py:329-330`) is a no-op
  (`pass # will be usefull later on`). So there is NO Moment-1 auto-detect for
  Qcut/njmax — they stay at template defaults (`Qcut=-1.0`, `njmax=-1`) until the
  user sets them. An FxFx run with an unset Qcut is the user's responsibility, not
  auto-filled (contrast the run-card, whose Moment 1 DOES set ickkw/ptj). See
  shower-card-qcut.
