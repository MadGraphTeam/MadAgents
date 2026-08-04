---
description: Param-card validation & the ParamCardRule restriction-rule engine in check_param_card.py — make_valid_param_card, check_valid_param_card, ParamCardRule (zero/one/identical/opposite ENFORCED; <rule>/<constraint> functional category loaded but vestigial & non-round-trip), and analyze_param_card comment-name extraction (the restricted_value surface). Validation applies the restriction template only — NOT a physics consistency rule (no mass-vs-width / mixing check). Conversion machinery is in slha1-slha2-conversion.md.
---

# Param-card validation & the restriction-rule engine (`$MADGRAPH_INSTALL/models/check_param_card.py`)

This page is the **validation/rule-engine** half of the param-card I/O machinery. The
**slha1<->slha2 conversion** half is slha1-slha2-conversion.md. Key boundary: these validators apply
the restriction `ParamCardRule` template only; they do **NO physics consistency check** (no mass-vs-width
reconciliation — width-representation-in-card.md; no EXTPAR-vs-NMIX — mssm-slha2-mixing-matrix-stale.md).

## `analyze_param_card` — L415: comment-format parameter-name extraction
Returns `(pname2block, restricted_value)` by parsing each param's **comment text** (not the value).
Format dispatch (L426-452):
- comment starts `set of param :` → merged param; var names via `re.findall(r'[^-]1\*(\w*)\b')` (L432).
- comment is a single token → that token IS the var name (L434-435).
- `name : expr` (≥3 tokens, 2nd token `:`) → NO var name; the `(bname, lha_id)` is put in
  `restricted_value` with the expression string (L439-441). **This is the surface that drives the
  editor's "this parameter seems to be ignored by MG, will use expression ..." warning** (card-editor
  page) — a pruned/restricted param's comment carries its replacement expression here.
- `name [X]eV^...` unit-format 2-token → var name (L442-444); `name (...)` → first token is var name (L445-446).
- else: unrecognized, skipped (debug-logged unless qnumbers). Docstring (L419-421) warns this is reliable
  on `*_default.dat` but "typically dangerous on the user-defined card" — hand edits break the format.

The `restricted_value` dict is consumed by `AskforEditCard` (populated at common_run_interface L5175) to
warn on `set` of a pruned/derived param and to skip it in `set <block> all` (card-editor-update-commands.md);
and `do_help` (data-model-classes.md L840) warns "will not be consider by MG5_aMC" off the same dict.

## `make_valid_param_card(path, restrictpath, outputpath=None)` — L1817
- Loads `ParamCardRule(restrictpath)`; first runs `check_param_card(modify=False)` (L1826).
- If it raises `InvalidParamCard`, re-runs with `modify=True, write_missing=True` and writes the corrected card (L1828-1830). Else copies unchanged.

