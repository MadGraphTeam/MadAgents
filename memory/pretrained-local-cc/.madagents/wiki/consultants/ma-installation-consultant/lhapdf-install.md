---
description: install lhapdf6/lhapdf5 command — token routing, dual config writeback (lhapdf + lhapdf_py3), and the hard boundary that do_install installs the LHAPDF LIBRARY only, never PDF sets (v3.7.1).
---

# `install lhapdf6` / `install lhapdf5` — LHAPDF library install (NOT PDF sets)

All in `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` unless noted.

## Tokens (case-sensitive)
- `_advanced_install_opts` `:3007` lists BOTH `'lhapdf6'` and `'lhapdf5'` — two distinct HEPToolsInstaller-managed targets. (`_install_opts.extend(_advanced_install_opts)` `:3012`, so both also live in `_install_opts`.)
- `check_install` `:1358` validates `if args[0] not in self._install_opts + hidden_prog + self._advanced_install_opts` — NO `.lower()`, so tokens are case-sensitive. `install lhapdf6` works; `install LHAPDF6` / `install lhapdf` raise `InvalidCmd('Not recognize program …')` `:1361`. (There is no bare `lhapdf` install token — `lhapdf` is only the config KEY.)

## Routing: `install lhapdf6` → advanced_install('lhapdf6')
1. `do_install` `:6552` — `lhapdf6` is in `install_ad` (`install_ad['lhapdf6']=['arXiv:1412.7420']` `:6492`, `lhapdf5`→`['arXiv:0605240']` `:6493`), so it prints the citation line `:6558` before installing.
2. `install_name = {...}` `:6508`; `install_name['lhapdf6'] = 'lhapdf6_py3'` → `name = self.install_name…` `:6625`. (lhapdf5 has no remap → stays `lhapdf5`.)
3. `args[0]='lhapdf6'` ∈ `_advanced_install_opts` `:6635` → `advanced_install('lhapdf6_py3', …)` `:6649`.
4. In `advanced_install`, `name_map={'lhapdf6_py3':'lhapdf6'}` `:6165` maps it BACK to `tool='lhapdf6'`. So the round-trip installs LHAPDF v6; the `_py3` suffix only names the install subdir (`HEPTools/lhapdf6_py3`).

## Config writeback (I OWN the WRITE; interface owns the schema/read)
`advanced_install` post-install `:6359-6368`:
- **lhapdf6** `:6359-6362` — sets in-memory BOTH `options['lhapdf_py3'] = prefix/lhapdf6_py3/bin/lhapdf-config` `:6360` AND `options['lhapdf'] = options['lhapdf_py3']` `:6362`. NUANCE: only `save options … lhapdf_py3` `:6361` is persisted to the config FILE; the `lhapdf` key is set in-memory but NOT explicitly re-saved in this branch — its on-disk value updates only if a later `save options` writes the full block. Operatively the RUNTIME (systematics/reweight) reads `options['lhapdf']`, so the in-memory set is what matters for the current session.
- **lhapdf5** `:6366-6368` — sets `options['lhapdf'] = prefix/lhapdf5/bin/lhapdf-config` `:6367` and `save options … lhapdf` `:6368`.
- Default before any install: `options['lhapdf']='lhapdf-config'` (bare, PATH-resolved) `:3082`; `lhapdf_py2`/`lhapdf_py3` = `None` `:3084-3085`.
- Writeback target is in-tree `input/mg5_configuration.txt` when `heptools_install_dir` is default, else the custom config (see advanced-install-writeback.md).

## HARD BOUNDARY: library vs PDF set
`do_install`/`advanced_install` install the LHAPDF **library/tool** ONLY. There is NO do_install path that downloads a PDF *set*. Confirmed by grep: `copy_lhapdf_set` / `get_lhapdf_pdfsets_dir` / any pdfsets fetch live ONLY in `common_run_interface.py` (runtime, scales-pdf / interface territory), never in `madgraph_interface.py`. A PDF set is fetched separately by the external LHAPDF CLI (`lhapdf install <setname>`) or dropped manually into `share/LHAPDF/` — both are LHAPDF-tool / runtime behavior, NOT my install slice. Do not claim `install lhapdf6` brings any PDF set.

## "LHAPDF not found" at the install/config boundary
- Auto-install trigger: `advanced_install` for **pythia8 / eMELA** `:6238` probes `misc.which(options['lhapdf'])` then `lhapdf-config --version` (must be 5 or 6, else `InvalidCmd`). If absent → y/n prompt to auto-install lhapdf6 (recursive `advanced_install('lhapdf6')` `:6261`); passes `--with_lhapdf{5,6}=<path|OFF>` `:6274-6283`.
- SysCalc `:6797` raises `InvalidCmd('lhapdf is required to compile/use SysCalc. Specify his path or install it via install lhapdf6')`.
- **systematics/reweight require lhapdf; NO internal-PDF fallback for PDF-error-set reweighting** (systematics slice — pointer): `systematics.py:224` `lhapdf = misc.import_python_lhapdf(lhapdf_config)`; `:225-227` `if not lhapdf and not isEVA:` → logs `'fail to load lhapdf: doe not perform systematics'` and `return`s — i.e. a SILENT SKIP of the whole systematics pass, not a hard crash and not an internal-PDF substitute. So PDF-error-set reweighting hard-requires the LHAPDF library; the operative config key it resolves through is `lhapdf` (the lhapdf-config path, set by both writeback branches above). The install command to satisfy it is `install lhapdf6`.

## Cross-slice pointers
- Config KEY `lhapdf_py3` schema + READ/resolve (None-sentinel, per-tool sentinel validation) → interface slice / `mg5-configuration-read-resolve.md`.
- PDF-set download at runtime, `pdlabel`/`lhaid` coherence → scales-pdf / common_run_interface.
- `lhapdf6` requirement for systematics/reweighting → systematics slice.
