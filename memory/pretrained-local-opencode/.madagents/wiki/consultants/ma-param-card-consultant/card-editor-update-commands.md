---
description: The AskforEditCard "update" command family (dependent/missing/to_slha1/to_slha2/to_full) — user-facing + auto-triggered entry points mutating the operative param_card.dat before a run; auto-update dependent fires on the INTERACTIVE path only (launch -f skips it, probe-confirmed); dependent/internal params are recomputed Fortran-side and never read from the card. Includes the "Failed to update dependent parameter" warning's four firing sites and the confirmation that MadSpin reads the operative param_card (banner slha / mymod.initialise) so a stale internal line propagates.
---

# Card-editor `update` commands — operative-card mutations before the run

The card-edit prompt (`AskforEditCard` in `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py`)
exposes an `update` command that rewrites the operative `Cards/param_card.dat` **on disk** before
integration. These are the user-facing / auto-triggered front-ends to the `check_param_card.py`
library routines documented in operative-source-chain.md, slha1-slha2-conversion.md,
param-card-validation-rule-engine.md, and
override-stages-card-to-fortran.md. They mutate the card the user sees, **earlier** than the four
`write_inc_file`-time override stages — so a value can change at the editor stage AND again at inc-file time.

## `do_update(line)` — L6833. Subcommands (docstring L6834-6839)
`dependent | missing | to_slha1 | to_slha2 | to_full [run_card] | <hidden run_card block>`.
Valid list also at L5611: `['dependent','missing','to_slha1','to_slha2','to_full']`.

### `update dependent` — L6848-6869
Recomputes model-derived (non-free) masses/widths and re-applies restriction rules, then writes the card.
- **Auto-width first** (L6861-6862): if any `decay <pid> auto` is present, runs `do_compute_widths('')`
  and reloads the card before updating (madwidth owns the computation).
- **Scan short-circuit** (L6855-6864): if a `scan` line is present (`^(decay)?[\s\d]*scan`), the whole
  update is **skipped** (`return`) — dependent params are NOT resolved at edit time for scan cards.
- Then calls the static worker `AskforEditCard.update_dependent(...)` (L6934) which:
  1. **alpha_s ↔ PDF sync** (L6961-7019): if beams are on (`lpp1/lpp2 != 0`), overwrites `sminputs 3`
     (aS) with the value from the chosen PDF — `pdf.alphasQ(91.1876)` for LHAPDF (L7010), or a hardcoded
     table for the built-in `cteq6*`/`nn23*`/`ct14q*` sets (L6964-6974). This silently changes a
     hand-set aS to match the PDF.
  2. loads the model under a `timer`-second alarm; on timeout/exception logs a warning and **bypasses**
     the update (L7029-7038) — leaves dependent params stale, flagged as trouble for MadSpin/shower.
  3. `param_card.update_dependent(model, restrict_card, log_level)` (check_param_card.py L463) — the
     library routine (see below).
  4. `param_card.write(path)` if modified (L7051-7052) — overwrites the operative card.

### `ParamCard.update_dependent(model, restrict_rule, loglevel)` — check_param_card.py L463
- First applies all restriction rules via `restrict_rule.check_param_card(modify=True)` (L477-478) —
  same engine as param-card-validation-rule-engine.md.
- Builds a `ModelReader`, `set_parameters_and_couplings(self)` (L484-486).
- For each particle (skipping goldstone/ghost), if its mass/width is a derived `ModelVariable` (not a
  `ParamCardVariable`), recomputes it from the model and **overwrites the card value** when it differs
  (mass L508-516, width L538-539). Logs `For consistency, the mass/width of particle N (name) is
  changed to V.` A complex result with imag > 1e-5·real **raises** (mass L504-505, width L528-529);
  else takes `.real` (mass) / `abs` (width). A missing mass/width param is appended with a sentinel
  `-999.999` placeholder then overwritten (L499-501, L523-525).
- Returns whether the card was modified.

