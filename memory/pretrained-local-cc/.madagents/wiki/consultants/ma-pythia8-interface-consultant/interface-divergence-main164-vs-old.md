---
description: The use_mg5amc_py8_interface flag makes MG emit a structurally different PY8 card for the default main164 path vs the old MG5aMC_PY8_interface path — name translation, SysCalc disabling, and gated matching steps. The deeper principle behind the per-facet interface notes.
---

# Interface divergence: main164 (default) vs old MG5aMC_PY8_interface

## Principle
The two PY8 driver paths are not just two executables steering the same card. The single boolean `use_mg5amc_py8_interface` (set by the `--old_interface` flag in `do_pythia8`, `madevent_interface.py:4635`) is threaded through `setup_Pythia8RunAndCard(..., use_mg5amc_py8_interface)` (`:4307`) and `PY8Card.write(..., use_mg5amc_py8_interface=)` (`banner.py:2174`) and makes MG emit a **structurally different card** for each path. When reasoning about *what ends up in the PY8 card*, always resolve which interface is in play first — the same run_card can yield different cards.

Boundary: this governs only what MG *writes* on the LO `do_pythia8` path. It does not govern PY8's own shower/MPI/hadronization (out of slice), nor matching-*scheme selection* (matching slice). NLO+PS uses a different driver (run_mcatnlo) — see shower-card-and-routing.md.

## Three divergence mechanisms

### 1. Card-write name translation (`banner.py:2165-2171`, applied at 2334/2367/2423)
`PY8Card.interface_to_164` dict (def at `:2165-2171`) is applied **only when `not use_mg5amc_py8_interface` AND `direct_pythia_input`** (`:2333-2334`, `:2366-2367`). do_pythia8 always passes `direct_pythia_input=True`, so on the LO handoff the `not use_mg5amc_py8_interface` condition is the operative one — but the full guard includes `direct_pythia_input`. Full map (probe-confirmed via `PY8Card.write`):
- `HEPMCoutput:file` -> `HepMC:output` (and main164 also emits `Main:HepMC=on`, `:2337-2338`/`:2370-2371`).
- `LHEFInputs:nSubruns` -> `Main:numberOfSubruns`.
- `SysCalc:fullCutVariation`, `SysCalc:qCutList`, `SysCalc:qWeed`, `SysCalc:tmsList`, `HEPMCoutput:scaling` -> commented out as `!... (not supported with 164)`.

So the entire `SysCalc:*` family AND `HEPMCoutput:scaling` are **structurally absent** from a main164 card even if set. `Main:HepMC`/`HepMC:output` are "only needed for main164" (`banner.py:2004-2008`, always_write_to_card=False).

### 2. Control-flow gating in setup_Pythia8RunAndCard
Several auto-derivations fire **only on `use_mg5amc_py8_interface AND run_card['use_syst']`** (MLM and CKKW branches both):
- MLM: `SysCalc:qWeed` (`:4422-4423`), `SysCalc:qCutList` (`:4425`, inner `use_syst` guard), `JetMatching:doVeto=False` (`:4452-4455`).
- CKKW: `Merging:applyVeto=False`, `Merging:includeWeightInXsection=False`, `SysCalc:tmsList` (`:4528-4554`).
On the default main164 path these are skipped — the systematics/qCutList/veto-on-driver machinery is an old-interface feature. (Even if computed, mechanism #1 would strip them on write.)

### 3. Executable + wrapper differences
- Default: `pythia8_path/share/Pythia8/examples/main164` (`:4650`); wrapper passes `-c` before the card (`:4734`). main164 not found -> warns and retries `--old_interface` (`:4654-4655`).
- Old: `mg5amc_py8_interface_path/MG5aMC_PY8_interface` (`:4644`); no `-c`; runs `mg5amc_py8_interface_consistency_warning` (`:4646`); missing binary -> InvalidCmd.

## Probe evidence (v3.7.1, direct PY8Card.write of LO default template)
Same card system-set with `SysCalc:qCutList`+`HEPMCoutput:file`, written twice:
- `use_mg5amc_py8_interface=True`: card contains `HEPMCoutput:scaling=1.0e9`, `SysCalc:qCutList=15.000,20.000`, `LHEFInputs:nSubruns=1`.
- `use_mg5amc_py8_interface=False`: those three lines are **absent** (dropped/commented by `interface_to_164`).

## Cases this catches beyond the per-facet pages
matching-param-handoff documents the MLM/CKKW gates; py8-card-defaults documents `Main:HepMC` main164-only; do-pythia8-handoff documents executable selection; hepmc-output-and-paths documents HepMC path resolution. None document the `interface_to_164` map as a whole, nor the wholesale `SysCalc:*` disabling under main164, nor that **any future param added to that dict** is auto-governed by this rule. The principle: any "does param X reach the card?" question must be answered per-interface.
