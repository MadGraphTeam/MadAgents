---
description: GENERALIZATION — a restriction-pruned EXTERNAL param (zeroed in restrict_*.dat) is DROPPED from both the operative card's editable blocks (lhacode GAPS) AND ident_card.dat (no read-filter line), so a hand-added line for it is silently inert at the matrix element. General across any model/restriction; distinct from value-overwriting rules (which keep+rewrite the line) and from internal params (never had an ident line). Probe-confirmed on SMEFTatNLO + sm-no_b_mass + DEFAULT sm (restrict_default zeros ymc/yme/ymm → YUKAWA block is only 5/6/15, lepton-Yukawa hand-add inert).
---

# Restriction-pruned external → dropped from card AND ident_card (silently un-editable)

Generalizes two instance pages — `smeft-wilson-coefficient-blocks.md` (SMEFTatNLO `cG`/`cpG` =
DIM6 7/8 pruned) and the override/source-chain pages' restriction notes. The deeper principle, which
neither instance states as a model-independent rule: **how restriction by value-zeroing removes an
external param from the editable surface of the card.**

## The principle
A model restriction (`restrict_<name>.dat`, a full param_card used as a template) prunes a parameter by
setting its value to `0.000000e+00` in the template. For an **external** param, RestrictModel
(`models/import_ufo.py`, restriction-slice algorithm) then removes it from the model's external set, with
a chain of consequences that is THIS slice's:

1. The param's editable line is **absent from the generated operative `Cards/param_card.dat`** — the
   block keeps its other lhacodes, so you see **lhacode GAPS** (e.g. `... 6 <v> / 9 <v> ...`, 7 and 8
   gone). Gaps are normal, not corruption.
2. The param has **no line in `Cards/ident_card.dat`** — the externals-only read filter
   (`create_ident_card`, export_v4.py L9684; operative-source-chain.md). `write_inc_file` walks ONLY
   ident_card, so a pruned external **never reaches `param_card.inc`**.
3. Therefore **hand-adding a line for a pruned external is silently inert** — no inc-file line, no
   warning (the read filter simply never names it). To activate it you must pick a restriction that keeps
   it (or the unrestricted model) and re-`output` — a card edit cannot resurrect it.

This is the EFT face of the operative-source-priority surprise, but it is **not EFT-specific**: it is the
behaviour of any external param under any value-zeroing restriction, in any model.

## Probe evidence — two independent models (both this install, v3.7.1)
- **SMEFTatNLO-NLO, `p p > t t~ NP=2 [QCD]`**: restrict_NLO zeros `cG`(DIM6 7) /
  `cpG`(DIM6 8); operative `Block dim6` jumps 6→9, `ident_card.dat` has no `dim6 7`/`dim6 8`. DIM62F
  gaps (17,18,20,21) match restrict_NLO's zeros. (smeft-wilson-coefficient-blocks.md.)
- **sm-no_b_mass, `p p > b b~`**: `restrict_no_b_mass.dat` sets
  `ymb`(YUKAWA 5) AND `MB`(mass 5) to `0.000000e+00`; the generated card's editable YUKAWA block holds
  only `6 ymt / 15 ymtau` (4,5,11,13 gone) and `ident_card.dat` has only `yukawa 6 mdl_ymt` /
  `yukawa 15 mdl_ymtau` (no `yukawa 5`), `mass` only `23/6/25/15` (no `mass 5`). Identical drop
  behaviour with a non-EFT SM restriction — the generalization holds beyond Wilson coefficients.

