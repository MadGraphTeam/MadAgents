---
description: SMEFTsim_topU3l_MwScheme_UFO (when present under models/) — NP=1/insertion, coupling_orders (NP/NPprop/SMHLOOP + per-Wilson-coeff NPc orders), block naming (SMEFT/SMEFTcpv/SMEFTcutoff), restrict file names, source-verified for the topU3l variant; other flavor/scheme variants stay GAP.
---

# SMEFTsim at LO — grounded for topU3l_MwScheme (v3.7.1)

**Install-state is session-specific (`ls models/` first — see bundled-eft-models.md).** The facts below were
SOURCE-VERIFIED against `models/SMEFTsim_topU3l_MwScheme_UFO/` when present. That variant
is NOT bundled and can be absent on a given install (`ls models/` first); when present its files are
`coupling_orders.py`, `couplings.py`, `parameters.py`, `vertices.py`, `decays.py`,
`restrict_massless.dat`, `restrict_SMlimit_massless.dat`, `param_card_massless.dat`, `version.info`.
Re-resolve each cited coordinate against the installed copy before relying on it. Values specific to OTHER
flavor/scheme variants (U35, MFV, general; alphaScheme) remain GAP — only topU3l_MwScheme was ever on disk here.

## 1. Variant taxonomy — still package-layout, only topU3l_MwScheme present
Doc: variants = flavor {U35, MFV, top, topU3l, general} × scheme {MwScheme=(MW,MZ,GF),
alphaScheme=(αEW,MZ,GF)}; dir `SMEFTsim_<flavor>_<scheme>_UFO`. Nothing in MG5 fixes this — model-package
layout. GROUNDED: exactly one variant installed, `topU3l_MwScheme`. Other variants GAP (install to read).

## 2. NP per insertion = 1 — SOURCE-CONFIRMED (was ANCHORED)
`SMEFTsim_topU3l_MwScheme_UFO/couplings.py` (when present): NP-bearing couplings carry `'NP':1`;
grep for `'NP':2`/`'NP':3` returns none. So **p = 1** for SMEFTsim. Contrast SMEFTatNLO p=2 (`'NP':2`).
(Recipe: `grep -oE "'NP':[0-9]+" couplings.py | sort | uniq -c` — only `:1` appears; don't cache the tally.)
`coupling_orders.py`: `NP` has `expansion_order = 99` (a CAP, NOT the per-insertion increment — the increment
is read from `couplings.py order={...}`, here always 1). This is the trap: **do not read the per-insertion
value off `expansion_order`** — SMEFTsim's NP expansion_order=99 would wrongly suggest a large increment.

Bin rule with p=1 (a squared bin `NP^2==N` selects two amps whose NP powers sum to N):
- σ_SM = `NP^2==0`; σ_int (SM×EFT, 1 insertion) = `NP^2==1`; σ_quad (EFT×EFT) = `NP^2==2`.
So the common doc table (SM=`==0`, int=`==2`, quad=`==4`) is the **p=2 SMEFTatNLO** pattern and is WRONG for
SMEFTsim. Bin number N is NOT portable across EFT UFOs — read the per-insertion value first. Odd bins are
NOT empty for SMEFTsim (unlike SMEFTatNLO): amplitude NP can be odd, so `NP^2==1` is the interference bin.

## 3. coupling_orders.py order zoo — SOURCE-CONFIRMED
`SMEFTsim_topU3l_MwScheme_UFO/coupling_orders.py` (when present) declares, besides QCD/QED:
- `SMHLOOP` expansion_order=99, hierarchy=99 (the SM loop-induced-Higgs guard order — CONFIRMED to exist).
- `NP` expansion_order=99, hierarchy=99 (global EFT order; per-insertion +1, see §2).
- `NPprop` expansion_order=**0**, hierarchy=99 (propagator-correction order).
- `NPshifts`, `NPcpv` expansion_order=99; plus **one per-operator order per Wilson coefficient**
  `NPc<coeff>` (NPcbb, NPcbG, NPctG, NPcHW, …) each expansion_order=99, hierarchy=1 — so a single coefficient
  can be isolated by its own order (e.g. `NPctG<=1`). This per-operator-order design is SMEFTsim-specific;
  SMEFTatNLO has NO per-operator orders (only the global NP).

`NPprop expansion_order=0` doc mechanism REFUTED at MG core (unchanged finding): `base_objects.py:3766`
`[(k,v) … if 0 < v < 99]` — v=0 fails `0<0`, so expansion_order=0 gets NO amplitude cap (behaves like 99),
NOT auto-excluded. See eft-expansion-order-and-weighted-default-cap.md.

## 4. Block naming — SMEFT / SMEFTcpv / SMEFTcutoff (NOT DIM6*)
`parameters.py` lhablock census (when present): `SMEFT` (129 params), `SMEFTcpv` (53), `SMEFTcutoff` (1,
the Λ cutoff), plus SMINPUTS/MASS/YUKAWA/DECAY/SWITCHES. So SMEFTsim uses ONE big `SMEFT` block (+ CPV split
`SMEFTcpv`), whereas SMEFTatNLO fragments by fermion content (DIM6/DIM62F/DIM64F/DIM64F2L/DIM64F4L)+Renor.
**Block name is per-model — a `block=DIM6` naming is SMEFTatNLO-only, and even there only for bosonic ops.**
The Λ cutoff lives in `SMEFTcutoff` (SMEFTsim) vs `DIM6` lhacode 1 (SMEFTatNLO). Read parameters.py per model.

## 5. Re/Im coeff naming — topU3l has real+imag split; per-variant names still GAP
SMEFTsim v3 splits complex WCs into `<op>Re`/`<op>Im`; the `SMEFTcpv` block (53 params) is the imaginary
side. topU3l coeff names (e.g. ctGRe) are read-able from this tree; U35 (`cuGRe`) / general (`cuG1x3Re`)
remain GAP. SMEFTsim↔SMEFTatNLO map anchor (SMEFTatNLO side confirmed): `ctGRe`↔`ctG`, `cHGRe`↔`cpG`,
`ctHRe`↔`ctp`. → PROBE-CANDIDATE (cheap): grep `SMEFTsim_topU3l_MwScheme_UFO/parameters.py` for the exact
topU3l coeff spelling + SMEFT-block lhacode of ctG/cHG/ctH analogues.

## 6. Restriction files — NAMES now CONFIRMED for topU3l
`restrict_massless.dat` and `restrict_SMlimit_massless.dat` BOTH present for topU3l when the model is on disk. Mechanism (transfers, grounded elsewhere): `SMlimit_massless` zeroes the WCs → zero-coupling NP
vertices removed → order validation (from SURVIVING interactions) rejects `NP=…` with "model order NP not
valid for this model"; `massless` keeps WCs nonzero → NP available. → PROBE-CANDIDATE: does bare
`import model SMEFTsim_topU3l_MwScheme_UFO` (no `-restriction` suffix) apply a default restriction? (there is
no `restrict_default.dat` in this tree — only massless / SMlimit_massless — so bare-import default behaviour
must be tested, not assumed.)

## Bottom line
Now GROUNDED for topU3l_MwScheme: NP=1/insertion (couplings.py `'NP':1`), coupling_orders zoo
(SMHLOOP/NPprop=0/NP + per-Wilson-coeff `NPc<coeff>` orders), block naming SMEFT/SMEFTcpv/SMEFTcutoff, restrict file names
massless/SMlimit_massless. Bin map int=`NP^2==1` quad=`NP^2==2`. Still GAP: other flavor/scheme variants,
exact topU3l Re/Im coeff spellings, bare-import default-restriction behaviour.
