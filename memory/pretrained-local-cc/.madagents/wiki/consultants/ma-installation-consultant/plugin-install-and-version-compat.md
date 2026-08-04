---
description: install_plugin path, plugin version-compatibility enforcement (is_plugin_supported), and the __debug__/-O nuance that flips out-of-bounds behavior (v3.7.1).
---

# Plugin install & version compatibility

## install_plugin set
`install_plugin = ['maddm', 'maddump', 'MadSTR', 'cudacpp']` at `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:6484`. These install via the standard `do_install` tarball path (NOT advanced_install) but get the plugin branch `:6802-6860`: no compilation, `shutil.move` into `PLUGIN/<name>`, then `__import__('PLUGIN.<name>')` to read the plugin's `new_interface`, `new_output`, `latest_validated_version`, `minimal_mg5amcnlo_version`, `maximal_mg5amcnlo_version`.
- If the py3 import fails: logs "Plugin not python3 compatible! It will run with python2", falls back to a text-scan for `new_interface`, sets `pyvers=2`. `:6819-6832`.
- Prints "Plugin <name> correctly interfaced. Latest official validition for MG5aMC version <latest_validated_version>." `:6834`.
- If `new_interface`: writes launcher `bin/<name>.py` (python{pyvers}, `-O` in release / `-tt` under `__debug__`) and chmods it. `:6835-6859`.

CAUTION: `do_install` reads `minimal_/maximal_mg5amcnlo_version` but does NOT compare them — install never blocks on version bounds. The actual enforcement is at plugin LOAD time.

## `--mode=<name>` launch-time plugin load + discovery (`bin/mg5_aMC:169-187`)
A plugin is SELECTED at launch via `-m/--mode=<name>` (`option dest="plugin"`, `:64`). Load path (`:169-187`):
- `root_path` = install root (`:47`, dir two up from `bin/mg5_aMC`).
- Discovery is TWO-tier: (1) if `root_path/PLUGIN/<name>` exists → `__import__('PLUGIN.<name>')` (`:170,178-179`) — the in-tree directory (where `install_plugin` `shutil.move`s a plugin, and where a manual "copy inner dir into `<MG5_DIR>/PLUGIN/<name>`" lands). (2) ELSE try `__import__('MG5aMC_PLUGIN.<name>')` (`:172-173`) — an EXTERNAL importable package resolved off `PYTHONPATH` (user-global plugin route). If neither imports → prints `ERROR: <name> is not present in the PLUGIN directory. Please install it first` and `sys.exit()` (`:175-176`).
- `if not plugin.new_interface:` → warns "Plugin: <name> do not define dedicated interface and should be used without the --mode options" then `sys.exit()` (`:180-182`). So a plugin whose `__init__.py` sets `new_interface=None` (an output-only / non-interface plugin, e.g. cudacpp) CANNOT be driven by `--mode`.
- **LOAD-TIME version gate** `:184-185`: `if not misc.is_plugin_supported(plugin): sys.exit()`. This is the enforcement point — an out-of-version-bounds plugin makes `mg5_aMC --mode=<name>` EXIT before the REPL starts (under default `-O`; see below). Then `cmd_line = plugin.new_interface(mgme_dir=...)` (`:186`), `cmd_line.plugin=<name>` (`:187`).
- Mechanism: `--mode=<name>` reads the plugin `__init__.py` and its version attrs; the version-gate attribute NAMES are `minimal_mg5amcnlo_version` / `maximal_mg5amcnlo_version` / `latest_validated_version` (read by `is_plugin_supported`, `misc.py:2144-2146`) — NOT compared at install, only here at load.

## Version-compat enforcement: is_plugin_supported
`$MADGRAPH_INSTALL/madgraph/various/misc.py:2130-2167`.
- MG5 version from `get_pkg_info()['version'].split('.')` (or cached `plugin_support['__mg5amcnlo__']`).
- Missing any of min/max/val_ver attrs -> "Plugin <name> misses some required info... discarded" (False). `:2143-2150`.
- In-bounds test `:2153-2154`: `get_older_version(min_ver, mg5_ver)==min_ver AND get_older_version(mg5_ver, max_ver)==mg5_ver`. If in-bounds: supported=True; additionally if `mg5_ver < val_ver`, warns "Plugin ... NOT being validated with this version ... last validated with version <val>". `:2156-2159`.
- OUT of bounds `:2160-2166`:
  - under `__debug__` (True): logs `error` "...not supported... Keep it active (please update status)" and **keeps it active** (True).
  - else (`-O`, `__debug__` False): logs `error` "...is not supported..." and **disables** it (False).

