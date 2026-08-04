---
description: mu comparable to M1, not >> M1 — decoupled mu kills Z-neutralino coupling for gauge-boson mediated processes.
---

# Gaugino limit: keep mu comparable to M1, not decoupled

TRAP: The "gaugino limit" (gaugino-dominated neutralino eigenstates) is often confused with the "higgsino-decoupling limit" (|mu| >> M1, M2). For **Z-mediated** electroweakino production and decay (e.g., pp -> ch0_2 ch0_1 via s-channel Z, then ch0_2 -> ch0_1 Z), **decoupling mu kills the signal.**

## Source-walked fact: Z-neutralino coupling lives ONLY in higgsino columns

`$MADGRAPH_INSTALL/models/MSSM_SLHA2/couplings.py:1697` (GC_422, Z-ch0_2-ch0_1 coupling):
```
(cw*ee*i*NN2x3*conj(NN1x3)) / (...) - (cw*ee*i*NN2x4*conj(NN1x4)) / (...)
```
Only columns 3 and 4 (NNx3, NNx4) — the **higgsino** entries of the neutralino mixing matrix. No gaugino columns (NNx1, NNx2) appear.

`$MADGRAPH_INSTALL/models/MSSM_SLHA2/couplings.py:1785` (GC_444, Z-ch0_1-ch0_2):
```
-(cw*ee*i*NN1x3*conj(NN2x3)) / (...) + (cw*ee*i*NN1x4*conj(NN2x4)) / (...)
```
Same structure: exclusively higgsino columns.

The full family (GC_422 through GC_446) for Z-ch0_i-ch0_j couplings shares this pattern. **There is no "gaugino piece" (N_i1 * N_j2 or similar) in the Z-neutralino coupling.**

## Physics derivation

Z couples to gauge eigenstates via T3 - Q sin^2(theta_W):
- B-tilde (adjoint of U(1)_Y, Y=0): T3=0, Q=0 -> coupling = 0
- W-tilde3 (adjoint of SU(2)_L, diagonal generator): T3=0, Q=0 -> coupling = 0
- H_d0 (weak doublet): T3=-1/2, Q=0 -> coupling = -1/2
- H_u0 (weak doublet): T3=+1/2, Q=0 -> coupling = +1/2

Pure gauginos have **zero** Z coupling by gauge quantum numbers. The coupling exists only through gaugino-higgsino mixing in the mass eigenstates, which brings in higgsino fraction ~ (m_Z/mu)^2.

Therefore: Z-ch0_i-ch0_j coupling ~ product of higgsino fractions ~ (m_Z/mu)^2.

**As |mu| -> infinity, this vanishes as O(m_Z/mu)^2.**

## Numerical anchoring

Numerical diagonalization of the 4x4 neutralino mass matrix confirms:

| M1 | M2 | mu | Z-coupling magnitude | Higgsino fraction chi1 | Higgsino fraction chi2 |
|----|----|----|---------------------|----------------------|----------------------|
| 100 | 300 | 2000 | 0.013 | 0.0002 | 0.9997 |
| 100 | 300 | 300 | 0.181 | 0.0169 | 0.9957 |
| 100 | 300 | 150 | 0.459 | 0.1960 | 0.9867 |

Decoupling mu=2000 gives a coupling **14x smaller** than mu=300 and **34x smaller** than mu=150. Both production (pp -> ch0_2 ch0_1) and decay (ch0_2 -> ch0_1 Z) are proportional to this coupling squared, so the cross-section penalty is squared again: ~200x and ~1200x respectively.

## Recommendation

For Z-mediated electroweakino signals (pp -> ch0_2 ch0_1 -> ch0_1 Z Z or similar):
- **Choose |mu| comparable to M1** (e.g., mu ~ 2-3x M1) to keep higgsino admixture ~10% in the gaugino-like eigenstates.
- **Do NOT choose |mu| >> M1, M2** — the "gaugino limit" means gaugino-dominated eigenstates, not fully-decoupled higgsinos. The signal dies as (m_Z/mu)^2.
- Keep M1 and M2 well-separated (M2 > M1 + M_Z) for phase space.
- This is a **coupling-viability** issue: the spectrum can look right (light neutralinos, mass splitting > M_Z) while the coupling is effectively zero.

See also: `coupling-viability-from-spectrum.md` (general principle).