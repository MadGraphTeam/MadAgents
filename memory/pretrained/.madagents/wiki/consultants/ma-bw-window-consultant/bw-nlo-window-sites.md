---
description: NLO-template BW-window sites (cluster.f, add_write_info.f) using the registered bwcutoff — unconditional, real-width, no small_width_treatment / gForceBW / 5σ, v3.7.1
---

# NLO BW-window sites vs LO cut_bw

I own the *registration* of the NLO `bwcutoff` (banner.py:5713, default read there;
bw-runcard-knobs.md) and the conceptual on/off-shell BW-window test. The *purpose* each NLO
site serves (clustering topology selection, LHE resonance-writing for the shower) is
amcatnlo/fks territory — but the BW-window *expression* itself is my slice, and its sharp
differences from the LO `cut_bw` machinery are source-static facts worth holding so I don't
wrongly carry LO assumptions (Γ_eff floor, Regime A/B, 5σ fallback, gForceBW) into an NLO
question. Cites `$MADGRAPH_INSTALL/Template/NLO/SubProcesses/`, v3.7.1.

## The two NLO BW-window sites
- **`cluster.f:692`** (`subroutine cluster_check`-style; header lines 660-663): for each
  s-channel propagator with `prwidth(i)>0`,
  `onshell = abs(mass(i)-prmass(i)) .lt. bwcutoff*prwidth(i)`. Sets `OnBW`, then the SAME
  idenpart logic as LO cut_bw (mother/daughter same ID → drop one; else keep the leg closer
  to pole — cluster.f:696-719). **Purpose:** restricts clustering to topologies that carry
  the on-shell s-channel particle (amcatnlo/fks ownership).
- **`add_write_info.f:808`**: `onshell = ( abs(xmass-pmass(i)) .lt. bwcutoff*pwidth(i) )`,
  same idenpart logic (815-829). **Purpose:** decides which resonances get written to the
  event for the shower. The `igranny`/`write_granny(nFKSprocess)` branch (801-805)
  **bypasses the bwcutoff test entirely** — comment lines 797-800: *"If s-channel is the
  grandmother, check if we need to write this resonance. In that case, ignore the bwcutoff
  parameter."* When write_granny, `onshell=.true.` is forced regardless of mass; when not
  write_granny, the granny is `cycle`-skipped. So bwcutoff is overridden for the grandmother
  leg by the FKS granny machinery.

## How NLO differs from LO cut_bw (the load-bearing contrast)
1. **Real width, not Γ_eff.** Both NLO sites use `bwcutoff*prwidth`/`bwcutoff*pwidth` — the
   literal propagator width. There is **no `max(prwidth, prmass*small_width_treatment)`
   floor.** `grep -l small_width_treatment Template/NLO/` = **0 hits** — small_width_treatment
   is absent from every NLO template file (it is registered for LO RunCard only, banner.py:4452;
   NOT re-registered for RunCardNLO). A width below `mass*small_width_treatment` (the LO floor)
   at NLO is used literally, with no NWA σ-correction in this BW path.
2. **Unconditional bwcutoff — no Regime A/B split.** The LO file has 6 bwcutoff sites split
   into unconditional (Les-Houches tag, s-hat gate) vs forced-only (cut_bw enforcement,
   set_peaks) — bw-bwcutoff-scaling-regimes.md. The NLO window is a single
   `bwcutoff*width` for ALL s-channel resonances. There is **no 5d0*width hardcoded
   fallback** (grep for `5d0`/`5.0d0` near width in cluster.f/add_write_info.f = none).
3. **No gForceBW CONSUMER / no decayBW.inc in the BW path.** `grep -rn gForceBW Template/NLO/`
   = **0 hits** — no NLO Fortran reads gForceBW; the forced-on-shell apparatus (gForceBW=1/2,
   lbw require/exclude) is functionally LO-only and every NLO resonance is tested by the same
   plain window. REFINEMENT: the exporter `export_fks.py:3966` DOES emit
   `data gForceBW(...)` lines — but over `booldict[leg.get('from_group')]` (NOT `onshell` as in
   the LO writer export_v4.py:5894) and declared **`logical gforceBW`** (:3979), bundled into a
   configs-style file (not a standalone decayBW.inc). So the SYMBOL is written at NLO with
   `from_group` (boolean) semantics and no consumer — distinct from the LO 3-valued
   `integer gForceBW` from the decay-chain onshell flag (bw-gforcebw-lbw-provenance.md). The
   behavioural claim (NLO BW window ignores any force flag) stands; "no gForceBW emitted at all"
   would be wrong.
4. **Drives clustering / LHE-write, not an event cut.** `cut_bw` returns `.true.` to CUT an
   event (bw-onshell-test-cutbw.md). The NLO sites set an `OnBW` array consumed by clustering
   and event-writing; an off-shell resonance is not a fired window-cut here, it just doesn't
   restrict clustering / isn't written.

## What carries over from LO
- The **idenpart logic** is structurally identical (mother/daughter same-ID → keep the leg
  closer to its pole, drop the other; always drop an identical final-state daughter). Same
  algorithm, both files.
- The **t-channel skip** (`exit` when itree points at legs 1/2) is the same shape as LO's
  nbw-skip of t-channel/initial legs.

## MadWeight aside (separate template, separate parser)
- `Template/MadWeight/src/setrun.f:371`: `call get_real(...,"bwcutoff",bwcutoff,<default>)` and
  `run.inc:26-27` declare the same `common/to_bwcutoff/`. MadWeight parses its own bwcutoff
  (default is the `get_real` fallback at setrun.f:371 — read it there) independent of the
  matrix-element BW test. Noted for completeness; MadWeight
  internals are not this slice.

## Cautions
- Do NOT answer an NLO bwcutoff question with LO reflexes. There is no Γ_eff floor, no
  small_width_treatment, no Regime A/B, no 5σ fallback, no gForceBW at NLO — the window is
  plain `bwcutoff*real_width`, unconditional, and (in add_write_info) overridable by the FKS
  granny flag. The *purpose* (cluster topology, shower-write) is amcatnlo/fks; route there for
  how OnBW is consumed.
- These are static source facts (which expression, which width, grep-confirmed absences); the
  runtime effect of changing NLO bwcutoff (clustering / LHE resonance population) is a
  runtime prediction, not probed here.