## __debug__ / -O nuance (load-bearing)
`bin/mg5_aMC:75-78` re-launches itself with `python -O ...` in a normal release install (when `bin/create_release.py` is absent OR `--web`), so `__debug__` is False at runtime by default → an out-of-version-bounds plugin is DISABLED. Launching with `--debug` (`:62`) suppresses the relaunch, keeps `__debug__` True → out-of-bounds plugin stays ACTIVE with only an error logged. Same plugin silently dropped or kept depending on debug mode. Under `--mode=<name>` the False verdict is HARDER than "disabled": `is_plugin_supported`→False makes `bin/mg5_aMC:185 sys.exit()` — MG5 refuses to start at all. So a MadSTR declaring `maximal_mg5amcnlo_version=(3,6,1000)` on v3.7.1 (3.7.1 > 3.6.1000 → out of bounds): default `-O` run → `mg5_aMC --mode=MadSTR` prints "not supported" + exits; `--debug` run → loads with only an error logged. This is why "v3.7.0+ needs manual editing of `__init__.py`" is real for a default launch (must bump the max attr or run `--debug`). The relaunch is probe-confirmed (default `mg5_aMC` spawns a `-O` child) and is the same switch that flips the launcher flag above (`-tt` vs `-O`, `:6837`). This is one instance of a slice-wide pattern — see `debug-flag-release-behavior.md` for the full set of `__debug__`-gated install sites (MA5 install recovery, silenced `misc.sprint`, etc.).

## MG5 version source feeding the comparison: get_pkg_info
`is_plugin_supported` gets `mg5_ver` from `get_pkg_info()['version'].split('.')` at `$MADGRAPH_INSTALL/madgraph/various/misc.py:2141` (unless `plugin_support['__mg5amcnlo__']` is cached). `get_pkg_info` (`misc.py:116-150`):
- Reads `$MADGRAPH_INSTALL/madgraph/VERSION` via `files.read_from_file(..., parse_info_str, print_error=False)`, caches result in module global `PACKAGE_INFO` (read once per process).
- MADEVENT mode (`MADEVENT` flag) reads a DIFFERENT file: `MGMEVersion.txt` (two dirs up from `internal`), NOT `VERSION`, and hardcodes `date='20xx-xx-xx'`. `:131-135`.
- CAUTION: if `VERSION` is missing/unparseable, falls back to `info_dict['version']='3.x.x'` (`:146-148`). That `'3.x.x'.split('.')` → `['3','x','x']` flows straight into the plugin min/max `get_older_version` comparison (`misc.py:2102-2125`). `get_older_version` does NOT do "string ordering of 'x'" (probe `get_older_version('3.x.x', bounds)`) — it `int()`s each component and on the FIRST non-integer component short-circuits, returning `v2` (if `a1` non-int) or `v1` (if `a2` non-int) immediately (`:2113-2120`). So the poison effect is **bound-dependent, not universal**:
  - bounds straddling integer-3 on BOTH ends without a `3` boundary (e.g. min `2.0.0`, max `9.9.9`): first-component compare resolves before reaching `'x'` → reads IN bounds (supported, probe-confirmed True).
  - a `3.y.z`-shaped max (the realistic v3.x plugin case, e.g. min `3.5.0` max `3.9.0`): the `3`==`3` tie advances to component 2, hits `'x'`, short-circuits returning `max_ver` ≠ `mg5_ver` → out of bounds → DISABLED under `-O` / kept-with-error under `__debug__` (probe-confirmed False).
  So a corrupt/absent `VERSION` doesn't error here; it poisons plugin compat for plugins whose bound tie-breaks past the major version — NOT "every plugin," and not via string ordering. (The version-file read is my slice; this is the in-slice consequence for plugin compat.)