### The "Failed to update dependent parameter" warning — four distinct firing sites
The warning the seed-doc names fires from the `update dependent` path when MG cannot recompute the
dependent (internal) params, leaving them stale. Exact strings + conditions (all in
common_run_interface.py):
1. **L6850** — `do_update('dependent')` when `not self.mother_interface` (card editor has no parent MG
   interface to build the model). Text: `Failed to update dependent parameter. This might create
   trouble for external program (like MadSpin/shower/...)`. It does NOT return — it proceeds and calls
   `update_dependent(None,...)`, which then trips site 3 as well.
2. **L7030** (`update_dependent`, TimeOutError from the `signal.alarm(timer)`) — model exceeded the
   timer (default 20 s, set at L6805): `The model takes too long to load so we bypass the updating of
   dependent parameter.\nThis might create trouble for external program (like MadSpin/shower/...)\nThe
   update can be forced without timer by typing 'update dependent' at the time of the card edition`.
   This is the source of the seed-doc's remedy "respond `update dependent` when prompted" — the message
   literally instructs it.
3. **L7036** (generic `Exception` during `mecmd.get_model()`): same text as site 1.
4. **L7049** (`get_model()` returned falsy): `missing MG5aMC code. Fail to update dependent parameter.
   This might create trouble for program like MadSpin/shower/...`.
   In every case `modify=False` → the card is NOT rewritten (L7051 guarded on `modify`), so the stale
   internal lines survive into the operative card and thence the LHE banner / MadSpin / shower.

### MadSpin reads the operative param_card — so a stale internal line propagates (operative-source point)
Confirmed MadSpin consumes the written `Cards/param_card.dat` (NOT a fresh MG-recomputed set):
- `MadSpin/interface_madspin.py:371-372` — `self.banner.charge_card('slha')` then
  `check_param_card.ParamCard(card)`; L376 `self.banner.param_card.create_diff(param_card)` — the
  banner's `slha` block IS the operative param_card MG wrote at run time.
- `interface_madspin.py:1795/1797` — `mymod.initialise(pjoin(self.path_me, 'Cards','param_card.dat'))`
  loads the model from the operative card for the decay-ME.
- `MadSpin/decay.py:1625` — `self.banner['slha'] = open(pjoin(self.path_me,'param_card.dat')).read()`;
  decay.py:1691 `check_param_card.ParamCard(param_card)`.
So the seed-doc's core claim holds: MadSpin reads the param_card MG wrote, and if `update dependent`
failed/was skipped, a stale internal parameter line is what MadSpin sees. (Whether MadSpin then
RECOMPUTES internals from the externals via its own ModelReader vs trusts the literal line is
madspin-interface's slice — the warning targets MadSpin precisely because that consistency is not
guaranteed for every consumer, including the LHE banner text and Pythia8.)

### `update missing` — `update_missing()` L7060
Adds every block/param present in the **default** card (`self.param_card_default`) but absent from the
operative card, at its default value, then rewrites + reloads (L7142-7145). This is the **user-facing
default-fill** — distinct from `write_inc_file`'s silent per-param fill (override-stages stage 3):
here the missing lines are physically written into `Cards/param_card.dat`. `qnumbers`/`decay` blocks are
handled specially (L7100-7104, L7138-7140). Reports `Adding N parameter(s) to block X` / `No missing
parameter detected.`

### `update to_slha1` / `to_slha2` — L6876-6889
Thin wrappers: `convert_to_slha1(path)` / `convert_to_mg5card(path)` in place (slha1-slha2-conversion.md),
then reload. Marked "(beta)" in the docstring; failures are caught and warned, not fatal.

### `update to_full [run_card]` — `update_to_full()` L6902
Run-card only (rewrites run_card with `write_hidden=True`); not a param-card op. Listed for completeness.

## Auto-trigger: `update dependent` fires on its own — but ONLY on the interactive edit path
- **End of card editing** (`postcmd`, L6793; guard L6801-6804): when the edit question ends and
  `self.param_consistency` is True and `update_dependent_done` is False, MG runs
  `do_update('dependent', timer=20)` automatically (L6804). A user who interactively edits cards and presses
  enter to finish gets dependent params recomputed + aS-PDF-synced + the card rewritten — without
  ever typing `update`.
