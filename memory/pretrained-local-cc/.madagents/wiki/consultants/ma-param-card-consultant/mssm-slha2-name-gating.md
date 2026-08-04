---
description: The shipped MSSM is MSSM_SLHA2, not legacy 'mssm'; the SLHA1-conversion + MG5_param.dat branches key on name=='mssm'/'mssm-*' and DO NOT fire for MSSM_SLHA2 — its on-disk card is native SLHA2 (probe-confirmed v3.7.1). Plus the fresh-vs-roundtrip block-name casing dichotomy.
---

# MSSM_SLHA2 vs legacy 'mssm': the SLHA1/MG5_param.dat branches are DEAD for the shipped model

**Correction to operative-source-chain.md / slha1-slha2-conversion.md / fresh-card-writers.md**, all of which
describe "the MSSM family routes through MG5_param.dat / is written SLHA1" without flagging that the
shipped MSSM model does NOT trigger those branches. In v3.7.1 the legacy `mssm` model is **gone**.

## The legacy `mssm` name is retired; the shipped model is `MSSM_SLHA2`
- `$MADGRAPH_INSTALL/models/` ships `MSSM_SLHA2/` (with `restrict_default.dat`, `restrict_no_b_mass.dat`,
  `restrict_no_masses.dat`, `restrict_no_tau_mass.dat`). There is **no `mssm/` dir.**
- `import model mssm` is intercepted and errors: `import_ufo.py:207-208` / `:215-216`
  `logger.error("mssm model has been replaced by MSSM_SLHA2 model. The new model require SLHA2 format...")`.
- Model `name` = the directory basename: `import_ufo.py:412` `model.set('name', os.path.split(model_path)[-1])`.
  So importing `MSSM_SLHA2` gives `model.get('name') == 'MSSM_SLHA2'` (plus `-restriction` suffix if any,
  appended L256-257). It is **never** normalized to `'mssm'`.

## The SLHA1-conversion / MG5_param.dat branches gate on the literal string `'mssm'`
All these checks are `name == 'mssm' or name.startswith('mssm-')` — `MSSM_SLHA2` matches NEITHER:
- **Output-time MG5_param.dat:** `export_v4.py:4659` `if modelname == 'mssm' or modelname.startswith('mssm-'):`
  → `convert_to_mg5card(param_card, MG5_param.dat)`. (`modelname = self.opt['model']`, L4658.)
- **Output-time SLHA1 collapse:** `export_v4.py:9833` (inside `create_param_card_static`, `mssm_convert=True`)
  `if model_name == 'mssm' or model_name.startswith('mssm-'):` → `make_valid_param_card` + `convert_to_slha1(output_path)`.
  (`model_name = model.get('name')`, L9831.)
