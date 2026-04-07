# 10 — Detector Simulation — Delphes

Delphes fast detector simulation setup, detector cards, jet clustering, and b-tagging configuration in MadGraph5.

## Contents

- [Role in the Simulation Chain](#role-in-the-simulation-chain)
- [Enabling Delphes in Scripts](#enabling-delphes-in-scripts)
- [Installation](#installation)
- [Detector Cards](#detector-cards)
- [Detector Card Components](#detector-card-components)
  - [Jet Clustering](#jet-clustering)
  - [b-Tagging](#b-tagging)
  - [Other Configurable Modules](#other-configurable-modules)
- [Output Format](#output-format)

## Role in the Simulation Chain

```
MadGraph5 (LHE) → Pythia8 (HepMC) → Delphes (ROOT) → Analysis
```


## Enabling Delphes in Scripts

```
launch my_process
  shower=PYTHIA8
  detector=Delphes
  set run_card nevents 10000
  done
```

Pythia8 must also be enabled — Delphes reads the showered events. The output is a ROOT file:
`Events/run_01/tag_1_delphes_events.root`

**Shower/detector consistency**: Setting `detector=Delphes` while `shower=OFF` causes MadGraph to automatically promote shower to Pythia8. Setting `shower=OFF` while `detector=Delphes` is active forces the detector back to OFF. These corrections are enforced silently — no explicit warning is printed.

## Installation

If Delphes is not installed:

```
install Delphes
```

This downloads and compiles Delphes within the MG5 installation. See [Installation & Setup](installation.md).

## Detector Cards

Delphes uses a card file to define the detector configuration. Pre-built cards for major experiments are provided:

| Card | Description |
|------|-------------|
| `delphes_card_CMS.dat` | CMS detector configuration |
| `delphes_card_ATLAS.dat` | ATLAS detector configuration |
| `delphes_card_FCC.dat` | Future Circular Collider |

The default card is typically the CMS card. You can provide a custom card:

```
launch my_process
  shower=PYTHIA8
  detector=Delphes
  /path/to/my_delphes_card.dat
  done
```

## Detector Card Components

A Delphes card is organized into modules. Key configurable components:

### Jet Clustering

```
module FastJetFinder {
  set JetAlgorithm 6        # anti-kT algorithm
  set ParameterR 0.4        # cone radius
  set JetPTMin 20.0         # minimum jet pT (GeV)
}
```

Algorithm options: 6 = anti-kT (standard at LHC), 5 = Cambridge-Aachen, 4 = kT.

### b-Tagging

```
module BTagging {
  # b-jet efficiency (pT-dependent)
  add EfficiencyFormula {0} {0.001}    # light-jet mistag rate
  add EfficiencyFormula {4} {0.10}     # c-jet mistag rate
  add EfficiencyFormula {5} {0.70}     # b-jet tagging efficiency
}
```

### Other Configurable Modules

Delphes cards also configure: `ElectronEfficiency`, `MuonEfficiency` (pT/eta-dependent ID efficiency), `Isolation` (cone radius `DeltaRMax`, pT ratio `PTRatioMax`), `Calorimeter` (ECAL/HCAL energy resolution and segmentation), `MissingET` (computed from all visible objects), and `TauTagging`.

## Output Format

Delphes produces a ROOT file containing trees with reconstructed objects:

- `Jet`: Reconstructed jets with pT, eta, phi, mass, b-tag flag
- `Electron`: Reconstructed electrons with ID and isolation info
- `Muon`: Reconstructed muons
- `Photon`: Reconstructed photons
- `MissingET`: Missing transverse energy (MET)
- `Track`: Reconstructed tracks
- `Tower`: Calorimeter towers

The ROOT file can be analyzed with ROOT, PyROOT, uproot, or MadAnalysis5.
