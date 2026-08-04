---
description: Your signal leans on a coupling the model variant or restrict card may have deleted outright, not merely made small.
---

# Removed coupling ≠ small coupling — the coupling-driven "missing contribution" class

The class turns on a model-load-time fact: `restrict_default` does not *default* a zeroed coupling to a small number — it **removes the parameter, the derived coupling, and every vertex that depends on it** from the in-memory model. So a process/flavor the user expects (because nature has it, or "the Yukawa is just small") generates **zero diagrams**. The dangerous part is that MG5 surfaces this in two different ways depending on whether a multiparticle saves the process — one loud, one silent — and the silent one invites a "right number, wrong story" answer.

## When it applies (the regime trigger)

A user expects a contribution from a coupling that `restrict_default` zeros (the first/second-generation Yukawas: `yme`(11), `ymm`(13), `ymc`(4), and the first-gen quark Yukawas), and is surprised when:
- `generate h > e+ e-` (or `h > mu+ mu-`, etc.) → `NoDiagramException : No amplitudes generated`; OR
- a flavor-inclusive form (`(h > l+ l-)` with `l = e mu ta`) runs fine and gives a σ but the user wants to know **which flavors actually contribute and why**.

Surface keywords: "the channel exists / PDG says BR≈…", "tiny but nonzero", "Yukawa scales with mass so e/μ are negligible", "inclusive over flavor", "why does MG5 refuse `h > e+ e-`", "can I just `set ye`".

**Diagnostic core to ship: removed ≠ small.** A zeroed-in-`restrict_default` coupling is *structurally absent*, not numerically tiny. Three downstream tells (pointers, not restated facts):
- the parameter is gone from the `set` option-list and gets **no** `param_card` line written (absent, not present-with-zero) — `../consultants/ma-restriction-consultant/remove-interactions.md`, `../consultants/ma-param-card-consultant/restriction-pruned-external-is-dropped.md`;
- the only shipped `sm-*` restrict variant that keeps `yme≠0` is `sm-lepton_masses` — `../consultants/ma-restriction-consultant/sm-restrict-files.md`;
- the fix is **model-load-time** (load `sm-lepton_masses` or a custom `restrict_<tag>.dat`), never a `set`/param-card edit — those cannot resurrect a removed vertex.

## The two observable forms (route by which one fired)

| form | what MG5 does | owning slice |
|---|---|---|
| **lone zero-diagram process** (`generate h > e+ e-`) | `NoDiagramException` — loud, no output dir | diagram-enum: `NoDiagramException` fires only when the WHOLE (post-expansion) process is empty (`diagram_generation.py:1907-1911`) |
| **zero-diagram subprocess inside a multiparticle expansion** (`(h > l+ l-)`, l=e,mu,ta) | the 8 e/μ subprocesses are **SILENTLY dropped** — no per-subprocess warning, no "Process has X diagrams" line; the τ subprocess survives; σ is **bit-identical** to `(h > ta+ ta-)` alone | diagram-enum: the `failed_procs.append` branch at `diagram_generation.py:1902-1904` has no `logger` call; survives-on-any-nonzero |

Page: `../consultants/ma-diagram-enumeration-consultant/multiprocess-crossing-mirror.md` (the silent-drop section). The silent multiparticle drop is **distinct** from the chain-decay "Decay information for particle(s) … is discarded" warning (that is a sub-decay scope mismatch — see `process-line-scope-traps.md` case 3); the multiparticle drop is genuinely warning-less.

## Dispatch sequence

1. **ma-restriction-consultant** — ground the removal (`RestrictModel.restrict_model`, `import_ufo.py:2390`; emissions `remove interactions: e- e- h` / `remove parameters: mdl_yme` at `:2925`/`:3097`) and the `sm-*` variant survey (only `sm-lepton_masses` keeps `yme≠0`; no `sm-full`; `sm-no_b_mass` is the wrong "less-restricted" guess — it only restores the b mass). This is the slice that owns "removed ≠ small."
2. **ma-diagram-enumeration-consultant** — which observable form fired (NoDiagramException vs silent multiparticle drop) and the σ-bit-identical consequence.
3. **ma-model-loader-consultant** — the `import model sm-lepton_masses` resolution (the model-load-time fix). Only if the user needs the fix prescribed.
4. **ma-param-card-consultant** — only if the user proposes a `param_card`/`set` workaround; confirm the line is absent and inert.

## Anticipated traps (named by behavioural shape)

- **Fabricated "tiny number"** — agent quotes the user's PDG BR (≈5e-9) as if it came from the run, never engaging that MG5 *refused*. Silent fail; the answer superficially matches the expectation.
- **Yukawa-smallness "right number, wrong story"** — agent invokes `y_ℓ ∝ m_ℓ` to argue e/μ contribute negligibly. Numerically ≈ right (σ_inclusive ≈ σ_ττ) but structurally wrong: the vertices don't exist, they aren't "small." The "small" picture predicts a ~0.35% δσ from the μ piece (observable above MC stat at 10k); the truth is **exactly 0** (bit-identical σ). **The headline trap of the inclusive form.** → restriction + diagram-enum.
- **`set ye` / param-card workaround** — `set ye 5.11e-4` → `InvalidCmd` (param not in option list); a `Block YUKAWA 11` edit is inert (no Fortran reads it). Hard fail — doesn't reach `generate`. → restriction/param-card.
- **Wrong restrict variant** — `sm-no_b_mass` ("less restricted") still zeros `yme` → same `NoDiagramException`. Wrong dimension of restriction space. → restriction.
- **`sm-full` mythical variant** — no such card in 3.7.1. → restriction/model-loader.
- **Sign-flipped `l+` factoid** — "default `l+` is e+ μ+ only (no τ)" is true in general but irrelevant when the user redefined `l+`; deploying it to conclude e/μ contribute and τ doesn't is *inverted* physics. → process-syntax (the user's `define` took effect) + restriction (τ is the survivor).

## Relation to neighbouring playbooks
- **`model-content-lifecycle.md`** is the CONTENT axis (what's in the model; restriction prunes interactions/couplings but drops NO particle). This page is its **observable-consequence** side: what the user *sees at `generate`* when a coupling was pruned. Cross-link, don't duplicate.
- **`process-line-scope-traps.md`** is the topology sibling — when the unwanted contribution is present (Yukawa Hττ alongside HWW) rather than removed, and must be filtered out (chain syntax / `/`-filter). Removed-coupling is "it's not there"; scope-traps is "it's there but you didn't want it."
