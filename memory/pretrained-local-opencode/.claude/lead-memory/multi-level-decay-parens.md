---
name: multi-level-decay-parens
description: Multi-level decay chains (A>B>C) require outer parentheses to bind sub-decays to intermediate particles
metadata: 
  node_type: memory
  type: feedback
---

**Lesson:** In MG5 decay-chain syntax, a multi-level chain like `A > B C, B > D E, C > F G` MUST be wrapped in outer parentheses: `(A > B C, B > D E, C > F G)`. Without outer parens, MG5 discards the sub-decays of the first-level daughters and produces the wrong final state.

**Why:** The comma-separated decay segments are parsed hierarchically — the first segment defines the core decay (A → BC), and subsequent segments define sub-decays of the first-level daughters. Without outer parens, the parser treats the W sub-decays as independent decay specifications not bound to the W bosons from H → WW, producing bare W⁺W⁻ in the final state (NEXTERNAL=6) instead of the expected 4-body final state (NEXTERNAL=8).

**Discipline:** When building a chain-decay with sub-decays (depth ≥ 2), always wrap the full H-decay chain in one set of outer parentheses. Verify by checking the subprocess name for `_tapvl_` (tau neutrino) or the NEXTERNAL count matches expected final-state particles.