## `check_valid_param_card(path, restrictpath=None)` — L1836
If `restrictpath` is None, searches `../../Source/MODEL/param_card_rule.dat` then `../Source/MODEL/param_card_rule.dat`; if neither exists, returns True (no rules → always valid, L1843-1848). Then `check_param_card(modify=False)` — raises on violation. (This is the validator `do_treatcards`'s ELSE branch calls for non-MSSM models — operative-source-chain.md.)

## `ParamCardRule` — L1121, the restriction-rule engine
Five rule categories loaded from XML `param_card_rule.dat` (`load_rule` L1207): `<zero>`, `<one>`, `<identical>` (a==b), `<opposite>` (a==-b), `<rule>` (functional/constraint). The first four encode model-restriction constraints (e.g. zero-couplings from restriction, mass/coupling degeneracies) and ARE enforced by `check_param_card`; the fifth (`<rule>`/`<constraint>`) is loaded but **not enforced and not round-trip-safe** — see the vestigial-category note below.

`write_file(output=None)` L1166 serializes the rules back to the `param_card_rule.dat` format —
envelope `<file>...comment-banner...` then `<zero>...</zero><one>...</one><identical>...</identical>
<opposite>...</opposite><constraint>...</constraint></file>`. Each line: `<block> <id...> # <comment>`
for zero/one; `<block> <id...> : <id2...> # <comment>` for identical/opposite; and
`<block> <id...> : <rule> # <comment>` for constraint (L1173-1199). Symmetric to `load_rule` (L1207).
Returns the text and optionally writes to a path/handle.

`check_param_card(card, modify, write_missing, log)` L1308:
- zero (L1319): non-zero param → raise if `modify=False`, else set to 0 + comment "fixed by the model".
- one (L1350): same, target 1.
- identical (L1382): force id1 = value(id2); **missing whole block → warns "Param card is not complete: Block %s is simply missing" and continues** (L1383-1388).
- opposite (L1417): force id1 = -value(id2).
- `write_missing=True` adds missing params with the rule-implied value instead of failing.
- **The `rule`/constraint (functional) category is NOT enforced** — `check_param_card` has no `self.rule`
  loop (the body L1318-1446 iterates only zero/one/identical/opposite). So a functional constraint listed
  in `param_card_rule.dat` is loaded and round-tripped but never *checked*; it cannot raise `InvalidParamCard`
  or rewrite a value. Treat the constraint category as effectively vestigial in v3.7.1 validation.
Returns `(card, is_modified)`.

### The `<rule>`/`<constraint>` category is vestigial + has live bugs (source-certain)
The "functional constraint" rule category (the one a model would use for e.g. CKM unitarity) is loaded
and serialized but plays no part in validation, and the load/write paths are inconsistent:
- **Load reads `<rule>`** — `load_rule` L1273 does `tree.find('rule')`. **Write emits `<constraint>`** —
  `write_file` L1195 wraps the same data in `<constraint>...</constraint>`. So a `param_card_rule.dat`
  produced by `write_file` does NOT round-trip back through `load_rule`: re-loading it finds no `<rule>`
  element and silently drops every constraint. (zero/one/identical/opposite use matching tags and DO
  round-trip.)
- **`write_file` would crash on a non-empty rule list.** `add_rule` L1162-1164 appends a **3-tuple**
  `(lhablock, lhacode, rule)` (no comment). But `write_file` L1196 unpacks **4** —
  `for name, id, rule, comment in self.rule` — which raises `ValueError: not enough values to unpack`
  the moment `self.rule` is non-empty. So the constraint serialization path is unexercised / latently broken.
- No `param_card_rule.dat` ships pre-built under `models/` (it is generated into `Source/MODEL/` at
  `output` time by `create_param_card_static` — fresh-card-writers.md; the ONLY on-disk-rule-card source),
  so whether any shipped restriction ever populates the constraint category could not be settled statically.
  Given the load/write/enforce gaps, assume restrictions rely only on the
  zero/one/identical/opposite categories. (The slha1↔slha2 collapse of CKM/mixing blocks is done by
  `convert_to_slha1`/`convert_to_mg5card` directly — NOT by a constraint rule. slha1-slha2-conversion.md.)

## How validation relates to the override chain
The zero/one/identical/opposite rules are the **value-OVERWRITING** override mechanism (override-stages
stage 2): a hand-set value violating a `<zero>`/`<one>`/`<identical>`/`<opposite>` rule is **rewritten** on
load with `modify=True` ("fixed by the model" appended to comment), and the param's card line is KEPT and
still read. This is structurally DIFFERENT from restriction *pruning*, which REMOVES the line entirely
(restriction-pruned-external-is-dropped.md): rule-constrained → line present, value reverts on load; pruned
→ line absent, lhacode gap, hand-add inert. Symptom test in that page's diagnostic.

## Cautions
- `check_param_card` with `modify=True` silently rewrites user values to satisfy restriction rules
  ("fixed by the model" appended to comment) — a hand-set value violating a restriction is overridden,
  not honored.
- The validators apply ONLY the restriction `ParamCardRule` template — there is **no physics consistency
  check**: no mass↔width reconciliation (a 125-GeV width on a 400-GeV mass passes silently —
  width-representation-in-card.md), no EXTPAR↔NMIX check (a stale mixing matrix passes silently —
  mssm-slha2-mixing-matrix-stale.md), no BR≤1 check.
- `analyze_param_card` is reliable on `*_default.dat` but explicitly "dangerous on the user-defined card"
  (docstring L419-421) — hand edits break the comment format that drives the var-name / restricted_value
  extraction.
