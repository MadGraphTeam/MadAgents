---
description: cut_decays=False (default) silently exempts decay-product legs from per-particle fiducial cuts (ptl/etal/drll); comma/chain decay drops them, arrow form keeps them; setcuts.f do_cuts mechanism + anchored sigma
---

# cut_decays — decay-product legs are silently exempt from fiducial cuts

Source: `$MADGRAPH_INSTALL/Template/LO/SubProcesses/setcuts.f` + `cuts.f` + run_card
default `banner.py:4306`. v3.7.1.

## Class pin (LO-only)
`cut_decays` is registered ONLY in `RunCardLO` (banner.py:4306; class spans 4187–5593).
It is ABSENT from `RunCardNLO` (starts 5594; zero `cut_decays` occurrences). So this whole
exemption mechanism is an LO-run_card concept; do not quote a `cut_decays` default for NLO.

## The trap (user-facing)
`cut_decays` defaults to **False** (`banner.py:4306`: `self.add_param("cut_decays", False, cut='d')`).
With the default, the generic per-particle fiducial cuts (`ptl`/`etal`/`drll`, and the jet/
photon/b analogues) are **silently NOT applied to decay-product legs** of a forced-BW /
chain decay. The run_card still lists the cut values; they just never bite those legs.

Process-WRITING form decides whether a leg is "from decay":
- **Comma / chain form** `p p > z, z > l+ l-` — the Z is a forced-BW propagator
  (`gForceBW=1`); its daughter leptons are tagged `from_decay=.true.` → cuts dropped on them.
- **Arrow form** `p p > z > l+ l-` — `gForceBW=0`, no leg tagged → `do_cuts=.true.`,
  cuts applied normally.

Anchored σ (Drell-Yan, ptl=25, etal=2.5, drll=0.4, byte-identical run_card):
- arrow `p p > z > l+ l-` = **1131 pb** (fiducial).
- comma `p p > z, z > l+ l-` = **2840 pb** (un-fiducial, 2.5× larger — cuts inert on leptons).
- comma with `cut_decays=True` = **1123 pb** (collapses onto the arrow value).
**Fix when you want fiducial cuts on decay products: set `cut_decays=True`.**

## The mechanism (source-walked, confirmed)
1. `setcuts.f:192-193`: `check_decay(from_decay)` is called **only when `cut_decays=False`**
   (`if(.not.cut_decays) call check_decay(from_decay)`). With `cut_decays=True` the
   from_decay array is never populated → never trips the exemption.
2. `check_decay` (`setcuts.f:961-1003`): for each s-channel propagator with
   `tprid(i,1).eq.0 .and. gForceBW(i,1).eq.1` (forced BW, from `decayBW.inc`), sets
   `from_decay(i)=.true.` and propagates to its daughters `from_decay(iforest(1,i,1))` /
   `from_decay(iforest(2,i,1))` (`:995-999`). gForceBW=1 is the forced-resonance /
   chain-decay flag — its ORIGIN is co-owned with ma-bw-window-consultant (the
   cut_decays↔BW interaction); this page owns only the cut-application side.
3. `setcuts.f:201-203`: per leg, `do_cuts(i)=.true.` then
   **`if(.not.cut_decays.and.from_decay(i)) do_cuts(i)=.false.`** (the load-bearing line).
4. `setcuts.f:259-313`: per-particle cut arrays init to no-op (`etmin=0, etmax=-1,
   etamin=0, etamax=-1`); the per-CLASS values (`ptl→etmin`, `etal→etamax`, …) are
   assigned **only inside `if(do_cuts(i)) then`** (`:269`). So a `do_cuts=.false.` leg
   keeps the no-op init.
5. `cuts.f:330-340` (pt loop) and the eta loop read `etmin(i)/etmax(i)/etamin/etamax`
   directly with NO `do_cuts` reference — they are inert on an exempt leg purely because
   its arrays were never filled. Same for the pairwise ΔR/mass fills, which are guarded
   by `if(do_cuts(i).and.do_cuts(j))` (`cuts-f-filter.md` Mapping layer) — a pair with an
   exempt leg gets `r2min=0/r2max=-1`, so `drll` etc. are dropped too.

## Scope caveat — only bites when decay products are IN the cut's class
The exemption is moot unless the decay products fall in the cut's particle class.
- Default `l` multiparticle is `{e,μ}` (process-spec territory). τ's are NOT in the default
  `l` define, so for a τ final state `ptl`/`etal`/`drll`/`mmll` never restricted the τ's and
  `cut_decays` is moot there. (Note the Fortran `is_a_l` array at `setcuts.f:227-229` DOES
  tag PDG 15/τ — the τ-exclusion is at process-generation multiparticle level, not is_a_l.)
- The trap fires only when the decay products are in the cut's class (here e/μ leptons).

## Refinements vs other pages
- **Generic cuts** respect cut_decays via the `do_cuts` path above.
- **PDG-specific dict cuts** (`pt_min_pdg`/`mxx_min_pdg`/…) BYPASS `do_cuts` but STILL
  respect cut_decays/from_decay: `setcuts.f:322-324` `cycle`s an exempt leg
  (`if(.not.cut_decays.and.from_decay(i)) cycle`). So cut_decays=False suppresses PDG cuts
  on decay products too. See pdg-cuts-and-smin.md §2.
- **Merging-cut tagging** also excludes decay products: `is_pdg_for_merging_cut(i)` only set
  when `.not.from_decay(i)` (`setcuts.f:241-249`).

## Caution
The written run_card value ≠ the enforced cut for decay-product legs under the default
`cut_decays=False` — another instance of the cut-value layer law (cut-value-layer-precedence.md):
the value is silently neutralized at setcuts.f array-fill time. There is NO warning printed;
the only tell is the σ shift. Trace cut_decays + the process-WRITING form (comma vs arrow)
before answering "why isn't my ptl/drll respected on the leptons?".
