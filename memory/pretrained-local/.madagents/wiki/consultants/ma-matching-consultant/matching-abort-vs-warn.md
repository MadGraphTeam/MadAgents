---
description: Matching-config two-tier rule — malformed/unsupported settings raise (abort); physically-questionable-but-runnable settings only warn and may silently override. Predicts whether any matching misconfig stops the run.
---

# Matching misconfig: abort tier vs warn-only tier

Cross-cutting principle over the LO, NLO, and PY8-bridge pages. Every matching
validity check in MadGraph falls into one of two tiers. The tier predicts
whether a given misconfiguration **stops the run** or **proceeds (often with the
user's value silently changed)**. Use it to classify a misconfig you have not
seen enumerated.

## The rule
- **Abort tier** — the configuration is *malformed or unsupported*. MadGraph
  `raise`s (`InvalidRunCard` / `InvalidCmd`); the run stops.
- **Warn-only tier** — the configuration is *runnable but physically
  questionable, or inconsistent with the chosen scheme*. MadGraph logs
  (`logger.error`/`warning`/`critical`), optionally **silently overrides** the
  user's value to a scheme-consistent one, and the run **proceeds**.

Heuristic for classifying a new case: "is this value *impossible/unsupported* to
run with, or merely *unwise / scheme-inconsistent*?" Impossible → abort.
Unwise → warn + proceed.

## Abort-tier instances (raise; run stops)
All `$MADGRAPH_INSTALL/madgraph/various/banner.py` unless noted.
- `ickkw>1` and user declines the interactive prompt → `InvalidRunCard('ickkw>1 is still in alpha')` @4550 (LO).
- `ickkw>0` with `maxjetflavor==6` → `InvalidRunCard('maxjetflavor at 6 is NOT supported for matching!')` @4557 (LO).
- CKKW run with `Merging:Process=='<set_by_user>'` → `InvalidCmd(...)` @4476 of `madgraph/interface/madevent_interface.py` (bridge).
- CKKW with BOTH `ktdurham>0` AND `ptlund>0` → `InvalidCmd("*both* cuts cannot be turned on at the same time")` @4500-4503 (bridge). Also the both-zero-cut-with-unset-TMS abort @4519, and `Merging:Process` abort above. (See ckkwl-durham-lund for the full CKKW branch.)
- NLO FxFx (`ickkw==3`) at LO/aMC@LO/noshowerLO mode → `InvalidCmd("FxFx merging (ickkw=3) not allowed at LO")` @5894 of `madgraph/interface/amcatnlo_run_interface.py`. FxFx with `PYTHIA6Q` shower → `InvalidCmd("...does not work with Pythia6's Q-squared ordered showers")` @5902. FxFx with PYTHIA8 but plugin missing/mismatched → `raise Exception("FxFx requires a dedicated plugin...")` @4022/4026. Jet-veto (`ickkw==-1`) at aMC@NLO/noshower → `InvalidCmd("NNLL+NLO jet veto runs (ickkw=-1) only possible for fNLO or LO")` @5913. (See fxfx-amcatnlo-execution.)
- MC@NLO-Delta with non-PYTHIA8 shower → `InvalidRunCard` @5935 banner.py (see mcatnlo-delta).

## Warn-only-tier instances (log + proceed; may silently override)
- `xqcut>0 + ickkw=0` → `logger.error(...)` + `time.sleep(5)`, then proceeds @4563-4565 (LO).
- `ickkw>0`: `drjj`/`drjl` force-zeroed @4566-4573, `alpsfact` forced to 1.0 under use_syst @4552-4555 (LO).
- FxFx `ickkw==3`: `fixed_ren/fac/QES_scale` forced False, `dynamical_scale_choice` forced [-1], `jetradius/jetalgo` forced 1.0 @5798-5819 (NLO).
- Jet-veto `ickkw==-1`: `dynamical_scale_choice` forced [-1] @5820-5825 (NLO).
- MLM `JetMatching:qCut < 1.5*xqcut` (single @4411-4416 and list @4439-4448 of madevent_interface.py) → `logger.error`, proceeds (bridge).
- CKKW `Merging:TMS < run_card[CKKW_cut]` @4519-4522, and `SysCalc:tmsList` scale < cut @4560-4565 → `logger.error`, proceeds (bridge).
- NLO FxFx with an untested (non-PY8/HW6/HWPP) shower → interactive `ask` prompt @5905, default 'n'; non-PY8 FxFx and noshower/noshowerLO → warn-only @5896/1879 (bridge, amcatnlo). FxFx merged cross-section "not retrieved" → logger.warning @4396 (informational, proceeds).

## Probe verification (runtime, not just source-read)
Driving `check_validity()` directly (time.sleep patched out):
- `xqcut=20, ickkw=0` → PROCEEDS (no exception). Confirms warn-only tier.
- `ickkw=1, maxjetflavor=6` → ABORTS `InvalidRunCard: maxjetflavor at 6 is NOT supported for matching!`. Confirms abort tier + verbatim message.
- `ickkw=3, fixed_ren_scale=True, dynamical_scale_choice=[10]` → PROCEEDS, silently flipping `fixed_ren_scale True->False` and `dyn_scale [10]->[-1]`. Confirms warn-only-with-silent-override on the NLO side.

## Why this catches MORE than the instance pages
Each page (lo-ickkw-mlm, nlo-ickkw-fxfx, mlm-py8-bridge) lists its own
warn/abort behaviors in isolation. None states the *predictive* rule. When a
user asks "will MadGraph stop if I set <some matching combo>?", this rule
answers for combos not individually enumerated: classify by
malformed-vs-merely-unwise. The dominant tier is warn-only — most matching
misconfigs proceed silently, so "no error" does NOT mean "physics is right".

## Boundary
- Tier classification is for *matching-gated* checks (ickkw/xqcut/FxFx/CKKW/qCut).
  General run-card validity (beams, PDF, lhaid lengths) also raises but is not
  this slice's concern.
- Whether the interactive `ickkw>1` prompt is even reached depends on
  non-interactive mode; in batch the default answer 'n' triggers the abort.
- The silent-override behavior means a returned/written run_card may differ from
  what the user typed — read the *generated* card, not the user's input, when
  verifying a matched run's effective scales/cuts.
