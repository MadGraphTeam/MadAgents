---
name: subthreshold-bwcutoff-derivation
description: "When m_parent < m_daughter_sum, derive bwcutoff from kinematics — never accept default 15"
metadata: 
  node_type: memory
  type: feedback
---

When assembling a setup with a sub-threshold decay chain (m_parent < sum of daughter masses), the lead must derive bwcutoff from first-principles kinematics before checking any consultant return about gForceBW or BW-window enforcement.

**Derivation:** For a decay X→AB where m_X < m_A + m_B, one daughter must be off-shell. The minimum virtuality is:
  m_A_off ≤ m_X − m_A  (when B is on-shell at its pole)
  Widths below pole: (m_A − (m_X − m_A)) / Γ_A

If this exceeds ~15 Γ (the default bwcutoff), bwcutoff must be raised. Recommended: bwcutoff ≥ ceil(Γ_A / (m_A − (m_X − m_A))) rounded generously.

**For H→WW at 125 GeV:** m_W_off ≤ 125 − 80.4 = 44.6 GeV. Widths below: (80.4 − 44.6)/2.05 ≈ 17.5. Use bwcutoff ≥ 50.

**Hardening trigger:** Any chain-decay where m_parent < m_daughter_sum → derive bwcutoff. Do not adopt a consultant's "gForceBW controls window, and default is fine" claim without this arithmetic.