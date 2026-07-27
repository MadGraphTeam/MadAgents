---
description: A flat comma chain binds a sub-decay IFF its incoming particle is a final-state leg of the CORE at that recursion level. Level-1 daughters (direct core legs) bind flat; level-2+ daughters (daughter-of-a-daughter) need parens grouping them under their parent's decay, else DISCARDED (warn), not attached to a wrong parent. CORRECTS the old "h>WW>4tau flat form discards" claim — that flat form BINDS (probe).
---

# Multi-level decay chains — parens required only for LEVEL-2+ sub-decays

Source: MG5_aMC v3.7.1. Probe-confirmed. Triggered by multi-level (>=3-level) comma chains, e.g. `decay h2 > z h3 mu+ mu-, h3 > z h1 j j, h1 > b b~`.

## The rule (corrected)

A flat comma chain `CORE, D1, D2, …` binds each sub-decay `Di : X > …` **iff `X` is a final-state leg of the CORE fragment at that recursion level** (`extract_decay_chain_process`, madgraph_interface.py:5661, splits on `,`/`(`/`)`; core = the fragment before the first comma). The amplitude-layer gate is set-based PDG-match: `DecayChainAmplitude` collects `decay_ids` (diagram_generation.py:1392-1395) and `trim_diagrams` flags a leg `onshell=True` only when `leg.get('state') and leg.get('id') in decay_ids` (diagram_generation.py:1285-1286). A decay whose incoming id survives the "present in a core leg?" removal loop (:1402-1414) is **discarded** with a RED warning ("Decay information for particle(s) X is discarded … you forgot parentheses").

- **Level-1 daughter** (X is a direct final-state leg of the core) → binds FLAT, no parens needed.
- **Level-2+ daughter** (X is a daughter of a daughter — NOT itself a core leg) → its sub-decay is DISCARDED in flat form. It is NOT attached to the wrong parent and NOT nested sequentially — the flat comma chain does neither. Fix: parentheses grouping the sub-decay with its parent's decay, `(parent > … X …, X > …)`, so X becomes a leg of the nested core.

## CORRECTION — the old h>WW→4τ "flat discards" claim was WRONG

This page previously claimed `generate h > w+ w-, w+ > ta+ vt, w- > ta- vt~` (flat) discards both W decays → NEXTERNAL=6, bare `_h_wpwm`. **That is false.** Fresh probe (v3.7.1):

| Form | NEXTERNAL | Subprocess | decayBW `/1/` lines | Warning |
|------|-----------|------------|---------------------|---------|
| `h > w+ w-, w+ > ta+ vt, w- > ta- vt~` (flat) | **5** | `P1_h_wpwm_wp_tapvl_wm_tamvl` | `GFORCEBW(-1,1)/1/`, `GFORCEBW(-2,1)/1/` (both W) | **none** |

The flat form BINDS both W decays because the core is `h > w+ w-` and w+/w- ARE its final-state legs (level-1 daughters). NEXTERNAL=5 = h (chain-incoming) + {ta+ vt ta- vt~}. Two `/1/` lines = both W mothers forced-BW. No parens needed here.

## The genuine trap — a LEVEL-2 sub-decay (fresh probes)

The trap needs the discarded sub-decay's parent to be a **level-2+ daughter**, i.e. a production/decay core whose grand-daughter decays:

| Form | Subprocess | Warning |
|------|------------|---------|
| `p p > z h, z > e+ e-, h > w+ w-, w+ > mu+ vm` (flat) | `P1_qq_zh_z_ll_h_wpwm` (W bare) | `Decay information for particle(s) w+ is discarded` |
| `p p > z h, z > e+ e-, (h > w+ w-, w+ > mu+ vm)` (paren) | `P1_qq_zh_z_ll_h_wpwm_wp_lvl` (W bound) | none |

Flat: core `p p > z h`, legs {z,h}. `z > e+ e-` binds (z is a core leg), `h > w+ w-` binds (h is a core leg) — both LEVEL-1 → z_ll and h_wpwm appear in the suffix. But `w+ > mu+ vm` — w+ is a daughter of h (LEVEL-2), NOT a core leg of `p p > z h` → **discarded**. The paren `(h > w+ w-, w+ > mu+ vm)` opens a nested level whose core is `h > w+ w-` (legs w+, w-), so w+ binds → `_wp_lvl` suffix.

## Worked 3-level case

`decay h2 > z h3 mu+ mu-, h3 > z h1 j j, h1 > b b~` (flat): core `h2 > z h3 mu+ mu-`, legs {z, h3, mu+, mu-}.
- `h3 > z h1 j j`: h3 IS a core leg (level-1) → **binds**.
- `h1 > b b~`: h1 is NOT a core leg — it is a daughter of h3 (level-2) → **discarded** with the "forgot parentheses" warning. h1 stays a bare ME external; it is NOT re-attached to h2 or h3.

So the flat chain does NOT "distribute each clause to all parents" and does NOT "nest sequentially": it binds only clauses whose parent is a current-scope core leg, and drops the rest. The parenthesised form `decay h2 > z h3 mu+ mu-, (h3 > z h1 j j, h1 > b b~)` is the **correct** fix: the outer paren makes a nested core `h3 > z h1 j j` (legs z, h1, j, j); `h1 > b b~` then matches leg h1 and binds. (Characterising the flat failure as "misinterpreted nesting" is imprecise — the flat outcome is discard-with-warning of the h1 sub-decay, not a mis-attachment.)

## Fingerprint

| Signal | Meaning |
|--------|---------|
| `Decay information for particle(s) X is discarded` warning | a level-2+ sub-decay dropped (parens missing) |
| Subprocess suffix stops one level short (`…_h_wpwm` with no `_wp_…`) | the grand-daughter decay dropped |
| decayBW.inc `/1/`-line count < expected resonance count | one fewer forced-BW mother than a fully-bound chain |

Never count commas/parens — read the diagram/suffix/decayBW fingerprint (see decay-binding-is-scope-times-match.md).

## Boundary
- Warning EMISSION formatting (singular vs plural id list) is diagram-enumeration's slice.
- Runtime σ of a dropped-subdecay config (it's the shorter chain's σ, different magnitude) is phase-space's slice.

## Related
`nested-subdecay-paren-taxonomy.md` (H→tt̄ via `p p > z h` core — t/t̄ are level-2, so it correctly requires parens; its 6/7/8-diagram taxonomy is the paren-placement enumeration and is unaffected by this correction). `decay-binding-is-scope-times-match.md` is the general BINDING principle. `clause-distribution-and-topology.md` for same-clause distribution.
