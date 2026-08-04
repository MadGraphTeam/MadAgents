---
description: maxjetflavor / asrwgtflavor run_card params — defaults read at their banner.py coordinates, auto-set from beam(=p/j) content at card-creation, NO PDF-nf coherence guard; 4FS/5FS consistency is physics-only.
---

# maxjetflavor / asrwgtflavor and the 4FS/5FS coherence question

All cites `$MADGRAPH_INSTALL/madgraph/various/banner.py` unless noted (v3.7.1).

## maxjetflavor (RunCardLO and RunCardNLO)
- Default read fresh at LO `:4424` `add_param("maxjetflavor", ...)` (visible) / NLO `:5736` `add_param('maxjetflavor', ..., hidden=True)`.
- **Auto-set at card-CREATION time** (`create_default_for_process`), not at parse/read. LO `:4807-4810`; NLO `:6047-6048`:
  `maxjetflavor = max([4]+[abs(i) for i in beam_id if -7<i<7])` — floor 4, raised to the highest quark PDG appearing among initial-state legs.
  Gated by `if any(i in beam_id for i in [±1..±5,21,22])` (`:4807`). `beam_id` is the set of initial-state leg PDGs accumulated over the expanded `proc_def` (`:4791-4798`) = the **content of the `p`/`j` multiparticle** after expansion.
  → With b IN the beams (5FS, b massless → b∈p, PDG 5 present) auto-set gives **5**; with b absent (4FS) it stays **4**. So "typically 4 or 5 for pp" is correct, and the 4-vs-5 outcome is driven entirely by whether ±5 is in the beam content.
- **Whether b is in `p`/`j` (mass-driven, massless→in) is model-loader's `add_default_multiparticles`, NOT this slice.** maxjetflavor only READS the resulting beam_id.
- Guards (`check_validity`): `:4507` `>6 → InvalidRunCard`; `:4556-4557` `==6 with ickkw>0 (matching) → InvalidRunCard`. (The =6+matching guard is kinematic-cuts consultant's flagged item.)
- Runtime consumers: `jet_id=[21]+range(1,maxjetflavor+1)` (`:4994`); PDF/cut jet classification `:5080`; Fortran `Template/LO/SubProcesses/setcuts.f:217-222` (b-jet vs light-jet split), `cuts.f:1107`, `reweight.f:194`; MLM PY8 `JetMatching:nQmatch` / `Merging:nQuarksMerge` (`madevent_interface.py:4460,4535`).

## No PDF-flavor-scheme coherence guard (verified)
- maxjetflavor is derived from **beam(=p/j) content**, never from the PDF set's internal nf. There is **NO source-level check** cross-validating maxjetflavor against the PDF's flavor scheme (e.g. 5F-PDF + maxjetflavor=4). PDLabelBlock coherence (`pdlabel-coherence.md`) governs only the pdlabel1/2 triple, not nf. grep for pdf/flavor-scheme coupling in banner.py → none; the ONLY maxjetflavor guards are `:4507` (>6) and `:4556` (=6+matching).
- Therefore the "flavor scheme must be consistent across p/j-def, maxjetflavor, and PDF set" rule is a **PHYSICS consistency requirement with no code guard**. MG5 will run a 5F-PDF with maxjetflavor=4 (or vice-versa) silently, wrong results, no warning. (Instance of parser-vs-fortran-mismatch class: no guard, not even a Python-layer one.)

## asrwgtflavor (LO / MLM only)
- Default read fresh at `:4290` `add_param("asrwgtflavor", ..., hidden=True, comment='highest quark flavor for a_s reweighting in MLM')`. Rendered comment `:3989`.
- **Auto-set to `= maxjetflavor`** at card creation `:4810` (LO only; the NLO auto-set block `:6047-6048` sets maxjetflavor but NOT asrwgtflavor — asrwgtflavor is not an NLO param).
- Consumed in `Template/LO/SubProcesses/reweight.f:216` for the α_s reweight in MLM matching: `irfl.gt.max(asrwgtflavor,maxjetflavor)`.
- **Semantics are MLM-matching-owned** (matching consultant); this slice confirms only the run_card default(5)/auto-set(=maxjetflavor)/α_s-reweight-nf mechanics. A manual "set maxjetflavor=4 for 4FS" is already handled by the auto-set (=maxjetflavor=4 in 4FS).

## External / gap
- LHAPDF set identity (e.g. `lhaid 320500` ↔ a named NNPDF nf_4 set) is in the LHAPDF index, EXTERNAL to MG5 source — not verifiable here. Whether a given lhaid is 4F or 5F cannot be read off MG5 code; it is the user's responsibility (no guard, per above).
