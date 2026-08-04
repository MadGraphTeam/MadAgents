---
description: A vertex's presence in the loaded model comes from vertices.py and is independent of the param-card VALUE of its coupling; a coupling set to zero leaves the vertex present (diagrams generate, amplitude→0); a vertex not declared in vertices.py can never enter any diagram regardless of couplings. Model-content half of coupling/vertex viability.
---

# UFO vertex presence vs coupling param-card value (v3.7.1)

The model-content half of the "coupling/vertex viability" class (sibling of the lead's `removed-coupling-not-small`, which is the restriction-REMOVAL story). The deeper principle behind this page — the loader keys content on value STRINGS, not on evaluated numbers — is `ufo-loader-keys-on-value-strings-not-numbers.md`; this page is its concrete model-content instance. One principle, three legs, all source-grounded:

**A vertex's PRESENCE in the loaded model is set by `vertices.py`; it does NOT depend on the param-card VALUE of its coupling.**

1. **Set-to-zero ≠ removed.** A param-card value that drives a coupling to 0 leaves the `Vertex` in `vertices.py` untouched, the coupling object present, the interaction in the loaded model, and diagrams still generated — only the *amplitude* collapses (→0 or to the residual term). Contrast `restrict_default`, which DELETES the parameter+coupling+vertex (RestrictModel, restriction slice).
2. **Undeclared vertex = never.** A vertex not declared in `vertices.py` (e.g. ZZZ in default sm) can never enter any diagram regardless of any coupling value — there is no object to carry an amplitude.

Why the loader does NOT drop a zero-VALUED coupling at load: `optimise_interaction`'s ZERO/identical-collapse (`import_ufo.py:686`, see `ufo-vertex-to-interaction-conversion.md`) keys on the **literal source value STRING** `str(coupling.value)`, dropping only couplings whose string is literally `'0'`. A coupling whose `value` is an expression like `'(cN*cq*complex(0,1)*gw**2)/(2.*gst) + ...'` is NOT the string `'0'`, so it survives the loader no matter what `cq` evaluates to. The param_card value is read FAR LATER (numerical evaluation), well after vertex membership is fixed. So a runtime-zero coupling rides into the loaded model as a live interaction.

## Leg 1 — HVT: external `cq` drives GC_90 but does not gate the vertex

Model `$MADGRAPH_INSTALL/models/HVT` — an oscillating BSM model NOT in the fixed shipped core (`ls models/HVT/` to confirm presence; absent → fetch/install first). All GC_/V_ indices and `.py:line` coordinates below are per-this-version reads — **when HVT is present, re-resolve them** (grep the coupling/vertex by particle content, don't trust the cached index). The DURABLE, model-independent point is the mechanism (external coupling drives a value but does not gate vertex presence), not HVT's specific coordinates.

- The Drell-Yan qq̄V⁰ coupling `GC_90` (`couplings.py:368-370`):
  `value = '(cN*cq*complex(0,1)*gw**2)/(2.*gst) + (cwt*ee*complex(0,1)*sN)/(2.*swt)'`, `order={'QED':1}`. First term cq-driven; second a V–Z mixing remnant (sN internal `cmath.sin(thN)`, `parameters.py:452-455`).
- `cq` is **external**, `parameters.py:92-98`: `nature='external'`, `lhablock='RHOINPUTS'`, `lhacode=[4]`. (Siblings `cl` lhacode 5 `:100-106`, `ch` lhacode 7 `:116-122`.) So `cq` is a free param-card input.
- GC_90 sits at cell (0,0) of the DY neutral-vector vertices: V_83 `[c̄, c, Vz]` (`vertices.py:504-508`) and V_87 `[ū, u, Vz]` (`:528-532`), both `lorentz=[FFV2,FFV5]`, `couplings={(0,0):GC_90,(0,1):GC_100}`. `Vz` is the neutral heavy vector V⁰.

→ Setting `cq=0` in the card does NOT remove V_83/V_87 or GC_90; the process still generates the qq̄→V⁰ diagrams. Only GC_90's value collapses to the tiny mixing remnant (the second term, sN-suppressed). The V–W–W coupling `GC_15 = '-2*cC*cN*complex(0,1)*gw*sC'` (`couplings.py:68-70`, on V_36 `vertices.py:202`) is mixing-suppressed (sC internal `cmath.sin(thC)`, `:428-431`).

## Leg 2 — MSSM_SLHA2: the SAME Zχχ coupling drives production and decay, via NMIX columns 3,4

Model `$MADGRAPH_INSTALL/models/MSSM_SLHA2`.

- The χ̃₂⁰χ̃₁⁰Z vertex V_454 `[n2, n1, Z]` (`vertices.py:2731-2734`): `lorentz=[FFV2,FFV3]`, `couplings={(0,0):GC_444,(0,1):GC_422}`. The SAME vertex object serves both production (qq̄→Z*→χ̃₂⁰χ̃₁⁰) and the decay vertex (χ̃₂⁰→χ̃₁⁰Z) — there is one Zχχ interaction in the model, not two.
- GC_444 (`couplings.py:1784-1786`): `value = '-(cw*ee*complex(0,1)*NN1x3*complexconjugate(NN2x3))/(2.*(-1+sw)*sw*(1+sw)) + (cw*ee*complex(0,1)*NN1x4*complexconjugate(NN2x4))/(2....)'` — i.e. ∝ (N₁₃N₂₃* − N₁₄N₂₄*). GC_422 (`:1696-1698`) is the conjugate-flow partner ∝ (N₂₃N₁₃* − N₂₄N₁₄*). Diagonal n1n1Z is GC_421 (`:1692-1694`) ∝ (|N₁₃|² − |N₁₄|²).
- `NNixj` are the higgsino columns 3,4 of the NMIX mixing matrix. `NN1x3` (`parameters.py:1456-1459`) is internal, `value='RNN1x3'`; `RNN1x3` (`:292-298`) is **external**, `lhablock='NMIX'`, `lhacode=[1,3]` (NMIX row 1, col 3). Cols 3,4 = the higgsino content of the neutralino.

→ The Zχχ coupling depends ONLY on the higgsino columns (N_i3, N_i4) of NMIX; a bino-like neutralino (N_i3,N_i4 ≈ 0) makes the coupling small but the vertex stays present. Because one vertex object drives both legs, a param-card NMIX change moves production and decay together — they cannot be tuned independently.

## Leg 3 — default sm: WWZ/WWγ + quartics present, NO neutral trilinear declared

Model `$MADGRAPH_INSTALL/models/sm`. Complete pure-gauge (particles ∈ {W+,W-,Z,a}) vertex inventory, enumerated from `vertices.py` (count `Vertex(` entries for the total):

Trilinears (2 only):
- `[a, W-, W+]` (WWγ) → GC_4 = `'ee*complex(0,1)'`, `order={'QED':1}` (`couplings.py:24-26`).
- `[W-, W+, Z]` (WWZ) → GC_53 = `'(cw*ee*complex(0,1))/sw'`, `order={'QED':1}` (`:220-222`). **dim-4, QED¹ — present in default sm, NOT a dim-6 EFT operator.**

Quartics (4):
- `[a, a, W-, W+]` (γγWW) → GC_5 (`:28+`).
- `[W-, W-, W+, W+]` (WWWW) → GC_35 = `'-((ee**2*complex(0,1))/sw**2)'`, `order={'QED':2}` (`:148-150`).
- `[a, W-, W+, Z]` (γWWZ) → GC_57 = `'(-2*cw*ee**2*complex(0,1))/sw'`, `order={'QED':2}` (`:236-238`).
- `[W-, W+, Z, Z]` (WWZZ) → GC_36 = `'(cw**2*ee**2*complex(0,1))/sw**2'`, `order={'QED':2}` (`:152-154`).

NO neutral 3-gauge vertex: a scan for any vertex with ≥3 particles all in {Z, a} returns NONE — there is no ZZZ, ZZγ, Zγγ, or γγγ vertex declared. (The γWWZ/WWZZ/WWWW quartics are present; GC_5 is the γγWW quartic, also present.)

→ A process needing a ZZZ or Zγγ trilinear (e.g. anomalous neutral triple-gauge coupling) generates ZERO such diagrams in default sm no matter what any coupling is set to — the vertex is undeclared. (Adding it requires a different model/UFO, e.g. an EFT with the dim-6 neutral TGC operators.)

## Leg 4 — default sm: Higgs (id25) tree-vertex inventory (madwidth-enumeration seam)

Enumerated from `$MADGRAPH_INSTALL/models/sm/vertices.py`. Which H(25) tree vertices exist fixes which decay channels `compute_widths`/MadWidth can enumerate (it keeps only `type=='base'` tree/effective interactions; loop/CT invisible — that filter is madwidth's, `mg5decay/decay_objects.py:1591-1592`).

**Physical H tree vertices (survive unitary gauge):**
- Higgs self: `[H,H,H]` V at :61, `[H,H,H,H]` :43.
- Gauge-Higgs: `[W-,W+,H]` :319, `[Z,Z,H]` :421, `[W-,W+,H,H]` :313, `[Z,Z,H,H]` :415.
- Yukawa (the 1→2 fermionic decay vertices): `[b~,b,H]` **V_78 :475 → GC_83**; `[ta+,ta-,H]` :643; `[c~,c,H]` :847; `[t~,t,H]` :853; `[e+,e-,H]` :631; `[mu+,mu-,H]` :637. Among quarks ONLY b,c,t carry a Yukawa vertex (no d/s/u); among leptons e,μ,τ all present in the raw file (restrict_default later zeros e/μ — restriction slice).
- Goldstone/ghost H couplings (`G0 G0 H`, `G- G+ H`, `ghWm ghWm~ H` :109, `ghZ ghZ~ H` :211, etc.) are DROPPED in unitary gauge (loader Goldstone/ghost skip) — not physical decay channels.

**NO effective loop-induced H vertex in sm.** All gluon vertices are `[ghG,ghG~,g]` :217, `[g,g,g]` :223, `[g,g,g,g]` :229 — **no `g g H`**. All two-photon vertices are `[a,a,G-,G+]` :67 (Goldstone) and `[a,a,W-,W+]` :325 — **no `a a H`**. **No `Z a H`** either. So H→gg, H→γγ, H→Zγ carry NO base vertex in sm → absent from compute_widths on sm. (H→bb/ττ/cc/tt/WW/ZZ/ee/μμ all have base vertices.)

**Hbb coupling drive (pole-mass vs Yukawa decouple):** V_78 → GC_83 = `-((complex(0,1)*yb)/cmath.sqrt(2))` (`couplings.py:340-342`), yb internal = `(ymb*cmath.sqrt(2))/vev` (`parameters.py:349-353`). Driven by **ymb** (external, YUKAWA block, lhacode 5, value **4.2**, `:85-91`) — NOT the pole mass MB (external, MASS block, lhacode 5, value **4.7**, `:149-155`). Same lhacode 5, different block/value; MB does not enter GC_83. (Physical pole-vs-MSbar interpretation = physics slice.)

**heft is NOT on this install** (`find $MADGRAPH_INSTALL -iname '*heft*'` → nothing; only `sm`, `loop_sm`, `hgg_plugin` effective). So heft's ggH/Hγγ content CANNOT be source-verified here — route to online-DB fetch. The shipped effective-vertex analogue `hgg_plugin` carries BOTH ggH (`V_13` GG H → GC_13, HIG:1) and Hγγ (`V_12` A A H → GC_1, HIW:1) — see `ufo-shipped-models-and-model-db.md`. If a doc claims "the shipped effective Higgs model has no H→γγ", that is wrong for hgg_plugin; for the true `heft` UFO it is unverifiable without the files.

## Cautions
- "Set the coupling to zero" and "the coupling/vertex is removed" are DIFFERENT model states. Set-to-zero: vertex+coupling+interaction all present, diagrams generate, amplitude→0 (or to a residual term). Removed (`restrict_default`): parameter+coupling+vertex GONE. The observable differs — set-to-zero still produces diagrams (and may carry a residual non-zero amplitude, e.g. HVT's mixing remnant); removed gives NoDiagramException / silent subprocess drop (restriction + diagram-enum slices).
- The loader fixes vertex membership BEFORE any param_card numerical value is read; the ZERO-collapse keys on the literal `value` STRING `'0'`, not the evaluated number (`optimise_interaction`, `import_ufo.py:686`). So a coupling that *evaluates* to 0 at runtime is NOT dropped at load.
- A vertex not in `vertices.py` can never enter a diagram — coupling values are irrelevant. The fix is a different model, not a param-card edit.
- Where the param-card VALUE goes once read, and the σ consequence of a small/zero coupling, is param-card + phase-space slices, not mine. My slice ends at: which vertices/couplings are PRESENT in the loaded model and what their `value` strings + `order` are.
