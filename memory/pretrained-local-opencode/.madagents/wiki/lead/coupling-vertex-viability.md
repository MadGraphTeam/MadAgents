---
description: The signal needs a vertex/coupling alive in THIS model at THIS benchmark, or you must name which vertex carries it.
---

# Coupling / vertex viability — a clean run is not evidence the needed coupling is alive

This page is dispatch behaviour — the facts live in the cited consultant pages, not here. It covers three shapes: explicit coupling-zero + no-viable-channel + BSM names (HVT fermiophobic Z′); derived coupling-zero + BSM names (MSSM decoupled-μ neutralinos); and vertex identification + framing (pp→WWZ self-coupling).

## The unifying lead principle

A process/signal needs a specific coupling/vertex to be (1) **present** in the loaded model, (2) **non-zero** at the chosen benchmark — including a coupling *derived* from the benchmark, never set directly — and (3) **applicable** to the topology (right legs, right framing). **MG5 checks NONE of these against your intent and runs clean regardless.** The diagnostic is never "it generated / it ran / it gave a σ" — it is the **σ magnitude / partial width / BR**, compared against a consistent baseline.

The **diagram count discriminates the two failure families:**
- count UNCHANGED + σ collapse → vertex present, the *benchmark zeroed the coupling value* (this page). Enumeration keys off vertex presence, blind to coupling value → `../consultants/ma-diagram-enumeration-consultant/vertex-presence-not-value-enumeration.md`.
- count DROPS (or NoDiagramException / silent multiparticle drop) → the *model removed the coupling* (restrict_default) → `removed-coupling-not-small.md`.

So "I zeroed a coupling but get the same diagrams" is **expected and correct** — point the user at integration-time σ, not the diagram count. A *changed* count after a "set to zero" attempt means they actually hit a model restriction, not a value set.

## Five faces (route by which one fired)

| face | shape | owning page |
|---|---|---|
| **explicit coupling-zero** | user sets an external coupling to 0 (HVT fermiophobic `cq=0`); vertex stays, σ collapses ~3400×. A non-zero *mixing remnant* survives — not a clean 0 | ufo `ufo-vertex-presence-vs-coupling-value.md` |
| **derived coupling-zero** | spectrum params derive a zero coupling never set directly (MSSM decoupled-μ → higgsino→0 → Zχ̃χ̃ ∝ (N_i3N_j3−N_i4N_j4)→0); ONE vertex drives production + decay → both legs move together | physics `coupling-viability-from-spectrum.md`; artifact = partial width: madwidth `compute-widths-as-coupling-viability-check.md`; NMIX is card-read & never recomputed: param-card `mssm-slha2-mixing-matrix-stale.md` |
| **no-viable-channel** | every alternative production mode is *also* suppressed → the benchmark itself is a dead end (HVT fermiophobic: VBF/Vh 860×–50000× below DY). Switching mode is NOT a fix | physics `coupling-viability-from-spectrum.md` |
| **vertex identification + framing** | name the *present SM* vertex; rule out absent (ZZZ/Zγγ — never in `sm`), inapplicable (WWWW — leg-counting), mis-framed (aTGC/dim-6 — a deviation ON TOP, not the SM vertex), false-attribution (QCD: gg-zero-tree; photon-PDF: default `p` has no `a`) | ufo (inventory) + diagram-enum (gg-zero, leg-count) + eft `eft-model-content-wilson-coupling-vertex.md` + model-loader `process-model-and-multiparticle-defaults.md` |
| **BSM particle names** | guessed names (zp/Zprime/V0; chi20/neutralino2) → hard `InvalidCmd: No particle X in model` pre-generation; resolution is case-insensitive *per-model* (gated on `case_sensitive=False`, NOT universal) | process-syntax `particle-name-resolution.md` |

## Dispatch sequence

1. **Identify the needed coupling/vertex** from the signal (which vertex carries the production graph AND/OR the decay). For a cascade the SAME coupling often drives both (MSSM Zχ̃χ̃) — they cannot be tuned independently.
2. **ufo** — is the vertex present in `vertices.py`? (Absent ⇒ wrong model, never a param-card fix.) Is its coupling an external settable parameter or derived from one?
3. **For a value the benchmark could zero — route the CHECK, not a blessed value:**
   - production coupling → σ-magnitude vs a consistent baseline;
   - decay vertex → **madwidth** `compute_widths` partial width + BR — the discriminating artifact. A microscopic partial width / BR≈0 is the silent-fail fingerprint; no MG5 check flags it for a colorless particle.
