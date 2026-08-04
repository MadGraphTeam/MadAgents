---
description: AskLoopInstaller — the loop reduction-library install menu (cuttools/iregi/ninja/collier/golem); default codes, online-hardcoded, cycling logic, resume-detection, and code-dict dispatch (v3.7.1).
---

# Reduction-library install menu (AskLoopInstaller)

The interactive menu that drives `install_reduction_library` (the loop reduction-library install — `vendor-and-offline-install.md` owns the consumer/dispatch; THIS page owns the menu that produces the answer). Class `AskLoopInstaller(cmd.OneLinePathCompletion)` at `$MADGRAPH_INSTALL/madgraph/interface/loop_interface.py:930`. Invoked at `:527` via `self.ask('install','0', ask_class=AskLoopInstaller, timeout=300, path_msg=' ')`; the returned object's `answer`/`code` dict is the `to_install` consumed at `:530+`.

PROBE-CONFIRMED (parse-time, this image: instantiate-free class introspection): `local_installer=['ninja','collier']`, `required=['cuttools','iregi']`, `order=['cuttools','iregi','ninja','collier','golem']`, `bypassed=['pjfry']`; `self.online = True` hardcoded with the urllib reachability probe commented out; default `ninja:'install'` and the `no-cmake → collier:'off'` gate both present in `__init__` source.

## Tool lists (`:932-935`)
- `local_installer = ['ninja','collier']` — the ONLY two tools with an offline-from-vendor option.
- `required = ['cuttools','iregi']` — always installed, NOT user-selectable (the `if key in self.required: continue` at `:1023-1024` skips registering allowed answers / cycling for them).
- `order = ['cuttools','iregi','ninja','collier','golem']` — menu display order (numbers 1-5).
- `bypassed = ['pjfry']` — pjfry suppressed (off rows for bypassed tools are hidden, `:1015-1016`).

## Default codes (`:952-962`)
Initial `self.code` (`:952-956`): `ninja:'install'`, `collier:'install'`, `golem:'off'`, `cuttools:'required'`, `iregi:'required'`.
- **`self.online = True` is HARDCODED** (`:950`) — the urllib reachability probe is commented out (`:945-949`). So the `not self.online` block (`:957-960`, which would flip ninja/collier to `'local'` and golem to `'fail'`) NEVER runs. CONSEQUENCE: `'local'` (offline vendor-tarball install) is **never auto-selected** — it is reached ONLY by the user explicitly cycling/typing it. The default loop-tool install therefore goes ONLINE (`ninja`/`collier` → online `install`), not offline, even though `vendor/ninja.tar.gz`/`vendor/collier.tar.gz` exist.
- **No cmake → collier forced `'off'`** (`:961-962`, `if not misc.which('cmake')`). collier's TIR build needs cmake; absent it, collier is dropped from the default install.

## Resume detection (`:964-982`)
If a prior partial install exists, codes are overwritten to that PATH (a filesystem path value, not a keyword):
- install dirs: `heptools_install_dir` if set, else `install_dir1=$MG5DIR/HEPTools`, `install_dir2=$MG5DIR`.
- `CutTools`/`IREGI` under `install_dir1` → cuttools/iregi code = that dir.
- `collier`/`ninja` under `install_dir1`, `golem95` under `install_dir2` → code = that path (ninja → `<dir>/ninja/lib`).
So re-running the menu after a partial install shows "already at <path>" rows and skips re-install for those.

## Cycling logic (`default()`, `:1045-1086`)
Hitting enter / `0` / `done` / EOF → `value='done'`, returns the current `code` dict. Typing a tool name or its number CYCLES its option:
- For a `local_installer` tool (ninja/collier): `off → install → local → off → ...` (online assumed, so `off`→`install`, `install`→`local`, `local`→`off`). `:1067-1077`.
- For a non-local tool (golem): `off ↔ install` only (no `local` state). `:1067-1075`.
- Two-token form `<tool> <on|install|off|noinstall|local|<path>>` sets directly (`:1083-1107`): `local`/online-`install` honored only for `local_installer` tools, else warns "offline installer not available for %s" and forces `off` (`:1097-1105`); a path value (`os.sep` in arg) is taken verbatim as the code (`:1106-1107`).
- Per-tool `do_ninja`/`do_collier`/... lambdas route to `apply_name` → `default('<name> <line>')` (`:1120-1124`).

## Recommended marker (`:1020`)
ninja and collier rows print `(recommended)` ONLY when their code is `'install'`. They are the recommended OPP/TIR pair for the default online install.

## How the code-dict dispatches (consumer, `install_reduction_library` `:530-605` — full table owned HERE; `vendor-and-offline-install.md` owns ONLY the `'local'` offline-tarball branch)
Each `key,value` in the answer:
- cuttools/iregi with a PATH value → copy prebuilt `libcts.a`+`mpmodule.mod` / `libiregi.a` from that path into `$MG5DIR/vendor/{CutTools/includects,IREGI/src}`. Accepts THREE path layouts: bare, `<tool>/...`, or `vendor/<tool>/...` (`:535-567`). cuttools/iregi with a NON-path value (`'required'`) → skipped here (they're installed via the normal flow).
- `value=='local'` → OFFLINE: `do_install(key, paths={HEPToolsInstaller: vendor/OfflineHEPToolsInstaller.tar.gz}, additional_options=['--ninja_tarball=vendor/<key>.tar.gz'])`. NOTE: the flag is literally `--ninja_tarball=` even for collier (`'--ninja_tarball=%s' % pjoin(...,'%s.tar.gz'%key)`, `:573`); ONLY ninja additionally appends `--oneloop_tarball=vendor/oneloop.tar.gz` (`:574-575`). On `InvalidCmd`: warns + `set <key> ''` + `save options` (disables it). `:570-589`.
- `value=='install'` → ONLINE `install <key>`, with golem remapped to `Golem95` (`prog={'golem':'Golem95'}`). `:591-597`.
- `value=='off'` → `set <key> ''` + save. `:599-601`.
- else (a path value, i.e. resume-detected) → `set <key> <path>` + save. `:603-605`.

## Cautions
- The offline vendor-tarball path (`'local'`) is opt-in only because `online` is hardcoded True — do NOT tell a user "no internet → it installs from vendor automatically." It does not; the auto-default is online. (Refines `vendor-and-offline-install.md`'s `'local'` description: that branch exists but is user-triggered, not auto.)
- `--ninja_tarball=` carrying a COLLIER tarball is intentional (the OfflineHEPToolsInstaller reads that flag generically), but is a footgun if read literally as ninja-only.
- collier silently absent from the default install when cmake is missing — a loop run would then have no TIR reducer from this menu unless golem/iregi are chosen.
