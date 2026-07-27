---
description: ALOHA expression parsing (aloha_parsers.py PLY grammar UFO->primitive-object string) and function-library hooks / fermion-flow checks (aloha_fct.py).
---

# Parser + function hooks

Cites `$MADGRAPH_INSTALL/aloha/aloha_parsers.py`, `aloha_fct.py`, v3.7.1.

## aloha_parsers.py — UFO Lorentz expr -> object algebra
- `UFOExpressionParser` (`:45`) — PLY (lex/yacc) base. Tokens for `csc/sec/acsc/asec/sqrt/pi/conj/im/re/complex/function/variable` (`:75-119`); grammar `p_statement_expr`/`p_expression_binop`/uminus/parentheses/group (`:153-178`).
- `ALOHAExpressionParser(UFOExpressionParser)` (`:192`) — ALOHA dialect. `aloha_object` whitelist (`:194-200`) names every primitive the parser may emit (P, Gamma, ProjM/P, Spin2, EPSL/T, UFP/UFM…, Tnorm/TnormZ). The parser turns a UFO `lorentz.structure` STRING into a STRING of Python that `create_aloha.parse_expression` then `eval`s into primitive objects.
- Key rules: bare `VARIABLE` → `Param('name')` (`:222-224`) — so any unknown identifier becomes a model parameter; `PI` → `Param('PI')` and sets `KERNEL.has_pi` (`:202-205`); `complex(a,b)` passthrough (`:234`); power: if base is an aloha_object keep textually, else route to `KERNEL.add_function_expression('pow',...)` (`:207-219`); funcs `csc/sec/acsc/asec/re/im/sqrt` (`:244+`).
- `parse_expression` (create_aloha.py:255) optionally flips P/PSlash sign (`need_P_sign`) to reconcile HELAS-vs-FeynRules outgoing-fermion momentum convention.

## aloha_fct.py — fermion-flow + function library
- `WrongFermionFlow(Exception)` (`:20`).
- `get_fermion_flow(expression, nb_fermion)` (`:26`) — analyzes the Lorentz string to recover which spinor indices pair into a fermion line; used by `apply_conjugation` to validate Majorana / flow-violating vertices (returns pairing dict; compared to canonical `{2i+1:2i+2}`).
- `check_flow_validity(expression, nb_fermion)` (`:104`).
- `guess_routine_from_name(names)` (`:163`).

## Why this matters
The whitelist + "unknown→Param" rule means a typo or a model function not in the list silently becomes a model parameter rather than erroring at parse time — it surfaces later as an undefined coupling/parameter. Special functions in a Lorentz expression must be registered (parser token + `aloha_fct`/`KERNEL.add_function_expression`) or they won't lower correctly.
