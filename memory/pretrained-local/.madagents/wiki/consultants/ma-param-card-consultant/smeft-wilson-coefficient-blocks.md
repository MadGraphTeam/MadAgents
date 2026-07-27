---
description: How SMEFT Wilson-coefficient blocks (DIM6/DIM62F/DIM64F.../FCNC) appear in a generated param_card — per-operator UFO param→block/lhacode map (ctG=DIM62F 24, cQq83=DIM64F 1, cQlM1=DIM64F2L 1, Lambda=DIM6 1), the Lambda scale as block DIM6 lhacode 1, THREE distinct scale externals Lambda(DIM6 1)/mueft(Renor 1)/MU_R(LOOP 1) whose OPERATIVE mueft default is the restrict-card override not the raw UFO (restriction layer supersedes; the anti-merge comment keeps mueft/MU_R/MZ deliberately distinct so RestrictModel won't merge them — read each at its coordinate), restriction-pruned coeffs DROPPED from both card and ident_card, restrict-value-as-marker, NLO LOOP-block omission, the `set param_card BLOCK <index|name> value` resolution path (THREE addressing forms: block+index, block+name, bare-name — all valid), block names are MODEL-SPECIFIC (SMEFTatNLO=DIM6* NOT SMEFT/SMEFTcpv; SMEFTsim block/index maps are a GAP, model not installed), discovering WCs via `display parameters` / restrict card, and the "zero all other WCs not leave-at-default" lineage discipline (1e-10 and 0 both normal external floats). Anchored on SMEFTatNLO + dim6top_LO_UFO (v3.7.1).
---

# SMEFT Wilson-coefficient blocks in the param_card

Two local EFT models: `$MADGRAPH_INSTALL/models/SMEFTatNLO/` (NLO-capable, FeynRules-generated) and
`$MADGRAPH_INSTALL/models/dim6top_LO_UFO/` (LO). This page is param-card-slice: how the UFO
Wilson-coefficient external params surface as SLHA blocks, how restriction shapes the on-disk card, and
the EFT-specific override/edit hazards. Restriction ALGORITHM is the restriction slice; UFO param
CONTENT is the ufo slice — boundaries noted inline.

## UFO Wilson coefficients → param_card blocks (SMEFTatNLO)
`models/SMEFTatNLO/parameters.py` (external/internal counts drift-prone — `grep -c "nature = 'external'"`). Distinct `lhablock`s:
`DIM6 DIM62F DIM64F DIM64F2L DIM64F4L LOOP MASS Renor SMINPUTS YUKAWA` (grep `lhablock = '...'`).
The DIM6* family carries the Wilson coefficients; the naming tier is by operator class
(2-fermion `DIM62F`, 4-fermion `DIM64F`, 2-lepton `DIM64F2L`, 4-lepton `DIM64F4L`). **Block names are
MODEL-SPECIFIC, not a universal SMEFT convention.** Re-verified on the on-disk SMEFTatNLO_running param_card
+ parameters.py (`tests/input_files/SMEFTatNLO_running/`): the block headers are exactly
`DIM6 DIM62F DIM64F DIM64F2L DIM64F4L` — there is **NO `SMEFT` block and NO `SMEFTcpv` block** anywhere in
SMEFTatNLO. A doc that claims Wilson coefficients live in `SMEFT` (CP-even/real) + `SMEFTcpv` (CP-odd/imag)
is describing **SMEFTsim**, a DIFFERENT model — those names do NOT transfer to SMEFTatNLO/dim6top. **GAP:
SMEFTsim is not installed in this environment**, so its actual block names (`SMEFT`/`SMEFTcpv`?) and the
CP-even/CP-odd split are UNVERIFIED — do not assert them from a doc. dim6top_LO_UFO
uses blocks `DIM6 FCNC MASS SMINPUTS YUKAWA` — note `FCNC`, a model-specific block name.
Each coefficient is a plain external `Parameter` (parameters.py L46+): `nature='external'`,
`type='real'`, a `value`, `lhablock`, `lhacode=[N]`. They surface in the card by
the SAME generic mechanism as any external param (ParamCardWriter / ident_card — fresh-card-writers.md,
operative-source-chain.md). There is NO EFT-special read/write path; what differs is what restriction does.

## Operator → block/lhacode map (verified per-operator, SMEFTatNLO v3.7.1)
Each is a `nature='external'`, `type='real'` `Parameter` in `parameters.py` ⇒ a card line exists
(card-line-iff-external invariant). Confirmed by reading the Parameter def:
- `ctG` → block **DIM62F**, lhacode **24** (`parameters.py:278-284`).
- `cQq83` → block **DIM64F**, lhacode **1** (`parameters.py:286-292`).
- `cQlM1` → block **DIM64F2L**, lhacode **1** (`parameters.py:438-444`).
- `Lambda` → block **DIM6**, lhacode **1** (`parameters.py:46`) — the EFT SCALE,
  not a WC; zeroing it sends c/Λ²→∞ (NaN). (Lambda detail below.)
Read the default value at each cited Parameter def, or read the block/lhacode line in the generated card.
**Default-value caveat (mechanism, not the numbers):** the UFO defaults are NOT uniform — 2-fermion
dipole/Yukawa ops (e.g. `ctG`) ship an O(1) default, while 4-fermion ops (`cQq83`/`cQlM1`) ship a tiny
placeholder (order 1e-10), NOT 1.0. But the *operative* card value is the restrict-card value (the
scrambled-placeholder anti-merge idiom — restriction slice), NOT the UFO default; the UFO default only
governs an unrestricted `output` or a `set ... default`. (SMEFTsim, ABSENT here: `clq1` → block
`SMEFT` lhacode 35 — not verified here.)

## The Lambda scale IS a param_card entry, not a special parameter
`parameters.py:46` `Lambda = Parameter(name='Lambda', nature='external', value=<default>, lhablock='DIM6',
lhacode=[1])`. So the EFT cutoff scale Λ lives in the operative card as a `<value> # Lambda` line at lhacode 1
under `Block DIM6` (probe-confirmed present in the generated card; read `DIM6 1` for the default). It is read,
written, default-filled, and overridable exactly like a coefficient — and it has an ident line
(`dim6 1 mdl_Lambda`), so a hand-edit DOES reach Fortran. The Wilson coefficients occupy lhacode 2+ of
the same DIM6 block. dim6top's analogue: also block `DIM6`, `Lambda` at lhacode 1 (the SMEFT convention).

## THREE distinct scale externals — Lambda (DIM6 1) vs mueft (Renor 1) vs MU_R (LOOP 1)
Load-bearing card fact: SMEFTatNLO carries THREE separate scale-like external params in THREE separate
blocks — do not conflate them. Coordinates (external, `type='real'`; read each default at its line):
- **`Lambda`** → block **DIM6**, lhacode **1** (`:46-52`). The 1/Λ² suppression scale.
- **`mueft`** → block **Renor**, lhacode **1** (`parameters.py:654-660`). The EFT renormalization scale at
  which the Wilson coefficients are defined (no RG running in the UFO — a fixed input).
- **`MU_R`** → block **LOOP**, lhacode **1** (`:37-43`). The QCD renormalization scale used by the NLO/FKS
  machinery (dropped from the operative card for FKS — see the LOOP-block section).

**RAW UFO value ≠ OPERATIVE default — the restriction layer overrides `mueft`.** Per the operative-source
priority chain (UFO → restriction → output → user → treatcards), the restriction layer supersedes the raw
`parameters.py` value whenever the active `restrict_*.dat` sets that block/index. ALL FOUR SMEFTatNLO
restrict cards write a `Block Renor` lhacode-1 `mueft` line (`restrict_default.dat:189`,
`restrict_LO.dat:207`, `restrict_NLO.dat:207`, `restrict_NLO_no4q.dat:207`) that DIFFERS from the raw
`parameters.py:654` value. So the **OPERATIVE `mueft` default (what lands in a generated param_card) is the
restrict-card value, NOT the raw UFO value.** The raw value only governs an unrestricted `import` with no
restriction. Read the operative value via `display parameters` after `import model SMEFTatNLO-NLO`
(`mdl_mueft` in the external/settable group) or read `Renor 1` in the generated card.

**Why the three are kept slightly apart (the durable mechanism):** the restrict cards carry the comment
*"keep MZ, MU_R and mueft slightly different to avoid issues with restrictions"* (`restrict_default.dat:180`,
`restrict_LO/NLO/NLO_no4q.dat:198`). `mueft` (Renor 1), `MU_R` (LOOP 1) and `MZ` are written at
DELIBERATELY DISTINCT values precisely so `RestrictModel`'s identical-value merge does NOT collapse the
three into one external. So the three ARE distinct params AND distinct values — read each at its own
block/lhacode; never quote `mueft` as MU_R's value or as the raw UFO value.

## Additional named-WC block/lhacode (SMEFTatNLO v3.7.1, all external ⇒ card lines)
Extends the operator map above (each `nature='external'`, `type='real'` ⇒ card line):
- `cpG` → **DIM6 8** (`:102-108`) — gluonic operator, in the DIM6 block (not DIM62F).
- `ctp` → **DIM62F 19** (`:254-260`).
- `ctZ` → **DIM62F 22** (`:262-268`).
- `ctW` → **DIM62F 23** (`:270-276`).
- `cQq13` → **DIM64F 10** (`:342-348`).
(`ctG`=DIM62F 24, `cQq83`=DIM64F 1 already mapped above.) Durable pattern: 2-fermion dipole/Yukawa ops ship
an O(1) UFO default; 4-fermion ops ship a tiny placeholder (order 1e-10) — read the actual default at each
cited line. Operative card value is the restrict-card value, not these UFO defaults (restrict-value-as-marker
section).

## Conditional coefficients gated by configuration.py (the param-card composition is config-dependent)
`parameters.py:11` `if configuration.bottomYukawa:` wraps `ymb` (YUKAWA 5) AND `cbp` (DIM62F 18).
`configuration.py` ships `bottomYukawa = False`, so by default `cbp` is NOT declared as a param at all —
it never appears in any block. Flipping the model's `configuration.py` flag adds a DIM62F lhacode-18 line
to every freshly-generated card. **So the set of Wilson-coefficient param-card lines is not fixed by the
model name; it depends on the UFO `configuration.py` flags** — a fresh `output` with the flag toggled
yields a different DIM62F block. (The conditional-declaration mechanism is ufo-slice; the param-card
consequence — a block line appears/disappears — is ours.)

## Restriction shapes the card: pruned coeffs are DROPPED, not zeroed (SMEFT-critical)
(Model-independent form of this drop mechanism — and how it differs from value-overwriting rules and
from internal params — is restriction-pruned-external-is-dropped.md; this section is the SMEFT instance.)
SMEFTatNLO ships FOUR restrict cards — `restrict_default.dat restrict_LO.dat restrict_NLO.dat
restrict_NLO_no4q.dat` (ASCII, ISO-8859-1 texname comments — read with `iconv -f ISO-8859-1`). Each is a
FULL param_card used as the restriction template. The restriction marks pruning by value:
- **`0.000000` ⇒ prune.** A coefficient with restrict value `0.000000` is removed by RestrictModel
  (`models/import_ufo.py`, restriction slice) and **does not appear in the generated operative card at
  all — nor in `ident_card.dat`.** Probe (model `SMEFTatNLO-NLO`, `p p > t t~ ... NP=2 [QCD]`,): restrict_NLO sets `cG` (DIM6 7) and `cpG` (DIM6 8) to `0.000000`; the operative
  card's `Block dim6` skips the cG/cpG lhacodes (absent) and `ident_card.dat` has no `dim6 7`/`dim6 8`
  line. **Pruning produces lhacode GAPS in the block.** The DIM62F operative lhacode set exactly matched
  restrict_NLO's nonzero lhacodes (the zeroed ones pruned) — value source is the restrict card verbatim
  (a restrict `<float>` re-emits as the same `<float>` in the card, no rounding).
- **distinct non-zero values ⇒ keep, and keep DISTINCT.** restrict_NLO's DIM6 lines are random-looking,
  all different placeholders. This is the restriction's
  "don't merge these params" technique: identical values would let RestrictModel collapse two coefficients
  into one; distinct values keep each coefficient an independent external. (This is the EFT analogue of —
  but DIFFERENT from — the SM `9.999999e-1`/`0.000001e-99` sentinels in fresh-card-writers.md, which the
  writer rounds to 1/0. SMEFT restrict cards use genuinely distinct floats, NOT those two magic strings;
  the values are NOT rounded on write — they pass through verbatim.)
- **LO vs NLO differ in WHICH coeffs are pruned, not block structure.** `diff` of the LO/NLO block
  headers is empty (same blocks), but `cG`/`cpG` (DIM6 7/8) are NONZERO in restrict_LO and ZEROED in
  restrict_NLO — the gluonic operators are pruned at NLO. So the chosen `MODELNAME-restriction`
  determines which Wilson-coefficient lines exist in the card. `restrict_NLO_no4q` drops the 4-quark
  operators on top.

## NLO ([QCD]/FKS) drops the LOOP block (MU_R) from the operative card
`parameters.py:37` `MU_R` is external, `lhablock='LOOP'`, lhacode [1] (read the default there). In the probed
NLO/FKS card the **LOOP block is ABSENT from both `param_card.dat` AND `param_card_default.dat`**, yet
`ident_card.dat` HAS `loop 1 MU_R` (so MU_R still reaches Fortran). Cause:
`models/write_param_card.py:206-207` `if not write_special and param.lhablock.lower() == 'loop':
continue` — the generic ParamCardWriter skips the entire LOOP block when `write_special=False`, and
`export_v4.py:9846-9854` (`create_param_card` method, body starts L9840) forces `write_special=False`
for the FKS exporter (`export_fks.ProcessExporterFortranFKS`, L9853-9854) and loop-induced — verified:
`write_special = True` default L9846, force-`False` for FKS/LoopInduced L9854. So for an NLO SMEFT run the renormalization
scale MU_R is read via the scale-row / hardcoded-`loop`-block fallback in `write_inc_file`
(operative-source-chain.md; read the hardcoded default there), NOT from an editable card line. The `Renor` block (`mueft`, Renor 1) is a
normal external and IS written. Header on the probed card was the GENERIC writer banner
("AUTOMATICALLY GENERATED BY MG5 FOLLOWING UFO MODEL"), confirming the `create_param_card_static`→
`ParamCardWriter` path (not the per-model UFO writer), with block names lowercased on the
Block round-trip (`Block dim6`, expected — data-model-classes.md).

## Flow of a user-set Wilson coefficient to the matrix element
Identical to any external param: edit `Block dim6 / <code> <value>` in the operative card → `do_treatcards`
→ `write_inc_file` looks up the value via the ident line → emits `mdl_<name> = <value>d0` to
`param_card.inc` → compiled into `coupl.inc`. The coefficient is `nature='external'`, so it is read from
the card (NOT recomputed Fortran-side — contrast SM dependent params, MEMORY.md). The full priority chain
(UFO default → restriction prune → output writes card → user edit → treatcards read) is
operative-source-chain.md; nothing EFT-special overrides it. SLHA1↔SLHA2 is a non-issue: the DIM6* blocks
are not MSSM mixing blocks, `usqmix` is absent, so `convert_to_slha1`/`secure_slha2` no-op (slha1-slha2-conversion.md).

## `set param_card <block> <lhacode|name> <value>` — THREE addressing forms (v3.7.1, re-verified)
`AskforEditCard.do_set` (`common_run_interface.py:5868`). Entry branch line drifted since first cache:
the explicit-block branch is now `:6117` (`args[start] in self.param_card ... and card in ['','param_card']`),
not `:6097`. Three interchangeable ways to name the same coefficient:
- **block + integer index** (`set param_card DIM62F 24 0.5`): `args[start+1]`='24' is NOT a param NAME in
  `pname2block`, so the `else` at `:6148-6150` builds `key = tuple([int(i) for i in args[start+1:-1]])` → `(24,)`.
- **block + param NAME** (`set param_card DIM62F ctG 0.5`): `args[start+1]`='ctG' IS in `pname2block`, so
  `:6133-6139` resolves `all_var = self.pname2block['ctG']` and picks the `lhaid` whose `bname` matches the
  given block (`DIM62F`). If the name isn't in that block it warns `... is not part of block ... but ...` and
  returns (`:6141-6143`).
- **bare NAME, no block** (`set ctG 0.5` or `set param_card ctG 0.5`): enters the no-block branch `:6187`
  (`args[start] in self.pname2block`); `:6194-6198` re-issues `param_card <block> <lhaid> <value>` for every
  (block,lhaid) the name maps to, recursing into the block-name branch. A name mapping to >1 param sets ALL
  and warns (`:6199-6203`).
Common tail: `:6163` `if key in self.param_card[args[start]].param_dict:` confirms the lhacode exists;
`:6175` `value = float(args[-1])`; `:6180` `self.setP(args[start], key, value)`. `setP` (`:6443`) stores the
float into `param_dict[key].value`. A lhacode NOT in the block (pruned coeff → gap in `param_dict`) → `:6182`
`invalid set command` warning, no-op (the pruned-coeff silent-inert caution below is the ME face of the same
gap). So for a WC in ANY EFT model, both `set param_card <BLOCK> <index> <v>` and `set param_card <BLOCK>
<name> <v>` (and bare `set <name> <v>`) are valid — index-vs-name addressing is a free choice.

## 1e-10 and exact-0 are both normal external floats (the "zero all other WCs" discipline)
Probe (ParamCard read+write round-trip): setting a DIM62F coeff to `1e-10` re-emits `24 1.000000e-10`;
setting it to `0.0` re-emits `24 0.000000e+00`. Both are accepted as ordinary external float values — no
special-casing, no rounding, no rejection. So a recipe that does `set <WC> 1e-10` or `set <WC> 0` writes a
plain card line that reaches Fortran via the ident path like any other coefficient.
**The "leave the others at default" trap (card-I/O lineage):** the generated card's per-WC value is NOT
0 and NOT the UFO default — it is the restrict-card scrambled placeholder, written VERBATIM into the
operative card (restrict value → `output` writes card → user edit → `treatcards` read; restrict-value-as-
marker section above — a distinct nonzero placeholder, not zero). So a pure-bin recipe (one target WC, rest off) that says
"leave the others at default" leaves every non-target coefficient at its NONZERO scrambled placeholder →
σ(c_target=0) ≠ 0 when it should be exactly 0. The card-I/O fix is to explicitly write 0 (or 1e-10) for
every non-target WC; "default" here means the placeholder, not zero. (WHICH WCs the chosen restrict card
keeps + the anti-merge idiom origin = restriction slice; the NP^2 bin selection = coupling-order slice.)
**1e-10-vs-0 for the zeroed WCs is a model/counterterm fact, not card-I/O** — the reference claims exact-0
can trip a division-by-zero in some SMEFTatNLO R2 counterterms; whether that pathology is real and whether
1e-10 cures it is nlo-model/madloop's slice. The card-slice answer: the card accepts, writes, and reads
back BOTH `1e-10` and exact `0` as valid external floats; neither is malformed at the I/O layer.

## Discovering the WC parameter set of a loaded EFT model (enumeration, boundary note)
Two valid ways to enumerate which Wilson coefficients exist before editing the card:
- **`display parameters`** (mg5 REPL, `madgraph_interface.py:3676-3701`) — prints ALL loaded-model
  parameters grouped by type key, with the `('external',)` group sorted FIRST (`key_sort` returns -1,
  `:3681-3686`); externals print `name = value`, derived print `name = expr = value`. It reads
  `self._curr_model['parameters']` (the loaded UFO model dict), NOT the param_card. It reflects the
  **post-restriction** model (restriction runs at import), so a pruned coefficient will NOT appear in the
  `('external',)` group — which is precisely the set that becomes the card's editable lines. So
  `display parameters` and the generated card agree on which externals survive. (The command itself is
  model-loader/ufo REPL territory; the param-card-slice fact is the `('external',)` ↔ card-line correspondence.)
- **Inspecting the active `restrict_*.dat`** — each is a FULL param_card (my read-write mechanics apply);
  its nonzero-valued lines are the WCs the restriction keeps. Reading the restrict card is the restriction
  slice's file, but the SLHA parsing is mine; it lists the same surviving-external set.
Both reflect post-restriction survivors; neither invents block names. Use them to get real WC NAMES rather
than reciting a doc's index map. (SMEFTsim index↔name maps are GAP here — see the block-name section.)

## Cautions (SMEFT-specific)
- **A pruned coefficient cannot be activated by hand-editing the operative card.** If your chosen
  restriction zeroed coefficient C, C has NO ident line, so adding `<code> 0.5 # C` to the card is
  SILENTLY IGNORED at the matrix element (no warning at inc-time — the read-filter simply never names it).
  To turn C on you must pick a restriction that keeps C (e.g. `-LO` vs `-NLO`) or use the unrestricted
  model — re-`output`, not a card edit. This is the EFT face of the operative-source-priority surprise.
- **Wrong restriction = wrong operator basis silently.** LO vs NLO vs NLO_no4q prune different
  coefficients; picking `SMEFTatNLO` bare vs `SMEFTatNLO-NLO` changes which DIM6* lines exist. A user who
  expected `cG` and got a card without a DIM6 lhacode-7 line chose a restriction that pruned it.
- **lhacode gaps are normal**, not corruption — they mark pruned operators. Do not "fill them in"; the
  values would be inert (no ident line).
- **Lambda is editable and reaches the ME** (DIM6 1) — but coefficients are dimensionless c_i with the
  1/Λ^n already factored in the UFO couplings; changing Λ rescales, changing a c_i is the operator
  strength. (The exact Λ-power per coupling is ufo-slice / couplings.py.)
- **The conditional `cbp`/`ymb` (bottomYukawa) lines exist only if the model's configuration.py flag is
  True** — a card generated with the default model will not have DIM62F lhacode 18.

## Probe-candidates (cheap, confirmed inline)
- [DONE] `SMEFTatNLO-NLO`, `p p > t t~ NP=2 [QCD]`: cG/cpG (DIM6 7/8) absent from operative card AND
  ident_card; LOOP block absent from both cards but `loop 1 MU_R` present in ident_card; DIM62F lhacode
  gaps match restrict_NLO nonzero set; values verbatim from restrict card.
## Probe-candidates (SMEFTsim-specific GAPs — blocked: model not installed)
- **SMEFTsim block names + CP-split**: confirm whether SMEFTsim's WCs live in `SMEFT`(real)+`SMEFTcpv`(imag)
  or another block layout, and the per-operator index↔name map (doc claim `SMEFT 15 == ctGRe`). Requires
  `install SMEFTsim` (or an external UFO drop) → `import model SMEFTsim...`, `display parameters`, read the
  generated card block headers. UNVERIFIABLE until the model is present — do NOT cache index maps on doc word.
- **name-vs-index addressing on SMEFTsim**: once installed, confirm `set param_card SMEFT 15 1.0` and
  `set param_card SMEFT ctGRe 1.0` both hit the same coefficient (the three-form addressing above is
  model-independent do_set logic, so expected yes — but the 15↔ctGRe identity is the SMEFTsim-specific part).

## Probe-candidates (expensive, not run)
- Hand-edit a KEPT coefficient (e.g. DIM6 2 cpDC) to a new value, `launch -f`, confirm it propagates to
  `param_card.inc` as `mdl_cpDC = <newval>` (expected: yes, it has an ident line). One line.
- Confirm a hand-added PRUNED coefficient line (e.g. `7 0.9 # cG`) is silently ignored end-to-end (no
  inc-file line, no warning) on a `launch -f` — the cautioned silent-ignore. One line.
- dim6top_LO_UFO has NO restrict_*.dat shipped (only parameters.py + write_param_card.py): confirm
  `import model dim6top_LO_UFO` with no `-restriction` writes ALL externals (no pruning) and whether
  the `FCNC` block round-trips. One line.
