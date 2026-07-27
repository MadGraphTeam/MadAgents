---
description: decision rule — which install/update/plugin answers are baked into MG5 source vs fetched from a server or external tree at runtime (not source-decidable) (v3.7.1).
---

# Static vs runtime boundary in the install machinery

A recurring trap: many `install <tool>` / `install update` / plugin questions are **NOT decidable from MG5 source**, because the load-bearing value lives in a network resource or an externally-fetched file, resolved at install/update time. Before trying to source-answer an install question, classify it.

## Decision rule
Ask: *is this value baked into MG5's own tree, or fetched from a server / external tool tree at runtime?*
- **Source-decidable** (answer from MG5 code/config — walk it): the install-target sets (`_install_opts`/`_advanced_install_opts`/`install_plugin`), server URLs (`install_server`), the `--source` flag logic, citation map (`install_ad`), the conversion regexes, the `__debug__`/-O plugin branch, `mg5_configuration.txt` schema, vendor inventory.
  - INVERSION TRAP (looks runtime, is actually source-decidable): `AskLoopInstaller.online` (`loop_interface.py:950`) reads like a network-reachability answer but its urllib probe is commented out and `online=True` is HARDCODED — so the loop-reduction-menu default is statically online regardless of real connectivity, and the offline-vendor (`'local'`) branch is user-opt-in, never auto. A "what does the menu do with no internet?" question is therefore source-answerable (it ignores connectivity). See `reduction-library-install-menu.md`.
- **Runtime/external** (NOT source-decidable — say so, name where it actually lives): everything below.

## The runtime/external cases (each verified against source)
1. **Tarball URLs and tool versions** for any `install <tool>`: come from the remote `package_info.dat` fetched per request — `path[split[0]] = split[1]` at `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:6606-6612`. So "what version of pythia8/lhapdf6 will I get?" / "what URL?" / "is tool X released yet?" all resolve here, not in source. (The `'xxx' in advertisements[name][0]` check at `:6683` — lowercase, FIRST citation ref — is the only source-side "Program not yet released" branch, but it is DORMANT in v3.7.1: no current built-in advertisement's first ref matches it. Don't claim it fires — re-check the built-in advertisements' first refs live before asserting it ever matches.)
2. **Update availability / build number**: `urllib.request.urlopen('http://madgraph.phys.ucl.ac.be/mg5amc3_build_nb')` at `:7230` — hardcoded UCL host, independent of `--source`. Whether an update exists is a runtime web answer.
3. **Patch contents** applied by `install update`: downloaded `.patch` text, applied via `patch -p1` (`apply_patch`, `:6995-7137`). What a given update changes is not in source.
4. **Plugin version bounds (min/max/validated)**: read off the plugin object's own attributes at `$MADGRAPH_INSTALL/madgraph/various/misc.py:2144-2146` (`obj.minimal_/maximal_/latest_validated_..._version`), which come from the plugin's `__init__.py` fetched at install. The *enforcement logic* is source (`:2153-2167`); the *bound values* are per-plugin/external.
5. **Whether a UFO model converts cleanly**: `do_convert_model` only patches `object_library.py`/`__init__.py` + drops in sm's `write_param_card.py`; success on the rest is model-specific and runtime — best-effort by design.

## Why a separate page
Each instance is also noted in its topic page's Gaps section; this page is the forward-looking *rule* that catches install questions none of those pages enumerate (e.g. version/URL of an arbitrary advanced tool → case 1). When an install answer feels un-findable in source, that is usually the signal it is a runtime/external value — locate where it actually lives and report the boundary rather than guessing.
