---
description: The standalone reweight_card's `set BLOCK ID VALUE` lines reuse the param_card SLHA machinery I own — routed through AskforEditCard.do_set (the launch-dialogue card editor) and ParamCardIterator for scans. `set width N` rewrites to the DECAY block.
---

# reweight_card `set` reuses the param_card SLHA editor

The systematics slice owns reweight-module activation / `change` / `do_launch` flow. What is MINE: the `set` lines in a reweight_card ARE param_card SLHA block/id addressing, parsed by the exact same `ParamCard` / `AskforEditCard.do_set` / `ParamCardIterator` code path as the launch dialogue's param_card editing.

## The routing — reweight_interface.py
- `do_set` (L1050-1055) does NOT parse the value itself: it stashes `self.stored_line = "set %s" % line` and re-dispatches to `launch`. So a `set yukawa 6 180.0` line in a reweight_card is deferred, not parsed inline.
- `handle_param_card` (L802) writes the banner SLHA (`self.banner['slha']`) to `rw_me/Cards/param_card.dat` (L817-818), then calls `CommonRunCmd.ask_edit_card_static(cards=['param_card.dat'], first_cmd=self.stored_line, ...)` (L819-822). `first_cmd` = the stored `set …` lines. The returned `cmd.param_card` (L824) is a `ParamCard`; `card.write()` re-serializes it.
- So the reweight `set` is executed by the **AskforEditCard card editor** — identical to the launch-dialogue param_card `set`. There is no separate reweight parser.

## The addressing — AskforEditCard.do_set (common_run_interface.py L5868)
- L5884 lowercases every arg except the value → block-name casing robust (`set YUKAWA 6 X` == `set yukawa 6 X`; ParamCard keys are lowercased on read).
- L6117-6118 "PARAM_CARD WITH BLOCK NAME" branch fires when `args[start] in self.param_card` (an SLHA block key) **or** `args[start] == 'width'`, and `card in ['','param_card']`. So bare `set <block> <id...> <value>` addresses the ParamCard block directly.
- L6130-6131: `if args[start] == 'width': args[start] = 'decay'` — **`set width 25 0.00407` is rewritten to address the DECAY block** (the SLHA particle total-width entry). Confirmed. (`decay` is also directly usable.)
- L6150: `key = tuple([int(i) for i in args[start+1:-1]])` — the lhacode is the SLHA integer-tuple id: `yukawa 6`→`(6,)`, `mass 25`→`(25,)`, `nmix 1 1`→`(1,1)` (multi-index mixing-matrix entry). L6163 validates `key in self.param_card[block].param_dict`; unknown id → warning, no-op.
- L6187 "NO BLOCK NAME" branch: `set <pname> <value>` (parameter name, no block) resolves via `pname2block` and expands to `param_card <block> <lhaid> <value>`. Both the block-name and bare-name forms are param_card addressing.
- `set param_card <block> <id> <value>` (explicit card prefix) ALSO works (same `card in ['','param_card']` guard) — the reweight card simply omits the prefix. The `set param_card` prefix is optional, not forbidden; what matters is that the addressing is the param_card SLHA model.

## scan: is the ParamCardIterator I own
- Value field accepts `scan:[...]` / `scan1:` / `scan2:` — validated at set-time (L6171 `args[-1].startswith('scan')` → passed through to `setP` verbatim, not float-coerced).
- reweight `handle_param_card` re-detects scan in the assembled card with `^(decay)?[\s\d]*scan` (L832, same regex as `static_check_param_card`), and on a hit builds `check_param_card.ParamCardIterator(new_card)` (L844) — my class. Multiple scanned params → Cartesian grid via `itertools.product`; same-integer-suffix (`scan1:`) params advance locked together, bare `scan:` → own axis. See scan-and-auto-detection.md for the iterator internals.

## So: claims 1-3 all TRUE
1. `set BLOCK ID VALUE` in a reweight_card IS param_card SLHA block/id addressing; `set width N` → DECAY block. ✓
2. `scan:`/`scan1:`/`scan2:` is the ParamCardIterator value form; multiple scans form a grid. ✓
3. The reweight `set` parsing reuses ParamCard + AskforEditCard.do_set + ParamCardIterator — my machinery, no separate parser. ✓
