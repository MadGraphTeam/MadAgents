---
description: RAMBO flat/democratic phase-space generator (rambo.py) — used by the standalone `check` command, NOT by integration; contrast with single-diagram-enhanced genps.f.
---

# RAMBO: the flat phase-space generator (off the integration path)

`$MADGRAPH_INSTALL/madgraph/various/rambo.py`. `RAMBO(N, ET, XM)` (rambo.py:57) is the
Ellis-Kleiss-Stirling **democratic** generator: it produces N final-state 4-momenta uniformly
("flatly") in massless phase space, then rescales for masses. Crucially it has **no propagator
structure** — no BW peaks, no t-channel mapping, no channel selection. It is the conceptual opposite
of the single-diagram-enhanced `genps.f` path that the rest of my slice owns.

## What it computes (rambo.py:57-223)
1. **Massless momenta in infinite phase space** (124-136): for each particle draw `c=2r-1`
   (cos theta), azimuth `f=2pi*r`, and energy `Q4 = -log(r1*r2)` (so energies are exponentially
   distributed); build a massless 4-vector `Q`.
2. **Conformal boost to fixed CM energy ET** (138-155): sum the `Q`'s, compute the invariant mass
   `rmas`, boost+scale all momenta so the total is `(ET,0,0,0)`. Output `P` are massless momenta
   summing to ET.
3. **Massless weight** (158-160): `wt = (2N-4)*log(ET) + Z[N]`, where `Z[N]` is the precomputed
   log-factorial phase-space volume constant (rambo.py:104-105). For `N==2`, `wt=po2log`.
4. **Massive rescale** (174-203): if any mass is nonzero, Newton-iterate (max `itmax=6`,
   rambo.py:76) a scale `x` so the massive energies sum to ET, then set `P(4,i)=E[i]`.
5. **Mass-effect weight** (205-214): multiply in `wtm = (2N-3)*log(x)+log(wt2/wt3*ET)`.

Returns `(P, wt)` — momenta and the **log** event weight (Kuijf's logarithmic-weight adjustment,
rambo.py:64). Underflow/overflow warnings if `wt<-180` or `wt>174` (rambo.py:161-166, 215-220).

`random_nb` (rambo.py:225) is a uniform draw floored at 1e-16 (avoids log(0)).

## Where it is actually used — the `check` command, not integration
The only Python callers are in `$MADGRAPH_INSTALL/madgraph/various/process_checks.py`:
- `process_checks.py:476` (1 incoming) and `:509` (2 incoming) call `rambo.RAMBO(nfinal, energy, masses)`
  to generate a random kinematic point for **matrix-element checks** (gauge invariance, Lorentz
  invariance, permutation symmetry — the `mg5> check` command).
- The caller reorders RAMBO's `(px,py,pz,E)` layout into MadGraph's `(E,px,py,pz)` convention
  (process_checks.py:478-481, 511-515) and prepends the incoming-particle momenta.
- `XM` must be a `rambo.FortranList` (1-indexed, rambo.py:94-96, asserted); incoming legs are set
  by the caller, not by RAMBO (RAMBO only does the `nfinal` final-state momenta).

## Cautions / boundaries
- **RAMBO is NOT on the event-generation / integration path.** Integration uses the
  diagram-aware `genps.f` (`x_to_f_arg` -> `gen_mom` -> `one_tree`) with set_peaks BW/collinear/soft
  mappings. A claim that "MadGraph integrates with RAMBO" is wrong for the LO MadEvent path — RAMBO is
  the standalone-check generator. (The only Fortran that *calls* a rambo-style flat generator under
  `Template/` is the NLO check code — `Template/NLO/SubProcesses/check_sudakov.f`,
  `check_sudakov_angle2.f`, `check_poles.f` — for Sudakov/pole checks, not LO integration. No file
  *named* `rambo*` lives under `Template/`; the standalone Fortran `rambo.f` is under
  `vendor/CutTools/examples/`. LO integration never touches any of these.)
- The flat weight has no importance sampling: RAMBO is fine for a uniform validity check but would be
  catastrophically inefficient for a resonant integrand — which is exactly why the integration path
  uses single-diagram enhancement instead.
- `1 < N < 101` is asserted (rambo.py:108); energy sufficiency `sum|m| <= ET` raises `RAMBOError`
  (rambo.py:118-119).
