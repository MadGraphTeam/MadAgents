---
name: off-shell-bwcutoff-derivation
description: When a daughter is off-shell in a chain-decay, derive bwcutoff from V_min = m_lightest_decomposition, not use default
metadata:
  type: feedback
---

<Mistake>When m_parent < 2m_pole for a chain-decay, left bwcutoff at default 15, which clips the entire off-shell region.</Mistake>
<Why>The default BW window covers ±15·Γ around the pole. For virtual daughters, the pole is ABOVE the kinematic range, so the BW window must extend DOWN to the kinematic floor.</Why>
<How to apply>In process-spec building, when m_parent < 2m_daughter_pole: compute V_min = sum of lightest allowed decay products (e.g. m_W+m_b for t→bW), then bwcutoff = ceil((m_pole − V_min) / Γ_daughter). Round up to nearest integer. Default 15 is never sufficient for off-shell daughters.</How to apply>