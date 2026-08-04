---
description: install machinery self-re-dispatch — one install/import command fans out into recursive do_install/advanced_install/convert calls; the visible command is not the full action set (v3.7.1).
---

# Install-machinery re-dispatch fan-out

## The principle
A single user-issued `install <tool>` or `import model` does NOT map to one install action. The install machinery re-dispatches itself — recursing into `do_install` / `advanced_install` / `exec_cmd('convert model ...')` with added flags or a different tool — at numerous baked-in sites. When reasoning about "what does `install X` actually do," enumerate the fan-out, not just the top-level call. This is control flow in MG5 source (which call recurses, with what added flag, under what gate) — **source-decidable, not a runtime prediction**; no probe needed to establish the edges.

## The re-dispatch sites (all `madgraph_interface.py`)
| Site | Trigger | Re-dispatch | Added flag / note |
|---|---|---|---|
| `:6611` | corrupt `package_info.dat` line, no explicit `--source` | `do_install(line+' --source=<other>')` | mirror flip; recursion to retry parse |
| `:6680` | tarball name absent from `path`, no `--source` | `do_install('<args> --source=<othersource>')` | other-mirror fallback (the `misc.sprint` trace at `:6679` is SILENT in default release — see debug-flag page) |
| `:6331` | HEPToolInstaller exit 66 (already installed) + user y | `advanced_install(tool, +['--force'])` | overwrite re-run |
| `:6261` | pythia8/eMELA install, LHAPDF absent, user default-y | `advanced_install('lhapdf6')` | dependency install |
| `:6344` | madanalysis5 default install FAILED, `not __debug__` | `advanced_install('madanalysis5', +['--no_MA5_further_install','--no_root_in_MA5','--force'])` | auto-recovery; `__debug__`-gated (default release only; `--debug` suppresses — see debug-flag page) |
| `:6357` | pythia8 install SUCCEEDED (post-install) | `advanced_install('mg5amc_py8_interface', +['--force'])` | chained — pythia8 always drags py8_interface |
| `:7321` | (install update path) | `do_install('mg5amc_py8_interface', +['--force'])` | py8_interface refresh on update |
| `:5796` | `import_ufo` raises `UFOError`, `auto_convert_model` True | `exec_cmd('convert model <path>')` then retry import with `auto_convert_model` forced False | in-place model edit + one retry (no loop) |

## What this catches beyond the instances
The instances live on four different pages (source-server-selection: `:6611`/`:6680`; advanced-install-writeback: `:6331`/`:6261`/`:6344`/`:6357`; install-update: `:7321`; convert-model: `:5796`). No single page tells a reader the *through-line*: **the visible command understates the action set.** Operative consequences this catches that no instance page states as a rule:
- `install pythia8` => pythia8 + mg5amc_py8_interface (always) + possibly lhapdf6 (if absent, default-y) + possibly an overwrite re-run (exit 66) — up to four installs from one command.
- `install eMELA` => possibly lhapdf6 too.
- `import <py2-UFO>` with default `auto_convert_model=True` => an in-place model rewrite happens BEFORE the error surfaces; the model dir is mutated even on a "failed" import (the retry can still fail, but the convert already ran).
- Any FUTURE re-dispatch site added to the install machinery is caught by the same "enumerate the fan-out" discipline.

## Cautions
- Several edges are **gated**: the mirror-fallback recursions (`:6611`/`:6680`) fire ONLY with no explicit `--source`; the MA5 auto-recovery (`:6344`) fires ONLY under `not __debug__` (default release). With `--debug` or an explicit `--source` the fan-out is smaller.
- The lhapdf6 and overwrite edges are **user-gated** (y/n prompts, default y) — under a non-interactive/`-f` run they take the default; under explicit `n` they don't fire.
- The convert-model retry forces `auto_convert_model=False` for the second attempt so a still-broken model does not loop (`:5799`).
