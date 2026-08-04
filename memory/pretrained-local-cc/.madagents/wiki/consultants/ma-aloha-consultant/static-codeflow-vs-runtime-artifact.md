---
description: Generalization — an ALOHA static code-flow fact (which tag/flag/branch fires) does NOT determine the runtime artifact (emitted routine name, the file SET in Source/DHELAS, a specific generated line); those are runtime instantiations — mark hypothesis and PROBE before asserting.
---

# Static code-flow fact vs runtime artifact (ALOHA)

Generalization over four instance cautions. The shared principle catches MORE than any one:
the boundary between what ALOHA source *determines* and what is only fixed at `output` time.

## The principle
Reading ALOHA source tells you **which code path fires** — which propagator/loop/conjugate/precision
tag is on a routine, which kernel branch and which writer the tag selects, which flag steers layout.
It does NOT by itself tell you the **concrete runtime artifact**:
- the **emitted routine/file NAME**,
- the **SET of files** in `<PROC_DIR>/Source/DHELAS/`,
- the **exact generated Fortran line**.

Each of those is a runtime instantiation of the code path, with at least one non-static degree of freedom.
Any claim of that form is a **runtime prediction → mark hypothesis and probe** (cheap `output`), never assert from reading.

This is the gate that fires for ANY future ALOHA "what file/name/line comes out" question, not just the four
documented instances. To predict the artifact, run a cheap `output` and read the directory.

## Why source alone cannot fix the artifact (source-grounded, v3.7.1)
Three named non-static degrees of freedom, all in `$MADGRAPH_INSTALL/aloha/aloha_writers.py`:
- **Name hashing.** `combine_name`'s nested `myHash` (`:1351`, def `:1354`) returns the literal name only
  if the target string is shorter than a length threshold (read the literal at `aloha_writers.py:1354`);
  else `'ALOHA_%s' % str(hash(target_string.lower()))`. A long combined-Lorentz
  name is HASHED → not literally predictable from the tag set.
- **Tag-order in the name.** `get_routine_name` (`:1324`) strips `MP` to an `MP_` prefix and moves the `P*`
  propagator tag to the END (`:1338-1341`) — the emitted name is a re-ordered transform of the raw tag list.
- **Inline-vs-separate FILE.** Whether a multiple-Lorentz combine yields an inline `add_combine` (no extra file)
  or a SEPARATE combined-routine file is `self.explicit_combine`, target-dependent (C++ always explicit
  `export_cpp.py:382`; Fortran inline unless a loop tag forces it `create_aloha.py:1011-1014`).
And the file SET also depends on runtime inputs the source doesn't pin: `wanted_lorentz` (which Lorentz are
needed), `outgoing == -1` expansion to one `P1N` file per leg (`create_aloha.py:991-996`).

## Probe evidence (grounds the runtime half)
`output u u~ > e+ e-` (SM, tree), inspected `Source/DHELAS/`:
- Names follow `<NAME>_<outgoing>`: `FFV1_0.f` (amplitude, outgoing 0), `FFV1P0_3.f` (P0 tag, off-shell leg 3),
  `FFV1P1N_1/2/3.f` (P1N hel-recycling, one file PER outgoing leg — the `-1` expansion), `FFV2_3`, `FFV4P1N_*`, `FFV5_3`.
- Propagator tag (`P0`,`P1N`) sits at the END of the name, exactly per `get_routine_name`'s reorder.
- No `ALOHA_<hash>` names here — expected: no combined name exceeded the `myHash` length threshold in this
  simple process (read the literal at `aloha_writers.py:1354` under `combine_name`, do not cache the number). The hash
  path is real in source but only triggers for long combined names (a different process is needed to see it surface).

## Instance pages (kept — each carries its specific caution)
- `helas-library-map.md` — `<PROC_DIR>` routine name ≠ classic HELAS `f*.F` filename 1:1 (combine_name hashing).
- `tag-routing-channel.md` — a tag SET does not map 1:1 to a predictable filename / file set.
- `compute-subset-production-path.md` — inline-combine vs explicit-combined FILE is a runtime `explicit_combine` consequence.
- `writer-lowering-mechanics.md` — the exact emitted `*.f` line is a runtime instantiation of the static packing convention.
