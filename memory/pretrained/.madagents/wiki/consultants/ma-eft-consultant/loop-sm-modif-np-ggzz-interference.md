---
description: gg→ZZ signal/bkg/interference isolation via loop_sm_modif's custom NP order — stock loop_sm declares ONLY QCD+QED (NP rejected, probe-confirmed); loop_sm_modif is an EXTERNAL (non-bundled) model whose NP-tags-HVV / p=1 claim cannot be source-verified here.
---

# loop_sm_modif + custom NP order for gg→ZZ signal/bkg/interference

Context: gg→ZZ signal (H→ZZ), continuum background, and their interference can be
isolated using `loop_sm_modif` — a modified `loop_sm` where the HVV couplings carry
a custom `NP` order, so coupling-order bins pick out the pieces. The gg→ZZ
interference PHYSICS is ma-physics; the NP^2==N squared-order
binning syntax is coupling-order; the NLO ==/> rejection is nlo-syntax. This page
owns only the MODEL / coupling-order-DEFINITION side.

## GROUNDED: stock loop_sm declares ONLY QCD and QED — NP is rejected

`$MADGRAPH_INSTALL/models/loop_sm/coupling_orders.py` declares exactly two orders:
- line 9-12: `QCD` (hierarchy=1, expansion_order=-1, perturbative_expansion=1)
- line 14-17: `QED` (hierarchy=2, expansion_order=-1, perturbative_expansion=0)

No `NP` (nor DIM6/EFT) order exists. Consequence: `generate ... NP=...` on stock
loop_sm ERRORS. Probe-confirmed (v3.7.1, `import model loop_sm; generate g g > z z NP=1`):
> InvalidCmd : model order NP not valid for this model (valid one are: QED, QCD, EW, EW^2, aEW, aS).

(The valid list's `EW/EW^2/aEW/aS` are auto-generated aliases of the two declared
QED/QCD orders — coupling-order slice mechanics, not extra declared orders.)
So to run any `NP=`/`NP^2==` gg→ZZ bin-isolation you MUST supply a model that
DECLARES an `NP` order; stock loop_sm cannot do it. This is the general principle
this slice owns: to isolate a coupling-order bin you need the operator-carrying
vertices tagged with a dedicated order, and the model must declare that order in
its own `coupling_orders.py` (read it — never assume from memory).

## GAP (external model, NOT installed here): loop_sm_modif

`models/` on THIS install (v3.7.1) contains: hgg_plugin, loop_sm, MSSM_SLHA2, sm,
taudecay_UFO (verified `ls`). **No `loop_sm_modif`.** So the following doc claims
are EXTERNAL / unverifiable-here — record, do NOT cache as source fact:

- **Provenance:** `loop_sm_modif` is obtained by downloading `loop_sm_modif.tar.gz`
  from the MadGraph Offshell_interference wiki and extracting into `models/`. It is
  NOT bundled and NOT in the `_online_model` dict (so not fetchable via
  `import model loop_sm_modif` auto-DB) — a manual-download external model.
- **What NP tags (UNVERIFIED):** doc says NP tags the HVV vertices (HWW/HZZ,
  "GC_31/GC_32 in the UFO"), Yukawas stay QED. Do NOT cache the GC_31/GC_32 identity
  as fact — it is a claim about a file not present here.
- **Per-insertion power (UNVERIFIED for this model):** if NP counts one HVV vertex
  per insertion with increment **p=1**, then the bin map would be
  σ_bkg ↔ `NP=0`, σ_int ↔ `NP^2==1`, σ_quad(signal) ↔ `NP^2==2`. This p=1 map is
  CONSISTENT with the general single-insertion convention but is NOT source-verified
  for loop_sm_modif — the increment is per-model and MUST be read from the extracted
  model's `coupling_orders.py`/`couplings.py` before trusting any bin label.
  (Contrast the two dim-6 EFT models' convention range — fetch-first, NOT bundled: SMEFTatNLO NP p=+2 → bins all even; dim6top
  DIM6 p=+1. Bin N is NOT portable across EFT UFOs — see smeftatnlo-np-bin pages.)

## Note: cached bundled-eft-models.md is install-specific / stale here
`bundled-eft-models.md` lists dim6top_LO_UFO + SMEFTatNLO as "bundled". THIS install
has NEITHER (only the SM/loop_sm/MSSM/taudecay/hgg baselines). Those two are
install-snapshot-dependent, not universally bundled — the page's own "always ls the
actual install" caveat governs. Re-`ls models/` before asserting any model is present.
