---
description: The symmetry program's BW-window sites (BW_Conflict + failConfig in madevent_symmetry.f → P_*/symmetry.f) — a THIRD bwcutoff/gForceBW consumer that drops configs / masks conflicts at symfact.dat time, v3.7.1
---

# BW-window in the symmetry program (BW_Conflict + failConfig)

Cite `$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_symmetry.f`, v3.7.1. This
template is rendered by `export_v4.py:write_symmetry` (`export_v4.py:5993` loads it) into
`<PROC_DIR>/SubProcesses/<P_n>/symmetry.f` (export_v4.py:4262-4263, 4383-4384), compiled as
`symmetry.o` (linked with `idenparts.o`; `Template/LO/SubProcesses/makefile:51`). The
`program symmetry` (madevent_symmetry.f:2) header: *"Given identical particles, and the
configurations. This program identifies identical configurations and specifies which ones
can be skipped"* — it writes `symfact.dat` (opened at :187).

This is a **third bwcutoff/gForceBW consumer** beyond `cut_bw` and `set_peaks`
(bw-onshell-test-cutbw.md, bw-setpeaks-psgrid.md) — those run at integration/event time;
this runs at **symmetry-determination / config-pruning time** and can DROP a whole
integration config — a distinct site from the runtime myamp.f BW logic: it is the
symmetry-program copy.

## The two BW routines in this program
Both take `forcebw(-max_branch:-1)` as an argument — the per-config `gForceBW` column from
`include 'decayBW.inc'` (declared :180 / :323, passed in at the call sites :200, :228). So
the same `decayBW.inc` gForceBW array this slice consumes at runtime is also consumed here.

