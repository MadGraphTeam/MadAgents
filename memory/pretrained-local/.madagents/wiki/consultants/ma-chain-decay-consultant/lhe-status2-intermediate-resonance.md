---
description: When an intermediate resonance is written to the LHE with status +2 (ISTUP=2) at LO madevent — gated by the runtime OnBW test in cut_bw, NOT by decay-chain syntax. decayBW.inc/gForceBW MODIFIES that test (forces narrow-width bypass + cuts off-window events), it does not itself gate the status-2 write. Corrects the "status-2 only appears with decay-chain syntax" myth.
---

# LHE status-2 intermediate resonance — what my slice controls vs the runtime BW gate

Source: MG5_aMC v3.7.1, LO madevent template. This page nails the SEAM between the
decay-chain/gForceBW artefact (my slice) and the actual status-2 LHE write.

## The write happens at runtime in addmothers.f, gated by OnBW — not by decay-chain syntax
LHE event assembly: `write_leshouche` (Template/LO/SubProcesses/unwgt.f:463) calls
`cut_bw(p)` (unwgt.f:737) then `addmothers(...)` (unwgt.f:738) — comment "Add info on
resonant mothers". `addmothers` (madgraph/iolibs/template_files/addmothers.f) is where the
intermediate particle line and its status code are produced.

- An s-channel propagator slot `i` becomes a candidate only if `sprop(numproc,i,lconfig)>0`
  for the SELECTED config (addmothers.f:196) — i.e. the diagram/config chosen for THIS event
  carries that s-channel propagator (configs.inc structure; config selection = phase-space slice).
- **Status assignment (addmothers.f:253-268):** with matching OFF (`ickkw.eq.0`, the LO
  default):
  ```
  if(ickkw.eq.0.and.OnBW(i)) then
     jpart(6,i)=2      ! status +2, resonance whose mass is preserved
     nres=nres+1
  else
     jpart(6,i)=3      ! "Propagator for documentation only - not included"
  ```
- **Only status-2 propagators reach the LHE (addmothers.f:338-362):** the compaction loop
  gives a record position `ito(i)=2+ires` ONLY to `jpart(6,i).eq.2` slots (:346-348);
  everything else gets `ito(i)=0` (:350) and is skipped by `if(ito(i).le.0) cycle` (:362).
  So `npart = nexternal + nres`, and a status-3 propagator is dropped entirely (NOT written
  as a documentation line at LO madevent).

**Therefore the status-2 write is gated by `OnBW(i)`, a per-event runtime flag — not by the
presence of decay-chain (comma) syntax.**

## What sets OnBW — cut_bw (myamp.f), the runtime BW-window test (bw-window's slice; PREMISE)
`OnBW(i)` is set in `cut_bw` (Template/LO/SubProcesses/myamp.f, common `/to_BWEvents/` :53-54).
The on-shell test that flips OnBW true (myamp.f:136-147):
```
onshell = (abs(xmass - prmass) .lt. bwcutoff*prwidth_tmp
           .and. (prwidth_tmp/prmass .lt. 0.1  .or.  gForceBW(i,iconfig).eq.1))
if(onshell) ... OnBW(i)=.true.
```
Requires a BW propagator (`prwidth>0`, myamp.f:123 — so a zero-width propagator like the
photon is NEVER status-2) AND the reconstructed mass inside the `M ± bwcutoff·Γ` window.
The bwcutoff window value + small_width_treatment handling are **bw-window's slice** — taken
here as PREMISE. My slice's contribution is the role of `gForceBW`, below.

## What decayBW.inc / gForceBW ACTUALLY controls here (my slice)
decayBW.inc supplies `gForceBW(i,iconfig)` (see decayBW-artefact.md, onshell-flag-and-decayBW.md).
Comma decay-chain → `gForceBW=1` (onshell=True); arrow / plain cascade → `gForceBW=0`. Its
effect on the status-2 gate is TWO-fold and it MODIFIES the runtime test, it does not replace it:

1. **Narrow-width bypass (myamp.f:139):** the `.or. gForceBW(i,iconfig).eq.1` term lets a WIDE
   resonance (Γ/M ≥ 0.1) still qualify as on-shell → OnBW=true → status-2. Without gForceBW=1,
   a wide s-channel propagator can never be status-2 no matter how close to its pole.
2. **Off-window event CUT (myamp.f:179-183):** if `gForceBW=1` and the resonance is OUTSIDE the
   `bwcutoff·Γ` window, `cut_bw=.true.` → the ENTIRE event is rejected (returns). So a forced-BW
   resonance can never end up status-3: it is either on-shell (status-2) or the event is killed.

