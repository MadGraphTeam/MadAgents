---
description: EFT order tokens are silently rewritten between the command line and the emitted process line (==→auto-squared, =→<=, squared-only→inferred amp, expansion_order clamp, NLO default 99); read the emitted Trying/born process line, never the typed constraint.
---

# EFT order tokens are rewritten before enforcement — read the emitted process line

The single principle behind the four EFT order-mechanism pages: **the coupling-order constraint you
type is almost never the one MG5_aMC enforces.** Between `extract_process` parsing and the generated
matrix element, an EFT order token passes through several silent transformations. The only reliable
record of what was actually enforced is the emitted `Trying process:` (LO) / `Generating ... born
process:` (NLO) line — NOT the command you typed. Always quote that emitted line when telling a user
what their EFT truncation is.

## The transformation table (each verified from source + probe, v3.7.1)
| You type | What MG enforces | Where | Instance page |
|---|---|---|---|
| `NP==2` (amp, LO) | amp `NP==2` **plus auto** `NP^2==4` | madgraph_interface.py:4955-4960 | eft-power-counting-parser |
| `NP>2` (amp, LO) | amp `NP>2` plus auto `NP^2>4` | madgraph_interface.py:4962-4965 | eft-power-counting-parser |
| `NP=2` (amp) | reinterpreted as `NP<=2` (warns) | madgraph_interface.py:4950-4954 | eft-power-counting-parser |
| `NP^2=4` (squared) | reinterpreted as `NP^2<=4` (warns) | madgraph_interface.py:4936-4939 | eft-power-counting-parser |
| `NP^2==2` ALONE (LO) | amp `NP` **inferred** = squared value (or 99 if neg/`>`) | madgraph_interface.py:4994-5000 | eft-power-counting-parser |
| (nothing, SMEFTatNLO LO) | `NP<=2` injected by expansion_order cap | base_objects.py:3766+ | eft-expansion-order-and-weighted-default-cap |
| `NP==4` over cap (SMEFTatNLO) | amp clamped `NP<=2`, token `NP==4` kept but unreachable | base_objects.py check_expansion_orders | eft-expansion-order-and-weighted-default-cap |
| `NP==2`/`NP^2==4` at NLO `[QCD]` | **REJECTED** — only `<=` allowed | amcatnlo_interface.py:542 / madgraph_interface.py:4982-4985 | eft-nlo-order-determination |
| unset NP at NLO (some orders given) | `NP<=99→` amp-capped to 2, `NP^2=198` | amcatnlo_interface.py:533-539 (unset→default_unset_couplings), 607-612 (NP^2=2*v warn) | eft-nlo-order-determination |
| any order, LO, `default_unset_couplings≠99` | unmentioned EFT orders set to that value (often 0) | madgraph_interface.py:4971-4980 | eft-nlo-order-determination |
| any NLO process | every model order forced into split_orders | amcatnlo_interface.py:625-626 | eft-nlo-order-determination |

## Why this is a generalization, not a merge
Each instance page documents ONE transformation. This page asserts the *operational rule that catches
cases the instances don't enumerate*: **for any EFT order token — including operators/models not yet
probed — the gen-time emitted process line is authoritative, and it may differ from the typed token in
direction (`=`→`<=`), in added constraints (auto-squared, forced split_orders), in value (clamp to
cap, default to 99/198), or in acceptance (NLO rejection).** When asked "what does `NP=X` do for this
model/process", the answer is never read off the typed token; it is read off the emitted line (and the
warnings), which depend on the model's `coupling_orders.py` (expansion_order, per-insertion k), the
`default_unset_couplings` option, and whether a perturbation `[...]` is present (LO vs NLO path).

## How to apply (the rule)
1. Never quote the user's typed constraint as the enforced truncation. Run/inspect the emitted
   `Trying process` (LO) or `born process` (NLO) line and quote THAT.
2. The same typed token gives different enforced orders across models (per-insertion k, expansion_order
   cap) — re-derive per model, never reuse a remembered mapping. (bundled-eft-models for k; the
   expansion-cap page for the auto-cap.)
3. LO vs NLO diverge hard: `==` works at LO, is rejected at NLO; an unset order caps-but-doesn't-truncate
   at NLO (→198). Branch on whether `[...]` is present before predicting.
4. Watch the warnings, not just the process line: `=`→`<=`, over-cap clamp, and "Using: NP^2=198" all
   surface only in warning text.

## Boundary
- This is the *order-determination* axis (what constraint is enforced). Whether the resulting truncation
  is the physically-wanted linear-vs-quadratic choice is ma-physics-consultant. The downstream per-order
  ME / amp_split consumption of the enforced squared/split orders is nlo-export slice.
- The four instance pages are KEPT — they carry the per-mechanism source detail and probe counts this
  table only points at.
