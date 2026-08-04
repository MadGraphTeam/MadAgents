---
description: The three class-level parse enumerations (_valid_nlo_modes, _valid_sqso_types, _valid_amp_so_types) plus _check_opts and coupling_alias, verbatim from madgraph_interface.py v3.7.1 — read source to confirm, they drift across versions.
---

# Parse enumerations (v3.7.1, verbatim)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, class-level (3035-3037, 2999).

```
_valid_nlo_modes   = ['all','real','virt','sqrvirt','tree','noborn','LOonly', 'only']   # 3035
_valid_sqso_types  = ['==','<=','=','>']                                                # 3036 (squared-order operators)
_valid_amp_so_types= ['=','<=', '==', '>']                                              # 3037 (amplitude-order operators)
_check_opts        = ['full','timing','stability','profile','permutation','gauge','lorentz','brs','cms']  # 2999 (def line; list continues 3000)
```

These are consumed in extract_process:
- `_valid_nlo_modes` at 4863 (the `if option in self._valid_nlo_modes:` bracket-option validation in extract_process; raise message at 4872; nlo-syntax slice owns semantics). ALSO consumed upstream in `master_interface.py:Switcher` at 211 (do_add), 245 (do_check), 268 (do_generate) — the Switcher validates the mode and routes the interface before extract_process runs, so the user-visible bad-mode error comes from there, not 4863. See switcher-predispatch-layer.md.
- `_valid_sqso_types` at 4933 (`NAME^2 op VALUE`; coupling-order slice owns semantics).
- `_valid_amp_so_types` at 4945 (`NAME op VALUE`; coupling-order slice owns semantics).
- `_check_opts` at check_check 1012.

## coupling_alias (extract_process 4892-4907, model-dependent)
Built from `self._curr_model.get('coupling_orders')`:
- model has `EW` (not `QED`): `QED→EW`, `QED^2→EW^2`, `aEW→EW^2=2*`.
- model has `QED` (not `EW`): `EW→QED`, `EW^2→QED^2`, `aEW→QED^2=2*`.
- model has `QCD` (not `aS`): `aS→QCD^2=2*`.
The `=2*` suffix means: strip suffix, double the value. (coupling-order slice owns the operator semantics; this is the alias-resolution parse step.)

## CAUTION
These lists drift across MG versions — always re-read source for the active install rather than trusting this page for a non-3.7.1 environment.
