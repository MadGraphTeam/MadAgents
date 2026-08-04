---
description: detect_card_type — tag strings that classify a file as delphes_card / delphes_trigger / pgs_card; missing-comma bug makes ParticlePropagator/<mg5proccard> dead tags
---

# Card-type recognition (interface side)

`$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py`, `detect_card_type` (line 1168;
note a second `detect_card_type` method exists at 7726). Docstring lists supported cards at
lines 1170-1190; `to_search` tag list 1197-1227; classification 1230-1258. MadGraph identifies an uploaded/edited card by substring match,
not by filename — relevant when a user supplies a renamed card.

## Tags that route to MY slice's cards
- `delphes_card.dat` ← any of `ExecutionPath`, `Treewriter`, or `CEN_max_tracker`
  (1234-1237). `ExecutionPath`/`Treewriter` are delphes3 markers; CEN_max_tracker is
  delphes2-era. (`ParticlePropagator` is also intended but is a DEAD tag due to the
  missing-comma bug below — do not rely on it.)
- `delphes_trigger.dat` ← `#TRIGGER CARD` (1249-1250). This is why the trigger template's
  first line is `#TRIGGER CARD  # DO NOT REMOVE THIS IS A TAG!`.
- `pgs_card.dat` ← `parameter set name` OR `muon eta coverage` (1251-1254). Both appear in
  the pgs card templates.

## Caution (source bug, benign — but NOT for the reason you'd guess)
Line 1198-1199: the `to_search` list has a missing comma after `'<mg5proccard>'`, so it and
`'ParticlePropagator'` string-concatenate into ONE element `'<mg5proccard>ParticlePropagator'`.
The list is OR-joined into a regex and matched with `re.findall` (1230). `findall` emits only
whole-alternative matches, so the concatenated literal matches ONLY text containing
`<mg5proccard>ParticlePropagator` verbatim — which never occurs. Verified (v3.7.1) with a
standalone script: `<mg5proccard>` alone → NO match; a bare `ParticlePropagator` token → NO
match. So the substrings do **NOT** match individually.

Why it's still benign:
- delphes_card recognition survives via the OTHER tags `ExecutionPath` / `Treewriter` /
  `CEN_max_tracker` (separate list elements 1200-1202), which the default Delphes card
  contains (`ExecutionPath`, `TreeWriter`×2 confirmed in delphes_card_default.dat). Standalone
  `ParticlePropagator` is now effectively a DEAD tag.
- banner recognition survives via `<MGVersion>` (separate element 1197). The
  `'<mg5proccard>' in text` branch at line 1232 is now DEAD (regex can never emit that token).
Do not "fix" expecting a behavior change for real cards, but know the two named tags above are
the live ones, not `ParticlePropagator`/`<mg5proccard>`.
