---
description: Diagnostic — a user-typed param_card value can be silently overridden/substituted at four stages between the operative card and param_card.inc; check them in pipeline order for "I set X but the run used Y".
---

# Override stages: what reaches Fortran is not what you typed

Between the operative `<PROC_DIR>/Cards/param_card.dat` and the Fortran `param_card.inc`,
a value the user believes authoritative can be silently changed at **four distinct stages**.
When the symptom is "I set X in the card but the run used Y", walk these in pipeline order.
This page owns the override *mechanism* only — not width computation (madwidth), the restriction
*pruning algorithm* (restriction slice), or UFO default *content* (ufo slice).

## The four stages (read → validate → write_inc_file)

1. **Read drop** — a malformed param line is warned-and-dropped, not fatal.
   `$MADGRAPH_INSTALL/models/check_param_card.py` L402: `Block "%s" has line "%s" that is
   not in slha1 format: line is ignored`. The line silently vanishes from the loaded card; its
   value then comes from stage 3. A value-conflicting **duplicate** lhacode is the one hard stop
   (raises `InvalidParamCard`, L240-243) — exact duplicates are dropped silently.
   (Detail: read-write-entry-types.md.)

2. **Restriction rewrite** — `check_valid_param_card` / `make_valid_param_card` run the model's
   `param_card_rule.dat` rules. With `modify=True` a value violating a `<zero>`/`<one>`/`<identical>`/
   `<opposite>`/`<constraint>` rule is **overwritten** and commented "fixed by the model"
   (`check_param_card` L1308+). A hand-set value violating a restriction is not honored.
   (Detail: param-card-validation-rule-engine.md. The pruning *decision* is the restriction slice's; this page
   notes only that the rewrite happens in param-card code.)

3. **Default-fill** — `ParamCard.write_inc_file` (L640) walks `Cards/ident_card.dat`; any param the
   operative card lacks is filled from the **default card** with a logged warning, NOT from zero.
   `information about "%s %s" is missing using default value: %s.` (L678/684); full-block-missing
   has its own text; `loop [0]` missing falls back to hardcoded `91.118` (L690). The default card is
   `bin/internal/ufomodel/restrict_default.dat` when present (restriction defaults), else
   `param_card.dat`. Deleting a line therefore reverts to model default, not zero.
   (Detail: operative-source-chain.md.)

4. **Sentinel rounding (fresh-card write only)** — when a fresh card is written by
   `ParamCardWriter`, restriction sentinels `9.999999e-1`→`1` and `0.000001e-99`→`0`
   (`$MADGRAPH_INSTALL/models/write_param_card.py` L253-256). A literal `1`/`0` in a restricted slot
   is what keeps the param alive; editing it can collide with the restriction.
   (Detail: fresh-card-writers.md.)

Plus the non-override but easily-confused transforms at write_inc_file time: negative-mass→negative-width
(L693-695) and slha1↔slha2 block remapping for MSSM-family (`secure_slha2`, slha1-slha2-conversion.md).

## Probe-confirmed (this install, v3.7.1)
Deleting the `MASS` block line for pid 6 (MT) from a generated `e+ e- > mu+ mu-` card, then
`treatcards param`, emitted exactly: `information about "mass [6]" is missing using default value:
<MT default>.` and the run proceeded (non-fatal). Confirms stage 3 end-to-end: missing → model
default, not zero. The filled value is the DEFAULT CARD's MASS 6, read fresh — for a normal generated
sm dir that is `restrict_default.dat` MASS 6, which DIVERGES from raw `parameters.py` MT
(sm-default-param-values.md); do NOT cache a bare number, the two layers disagree. The resolved value
is written to `<output_dir>/param_card.inc` (`do_treatcards` L3224:
`outfile = pjoin(opt['output_dir'], 'param_card.inc')`).

**Decay-line discriminator — stage-3 is non-fatal ONLY when the deleted-mass pid has NO `decay <pid>`
line in ident_card** (probe-confirmed). In `e+ e- > mu+ mu-` the top (pid 6) is not in the process so
its `decay 6` line is pruned from ident_card; the L678 default-fill then completes cleanly. But on a
card where pid 6 has BOTH `mass 6` and `decay 6` in ident_card (e.g. a plain-SM `output` dir), deleting
`mass 6` and running the SAME bare `treatcards param` emits the default-fill warning and THEN **crashes
`KeyError: 'id (6,) is not in mass'`** — the inc-time negative-mass lookup at write_inc_file L693
(`self['mass'].get((6,))`) is unguarded for every decay line. This is an INC-TIER crash (fires on every
launch path including `-f`, since it lives in write_inc_file), distinct from the edit-tier
dependent-recompute KeyError below. So "deleting a mass line is non-fatal via `treatcards param`" holds
only for a pid without a paired decay line. (Detail + probe transcript: operative-source-chain.md.)

**Path-dependence caveat (probe-confirmed):** stage-3 non-fatality holds for the *bare* `treatcards
param` path, which does NOT run the edit-time dependent recompute. On the FULL `./bin/madevent launch`
path, deleting the same `mass 6` (MT) line from an SM `p p > t t~` card **crashes** with
`KeyError: 'id (6,) is not in mass'` plus three `Missing mass in the lhef file (6)` warnings — the
edit-time `static_check_param_card(dependent=True)` → `update_dependent` (common_run_interface.py
L3777) dereferences the top mass and aborts before integration. So "a deleted line is non-fatal,
reverts to default" is true at the inc-file stage in isolation but NOT for a mass that the dependent
recompute needs: same edit, non-fatal via `treatcards param`, fatal via `launch`. Diagnose by which
entry point processed the card.

## Diagnostic checklist for "set X, run used Y"
- Is X's line malformed / a duplicate? → stage 1 (grep the read warning).
- Does the model restriction force X to 0/1/=other/=−other? → stage 2 ("fixed by the model" comment).
- Is X's line actually present in the operative card? → stage 3 (grep the "missing using default" warning).
- Was Y exactly `1` or `0` in a restricted slot, or did a fresh `output` overwrite a hand edit? → stage 4.
- Is X a width on `Auto`? → not an override; value is madwidth's (scan-and-auto-detection.md detects, madwidth computes).
