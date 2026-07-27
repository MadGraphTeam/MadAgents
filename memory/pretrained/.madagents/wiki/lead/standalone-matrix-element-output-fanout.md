---
description: You want the matrix element itself, evaluated outside MadGraph (MEM, custom integrator, reweighting), not events.
---

# Standalone matrix-element output — fan-out

`output standalone <dir>` (Fortran) and `output standalone_cpp <dir>` (C++) build a
minimal package that evaluates |M|² only — no integration, no PDFs, no αs running,
no run_card. It is chosen at the `do_output` layer but its *contents* (the entry
points, the averaging factors, the color structure, the HELAS calls, the loop
case) are owned by different slices. Route each sub-question to its owner.

## Sub-question → owning slice

| Sub-question | Owning consultant | Notes |
|---|---|---|
| Which exporter runs for `standalone` / `standalone_cpp`; directory layout (`Cards/`, `Source/{MODEL,DHELAS}`, `SubProcesses/P<N>_...`, `src/`, `lib/`); `P<N>_<name>` naming + `@N`→`P<N>`; f2py wrapper targets; `--prefix=int`; C++ `CPPProcess` API; standalone caveats (no αs/PDF/run_card) | `ma-output-consultant` | `ProcessExporterFortranSA`/`ProcessExporterCPP`, `export_v4.py`; `matrix2py`/`all_matrix2py` |
| `SMATRIX(P,ANS)` vs `MATRIX(P,NHEL,IC)` entry points; IDEN averaging; DENOM *consumption* in the color loop; where the ±IC flow toggle feeds the MATRIX function | `ma-helas-amplitude-consultant` | `matrix.f` SMATRIX/MATRIX; `get_denominator_factor` |
| CF color matrix + DENOM *derivation* (rational color coefficients cleared to integer common denominator) | `ma-color-decomposition-consultant` | `color_amp.py get_line_denominators/numerators`; write-side packing in `export_v4.py` is a seam |
| HELAS/HelAmps external-wavefunction call signatures (`VXXXXX`/`IXXXXX`/`OXXXXX`/`SXXXXX`), the `Source/DHELAS/` lib, C++ `HelAmps_<model>` | `ma-aloha-consultant` | `aloha_functions.f`; the ±IC sign is the nsf/nsv convention |
| MadLoop `[virt=…]` standalone: `ML5_<N>_SLOOPMATRIX`, RESULT layout, `MadLoop5_resources/`, `SETMADLOOPPATH`, `OLP_static` | `ma-madloop-consultant` | `loop_exporters.py`, `loop_matrix_standalone.inc`; `[virt=…]` bracket *parse* is nlo-syntax |
| Flux factor / averaging as physics (is `1/(2ŝ)` right, are the 1/8·1/3·1/2·1/n! factors correct) | `ma-physics-consultant` | massless-initial-only caveat |

## Anticipated traps (doc-myths — source truth is INVERTED from common write-ups)

- **"the default `make` in a standalone subprocess dir builds the python wrapper; use `make check` for the executable"** — BACKWARDS. The per-P `makefile`'s first/default rule builds the **`check` executable** (`PROG=check`); the f2py `.so` is a *separate named target* (`make matrix2py.so`, or `all_matrix2py.so` via `--prefix`). → `ma-output-consultant` (`sa-make-default-target`).
- **"for `[virt=QCD]` standalone, `output` compiles everything and `launch` is not needed/supported"** — INVERTED. `output`/`ML5finalize` writes source only (NO compile); `launch` IS explicitly supported for standalone ML5 and is the built-in compile+evaluate path (else `make` manually). → `ma-madloop-consultant` (`output-writes-launch-compiles`).
- **IDEN vs DENOM conflated** — two unrelated denominators at different levels. IDEN (SMATRIX-level) = initial-state color-avg × helicity-avg × final-state 1/n! symmetry, all folded into one integer. DENOM (MATRIX-level) = the color-matrix common denominator only. Discriminator: `uu~>ttx` has DENOM=1 while its color-averaging (9) sits in IDEN=36; `gg>ttx` DENOM=3. → helas (`iden-vs-denom-two-different-denominators`) + color.
- **"the generated CF is a full symmetric `CF(j,i)` matrix"** — no (standard symmetric-basis case). It is stored **packed upper-triangular** (`CF(NCOLOR*(NCOLOR+1)/2)`) with off-diagonal entries **pre-doubled at write time**, so a single-count `J=I,NCOLOR` loop reproduces the full double sum. A 2-D `CF(i,j)` is emitted only for the asymmetric/loop branch. → color + helas.
- **"the flow-direction argument is `-1*IC` because the leg is incoming"** — imprecise. The baked sign is the HELAS **nsf/nsv convention** (vector: initial −1 / final +1; fermion: particle +1 / antiparticle −1). An *outgoing antiparticle* also carries `−1*IC`. `IC(i)` is the runtime crossing toggle. → `ma-aloha-consultant` (`extwf-sign-is-nsf-nsv-not-inout`).
- **"σ = (1/2ŝ)∫SMATRIX dΦ works for any initial state"** — massless-initial only. Massive incoming legs need F = 4√((p₁·p₂)²−m₁²m₂²) ≠ 2ŝ. SMATRIX already carries IDEN (incl. the 1/n!), so the user must NOT re-apply averaging/symmetry — supply only flux×dΦ. → physics.

## IDEN reference (generation-grounded, sm)

`gg>ttx`=256 (64·4·1), `gg>gg`=512 (64·4·2!), `uu~>ttx`=36 (9·4·1), `e+e->ttx`=4 (1·4·1). Antiquark color contributes +3 (not −3) to the color_factor product.

## Dispatch note

For "verify/build a standalone |M|² setup", fan out one focused question per present
concern (layout+wrappers → output; entry-points+IDEN → helas; CF/DENOM → color; HELAS
calls → aloha; loop → madloop; flux/averaging physics → physics). The two inverted
doc-myths (`make` default target; `output` vs `launch` for loops) are the highest-value
catches — they read as authoritative in hand-written guides but are backwards in source.
Detailed source facts live in the consultant subtrees; dispatch, don't restate.
