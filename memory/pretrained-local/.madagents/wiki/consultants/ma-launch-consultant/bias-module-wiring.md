---
description: run_card bias_module/bias_parameters (RunCardLO-only) registration + how launch wires the selected bias module into the compiled generator — treatcards param-reconcile + BIAS/bias.inc injection, configure_directory copy/validate/compile, dummy no-op fallback, correct_bias at combine.
---

# Bias-module wiring (biased event generation)

Covers the LO run_card knobs `bias_module` / `bias_parameters` and how `launch` compiles+links the chosen bias module into madevent. Scope: RunCardLO only. All file:line for MG5_aMC v3.7.1.

## Registration + defaults (RunCardLO, banner.py)
- `banner.py:4279`: `self.add_param("bias_module", 'None', include=False, hidden=True)`. Default is the **string** `'None'`; `include=False` → bias_module itself writes to NO `.inc`. **No `allowed=` list** — accepts any value (a directory name resolvable under `Source/BIAS/`, or an absolute path to a custom module dir). So `ptj_bias` is not enum-validated; it is accepted because a `ptj_bias/` dir ships in the Template (below). Validation is existence + `make requirements`, not an allowed-list.
- `banner.py:4280`: `self.add_param('bias_parameters', {'__type__':1.0}, include='BIAS/bias.inc', hidden=True)`. Registered literal is `{'__type__':1.0}`, NOT `{}`. `__type__` is a sentinel: `add_param` (banner.py:1337-1344) records the dict value-type (here `float`/double from `1.0`) in `dict_parameter`, then **deletes `__type__`** — so the *operative* default is the empty dict `{}`. `include='BIAS/bias.inc'` → this param IS written into the generated Fortran include `BIAS/bias.inc`.
- Both are `hidden=True` (not shown in the standard run_card unless expanded).
- **LO-only.** RunCardNLO (banner.py:5594-6406) registers NEITHER `bias_module` nor `bias_parameters`. NLO's biasing is a different mechanism: `flavour_bias` (default registered banner.py:5709 — read fresh; requires `event_norm='bias'`) + `bias_weight_function` dummy hook (banner.py:5603). Do not conflate.
- `ProcCharacteristic` also carries a `bias_module` key (banner.py:1758, default `'None'`) — the persisted record of which module the process dir was last compiled against (used by configure_directory to detect changes; see below).

## bias_parameters card syntax + parsing (banner.py ConfigFile.__setitem__, dict branch 1216-1265)
A dict-param card entry is `<value> = bias_parameters`. Accepted forms for `<value>`:
- **Full reset** (banner.py:1229-1239): `{ptj_bias_target_ptj: 1000.0, ptj_bias_enhancement_power: 4.0} = bias_parameters` — braces, comma-separated, each pair `rsplit(':',1)`; replaces the whole dict. This is the canonical card form.
- **Incremental** single-entry (no braces): `name : value`, `name , value`, or `name value` → `.update()` one key, does not reset (banner.py:1240-1252).
- Values are `format_variable`'d to the declared type (double) at banner.py:1256. Keys are kept verbatim (used later as Fortran variable names).
- A literal Python dict object assigned directly is rejected in the list-path (banner.py:1167-1169 "not being able to handle dictionary in card entry") — the dict branch at 1216 is the live path for card text.

## treatcards: param reconcile + inject (madevent_interface.py:do_treatcards, run mode)
`do_treatcards` (madevent_interface.py:3175), run mode, after ninitial==1 beam-zeroing:
- `if run_card['bias_module'].lower() not in ['dummy','none']:` (3284) gate — `'None'`/`'dummy'` skip the whole block.
- Resolve `Source/BIAS/<basename(bias_module)>` (3286-3287). If that dir absent but the given path is a dir (3288-3289), require `makefile` + `<name>.f` (3292-3295) then `misc.copytree` the custom module into `Source/BIAS/<name>` (3296-3297). Using basename means an already-present module is not overwritten.
- **Default-param harvest** (3300-3333): reads the module's `<name>.f`, scans for a comment block `C parameters = { 'k': v, ... }` and parses declared keys/defaults into `default_bias_parameters`.
- **Reconcile** (3334-3339): for each user `run_card['bias_parameters']` key — if not among the module's declared defaults, `logger.warning('%s not supported by the bias module. We discard this entry.')`; else overwrite the default. Result stored back into `run_card['bias_parameters']`.
- `run_card.write_include_file(opt['output_dir'])` (3343) then emits `BIAS/bias.inc`.

