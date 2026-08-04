---
description: SM/loop_sm UFO EW input scheme — SMINPUTS block (aEWM1/Gf/aS), the alpha-Gmu-mixed scheme with MW declared nature='internal' (derived from aEWM1,Gf,MZ, absent from param_card, not overridable), aS as an independent QCD input decoupled from the EW/MW relation, and where the YUKAWA block values live. No Gmu-input variant is bundled (loop_qcd_qed_sm_Gmu absent from disk).
---

# SM UFO EW input scheme + MW internal-vs-external (v3.7.1)

Topic: the electroweak input set of the default `sm` and `loop_sm` UFO models, why MW is NOT a param_card entry, and the SMINPUTS/YUKAWA declared values. Complements `ufo-param-to-paramcard-chain.md` (the nature=='external' membership predicate) and `ufo-declaration-object-grammar.md`. Ref: `$MADGRAPH_INSTALL/models/sm/parameters.py`, `models/loop_sm/parameters.py`.

## 1. SMINPUTS block — three externals, aS decoupled from EW (sm parameters.py:21-43)
All three are `nature='external'`, `lhablock='SMINPUTS'`:
- `aEWM1` [1] (`:21-27`) — inverse EW coupling alpha_EW(MZ)^-1. Read value at coordinate.
- `Gf`    [2] (`:29-35`) — Fermi constant. Read value at coordinate.
- `aS`    [3] (`:37-43`) — strong coupling alpha_s(MZ). Read value at coordinate.

aS is an INDEPENDENT QCD input, NOT part of the EW set: it feeds ONLY the internal `G = 2*sqrt(aS)*sqrt(pi)` (`:289-293`), never the MW relation. (aS/SMINPUTS#3 is also name-locked at import — `ufo-loader-validation-gates.md`, `check_model_aS`.)

## 2. MW is INTERNAL (derived) — the load-bearing fact (sm parameters.py:295-299, loop_sm:331-335)
Both models declare, IDENTICALLY:
```python
MW = Parameter(name = 'MW',
               nature = 'internal',
               type = 'real',
               value = 'cmath.sqrt(MZ**2/2. + cmath.sqrt(MZ**4/4. - (aEW*cmath.pi*MZ**2)/(Gf*cmath.sqrt(2))))')
```
with `aEW = 1/aEWM1` internal (sm `:283-287`). So MW is derived from {aEWM1, Gf, MZ} via the tree EW relation.

Consequence (via `ufo-param-to-paramcard-chain.md` membership predicate = nature=='external'): MW nature='internal' -> ModelVariable, NEVER a ParamCardVariable -> **MW does NOT appear in the generated param_card MASS block and cannot be independently overridden.** The MASS block carries MZ [23] (`:125-131`), MT [6], MB, MC, MTA, MH — but NO PDG-24 entry (read each value at its coordinate). To change MW you change aEWM1/Gf/MZ. This is the alpha(MZ)-Gmu-mixed input scheme (three EW inputs aEWM1, Gf, MZ fix MW + weak mixing at tree level). Doc's single load-bearing check CONFIRMED.

## 3. No Gmu-input variant bundled on disk
Bundled model dirs under `$MADGRAPH_INSTALL/models/`: `sm`, `loop_sm`, `MSSM_SLHA2`, `hgg_plugin`, `taudecay_UFO` (+ `template_files`, `__pycache__`). There is NO `loop_qcd_qed_sm_Gmu` (or any `*Gmu*`/`*mu*`) directory. A Gmu scheme (MW an independent input, alpha_EW derived) is NOT available among bundled models; obtaining it would require an online-DB fetch / manual install — OUT of slice (installation / model-loader). Reported as on-disk fact only.

## 4. YUKAWA block — where the declared values live (sm parameters.py:77-123)
Six externals, `nature='external'`, `lhablock='YUKAWA'`: `ymc` [4], `ymb` [5], `ymt` [6], `yme` [11], `ymm` [13], `ymtau` [15] — read each value at parameters.py:77-123.

CORRECTS a hand-doc that conflated the Yukawa with the pole mass. The MECHANISM: `ymt` (YUKAWA[6], MSbar running mass driving the Hff coupling) is a DIFFERENT param in a DIFFERENT block from `MT` (MASS[6], pole mass, `:141-147`) — same lhacode 6, different block, different value. Read both coordinates fresh; do not conflate. Each ym* feeds an internal `y* = (ym*·√2)/vev` that the couplings.py GC_* reference (`:349-384`).

## Cautions
- **MW is not settable in default sm/loop_sm.** A user expecting a MASS-block PDG-24 line will not find one; MW tracks aEWM1/Gf/MZ. A run that "sets MW" via a hand-added MASS 24 line has no effect (the param is internal; no ParamCardVariable consumes it).
- **ymt ≠ MT.** Yukawa/MSbar (YUKAWA[6]) vs pole mass (MASS[6]) — different values, read each at its coordinate. Editing MASS[6] does not change the Htt coupling strength and vice-versa — decoupled inputs (same pattern as MB[5] vs ymb[5] in `ufo-param-to-paramcard-chain.md`).
- Online-DB download of a Gmu model, and which scheme a fetched model uses, are installation/model-loader territory — this page reports only what is on disk.