## Version files (read live; all drift per install — read the file, do not recall the number)
- `$MADGRAPH_INSTALL/VERSION`: `version` + `date` fields — read live (this tier scopes to MG5 v3.7.1; the build `date` drifts).
- `$MADGRAPH_INSTALL/HELAS/HELASVersion.txt`: bundled HELAS version — read live.
- `$MADGRAPH_INSTALL/Template/LO/TemplateVersion.txt`: LO-template version — read live.
- `$MADGRAPH_INSTALL/Template/NLO/TemplateVersion.txt`: NLO-template version — read live (structural note: this file has no trailing newline).
- `$MADGRAPH_INSTALL/Template/MadWeight/TemplateVersion.txt`: DOES NOT EXIST in this image (the `Template/MadWeight/` dir is present but carries no `TemplateVersion.txt` — verified by `ls`; a read raises "No such file or directory", not an empty read).

## maddm (MadDM plugin source ABSENT here — core-MG5 half only)
`maddm` is a registered plugin install target (`install_plugin :6484`; option list `:3003`; citation `install_ad['maddm']=['arXiv:1804.00444'] :6501`; `install_name['maddm']='maddm' :6515`). What `install maddm` actually does, walked in core MG5 source:
- FETCH: NOT a git clone. `do_install` fetches a TARBALL whose URL comes from the remote `package_info.dat` on the MG5 package server (UCL `madgraph.phys.ucl.ac.be` / INFN `madgraph.mi.infn.it`, `--source=ucl/uiuc/<url>`-steerable; `MG5aMC_WWW` override). A github URL like `maddmhep/maddm.git` (as used in manual git-clone recipes) is NOT anywhere in MG5 source. `rm -rf $MG5DIR/maddm` then `misc.wget`+`tar -xzpf` (`:6668-6698`). Whether the remote `package_info.dat` carries a `maddm` line today is a runtime/network fact (GAP).
- PLACE: plugin branch `if name in plugin:` (`:6803`) — no compile, `shutil.rmtree(PLUGIN/maddm)` then `shutil.move($MG5DIR/maddm → PLUGIN/maddm)`. Recognition of a plugin thereafter is directory-existence in `PLUGIN/<name>` (`bin/mg5_aMC:170`), so a manual route (`git clone … PLUGIN/maddm`) lands the plugin in the SAME place core-install would and IS recognized.
- WIRE-UP: a manual `cp PLUGIN/maddm/maddm bin/maddm` is NOT what core MG5 does. Core AUTO-GENERATES `bin/maddm.py` (`.py` suffix) — a python WRAPPER that runs `mg5_aMC … --mode=maddm` (`:6835-6859`), written ONLY `if new_interface` truthy (a plugin-internal attr; maddm is an interface plugin but that attr lives in its absent `__init__.py` → GAP). It does NOT copy the plugin's own inner `maddm` script into `bin/`. So the copy-an-executable and MG5's write-a-`.py`-wrapper are DIFFERENT launcher mechanisms; the manual copy works only if the plugin's inner `maddm` is itself a self-contained launcher (plugin-internal, unverifiable here).
- VERSION GATE: `install maddm` READS maddm's `minimal_/maximal_mg5amcnlo_version` (`:6816-6820`) but does NOT compare them — install never blocks on version. A plugin's own `minimal_mg5amcnlo_version` (e.g. `(2,9,3)`) "refuses to load under older MG5" is enforced by CORE MG5 at LOAD time (`is_plugin_supported`, `misc.py:2130-2167`, called at `bin/mg5_aMC:184-185`), reading the plugin's own attr — confirmed core reads/enforces a plugin minimal-version attribute; the attr's VALUE is plugin-internal (GAP). In this image bin/ holds only `mg5_aMC` (no maddm.py) — maddm not installed, consistent.

## Gaps
- A specific plugin's actual min/max/validated values live in that plugin's `__init__.py` (fetched at install) — not in MG5 source; verify per plugin.
- Whether remote `package_info.dat` carries a `maddm` tarball line, and maddm's `new_interface`/version attrs — MadDM plugin/network state, not core-source-decidable.
