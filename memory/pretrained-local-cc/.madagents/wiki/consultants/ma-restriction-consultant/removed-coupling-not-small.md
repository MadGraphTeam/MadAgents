---
description: Zero coupling in a restrict card removes the vertex entirely (not "small") — e/mu/c Yukawas pruned, b/t/tau kept; a process relying only on a removed vertex yields zero diagrams (models/sm + import_ufo.py v3.7.1)
---

# Removed coupling ≠ small coupling

A coupling that is zero in the restrictive param_card is not "small" — it is **removed entirely** from the in-memory model at import time. The vertex does not exist for process generation. A process whose only diagrams use that vertex produces **zero diagrams**, not a small cross-section.

## Source-walked facts

**`models/sm/restrict_default.dat`, YUKAWA block:**
- `yme = 0.0` (PDG 11, electron)
- `ymm = 0.0` (PDG 13, muon)
- `ymc = 0.0` (PDG 4, charm)
- `ymb` (PDG 5, bottom) — nonzero, KEPT
- `ymt` (PDG 6, top) — nonzero, KEPT
- `ymtau` (PDG 15, tau) — nonzero, KEPT

**`models/sm/parameters.py:349-383` — internal parameter chain:**
- `ye = (yme * sqrt(2))/vev` → 0
- `ym = (ymm * sqrt(2))/vev` → 0
- `yc = (ymc * sqrt(2))/vev` → 0
- `yb = (ymb * sqrt(2))/vev` → nonzero
- `yt = (ymt * sqrt(2))/vev` → nonzero
- `ytau = (ymtau * sqrt(2))/vev` → nonzero

**`models/sm/couplings.py:340-406` — coupling values:**
- `GC_89 = -(i*ye)/sqrt(2)` → 0 (e+ e- H)
- `GC_93 = -(i*ym)/sqrt(2)` → 0 (mu+ mu- H)
- `GC_84 = -(i*yc)/sqrt(2)` → 0 (c~ c H)
- `GC_83 = -(i*yb)/sqrt(2)` → nonzero (b~ b H)
- `GC_94 = -(i*yt)/sqrt(2)` → nonzero (t~ t H)
- `GC_99 = -(i*ytau)/sqrt(2)` → nonzero (ta+ ta- H)

**`models/sm/vertices.py:630-646` — H-fermion vertices:**
- V_104: `e+ e- H` → GC_89 → **PRUNED**
- V_105: `mu+ mu- H` → GC_93 → **PRUNED**
- V_106: `ta+ ta- H` → GC_99 → **KEPT**
- V_78 (line 474): `b~ b H` → GC_83 → **KEPT**
- V_140 (line 846): `c~ c H` → GC_84 → **PRUNED**
- V_141 (line 852): `t~ t H` → GC_94 → **KEPT**

**`models/sm/vertices.py:612-628, 876-892` — Goldstone-fermion vertices (same pruning):**
- V_101: `e+ e- G0` → GC_88 (ye) → **PRUNED**
- V_102: `mu+ mu- G0` → GC_92 (ym) → **PRUNED**
- V_103: `ta+ ta- G0` → GC_98 (ytau) → **KEPT**
- V_145: `e+ ve W-` → GC_86 (ye) → **PRUNED**
- V_146: `mu+ vm W-` → GC_90 (ym) → **PRUNED**
- V_147: `ta+ vt W-` → GC_96 (ytau) → **KEPT**

**`models/import_ufo.py:2549-2550` — zero detection:**
```python
if value == 0:
    zero_coupling.append(name)
```

**`models/import_ufo.py:2924-2927` — interaction removal:**
```python
if not vertex['couplings']:
    self['interactions'].remove(vertex)
```

## Implications

**DIRECT:** `import model sm` (SM restrict_default.dat) zeros electron, muon, and charm Yukawas. All vertices using those Yukawa couplings — both H-ff and G0-ff and the charged-current W-ff' vertices — are removed from the in-memory model. The UFO still declares them; they simply do not exist post-restriction.

**DIRECT:** Only bottom, top, and tau retain non-zero Yukawas in the SM restriction. H-b-b, H-t-t, H-tau-tau, and their Goldstone counterparts survive. H-e-e, H-mu-mu, H-c-c, and the e/mu W couplings are gone.

**INFERRED:** If a process like `p p > e+ e-` has zero diagrams, the UFO declares the vertex but restrict_default has pruned it (via the γ/Z/e+e- vertex itself not being Yukawa-dependent — check whether it is actually the H-mediated diagram, or some other topology, that is zero). More typically: `p p > h, h > e+ e-` produces zero diagrams because V_104 (e+ e- H) was pruned by restrict_default.

**INFERRED:** The SM restrict_default's choice of massless e/μ/c vs massive b/t/tau is motivated by computational cost (top-quark loops in gg→H dominate; bottom loops are next-leading; light-fermion loops are negligible). But the pruning is structural: zero-coupling vertices are deleted, not suppressed. A user who needs e+e- final states from Higgs must use a non-default restriction (or a BSM model that does not zero these Yukawas).

**HYPOTHESIS:** Other models ship different restrict cards with different zero-patterns. Always read the actual `restrict_*.dat` for the model in question rather than assuming the SM pattern applies.

## Diagnosing "zero diagrams" after `import model <name>`

When a process produces zero diagrams, check the restriction before checking the process syntax:

1. Identify which vertex the missing diagrams would use.
2. Check the restrict card's YUKAWA (or equivalent) block — is the relevant coupling zeroed?
3. Verify the coupling → internal parameter → vertex chain in the UFO files.
4. If the coupling is zeroed, the fix is **model-load-time**: use a different restrict card or load without restriction. A post-load `set` command cannot resurrect a removed vertex.

## Fermions pruned by SM restrict_default.dat

| PDG | Fermion | YUKAWA value | H-vertex | G0-vertex | W-vertex |
|-----|---------|-------------|----------|-----------|----------|
| 11 | e | 0.0 | PRUNED (V_104) | PRUNED (V_101) | PRUNED (V_145) |
| 13 | μ | 0.0 | PRUNED (V_105) | PRUNED (V_102) | PRUNED (V_146) |
| 4 | c | 0.0 | PRUNED (V_140) | — | — |
| 5 | b | nonzero | KEPT (V_78) | — | — |
| 6 | t | nonzero | KEPT (V_141) | — | — |
| 15 | τ | nonzero | KEPT (V_106) | KEPT (V_103) | KEPT (V_147) |

Notes: sfermion vertices (c~ c H, t~ t H) follow the same Yukawa chain. SM does not declare slepton vertices, so no stau/stau-H pruning to report here.