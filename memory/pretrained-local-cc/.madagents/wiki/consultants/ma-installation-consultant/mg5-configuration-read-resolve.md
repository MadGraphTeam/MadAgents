---
description: set_configuration — how mg5_configuration.txt is READ/resolved at startup — config-file precedence chain, None-sentinel, per-tool path validation (silent reset to None), golem/samurai auto, generic do_set fallback (v3.7.1).
---

# mg5_configuration.txt read & resolve (set_configuration)

`set_configuration(self, config_path=None, final=True)` at `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:7354`. The READ side of the config slice — complements `mg5-configuration-tool-paths.md` (which owns the file ENTRIES + the install WRITEBACK). This page owns how those entries are parsed, validated, and turned into `self.options` at startup.

## Config-file precedence chain (`:7363-7380`)
Read in this order, each via a recursive `set_configuration(path, final=False)`:
1. `$MADGRAPH_BASE/mg5_configuration.txt` (if env `MADGRAPH_BASE` set).
2. User config: `~/.mg5/mg5_configuration.txt` (legacy, if `~/.mg5` exists) ELSE `$XDG_STATE_HOME/mg5_configuration.txt` (fallback `~/.config/...`).
3. In-tree `$MG5DIR/input/mg5_configuration.txt` — read LAST with `final=True`.
CAUTION: the in-tree config is read LAST, so its values OVERRIDE the user/`~/.mg5` config — opposite of the usual "user config wins" expectation. (`final=False` calls only populate `self.options`; the final in-tree pass also runs all the resolution/validation below.)
- If `config_path` doesn't exist, it is created from `input/.mg5_configuration_default.txt` (`:7383`). Default run cards `default_run_card_{lo,nlo}.dat` are also materialized from their dotfiles on first run (`:7385-7387`).

## Line parse (`:7392-7413`)
- `#`-comment stripped (split on first `#`); `=`-split into name/value (lines without `=` silently ignored).
- Special keys `mg5_path`, `f2py_compiler{,_py2,_py3}`, `lhapdf` (the `:7405` exclusion list) skip the direct `self.options[name]=value` store. They are routed to `set2_<name>(value.split())` ONLY if `hasattr(self,'set2_<name>')` AND value non-empty (`:7407-7410`). Only `set2_f2py_compiler` (`:8193`) and `set2_lhapdf` (`:8410`) exist — there is NO `set2_mg5_path`, NO `set2_f2py_compiler_py2/_py3`. So `mg5_path` and `f2py_compiler_py2/_py3` are in the exclusion list yet have no setter: they are NEITHER stored directly NOR routed — effectively dropped from `self.options` by this branch (they only get the None-check at `:7411`). All non-excluded keys → `self.options[name] = value`.
- **`value.lower()=="none"` or `value==""` → `self.options[name] = None`** (`:7411-7412`). This is what makes the `$MADGRAPH_INSTALL/None` / `None` sentinel (see tool-paths page) resolve to Python `None` = unset. Case-insensitive.

## Per-tool path VALIDATION → silent reset to None (`:7421-7468`)
For `pythia8_path, hwpp_path, thepeg_path, hepmc_path, mg5amc_py8_interface_path, madanalysis5_path`: each is probed for a sentinel file, trying BOTH `$MG5DIR/<path>` (relative) AND bare `<path>` (absolute). If the sentinel is absent in both → the option is **silently set to `None`** (tool treated as not installed). No error, no warning (except MA5 compat — below). Sentinels:
- pythia8 → `include/Pythia8/Pythia.h`
- mg5amc_py8_interface → `MG5aMC_PY8_interface`
- madanalysis5 → `bin/ma5` (PLUS `is_MA5_compatible_with_this_MG5(ma5path)`; incompatible → `None` + `logger.warning(message)`)
- hwpp → `include/Herwig++/Analysis/BasicConsistency.hh`
- thepeg → `include/ThePEG/ACDC/ACDCGenCell.h`
- hepmc → `include/HepMC/HEPEVT_Wrapper.h`
CONSEQUENCE: a config entry pointing at a stale/half-deleted install is silently dropped at startup — the tool just "isn't available" with no diagnostic (MA5 is the only one that warns, and only on version-incompat, not on missing-file). So "I set pythia8_path but MG5 says it's not installed" is usually this sentinel-file check failing, not a parse error.

## golem / samurai 'auto' resolution (`:7470-7503`)
For `golem`/`samurai` with value `'auto'`: `misc.which_lib('lib<key>.a')` first; else local `$MG5DIR/{golem95,samurai}/lib/lib<key>.a`; else `None`. samurai additionally gets a VERSION-file recency check — too-old/unreadable VERSION → disabled to `None` with a multi-line "samurai too old" notice.

## Other key handling (`:7505-7541`)
- `key.endswith('path')` (any other `*path` key) → `pass` (kept as-is, no validation).
- `run_mode`, `auto_update` → cast to `int` (`:7508`). (So `auto_update`'s stored value is integerized here — ties to install-update.md's default-7.)
- `lhapdf_py3`/`lhapdf_py2` (if not None/none) → `do_set("<key> <val> --no_save")`.
- `notification_center` → eval'd to bool.
- GENERIC FALLBACK (`:7531`): any remaining non-path, non-special key → `do_set("<key> <value> --no_save", log=False)`; on `MadGraph5Error` prints the error + `logger.warning("Option <key> from config file not understood")`. So an unrecognized/typo'd config option WARNS but does not crash startup.

## Tail (`:7543-7549`)
- `MadEventCmd.mg5amc_py8_interface_consistency_warning(self.options)` → logs a warning if pythia8/py8_interface versions are inconsistent.
- `launch_ext.open_file.configure(options)` (file-opener: text_editor/eps_viewer/web_browser) and `misc.configure_gzip(options)` (use_pigz) applied last.

## Cautions
- In-tree config OVERRIDES user config (read last) — don't assume `~/.mg5` wins.
- Tool-path entries are validated against a sentinel file and SILENTLY reset to None if missing — a present-but-stale path looks identical to "not configured." Verify the sentinel file exists, not just that the config line is present.
- `lhapdf`/`mg5_path`/`f2py_compiler*` bypass the generic store and go through `set2_*` setters — their config value is not necessarily `self.options['lhapdf']` verbatim.
