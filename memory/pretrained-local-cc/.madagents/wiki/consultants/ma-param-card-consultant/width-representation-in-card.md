---
description: How a total width (numeric float vs the 'auto' string) and its partial-width BR sub-lines are represented in the ParamCard/Block/Parameter data model and round-trip through read/__str__; the get_value('width')→decay alias. A numeric width is a PLAIN stored float — NO width-vs-mass consistency check at card-read/launch (default sm Higgs DECAY 25 stays stale after a MASS 25 edit; WH is free external, so update_dependent's ModelVariable-only reconciliation never fires).
---

# Width representation in the card (data model + round-trip)

The DECAY-block representation in `$MADGRAPH_INSTALL/models/check_param_card.py`. This is the
*representation/round-trip* layer; detection of `Auto`/`scan` lines is scan-and-auto-detection.md, the
read-dispatch entry-types are read-write-entry-types.md, and the COMPUTATION of an Auto width is
madwidth's slice — this page covers only how the value SITS in the card object and re-serializes.

## The decay block is named `decay` internally, holds one `Parameter` per pid
`ParamCard.read` (L362-372) finds-or-creates a single `Block('decay')` and appends one `Parameter`
per `decay <pid> <width>` line; the Parameter's `lhacode` is `(pid,)` (a 1-tuple) and `value` is the
width. There is NO `width` block — the block key is the string `'decay'` everywhere.

## `Parameter.value` is a float for a numeric width, the STRING `'auto'` for Auto — the type IS the flag
`Parameter.load_str` (L62-98): splits the line, tries `self.value = float(self.value)` (L91); on
`ValueError` it **keeps the value as a string** (the `auto` / `auto@nlo` case survives as a str because
read lowercases first, L355). So the in-memory discriminator between a resolved width and an unresolved
Auto width is purely `isinstance(value, str)` — there is no separate boolean.

## `Parameter.__str__` re-serializes the str value VERBATIM — there is no `Auto`-token normalization (probe-confirmed)
`__str__` (L122-160) begins by **re-coercing** `format` from `self.format`: a local `format = self.format`
(L126); if `self.format == 'float'` it tries `value = float(self.value)` and on exception sets the LOCAL
`format = 'str'` (L127-131). For a str-valued decay param (`value='auto'` or `'auto@nlo'`) this coercion
ALWAYS makes `format == 'str'`, so the `if format == 'float':` block at L137-146 is **never entered** for
an Auto width. The `format == 'str'` branch fires instead (L148-150):
`if self.lhablock == 'decay': return 'DECAY %s %s # %s' % (lhacode, self.value, comment)` — it emits
**`self.value` VERBATIM**. So:
- numeric width (float value) → `DECAY %s %.<prec>e # <comment>` (L138-139, default 6-digit) — reached via
  the `format=='float'` branch because `float(self.value)` succeeds.
- Auto width (str value `'auto'`) → `DECAY <pid> auto # <comment>` (L148-149) — the **lowercase token
  `auto`**, NOT a hardcoded capital `Auto`. The literal `DECAY %s Auto` line at L140 belongs to the
  `format=='float'` decay branch's `elif self.lhablock == 'decay':` — that line is **unreachable for a
  str-valued param** (the L127-131 coercion already flipped `format` to `'str'`), so it does not fire in
  practice; it would only matter for a hypothetical `format=='float'` decay param whose value is somehow
  a str without going through the coercion.

**Probe-confirmed (this install, v3.7.1):** a full `ParamCard(text)` read + `.write()` round-trip of
```
DECAY 6 auto@NLO
DECAY 23 auto
DECAY 24 2.0e+00
```
yields `DECAY 6 auto@nlo`, `DECAY 23 auto`, `DECAY 24 2.000000e+00`. The `@NLO` suffix is **PRESERVED**
(only lowercased — because `read` lowercases the whole line at L355, not because of `__str__`), and the
token is the lowercase `auto`, not `Auto`. (`python3 -c` driver against the live `check_param_card`.)

Caution: round-tripping an Auto card through `ParamCard.read` + `.write` re-emits the width value
verbatim — `auto`→`auto`, `auto@NLO`→`auto@nlo`. The `@NLO` is NOT lost and the token is NOT capitalized.
Code that greps a round-tripped card for `auto` (case-insensitive) finds it; the `@nlo` suffix survives
on the line too (the read-path regex at scan-and-auto-detection.md L11 also captures `@NLO` separately for
the compute-widths `--nlo` decision, but that is a parallel path, not the only place the suffix lives).

## Partial-width BR sub-lines: `Block.decay_table[pid]`, format `'decay_table'`
SLHA partial-width rows under a DECAY (the `# BR NDA ID1 ID2` table) are NOT stored on the decay
Parameter — they live in a SEPARATE sub-block. Read path (L383-395): when a non-`decay`-leading line
follows a decay line, a fresh `Block('decay_table_<pid>')` is created keyed on the last-seen decay pid
and stashed at `self['decay'].decay_table[pid]` (L386-387). Each row loads via `Parameter.load_decay`
(L100-120):
- `value = float(data[0])` = the branching ratio (L119).
- `lhacode = (N, sorted_daughter_pids...)` where N = daughter count (L115-117) — note the FIRST tuple
  element is the multiplicity, not a pid.
- `format = 'decay_table'` (L120).
A malformed BR row raises `InvalidParamCard` on append and is **swallowed** (L393-395) — same
lossy tolerance as the generic read.

## `Block.__str__` re-emits each BR table immediately after its DECAY line (L295-302)
For the `decay` block specifically (L295-302): iterate the decay Parameters, emit `str(param)` (the
DECAY line), then if `pid in self.decay_table` emit `str(self.decay_table[pid])` right after — so the
BR table follows its parent DECAY line in the written card. A `decay_table_*` sub-block emitted on its
own suppresses the block header (L303-304: `text = ''`). The BR-row `__str__` (L152-153) is
`'      %e %s # %s' % (value, ' '.join(lhacode), comment)` — i.e. `<BR>  <N> <daughters>`.

## `get_value('width', pid)` is an alias to `get_value('decay', pid)` — L584-593
`get_value(blockname, lhecode, default=None)` (L584): on a `KeyError` for `blockname=='width'` it retries
with `blockname='decay'` (L588-590). So width-querying callers may ask for either `'width'` or `'decay'`;
the stored block is always `'decay'`. (This is the accessor the scan per-point Auto-width capture uses to
record `width#<pid>` into the summary — scan-and-auto-detection.md L36-37.)

## A numeric width is a PLAIN stored float, NOT reconciled against the mass at card-read or launch
The default `sm` ships a `MASS 25` (the Higgs mass) and a `DECAY 25` (its total width) as
**independent stored externals** — coordinates: `restrict_default.dat` MASS L24 + DECAY L33; both
`MH` and `WH` are `nature='external'` in `models/sm/parameters.py` (MH decl ~L157-163 lhacode `[25]`;
WH decl ~L213-219 lhacode `[25]`). Read `MASS 25` / `DECAY 25` in the generated card for the current
defaults — they are drift-prone, not cached here. When a user edits `MASS 25` to,
say, `400` for a heavy-Higgs study, the `DECAY 25` line is left **untouched** — the read path loads
each as a plain float (`load_str` L91 `float(self.value)`, no cross-param logic) and the card I/O
layer performs **no width-vs-mass consistency check and emits no warning** at card-read or at launch.
The card becomes internally inconsistent (the light-Higgs width attached to a heavy mass) and the stale
width is used verbatim. (The validators `make_valid_param_card`/`check_valid_param_card`
L1817/L1836 and `check_param_card` L1308 do NOT cross-check mass against width — they apply the
restriction/`ParamCardRule` template, not a physics consistency rule.)

**The ONE place a width is reconciled — and why it does NOT fire for the sm Higgs.**
`update_dependent` (L463-539) is the interactive-edit-path consistency pass
(card-editor-update-commands.md). It rewrites a width "For consistency" (L534/L536 log) **only when**
`isinstance(width, base_objects.ModelVariable)` (L519) — i.e. the width is **model-DERIVED**.
For the sm Higgs, `WH` is a free `ParamCardVariable` (external), NOT a `ModelVariable`, so the
L519 guard is **False** and the branch never runs: editing `MASS 25` never triggers a width
rewrite for the Higgs, even on the interactive `update dependent` path. (Masses get the symmetric
treatment at L495 with the stricter `ModelVariable and not ParamCardVariable` guard.) So:
- **External/free width (sm `WH`/`WZ`/`WW`, all top-level `DECAY` externals): never reconciled.**
  Stale-after-mass-edit, used verbatim. This is the common case.
- **Model-DERIVED width (a `ModelVariable` width in some BSM model): rewritten by
  `update_dependent` on the interactive edit path** (and recomputed Fortran-side regardless).
Do NOT overclaim "MG never reconciles a width" — it does, but only for derived widths and only on
the edit-time tier (launch -f / scan skip even that; card-rewrite-tiers-edit-vs-inc.md). The
mass-edit-makes-the-width-stale surprise is specifically about a FREE external width.

The fix for a stale width after a mass edit is a deliberate **width regeneration** — `set WH Auto`
/ `compute_widths` (madwidth's slice), which recomputes from the new mass and writes the resolved
numeric back via the string-based `update_width_in_param_card` (read-write-entry-types.md). Auto
representation in the card itself: the value is the str `'auto'`/`'auto@nlo'` (the type IS the flag,
section above), re-emitted verbatim on round-trip.

## Where this sits in the lifecycle (pointers, not restated)
- An Auto width is detected + dispatched to compute_widths at read time (scan-and-auto-detection.md);
  the resolved numeric value is written BACK into the operative card by the string-based
  `update_width_in_param_card` / `compute_widths --output` path, NOT by `Parameter.__str__`
  (read-write-entry-types.md L37-43). After resolution the card holds a numeric `DECAY %.6e` line.
- A width is EXTERNAL (every `decay <pid>` gets an ident_card line for in-process pids) so a hand-set
  numeric width DOES reach Fortran via param_card.inc — UNLIKE an internal/dependent mass
  (card-editor-update-commands.md: "Width WW (decay 24) IS external"). But a width that is itself
  model-DERIVED gets recomputed/overwritten by `update_dependent` at edit time on the interactive path
  (check_param_card.py L528-539; card-editor-update-commands.md) — same str-vs-float value, governed by
  whether the particle's width is a ParamCardVariable (free) or a ModelVariable (derived).

## Cautions
- The width "block" is keyed `'decay'`, never `'width'`; only `get_value` accepts the `'width'` alias.
  Code doing `card['width']` raises `KeyError`.
- A str width value is re-emitted VERBATIM by `__str__` (lowercased on read, not on write): `auto`→`auto`,
  `auto@NLO`→`auto@nlo`. There is NO `Auto`-token normalization and the `@NLO` IS preserved (probe-confirmed).
  The hardcoded capital-`Auto` line at check_param_card.py L140 is unreachable for a str-valued param (the
  `__str__` L127-131 format-coercion flips `format` to `'str'` first, so the `format=='str'` verbatim branch
  L148-149 fires). Grep a round-tripped card case-insensitively for `auto` and the suffix is on the line.
- BR sub-lines live in `decay_table[pid]`, not on the decay Parameter; a `copy_param`/`remove_param` on
  the decay block does not carry the BR table (it is a side dict on the Block, L173).
- The decay Parameter's `lhacode` is a 1-tuple `(pid,)`; a BR row's `lhacode` is `(N, *daughters)` with
  N=count first — different tuple shapes in the same block family.
