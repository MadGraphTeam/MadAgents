---
description: SMEFTatNLO NP=2/insertion → squared NP^2 bins all EVEN (σ_int in NP^2==2, σ_quad in NP^2==4, odd bins empty); NP=1 unsatisfiable → SM-only. Contrast SMEFTsim NP=1/insertion (int in NP^2==1, quad in NP^2==2).
---

# SMEFTatNLO NP^2 bin selection — odd bins are empty; which bin holds int vs quad (v3.7.1)

The per-insertion convention (read it per-model, never assume) directly fixes WHICH `NP^2==N` bin
holds the SM×EFT interference vs the EFT² squared term, and makes half the bins identically empty.
This is the practical "which constraint do I write for σ_int / σ_quad" answer.

## Source facts (SMEFTatNLO, v3.7.1)
- `coupling_orders.py:9-11`: `NP = CouplingOrder(name='NP', expansion_order=2, hierarchy=1)`.
- `couplings.py`: **every** NP-bearing coupling carries `'NP':2` — **zero** `'NP':1`, **zero** `'NP':4`
  (recipe: `grep -oE "'NP':[0-9]+" couplings.py | sort | uniq -c` → only the `:2` value appears).
  So **one dim-6 insertion = NP+2** (ctG examples: GC_154 `{'NP':2,'QCD':1,'QED':1}` couplings.py:299;
  GC_358 `{'NP':2,'QCD':1}` couplings.py:1719; GC_360 `{'NP':2,'QCD':2}` couplings.py:1731).

## Arithmetic consequence — every amplitude has EVEN NP, every squared bin is EVEN
- An amplitude's NP order = (#dim-6 insertions) × 2 ∈ {0, 2, 4, …} — always EVEN. There is no NP:1
  coupling, so an NP=1 amplitude **cannot be built** at all.
- The squared order is the SUM of the two interfering amplitudes' NP powers
  (`pass_squared_order_constraints`, base_objects.py:2670-2671; see eft-squared-order-diagram-filtering.md).
  EVEN + EVEN = EVEN → `NP^2 ∈ {0, 2, 4, 6, …}`, all EVEN. **`NP^2==1` and `NP^2==3` are identically
  EMPTY** (no amplitude pair sums to an odd power).

## Which bin holds what (SMEFTatNLO)
| want | constraint | what it keeps |
|---|---|---|
| SM only | `NP=0` / `NP==0` | pure SM (no NP amplitude) |
| SM × EFT interference (σ_int) | `NP^2==2` | SM(NP=0) × 1-insertion(NP=2) |
| EFT² squared (σ_quad) | `NP^2==4` | 1-insertion(NP=2) × 1-insertion(NP=2) [+ SM × 2-insertion(NP=4) if present] |
| amplitude linear (interference) | `NP=2` / `NP==2` | exactly one insertion at amplitude level |
| `NP^2==1`, `NP^2==3` | — | **EMPTY** (odd bin) |
| `NP=1` | — | **SM-only** — no NP:1 amplitude exists, only NP=0 survives |

## Anchored-empirical (trusted reference numbers)
- `SMEFTatNLO; g g > t t~ NP=2` → 10 diagrams, σ(ctG=0.1)=467.9pb vs σ(ctG=0)=453.2pb (Δ=+14.7pb,
  the SM×ctG interference). `g g > t t~ NP=1` → 3 diagrams = SM-only 452.1pb (ctG invisible — NP=1 is
  the unsatisfiable amplitude bound, so the ME is pure SM and the ctG value does nothing).
- σ_quad of O_lq^(1) lives in `NP^2==4`; σ_int in `NP^2==2`; `NP^2=1` bin is EMPTY. (Matches the
  even-bin arithmetic above.)

## Contrast — SMEFTsim (NP=1 per insertion) shifts the bins by one rung
When `models/SMEFTsim_topU3l_MwScheme_UFO/` was on disk (session-specific — `ls models/` first;
see bundled-eft-models.md), its `couplings.py` carried NP-bearing couplings with `'NP':1` (no `'NP':2`)
— so **p=1** for that variant. NB its `coupling_orders.py` has `NP expansion_order=99` (a CAP, not the
increment) — read the increment off `couplings.py`, not expansion_order. With p=1 amplitudes have
NP ∈ {0,1,2,…} (odd allowed):
- σ_int (SM×EFT) lives in `NP^2==1`; σ_quad (EFT²) in `NP^2==2`.
So a user porting a "σ_int = NP^2==1" recipe from SMEFTsim to SMEFTatNLO gets an **EMPTY** bin. The
correct SMEFTatNLO bins are int=`NP^2==2`, quad=`NP^2==4`. **Always read the active model's
`couplings.py` per-insertion value before writing an `NP^2==N` constraint** — N is not portable across
EFT UFOs (bundled-eft-models.md: NP=+2 SMEFTatNLO, DIM6=+1 dim6top, NP=+1 SMEFTsim).

## dim6top — DIM6=+1 (like SMEFTsim numerically, different order NAME)
dim6top uses DIM6=+1 per insertion (couplings.py: every DIM6 coupling `'DIM6':1`), so its bins follow the SMEFTsim
rung pattern: int in `DIM6^2==1`, quad in `DIM6^2==2`. **But the order NAME is `DIM6` (+`FCNC`), not
`NP`** — writing `NP^2==N` on dim6top errors at parse with the valid-order-set message
(dim6top-fcnc-second-eft-order.md). So the bin shift AND the token name both differ from SMEFTatNLO.

## Boundary
- Whether the user physically wants linear (int) or quadratic (squared) truncation is
  ma-physics-consultant's call; this page records only which NP^2 bin each maps to per-model.
- The LO-accept / NLO-reject parser asymmetry for `NP^2==N` is coupling-order/amcatnlo slice.
- The diagram-pruning mechanism that realizes these bins (apply_squared_order_constraints, LO-only) is
  in eft-squared-order-diagram-filtering.md; the auto-cap (bare process → NP<=2) in
  eft-expansion-order-and-weighted-default-cap.md.
