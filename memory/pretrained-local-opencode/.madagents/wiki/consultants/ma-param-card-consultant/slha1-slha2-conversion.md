---
description: SLHA1 <-> SLHA2(MG5) conversion machinery in check_param_card.py — convert_to_slha1, convert_to_mg5card, the inc-time (secure_slha2) and model-read-time auto-conversion firing points, CMS conversion, output-time MSSM->SLHA1. (MSSM-specific; keyed on usqmix; auto-fires only for a model literally named mssm/mssm-* — DEAD for shipped MSSM_SLHA2.) Validation/rule-engine is in param-card-validation-rule-engine.md.
---

# SLHA1 <-> SLHA2 conversion machinery (`$MADGRAPH_INSTALL/models/check_param_card.py`)

This page is the **conversion** half of the param-card I/O machinery (slha1<->slha2 transforms
+ their firing points + CMS conversion). The **validation/rule-engine** half (ParamCardRule,
analyze_param_card, make_valid/check_valid) is param-card-validation-rule-engine.md.

## Detection key: `usqmix`
Both conversion routines decide format by presence of the `usqmix` block: present ⇒ SLHA2/MG5 format;
absent ⇒ SLHA1.

## `convert_to_slha1(path, outputpath=None)` — L1449
If `usqmix` absent → already slha1, just write and return (L1455-1458). Otherwise (MSSM SLHA2→SLHA1):
- Copies masses into `sminputs` (top→6, tau→7, Z→4; L1462-1464), sets `modsel 1 = 1` (L1468).
- Reconstructs `sminputs 2` (G_F) from alpha/Mz/Mw if missing (L1477-1482, formula `pi/sqrt(2)/aem1 * mz^2/mw^2/(mz^2-mw^2)`).
- Collapses the diagonal-identity mixing blocks (usqmix/dsqmix/selmix/snumix/upmns/vckm) via `check_and_remove(...,1.0)` and maps the 3rd-gen 2x2 sub-block to stopmix/sbotmix/staumix (L1484-1543).
- Maps trilinear `te/tu/td` → `ae/au/ad` dividing by the corresponding Yukawa (L1545-1573).
- Maps soft mass-squared `msl2/mse2/msq2/msu2/msd2` diagonals → `msoft 31..49` taking `sqrt(value)` (L1575-1614).
- Reconstructs `hmix 3` (vev) from EW inputs if missing (L1519-1527); applies the `hmix` scale to derived blocks.
Run as `__main__` it calls `convert_to_slha1(argv[1], argv[2])` (L1864).

## `convert_to_mg5card(path, outputpath=None, writting=True)` — L1625
Inverse. If `usqmix` present → already mg5/slha2, return card (write only if outputpath differs, L1632-1636). Otherwise strips the SLHA1-only `sminputs 2/4/6/7` and `modsel 1` (L1640-1647) and rebuilds the SLHA2 mixing/soft blocks. **Returns the ParamCard object** (unlike convert_to_slha1 which writes in place).
Called by `do_treatcards`/output only for a model literally named `mssm`/`mssm-*` → `Source/MODEL/MG5_param.dat` (see operative-source-chain.md). **DEAD for the shipped `MSSM_SLHA2`** (name ≠ `'mssm'`) — see mssm-slha2-name-gating.md; the shipped MSSM is native SLHA2 with no MG5_param.dat. This routine is still reachable on demand via the editor's `update to_slha2`.

## `convert_to_complex_mass_scheme()` — L712 (method on ParamCard)
A separate in-card conversion (not slha1↔slha2). Called by
`models/model_reader.py:97/100` inside `set_parameters_and_couplings` when CMS is on
(`complex_mass_scheme` arg, else the `aloha.complex_mass` global, L95-100). Two transforms:
- **Removes the `yukawa` block entirely** (L718-721) — "irrelevant for the CMS models". Last param
  removed also drops the block.
- **Forces the EW input scheme to (MZ, MW, aewm1)** (L723-764). Reads `sminputs 1` (aewm1),
  `sminputs 2` (GF), `mass 23` (MZ), `mass 24` (MW). Exactly one may be internal; supported internals
  are only `mass 24`, `sminputs 2`, or `sminputs 1` (else `InvalidParamCard`, L742-750). If `mass 24`
  (MW) is internal, computes it from the others — `Mw = sqrt(Mz^2/2 + sqrt(Mz^4/4 - (1/aewm1)·pi·Mz^2/(Gf·sqrt2)))`
  (L757-758; `sminputs 1` is 1/alpha, so the code uses `(1.0/aewm1)` — alpha = 1/aewm1) — then **removes
  `sminputs 2` and adds `mass 24`** (L763-764), i.e. swaps GF-in for MW-in.
  If all four are already present it returns unchanged (L738-740).
