---
description: ReweightInterface ME-source generation pipeline — do_import banner gating, create_standalone_directory (rw_me/rw_mevirt via output standalone_rw), get_LO_definition_from_NLO + NoDiagramException retry, NLO_tree fake-loop dir, compile (Sudakov libsudpy + __debug__/-O failure divergence), load_module f2py loading (all_matrix<tag>py, ctypes liball, f<N>_ prefix aliasing), dedicated_path symlink.
---

# Reweight ME-source generation pipeline

`$MADGRAPH_INSTALL/madgraph/interface/reweight_interface.py`, v3.7.1. How `ReweightInterface` *builds and loads* the standalone matrix-element code that `me-reweight-evaluation-core` then calls via `smatrixhel`. `reweight-interface` covers the command layer; `handle_param_card` covers param injection; THIS page is the dir-generation + f2py-load layer (the "where does rw_me come from" pipeline). `sa_class = 'standalone_rw'` (ri.py:70).

## do_import — banner read + mode gating (ri.py:132-220)
Entry that reads the LHE and sets `rwgt_mode` from the event file:
- Resolves `.gz` (gunzips, ri.py:157-159); sets `curr_dir` to the proc dir if input is under `Events/` (ri.py:140-143).
- Reads banner; missing banner → asks for a path (ri.py:163-165). Extracts `orig_cross` from the `init` block (ri.py:169-177).
- **Hard gates** (all `InvalidCmd`/`Exception`): no `slha` → "does not contain model information" (ri.py:182-184); no `mg5proccard` → "does not contain generation information" (ri.py:185-187); **`madspin` in banner and not `allow_madspin` → "Reweight should be done before running MadSpin"** (ri.py:189-190); no `generate` line → Exception (ri.py:212-214).
- **NLO mode degrade** (ri.py:195-208): NLO event (`[` in process AND RunCardNLO) checks three conditions, each forcing `rwgt_mode='LO'` with a warning: `store_rwgt_info` False; `OLP != 'madloop'`; lhapdf not installed. (Same three as the `change mode` re-check; see `reweight-interface`.) LO event file → `rwgt_mode='LO'` always (ri.py:209-210).
- `is_decay = len(process before '>') == 1` (ri.py:217).

## create_standalone_directory (ri.py:1962-2129) — the generator
Builds the standalone dirs the f2py ME modules compile from. Always two per library: `rw_me` (tree/Born) + `rw_mevirt` (virtual/loop) (ri.py:1967); for second model/process → `rw_me_<nb_library>`/`rw_mevirt_<nb_library>`, `nb_library` incremented and the prior library's f2pylib entries purged (ri.py:1984-1989).
- **Processes reconstructed from the banner proc_card** `generate`/`add process` lines (ri.py:1976-1979); model from `proc_card 'model'`, `-modelname` flag honored (ri.py:1969-1974). Second uses `self.second_process`/`self.second_model` if set (ri.py:2005-2012).
- Replays proc_card `set` lines (detecting `complex_mass_scheme` via regex) and `define` lines into `mg5cmd` (ri.py:2036-2046).
- **Non-UFO model → `InvalidCmd('Only UFO model can be loaded in this module.')`** (ri.py:2049-2050).
- Reloads model + multiparticle defs (ri.py:2051-2069).
- **dedicated_path symlink** (`change tree_path`/`virtual_path`): instead of generating, `files.ln` the pre-built standalone dir; `virtual_path` presence sets `has_nlo` (ri.py:2070-2084). This is the bring-your-own-standalone-ME path.
- Virtual created only if `has_nlo and 'NLO' in rwgt_mode` (ri.py:2085-2086); `multicore=='create'` pre-compiles `OLP_static` (ri.py:2088-2094).
- Second model/process triggers a recursive `create_standalone_directory(second=True)` (ri.py:2124-2125).

