---
description: HELAS Fortran library map ($MADGRAPH_INSTALL/HELAS) — file-naming convention and family inventory. ALOHA generates CALLS into this fixed, pre-MadGraph library.
---

# HELAS library map ($MADGRAPH_INSTALL/HELAS)

The install's HELAS version lives in `$MADGRAPH_INSTALL/HELAS/HELASVersion.txt` — read it, do not cache the value (version-specific). ALOHA generates routines that CALL into these; the library content is FIXED and predates MadGraph. (Which physics modes each `f*.F` covers is out-of-slice — this page is a structural map only.)

## Naming convention (HELAS legacy)
First letters encode the routine kind + particle legs:
- 1st char = output kind: `i`/`o` external fermion in/out wavefunction, `f` fermion-flow off-shell, `j` vector current (off-shell vector), `h` off-shell scalar, `u` off-shell tensor, `v`/`s`/`t` vector/scalar/tensor wavefunctions, `w` W-boson currents, `g` gluon vertices.
- middle = the legs entering the vertex (e.g. `fvi` fermion+vector→incoming-fermion, `iov` in-out fermion + vector amplitude, `vvv` triple-vector, `hvv` scalar from two vectors).
- trailing `x...x` = legacy padding; suffix variants: `c` charge-conjugate (Majorana) flow, `gld`/`gox` goldstino/gravitino, `kk`/`dmx`/`dm` KK/special, `2` alternate.

## Family inventory (install/version-specific — DERIVE by re-scan, never cache the counts)
The 3-letter-family counts over `$MADGRAPH_INSTALL/HELAS/*.F` (and the total `.F` count) are a FROZEN snapshot that rots — a past snapshot here shipped counts a live re-scan contradicted (see slate "snapshot-inventory-rots"). Do NOT store counts; read them fresh:
`ls $MADGRAPH_INSTALL/HELAS/*.F | sed -E 's/^(...).*/\1/' | sort | uniq -c | sort -rn`
Representative families present (names, not counts): `hvv`, `vvv`, `vvs`, `iov`, `jio`, `fvo`, `fvi`, `ios`, `sss`, `ggg`. Which families dominate is exactly the count question — re-scan.

## Utilities (not vertex routines)
- `boostx.F`, `boostm` (boost), `rotxxx.F` (rotation), `momntx.F`/`mom2cx.F`/`pxxxxx.F` (momentum setup) — see `aloha_functions.f` which inlines `ixxxxx`/`oxxxxx`/`vxxxxx`/`sxxxxx`/`txxxxx`/`irxxxx`/`orxxxx` (external-wavefunction builders) plus `CombineAmp`/`CombineAmpS` (`aloha_functions.f:2054`/`:2073`).

## ALOHA-side templates (`aloha/template_files/`)
- `aloha_functions.f` — the Fortran helper library copied per process (double precision); `aloha_functions_fd.f` (FD gauge), `aloha_functions_loop.f` (loop).
- `aloha_aux_functions.cc/.h`, `ixxxxx/oxxxxx/sxxxxx/txxxxx/vxxxxx.cc/.h`, `wavefunctions.py` — C++/Python wavefunction templates.
- `gpu/helas.cu`, `gpu/helas.h` — GPU templates. `Makefile_F`, `Makefile`/`Makefile.template`.
- The HELAS `lib/` dir is empty in a fresh install (built per process).

## Runtime placement
ALOHA-generated routines land in `<PROC_DIR>/Source/DHELAS/` (or `Source/`); `combine_name`/`get_routine_name` produce the call names matching this convention.

## Caution
The naming convention is HEURISTIC and HELAS-legacy; ALOHA-generated routine names follow `get_routine_name`/`combine_name` (aloha_writers.py) which may hash long combined names — do not assume a `<PROC_DIR>` routine name maps 1:1 to a classic HELAS filename. For "which f*.F covers which physics mode", redirect (out-of-slice: library content is fixed).