- **DEFAULT sm (no opt-in restriction), any `p p > ...` run**: the SHIPPED `restrict_default.dat` (the default
  restriction, applied to EVERY plain `import model sm` run) zeros the light-fermion Yukawas in its
  YUKAWA template — L48 `4 0.000000e+00 # ymc`, L51 `11 0.000000e+00 # yme`, L52 `13 0.000000e+00
  # ymm` — keeping only L49 `5 ymb`, L50 `6 ymt`, L53 `15 ymtau` non-zero. So the generated operative
  card's YUKAWA block holds **exactly `5 ymb / 6 ymt / 15 ymtau`** (lhacodes 4, 11, 13 GONE — gaps),
  and `ident_card.dat` has only `yukawa 5 mdl_ymb` / `yukawa 6 mdl_ymt` / `yukawa 15 mdl_ymtau` (no
  `yukawa 4/11/13`). The `yme`/`ymm`/`ymc` lines are **ABSENT, not present-with-zero** — there is no
  `# ymc`/`# yme`/`# ymm` line anywhere in the operative card (probe-grepped). A user **cannot
  resurrect H→ee by hand-adding `11 5.11e-4` to the YUKAWA block** — no Fortran reads it (no
  ident_card line → never in `param_card.inc`). This is the most everyday instance: the drop fires
  on the DEFAULT restriction of plain `sm`, not only opt-in restrictions like `no_b_mass`. (All three
  light-fermion Yukawas — `ymc`(4), `yme`(11), `ymm`(13) — are zeroed the same way in
  restrict_default.)

So the mechanism is the SAME whether the zeroed external is a Wilson coefficient or a SM Yukawa/mass.
It catches every SM restriction (`no_b_mass`, `no_tau_mass`, `c_mass`, `lepton_masses`, `no_masses`,
`no_widths`, `ckm`/`zeromass_ckm` — all zero externals in their template), every BSM/EFT restriction,
not just the two probed.

## Boundaries — three things this is NOT
1. **Internal/dependent params never had an ident line to begin with** — they are recomputed
   Fortran-side, not pruned. A wrong value for `mass 24` (MW, `nature='internal'`) is inert at the ME
   for a DIFFERENT reason (it was never read), and IT still leaks to the LHE banner / Pythia / MadSpin.
   That is operative-source-chain.md / card-editor-update-commands.md, a separate mechanism. This page
   is specifically about an EXTERNAL that restriction *removed*.
2. **Value-OVERWRITING rules are a different mechanism.** The `param_card_rule.dat` zero/one/identical/
   opposite rules (override-stages-card-to-fortran.md stage 2; param-card-validation-rule-engine.md) KEEP the param's
   line and *rewrite* its value ("fixed by the model"). Pruning REMOVES the line entirely. A param that
   is rule-constrained still has an ident line and is still read; a pruned param does not and is not.
   Symptom test: rule-constrained → line present, value reverts on load; pruned → line absent, lhacode
   gap, hand-add inert.
3. **The dependent-param comment lines remain.** The pruned particle may still appear in the card's
   `# <name> : <expr>` informational comment block (the `restricted_value` / dependent-mass lines —
   e.g. `5 0.000000e+00 # b : 0.0` in the no_b_mass MASS block) but those are comments MG5 ignores
   (downstream tools read them), carry NO ident entry, and are not the editable external line. Do not
   mistake a `# name : expr` comment line for an editable param — it is the marker of a pruned/derived
   param (analyze_param_card → restricted_value, param-card-validation-rule-engine.md L415).

## Diagnostic
"I set parameter X in the card but the run ignored it, and X isn't in my generated card / has a gap":
- X absent from operative card with a lhacode gap AND absent from `ident_card.dat` → **pruned by the
  chosen restriction.** Re-`output` with a restriction that keeps X (or unrestricted); a card edit
  cannot turn it on.
- X present in the card but its value reverts to a fixed 0/1/=other on load → **rule-constrained**
  (override-stages stage 2), not pruned.
- X is an internal/dependent param (no ident line, `# name : expr` comment) → never read from card,
  recomputed Fortran-side (operative-source-chain.md); the edit leaks only to LHE banner / downstream.

## Probe-candidates (expensive, not run)
- Confirm end-to-end inertness: hand-add a pruned-external line (e.g. `5 4.7 # ymb` in the no_b_mass
  card or `7 0.9 # cG` in the SMEFT card), `launch -f`, grep `param_card.inc` for the var — expect
  absent, no warning. One line each. (Static chain is certain; this is the runtime confirmation.)
