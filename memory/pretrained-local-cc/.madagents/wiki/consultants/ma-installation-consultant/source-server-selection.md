---
description: install source-server selection — UCL/INFN servers, --source flag (ucl/uiuc/custom-url), mirror fallback, MG5aMC_WWW override (v3.7.1).
---

# Source-server selection for `install`

In `do_install`, `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:6560-6612`.

## Servers
`install_server` `:6505-6506`:
```
['http://madgraph.phys.ucl.ac.be/package_info.dat',     # index 0 = "ucl"
 'http://madgraph.mi.infn.it/package_info.dat']          # index 1 = "uiuc" (label is historical)
```
CAUTION: the `--source=uiuc` flag maps to index 1, which is the **INFN Milan** mirror (`madgraph.mi.infn.it`), NOT a UIUC URL. The string "uiuc" is a legacy alias; do not assume a uiuc.edu host. `:6573-6574`.

## --source flag
`:6571-6581`. Takes the last `--source=` arg.
- `--source=ucl` → `r=[0]` (UCL only).
- `--source=uiuc` → `r=[1]` (INFN mirror only).
- `--source=<custom>` → if custom ends in a digit or `/`, append `/package_info.dat`; the custom URL is appended to `data_path` and `r=[2]`. `:6578-6581`.

## Default (no --source)
`:6582-6587`. `r = random.randint(0,1)` then `r=[r, 1-r]` — random primary with the other as fallback. If env `MG5aMC_WWW` is set non-empty, its `/package_info.dat` is appended and index 2 is tried FIRST (`r.insert(0,2)`).

## Fetch loop & fallbacks
`:6591-6612`. Iterates `r`, urlopen each; skips on exception or non-200. If all fail → `MadGraph5Error('Impossible to connect any of us servers...')`.
- Corrupt `package_info.dat` line (split != 2 fields) with no explicit `--source`: recurses `do_install(line+' --source='+{0:'uiuc',1:'ucl'}[index])`. `:6606-6611`.
- Tarball name absent from `path` after fetch with no `source`: tries the OTHER mirror via recursion (`misc.sprint('try other mirror', ...)`). `:6672-6681`. NB: that `misc.sprint` trace is SILENT in a default release run (`__debug__` False) — see `debug-flag-release-behavior.md`; the fallback still happens, you just don't see the message. With an explicit source, raises "Online server are corrupted. No tarball available for <name>" unless `'xxx' in advertisements[name][0]` (then "Program not yet released. Please try later"). NB: the `'xxx'` check is lowercase + first-ref-only and currently matches NO `install_ad` entry — see do-install-flow.md Cautions; the placeholder path is dormant in v3.7.1.

## Other flags (per card)
- `--force` → passed through `additional_options`; advanced_install overwrites existing install without warning (see do_install docstring `:6520-6523`).
- `--keep_source` → retain tarballs (HEPToolsInstaller option, forwarded via `options_for_HEPToolsInstaller`).

## Parallel selector: online model-db fetch (boundary note)
The online-MODEL database fetch reuses the SAME server-selection shape but is a SEPARATE, flag-less code path — `import_ufo.get_model_db()` at `$MADGRAPH_INSTALL/models/import_ufo.py:104-133`:
- Same two hosts (`madgraph.phys.ucl.ac.be/models_db.dat`, `madgraph.mi.infn.it//models_db.dat`), same `r=random.randint(0,1); r=[r,1-r]` random-primary-with-fallback, same `MG5aMC_WWW` override inserted at index 0 (`:114-116`).
- KEY DIFFERENCE: there is NO `--source` flag here. `--source=ucl/uiuc/<url>` governs ONLY `do_install`'s `package_info.dat` fetch; it does NOT steer model-db selection. A user wanting to pin the model-db mirror must use `MG5aMC_WWW`, not `--source`.
- The fetch BODY — `import_model_from_db` (`:135+`): match `model_name` against `models_db.dat` lines, `misc.wget` the tarball into `$MG5DIR/models/`, untar, plus an `omattelaer`-username PYTHONPATH special-case — is **ufo-slice territory** (the "actual fetcher"), not mine. My slice owns only the recognition that the SELECTION pattern is shared and `--source` is install-only. Route fetcher internals to the ufo slice.

## Gaps
- Actual contents of remote `package_info.dat` are network-fetched at runtime — not statically verifiable from source. Tarball URLs come from there.
