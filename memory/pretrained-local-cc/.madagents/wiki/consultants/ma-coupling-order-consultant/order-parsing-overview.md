---
description: How extract_process parses coupling-order constraints into orders / squared_orders / constrained_orders, and the order_pattern regex.
---

# Order-constraint parsing in `extract_process`

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, method
`extract_process` (signature `4822-4824`: `def extract_process(self, line, proc_number=0, overall_orders={}, avoid_squared_orders=False)`).

## The regex (`4883-4885`)
```python
order_pattern = re.compile(
   r"^(?P<before>.+>.+)\s+(?P<name>(\w|(\^2))+)\s*(?P<type>"
   r"(=|(<=)|(==)|(===)|(!=)|(>=)|<|>))\s*(?P<value>-?\d+)\s*?(?P<after>.*)")
```
- Requires a `>` in `before` (so it only matches process lines).
- `name` = word chars OR literal `^2`.
- `type` alternation lists `===`, `!=`, `>=`, `<` — but these get filtered out later by the valid-type lists; only a subset is actually accepted.
- `value` may be negative (`-?\d+`).
- Parsing is iterative from the *back* of the line: each match consumes one
  constraint, then `line = before + after` and re-matches (`4967-4968`).

## Three output dictionaries (`4887-4889`)
- `orders` — amplitude-level constraints, `{name: value}`.
- `squared_orders` — `{basename: (value, type)}` for `^2` names.
- `constrained_orders` — `{name: (value, type)}` for strict `==`/`>`.

## Valid-operator lists (`3036-3037`)
```python
_valid_sqso_types = ['==','<=','=','>']
_valid_amp_so_types = ['=','<=', '==', '>']
```
- Squared orders accept `== <= = >` (no `<`).
- Amplitude orders accept `= <= == >` (same set, different order).
- `===`, `!=`, `>=`, `<` parse in the regex but fail validation
  (`4933-4935` sqso, `4945-4947` amp) -> `InvalidCmd`.
- Cross-check from tab-completion (`2174-2175`): the process-command completer
  offers each coupling (and `WEIGHTED`) only as `<=`, `==`, `>`, `^2<=`,
  `^2==`, `^2>` — i.e. it never SUGGESTS bare `=` or `<`. `=` still parses (as
  `<=` with a warning); `<` does not. So the UI nudges toward the unambiguous
  operators even though the validator's accepted set still includes `=`.

## Dispatch per constraint (`4914-4968`)
1. Alias rewrite if `name in coupling_alias` (`4918-4926`) — see
   `coupling-aliases.md`.
2. If `name` ends `^2` (`4927-4940`): squared order. `basename` must be in
   `model_orders + ['WEIGHTED']` else `InvalidCmd`. Validate type vs
   `_valid_sqso_types`. `=` -> `<=` with warning. Store `(value,type)`.
3. Else amplitude order (`4941-4965`): `name` must be in `model_orders` or
   `'WEIGHTED'`. Validate vs `_valid_amp_so_types`.
   - `=`/`<=` -> `orders[name]=value` (`=` with value!=0 warns, see
     `equals-interpretation-and-strict-equality.md`).
   - `==` -> `constrained_orders[name]=(value,'==')`; also (unless
     `avoid_squared_orders`) `squared_orders[name]=(2*value,'==')`; also
     `orders[name]=value` (`4955-4960`).
   - `>` -> `constrained_orders[name]=(value,'>')`; also (unless
     `avoid_squared_orders`) `squared_orders[name]=(2*value,'>')` (`4962-4965`).

## Assembly into ProcessDefinition (`5329-5352`)
- `sqorders_values = {k: v[0]}` and `sqorders_types = {k: v[1]}` split the
  squared_orders tuples into two dicts.
- Stored keys: `orders`, `squared_orders` (values), `sqorders_types`,
  `constrained_orders`, `split_orders`, plus non-slice keys.
- At most one negative squared-order constraint allowed (`5330-5332`).

## `default_unset_couplings` (`4970-4980`)
If `options['default_unset_couplings'] != 99` and any order/squared-order was
set, every model coupling NOT otherwise constrained is set to that max value in
`orders`. Logged at info.

## Constrained-orders are LO-only (`4983-4985`)
If `constrained_orders` non-empty and `LoopOption != 'tree'` -> `InvalidCmd`:
amplitude order constraints for non-LO can only be `<=`. So `==`/`>` amplitude
constraints are rejected at NLO.

## squared-but-no-orders fallback (`4994-4999`)
If `orders=={}` and `squared_orders!={}` and no perturbation couplings:
for each squared order, if value>=0 and type!='>', set `orders[order]=value`;
else `orders[order]=99` (negative or `>` -> can't know leading -> max).

## Two OTHER order regexes (not the main `order_pattern`)
The main `order_pattern` (`4883`) is one of three order-bearing regexes in this
file. The other two are simpler and live outside `extract_process`:

- **`get_proc_options` position-finder (`5494`)**: `r"^(.+)\s+(\w+)\s*=\s*(\d+)\s*$"`.
  Only `name=value` (no operators besides `=`, no negatives, no `^2`). Its job
  is NOT to parse constraints but to LOCATE where the option string begins
  (compared against `/` and `$` positions) so the line can be split into
  process vs. options (`5491-5510`). The real parsing is still done later by
  `extract_process`'s main regex.
- **`overall_orders` regex (decay chains, `5666` + `5673`)**: see below.

## `overall_orders` — orders after the `@N` process number
`extract_decay_chain_process` (`5661`) parses orders written AFTER the process
number, e.g. `p p > t t~ @1 QED=0 QCD=2`:
- `proc_number_pattern` (`5666`): `r"^(.+)@\s*(\d+)\s*((\w+\s*\<?=\s*\d+\s*)*)$"`
  captures the trailing `name(<?=)value` group.
- That group is iterated by a second regex (`5673`):
  `r"^(.*?)\s*(\w+)\s*\<?=\s*(\d+)\s*$"`, each match -> `overall_orders[name]=int(value)`
  (`5676-5679`).
- RESTRICTED GRAMMAR: only `=` or `<=` (`\<?=`), only non-negative `\d+`, no
  `^2`, no `==`/`>`. So no squared orders, no strict equality, no negatives can
  ride after `@N`.
- `overall_orders` is passed into `extract_process` (`5691`/`5694`) but is NOT
  merged into `orders`/`squared_orders`/`constrained_orders`. Inside
  `extract_process` it is only stored verbatim as the procdef key
  `'overall_orders'` (`5347`). It rides ALONGSIDE this slice's three dicts as a
  separate constraint channel. (Only the decay-chain path supplies a non-empty
  `overall_orders`; the signature default is `{}` at `4822`.)
