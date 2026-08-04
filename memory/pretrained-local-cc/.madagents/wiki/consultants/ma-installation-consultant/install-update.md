---
description: install update / install_update — auto-update modes, .autoupdate state file, patch application machinery, build-number check (v3.7.1).
---

# install update (install_update)

`install_update(self, args, wget)` at `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:6991`. Reached via `do_install('update')` `:6539`.

## Modes `:7139-7181`
`--mode=` arg (default `userrequest`):
- `mg5_start`: timeout 2s, default 'n', `update_delay = auto_update * 86400`; returns immediately if `auto_update==0`.
- `mg5_end`: timeout 5s, default 'n', removes 'on_exit' option; same delay/zero-check.
- `userrequest`: default 'y', `update_delay=0` (always checks).
- else: `InvalidCmd('Unknown mode...')`.
`-f` -> force (skips the y/n prompt) `:7144`. `--timeout=` and `--input=` also parsed.

## Preconditions
- Requires `$MG5DIR/input/.autoupdate` to exist `:7183-7190`; else "doesn't support auto-update" (bzr/beta). Raises only in userrequest mode.
- Requires `patch` binary on PATH `:7192-7197`.
- `.autoupdate` holds `version_nb`, `last_check`, `last_message` `:7199-7212`.
- Skips if `now - last_check < update_delay` `:7217`.

## Build-number check `:7220-7285`
- SIGALRM-based timeout around `urllib.request.urlopen('http://madgraph.phys.ucl.ac.be/mg5amc3_build_nb')`. Parses line0=web_version, line1=msg_version, rest=message.
- On connect failure in mg5_end mode, rewrites `.autoupdate` to wait ~24h.
- Shows INFORMATION message if `msg_version > last_message`.
- `web_version == version_nb` -> "No new version of MG5 available". `version_nb > web_version` -> "impossible to update". Else offers update.

## apply_patch (`:6995-7137`, nested fn)
Applies a downloaded `.patch` text covering bzr-style directives:
- renamed directory / renamed file (copied manually since `patch` mishandles renames).
- added / removed+re-added file bookkeeping.
- `patch -p1` invoked on the body `:7049-7051`.
- modified-file path remaps, touch file/dir, link file directives.
- chmod +x sweep over bin/ and Template/*/bin trees `:7092-7101`.
- Recompiles `vendor/CutTools` (`-j1`) and `vendor/IREGI/src` if their `.a` libs exist `:7126-7130`.
- Returns True if patch references binary files (signals "some files need to be loaded separately").

## Cautions
- Hardcoded update host is UCL (`madgraph.phys.ucl.ac.be`), independent of the `--source` mirror used by `install <tool>`.
- `auto_update` default is 7 days (commented in config, so effectively the in-code default); `auto_update=0` disables startup/exit checks.

## Gaps
- Patch contents and `mg5amc3_build_nb` are network-fetched at runtime; not statically verifiable.