### 1. `subroutine BW_Conflict(iconfig,itree,lconflict,sprop,forcebw)` (:286)
Marks which s-channel propagators are in mutual mass conflict (their summed daughter mass
can't sit on the parent pole) so they can be cut from BW treatment. Mechanism:
- `call idenparts(...)` (:361) first — only the outermost identical particle is viewed as a
  BW unless required (`idenparts` lives in `Template/LO/SubProcesses/idenparts.f`, its own
  file — boundary, not this page).
- For each s-channel with `prwidth>0` and not radiation (`iden_part(-i).eq.0`): if the
  summed daughter mass `xmass(-i) > prmass(-i,iconfig)` it **can't be on shell** →
  `lconflict(-i)=.true.` (:376-379).
- **THIRD margin — `+3d0*prwidth` (hardcoded 3σ, NOT bwcutoff, NOT 5σ):**
  madevent_symmetry.f:381: `xmass(-i) = max(xmass(-i), prmass(-i,iconfig)+3d0*prwidth(-i,iconfig))`
  for non-iden parts. This is a distinct hardcoded window — the codebase uses bwcutoff (forced),
  5σ (set_peaks/cut_bw non-forced), AND 3σ here for the conflict mass bound.
- Daughters of a conflicted BW are propagated as conflicting (:387-407) **unless**
  `gForceBW(itree(k,-j),iconfig).eq.1` — a forced-BW daughter is NOT marked conflicting
  (:392, :399). Comment :211 "JA 4/8/11 don't treat forced BW differently" at the call-side
  loop, but here forced legs ARE spared the conflict propagation.
- If `stot < mtot**2` (not enough CM energy) ALL BWs are marked conflicting (:411-416).
- Final pass: a conflict is dropped if the leg has `prwidth<=0` or is an identical-particle
  radiation (:420-428) — i.e. conflicts are only kept for genuine BW props.

Uses **real `prwidth`** throughout — NO `max(prwidth, prmass*small_width_treatment)` floor
(grep small_width_treatment madevent_symmetry.f = 0). So unlike LO `cut_bw`/`set_peaks`, the
symmetry-program windows are NOT Γ_eff-floored.

### 2. `function failConfig(iconfig,iarray,itree,sprop,forcebw)` (:434)
*"Determines if the configuration allows integration based on mass relations"* (:436-437).
Returns `.true.` → config is dropped (cannot integrate). Default `.false.` (:516). The
per-config `iarray` (the conflict-encoding from BW_Conflict, 1 = "cuts on BW") gates the
non-forced branch. For each s-channel with `xwidth(-i)=prwidth(-i,iconfig)>0` (:518):

**Dual window — SAME gForceBW=1→bwcutoff / else→5σ split as cut_bw, but here it FAILS a config:**
- `forcebw(-i).eq.1` (gForceBW=1, decay-chain): madevent_symmetry.f:525:
  `if (xmass(-i) > prmass(-i,iconfig) + bwcutoff*xwidth(-i)) failConfig=.true.; return`
  else floor `xmass(-i)=max(xmass(-i), prmass-bwcutoff*xwidth(-i))` (:529-530).
- else if `iarray(nbw).eq.1` (conflicted, non-forced): madevent_symmetry.f:533:
  `if (xmass(-i) > prmass(-i,iconfig) + 5d0*xwidth(-i)) failConfig=.true.; return`
  else floor with `5d0*xwidth` (:537).
- (Non-conflicted non-forced legs: no window test here.)
- Final: `if (stot < mtot**2) failConfig=.true.` (:546-548) — insufficient phase space.

The live `bwcutoff` comes from `include '../../Source/run_card.inc'` (:86) →
`common/to_bwcutoff/bwcutoff` (:333, :478). The commented-out
`call get_real(...," bwcutoff ",bwcutoff,5d0)` at :89 is **DEAD CODE** — its 5d0 default is
NOT operative; do not mis-read it as the symmetry-program bwcutoff default.

## Why this is load-bearing (the non-obvious part)
- bwcutoff has a reach beyond the integration/event-time sites: at symmetry time, a forced-BW config whose
  minimum daughter-sum mass exceeds `prmass + bwcutoff*width` is **dropped entirely**
  (`failConfig=.true.`) — it never becomes an integration channel. This is parallel to but
  EARLIER than the set_peaks impossible-onshell `write_null_results+stop`
  (bw-setpeaks-psgrid.md): failConfig prunes the config at symfact.dat generation; set_peaks
  zeroes a channel at integration. Both gate on `gForceBW=1 → bwcutoff` vs the fixed fallback,
  but with DIFFERENT fallbacks (failConfig: 5σ only if iarray=1; set_peaks: 5σ for lbw=1).
- The Regime A/B taxonomy (bw-bwcutoff-scaling-regimes.md) was scoped to myamp.f's bwcutoff sites.
  These two symmetry-program sites are a separate file with the SAME forced-only character as
  Regime B (bwcutoff only when gForceBW=1; else hardcoded). They do NOT add a Regime-A
  (unconditional) use — the symmetry-program bwcutoff is forced-only. **IMPORTANT:** this
  forced-only characterization applies ONLY to the symmetry program. It does NOT mean
  bwcutoff is inert for gForceBW=0 at myamp.f — Regime A (Les Houches tag + s-hat gate)
  uses bwcutoff unconditionally for ALL legs at myamp.f, regardless of gForceBW.
- Three distinct hardcoded margins now mapped across the LO BW machinery:
  **bwcutoff** (forced legs), **5σ** (cut_bw enforcement / set_peaks grid / failConfig
  conflicted-non-forced), **3σ** (BW_Conflict's `+3d0*prwidth` conflict mass bound — unique
  to this file).

## Boundary
- LO only. The NLO symmetry program `Template/NLO/SubProcesses/symmetry_fks_v3.f` has
  ZERO bwcutoff/gForceBW/failConfig/bw_conflict (grep = 0) — FKS symmetry is
  amcatnlo/fks territory.
- `idenparts` (the identical-particle BW selection) is `Template/LO/SubProcesses/idenparts.f`
  — a separate file; this page owns only the bwcutoff/gForceBW windows in the symmetry program.
- *What configs get dropped for a given process* (the runtime symfact.dat content / channel
  count) is a phase-space/integration outcome — a runtime prediction, NOT probed here.

## Caution (source-visible, not probed)
- A forced-BW (`$$`/decay-chain) config that is kinematically impossible at the bwcutoff
  window is silently pruned by failConfig at symmetry time — no error, just absent from
  symfact.dat. Lowering bwcutoff narrows this window and can drop MORE configs. Source-visible;
  the per-process channel-count effect is a runtime quantity, not probed here (expensive probe).
