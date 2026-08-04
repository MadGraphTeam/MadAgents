---
description: MSSM_SLHA2 has NO spectrum generator — NMIX/UMIX/VMIX mixing matrices AND neutralino masses are nature='external' card-read inputs; MG5 never recomputes them from EXTPAR/MASS, and update_dependent only ever refreshes the mass/width blocks (never a mixing block), so a hand-edited M1/M2/mu/tanβ leaves a STALE NMIX governing the Z-χχ coupling, clean run, no warning. Derived-quantity-staleness instance. HVT RHOINPUTS is a parallel external-input block (but a direct-input model, not a stale-derived one).
---

# MSSM_SLHA2 mixing matrices are external card inputs — NOT recomputed from EXTPAR (stale-NMIX)

The MSSM_SLHA2 model (`$MADGRAPH_INSTALL/models/MSSM_SLHA2/`) is a **pure UFO with no spectrum
generator inside it.** Every physical input that a real spectrum tool (SoftSUSY, SuSpect, …) would
*derive* — the neutralino/chargino masses and the full mixing matrices — is declared as a
`nature='external'` SLHA-block entry, read verbatim from `param_card.dat`. MG5 never diagonalizes
anything; it has no EXTPAR→spectrum step. This is the MSSM instance of the derived-quantity-staleness
pattern (sibling of width-representation-in-card.md's stale-width-after-mass-edit).

## NMIX is the 4×4 neutralino mixing matrix, every element `nature='external'`, `lhablock='NMIX'`
`models/MSSM_SLHA2/parameters.py` declares 16 NMIX entries (4×4), e.g. (L276-282):
```python
RNN1x1 = Parameter(name = 'RNN1x1', nature = 'external', type = 'real',
                   value = <default>, lhablock = 'NMIX', lhacode = [ 1, 1 ])
```
…through `RNN4x4` (lhacode `[4,4]`). All 16 are `nature='external'`, `type='real'`, `lhablock='NMIX'`
(grep: 16 `lhablock = 'NMIX'` lines, L281…L401). The card carries `Block NMIX` with the 16 rows
(`restrict_default.dat:138` `Block NMIX`).

These real externals are then **cast to complex by a trivial INTERNAL pass-through** — `NN1x1`
(`parameters.py:1444-1448`):
```python
NN1x1 = Parameter(name = 'NN1x1', nature = 'internal', type = 'complex', value = 'RNN1x1', ...)
```
i.e. `NNixj = RNNixj` — no arithmetic, just a real→complex retype. The complex `NNixj` is what the
couplings consume (`couplings.py:893` `(cw*ee*complex(0,1)*NN1x1*Rd4x4*cmath.sqrt(2))/...`). So the
card's NMIX numbers flow **verbatim** into the Z-χ̃χ̃ / γ-χ̃χ̃ / sfermion-neutralino couplings; there
is no recomputation anywhere between the card and the coupling.

(Marked-premise from ufo/physics, used only to motivate the impact: the Z-neutralino-neutralino
coupling ∝ N_i3 N_j3 − N_i4 N_j4 — the higgsino columns of NMIX. The param-card-slice fact is that
those N_ij are read straight from the NMIX block.)

## Neutralino MASSes are also `nature='external'`, `lhablock='MASS'` — NOT derived from EXTPAR
`parameters.py:748-778`: `Mneu1`/`Mneu2`/`Mneu3`/`Mneu4`, all `nature='external'`, `lhablock='MASS'`,
lhacode `[1000022]`/`[1000023]`/`[1000025]`/`[1000035]`. (Mneu3 ships with a NEGATIVE default value —
SLHA signed-mass convention; the sign is part of the external input, MG5 does not re-derive or re-sign
it. Read `MASS 1000025` in the generated card to see the signed default.) Chargino masses Mch1/Mch2
likewise external (L780+). So the neutralino
spectrum is card-supplied, not auto-computed from M1/M2/μ/tanβ.

## There is NO EXTPAR / MINPAR block in this model at all
`grep -oP "lhablock = '\K[^']+" parameters.py | sort -u` yields: DECAY DSQMIX FRALPHA HMIX MASS MSD2
MSE2 MSL2 MSOFT MSQ2 MSU2 NMIX SELMIX SMINPUTS SNUMIX TD TE TU UMIX UPMNS USQMIX VCKM VMIX YD YE YU.
**No EXTPAR, no MINPAR.** The high-scale inputs (M1,M2,μ,tanβ) a benchmark author thinks in terms of
have NO MG5-visible home as external parameters — the model's externals are the *outputs* of
diagonalization (masses + mixing matrices), not the *inputs* to it. `tan β` survives only inside
`HMIX` (3 entries) and `MSOFT` (`M1`,`M2`,`M3` are MSOFT lhacodes 1/2/3), but nothing in the model
reads those to rebuild NMIX/MASS — they are independent external lines. (External/internal counts are
drift-prone — read them fresh with `grep -c "nature = 'external'" parameters.py` and `... 'internal'`.)

## MG5 has no recompute path: `update_dependent` only touches mass/width, and only for DERIVED ones
The only consistency pass in the card layer is `ParamCard.update_dependent`
(`models/check_param_card.py:463`, docstring L464-465: *"update the parameter of the card which are not
free parameter (i.e mass and width)"*). It:
- applies the restriction `ParamCardRule` (L477-478),
- loops `model.get('particles')` and refreshes **only the `mass` block (L489-516) and the `decay`/width
  block (L518-539)** — it never iterates or writes NMIX/UMIX/VMIX.
- AND even for a mass, it rewrites only when
  `isinstance(mass, base_objects.ModelVariable) and not isinstance(mass, base_objects.ParamCardVariable)`
  (L495) — i.e. only model-DERIVED masses. External params build as `ParamCardVariable`
  (`import_ufo.py:2156-2157` `if param.nature == "external": parameter = base_objects.ParamCardVariable(...)`),
  so the L495 guard is **False** for Mneu1-4 → their MASS lines are never refreshed either.

So there is no stage — not `update_dependent`, not restriction, not treatcards/launch — at which MG5
recomputes NMIX (or the neutralino masses) from anything. A grep for `diagonalize`/`spectrum`/`EXTPAR`
across `models/MSSM_SLHA2/*.py` returns NOTHING. (`update_dependent` even being CALLED is itself
edit-time-tier and interactive-only — card-editor-update-commands.md / card-rewrite-tiers-edit-vs-inc.md
— but the point here is it would not touch NMIX even if it ran.)

## Consequence — the stale-NMIX trap on a hand-edited electroweakino benchmark
A user sets a benchmark by (M1,M2,μ,tanβ) and then edits the `MASS` block (and maybe `MSOFT`/`HMIX`)
to the new spectrum. Unless they ALSO regenerate the `NMIX` block (and the masses) consistently — by
running an external diagonalizer of the 4×4 neutralino mass matrix and writing the resulting rows
into `Block NMIX` — the NMIX in the card stays at
its shipped/previous values. The run is **clean, exit 0, no warning**: the stale higgsino columns
N_i3/N_i4 silently govern the Z-χ̃χ̃ coupling and the cross section is wrong. There is no
mass↔mixing↔EXTPAR consistency check anywhere in the card I/O layer (the validators
`make_valid_param_card`/`check_valid_param_card`/`check_param_card` apply only the restriction
`ParamCardRule` template, not a physics rule — width-representation-in-card.md §"NO consistency check").

This is sharper than the stale-width case: a width at least *can* be regenerated in-tool (`compute_widths`
/ `set WH Auto`). NMIX has NO in-tool regeneration — MG5 ships no neutralino diagonalizer — so the fix
is necessarily an EXTERNAL spectrum computation written back into the card. "Edit EXTPAR/MASS and launch"
is never sufficient.

## Fix
Regenerate NMIX **and** the neutralino/chargino MASS rows **and** any other affected mixing matrix
(UMIX/VMIX for charginos, plus the squark/slepton mixings if those soft terms moved) from the new
(M1,M2,μ,tanβ) using an external diagonalizer, and write all of them into `param_card.dat` together.
A self-consistent SLHA2 spectrum file produced by SoftSUSY/SuSpect/etc. and imported wholesale is the
clean path. There is no MG5 command that derives NMIX from EXTPAR.

## Parallel external-input block: HVT `RHOINPUTS` (a direct-input model, NOT a stale-derived one)
The `HVT` model (`models/HVT/parameters.py`)
declares a `RHOINPUTS` block of `nature='external'` reals: `gst` (lhacode 1, L68-74), `MVz` (lhacode 2,
L76-82), `cvvw` (3), `cq` (lhacode 4, L92-98), `cl` (lhacode 5, L100-106), `c3` (6), `ch` (lhacode 7,
L116-122), `cvvhh` (8), `cvvv` (9), `cvvvv` (10) — so the source RHOINPUTS map is
gst=1/MVz=2/cq=4/cl=5/ch=7 (read each at its cited Parameter line). RHOINPUTS is the same *structural* kind (external SLHA-block inputs read verbatim from the
card), BUT the physics distinction matters: HVT's RHOINPUTS ARE the fundamental Lagrangian
parameters/couplings — they are inputs, not diagonalization outputs — so there is no "stale derived
quantity" exposure within HVT. Editing a RHOINPUTS coupling is the intended way to set the physics;
nothing else needs regenerating to stay consistent. The NMIX exposure is specifically that NMIX is
*mathematically derived* from (M1,M2,μ,tanβ) yet the model treats it as an independent external input.

## Where this sits / cross-links
- Mechanism twin (mass/width version): width-representation-in-card.md (stale-width-after-mass-edit;
  same `update_dependent` ModelVariable-vs-ParamCardVariable guard).
- MSSM_SLHA2 card-format facts (native SLHA2, keep_external, no MG5_param.dat): mssm-slha2-name-gating.md.
- External-line existence rule (card line exists iff UFO Parameter nature=='external'):
  restriction-pruned-external-is-dropped.md — NMIX/MASS being external is exactly why they have card lines.
- Lead axes: derived-quantity-staleness.md (the value-that-must-be-regenerated-per-input principle) and
  param-card-setup-fanout.md (the parameter VALUE lifecycle).

## Cautions
- Do NOT tell a user "set M1/M2/mu/tanβ and MG5 will compute the neutralino mixing" — MG5 has no spectrum
  generator; NMIX/masses are card-read and used verbatim.
- The internal `NNixj` is a pure real→complex retype of the external `RNNixj` — do NOT mistake the
  internal-parameter declaration for a recomputation; it carries no arithmetic.
- A negative neutralino MASS value (Mneu3 ships with a negative default — read `MASS 1000025`) is the
  SLHA signed-mass convention, not a typo; MG5 reads the sign verbatim.
