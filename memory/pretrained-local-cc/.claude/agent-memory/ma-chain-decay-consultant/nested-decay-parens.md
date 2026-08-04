---
name: nested-decay-parens
description: Sub-decays whose parents are not core legs require nested parens; flat syntax drops sub-decays
metadata:
  type: feedback
---

<Mistake>Used flat chain-decay syntax `h > t t~, t > b w+, t~ > b~ w-` when t and t̄ are not core final-state legs of the outer process. MG5 dropped the sub-decays and produced bare t t̄.</Mistake>
<Why>Flat syntax splits on commas: each clause searches for its parent among core final-state legs. t and t̄ are NOT legs of `p p > z h`, so the sub-decay clauses are discarded.</Why>
<How to apply>When sub-decays involve particles not in the outer process final state, wrap the entire chain (core + sub-decays) in outer parentheses with inner parens around each sub-decay: `(h > t t~, (t > b w+), (t~ > b~ w-))`. This is the same rule as multi-level-decay-parens for nested H-decay chains.</How to apply>