- **Run-time MG5_param.dat:** `madevent_interface.py:3211-3212` `tmp_model = os.path.basename(model)` then
  `if tmp_model == 'mssm' or tmp_model.startswith('mssm-'):` → `convert_to_mg5card(...MG5_param.dat)`,
  `opt['param_card'] = .../MG5_param.dat`. Else branch (L3219) just `check_valid_param_card`.
  (`model = self.find_model_name()` reads `proc_card_mg5.dat`'s `import model <X>` line, common_run_interface L4311/4341.)

`os.path.basename('MSSM_SLHA2') == 'MSSM_SLHA2'` ≠ `'mssm'` and does not `startswith('mssm-')` → **else
branch every time.** These three branches are effectively dead code for the only MSSM that ships.

## What MSSM_SLHA2 DOES trigger: keep_external (SLHA2 params survive restriction)
`import_ufo.py:298-305` is an **`if/elif/elif/else` — mutually exclusive, first match wins** (verbatim):
```python
blocks = model.get_param_block()                                     # :297
if model_name == 'mssm' or os.path.basename(model_name) == 'mssm':   # :298  branch (a)
    keep_external=True
elif all( b in blocks for b in ['USQMIX','SL2','MSOFT','YE','NMIX','TU','MSE2','UPMNS']):  # :300 branch (b)
    keep_external=True
elif model_name == 'MSSM_SLHA2' or os.path.basename(model_name) == 'MSSM_SLHA2':  # :302 branch (c)
    keep_external=True
else:
    keep_external=False
```
**MSSM_SLHA2 matches branch (c) ONLY** — NOT branch (b). "Hits both" is structurally impossible: `if/elif`
short-circuits on the first match. And branch (b) does not even match: its `all(...)` requires a block
literally named **`SL2`**, but the model declares **`MSL2`**, not `SL2`:
- `get_param_block()` (`import_ufo.py:2819-2823`) returns `set([p.lhablock for p in self['parameters'][('external',)]])`.
- `models/MSSM_SLHA2/parameters.py` declares `lhablock = 'MSL2'` (3 entries); there is **no** `SL2` lhablock.
- `models/MSSM_SLHA2/restrict_default.dat` has `Block MSL2`, no `Block SL2`.
- So `'SL2' in blocks` is **False** → the `:300` `all(...)` is **False** → branch (b) does NOT fire;
  evaluation falls through to the explicit `:302-303` `MSSM_SLHA2` branch, the only branch that matches.

`keep_external=True` → "Detect SLHA2 format. keeping restricted parameter in the param_card" (L307) →
`restrict_model(..., keep_external=True)` keeps the SLHA2 mixing/soft externals as editable card lines
instead of pruning them (restriction-slice owns the algorithm; the param-card consequence is that the
mixing blocks appear in the card).

## Probe — MSSM_SLHA2 card is native SLHA2 end to end (v3.7.1, this install)
`import model MSSM_SLHA2; generate g g > go go; output <PROC_DIR>`:
- **Operative `Cards/param_card.dat` blocks:** `dsqmix fralpha hmix mass msd2 mse2 msl2 msoft msq2 msu2
  nmix QNUMBERS selmix sminputs snumix td te tu umix upmns usqmix vckm vmix yd ye yu`. These are SLHA2.
- **NO SLHA1 markers** (`stopmix sbotmix staumix au ad ae modsel alpha`) present — the card is NOT collapsed
  to SLHA1. (`fralpha`, not `alpha`; `td/tu/te`, not `ad/au/ae`; `msq2/msl2`, not `msoft 31..49` only.)
- **No `Source/MODEL/MG5_param.dat`** at output time (export_v4:4659 didn't fire) NOR after
  `./bin/madevent treatcards param` (madevent_interface:3212 didn't fire).
- `ident_card.dat` carries the SLHA2 mixing externals directly (`usqmix 1 1 mdl_RRu1x1`, `usqmix 3 6
  mdl_RRu3x6`, ...) so the mixing-matrix elements are **editable and reach Fortran natively.**
- `Source/param_card.inc` (treatcards output) carries them as Fortran lines:
  `MDL_RRD3X6 = <value>D0`-style — read straight from the SLHA2 card, no SLHA1 round-trip.

So for a shipped-MSSM run the `convert_to_slha1`/`convert_to_mg5card`/MG5_param.dat machinery in
slha1-slha2-conversion.md is **present but never exercised**. Those routines remain reachable only via a model
literally named `mssm`/`mssm-*` (none ships) or a hand `import model mssm-<restr>` that resolves to an
actual `mssm/` dir (none ships) — i.e. dead in a stock install. The SLHA1↔SLHA2 *conversion code itself*
is still callable directly (e.g. via the editor's `update to_slha1`/`update to_slha2` commands —
card-editor-update-commands.md), which is how an SLHA1 MSSM card a user pastes in gets converted; but the
automatic output/treatcards MSSM-family path does not fire on `MSSM_SLHA2`.

## Custom FeynRules block-name casing dichotomy (fresh writer ≠ ParamCard round-trip)
BSM models declare arbitrary non-SLHA-standard lhablocks that round-trip via the GENERIC Block mechanism,
untouched by `secure_slha2`/`convert_to_*` (those act only on the MSSM mixing-block signature):
- 2HDMtypeII: `FRBlock Higgs LOOP MASS SMINPUTS YUKAWA`; 2HDM5F_NLO: `CKMBLOCK Higgs YukawaGDI..YukawaGUR
  LOOP ...`; SMEFTatNLO: `DIM6 DIM62F.. Renor LOOP`; dim6top_LO_UFO: `DIM6 FCNC`. (lhablock declarations
  in each `parameters.py`.)
- **The fresh card emits block names LOWERCASE.** `models/write_param_card.py:235/237`
  `self.fsock.write("""Block %s ...""" % name.lower())`. Probe: 2HDMtypeII fresh card shows
  `Block frblock` / `Block higgs` (lowercase), matching the SMEFT `Block dim6` probe.
- **A ParamCard read+write round-trip emits block names UPPERCASE.** `check_param_card.py:292/307`
  `Block.__str__` writes `## INFORMATION FOR <NAME>.upper()` and `BLOCK <NAME>.upper()`. So any card that
  passed through `ParamCard.write()` (the `update dependent` editor, scan restore, an auto-conversion) gets
  `BLOCK FRBLOCK`, while a freshly-`output`'d card has `Block frblock`.
- **Both load identically** — `Block.__init__` (check_param_card.py L166) lowercases the name, and ParamCard
  keys are lowercased on `__setitem__`. The on-disk casing is cosmetic; it just tells you WHICH writer last
  touched the card (lowercase = fresh ParamCardWriter; uppercase = a ParamCard.write round-trip).

## Cautions
- Do NOT tell a user "your MSSM card will be written in SLHA1 / there's an MG5_param.dat" — true only for a
  model literally named `mssm`, which v3.7.1 does not ship. `MSSM_SLHA2` is native SLHA2 throughout.
- The SLHA1↔SLHA2 conversion routines (slha1-slha2-conversion.md) are still the right answer for a user *pasting
  in* an SLHA1 spectrum and converting via the editor's `update to_slha2`; they are NOT auto-invoked by
  output/treatcards for `MSSM_SLHA2`.
- A particle/block appearing UPPERCASE vs lowercase in an MSSM/BSM card is not corruption — it marks whether
  the card is fresh-from-output or has been round-tripped through ParamCard.write.

## Probe-candidates (cheap, confirmed inline)
- [DONE] `MSSM_SLHA2 g g > go go output`: native-SLHA2 card, no MG5_param.dat at output, no MG5_param.dat
  after `treatcards param`, SLHA2 mixing externals in ident_card + param_card.inc.
- [DONE] 2HDMtypeII fresh card: custom blocks `Block frblock`/`Block higgs` lowercase.
## Probe-candidates (expensive, not run)
- Confirm the editor `update to_slha1` on an MSSM_SLHA2 card produces a valid SLHA1 spectrum (the
  conversion routine works on demand even though output doesn't auto-call it). One line.
