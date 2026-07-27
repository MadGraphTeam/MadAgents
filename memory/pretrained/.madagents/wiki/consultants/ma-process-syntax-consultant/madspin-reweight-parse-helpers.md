---
description: Two process-line parse helpers in madgraph_interface.py used by MadSpin/reweight — split_process_line (staticmethod, strips [NLO]/@N/orders/filters to bare core) and get_final_part (recursive final-state pid extractor with decay-chain/()/{pol}/leading-digit handling).
---

# MadSpin/reweight process-line parse helpers (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`. Two parse helpers distinct from `extract_process` — they tokenize a process line for *downstream* tools, not to build a `ProcessDefinition`. In-slice (process-line tokenization), but separate code paths from `do_add`.

## split_process_line (staticmethod, 5466)
`@staticmethod def split_process_line(procline)` → returns `(core_process, options)`. Docstring: "[Used by MadSpin]". Callers: `reweight_interface.py:215` and `:1188` via `MadGraphCmd.split_process_line(process)`.
Strips, in order:
1. **`[...]` NLO tag** (5477-5481): `pos1=line.find("[")`; if `pos1>0` and a later `]` exists, excise `line[pos1:pos2+1]`. (NOTE `pos1>0` — a `[` at index 0 is NOT stripped.)
2. **`@N` process number** (5485-5489): SAME `proc_number_pattern = r"^(.+)@\s*(\d+)\s*(.*)$"` as extract_process (4844). This is a THIRD `@N`-strip site in the file (extract_process 4844, split_process_line 5486). Discards the number; keeps surrounding text.
3. **Option string start** (5491-5510): finds earliest position among an `order` match (`r"^(.+)\s+(\w+)\s*=\s*(\d+)\s*$"`), `/`, `$` (each must be at index `>0`). Everything from that position → `proc_option`; before → bare `line`.
Returns bare `line` + `proc_option`. Does NOT resolve particle names or build legs — pure string split.

## get_final_part (instance method, 5514)
`def get_final_part(self, procline)` → returns a `set` of final-state particle pdg ids. Docstring: "[Used by MadSpin]". Recursive over decay chains. Uses `self._curr_model.get('name2pdg')` (NOT `get_copy`/`get_particle`) for name→pdg.
- 5519 lowercases procline if `not model['case_sensitive']`.
- **Decay chain** (`',' in procline`, 5529): splits `core , decay`; recurses on core; parses each comma-separated decay respecting `()` nesting depth (5538-5557); for each decay removes the decayed mother pid from `core_final` and unions in the decay's own final states (5559-5568).
- **No decay chain** (5572): regex `r'> ([^\/\$\=\@>]*)(\[|\s\S+\=|\$|\/|\@|$)'` (5574) captures the final-state token block after `>`, stopping at `[ / $ @ =` or end. Per token:
  - `{pol}` block stripped via `particle.split('{')[0]` (5577-5578) — strips polarization before pid lookup.
  - name in `name2pdg` → add pid; in `_multiparticles` → union members; leading-digit (`particle[0].isdigit()`) → retry `particle[1:]` (the duplication-count strip, 5583-5587).

## CAUTIONS
- `get_final_part` returns a *set* of pids — loses multiplicity and leg order; it answers "which species are final" for MadSpin, not "how many legs".
- The no-decay regex 5574 keys on `> ` (space after arrow), so it relies on the caller passing a spaced line; it does NOT run extract_process's spacing-normalisation first.
- Both helpers re-implement `@N`/digit-strip/`{pol}`-strip independently of extract_process — a syntax change to the main parser does not automatically propagate here.
- `split_process_line` `[` strip requires `pos1>0`; this differs from extract_process which has no such index guard. Not probe-checked for an edge line starting with `[`.
