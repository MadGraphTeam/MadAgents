---
description: The three LO callers of cut_bw (cuts.f/cluster.f/unwgt.f) and its dual nature — cut-return (event cut) vs OnBW side-effect populator (clustering + LHE write), v3.7.1
---

# cut_bw callers + dual nature (cuts.f / cluster.f / unwgt.f)

The earlier pages (bw-onshell-test-cutbw.md etc.) describe what `cut_bw` computes
*internally*. This page records *who calls it and why* — the invocation surface — which
turns out to matter because `cut_bw` is used in two completely different ways: as a return
value (an event cut) and as a side-effect that populates the `OnBW` array other code reads.
Cites `$MADGRAPH_INSTALL/Template/LO/SubProcesses/`, v3.7.1.

## The shared OnBW array (how the side-effect propagates)
- `myamp.f:53-54`: `logical OnBW(-nexternal:0)` in `common/to_BWEvents/ OnBW`.
- `cluster.f:401-402`: same declaration + same common block `to_BWEvents`.
- `addmothers.f:68-69` (`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/addmothers.f`,
  copied into each `P_*` at output): same declaration + same `common/to_BWEvents/`.
- => `cut_bw` writes `OnBW(i)` (myamp.f:147,161,165,168,173,176 — the idenpart block,
  bw-onshell-test-cutbw.md). The block `common/to_BWEvents/` is shared by **exactly three
  files — myamp.f, cluster.f, and addmothers.f** (`grep -rln to_BWEvents Template/LO/` =
  cluster.f + myamp.f only, plus the iolibs `addmothers.f` template; **unwgt.f has ZERO
  `OnBW`/`to_BWEvents` references**, verified). RE-GREP GUARD: a case-INSENSITIVE
  `grep -nciE OnBW unwgt.f` returns **1**, but that single hit is the *comment word* "onbw"
  in the comment at unwgt.f:736 ("recall onbw since that might have configured onBW for the
  wrong config") — case-sensitive `grep OnBW`/`grep to_BWEvents` on unwgt.f = **0** (no
  variable use, no common block). Do not misread the comment-word count-1 as contradicting
  the ZERO-references claim. The two consumers reach OnBW by DIFFERENT routes:
  - **cluster.f reads OnBW directly** through the shared block (declares it itself, l.401-402).
  - **The unwgt.f path reaches OnBW INDIRECTLY:** unwgt.f does *not* share the block. At
    unwgt.f:737 it re-populates OnBW via `call cut_bw(p)`, then unwgt.f:738 calls
    `addmothers`, and it is `addmothers` (which DOES share `to_BWEvents`) that reads OnBW
    (`addmothers.f:253: if(ickkw.eq.0.and.OnBW(i))`). So the common block is the channel by
    which cut_bw's side-effect reaches cluster.f, but NOT unwgt.f: unwgt.f never touches the
    block; addmothers is the reader on that path.

## Three callers, two roles

### 1. cuts.f:509 — the EVENT CUT (return value used)
- `pass_bw=cut_bw(p)` (cuts.f:509), inside the MadWeight tag pair
  `C $B$DESACTIVATE_BW_CUT$B$` (505) … `C $E$DESACTIVATE_BW_CUT$E$` (516). These tags let
  MadWeight strip the whole BW-cut block; the `$..._BW_CUT$` token is a **code-stripping
  marker, NOT the bwcutoff parameter** (do not confuse with run-card bwcutoff or MadSpin's
  `BW_cut`).
- cuts.f:510-515: `if (pass_bw .and. .not.CUTSPASSED) then passcuts=.false. ... return`.
  So the cut only bites when `CUTSPASSED` is false. `CUTSPASSED` is reset to `.FALSE.`
  immediately after (cuts.f:517), i.e. it is a guard set elsewhere; the comment "JA 4/8/11
  always check pass_bw" flags that this branch is always evaluated. This is the ONLY caller
  that consumes cut_bw's `.true./.false.` return as a cut.