## create_standalone_tree_directory (ri.py:1744-1810)
The Born/tree generation called from above:
- **`set group_subprocesses False`** forced first (ri.py:1751) — each subprocess kept separate so a per-event `tag` maps to one Pdir.
- NLO procs (`[...]`) → `get_LO_definition_from_NLO` (ri.py:1760-1771); FxFx (`ickkw==3`) uses `real_only=True` for non-shortest processes (ri.py:1764-1769); `inc_sudakov` propagated.
- **`NoDiagramException` retry** (ri.py:1777-1794): if the Born has no diagrams, re-generate with `[virt=...]` (or `noborn→virt`), set `has_nlo=False` — handles loop-induced / noborn processes.
- Output exporter: `output standalone_rw <dir> --prefix=int` (ri.py:1799-1806). **Source oddity**: ri.py:1799 first builds the command WITH `--prefixf2py=<nb_rw>`, but ri.py:1802 immediately overwrites `commandline` WITHOUT it — so the *tree* output actually executed has no `--prefixf2py` (yet `path2prefix` records the intended prefix). The virtual (ri.py:1909) and NLO_tree (ri.py:2107) outputs DO pass `--prefixf2py`. `inc_sudakov` → `output ewsudakovsa <dir>` instead (ri.py:1803-1805).
- `--prefix=int` makes f2py symbols integer-prefixed; `--prefixf2py=<N>` (export_v4.py:2761-2762, `f<N>_`) namespaces a library so multiple reweight libs don't collide on f2py symbols.

## Squared-order (`NP^2==N`) reweight process lines — accepted (tree path)
The `change process` line routes to the **tree-level `generate` parser**, so squared coupling-order constraints (`NP^2==N`, `==`, the `^2` marker) that NLO has-Born `[QCD]` rejects (`amcatnlo_interface.py:541-542`, HasBorn-guarded) and MadSpin rejects are **accepted** here — this is what lets a user reweight to isolate an SMEFT squared-order bin (SM interference vs quadratic).
- `do_change` stores the raw line verbatim into `self.second_process` (ri.py:386-394) — no order parsing at change-time.
- `create_standalone_tree_directory` builds `"add process %s ;" % proc` for every non-`[...]` proc, replaces the first `add process`→`generate`, and runs it via `mgcmd.exec_cmd(commandline)` (ri.py:1759-1776). `mgcmd = self.mg5cmd = master_interface.MasterCmd()` (ri.py:107) — the full MG5 tree command surface (`do_generate`/`do_add` → tree coupling-order machinery), **NOT** `amcatnlo_interface`. The HasBorn-guarded squared-order reject lives only in the NLO interface; the tree parser never sees it, so `NP^2==2` parses like any LO squared-order idiom.
- **Gate — only the bracket-free (LO/tree) branch**: a proc containing `[` is diverted to `get_LO_definition_from_NLO` (ri.py:1760-1771), which strips the squared marker to build `pert_`/`sqrvirt` LO-of-NLO definitions — so squared-order isolation via reweight is a **tree-mode** operation. Write the reweight process WITHOUT NLO brackets (e.g. `change process p p > t t~ QED=0 NP^2==2` — illustrative; the `==2` is NOT universal: the quadratic-bin squared order is `2×(NP-per-insertion p)`, model-dependent — read `p` per model from `coupling_orders.py` and derive `N`, do not copy the integer); leave `mode` at its LO default (the ME-level ratio `|M_new|²/|M_old|²` is what isolates the bin). Adding `[QCD]` would route to the NLO path and lose the squared constraint.
- Requires ME regeneration: `second_process` being set forces `create_standalone_directory` (ri.py:571, 810) → a fresh `rw_me` standalone built and f2py-loaded; the reweight is a genuine new-ME evaluation, not a param rescale.

## NLO_tree fake-loop directory (ri.py:2095-2119)
`NLO_tree` mode (no real virtual to reweight, but weight-combination scaffolding still needed) generates a throwaway `import model loop_sm; generate g g > e+ ve [virt=QCD]` directory (golem deactivated during it), output via `output standalone_rw ... --prefixf2py=`. Requires LHAPDF or `Exception("NLO_tree reweighting requires LHAPDF to work correctly")` (ri.py:2114-2115); downloads the event's LHAPDF set (ri.py:2118-2119).