## Injection to Fortran (banner.py:write_include_file dict branch 3661-3664)
For a dict param, each entry writes `'%s = %s \n' % (fortran_name=key, f77_formatting(value))`. So `bias_parameters` becomes, in `BIAS/bias.inc`:
```
ptj_bias_target_ptj = 1000.000000d0
ptj_bias_enhancement_power = 4.000000d0
```
The dict **keys are the Fortran variable names** — which is why `ptj_bias.f` declares `double precision ptj_bias_target_ptj` etc. (Template/LO/Source/BIAS/ptj_bias/ptj_bias.f:43-44). The `C parameters = {...}` comment block (ptj_bias.f:17-18) is both the declared-default source AND documents the keys.

## configure_directory: copy-detect / validate / compile (madevent_interface.py:6050+)
After `do_treatcards('')` (6166) and `make all` on Source (6171-6172):
- `bias_name = basename(run_card['bias_module'])`; **`if bias_name.lower()=='none': bias_name='dummy'`** (6176-6178). So when bias_module is `None`, the shipped no-op **`dummy`** module (Template/LO/Source/BIAS/dummy/) is what gets linked — a bias module is ALWAYS linked; `None` just selects the identity/no-op one.
- Refresh `bias_dependencies` symlink from `Source/BIAS/<bias_name>` into `SubProcesses` (6180-6185).
- **Change detection** (6187-6190): if `proc_characteristics['bias_module'] != bias_name` and `lib/libbias.a` exists → remove `libbias.a` and set `force_subproc_clean=True` (forces madevent recompile so the new bias links in).
- **Validation** (6194-6203): if `bias_module not in ['dummy',None]` → `make requirements` in the module dir; output must contain `VALID` and not `INVALID`, else `raise InvalidCmd`.
- `self.compile(cwd=Source/BIAS/<bias_name>)` (6205) builds the module (→ `libbias.a`); `proc_characteristics['bias_module']=bias_name` written back (6206-6209).
- If `force_subproc_clean` → clean-recompile subprocs (6211+).

## Runtime weight correction (do_combine_events)
- `do_combine_events` (madevent_interface.py:3770): after nb_event, `if bias_module not in ['dummy','none'] and nb_event: self.correct_bias()` (3941-3942); also fired for `custom_fcts` (3943-3944). This is the launch-side hook that un-does the artificial enhancement in the stored event weights (so σ stays unbiased while phase-space regions are over-sampled). correct_bias internals are the mc-integration/weighting territory; the launch hook is here.

## Shipped modules (Template/LO/Source/BIAS/)
- `dummy/` (dummy.f + makefile) — no-op, linked when bias_module=None.
- `ptj_bias/` (ptj_bias.f + makefile + bias_dependencies) — enhances high-ptj tail; params `ptj_bias_target_ptj` and `ptj_bias_enhancement_power` (declared defaults in the `C parameters = {...}` comment block, ptj_bias.f:17-18 — read fresh).

## Common misconceptions (source-checked)
1. `bias_parameters` is commonly stated to default to `{}`; source shows the registered default is `{'__type__':1.0}` (a type-declaration sentinel), with the operative default becoming `{}` only after `__type__` is stripped (banner.py:4280, 1337-1344). `bias_module` defaults to the string `'None'` (banner.py:4279). Both are RunCardLO-only; NLO uses `flavour_bias` instead (banner.py:5709).
2. Card syntax `{...} = bias_parameters` (full reset) is valid; incremental single-key forms are also accepted (banner.py:1216-1265).
3. Compile/link happens in `configure_directory` (madevent_interface.py:6176-6206), NOT in treatcards; treatcards only reconciles params + writes `BIAS/bias.inc` (madevent_interface.py:3284-3343). Values are injected as Fortran assignments keyed by the dict keys as variable names (banner.py:3661-3664).
4. `ptj_bias` is accepted by directory resolution (it ships in Template/LO/Source/BIAS/), NOT by an allowed-list enum. When bias_module is None, the `dummy` no-op module IS compiled+linked (bias_name None→'dummy', madevent_interface.py:6177-6178).
