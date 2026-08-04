---
description: A result is being justified by it-ran / it-gave-a-number instead of by the observable the spec implies.
---

# Clean run is not correct physics — the silent-physics-wrong family

The whole family (derived-quantities, removed-coupling, coupling/vertex-viability, SMEFT order-bin, process-line-scope) is the same mistake wearing a different mask: **an MG5 result was treated as evidence because the run succeeded.** This page is the umbrella dispatch discipline; the per-symptom mechanism and fix live in the sibling pages it routes to — **it carries no MadGraph facts of its own, only the routing.**

## The unifying principle

> MG5 validates *syntax, model-consistency, and numerics* — never your *intent*. A process that generates an output dir, integrates, and reports a finite σ has proven only that MG5 found something to compute, not that it computed the thing the physics-spec asked for. "It ran / it generated / it gave a number" is therefore **never** the evidence; the evidence is always the **physics observable the spec implies**, evaluated against a *consistent baseline*.

This is why the lead's `mg-setup` reconciliation compares the simulation-spec against the physics-spec rather than against the run's exit code, and why a setup-only task (σ-feedback loop deliberately closed) still has a right answer.

## The shared diagnostic menu (pick the one the spec turns on)

Every member of the family is caught by an observable, not by the exit code. The menu (each arm grounded in a sibling page, not here):

- **σ-magnitude vs a consistent baseline** — a collapse (×10³–10⁴) or a degeneracy (identical σ across configs that should differ) is the tell. *Baseline must be consistent* — same model, same card, same normalization.
- **partial width / BR** — for a decay vertex, `compute_widths` partial width and BR are the discriminator; a microscopic partial width or BR≈0 is the silent-fail fingerprint (no MG5 check flags it for a colorless particle).
- **BR ≤ 1 self-consistency** — BR = Γ_partial/Γ_total > 1 is the stale-width tell; MG5 accepts it silently.
- **diagram-topology fingerprint** — per-channel diagram count + a vertex-routine grep in `matrix1_orig.f` (e.g. FFV1 photon-vertex count, Yukawa FFS GC-tag count). The diagnostic's named home is diagram-enum `../consultants/ma-diagram-enumeration-consultant/enumeration-topology-fingerprint.md`.
- **order/sign parity** — for an EFT polynomial piece, σ-vs-sign-of-c parity (quad even, int odd) + σ(c=0)=0-under-`==N`-vs-≠0-under-`<=N` + matrix-source GC/JAMP fingerprint.

The discipline: **before trusting the run, name which observable distinguishes intended-from-wrong, and put it in the dispatch.** Route the VALUE/CHECK to the owning slice as a *derivation/inspection request* — never hand a consultant a candidate to bless (marked-premise validation would rubber-stamp it).

## Route by symptom to the owning sub-playbook

| symptom (what the user/spec presents) | family member | sub-playbook |
|---|---|---|
| a coupling/flavor/process expected to contribute gives **nothing** (or only one of several survives) | model **removed** the coupling (restrict_default) — diagram count CHANGES | `removed-coupling-not-small.md` |
| signal hinges on a coupling the **benchmark zeroes** (explicit fermiophobic; derived decoupled-μ); σ collapses, diagram count UNCHANGED | benchmark-zeroed coupling / no-viable-channel | `coupling-vertex-viability.md` |
| a mass/width was edited, or an off-shell/threshold regime entered; σ off by ×10³⁺ | **stale / regime-wrong derived value** (width, bwcutoff) | `derived-quantity-staleness.md` (→ `decay-widths-lifecycle.md`, `offshell-bwcutoff-derivation.md`) |
| an EFT σ_int/σ_quad/inclusive piece is wanted; σ degenerate across bins | wrong **order-bin** (convention-dependent label; LO single-run vs NLO multi-run) | `smeft-order-bin-isolation.md` |
| "what does this process line compute / is this the right final state / why is σ off" | wrong **amplitude scope** (single-`$` keeps diagram; clause distributes to all parents; comma-only sub-decay discarded; inclusive ≠ resonant chain) | `process-line-scope-traps.md` |
| "I set X in the card but the run did Y" | value governed at a **later lifecycle layer** | `config-value-lifecycle-layers.md` |
| fiducial cut seems not applied to decay products; comma-σ > arrow-σ | `cut_decays=False` silent exemption | `fiducial-cuts-fanout.md` |

## Boundary — this is the SILENT class only

The complement is **loud**: MG5 rejects at parse / validation / stability time, no output dir. That is `process-verification-fanout.md` (the rejection-message router) — there the failure announces itself; route to the slice whose guard fired. This page owns only the clean-exit-but-wrong cases, where the dominant mode is silence and the only defense is inspecting the artifact.

The diagram count is the **bridge** between two members: count CHANGES ⇒ model-removed (`removed-coupling-not-small`); count UNCHANGED + σ collapse ⇒ benchmark-zeroed (`coupling-vertex-viability`).

## Dispatch discipline (what this page changes about how I work)

1. When a result — mine, a consultant's, or the user's — is offered as correct *because it ran*, treat that as an unverified claim. Find the family member by symptom; name the observable; dispatch the check.
2. Scale depth to the symptom: one scope-owner + one topology check is the right depth for a process-line-scope question; a width derivation + BR check for a decay-chain σ; do not over-fan.
3. A consultant return of "already on my page, no drift, it reproduces" is a **confirmation**, not a miss — these traps are stable across v3.7.1.
4. A confidently-stated *mechanism* can be wrong even when the *number* it backs is right — trust the anchored number, dispatch-to-owner to fix the mechanism, and flag the backing consultant claim UNTRUSTED so the correction flows back to the lead artifact.
