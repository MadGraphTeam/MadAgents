---
description: generate_virtuals_from_OLP — BLHA external one-loop-provider (GoSam) path — OLE_order.lh, makevirt, libgolem_olp linking, make_opts libOLP patch, contract parse, BinothLHA.inc.
---

# OLP / BLHA external-virtuals path (v3.7.1)

`ProcessExporterFortranFKS.generate_virtuals_from_OLP(self, process_list, export_path, OLP)` — `$MADGRAPH_INSTALL/madgraph/iolibs/export_fks.py:2277`. The alternative to MadLoop for the virtual ME: hand the one-loop generation to an external OLP via the Binoth Les Houches Accord (BLHA). Fires only when the requested OLP is not `'MadLoop'`. Ties into the p-directory fact that `BinothLHA.f` symlink target is `../BinothLHA_OLP.f` when `OLP!='MadLoop'` (p-directory-layout page).

## Flow (generic + GoSam-specific)
1. Makes `OLP_virtuals/` under export_path; writes the BLHA order file `OLE_order.lh` via `write_lh_order` (`:2286`).
2. **GoSam branch** (`OLP=='GoSam'`, `:2293`):
   - Copies `Template/loop_material/OLP_specifics/GoSam/makevirt` + `gosam.rc` into `OLP_virtuals/` (`:2294-2297`).
   - Symlinks `Cards/param_card.dat` in.
   - Runs `./makevirt` (`subprocess.call`, cwd=virtual_path), logging to `virt_generation.log` (`:2302-2305`).
   - Detects shared-lib extension (`so` default, also `dylib`) by probing `Virtuals/lib/libgolem_olp.<ext>` (`:2308-2314`).
   - Checks `olp_module.mod` + `lib/libgolem_olp.<ext>` exist and retcode==0, else raises `fks_common.FKSProcessError` (`:2319-2321`).
   - Symlinks `libgolem_olp.<ext>` into `export_path/lib` (`:2323`).
3. **make_opts libOLP patch** (`:2326-2349`): rewrites `Source/make_opts` replacing `libOLP=`:
   - darwin: `libOLP=-Wl,-lgolem_olp` (rpath unsupported; lib path auto-wired).
   - other: `libOLP=-Wl,-rpath=<export_path/lib> -lgolem_olp` — uses ABSOLUTE path (comment: works only if the front-end disk is mounted on all worker nodes; the relative-rpath alternative is commented out).
4. **Generic OLP** (any OLP, `:2353-2360`): parses the returned contract `OLE_order.olc` via `parse_contract_file`, propagates per-process labels with `write_BinothLHA_inc` into SubProcesses, symlinks `OLE_order.olc` into SubProcesses.

## Cautions
- The absolute-rpath in make_opts (non-darwin) hardcodes the front-end `lib/` path into the executable — breaks on worker nodes that don't mount the front-end disk. Source comment acknowledges this; the safer relative-rpath is left commented.
- GoSam virtual generation actually RUNS `makevirt` at output time (compiles libgolem_olp). Output failure here aborts with FKSProcessError pointing at `virt_generation.log`. Runtime/external-tool dependent — needs gosam installed; probe before asserting it succeeds.
- This whole method is skipped on the default MadLoop path; only `output ... --OLP=GoSam` (or another non-MadLoop OLP) reaches it. The OLP selection / BLHA contract semantics beyond what the exporter copies/links is madloop-slice territory.
