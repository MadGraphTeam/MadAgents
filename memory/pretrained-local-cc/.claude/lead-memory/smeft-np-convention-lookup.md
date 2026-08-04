---
name: smeft-np-convention-lookup
description: "When building an EFT process command, look up the model's NP-per-insertion value from source before authoring any NP constraint"
metadata: 
  node_type: memory
  type: feedback
---

**Mistake:** Proposed `NP=1` for SMEFTatNLO NLO process, thinking NP=1 means "one NP vertex" (linear EFT). SMEFTatNLO assigns NP=2 per dim-6 insertion (each $1/\Lambda^2$ factor → NP=2), so `NP=1` excludes the operator entirely — σ = σ_SM only, a silent failure.

**Why:** The NP-per-insertion convention `p` is model-dependent: SMEFTatNLO uses p=2, SMEFTsim uses p=1. Pretraining associates "NP=1 = linear" from SMEFTsim and incorrectly transfers it.

**How to apply:** When building an EFT process command (any NP constraint, any EFT model), **look up `p` from the model's `coupling_orders.py` before writing the NP value.** Read the EFT consultant's return or the model source — don't guess. The existing `smeft-order-bin-isolation.md` wiki page carries the table (SMEFT@NLO p=2, SMEFTsim p=1), and `eft-smeft-fanout.md` says "Read coupling_orders.py for the per-model order name." Use them. The NP constraint is `NP=p` for inclusive SM+one insertion, `NP=2p` for two insertions. Also include `QED=0` for SMEFTatNLO at NLO (omitting QED=0 leaves QCD unconstrained → defaults to 0 → loop-induced gg→tt̄ instead of qq̄→tt̄).

**Also confirmed correct:** `generate p p > t t~ QED=0 NP=2 [QCD]` is the right process for inclusive SM+cQq83-interference at NLO in SMEFTatNLO.

Links: [[smeft-order-bin-isolation]], [[eft-smeft-fanout]]