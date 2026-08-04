---
description: A hadronic initial state where the PDF or the factorization/renormalization scale is a choice you must defend.
---

# PDF & scale configuration — fan-out and owner map

A "configure the PDFs and factorization/renormalization scales" request looks like one topic but spans the input-state (hadronic-beam) and scale axes, which several slices own. Route each sub-question to its owner; do not answer the bulk from scales-pdf alone.

## Owner map (route each sub-question here)

- **PDF selection + all LO scale run_card params** → **ma-scales-pdf-consultant** (the anchor). `pdlabel`/`lhaid`, built-in vs `lhapdf` mode, `lpp`/`pdlabel` coherence, `fixed_ren_scale`/`fixed_fac_scale`, `scale`, `dsqrt_q2fact1/2`, `dynamical_scale_choice` (LO formula bodies in LO `setscales.f`), `scalefact`, per-beam `pdlabel1/2` + `fixed_fac_scale1/2`, and the PDF-driven αs override on the run side (`setrun.f`/`pdfwrap.f`).
- **NLO scale run_card surface** → **ma-amcatnlo-consultant**. `mur_over_ref`/`muf_over_ref` (NLO analogues of LO `scalefact`, which is absent at NLO), `reweight_scale`, `rw_rscale`/`rw_fscale`, the NLO `dynamical_scale_choice` allowed list + NLO `setscales.f` sentinels. (LO/NLO scale divergence: see `runcard-lo-nlo-value-divergence.md`.)
- **Scale/PDF variations & uncertainties** → **ma-systematics-consultant**. `use_syst`, `systematics_program`/`systematics_arguments` (LO), `reweight_scale`/`rw_rscale`/`rw_fscale` variation *emission* (the NLO run_card *param* is amcatnlo; the reweight *machinery* is systematics), PDF error sets, the lhapdf6 and OLP=MadLoop gates.
- **4F/5F flavor scheme — MODEL side** → **ma-model-loader-consultant**. Whether `sm-no_b_mass` vs `sm` puts b in the default `p`/`j` label (governs which quarks are in the beam content). The decision is an exact string test `b['mass'] == 'ZERO'`, NOT a mass threshold.
- **4F/5F flavor scheme — RUN_CARD side** → **ma-kinematic-cuts-consultant** owns `maxjetflavor` (light-jet-vs-b-jet cut classification); read the registered default at its `banner.py` registration, auto-bumped upward by the beam-driven auto-set when b is in the beam.
- **LHAPDF library install** → **ma-installation-consultant** (`install lhapdf6`/`lhapdf5`, case-sensitive tokens; installs the *library*, not PDF sets).
- **LHAPDF config key** → **ma-interface-consultant** (`mg5_configuration.txt` key resolution; the operative key is bare `lhapdf`, `lhapdf_py3` is promoted into it).
- **alpsfact** → **ma-matching-consultant** (MLM-only, `ickkw>0`).
- **param_card αs storage** → **ma-param-card-consultant** (SMINPUTS[3] external param, superseded run-side for PDF beams).

## Dispatch order

scales-pdf first (it anchors the bulk and its returns tell you which secondary slices the input actually implicates), then fan the secondaries the spec names in parallel. A bare "what PDF/scale should I use" with no NLO, no flavor-scheme, no uncertainty ask collapses to scales-pdf alone.

## Doc-myth traps (common write-ups get these wrong; verify against source)

- **`dynamical_scale_choice=10` ≠ "geometric mean of masses".** At LO it runtime-`stop`s (no Fortran branch); at NLO it is the **user-defined scale hook**. See `runcard-lo-nlo-value-divergence.md`.
- **`nn23lo1` "lhaid" ambiguity is a category error, not a contradiction.** The banner writes a `pdfsup` bookkeeping ID (nn23lo1→247000, the LHAPDF id of that grid) when `pdlabel≠lhapdf`; the `lhaid` param (its default — read it in the run_card/banner.py) is consumed *only* in `pdlabel=lhapdf` mode. Both live in different fields, each correct in its own. Default LO PDF is the bundled nn23lo1 grid (αs=0.130), `lhaid` ignored.
- **`maxjetflavor`'s registered default is NOT "5 for sm-no_b_mass".** Read the registered default at its `banner.py` registration; the value 5 arises only via the beam-driven auto-set, never as the base default. And maxjetflavor sets *cut classification*, it does not make flavors massless.
- **The manual `define p = g u c d s u~ c~ d~ s~` for a 4F run is redundant** — default `sm` p/j already exclude b (the multiparticles_default.txt literal has no b). Harmless, not necessary.
- **The 7-point scale envelope is a POST-HOC choice, not a generation-stage filter.** Both the LO systematics module and the NLO `reweight_scale` compute the full 3×3=9 mur×muf grid; the 7-point envelope (dropping the two anti-correlated combos) is taken downstream at analysis time.
- **`lhapdf_py3` is not the operative config key** — every consumer reads bare `lhapdf`; `_py3` is promoted into it at config-reconcile time.
- **Editing param_card SMINPUTS[3] (αs) is a silent no-op for a PDF-beam collider run** — superseded by the PDF's fitted αs (gate: any `lpp!=0`, but `eva`/`iww`/`none` pass through). It IS operative for a no-PDF run (lpp=0, e.g. e+e−).
- **`alpsfact≠1.0` is silently reset to 1.0 under the LO default `use_syst=True`** — the live variation goes through `sys_alpsfact`; to use a nominal non-unit value set `use_syst=False`.

## Runtime confirmations still open (probe-candidates, not source-settled)

Left as named probe-candidates in the consultant subtrees (none block a source-grounded answer): live `install lhapdf6` dual-key writeback; the emitted per-event weight count for default `systematics_arguments`; the SMINPUTS[3]-edit σ-invariance check on a hadron-beam run.
