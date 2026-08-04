---
description: delphes_path config resolution + install token — code default is './Delphes' (NOT empty), resolves against mg5_path/MG5DIR to the bundled Delphes dir; the three-leg offer/run gate (path resolves / shower present / card exists)
---

# delphes_path config, the bundled Delphes, and the install token

Covers the CONFIG + PATH leg upstream of the card-existence switch (operative-card-
existence page) and shower leg (delphes-availability page). Corrects the loose "delphes_path
default empty" note: on a bundled install it is set by default.

## 1. The code default is './Delphes', NOT empty
`common_run_interface.py:653` — options_madevent dict carries `'delphes_path':'./Delphes'`
(same default in the mg5-level options_configuration). The config FILE line
`input/mg5_configuration.txt:172` is COMMENTED (`# delphes_path = ./Delphes`), but a
commented line does NOT mean unset — the code dict default fills it. So the effective
starting value is `'./Delphes'`, a relative path.

## 2. How './Delphes' resolves — set_configuration final cross-check
`common_run_interface.py:4105-4117` — for each `*_path` key (not cluster*) with non-None value:
1. `os.path.isdir(value)` (as-is, vs CWD/abs) → `os.path.realpath(value)`, keep.
2. elif `os.path.isdir(pjoin(me_dir, value))` → realpath, keep.
3. elif mg5_path set AND `os.path.isdir(pjoin(mg5_path, value))` → realpath, keep.
4. else → `self.options[key] = None`.
`'./Delphes'` resolves via leg 1 (if CWD==MG5 root) or leg 3 (`pjoin(mg5_path,'./Delphes')`
= `$MADGRAPH_INSTALL/Delphes`). The bundled `$MADGRAPH_INSTALL/Delphes` dir EXISTS
(+ `Delphes.tgz`) → isdir true → delphes_path becomes the realpath of the bundled dir.
=> On a stock bundled install, `delphes_path` is NON-empty by default; only if the dir is
absent does it fall to None (leg 4). The mg5-level install code confirms the same MG5DIR
join: `madgraph_interface.py:6231-6234` normpaths `pjoin(MG5DIR, delphes_path)`.

## 3. do_delphes path gate — check_delphes
`common_run_interface.py:335-350`: `if not self.options['delphes_path']` → retry
`set_configuration()`; if STILL unset → `raise InvalidCmd('No valid Delphes path set...')`.
So the path leg passes whenever delphes_path resolves to an existing dir (default: the
bundled one). NOTE: isdir only — a resolved delphes_path proves the SOURCE dir exists, NOT
that the Delphes binary is compiled/linked (build state is install-slice). do_delphes later
reads `pjoin(delphes_path,'data')` to pick delphes2-vs-3 (3389) and runs the binary from
`delphes_dir` (3418) — those can still fail if unbuilt though the path gate passed.

## 4. The full three-leg offer/run gate (union of pages)
For Delphes to be OFFERED in the launch menu and RUN:
- **PATH leg** — delphes_path resolves to an existing dir (this page; default satisfies it
  on a bundled install).
- **SHOWER leg** — `check_available_module` adds 'Delphes' to available_module only if PY6
  or PY8 present (madevent_interface.py:530-532); else warns and omits it. This is the REAL
  gate on a fresh bundled box (Delphes dir present, no shower → silently unavailable).
- **CARD leg** — `Cards/delphes_card.dat` must exist; its presence IS the on/off switch
  (operative-card-existence page). keep_cards / do_delphes copy-if-missing materialize it.

## 5. install token (install-slice — NOTE only, do not own)
`madgraph_interface.py:3002` `_install_opts = ['Delphes', 'MadAnalysis4', ...]` — exact
token is `Delphes` (capital D). `install Delphes` maps to config key via
`options_name = {'Delphes':'delphes_path','Delphes2':'delphes_path','Delphes3':'delphes_path',
...}` (6972). Install-time card interaction touching my slice: installing Delphes copies
`delphes_card_ATLAS.tcl` → `Template/Common/Cards/delphes_card_ATLAS.dat`
(6963-6966) and warns if no shower is installed (6969). Ownership of the install machinery
is ma-installation-consultant; I own only what delphes_path MEANS once set (this page).

## Caution
- "delphes_path default empty" is WRONG for a bundled install — it is `./Delphes` →
  resolved to the bundled dir. Emptiness only arises if the Delphes dir is missing.
- Path gate passing (dir exists) ≠ Delphes runnable (binary may be unbuilt) — INFERRED
  boundary, not probed here (delphes binary build state is install-slice).
