---
description: ParamCard/Block/Parameter data classes in models/check_param_card.py — structure, read/write, lhacode keying, mp_prefix.
---

# Param-card data model (`$MADGRAPH_INSTALL/models/check_param_card.py`)

File is 1866 lines (v3.7.1). Three core classes plus a dict subclass.

## `Parameter(object)` — L34
- Attrs set in `__init__` (L38): `lhablock`, `lhacode` (tuple of ints), `value`, `comment`, `format` (default `'float'`, L41).
- `load_str(text)` L62: splits on `#` for comment; `data.split()`; lhacode = tuple of leading ints, value = last token. `scan...` tokens are rejoined into one value token (L72-74). Value coerced to `float` if possible, else `format='str'` (L90-93). Special-case: block `modsel` → `format='int'`, value `int()` (L96-98).
- `load_decay(text)` L100: for decay-table sub-lines. Strips `]]>` (XML banner tail, L108). lhacode = `(n_daughters, *sorted_pids)` (L115-117); value = BR float; `format='decay_table'`.
- `__str__(precision='')` L122: SLHA serialization. `decay` block → `DECAY <pid> <width>` or `DECAY <pid> Auto` if value is str (L138-141). `qnumbers` block → integer format (L142). Default precision 6 (L133-134).

## `Block(list)` — L163
- `__init__(name)` L166: lowercases name; `scale=None` (Q-scale), `comment`, `decay_table={}` (pid→sub-Block), `param_dict={}` (lhacode-tuple → Parameter).
- `get(lhacode, default=None)` L177: lazily builds `param_dict`; int lhacode wrapped to 1-tuple; KeyError if missing and no default.
- `append(obj)` L228: asserts Parameter; **raises `InvalidParamCard` if same lhacode already present with a different value** (L240-243); silently ignores exact duplicate. Re-inits param_dict if missing (pickle path).
- `__eq__(other, prec=1e-4)` L212: relative tolerance comparison of all params (`abs(diff) > prec*abs(value)`).
- `load_str(text)` L260: parses `BLOCK <name> [Q= <scale>]` header — accepts both `Q=1.0` glued (L272) and `Q= 1.0` split (L277). `qnumbers <pid>` appends pid to name (L275-276).
- `__str__` L288: block header `BLOCK <NAME> [Q= <scale>]`; decay block iterates params + appends decay_table sub-blocks (L295-302); `decay_table*` blocks emit no header (L303-304).

## `ParamCard(dict)` — L315
- `mp_prefix = 'MP__'` L317 — multi-precision parameter name prefix (used in `write_inc_file`, see operative-source-chain.md).
- Keys are block names, **lowercased** via `__setitem__`/`__getitem__` (L408-413).
- `__init__(input_path)` L325: accepts a path, a `\n`-containing string (parsed via StringIO), or another ParamCard (round-trips through `write()`). `self.order` = list of Blocks in append order; `self.not_parsed_entry` = list.
- `append(obj)` L766: stores block by name; appends to `self.order` unless name starts with `decay_table`.
- `order_block()` L779: returns `self.order` unchanged (insertion order); `write()` uses it.
- Helpers: `has_block` L776, `has_param` L805, `get_value` L584 (falls back `width`→`decay` block, L588-590), `add_param` L828, `copy_param` L815, `mod_param` L866 (move/rename param, not duplicate; removes empty source block), `check_and_remove` L908 (assert value then remove; used by slha1 conversion), `remove_param`/`remove_block` L792-803.
- `do_help(block, lhacode, default)` L840: prints current vs default value; warns "will not be consider by MG5_aMC" if param is in `restricted_value` (analyze_param_card).

## `ParamCardMP(ParamCard)` — L920
Multi-precision variant; overrides `write_inc_file` (L923) to force `need_mp=True`.

## Caution
- Block/param keys are lowercased on read; case-insensitive lookups are safe, but never assume the on-disk casing survives a round-trip — `__str__` re-uppercases block names (L292/L307: `BLOCK <NAME>.upper()`). NOTE the FRESH-card writer does the OPPOSITE — `write_param_card.py:235/237` emits `Block <name>.lower()`. So a freshly-`output`'d card has lowercase block names (`Block dim6`, `Block frblock`) while a `ParamCard.write()` round-trip uppercases them (`BLOCK DIM6`); both load identically. Casing tells you which writer last touched the card (mssm-slha2-name-gating.md).
- `append` raising on a value-conflicting duplicate lhacode means a hand-edited card with two lines for the same id and different values fails to load (InvalidParamCard), not silently last-wins.
