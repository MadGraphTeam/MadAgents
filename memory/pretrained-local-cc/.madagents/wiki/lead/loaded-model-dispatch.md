---
description: Whether a vertex/coupling exists in the model as imported, not as the UFO declares it. A restriction ran at import.
---

# Loaded model dispatch — include restriction, not just UFO

When the question is "does vertex/coupling X exist in the loaded model?", dispatch **the restriction consultant**, not just the UFO consultant. `import model sm` auto-applies `restrict_default sm` at import time (`import_ufo.py:201-310`), which zeros first-gen Yukawas (yme, ymm, ymc = 0.0 in `restrict_default.dat`) and removes the corresponding vertices (V_104: H e⁺e⁻, V_105: H μ⁺μ⁻). The UFO consultant reads raw UFO files — the pre-restriction declaration. It tells you what the model declares, not what `import model X` loads.

The `model-content-lifecycle.md` lifecycle states: "What does model X actually CONTAIN" → ufo (declared) → model-loader (converted) → restriction (pruned). Dispatch **restriction** for the loaded-model question. The UFO consultant answers "what does the UFO declare?" — a different question.

**Concrete trigger:** any question about vertex existence in the default `sm` model → dispatch `ma-restriction-consultant` first. The `restrict_default` file ships with the model and is applied automatically; it is not optional.

**Verified by probe:** `generate h > e+ e-` → `NoDiagramException` (vertex V_104 removed by restriction); `generate h > ta+ ta-` → 1 diagram (vertex V_106 survives). The loaded model has one H→ℓ⁺ℓ⁻ vertex, not three.

**Relation to neighbouring playbooks:**
- `model-content-lifecycle.md` — the general lifecycle router (declare→convert→prune→augment). This page is its **dispatch reminder**: the "prune" stage is what determines the loaded model; dispatch it, not just "declare".
- `removed-coupling-not-small.md` — the observable playbook for the removed-coupling symptom class. This page is its **dispatch precursor**: reach this page when deciding which consultant to call; reach removed-coupling when the symptom is already known.