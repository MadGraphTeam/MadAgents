# MadGraph5_aMC@NLO — Overview

MadGraph5_aMC@NLO (MG5_aMC) is a framework for automated Monte Carlo simulation of particle physics processes at leading order (LO) and next-to-leading order (NLO) in QCD. It generates matrix elements, performs phase-space integration, and produces parton-level events in Les Houches Event (LHE) format. Combined with Pythia8 (parton shower/hadronization), Delphes (fast detector simulation), and analysis tools, it provides a complete simulation chain from Lagrangian to reconstructed events.

## Simulation Chain

```
Hard process — matrix elements, LHE events (MadGraph5)
  → Parton shower — shower, hadronization, underlying event (Pythia8, Herwig7, ...)
  → Detector simulation — fast/full detector response (Delphes, Geant4, ...)
  → Analysis — cuts, histograms, signal regions (MadAnalysis5, Rivet, ...)
```

Additional tools plug into this chain, e.g.: **MadSpin** (spin-correlated decays, between hard process and parton shower), **MadWidth** (decay width computation).

## Quick Start — Script-Based Execution

Save the following as `ttbar.mg5` and run with `<MG5_DIR>/bin/mg5_aMC ttbar.mg5`:

```
import model sm
generate p p > t t~
output ttbar_LO
launch ttbar_LO
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

This generates 10,000 LO t-tbar events at 13 TeV. Results appear in `ttbar_LO/Events/run_01/`.

## Reference Documentation

### Getting Started

| File | Description |
|------|-------------|
| [Installation](/madgraph_docs/installation.md) | Download, dependencies, `install` command for Pythia8/Delphes/MadAnalysis5 |
| [Process Syntax](/madgraph_docs/process-syntax.md) | `generate`/`add process`, multiparticle labels, decay chains, `@N` tags |
| [Models & Restrictions](/madgraph_docs/models-and-restrictions.md) | Built-in models (sm, heft, loop_sm), BSM imports, restriction files |
| [Cards & Parameters](/madgraph_docs/cards-and-parameters.md) | param_card, run_card, generation-level cuts, custom cuts |
| [Scripted Execution](/madgraph_docs/scripted-execution.md) | Script-mode workflow, `launch` options, gridpacks, `compute_widths` |
| [Interactive Mode](/madgraph_docs/interactive-mode.md) | Interactive MG5 prompt commands and navigation |

### NLO & Matching

| File | Description |
|------|-------------|
| [NLO Computations](/madgraph_docs/nlo-computations.md) | NLO QCD/EW syntax (`[QCD]`, `[QED]`), MC@NLO, `mcatnlo_delta`, FKS parameters |
| [NLO Plugins & Loops](/madgraph_docs/nlo-plugins-and-loops.md) | MadSTR plugin (DR/DS), loop-induced + jets, squared order constraints, flavor schemes at NLO |
| [Matching & Merging](/madgraph_docs/matching-and-merging.md) | MLM (xqcut/qCut), FxFx, CKKW-L, DJR validation plots |
| [Coupling Orders & Validation](/madgraph_docs/coupling-orders-and-validation.md) | `QCD=`, `QED=`, squared orders (`^2==`), automatic ordering, cross-section checks |

### Decays & Widths

| File | Description |
|------|-------------|
| [Decays & MadSpin](/madgraph_docs/decays-and-madspin.md) | Decay methods (syntax/MadSpin/MadWidth), `spinmode`, `compute_widths`, decision table |
| [Complex Mass Scheme](/madgraph_docs/complex-mass-scheme.md) | CMS for unstable particles, NWA validity, width consistency |

### Simulation Chain

| File | Description |
|------|-------------|
| [Pythia8 Interface](/madgraph_docs/pythia8-interface.md) | Shower settings, pythia8_card, tune selection, jet matching in Pythia8 |
| [Delphes Interface](/madgraph_docs/delphes-interface.md) | Fast detector simulation, detector cards, shower/detector consistency |
| [MadAnalysis5](/madgraph_docs/madanalysis5.md) | Analysis framework integration, cut definitions, histogram output |
| [LHE Output Format](/madgraph_docs/lhe-output-format.md) | Event file structure, particle records, weight normalization, Python parsing |

### Physics Inputs

| File | Description |
|------|-------------|
| [PDFs & Scales](/madgraph_docs/pdfs-and-scales.md) | PDF selection, LHAPDF, dynamical scale choices, flavor schemes (4F/5F) |
| [Parameter Scans](/madgraph_docs/parameter-scans.md) | `scan:` syntax, Cartesian product, correlated scans, thread-leak workaround |
| [Lepton & Photon Colliders](/madgraph_docs/lepton-photon-colliders.md) | `lpp` settings, beam polarization, EPA, muon colliders |
| [Systematics & Reweighting](/madgraph_docs/systematics-reweighting.md) | `use_syst`, `systematics` module, scale/PDF uncertainty envelopes |

### Advanced Topics & Troubleshooting

| File | Description |
|------|-------------|
| [Diagram Filtering](/madgraph_docs/diagram-filtering.md) | `/`, `$`, `$$` operators, s-channel filtering, resonance selection |
| [Biased Event Generation](/madgraph_docs/biased-event-generation.md) | `bias` module, `ptj_bias`, custom bias functions |
| [EFT & SMEFTsim](/madgraph_docs/eft-smeftsim.md) | Dimension-6 operators, restriction files, interference isolation |
| [MadDM Dark Matter](/madgraph_docs/maddm-dark-matter.md) | Relic density, direct/indirect detection, co-annihilation |
| [MadDM Cards & Scans](/madgraph_docs/maddm-cards-and-scans.md) | MadDM parameter cards, scan configuration, output format |
| [Standalone Matrix Elements](/madgraph_docs/standalone-matrix-elements.md) | Fortran/C++/Python standalone output, external ME evaluation |
| [Troubleshooting](/madgraph_docs/troubleshooting.md) | Common errors, integration problems, numerical instabilities, environment fixes |

## Key Conventions

- **Script-first**: All examples are shown as runnable script files (`<MG5_DIR>/bin/mg5_aMC script.mg5`) unless stated otherwise.
- **Placeholders**: `<PROC_DIR>` means a user-chosen process directory name. `<MG5_DIR>` means the MadGraph installation directory.
- **Verify numeric values**: LHAPDF IDs, default masses, widths, and other numeric parameters may differ across MG5_aMC versions, model versions, and PDF installations. Verify against the current installation (e.g., `lhapdf list` for PDF set IDs, `param_card_default.dat` for default masses, generated `run_card.dat` for run-card defaults).
- **Version**: Documentation targets MG5_aMC v3.x. Version-specific differences are noted where relevant.