4. **For a derived coupling (mixing matrix):** **param-card** — NMIX/UMIX/VMIX (and SUSY masses) are external card-read blocks MG5 never recomputes from EXTPAR; the user must supply a *consistent* mixing matrix from an external diagonalizer. Sharper than stale-width: there is **no in-tool diagonalizer** (`compute_widths`/`Auto` cannot fix it).
5. **For vertex-ID questions:** ufo inventory + diagram-enum (leg-counting / gg-zero) + eft (SM-vs-dim-6 framing) + model-loader (default-`p`-no-photon).
6. **process-syntax** — confirm BSM names came from `display particles` / `particles.py`, not PDG/paper guesses.
7. **physics** — the spectrum→coupling judgment and the no-viable-channel call (the load-bearing first-principles claims; both APPROVED).

## Anticipated traps (behavioural shape)

- **"fermiophobic is physically motivated" + bare `p p > vz`** — silent ~3400× σ collapse, run clean. The motivation is fine; the error is leaving the DY command needing cq while cq=0.
- **"diagnose cq=0, fix with VBF/associated"** — the subtler trap; still 860×–50000× too small (V-boson couplings mixing-suppressed). NO benchmark rescues fermiophobic in this UFO. → physics no-viable-channel.
- **"decoupled-μ pure-gaugino gives exactly the requested masses"** — silent ~2400× partial-width collapse; masses right, derived Zχ̃χ̃ ≈0. → madwidth + physics.
- **"WWZ is anomalous TGC / dim-6 / SMEFT"** — category error: SM WWZ is dim-4 in default `sm`; aTGC is a deviation on top (needs a SMEFT UFO + NP order). → eft.
- **"WWWW quartic / QCD gluon-fusion / photon-PDF is the missing piece"** — WWWW can't attach (2 W legs); gg→WWZ has zero tree diagrams; default `p` has no photon. → diagram-enum + model-loader.
- **"names the topology, never the vertex"** — when the prompt asks for the vertex, "Z radiates off W" without "WWZ / TGC / non-abelian self-coupling" misses the point.
- **guessed BSM particle name** — hard `InvalidCmd`, never silent. → process-syntax.

## Physics caveats the playbook must carry (ma-physics-consultant, both judgments APPROVED with WARNINGs)
- **MSSM second zero:** decoupled-μ is NOT the only way Zχ̃₂χ̃₁ vanishes — M₁≈M₂ (bino-wino near-degenerate) suppresses it regardless of μ. The robust invariant is the m_Z²/μ² product-of-admixtures scaling; operative guidance: require **both** μ comparable to M₁,M₂ **and** |M₁−M₂| ≫ m_Z.
- **HVT no-channel is multi-TeV-specific:** the V-gauge mixing θ~m_W²/M_V² weakens at low M_V, so the 864×/48400× VBF/Vh hierarchy does NOT generalize to a sub-TeV vector (cq≠0 is still the fix; just don't quote the hierarchy off-regime). A large cH does not rescue it (needs cH~29× → non-perturbative / EWPT-excluded).

## Relation to neighbours
- **`clean-run-not-correct-physics.md`** — the family umbrella: this page is the *benchmark-zeroed-coupling* member of the silent-physics-wrong family; the umbrella carries the family-wide diagnostic menu and route-by-symptom table. The diagram-count discriminator below has its named diagnostic home at diagram-enum `../consultants/ma-diagram-enumeration-consultant/enumeration-topology-fingerprint.md`.
- **`removed-coupling-not-small.md`** — the *model-removed* family (restrict_default deletes the vertex → diagram count CHANGES; fix is model-load-time). This page is the *benchmark-zeroed* family (vertex present → count UNCHANGED; fix is benchmark-choice-time, or recognize no viable benchmark exists). The diagram count is the bridge.
- **`derived-quantity-staleness.md`** — NMIX is the sharpest instance (a mathematically-derived value supplied as an independent external input, never reconciled to EXTPAR).
- **`process-line-scope-traps.md`** — the silent-wrong-ME sibling for *topology* (right final state, wrong diagrams). This page is the silent-wrong-σ sibling for *couplings* (right diagrams, dead coupling).
- **`param-card-setup-fanout.md` / `model-content-lifecycle.md`** — the value/content lifecycle axes this draws on.
