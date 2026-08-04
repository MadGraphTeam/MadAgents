---
name: off-shell-threshold-check
description: When m_parent < 2m_pole for a decay, check m_parent vs 2m_lightest_decomposition before concluding "forbidden"
metadata:
  type: feedback
---

**Mistake:** When m_parent < 2m_pole for a decay D, concluded the decay is "kinematically forbidden" and avoided the chain-decay syntax.

**Why it's wrong:** The pole-mass threshold is only the on-shell threshold. Daughters can be heavily off-shell, so the true kinematic limit is set by the lightest allowed decay products, not the pole masses. For H→tt̄ at m_H=250 < 2m_t=346, the top virtualities run from m_W+m_b≈85 GeV up to m_H−m_W−m_b≈165 GeV. The threshold check should be against 2(m_W+m_b)≈170, and 250 > 170 means the decay proceeds via virtual daughters.

**How to apply:** In process-spec building, when evaluating a chain-decay H→DD̄:
1. If m_parent < 2m_pole → do NOT conclude "forbidden".
2. Compute m_lightest_decomposition: sum of masses of the lightest allowed decay products for D (via SM cascade or model-allowed modes).
3. If m_parent < 2m_lightest_decomposition → truly forbidden.
4. If 2m_lightest ≤ m_parent ≤ 2m_pole → off-shell decay; proceed with chain-decay syntax, and derive bwcutoff for daughters from the virtuality range [m_lightest, m_parent − m_other], rounding generously.