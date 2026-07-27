---
description: EFT-NLO source-visible specifics — the TIR HEFT-vertex flag for CutTools limitations, and version-specific EFT/SMEFT/HEFT bug history in UpdateNotes.txt.
---

# EFT-NLO source-visible specifics

## TIR HEFT-vertex flag (CutTools limitation routing)
`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/loop_optimized/TIR_interface.inc`:
- `LOGICAL HAS_AN_HEFT_VERTEX(NLOOPGROUPS)` declared at line 475; comment (line 474):
  "This list specifies what loop involve an Higgs effective vertex so that CutTools limitations can be
  correctly implemented." Populated by template substitution `%(has_HEFT_list)s` (line 476).
- Passed per-loop into `CALL DETECT_LOOPLIB(LIBNUM,NLOOPLINE,RANK,complex_mass,
  HAS_AN_HEFT_VERTEX(loop_ID),MAX_SPIN_CONNECTED_TO_LOOP,LPASS)` at lines 514 (QP path) and 531 (DP path).
- `DETECT_LOOPLIB` is itself generated (no static .f under template_files — only this .inc references it);
  the flag steers reduction-library selection so loops with an effective hgg vertex avoid a library that
  can't handle them. Loop-library detection internals are nlo-mechanics territory, not EFT slice.

## EFT order flows through the NLO counterterms (SMEFTatNLO)
The NLO counterterm couplings carry the EFT power-counting order at the SAME per-insertion value as the
tree couplings, so an `NP==v` constraint is consistent across LO + R2/UV pieces:
- `$MADGRAPH_INSTALL/models/SMEFTatNLO/CT_couplings.py` — the CT couplings are tagged `'NP'`; sampled orders
  `order = {'NP':2,'QCD':2,'QED':1}` (line 14), `{'NP':2,'QED':2}` (lines 18,22). Same `NP:2` increment
  as the tree `couplings.py` (see bundled-eft-models.md). So the EFT increment is +2 in counterterms too.
- `NP` is NOT a literal in `CT_vertices.py` — counterterm vertices reference couplings by name and the
  order flows from the referenced CT coupling, not from the vertex entry.
Implication: EFT power-counting truncation (`NP==2`, `NP^2==4`) applies uniformly to the loop counterterm
contributions, not just the tree amplitude. (R2/UV declaration mechanics themselves are nlo-model slice;
this only records that the EFT order is present on them.)

## UpdateNotes.txt EFT-NLO history (version-specific — re-grep per version)
Search `SMEFT|EFT|dim6|HEFT|EWdim6` in `$MADGRAPH_INSTALL/UpdateNotes.txt`. Notable entries (v3.7.1 file):
- line 262-263: "Allow to have EFT operator to run for some special UFO model (quite restricted class of
  running are supported -- corresponding to EFT running --)" — EFT RGE running support, restricted.
- line 475: "Fixing issue with model (like SMEFTatNLO) where some interactions where using more than 9
  coupling" — SMEFTatNLO many-coupling-per-interaction fix.
- line 579: NLO multi-channel enhancement-factor fix "only appeared in BSM theories (or EFTs)".
- line 954: "Change in LO matching for HEFT (or any model with hgg vertex) in the way to flag jet that
  should not take part in the matching/merging procedure."
- line 1283: "Fixed a small bug in EWdim6 which was removing a coupling in AZHH interaction."
- line 1687/1689: EWdim6 updated to snowmass paper (3 more operators); use `import model EWdim6-full`.
- line 1402/1938: HEFT merging-crash fix; heft-load crash fix.

These are version-specific; treat as troubleshooting pointers, confirm against the install's own file.
