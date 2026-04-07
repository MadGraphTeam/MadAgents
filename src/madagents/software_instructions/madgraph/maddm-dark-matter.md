# MadDM (Dark Matter)

MadDM plugin: relic density, direct/indirect detection, and spectral features for BSM dark matter models.

## Contents

- [Installation](#installation)
- [Launching MadDM](#launching-maddm)
- [Core Commands](#core-commands)
  - [Import Model](#import-model)
  - [Define Dark Matter Candidate](#define-dark-matter-candidate)
  - [Define Coannihilators](#define-coannihilators)
  - [Generate and Add Observables](#generate-and-add-observables)
  - [Output and Launch](#output-and-launch)
  - [Display Commands](#display-commands)
- [Complete Workflow Example](#complete-workflow-example)
  - [With `_MD` variant (recommended for MadDM)](#with-_md-variant-recommended-for-maddm)
  - [With standard DMsimp model](#with-standard-dmsimp-model)
  - [Setting Parameters at Launch](#setting-parameters-at-launch)
- [DMsimp Models](#dmsimp-models)
  - [_MD Variants (for MadDM)](#_md-variants-for-maddm)
  - [Standard DMsimp Models (for collider simulations)](#standard-dmsimp-models-for-collider-simulations)
  - [Key param_card Parameters for DMsimp_s_spin1](#key-param_card-parameters-for-dmsimp_s_spin1)

## Installation

Two installation methods:

**Method 1 — From the MG5 interactive shell:**
```
MG5_aMC> install maddm
```

**Method 2 — Manual installation from GitHub:**
```bash
cd <MG5_DIR>
git clone https://github.com/maddmhep/maddm.git PLUGIN/maddm
cp PLUGIN/maddm/maddm bin/maddm
```

**Requirements:**

| Dependency | Required | Notes |
|------------|----------|-------|
| MadGraph5_aMC@NLO ≥ 2.9.3 | Yes | Enforced by the plugin (`__init__.py` sets `minimal_mg5amcnlo_version = (2,9,3)`). The README may state a lower version but the plugin will refuse to load with MG5 < 2.9.3. |
| Python 2.7 | Yes (master) | See Python version note below |
| gcc | Yes | |
| numpy, scipy | Yes | |
| Pythia8 | Optional | For indirect detection showering/hadronization |
| PyMultiNest | Optional | For parameter scans via nested sampling |
| DRAGON | Optional | For cosmic-ray propagation to Earth |

> **Python version note:** MadDM has **two branches** on GitHub with different Python requirements:
>
> | Branch | Version | Python | MG5 requirement |
> |--------|---------|--------|-----------------|
> | `master` (default) | v3.2.13 (latest stable, July 2023) | **Python 2.7 only** | ≥ 2.9.3 |
> | `dev` | v3.3.0 (in development) | **Python 3.6+** (also Python 2.7 with `six` package) | ≥ 3.6 (per README) |
>
> The `master` branch (installed by default via `git clone` or `install maddm`) does **not** support Python 3. To use MadDM with Python 3, you must explicitly check out the `dev` branch **and** use MG5_aMC@NLO ≥ 3.6:
> ```bash
> cd <MG5_DIR>/PLUGIN/maddm
> git checkout dev
> ```
> The `dev` branch is not an official stable release — expect possible API changes or bugs. For production work, the stable `master` branch with Python 2.7 is recommended.

## Launching MadDM

From the MadGraph installation directory:

```bash
python2.7 bin/maddm          # master branch (v3.2.x)
python bin/maddm             # dev branch (v3.3.x, Python 3)
```

This opens an interactive shell (`MadDM>`) with commands similar to MG5.

To run a script non-interactively:

```bash
python2.7 bin/maddm script.txt
```

Type `tutorial` at the MadDM prompt for a guided walkthrough.

## Core Commands

### Import Model

```
import model DMsimp_s_spin0_MD
```

Loads a UFO model. MadDM can auto-download some models from the MG5 model database — check availability with `display modellist`. Not all `_MD` variants are in the database; some must be downloaded manually from the FeynRules DMsimp wiki and placed in `<MG5_DIR>/models/`.

### Define Dark Matter Candidate

```
define darkmatter ~xd
```

Specifies the DM candidate particle. If omitted, MadDM auto-detects the lightest massive neutral BSM particle with zero width.

> **WARNING — Particle naming differs between DMsimp model variants.** The DM candidate has **different particle names** depending on whether you use a standard DMsimp model or a `_MD` (MadDM-formatted) variant. Using the wrong name silently fails — MadDM will not find the particle and computations will produce errors or nonsensical results.

| Model variant | Example | DM particle name | `define darkmatter` command |
|---------------|---------|-------------------|-----------------------------|
| Standard DMsimp | `DMsimp_s_spin0`, `DMsimp_s_spin1` | `xd` | `define darkmatter xd` |
| `_MD` variant (for MadDM) | `DMsimp_s_spin0_MD`, `DMsimp_s_spin1_MD` | `~xd` | `define darkmatter ~xd` |

**Always run `display particles` after importing a model to verify the exact particle names.** Look for the DM candidate in the output and use that exact name. Do NOT assume the name is `xd` or `~xd` without checking — it depends on the specific model variant.

```
import model DMsimp_s_spin1_MD
display particles              # check the DM candidate name in the output
define darkmatter ~xd          # use the name shown by display particles
```

For standard (non-`_MD`) DMsimp models:

```
import model DMsimp_s_spin0
display particles              # DM candidate is listed as 'xd'
define darkmatter xd           # note: no tilde prefix
```

### Define Coannihilators

```
define coannihilator ~xr
```

Includes coannihilation channels in the relic density computation. Use this when your model has BSM particles close in mass to the DM candidate.

### Generate and Add Observables

```
generate relic_density
add direct_detection
add indirect_detection
add indirect_spectral_features
```

**Key distinction:** `generate` removes all previously generated matrix elements and starts fresh. `add` preserves existing matrix elements and appends new ones. Always use `generate` first, then `add` for additional observables.

You can exclude particles from diagrams using `/` syntax:

```
generate relic_density / z       # exclude Z boson from diagrams
```

For indirect detection, you can specify final states:

```
generate indirect_detection u u~       # specific final state
generate indirect_detection u u~ a     # include internal bremsstrahlung
```

For spectral features (loop-induced, v3.2), specify photon final states:

```
generate indirect_spectral_features a a    # γγ line
add indirect_spectral_features a z         # γZ line
```

MadDM automatically tries loop-induced diagrams (`[noborn=QCD]`) when tree-level diagrams are not found. **Do not** use the `[QCD]` syntax manually — use `indirect_spectral_features` instead.

### Output and Launch

```
output MY_DM_RUN
launch MY_DM_RUN
```

`output` creates the run directory with matrix elements and card templates. `launch` runs the computation and presents an interactive configuration interface.

### Display Commands

```
display modellist          # list downloadable models
display particles          # list particles in the loaded model
display processes relic     # show generated relic density processes
display processes indirect  # show generated indirect detection processes
display diagrams all        # show Feynman diagrams
display options             # show settable run parameters
```

## Complete Workflow Example

### With `_MD` variant (recommended for MadDM)

```
# Launch MadDM
# $ python2.7 bin/maddm

import model DMsimp_s_spin0_MD
define darkmatter ~xd          # ~xd for _MD models
generate relic_density
add direct_detection
add indirect_detection
output my_dm_study
launch my_dm_study
```

### With standard DMsimp model

```
import model DMsimp_s_spin0
define darkmatter xd           # xd for standard models (no tilde)
generate relic_density
add direct_detection
output my_dm_study_std
launch my_dm_study_std
```

The `launch` command presents an interactive menu with numbered options:

| Switch | Options | Description |
|--------|---------|-------------|
| `relic` | `ON` / `OFF` | Compute relic density (Ωh²) |
| `direct` | `direct` / `directional` / `OFF` | Compute DM–nucleon scattering |
| `indirect` | `sigmav` / `flux_source` / `flux_earth` / `OFF` | Compute indirect detection (continuum spectrum) |
| `spectral` | `ON` / `OFF` | Compute loop-induced line spectrum (γγ, γZ, γh) — v3.2 |
| `nestscan` | `ON` / `OFF` | Enable MultiNest parameter scan |

After selecting options, you can edit cards:
- **param_card.dat** — model parameters (masses, couplings)
- **maddm_card.dat** — computation-specific settings
- **multinest_card.dat** — scan configuration (if `nestscan = ON`)

### Setting Parameters at Launch

```
set mxd 500              # set DM mass to 500 GeV
set wy1 AUTO             # auto-compute mediator width
set mxd scan:range(50,700,25)   # scan DM mass from 50 to 700 GeV in 25 GeV steps
```

The `scan:` prefix accepts any Python iterable. Use `scan1:` for parallel (simultaneous) scans of multiple parameters.

## DMsimp Models

The DMsimp (Dark Matter Simplified Models) family provides s-channel mediator models. Variants specifically formatted for MadDM have the `_MD` suffix.

### _MD Variants (for MadDM)

| Model | Mediator | DM Candidate | DM particle name | Notes |
|-------|----------|-------------|------------------|-------|
| `DMsimp_s_spin0_MD` | Y0 (scalar) | Xd (Dirac fermion) | `~xd` | Verify availability with `display modellist`; may need manual download |
| `DMsimp_s_spin1_MD` | Y1 (vector) | Xd (Dirac fermion) | `~xd` | Available on FeynRules wiki; may require manual download |
| `DMsimp_s_spin0_mixed_MD` (zip) | Y0 (scalar, mixed) | Xd (Dirac fermion) | `~xd` | Effective ggY/aaY couplings (LO). **Warning:** MG5 database name may differ from the zip file name |

### Standard DMsimp Models (for collider simulations)

Standard (non-`_MD`) DMsimp models also work with MadDM but are designed for collider simulations:

| Model | Description | DM particle name |
|-------|-------------|------------------|
| `DMsimp_s_spin0` | Scalar mediator (NLO capable) | `xd` |
| `DMsimp_s_spin1` | Vector mediator (NLO capable; v2.0 added leptons, v2.1 added monotop) | `xd` |
| `DMsimp_s_spin2` | Tensor mediator (spin-2) | `xd` |

DMsimp DM candidate types across variants: `Xr` (real scalar), `Xc` (complex scalar), `Xd` (Dirac fermion), `Xv` (vector DM).

### Key param_card Parameters for DMsimp_s_spin1

The DMsimp_s_spin1 model has **generation-specific** couplings. All couplings are in the `DMINPUTS` block:

| Parameter | Description |
|-----------|-------------|
| `gVXd` | DM–mediator vector coupling |
| `gAXd` | DM–mediator axial-vector coupling |
| `gVu11`, `gVu22`, `gVu33` | Vector couplings to up-type quarks (1st, 2nd, 3rd gen) |
| `gVd11`, `gVd22`, `gVd33` | Vector couplings to down-type quarks (1st, 2nd, 3rd gen) |
| `gAu11`, `gAu22`, `gAu33` | Axial-vector couplings to up-type quarks |
| `gAd11`, `gAd22`, `gAd33` | Axial-vector couplings to down-type quarks |
| `gVl11`, `gVl22`, `gVl33` | Vector couplings to charged leptons |
| `gAl11`, `gAl22`, `gAl33` | Axial-vector couplings to charged leptons |
| `gnu11`, `gnu22`, `gnu33` | Couplings to neutrinos |

Mass parameters (in the `MASS` block):

| Parameter | Description |
|-----------|-------------|
| `MXd` | Dark matter mass |
| `MY1` | Vector mediator mass |
| `WY1` | Mediator width (in `DECAY` block; set to `AUTO` for automatic computation) |

> **Note:** The `_MD` variants may have a reduced set of couplings compared to the full collider model. Always check the param_card of the specific model you import.
