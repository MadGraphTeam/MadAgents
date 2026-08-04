---
description: Ordered jet/lepton-pt cuts with jetor AND/OR (cutuse), staged running-HT cuts (ht2/3/4min), and the two WBF/VBF rapidity-gap cuts — cuts.f enforcement + setcuts.f mapping
---

# Ordered-pt, staged-HT, and WBF cuts — cuts.f enforcement + setcuts.f mapping

Source: `$MADGRAPH_INSTALL/Template/LO/SubProcesses/cuts.f` (:518-1095) and
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/setcuts.f` (:488-517). MG5_aMC v3.7.1.
This is the jet/HT/ordered-pt/WBF region that cuts-f-filter.md only sketches as "step 15".
Run-card registration of all params: banner.py:4383-4419 (runcard-cut-params.md).

## Jet array construction (cuts.f:521-535)
- `njets`/`ptjet` are filled from `is_a_j` only (light jets); `is_a_b` go into a SEPARATE
  `nheavyjets`/`ptheavyjet` (cuts.f:526-533). So the ordered-jet-pt cuts (ptj1..4min) and
  the jet-HT cut (htjmin) act on LIGHT jets only — a b that is_a_b is NOT in ptjet.
  Heavy jets enter only the INCLUSIVE HT sum (ihtmin), never the ordered ptj or htjmin.
- The KT_DURHAM block (:542-559) then RE-USES `njets`/`PJET` for the merging-cut PDG set
  (`is_pdg_for_merging_cut .and. .not.from_decay`) — a different array, scoped to that block.

## Ordered jet-pt cut + jetor AND/OR (cuts.f:816-871; setcuts.f:488-509)
- Existence guard (:817-824): too-few-jets vs ptj1min..ptj4min/htjmin -> reject.
- Jets sorted descending by pt (:827-835), then top-`min(njets,4)` checked against
  `ptjmin4(i)`/`ptjmax4(i)` = `ptj{i}min`/`ptj{i}max` (setcuts.f:488-496).
- **`jetor` prescription** (setcuts.f:509 `jetor = cutuse.eq.0`):
  - `cutuse=0` (DEFAULT) -> `jetor=.true.` -> **OR**: `notgood = .false. .or. (any ordered jet
    fails its window)` (cuts.f:851-855). If ANY of the top-4 jets is outside its
    [ptjNmin, ptjNmax] window, the event is REJECTED.
  - `cutuse=1` -> `jetor=.false.` -> **AND**: `notgood = .true. .and. (every jet fails)`
    (cuts.f:857-862). The event is rejected only if ALL of the top-4 jets are outside their
    windows; if even one jet passes, the event is kept.
  - `cutuse` has NO inline comment in banner.py (:4391) and NO check_validity logic — its
    entire semantics live in `jetor=cutuse.eq.0`. This is the non-obvious bit: `cutuse`
    flips ordered-jet-pt between "all must pass" and "at least one must pass".

## Staged running-HT cuts (cuts.f:876-913; setcuts.f:498-507)
Two distinct HT notions, both on the sorted light jets:
- `htj` = running sum of the top-i jet pts (:876-879). As each jet is added, for i=2..4 it is
  checked against `htjmin4(i)`/`htjmax4(i)` = `ht{i}min`/`ht{i}max` (setcuts.f:498-504; array
  dimensioned `(2:4)`, so ht2/ht3/ht4 only — there is no ht1). So `ht2min` = min HT of the two
  hardest jets, `ht3min` = of the three hardest, etc. (:882-889).
- After all jets summed, total `htj` checked against `htjmin`/`htjmax` (:892-896) — the sum of
  ALL light jets. `inclht = htj` (:898).
- **Inclusive HT** (ihtmin/ihtmax, `inclHtmin/inclHtmax`, setcuts.f:506-507): adds the heavy-jet
  pts (`ptheavyjet`, i.e. is_a_b jets) to `inclht` (:902-906), then checks ihtmin/ihtmax
  (:908-913). So ihtmin includes b-jets; htjmin does NOT. (Inclusive HT comment "incl heavy"
  in runcard-cut-params.md is precise: heavy = the is_a_b heavy jets, NOT >20 GeV resonances —
  those have do_cuts=.false. and never reach is_a_b.)

## Ordered lepton-pt cut (cuts.f:918-974; setcuts.f:514-522)
Same shape as ordered jets but ALWAYS OR-logic (no jetor analogue): `notgood=.false.` then
`.or.` over the top-`min(nleptons,4)` against `ptlmin4(i)`/`ptlmax4(i)` = `ptl{i}min`/`ptl{i}max`
(cuts.f:957-965). Existence guard at :934-941. Leptons = is_a_l (e/mu/tau), sorted descending.

## xptX special cuts (cuts.f:979-1030)
"At least one of class X with pt > xptX": for xptj/xpta/xptb/xptl, take `max` pt over the class
and reject if below the threshold (OR-of-one logic). These are the cuts the setcuts.f ERROR
TRAPS auto-zero when the class is absent (pdg-cuts-and-smin.md §5, cut-precondition-auto-disable.md).

## WBF/VBF cuts — TWO types, both opposite-hemisphere (cuts.f:1031-1095)
Active iff `XETAMIN>0 .or. DELTAETA>0` (:1054). Finds the 2 HARDEST light jets (hardj1,hardj2,
:1058-1072). If <2 jets (`hardj2.eq.0`), `goto 21` BYPASSES the cut AND the photon-isolation
block below it (jumps to the post-cut scale-setting at :1234) — i.e. a <2-jet event passes VBF
silently AND skips photon iso. (Runtime ignore is handled separately by the setcuts.f ERROR TRAP
that zeroes xetamin/deltaeta when <2 jets — pdg-cuts-and-smin.md §5.)
- **Type I — XETAMIN (rapidity-gap, :1078-1083)**: reject unless BOTH hardest jets have
  `|rap| >= xetamin` AND they are in OPPOSITE hemispheres (`rap(j1)*rap(j2) < 0`).
- **Type II — DELTAETA (:1088-1091)**: reject unless `|rap(j1) - rap(j2)| >= deltaeta`.
  NON-OBVIOUS: the Type-I cut block (:1078-1083) is NOT inner-gated on `xetamin>0` — it runs
  whenever the outer IF (`xetamin>0 .OR. deltaeta>0`, :1054) fires. So setting deltaeta alone
  (xetamin=0) STILL applies Type I's opposite-hemisphere reject `rap(j1)*rap(j2)>0` (the
  `|rap|<xetamin` tests are inert at xetamin=0, but the hemisphere test is live). Net: a
  deltaeta-only run silently also requires the two hardest jets in opposite hemispheres. The
  source comment at :1040-1044 lists `rap(j1)*rap(j2)<0` as a Type-II step, consistent with this
  joint behaviour. Both cuts act on the 2 hardest LIGHT jets only.

## Cautions
- htjmin / ptj1..4min act on LIGHT jets (is_a_j) only; b-jets contribute to inclusive HT
  (ihtmin) and to drbb/mmbb but NOT to htjmin or ordered ptj. A b-rich final state will see
  ihtmin behave very differently from htjmin.
- `cutuse=1` (AND) is a "keep if ANY ordered jet passes" relaxation — easy to misread as
  tightening. Default cutuse=0 is the strict "all must pass" (OR-reject).
- The VBF `goto 21` at :1074 short-circuits PAST photon isolation for <2-jet events. For a
  VBF+photon process this means a sub-2-jet event is not photon-isolated. Edge case; pointer.
- There is no ht1min (array starts at 2); ht{i} is the HT of the i hardest jets, i in 2..4.
