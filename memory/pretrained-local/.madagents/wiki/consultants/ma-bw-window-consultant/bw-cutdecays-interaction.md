---
description: cut_decays-vs-BW interaction — cut_decays gates kinematic cuts on decay-product legs via from_decay, which check_decay derives from the decay-chain gForceBW=1 flag, in setcuts.f, v3.7.1
---

# cut_decays vs BW interaction (setcuts.f)

Cite `$MADGRAPH_INSTALL/Template/LO/SubProcesses/setcuts.f`, v3.7.1. `cut_decays` is the
run-card flag (default False; bw-runcard-knobs.md). This page records how it gates cuts on
decay products — the kinematic-cut application itself is the kinematic-cuts slice; here we
only own the cut_decays gating semantics tied to BW/decay structure.

## from_decay computation
- `setcuts.f:31`: `logical from_decay(-(nexternal+3):nexternal)`.
- `setcuts.f:88`: in `COMMON /TO_MERGE_CUTS/ is_pdg_for_merging_cut, from_decay`.
- `setcuts.f:192-193`: `if(.not.cut_decays) call check_decay(from_decay)` — the decay-origin
  array is only populated when cut_decays is False (i.e. only needed when we intend to skip
  cuts on decay products).
- `subroutine check_decay(from_decay)` defined at `setcuts.f:961`.

## check_decay keys on gForceBW=1 — the decay-chain → from_decay link (the load-bearing mechanism)
`check_decay` declares `integer gForceBW(-max_branch:-1,lmaxconfigs)` + `include 'decayBW.inc'`
(setcuts.f:981-982) and computes from_decay **directly from the forced-BW flag**:
```
do i=-(nexternal-3),-1                                    ! setcuts.f:994-1001
   if(tprid(i,1).eq.0.and.gForceBW(i,1).eq.1.or.from_decay(i)) then
      from_decay(i)=.true.
      from_decay(iforest(1,i,1))=.true.                   ! both daughters
      from_decay(iforest(2,i,1))=.true.
   endif
enddo
```
- Condition: a genuine s-channel propagator (`tprid(i,1).eq.0`, i.e. NOT a t-channel) that is
  **forced-BW (`gForceBW(i,1).eq.1`)**, OR already flagged. Then it and BOTH `iforest`
  daughters are marked `from_decay=.true.`. The loop runs innermost→outermost so the flag
  propagates DOWN the whole decay sub-tree.
- => **The SAME decay-chain `onshell→gForceBW=1` flag that drives the BW-window enforcement
  (myamp.f cut_bw, bw-onshell-test-cutbw.md) ALSO identifies "decay products" for the
  cut_decays gate.** One flag, two consumers. So "which legs are decay products" is not a
  separate notion — it is exactly the forced-BW (decay-chain `decay`/`$$`) subtree.
- Consequence: a propagator written with decay-chain syntax (gForceBW=1) has its descendants
  exempted from kinematic cuts under the default cut_decays=False; an ordinary (non-forced,
  gForceBW=0) s-channel resonance's daughters are NOT from_decay and ARE cut. Only the
  config-1 column (`gForceBW(i,1)`, `iforest(...,1)`) is read here.

## Gating of per-particle cuts
- `setcuts.f:201-203`: loop over final-state legs; `do_cuts(i)=.true.` by default, then
  `if(.not.cut_decays .and. from_decay(i)) do_cuts(i)=.false.`.
  => **cut_decays=False (default): kinematic cuts are switched OFF for legs that came from a
  decay.** cut_decays=True: cuts apply to decay products too.
- Same `.not.cut_decays.and.from_decay(i/j)` guard repeats at setcuts.f:322, 441, 448 for
  other cut categories.

## Independent "heavy/neutrino" exclusions (NOT cut_decays-driven)
- setcuts.f:212: `if (pmass(i).gt.20d0) do_cuts(i)=.false.` — no cuts on top/W/Z/H
  regardless of cut_decays.
- setcuts.f:213-215: neutrinos (|pdg|=12,14,16) always excluded.

## PDG_CUT caveat (source comment, setcuts.f:211)
- `c-do not apply cuts to these. CAREFULL: PDG_CUT do not consider do_cuts (they simply
  check the cut_decays)` — PDG-specific cuts bypass do_cuts and look at cut_decays directly.

## Relation to the BW window
- cut_decays does NOT touch the `cut_bw` on-shell *test* (bw-onshell-test-cutbw.md) — the
  window enforcement and the cut gating are separate code. But they share ONE input: the
  decay-chain `gForceBW=1` flag. cut_bw uses it to choose the bwcutoff vs 5σ window
  (Regime B); check_decay uses it to mark from_decay. So "decay products" (cut_decays
  scope) ≡ "forced-BW subtree" (BW-window scope) — the same chain-decay legs.
- The interaction: with cut_decays=True, decay products that land inside the BW window are
  still subject to kinematic cuts (pt/eta/etc.), which can sculpt the in-window population.
  With the default False, in-window decay products pass kinematic cuts freely.

## Caution
- Default cut_decays=False is silent: a user expecting their pt/eta cuts to bite on, e.g.,
  leptons from a Z decay will find they don't, because those legs are from_decay and
  do_cuts is forced off. Heavy resonances (>20 GeV) and neutrinos are additionally exempt
  independent of the flag.

## Anchored σ (MG5_aMC v3.7.1, Drell-Yan) + the bwcutoff-invariance discriminator
Drell-Yan with leptonic cuts ptl=25 / etal=2.5 / drll=0.4 (anchored, not directly re-probed
— treat as hypothesis for a NEW process until probed):
- **arrow form** `p p > z > l+ l-` → gForceBW=0, the leptons are NOT from_decay → cuts apply →
  σ = 1131 pb (fiducial).
- **comma/chain form** `p p > z, z > l+ l-` → gForceBW=1, the leptons ARE from_decay →
  default cut_decays=False switches their cuts OFF → σ = 2840 pb (un-fiducial, 2.5× larger).
- **comma form + `cut_decays=True`** → cuts re-applied to the decay leptons → σ = 1123 pb,
  collapsing onto the arrow value. (1131 vs 1123 differ only by the residual on-shell-window
  difference between the two diagram sets, not by the cut treatment.)
- The which-syntax-writes-which-gForceBW step is chain-decay's slice (bw-gforcebw-lbw-
  provenance.md records the consumed flag); here we own the σ CONSEQUENCE of the flag through
  the cut_decays gate.

**The gForceBW=1 here is INERT for the BW WINDOW** — the Z is on-shell (m_Z within the window
at any reasonable bwcutoff), so the window enforcement does nothing; the flag's ONLY operative
role in this case is the from_decay tagging that drives the cut gate. This gives a clean
DISCRIMINATOR: **σ is invariant under bwcutoff (default → 1000 unchanged)** because no BW
reweighting is happening. So if a user sees the 2.5× comma-vs-arrow σ gap and suspects "the
BW window is reweighting my Z," the bwcutoff-invariance test rules that out — the gap is the
cut_decays/from_decay gate, not the window. (Contrast: an OFF-shell forced leg, where σ DOES
move with bwcutoff — bw-cutoff-sizing-derivation.md.)
