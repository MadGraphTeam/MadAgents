---
description: Tagged-particle (!a!) parse — the two syntactic forms, the initial-photon-only rule (5076), the aUPC auto-define for !a!+j, and the probe-confirmed split of which rejection fires — initial non-photon tag hits 5076 at tree level, final-state/initial-photon tags hit the tree-mode reject (5231).
---

# Tagged particles `!particle!` and UPC (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, in `extract_process` leg loop.

## Two tag syntaxes (5062-5071)
1. `!PART!` — `part_name.startswith('!') and endswith('!')` → strip both, `is_tagged=True` (5063).
2. `N!PART!`-style — `endswith('!') and count('!')==2 and leading part isdigit` → `replace('!','')`, `is_tagged=True` (5066). (digit-prefixed tagged form.)
Else `is_tagged=False`.

## Initial-photon-only rule (5073-5078)
If `is_tagged and not state` (initial state): unless `part_name in ('a','22')` → `InvalidCmd("only initial photons can be tagged")`. If photon AND `upc_with_jet` → `part_name='aUPC'.lower()`.

## UPC auto-define (5048-5052)
Before the loop: if `'!a!' in args and 'j' in args` → `upc_with_jet=True` and **`self.do_define('aUPC = a j / g', log=False)`** is invoked — the parser silently creates an `aUPC` multiparticle. Else `upc_with_jet=False`.

## CRITICAL probe-confirmed interaction (v3.7.1, sm) — message depends on WHICH tag
Two distinct tagged-particle rejections fire in DIFFERENT loop positions, and which one the user sees depends on the tag, NOT solely on tree-vs-NLO:
- **Photon check (5073-5076)** runs INSIDE the per-token loop, BEFORE leg construction. Fires only for an **initial-state** tag that is **not a photon** (`is_tagged and not state and part_name not in ('a','22')`). It fires at **tree level too**.
- **Tree-mode reject (5227-5231)** runs LATER in the same iteration, in the leg-construction block, gated on `LoopOption in ['virt','sqrvirt','tree','noborn']`. Fires for any tag that SURVIVED the photon check (all final-state tags; initial-photon tags) when LoopOption is tree-like.

Probes (all at tree/LO, sm):
- `generate !u! u~ > e+ e-` (initial **non-photon** tag) → **`only initial photons can be tagged`** (5076 wins — the photon check, at tree level, BEFORE the tree-mode reject is reached).
- `generate u u~ > !z! z` (final-state tag) → **`tree mode does not handle tagged particles`** (5231; photon check skipped because `state==True`).
- `generate !a! a > e+ e-` (initial **photon** tag) → **`tree mode does not handle tagged particles`** (5231; passes the photon check, then tree reject wins).

So the "only initial photons can be tagged" message (5076) IS reachable at tree level — for an initial non-photon tag (the `!u! u~` probe above). Tagged-particle physics is otherwise an FKS/NLO (`MultiTagLeg`, 5237) feature. Tagged-leg citation warnings (5244-5247): final-state tagged → arXiv:2106.02059; initial-state coherent photon → arXiv:2504.10104.
