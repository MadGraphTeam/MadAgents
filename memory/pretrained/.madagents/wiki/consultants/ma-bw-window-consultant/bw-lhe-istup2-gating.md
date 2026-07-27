---
description: Whether LHE intermediate-record (ISTUP=2) writing is gated by the bwcutoff on-shell window — YES for LO ickkw=0, via the "LesHouches" onshell → OnBW → addmothers status-2/3 path, v3.7.1
---

# LHE ISTUP=2 gating by the bwcutoff window (myamp.f → addmothers.f)

MG5 writes an intermediate s-channel particle to the LHE with ISTUP=2 only when it is
on-shell — its invariant mass within roughly M ± bwcutoff × Γ. This conclusion holds for
the default LO path (ickkw=0): the status-2 record IS per-event gated at write time by an
on-shell test built on
bwcutoff — but the stated criterion is incomplete (Γ_eff not raw Γ; narrow-resonance
gate; idenpart de-dup; different path when matching). bwcutoff does NOT merely control PS
mapping / SPROP classification; it directly governs the written status code.
Cites `$MADGRAPH_INSTALL`, v3.7.1.

## The write-path (two files, one seam)

### 1. myamp.f — the "LesHouches" onshell sets OnBW (Template/LO/SubProcesses/myamp.f)
There are TWO distinct `onshell` variables in `cut_bw`:
- **FIRST (`:129-140`, comment `:129` verbatim "Here we set if the BW is 'on-shell' for
  LesHouches")** — this is the one that feeds the LHE write:
  ```
  onshell = (abs(xmass - prmass) .lt. bwcutoff*prwidth_tmp        ! :136-137
            .and. (prwidth_tmp/prmass .lt. 0.1d0                  ! narrow gate :138-139
                   .or. gForceBW(i,iconfig).eq.1))
  ```
  with `prwidth_tmp = max(prwidth, prmass*small_width_treatment)` = Γ_eff (`:131-135`).
  If onshell → `OnBW(i)=.true.` (`:147`), then the idenpart identical-daughter block
  (`:148-178`) can CLEAR OnBW again (identical final-state daughter, or forced-daughter
  de-dup). `gForceBW=2` on-shell forbidden s-channel short-circuits to `cut_bw=.true.`
  (`:141-145`, event cut, not a write).
- **SECOND (`:186-193`, comment "Here we set onshell for phase space integration")** —
  `gForceBW=1 → bwcutoff` window, else `5σ` window; combines with `lbw(nbw)` to set the
  `cut_bw` EVENT-CUT return. Does NOT touch OnBW / the LHE record.

So the record-write gate and the phase-space/event-cut gate are computed by two separate
onshell tests in the same function; only the FIRST (bwcutoff + narrow gate) drives ISTUP=2.

### 2. addmothers.f — OnBW → status 2 vs 3, status-3 dropped
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/addmothers.f` (copied into each P_*):
- `:253` `if(ickkw.eq.0.and.OnBW(i)) then jpart(6,i)=2` (status 2 = "resonance whose mass
  should be preserved", `nres=nres+1`) `:255-256`.
- else if `ickkw.gt.0`: status driven by **`isbw(idij(i))` from clustering** (`:257-264`),
  NOT by OnBW — a DIFFERENT path when matching is on.
- else (`ickkw<0` or not-OnBW): `jpart(6,i)=3` "Propagator for documentation only - not
  included" (`:265-267`).
- `:339-357`: only `jpart(6,i).eq.2` s-channels get a slot `ito(i)=2+ires` (`:346-348`);
  everything with status 3 gets `ito(i)=0` and is skipped by `if(ito(i).le.0) cycle`
  (`:362`) in the shift loop → **status-3 propagators are NOT written to the event**.
- `jpart(6,i)` is the ISTUP status code emitted for the intermediate line.

## Net answer
- **Gated at write time: YES.** For LO ickkw=0, an intermediate s-channel appears in the
  LHE with ISTUP=2 iff `OnBW(i)` is set, and OnBW is set by the bwcutoff×Γ_eff window
  (myamp.f:136-140). The status-2 record does NOT simply follow the diagram's resonant
  structure independent of a per-event cutoff — it follows OnBW per event. Changing
  bwcutoff changes which resonances are written status-2. (This refutes the "bwcutoff only
  controls PS mapping, record follows diagram structure" alternative for this path.)
- **The diagram structure sets the CANDIDATE set** (which propagators i are s-channel BW at
  all: `prwidth(i,iconfig)>0` + iforest topology, myamp.f loop `:118`+); per-event
  on-shellness then selects which candidates get written. Whether the chain-decay structure
  alone fixes the candidate/gForceBW set is chain-decay's slice (premise here).
- **The stated criterion "within M ± bwcutoff × Γ" is INCOMPLETE:**
  1. Window uses Γ_eff = max(Γ, M·small_width_treatment), not raw Γ.
  2. Additional narrow-resonance gate: Γ_eff/M < 0.1 required (unless gForceBW=1). A BROAD
     resonance (Γ/M ≥ 0.1) is never flagged OnBW no matter how on-shell → never ISTUP=2
     unless forced. So "within window" ≠ "written".
  3. idenpart de-dup (myamp.f:148-178) can clear OnBW for a within-window resonance.
  4. Matched runs (ickkw>0) use isbw/clustering, not this OnBW window, at addmothers:257-264.

## Caution
- All static source (line-verified). The runtime effect on a specific event's ISTUP=2 lines
  is a prediction, not probed. The unwgt.f:737 re-`call cut_bw(p)` before
  addmothers (bw-cutbw-callers.md) recomputes OnBW for the SELECTED config — so the OnBW
  that reaches addmothers is the selected-config one, not a stale earlier value.
- gForceBW provenance (decayBW.inc static) and lbw (runtime DeCode) — see
  bw-gforcebw-lbw-provenance.md; consumed read-only here.