Caution: this mutates the in-memory card during model loading for CMS runs; the `yukawa` block silently
disappears and the EW scheme is rewritten. NLO/CMS-specific — does not fire for ordinary LO SM runs.

## Auto slha1→slha2 detection at inc-file time: `secure_slha2` — L614
Called first inside every `write_inc_file` (L643), keyed on which blocks `ident_card.dat` expects vs
the card has. `get_missing_block(identpath)` L595 returns `(missing, unknow)`: `missing` = blocks the
ident-card names but the card lacks; `unknow` = blocks the card has but the ident-card never names.
Two auto-conversion triggers (L619-623):
- `missing == {'fralpha'}` and `'alpha' in unknow` → renames block `alpha`→`fralpha` and key `()→(1,)`
  (L636-637), writes the card. (QED-alpha block-name mismatch — a non-MSSM case.) **Source-visible bug:**
  the trailing `self.write(param_card.input_path)` at L638 references `param_card`, which is only bound
  inside the *other* (`to_slha2`) branch at L629 — in the `fralpha`-only path `param_card` is referenced
  before assignment. Because `param_card` IS assigned elsewhere in the same function body (L629), Python
  treats it as a function-local, so this raises **`UnboundLocalError: cannot access local variable
  'param_card' where it is not associated with a value`** (probe-confirmed, Python 3.11+ message form),
  NOT a bare `NameError: name 'param_card' is not defined`. `UnboundLocalError` is a *subclass* of
  `NameError`, so `except NameError` catches it, but the grep-able message string differs — when
  diagnosing this path, grep for `UnboundLocalError ... param_card`, not the `NameError ... is not
  defined` text. The in-memory rename (L636-637) still happens before the failing write; whether this
  path is ever hit depends on a model whose ident-card names `fralpha` while the card has `alpha`
  (narrow).
- ALL of `te/msl2/dsqmix/tu/selmix/msu2/msq2/usqmix/td/mse2/msd2` missing AND ALL of
  `ae/ad/sbotmix/au/modsel/staumix/stopmix` unknown → `to_slha2`: logs "Convention for the param_card
  seems to be wrong. Trying to automatically convert ... (The converter is not fully general)" (L626),
  calls `convert_to_mg5card(param_card, writting=True)` with no outputpath, then `self.clear()` +
  `self.__init__(param_card)` to reload (L630-632).
Caution: `convert_to_mg5card(path, writting=True)` with no outputpath defaults `outputpath=path`
(L1629-1630), so the auto-conversion **overwrites the operative card on disk** at inc-file time — a
silent SLHA1→SLHA2 rewrite of `Cards/param_card.dat`, not just an in-memory transform. Fires only when
the *full* MSSM-block signature matches; a partial mismatch is left alone (and then fails later lookups).

## SECOND, EARLIER auto-conversion firing point: model-read time (`ModelReader.set_parameters_and_couplings`)
`secure_slha2` is NOT the only place the slha1→slha2 / alpha→fralpha auto-conversion fires. The SAME
family of conversion also runs at **model-load time**, much earlier in the pipeline, inside
`$MADGRAPH_INSTALL/models/model_reader.py:58` `set_parameters_and_couplings(param_card, ...)`. This is
the routine the `update dependent` editor path and `ParamCardWriter` call to evaluate dependent params
(model_reader L97/100 also calls `convert_to_complex_mass_scheme()` here for CMS — covered above).