### 2. cluster.f:423 — OnBW POPULATOR for clustering (return DISCARDED)
- `call cut_bw(p)` (cluster.f:423, a `call`, not an assignment — return thrown away),
  inside MadWeight tags `C $B$ ONBW $B$` (422) … `C $E$ ONBW $E$` (425).
- Immediately after: `if(OnBW(i))then nbw=nbw+1; ibwlist(1,nbw)=icl(i); ibwlist(2,nbw)=i;
  isbw(icl(i))=.true.` (cluster.f:424-431). So cut_bw is invoked purely for its
  **OnBW side-effect**, then cluster.f enumerates the on-shell resonances into `ibwlist` /
  flags `isbw`. The cut decision is irrelevant here; only which legs are on-BW matters.
- Purpose (which topologies carry an on-shell s-channel) is phase-space/clustering
  territory; the *call into cut_bw* is the seam this slice owns.

### 3. unwgt.f:737 — OnBW RE-CONFIG before LHE resonant-mother write (return DISCARDED)
- `call cut_bw(p)` (unwgt.f:737), again a bare `call`. Comment unwgt.f:735-736:
  *"Add info on resonant mothers / recall onbw since that might have configured onBW for the
  wrong config (check tt~a ,t >... for checking impact"*.
- Followed by `call addmothers(...)` (unwgt.f:738). So cut_bw is re-invoked to **re-populate
  OnBW for the selected config** right before `addmothers` writes resonant-mother info into
  the LHE event. The source comment is explicit that an earlier cut_bw call may have left
  OnBW set for a different config, so it must be recomputed here.

## Why this is load-bearing (the non-obvious part)
- `cut_bw` is NOT just a cut. Its `.true./.false.` return is used as a cut at exactly ONE
  site (cuts.f:509). At the other two sites the return is discarded and the function is
  called solely to write the shared `OnBW(-nexternal:0)` array, which then drives (a)
  clustering's on-BW resonance list (cluster.f ibwlist/isbw, read directly via the block) and
  (b) the LHE resonant-mother record. For (b), note unwgt.f itself never reads OnBW: unwgt.f
  *re-runs* cut_bw (to recompute OnBW for the selected config) then calls `addmothers`, and it
  is `addmothers` — sharing `to_BWEvents` — that reads the recomputed OnBW
  (`addmothers.f:253`, gated on `ickkw.eq.0`) and turns it into the resonant-mother record.
- Consequence for reasoning: a change to bwcutoff / the on-shell test does not only change
  *which events are cut* (cuts.f) — it also changes *which resonances are flagged on-BW in
  the written LHE event* (the unwgt.f → addmothers path) and *which topologies clustering
  treats as on-shell* (cluster.f). The first onshell definition's idenpart OnBW logic
  (myamp.f:146-178) feeds the LHE write; the second (enforcement) onshell + lbw drives the
  cuts.f cut. Both live in one function but surface at different callers.

## Routing notes
- `addmothers` internals (how OnBW becomes the LHE mother record), clustering topology
  selection, and `ibwlist`/`isbw` consumption are phase-space / event-writing territory —
  this page owns only the call *into* cut_bw and the OnBW common-block seam.
- The role-card "`BW_cut` sentinel": there is **no `BW_cut` token in LO Template or
  banner.py** (grep-confirmed; the only `_BW_CUT_` hits are the MadWeight
  `$DESACTIVATE_BW_CUT$` strip-tags above). MadSpin's `BW_cut` lives in
  `$MADGRAPH_INSTALL/MadSpin/decay.py` + `interface_madspin.py` — that is the MadSpin slice,
  not LO BW. Recorded so I don't hunt LO for it again.

## Caution
- Static source facts (which caller, which line, return-used-vs-discarded, common-block
  sharing — all grep/sed-confirmed). The runtime *effect* of the unwgt.f re-config on a
  specific LHE event's mother record is a runtime prediction, not probed here.
