# 11 — Analysis — MadAnalysis5

MadAnalysis5 setup, script-mode usage, kinematic cuts, histograms, and recasting in MadGraph5.

## Contents

- [Role in the Simulation Chain](#role-in-the-simulation-chain)
- [Installation](#installation)
- [Enabling MA5 in MG5 Scripts](#enabling-ma5-in-mg5-scripts)
- [MA5 Standalone Usage](#ma5-standalone-usage)
  - [Normal Mode (Interactive/Command-Line)](#normal-mode-interactivecommand-line)
  - [Expert Mode (C++ Analysis)](#expert-mode-c-analysis)
- [Key Capabilities](#key-capabilities)
  - [Kinematic Cuts and Selections](#kinematic-cuts-and-selections)
  - [Histograms](#histograms)
  - [Signal Regions](#signal-regions)
  - [Recasting](#recasting)
- [Example: WW → Dilepton Analysis](#example-ww-dilepton-analysis)
- [Output](#output)

## Role in the Simulation Chain

```
MadGraph5 → Pythia8 → Delphes → MadAnalysis5
                                   ↑
                        (or directly from LHE/HepMC)
```

MA5 reads event files in multiple formats: LHE, HepMC, ROOT (Delphes), and LHCO.

## Installation

From within MadGraph5:

```
install MadAnalysis5
```

This downloads and configures MA5 within the MG5 installation. See [Installation & Setup](installation.md).

## Enabling MA5 in MG5 Scripts

MA5 can be enabled as part of the MG5 launch chain:

```
launch my_process
  shower=PYTHIA8
  detector=Delphes
  analysis=MadAnalysis5
  set run_card nevents 50000
  done
```

When enabled, MA5 runs after Delphes (or after Pythia8 if no Delphes) and produces analysis outputs automatically.

## MA5 Standalone Usage

MA5 can also be run standalone on existing event files. It has two main modes:

### Normal Mode (Interactive/Command-Line)

MA5 provides its own command-line interface with a domain-specific language:

```
# Launch MA5
./bin/ma5

# Inside the MA5 session:
import /path/to/unweighted_events.lhe.gz
define mu = mu+ mu-
plot PT(mu[1]) 40 0 200 [logY]     # pT of leading muon
plot MET 40 0 500 [logY]            # missing ET distribution
select (mu) PT > 25                  # apply cut
plot M(mu[1] mu[2]) 40 0 200 [logY] # dimuon invariant mass
submit                                # generate plots and cutflow
```

### Expert Mode (C++ Analysis)

For complex analyses, MA5 provides a C++ framework (SampleAnalyzer) where users write custom analysis code with object selection, kinematic cuts, and histogram filling.

### Recasting

MA5 includes a recasting module that reimplements published LHC analyses, allowing users to test BSM models against existing experimental constraints.

## Example: WW → Dilepton Analysis

```
import model sm
generate p p > w+ w-
output ww_analysis
launch ww_analysis
  shower=PYTHIA8
  detector=Delphes
  analysis=MadAnalysis5
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 50000
  done
```


## Output

MA5 produces:
- Histograms in various formats (ROOT, matplotlib)
- Cutflow tables showing efficiency of each selection step
- HTML reports with plots and statistics
- Signal region yields for recasting comparisons