Block-mismatch reconciliation (model_reader L103-160):
- `key` = card blocks minus `qnumbers `/`decay_table`/`info` (L102-104). If `set(key) != set(parameter_dict.keys())`
  (the model's required blocks) it builds `missing_set`/`unknow_set` and dispatches `apply_conversion` (L120-140):
  - `loop` in missing → appended to key, **non-fatal** (`fail=False`, L121-123) — model can supply the loop scale itself.
  - no missing block (only extra unknown) → warns `Unknow type of information in the card` and continues (`fail=False`, L125-127).
  - **MSSM model** + non-empty missing → `apply_conversion=['to_slha2']`, `overwrite=False` (L128-134) — in-memory convert only.
  - `missing == {'fralpha'}` and `alpha` unknown → `apply_conversion=['alpha']` (L135-136).
  - `need_slha2(missing,unknow)` (model_reader L289 — the IDENTICAL 11-missing-`te/msl2/dsqmix/tu/selmix/msu2/msq2/usqmix/td/mse2/msd2`
    + 7-unknown-`ae/ad/sbotmix/au/modsel/staumix/stopmix` signature `secure_slha2` uses) → `to_slha2`, `overwrite=True` (L137-139).
- `apply_conversion` execution (L141-162):
  - `to_slha2`: if `overwrite` → logs `logger.error('Convention for the param_card seems to be wrong. Trying to automatically convert ...')`
    **and `time.sleep(5)`** (L143-148, a deliberate 5-second pause so the user reads the warning), then
    `param_card = convert_to_mg5card(param_card.input_path, writting=overwrite)` (L150-151). `writting=True`
    (overwrite case) rewrites the card on disk; `writting=False` (MSSM case) is in-memory only. Then re-checks
    whether converted keys cover `parameter_dict` (L152-155).
  - `alpha`: `param_card.rename_blocks({'alpha':'fralpha'})` (L159) + `param_card['fralpha'].rename_keys({(): (1,)})`
    (L160) + **`param_card.write(param_card.input_path)` (L161)** — the **clean** alpha→fralpha rename.
    Note this path DOES write the card to disk (L161), same as `secure_slha2`'s fralpha branch tries to;
    the difference is WHY one crashes and the other does not. Here `param_card` is a properly-bound local
    `ParamCard` instance (assigned L87, possibly reassigned to the `convert_to_mg5card` return L150-151) and
    `.write()` is called ON it. In `secure_slha2` (L636-638) the equivalent line is `self.write(param_card.input_path)`
    where `param_card` is a function-local assigned ONLY inside the *other* (`to_slha2`) branch (L629) → in the
    `alpha`-only path `param_card` is unbound → `UnboundLocalError`. So the crux is the bound-vs-unbound
    `param_card` reference, not the use of `rename_blocks`/`rename_keys` (both paths use those). This path does NOT crash.
Caution: so the alpha→fralpha conversion has TWO code paths with different failure behaviour — the
model-read path (clean, model_reader L157-160) and the inc-file path (`secure_slha2` L636-638, buggy
UnboundLocalError). Which one fires depends on whether the block mismatch is caught at model load
(set_parameters_and_couplings, e.g. via `update dependent` / ParamCardWriter) or only at inc-file write
(`write_inc_file`→`secure_slha2`). When diagnosing a fralpha conversion crash, check which stage hit it.

## Output-time MSSM→SLHA1 (`create_param_card_static`)
The fresh-card writer at `output` time is wrapped by `create_param_card_static`
(`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:9811`, called by `create_param_card` L9840). For a model
named `mssm`/`mssm-*` (L9831-9833 `model_name = model.get('name')`) it converts the just-written card to
SLHA1 (L9830-9838): `make_valid_param_card(output_path, rule_card_path)` (if a rule card exists; validation
half — param-card-validation-rule-engine.md) then `convert_to_slha1(output_path)`. **CRITICAL (v3.7.1):
this fires only for a model literally named `mssm`/`mssm-*`. The shipped `MSSM_SLHA2` (name `MSSM_SLHA2`
≠ `'mssm'`) is NOT converted — its on-disk card stays native SLHA2 and no MG5_param.dat is made
(probe-confirmed, mssm-slha2-name-gating.md).** The SLHA1-on-disk → SLHA2-for-ME round-trip described here
is the LEGACY `mssm` story, dead in a stock install.
(More on the writer + restrict-card-copy short-circuit + the rule-card emission step: fresh-card-writers.md.)

## Cautions
- `convert_to_slha1` overwrites `path` in place if `outputpath` not given (L1452-1453) — destructive default.
- The slha1↔slha2 conversions are MSSM-specific (keyed on `usqmix` and hardcoded block names); they are NOT general SLHA machinery and silently no-op on non-MSSM cards. (The slha1↔slha2 collapse of CKM/mixing blocks is done by these routines DIRECTLY — NOT by a `param_card_rule.dat` constraint rule, which is vestigial; param-card-validation-rule-engine.md.)
- For non-MSSM cards (no `usqmix`), `secure_slha2`/`convert_to_*` no-op — e.g. SMEFT DIM6* blocks are untouched (smeft-wilson-coefficient-blocks.md).
