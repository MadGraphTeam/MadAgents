# 01 — Installation & Setup

This document covers installing MadGraph5_aMC@NLO and its optional tool chain.

## Contents

- [Prerequisites](#prerequisites)
- [Downloading MadGraph5](#downloading-madgraph5)
- [Installing Optional Tools](#installing-optional-tools)
  - [Pythia8 (Parton Shower)](#pythia8-parton-shower)
  - [Delphes (Detector Simulation)](#delphes-detector-simulation)
  - [MadAnalysis5 (Analysis Framework)](#madanalysis5-analysis-framework)
  - [LHAPDF6 (PDF Library)](#lhapdf6-pdf-library)
  - [Installing All at Once](#installing-all-at-once)
- [Configuration — mg5_configuration.txt](#configuration-mg5_configurationtxt)
- [PDF Set Management](#pdf-set-management)
  - [LHAPDF Not Found Error](#lhapdf-not-found-error)
- [Verification](#verification)
- [Directory Structure](#directory-structure)

## Prerequisites

- Python 3.7+ (Python 2 is deprecated)
- Fortran compiler (gfortran recommended)
- C++ compiler (g++ for Pythia8, Delphes)
- GNU make
- For NLO: requires additional libraries (handled automatically by MG5)

## Downloading MadGraph5

Download the latest version from the MadGraph website or via:

```bash
wget https://launchpad.net/mg5amcnlo/3.0/3.6.x/+download/MG5_aMC_v3.6.7.tar.gz
tar xzf MG5_aMC_v3.6.7.tar.gz
cd MG5_aMC_v3_6_7
```

> **Note:** The extracted directory name is version-specific (e.g., `MG5_aMC_v3_6_7` for v3.6.7). On shared or production systems, administrators frequently rename or relocate the installation directory. **Do not hardcode this path in automation scripts.** Discover the path at runtime with `which mg5_aMC` (if `<MG5_DIR>/bin` is on `$PATH`) or `find / -name mg5_aMC -type f 2>/dev/null`.

Test the installation by starting an interactive session:

```bash
<MG5_DIR>/bin/mg5_aMC
```

This opens the `MG5_aMC>` prompt and prints the version banner. Type `exit` to quit.

## Installing Optional Tools

MG5 has built-in commands to download and compile optional tools. Run these from within MG5 (interactive or script):

### Pythia8 (Parton Shower)

```
install pythia8
```

Downloads, compiles, and configures Pythia8. Required for parton showering and hadronization. See [Parton Shower — Pythia8](pythia8-interface.md).

### Delphes (Detector Simulation)

```
install Delphes
```

Downloads and compiles the Delphes fast detector simulator. See [Detector Simulation — Delphes](delphes-interface.md).

### MadAnalysis5 (Analysis Framework)

```
install MadAnalysis5
```

Downloads and configures MadAnalysis5. See [Analysis — MadAnalysis5](madanalysis5.md).

### LHAPDF6 (PDF Library)

```
install lhapdf6
```

Installs the LHAPDF library for parton distribution functions. Without LHAPDF, MG5 falls back to a limited built-in PDF set.

### Installing All at Once

In a script:

```
install pythia8
install Delphes
install MadAnalysis5
install lhapdf6
```

## Configuration — mg5_configuration.txt

The file `input/mg5_configuration.txt` (in the MG5 installation directory) stores paths and settings:

```
# Paths to external tools (if pre-installed)
# pythia8_path = /path/to/pythia8
# delphes_path = /path/to/Delphes
# lhapdf = /path/to/lhapdf-config
# madanalysis5_path = /path/to/madanalysis5

# Fortran compiler
# f2py_compiler = gfortran

# Automatic updates
# automatic_html_opening = False
```

If tools are installed externally (not via `install`), set their paths here.

## PDF Set Management

After installing LHAPDF, download specific PDF sets:

```bash
lhapdf-config --pdfsets-path        # find the PDF directory
lhapdf install NNPDF31_lo_as_0118   # download a specific set
```

Common PDF sets:

| LHAPDF ID | PDF Set | Use Case |
|-----------|---------|----------|
| 315000 | NNPDF31_lo_as_0118 | LO calculations |
| 303400 | NNPDF31_nlo_as_0118 | NLO calculations |
| 11000 | CT10nlo | NLO, alternative |
| 25000 | MMHT2014lo68cl | LO, alternative |

Set the PDF in the run_card: `set run_card pdlabel lhapdf` and `set run_card lhaid 315000`

### LHAPDF Not Found Error

If MG5 reports `Error: LHAPDF library could not be found`:

1. Install via MG5: `install lhapdf6`
2. Or set the path in `input/mg5_configuration.txt`:
   ```
   lhapdf = /path/to/lhapdf-config
   ```
3. Without LHAPDF, MG5 uses its internal (limited) PDF set — results are less precise but functional.

## Verification

After installation, verify the setup works:

```
import model sm
generate e+ e- > mu+ mu-
output test_install
launch test_install
  set run_card ebeam1 45.6
  set run_card ebeam2 45.6
  set run_card lpp1 0
  set run_card lpp2 0
  set run_card nevents 100
  done
```

If this runs without errors and produces events in `test_install/Events/run_01/`, the installation is working.

To verify with Pythia8:

```
import model sm
generate p p > t t~
output test_shower
launch test_shower
  shower=PYTHIA8
  set run_card nevents 100
  done
```

## Directory Structure

After installation, the MG5 directory contains:

```
MG5_aMC_v3_6_7/
├── bin/                # mg5_aMC executable
├── input/              # mg5_configuration.txt
├── models/             # UFO model directories (sm, loop_sm, heft, ...)
├── Template/           # Template process directories
├── HEPTools/           # Installed tools (Pythia8, Delphes, LHAPDF, ...)
├── madgraph/           # MG5 Python source code
└── tests/              # Test suite
```