## compile — Subprocess compile + `__debug__`/-O divergence (`compile`, ri.py:2132-2194)
Compiles the generated standalone Pdirs before `load_module`. Two branches: the EW-Sudakov `libsudpy` multicore branch (reads `subproc.mg`, submits `misc.compile ['libsudpy']` per Pdir to a `cluster.MultiCore`, ri.py:2155-2185) and the ordinary `compile_SubProcess_dir` loop over `['rw_me','rw_me_<N>','rw_mevirt','rw_mevirt_<N>']` (ri.py:2187-2194).
- **`__debug__`/-O divergence on compile failure** (ri.py:2177-2184): when the Sudakov multicore compile raises, it always `logger.warning("Compilation of the Subprocesses failed")`, then under `__debug__` (default) `raise`s (hard crash with traceback); under `-O` it `compile_cluster.remove()` + `self.do_quit('')` (graceful teardown, no traceback). Same structural shape as the systematics NLO stored-vs-computed assertion (sys.py:1095-1101 raises under `__debug__`, sys.py:1055-1057 short-circuits under `-O`, see `systematics-weight-kernels`): default mode surfaces the fault hard, `-O` degrades. Two in-slice instances of this seam; the broader cross-slice version lives in the lead routing pages.

## load_module — f2py loading (ri.py:2217-2276)
Loads the compiled standalone ME into Python:
- Candidate dirs `['rw_me','rw_me_<nb_library>','rw_mevirt','rw_mevirt_<nb_library>']` (ri.py:2227); `inc_sudakov` returns early (dispatcher handles it, ri.py:2234-2235).
- Per dir, for `tag in [2*metag, 2*metag+1]`: optionally `ctypes.CDLL(liball<onedir>_<tag>me.so, RTLD_GLOBAL|RTLD_DEEPBIND)` (the "ctypes trick", best-effort, ri.py:2241-2252), then imports the f2py module `<onedir>.SubProcesses.all_matrix<tag>py` (ri.py:2253).
- **Reload mechanism**: if the module is already in `sys.modules`, delete it (and parent packages) then `importlib.import_module` + `importlib.reload` (ri.py:2255-2263). This is what the `nb_f2py_module` counter (`reweight-interface`) guards — fresh ME after a `change model`/`change process`.
- **f2py-prefix aliasing** (ri.py:2270-2276): if a prefix `f<N>_` was recorded in `path2prefix` (or auto-detected from module attrs), every prefixed attr is re-`setattr`'d under its unprefixed name so the caller's `module.smatrixhel(...)` works regardless of the per-library prefix.

## Cautions
- Reweighting an event file that already ran MadSpin → hard `InvalidCmd` (`allow_madspin` default False). Reweight must precede MadSpin.
- Non-UFO model in the banner → reweight cannot build the standalone ME (`InvalidCmd`).
- `set group_subprocesses False` is forced — the reweight ME is per-subprocess, not grouped; large multi-subprocess generations produce many Pdirs.
- `NLO_tree` silently requires LHAPDF (Exception if absent); the fake `g g > e+ ve` loop_sm dir is generated even though it has nothing to do with the user's process.
- The tree output's `--prefixf2py` is dropped by the ri.py:1802 overwrite (only virtual/NLO_tree carry it) — a source quirk; library symbol collision is avoided in practice because tree dirs differ by name (`rw_me` vs `rw_me_<N>`).
- Sudakov-compile failure raises (hard, with traceback) under default `__debug__`; under `-O` it tears down and `do_quit`s gracefully — same `-O`/`__debug__` seam as the systematics NLO assertion.
- RUNTIME claims (the generated dir layout, f2py symbol names, NoDiagramException retry firing) are read from source — a real `launch` on a reweight_card would confirm the rw_me/rw_mevirt tree and emitted weights.
