---
description: The `--diagram_filter` CLI flag on generate/add process — parsed by an UNANCHORED args.remove in do_add (3246-3249) BEFORE extract_process, so it is position-INDEPENDENT (works mid-line before a decay chain). Placement only matters via TOKENIZATION: glued to an adjacent char (e.g. `--diagram_filter,`) the membership test misses it and the fragment falls through to particle-name resolution → "No particle --diagram_filter in model". The flag alone sets a bool; actual filtering needs PLUGIN/user_filter.py:remove_diag (diagram-enumeration slice). v3.7.1, probe-confirmed sm.
---

# `--diagram_filter` flag: parse, placement, and the "No particle" trap (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` `do_add` (3232). The flag does NOT have to appear at the very end of the process line; the "No particle --diagram_filter in model" error is a tokenization failure, not a placement rule (see below).

## How the flag is parsed (do_add 3246-3249)
```
diagram_filter = False
if '--diagram_filter' in args:      # 3247  UNANCHORED membership test
    diagram_filter = True
    args.remove('--diagram_filter')  # 3249  removes the token wherever it sits
```
- `args = self.split_arg(line)` (3238) — split_arg tokenizes on WHITESPACE only (quote-aware). So `--diagram_filter` matches iff it is a **standalone whitespace-delimited token**.
- Runs BEFORE `check_add` (3257) and BEFORE `extract_process` (3310) / `extract_decay_chain_process` (3292). The bool flows into `MultiProcess(myprocdef, ..., diagram_filter=diagram_filter)` (3368-3371).
- Sibling `--` flags stripped the same way, same lines: `--no_warning=duplicate` (3242-3244), `--standalone` (3252-3254); `--optimize` is END-anchored (`args[-1].startswith('--optimize')`, 3264) — the ONLY one that is positional.

## PLACEMENT: position-INDEPENDENT, tokenization-dependent
`args.remove(...)` is unanchored → the flag is stripped from ANY position, INCLUDING mid-line before a decay chain. Placing it at the end (with a space) merely guarantees a clean token; end placement is not an enforced rule. The real rule: **the flag must be a standalone whitespace-delimited token.**

Probe-confirmed (v3.7.1 sm):
| input | outcome |
|---|---|
| `p p > z z --diagram_filter , z > mu+ mu-` (space-delimited, BEFORE chain) | flag stripped → reaches `remove_diag` plugin requirement (CASE1) — WORKS, refutes "must be at end" |
| `p p > z z, z > mu+ mu- --diagram_filter` (end, after chain) | flag stripped → same plugin requirement |
| `p p > e+ e- --diagram_filter` (end, simple) | flag stripped → same plugin requirement |
| `p p > z z --diagram_filter, z > mu+ mu-` (**glued to comma**, no space) | token is `--diagram_filter,` != `--diagram_filter` → membership MISSES → after comma-split `--diagram_filter` becomes a LEG token → **`InvalidCmd: No particle --diagram_filter in model`** |

So the "No particle --diagram_filter in model" error is a GLUING failure, not a POSITION failure: a naive `--diagram_filter,` (comma with no preceding space) leaves the token un-normalised (space_before tag-set at 4836 has `,` but requires `\S` on BOTH sides; a trailing space after the comma blocks insertion), so the fragment survives into extract_process's leg loop → raise at **5242** (see loud-parse-rejection-traps.md, particle-name-resolution.md). Same message string, same fall-through-to-name-resolution family.

## The flag alone does NOTHING without a plugin (premise — diagram-enumeration slice)
Setting `diagram_filter=True` only arms the hook. The actual filtering is `apply_user_filter` (`core/diagram_generation.py:904`), which `misc.plugin_import('user_filter', ...)` (909-911) — REQUIRES `PLUGIN/user_filter.py` defining `remove_diag(ONEDIAG)`. Without it, generation ERRORS: `"user filter required to be defined in PLUGIN/user_filter.py with the function remove_diag(ONEDIAG)..."` (probe-confirmed for all three working cases above). So `--diagram_filter` is NOT a self-contained operator like `/ $ $$ > >`; it is a user-plugin gate.

## Claim 4 — the "removed N diagrams" WARNING is enumeration-side, NOT parser-side
`logger.warning('Diagram filter is ON and removed %s diagrams for this subprocess.' % nb_removed)` at **`core/diagram_generation.py:933`**, inside `apply_user_filter` (904-933, called from 811). This is the diagram-enumeration slice, NOT interface/parser. The parser's only role is the bool at do_add:3246-3249.

## Relation to `/ $ $$ > >`
Those diagram-FILTER operators (diagram-filter slice) are parsed INSIDE extract_process (peeled at 5007-5019 etc.) and set `forbidden_*`/`required_schannels`. `--diagram_filter` is a completely SEPARATE mechanism: a CLI bool stripped in do_add before extract_process, consumed by a Python plugin at enumeration time. Do not conflate them.
