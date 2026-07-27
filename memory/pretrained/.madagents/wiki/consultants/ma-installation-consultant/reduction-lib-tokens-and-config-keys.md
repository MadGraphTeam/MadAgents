---
description: NLO reduction-library install TOKENS (Golem95/collier/ninja/oneloop; case-sensitive, built-in vs advanced) and their mg5_configuration.txt CONFIG KEYS with template defaults (ninja/collier/golem/samurai/pjfry/output_dependencies) — v3.7.1.
---

# Reduction-library install tokens & config keys

Covers the loop reduction libraries (OPP: ninja; TIR: collier/golem95/samurai/pjfry; scalar: oneloop) — the exact `install <token>` names and the `mg5_configuration.txt` keys that point MadLoop at their libraries. Menu-driven install flow is on `reduction-library-install-menu.md`; this page owns the token list + config keys.

## Install tokens (`madgraph_interface.py:3002-3012`; exact-membership check `:1358`, NO `.lower()` — CASE-SENSITIVE)
Two lists, unioned at `:3012`:
- `_install_opts` (built-in, NOT HEPToolsInstaller) `:3002-3004`: includes **`Golem95`** (capital G, digits "95"), `QCDLoop`, `looptools`, `MadSTR`, `RunningCoupling`, `Delphes`, `MadAnalysis4`, `ExRootAnalysis`, `maddm`, `maddump`, `update`.
- `_advanced_install_opts` (HEPToolsInstaller-managed) `:3007-3010`: includes **`collier`**, **`ninja`**, **`oneloop`** (all lowercase), plus pythia8/lhapdf6/lhapdf5/hepmc/fastjet/rivet/... .

Consequences of case-sensitive exact membership (`if args[0] not in ...` `:1358` → `InvalidCmd('Not recognize program')`):
- `install Golem95` VALID; `install golem` / `install golem95` INVALID (error).
- `install collier` / `install ninja` / `install oneloop` VALID; `install Collier` / `install Ninja` INVALID.
- `install looptools` VALID → routes to `install_reduction_library` (the AskLoopInstaller menu, `loop_interface.py:511`) — the menu-driven way to get ninja/collier/golem together.
- Inside the AskLoopInstaller menu the code-dict remaps the lowercase `'golem'` key to the `Golem95` install token (`prog={'golem':'Golem95'}`, `reduction-library-install-menu.md`) — but that remap is menu-internal; a bare `install golem` at the prompt still errors.

## NO `install loop_qcd_qed_sm` (or any model) token
`loop_qcd_qed_sm` (the QCD+QED / EW-corrections loop model) is **NOT** an install target — absent from both opt lists → `install loop_qcd_qed_sm` errors `Not recognize program`. It appears in `madgraph_interface.py` only as (a) `_online_model` restriction-tag metadata `:2895` (seeds `display modellist`, NOT a download trigger) and (b) the model-loader Feynman-gauge force `:5774-5775`. Only **`loop_sm`** is bundled under `models/`; `loop_qcd_qed_sm` is NOT bundled — it arrives via `import model loop_qcd_qed_sm` → online model-DB auto-download (see `online-model-import-trigger.md`), or manual placement. There is no separate "install the EW loop model" command.

## Config keys (`input/mg5_configuration.txt`, template defaults read live)
These keys hold the path to each reducer's static/shared lib (or a keyword). Template state in this image:
- `# pjfry = auto` (COMMENTED) `:215` — auto = autodetect on system; `''`/`None` disables.
- `golem = None` (**UNCOMMENTED / active**) `:222` — the ONLY active reduction-lib line; default disables Golem95. (Doc-myth: default is NOT `auto`; it ships as `None`.)
- `# samurai = None` (COMMENTED) `:229`.
- `# ninja = ./HEPTools/lib` (COMMENTED) `:234`.
- `# collier = ./HEPTools/lib` (COMMENTED) `:240` — comment notes COLLIER needs a STATIC library built.
- `# output_dependencies = external` (COMMENTED) `:246` — allowed values per comment `:242-245`: `external` (ML5 symlinks the MG5-wide libs; default), `internal` (ML5 copies all deps into the output for a self-contained dir), `environment_paths` (ML5 searches `$PATH`/env).

Read/resolve of these (golem/samurai `'auto'` → `misc.which_lib` then local `$MG5DIR/{golem95,samurai}/lib`, samurai VERSION-recency gate; `None`/`''` → Python None) is on `mg5-configuration-read-resolve.md:32-33`. Because golem's active line is `None`, Golem95 is disabled by default even though `install Golem95` exists — it must be installed AND the key set (`install Golem95` writeback sets `golem = <name>/lib`, `mg5-configuration-tool-paths.md`).

## Ninja bundling reality (doc-myth check)
Ninja is NOT shipped pre-compiled in a vanilla MG5 tarball — it is an `_advanced_install_opts` build target (from the online HEPToolsInstaller or offline `vendor/ninja.tar.gz` — read its bundled version with `tar -tzf`). The AskLoopInstaller default is `ninja:'install'`, so it IS installed by default on the first loop-ME output / `install looptools` (online, not from vendor — online is hardcoded True; see menu page). In an image where that already ran, `HEPTools/ninja/` exists with BOTH `libninja.a` (static) and `libninja.so*` (shared) under `HEPTools/lib` (symlinks into `../ninja/lib`). So "default OPP reducer, statically available" is true post-install, but it is built, not a prebuilt bundled binary. Same pattern for `oneloop` (avh_olo, `vendor/oneloop.tar.gz`) which ninja depends on.