**Net (my slice's authoritative statement):** a comma-decay resonance (gForceBW=1) is written
status-2 in EVERY surviving event. A gForceBW=0 s-channel propagator is written status-2
CONDITIONALLY — only when it is a narrow (Γ/M<0.1) BW propagator that lands inside its
bwcutoff window for that event. decayBW.inc does not gate the write; it forces / widens the
gate for its own resonance and cuts off-window events for it.

## Corrections to the "status-2 only with decay-chain syntax" doc claims
- **"MG writes ISTUP=2 ONLY for decay-chain / resonant (comma) structure; decayBW.inc is the
  mechanism"** — FALSE as stated. Any narrow s-channel BW propagator in the selected config,
  on its mass window, is written status-2 with gForceBW=0 too. decayBW.inc is NOT the gate; the
  runtime OnBW/cut_bw window test (bw-window) plus config selection (phase-space) is. E.g. the
  ARROW form `p p > z > e+ e-` carries gForceBW=0 (decayBW-artefact.md) yet its Z, being narrow
  and on-pole, is written status-2 in on-shell events.
- **"Non-chain multi-diagram process (e+e- > mu+mu- via Z and γ) → no unique intermediate → no
  status-2"** — FALSE. Status-2 is per-event, per-SELECTED-config: an event integrated
  through the Z-exchange config with the Z on its window gets a status-2 Z; the photon config
  never yields status-2 (zero width). Config selection is phase-space's slice; the point is the
  outcome is runtime-kinematic, not "unique-intermediate" gated.
  **Durable (qualitative) fact:** a fully inclusive LO `e+ e- > mu+ mu-` (no comma, no arrow) at
  √s = M_Z writes a status-2 Z in the VAST MAJORITY of events (those where the reconstructed mass
  lands inside the Z BW-window); a small tail (γ-dominated / off-window) carries NO intermediate
  record — only the 4 external particles. This directly demonstrates the per-event on-shell gating
  above and refutes the "no unique intermediate → no status-2 for interfering Z/γ" model. The
  ON-vs-OFF-window SPLIT FRACTION is NOT durable — it is set by the bwcutoff value (bw-window's,
  version-dependent), the beam √s, and MC statistics; derive it per setup, do not cache a number.
  (A single probe at default bwcutoff put the on-window share near ~99%, illustrative only.) The
  reconstructed status-2 Z additionally carries SPINUP=9 (mother reconstructed, no MC helicity) —
  cross-reference only; SPINUP-value ownership is mc-integration's.
- **"Status +2 appears only with decay-chain syntax"** — FALSE; same reason.

## Caution resolved (the dispatch's explicit question)
"Intermediate written when on-shell, within BW window (M ± bwcutoff·Γ)": the WRITE is gated by
`OnBW(i)` (addmothers.f:253), whose value comes from the runtime BW-window test in cut_bw
(myamp.f:136-139) — a RUNTIME test, NOT the decay-chain/gForceBW structure. What decayBW.inc
(my slice) controls is only whether that resonance is FORCED (gForceBW=1: narrow-width bypass +
off-window event cut) vs left to the ordinary narrow+on-window test (gForceBW=0). So the correct
mental model is: writing status-2 = (config has the s-channel propagator) × (runtime BW-window
on-shell test) — with gForceBW=1 forcing/widening that test for the comma resonance.

## Boundary hand-offs
- bwcutoff window value, small_width_treatment, OnBW/cut_bw semantics — **bw-window**.
- Which config (lconfig/ipsel) is selected per event, sprop/configs.inc channel structure —
  **phase-space** (config content) / diagram-enumeration.
- The addmothers.f record compaction / LHE field writing itself — **output** (I cite it as the
  consumer; the status decision is what my slice traces to gForceBW).

## Runtime-confirmed
The gForceBW=0 corollary is durable (qualitative), not a hypothesis: a fully inclusive LO
`e+ e- > mu+ mu-` (gForceBW=0, no s-channel forcing) at √s = M_Z writes a status-2 Z in the
majority (on-window) events and no intermediate record in the off-window tail — see the second
correction bullet above. This settles "status-2 only with decay-chain syntax" as FALSE: the write
is the runtime OnBW/bwcutoff window test, and gForceBW=0 resonances are written status-2 whenever
narrow and on-window. The exact on/off-window split fraction is setup-dependent (bwcutoff, √s, MC
stats) — not cached; derive per setup.
