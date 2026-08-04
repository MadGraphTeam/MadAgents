---
description: MadSpinOptions.default_setup full option set, defaults, allowed values, and post_set validators (interface_madspin.py)
---

# MadSpinOptions — the card option set

`class MadSpinOptions(banner.ConfigFile)` at `$MADGRAPH_INSTALL/MadSpin/interface_madspin.py:56`.
`default_setup` at :58 registers every option via `add_param` (:60-79). **Cache the lookup, not the value:** the default literals in the table below are drift-prone and version-pinned — the `:NN` coordinate is the evidence, the cached number is not. Read each default fresh at its line before relying on it. `spinmode` is kept as the one worked example (`"madspin"` @ :69, one of `allowed=['full','madspin','none','onshell']`); treat every other literal the same way. What IS general and stays cached is the mechanism/role/allowed-enum text per row (the sentinel ROLE, not its trigger number; the allowed set, not the chosen default).

| option | default | allowed / notes |
|---|---|---|
| `max_weight` | `-1` | :60. `-1` = sentinel "estimate it". `check_set` coerces to float (:462). |
| `curr_dir` | `os.path.realpath(os.getcwd())` | :61. reset by `do_import` to the event dir (:198). |
| `Nevents_for_max_weight` | `0` | :62. `0` = sentinel; resolved at import from nevents (see madspin-import-resolution page). |
| `max_weight_ps_point` | (default at :63) | :63. PS points per event for max-weight estimate; read the default fresh. Default card ships a `set max_weight_ps_point` line. |
| `BW_cut` | `-1` | :64. sentinel: inherit `bwcutoff` from input banner (see import-resolution page). |
| `nb_sigma` | `0.` | :65. sentinel; resolved at import. |
| `ms_dir` | `''` | :66. scratch dir; `post_set_ms_dir` mirrors into `curr_dir` (:84). If set + `madspin.pkl` exists, `do_launch` short-circuits to `run_from_pickle` (:624). |
| `max_running_process` | (default at :67) | :67. open-file cap (read default fresh); running scales ~2*VALUE (help_set :527). |
| `onlyhelicity` | `False` | :68. when True, launch proceeds with no decay branches (:568, :649). |
| `spinmode` | `"madspin"` | :69. `allowed=['full','madspin','none','onshell']`. Selects launch dispatch. `full` and `madspin` take the SAME launch dispatch (both fall through the none/onshell/bridge switch, :617-634) but are NOT strictly identical — see full-vs-madspin note below. |
| `use_old_dir` | `False` | :70. debug only. |
| `run_card` | `''` | :71. path/inline cuts for `spinmode != madspin`; `post_set_run_card` (:98) loads a `banner.RunCard` or builds a cutless `RunCardLO`. |
| `fixed_order` | `False` | :72. NLO counter-event handling; `post_fixed_order` (:121) emits two warnings (scale-bias; only onshell handles it correctly). |
| `seed` | `0` | :73. `0` -> random seed picked at launch (:658). `post_set_seed` seeds `random` once (:90). |
| `cross_section` | `{'__type__':0.}` | :74. force normalization for none/onshell. |
| `new_wgt` | `'cross-section'` | :75. `allowed=['cross-section','BR']`. weighting when particle count inconsistent. |
| `input_format` | `'auto'` | :76. `allowed=['auto','lhe','hepmc','lhe_no_banner']`. |
| `frame_id` | (default at :77) | :77. polarization frame (read default fresh); overwritten from run_card at import for LO (:258), forced to the NLO frame id for NLO (:260). |
| `global_order_coupling` | `''` | :78. |
| `identical_particle_in_prod_and_decay` | `'average'` | :79. `post_identical...` (:129) restricts to crash/average/max/first. |

## check_set validation (`:440`)
- `valid = ['max_weight','seed','curr_dir','spinmode','run_card']` (:456) — names accepted even if not in options dict; otherwise unknown -> InvalidCmd (:457).
- `spinmode` re-validated to full/onshell/none/madspin (:471) — note error text says "3 value" but lists 4.
- `run_card` edition rejected when `spinmode=='madspin'` (:475-476): "edition of the run_card is not allowed within normal mode".
- typo alias: `Nevents_for_max_weigth` -> `Nevents_for_max_weight` (:484).
- `set NAME=VALUE` (no space) is split into `[NAME, VALUE]` (:444-447); a bare `args[1] == '='` is popped (:453-454).
- `set onlyhelicity` with no value defaults the value to `'True'` (:448-449) — only `onlyhelicity` gets this bare-flag treatment.
- `max_weight` coerces Fortran-double `'d'`->`'e'` before `float()` (:462), so `1d3` parses.

## set-command surface area (what's discoverable vs settable)
- `do_set` (:493) joins `args[1:]` with spaces -> multi-token values stored as one string.
- `complete_set` (tab) offers `list(options.keys()) + ['seed','spinmode']` (:503) and, for `spinmode`, only `["full","onshell","none"]` (:513) — OMITS the default `madspin` and `onshell`-vs case. `help_set` (:528) documents only `spinmode=none`. So the default `spinmode='madspin'` and the `full`/`onshell` modes are under-advertised at the prompt even though `check_set` accepts all four. A user relying on tab-completion may not see `madspin`.

## `full` vs `madspin` are NOT functionally identical (corrects the "full is an alias" doc claim)
Despite sharing the launch dispatch, two source-visible divergences:
- **Interface-level (:474-476):** `set run_card ...` is rejected ONLY when `spinmode=='madspin'` ("edition of the run_card is not allowed within normal mode"). So `spinmode='full'` PERMITS editing the run_card (cuts on the decay ME); `spinmode='madspin'` (the default) FORBIDS it. This is the one in-slice behavioural difference between the two.
- **Internals (out of slice):** decay.py has explicit `mode=='full'` branches (decay.py:3506 `key[0]=='full'`, decay.py:4142 `elif mode=='full'` in the calculator/external-process handling), showing the decay engine treats `full` distinctly from `madspin`. The precise physics difference is decay.py internals.
So "full == madspin, functionally identical" is WRONG as stated; correct: same launch path, but full allows run_card cuts and the decay engine has full-specific branches.

## onshell REQUIRES f2py
`spinmode='onshell'` -> `run_onshell` (:619-620, def :1373). Its per-event weight evaluates the decayed matrix element through an **f2py-compiled Fortran module**: `calculate_matrix_element` imports `all_matrix2py` (:1770), initialises it with the param_card (:1795/:1797), and caches `smatrixhel(pdg, 0, *args)` into `self.all_f2py[pdir]` (:1799). So the onshell weight is |M|²-based and needs a compiled f2py extension; the full/madspin decay engine does not go through this `all_f2py` path. (The onshell weight formula w=|M_full|²/(|M_prod|²·∏|M_decay|²) is thus consistent with onshell using explicit MEs; the full/madspin reweighting math is decay.py internals — GAP.)

## Gaps
- What each spinmode does to the decay generation internally is MadSpin internals (decay.py), out of slice.
- The full/madspin reweighting formula (whether/how it uses decay MEs vs phase-space sampling) is decay.py internals, out of slice — the onshell |M|²-via-f2py path is the only interface-visible ME evaluation.