- **Force/`-f` path does NOT auto-update the operative card.** `launch -f` / `generate_events -f`
  routes through `ask_edit_cards(..., mode='auto')` (madevent_interface dispatch L6804 vs interactive
  L6806) and the interactive edit question is bypassed, so `postcmd`'s auto-`do_update('dependent')`
  does not rewrite `Cards/param_card.dat`. **Probe-confirmed (this install, v3.7.1):** in three
  separate `./bin/madevent launch -f` runs on a generated SM `p p > t t~` card with the dependent
  `mass 24` (MW) hand-set to a wrong 70.0, the operative card's `mass 24` stayed 70.0 after the run
  reached `survey` — no "For consistency ... is changed to" message, no "edit a card" question. The
  run is still physically correct because **MW is an `internal`/dependent param and is recomputed
  Fortran-side; it is never read from the card** (see below).
- **On reading a file answer** (`check_answer_consistency`, L7150-7154): same auto-call — also on the
  interactive/file-answer path, not the bare `-f` path.
- `param_consistency` can be turned off via the `param_consistency` option (L5045-5062) — then the
  auto-update is suppressed even interactively.

## Dependent params never reach Fortran via the card — so a stale dependent value is inert
Probe-confirmed (this install): `write_inc_file` walks **only** `Cards/ident_card.dat`, which lists
**only external params**. For SM `p p > t t~`, `ident_card.dat` has `mass 23/6/5/25/15` and
`decay 23/24/6/25` but **no `mass 24`** — MW is `nature='internal'` (parameters.py L295,
`value='cmath.sqrt(MZ**2/2.+...)'`). So `mdl_mw` never appears in `param_card.inc`; the resulting
inc holds only AEWM1/MDL_GF/AS/Yukawas/MDL_MZ/MDL_MT/MDL_MB/MDL_MH/MDL_MTA + external widths, and the
Fortran recomputes MW. **Consequence:** editing a dependent (internal) value in the operative card is
a no-op at the matrix-element level whether or not `update dependent` "fixes" it. The aS-PDF sync and
the dependent recompute matter for the *card file* (read by downstream Pythia/MadSpin and the LHE
banner), not for the MG5 matrix element of an external-vs-internal-split model. Width WW (`decay 24`)
IS external, so a hand-set W width DOES reach Fortran — internal/external is per-parameter.

## `restricted_value` warning on `set` — L6163-6169
`restricted_value` is populated by `default_param.analyze_param_card()` (L5175; the method lives in
check_param_card.py — data-model-classes.md). When a user `set`s a param that is in `restricted_value`,
the editor warns `Note that this parameter seems to be ignore by MG. MG will use instead the
expression: <expr>` (L6165-6167) and `set <block> all` **skips** restricted params (L6153-6155). This is
the user-facing surface of the restriction-pruned-param mechanism.

## Cautions
- `update dependent` is auto-triggered at edit end (L6804) **on the interactive path only** — a
  hand-set dependent mass/width or aS is silently corrected to the model/PDF value before the run,
  even with no explicit `update`. Symptom "I set the W mass / aS and it changed": this stage, not an
  inc-file override. **But `launch -f` skips this** (probe-confirmed above): the operative card keeps
  the stale value. The run is still correct for *internal* params (recomputed Fortran-side, not read
  from the card) but a stale value then leaks into the LHE banner / downstream Pythia/MadSpin, which
  DO read the card. So "my edited dependent value persisted in the card after a `-f` run" is expected,
  not a bug.
- The aS-PDF sync (L7007-7019) only fires when beams are on; it overwrites `sminputs 3` from the PDF.
- Scan cards **skip** `update dependent` entirely (L6856-6860) — dependent params are resolved per scan
  point downstream, not at edit time.
- Model-load timeout (default 20 s, L6805) silently bypasses the update (L7029-7032) — dependent params
  may stay stale; only a warning is logged. A runtime-timing claim — probe-candidate, not cached as fact.
