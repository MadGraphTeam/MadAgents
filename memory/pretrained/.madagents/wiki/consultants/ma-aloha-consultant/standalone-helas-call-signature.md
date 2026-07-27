---
description: External-wavefunction HELAS routine signatures (vxxxxx/ixxxxx/oxxxxx/sxxxxx) and the matrix.f ±IC(i) call pattern, plus how standalone (Fortran DHELAS) and standalone_cpp (HelAmps) package them. Verified v3.7.1 gg>ttx.
---

# Standalone external-wavefunction call signatures

External-wavefunction builders live in the ALOHA template `aloha_functions.f`
(`$MADGRAPH_INSTALL/aloha/template_files/aloha_functions.f`), copied verbatim into each
standalone package. ALOHA GENERATES the vertex routines (FFV1_*, VVV1P0_*); the external
wavefunction builders are fixed HELAS-legacy code shipped in the template.

## Signatures (aloha_functions.f, v3.7.1)
- `ixxxxx(p, fmass, nhel, nsf, fi)` (`:13`) — fermion wf, flowing-IN fermion number; out `fi(6)`.
- `oxxxxx(p, fmass, nhel, nsf, fo)` (`:273`) — fermion wf, flowing-OUT; out `fo(6)`.
- `vxxxxx(p, vmass, nhel, nsv, vc)` (`:798`) — vector wf; out `vc(6)`; nhel = -1,0,1 (0 forbidden if massless).
- `sxxxxx(p, nss, sc)` (`:570`) — scalar wf; **NO mass arg, NO nhel arg**; out `sc(3)`.
- **No external `fxxxxx`**: `f*` routines are off-shell fermion CURRENTS (internal/ALOHA-side), not
  external-leg builders. External fermion legs are only `ixxxxx` (flow-in) / `oxxxxx` (flow-out).

## The ±IC sign argument (nsf / nsv) — convention, not simply "incoming"
Doc-header conventions (aloha_functions.f):
- vector `nsv` (`:807`): **-1 for initial, +1 for final**.
- fermion `nsf` (`:22`,`ixxxxx`): **+1 for particle, -1 for anti-particle**.

Generated `matrix.f` pattern (probed via a `gg > t t~` standalone `output`; the external-leg
`CALL` block lives in `SubProcesses/P*/matrix.f` — exact line numbers are process-specific):
```
CALL VXXXXX(P(0,1),ZERO,  NHEL(1),-1*IC(1),W(1,1))   ! g  #1 initial  -> nsv=-1
CALL VXXXXX(P(0,2),ZERO,  NHEL(2),-1*IC(2),W(1,2))   ! g  #2 initial  -> nsv=-1
CALL OXXXXX(P(0,3),MDL_MT,NHEL(3),+1*IC(3),W(1,3))   ! t  #3 particle -> nsf=+1 (flow-out)
CALL IXXXXX(P(0,4),MDL_MT,NHEL(4),-1*IC(4),W(1,4))   ! t~ #4 antipart -> nsf=-1 (flow-in)
```
Args in order: momentum `P(0,i)`, mass, `NHEL(i)`, the `<sign>*IC(i)` flow/particle arg, output `W(1,i)`.
- The literal `<sign>` is BAKED AT GENERATION per external-leg role: it is the HELAS nsf/nsv
  convention (vector initial=-1/final=+1; fermion particle=+1/antiparticle=-1), NOT a plain
  incoming-vs-outgoing flip. "`-1*IC` for an incoming particle" is correct for the two initial
  gluons here but is an over-generalization: an outgoing antiparticle fermion also carries `-1*IC`.
- `IC(i)` is the runtime crossing/identical-particle-configuration vector; multiplying by it lets one
  matrix.f serve crossed/permuted helicity configs. It flips the baked sign per config.

## Packaging (both targets ship the same routine set, different language)
- **standalone** (`output standalone`): `Source/DHELAS/` holds `aloha_functions.f` (external
  builders ixxxxx/oxxxxx/vxxxxx/sxxxxx + boost/momentum utils) PLUS one file per ALOHA-generated
  vertex routine (`FFV1_0.f`, `FFV1_1.f`, `FFV1_2.f`, `VVV1P0_1.f` for gg>ttx) + `makefile`,
  `aloha_file.inc`. `matrix.f` (in `SubProcesses/P*/`) links against DHELAS.
- **standalone_cpp** (`output standalone_cpp`): `src/HelAmps_<model>.{h,cc}` (e.g. `HelAmps_sm.h/.cc`)
  concatenates the SAME external builders + generated vertex routines. C++ signature mirrors Fortran:
  `void vxxxxx(double p[4], double vmass, int nhel, int nsv, complex<double> vc[6])`;
  `sxxxxx(double p[4], int nss, complex<double> sc[3])` (no mass/nhel), etc. Momentum `p[4]` = p[0..3].

## Boundaries
- `SMATRIX`/`MATRIX`/`IDEN`/`DENOM`/helicity-sum math in matrix.f -> helas-amplitude slice.
- C++ `CPPProcess` class API (sigmaKin, the harness calling HelAmps) -> output slice.
- Which physics mode a given HELAS `f*.F` covers -> out-of-slice (library content fixed, pre-MG).
