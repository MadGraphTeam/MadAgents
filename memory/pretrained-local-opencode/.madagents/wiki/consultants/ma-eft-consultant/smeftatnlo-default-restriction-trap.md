---
description: Trap — SMEFTatNLO loaded with its default restriction rejects NP order constraints because all Wilson coefficients are zeroed; use restrict_LO/NLO instead. Contrast with dim6top (no restrict file).
---

# SMEFTatNLO default-restriction drops the NP order (TRAP)

## Symptom (probe-verified)
`import model SMEFTatNLO; generate p p > t t~ NP==2` →
`InvalidCmd: model order NP not valid for this model (valid one are: QCD, QED, EW, EW^2, aEW, aS)`.
Yet `display coupling_order` on the SAME loaded model lists `NP : weight = 1, QCD : 2, QED : 4`.

## Root cause
- `import model SMEFTatNLO` (bare) applies `restrict_default.dat`.
- In `restrict_default.dat`, every Wilson coefficient in blocks DIM6, DIM62F, DIM64F, DIM64F2L, DIM64F4L
  is `0.` (only `DIM6` code 1, Lambda, is nonzero). Verified by reading the file.
- The restriction algorithm removes interactions whose coupling is identically zero → all NP-carrying
  vertices are dropped from the surviving interaction set.
- Order validation in `extract_process` reads `self._curr_model.get('coupling_orders')`
  (madgraph_interface.py:4893), and `get_coupling_orders()` derives the set from the **interactions
  present** (base_objects.py:1374-1377: `set(sum([list(i.get('orders').keys()) for i in interactions]))`).
  With no NP interaction surviving, `NP` is absent from that set → rejected.
- `display coupling_order` reads a different source (the model's declared orders), so it still shows NP —
  hence the confusing mismatch.

## Fix
Import a restriction whose coefficients are nonzero:
- `import model SMEFTatNLO-LO`  (restrict_LO.dat, LO-only orders)
- `import model SMEFTatNLO-NLO` (restrict_NLO.dat)
- `import model SMEFTatNLO-NLO_no4q` (restrict_NLO_no4q.dat — the entire `DIM64F` 4-fermion all-quark block zeroed, incl. light-quark-coupling cQq83; see smeftatnlo-restrict-card-taxonomy.md)
Probe-verified: `SMEFTatNLO-LO` + `p p > t t~ NP==2` generates diagrams (7 for gg, 10-14 for qq~).

restrict file sizes: the default card is shorter than the LO/NLO/NLO_no4q cards (which are equal-length) — `wc -l` to confirm, don't cache the counts.
Card-to-card content lives authoritatively in **smeftatnlo-restrict-card-taxonomy.md** (block table,
exact zeroed coeffs per card, LO→NLO operator+ghost-width zeroing, NLO-vs-no4q DIM64F-only diff). Trap-
relevant fact only: `restrict_default.dat` has ALL Wilson coeffs zeroed (only Lambda nonzero) → no
NP-carrying interaction survives → NP order rejected. The other three cards keep NP-carrying coeffs.

## Scope: the trap needs `restrict_default.dat` — the running tree has NONE, so it does NOT reproduce it
The trap symptom above is SPECIFIC to the distributed `models/SMEFTatNLO/`, which ships `restrict_default.dat`
(all WCs zeroed → NP dropped on bare import). That distributed model is manually-placed and session-specific
(`ls models/` first — can be absent; see bundled-eft-models.md).
A separate `tests/input_files/SMEFTatNLO_running/` tree (the RGE/running variant) may be present independently
and is NOT the same model — it is not importable as a `models/` model, and its restrict set is
`restrict_LO.dat`, `restrict_NLO.dat`, `restrict_4f.dat` with **NO `restrict_default.dat`** and no
`restrict_NLO_no4q.dat` (verify against whichever copy is on disk). Consequences:
- No `restrict_default.dat` → a bare load of that tree would be UNRESTRICTED, and its `parameters.py` defaults
  the WCs NONZERO (`ctG` at lhablock DIM62F lhacode 24, parameters.py:315,321 — read the default there). So on
  the running tree the NP order is NOT dropped — the opposite of the trap. Trap ⇔ a `restrict_default.dat` that zeroes all WCs.
- Block/lhacode maps are per-copy: the running tree uses `DIM62F` (ctG) — verify block names against whichever
  copy is actually on disk, never assume the taxonomy page's distributed-card block names transfer.

## Contrast: dim6top_LO_UFO ships NO restrict file
`import model dim6top_LO_UFO; generate p p > t t~ DIM6==1` works out-of-box (probe-verified, 6 diagrams/subprocess).
With no restrict card, the full unrestricted interaction set loads, so `DIM6` is always in the order set
even though parameters.py defaults the Wilson coefficients to 0. The zero-coefficient stripping is an
explicit-restriction behaviour, not an unrestricted-load behaviour.
