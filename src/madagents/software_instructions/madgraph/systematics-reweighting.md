# 13 — Systematics & Reweighting

MadGraph5 supports on-the-fly reweighting to estimate systematic uncertainties from scale and PDF variations without regenerating events. This is implemented via the built-in `systematics` module, controlled by run_card parameters.

## Contents

- [Enabling Reweighting](#enabling-reweighting)
  - [Configuring via `systematics_arguments` (Recommended)](#configuring-via-systematics_arguments-recommended)
  - [Legacy Parameters (Deprecated)](#legacy-parameters-deprecated)
- [Scale Variations](#scale-variations)
  - [The 7-Point Envelope](#the-7-point-envelope)
  - [Interpreting Scale Uncertainties](#interpreting-scale-uncertainties)
  - [Limitation: Interference-Dominated Cross-Sections](#limitation-interference-dominated-cross-sections)
- [PDF Uncertainties](#pdf-uncertainties)
  - [Setting Up PDF Variations](#setting-up-pdf-variations)
  - [Types of PDF Uncertainty Sets](#types-of-pdf-uncertainty-sets)
  - [Complete Example](#complete-example)
- [Accessing Reweighting Weights](#accessing-reweighting-weights)
  - [Extracting Weights with Python](#extracting-weights-with-python)
- [Matching/Merging Uncertainties](#matchingmerging-uncertainties)
- [Summary of Uncertainty Sources](#summary-of-uncertainty-sources)
- [Standalone Reweight Module](#standalone-reweight-module)
- [Standalone Reweight Module](#standalone-reweight-module)
  - [Enabling Reweighting](#enabling-reweighting)
  - [Reweight Card Syntax (`reweight_card.dat`)](#reweight-card-syntax-reweight_carddat)
  - [What Can and Cannot Be Reweighted](#what-can-and-cannot-be-reweighted)
  - [Output: Reweight Weights in the LHE File](#output-reweight-weights-in-the-lhe-file)
  - [NLO Reweighting](#nlo-reweighting)

## Enabling Reweighting

The systematics module is controlled by three run_card parameters:

| Parameter | Default | Hidden | Description |
|-----------|---------|--------|-------------|
| `use_syst` | `True` | No | Master switch for the systematics module |
| `systematics_program` | `systematics` | Yes | Program to run: `systematics` (built-in), `none`, or `syscalc` (legacy) |
| `systematics_arguments` | `['--mur=0.5,1,2', '--muf=0.5,1,2', '--pdf=errorset']` | Yes | Command-line flags passed to the systematics program |

With the defaults, **all 9 scale variation combinations (3 μ_R × 3 μ_F factors) and PDF error-set reweighting are computed automatically** — no user action is required. The standard 7-point envelope is obtained by excluding the two extreme anti-correlated variations at analysis time.

### Configuring via `systematics_arguments` (Recommended)

The `systematics_arguments` parameter accepts a list of command-line-style flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--mur=VALS` | `0.5,1,2` | Comma-separated μ_R scale factors |
| `--muf=VALS` | `0.5,1,2` | Comma-separated μ_F scale factors |
| `--pdf=VALS` | `errorset` | `errorset` (all error members of generation PDF), `central`, or comma-separated LHAPDF IDs |
| `--alps=VALS` | `1` | Comma-separated α_s emission scale factors (relevant for MLM matching) |
| `--dyn=VALS` | `-1,1,2,3,4` | Dynamical scale choices to reweight over |
| `--together=VALS` | `mur,muf,dyn` | Which variations to correlate (vary together rather than independently) |
| `--start_event=N` | `0` | First event to process |
| `--stop_event=N` | (all) | Last event to process |

In a script:

```
launch my_process
  set run_card systematics_arguments ['--mur=0.5,1,2', '--muf=0.5,1,2', '--pdf=errorset']
  done
```

To add α_s variations (e.g., for matched samples):

```
launch my_process
  set run_card systematics_arguments ['--mur=0.5,1,2', '--muf=0.5,1,2', '--alps=0.5,1,2', '--pdf=errorset', '--together=mur,muf,alps,dyn']
  done
```

To specify alternative PDF sets by LHAPDF ID instead of using the generation PDF's error set:

```
launch my_process
  set run_card systematics_arguments ['--mur=0.5,1,2', '--muf=0.5,1,2', '--pdf=303400,325300']
  done
```

To disable systematics entirely:

```
launch my_process
  set run_card use_syst False
  done
```

### Legacy Parameters (Deprecated)

Older MadGraph versions (and the external SysCalc tool) used a different set of run_card parameters: `sys_scalefact`, `sys_pdf`, and `sys_alpsfact`. These are **deprecated** and should not be used for new workflows. They correspond to the `syscalc` setting of `systematics_program`. The modern `systematics_arguments` interface supersedes them entirely.

| Legacy Parameter | Modern Equivalent |
|------------------|-------------------|
| `sys_scalefact` (e.g., `0.5 1 2`) | `--mur=0.5,1,2 --muf=0.5,1,2` in `systematics_arguments` |
| `sys_pdf` (e.g., `303400`) | `--pdf=303400` in `systematics_arguments` |
| `sys_alpsfact` (e.g., `0.5 1 2`) | `--alps=0.5,1,2` in `systematics_arguments` |

## Scale Variations

### The 7-Point Envelope

The standard procedure for estimating missing higher-order uncertainties:

1. Vary the renormalization scale μ_R and factorization scale μ_F independently by factors of 0.5 and 2 around the central value.
2. Exclude the two extreme opposite variations (μ_R×2, μ_F×0.5) and (μ_R×0.5, μ_F×2).
3. Take the envelope (max and min) of the remaining 7 combinations.

With the default `systematics_arguments` (`--mur=0.5,1,2 --muf=0.5,1,2`), MadGraph generates weights for all 9 combinations of (μ_R × factor) and (μ_F × factor). The 7-point envelope is obtained by excluding the two anti-correlated extreme variations from this set.

### Interpreting Scale Uncertainties

- **LO**: Scale uncertainties are typically large (±30-50% or more) because LO has no constraint on the scale dependence.
- **NLO**: Scale uncertainties are reduced (±10-20% typically) due to partial cancellation between real and virtual corrections.
- The scale uncertainty is a rough estimate, not a rigorous error band.

### Limitation: Interference-Dominated Cross-Sections

For cross-sections dominated by **interference between amplitudes of different coupling orders** — such as SM–EFT interference terms isolated via squared-order syntax (e.g., `QCD^2==N QED^2==M`; see [Coupling Orders & Validation](coupling-orders-and-validation.md)) — the on-the-fly scale reweighting via `use_syst` may produce unreliable uncertainty estimates.

**Recommended approach**: Estimate scale uncertainties for interference-dominated cross-sections by running separate event generations with different central scale choices (e.g., varying `scalefact` in the run_card to 0.5, 1.0, and 2.0 in independent runs). See [PDFs and Scales](pdfs-and-scales.md) for scale definition options.

## PDF Uncertainties

### Setting Up PDF Variations

With the default `--pdf=errorset` in `systematics_arguments`, the systematics module automatically computes weights for every error member of the generation PDF set (the one specified by `lhaid` in the run_card). No additional configuration is needed.

To reweight to a different PDF set, specify LHAPDF IDs:

```
set run_card systematics_arguments ['--mur=0.5,1,2', '--muf=0.5,1,2', '--pdf=303400']
```

Multiple PDF sets can be specified as comma-separated LHAPDF IDs (e.g., `--pdf=303400,325300`). The module computes weights for each member of each specified error set.

### Types of PDF Uncertainty Sets

- **Hessian** (e.g., CT10, MMHT): combine eigenvector variations as quadrature sum.
- **Monte Carlo replicas** (e.g., NNPDF): take standard deviation across replicas.

### Complete Example

Using defaults (scale + PDF error-set reweighting enabled automatically):

```
import model sm
generate p p > t t~
output ttbar_syst
launch ttbar_syst
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 50000
  done
```

With custom systematics (explicit PDF set, α_s variations for matching):

```
import model sm
define p = g u c d s u~ c~ d~ s~
generate p p > t t~
output ttbar_syst
launch ttbar_syst
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 50000
  set run_card systematics_arguments ['--mur=0.5,1,2', '--muf=0.5,1,2', '--alps=0.5,1,2', '--pdf=303400', '--together=mur,muf,alps,dyn']
  done
```

## Accessing Reweighting Weights

The event weights from reweighting are stored in the LHE file inside `<rwgt>` blocks within each event:

```xml
<event>
  ... (particle records) ...
  <rwgt>
    <wgt id='1001'> 1.0234e+02 </wgt>   <!-- central -->
    <wgt id='1002'> 1.1456e+02 </wgt>   <!-- muR*2 -->
    <wgt id='1003'> 8.9123e+01 </wgt>   <!-- muR*0.5 -->
    ...
  </rwgt>
</event>
```

Each `<wgt>` element has an ID that maps to a specific scale/PDF combination. The mapping is documented in the LHE file header.

### Extracting Weights with Python

```python
import gzip
import xml.etree.ElementTree as ET

with gzip.open('unweighted_events.lhe.gz', 'rt') as f:
    content = f.read()

# Parse rwgt blocks to extract systematic weights
# Each event's <rwgt> section contains the alternative weights
```

See [Output Formats & LHE](lhe-output-format.md) for LHE parsing details.

## Matching/Merging Uncertainties

For matched samples (MLM or FxFx), additional uncertainties come from the matching procedure:

- **xqcut variation**: Vary xqcut by factors of 0.5 and 2 around the central value.
- **qCut variation**: Vary consistently with xqcut.
- The spread in post-shower cross-sections and distributions estimates the matching uncertainty.

These require separate event generations (cannot be done with on-the-fly reweighting).

## Summary of Uncertainty Sources

## Standalone Reweight Module

## Standalone Reweight Module

Beyond the `use_syst` systematics module (scale/PDF variations), MadGraph provides a standalone **reweight module** that recomputes event weights for arbitrary changes to model parameters, couplings, masses, widths, or even the process definition — without regenerating events.

### Enabling Reweighting

Reweighting is controlled via the `reweight_card.dat` in `<PROC_DIR>/Cards/`. To activate it during event generation, enable the `reweight` switch during the launch dialogue:

```
launch my_process
  reweight=ON
  done
```

When `reweight=ON` is set, MadGraph presents the `reweight_card.dat` for editing (in interactive mode) or reads it from `Cards/reweight_card.dat` (in scripted mode). The reweight module runs automatically after event generation.

To run reweighting on previously generated events (post-hoc), use `madevent reweight` from within the process directory:

```bash
cd my_process
./bin/madevent reweight -f
```

#### Scripted Workflow with Reweighting

For scripted execution, prepare the `reweight_card.dat` file before launching. The card file must be placed at `<PROC_DIR>/Cards/reweight_card.dat` or provided as a path during launch:

```
import model sm
generate p p > t t~
output my_ttbar
launch my_ttbar
  reweight=ON
  /path/to/my_reweight_card.dat
  done
```

Alternatively, edit `Cards/reweight_card.dat` in the process directory before running `launch`.

### Reweight Card Syntax (`reweight_card.dat`)

The reweight card defines one or more **reweight parameter points**. Each point starts with a `launch` line and contains `set` commands that modify param_card parameters:

```
# reweight_card.dat

# Vary the top Yukawa coupling
launch --rwgt_name=yt_up
  set yukawa 6 180.0

launch --rwgt_name=yt_down
  set yukawa 6 165.0
```

#### Reweight Card Commands

| Command | Description | Example |
|---------|-------------|--------|
| `launch` | Start a new reweight point | `launch` |
| `launch --rwgt_name=NAME` | Start a new reweight point with a named ID | `launch --rwgt_name=yt_up` |
| `set BLOCK ID VALUE` | Change a param_card parameter | `set yukawa 6 180.0` |
| `set WIDTH ID VALUE` | Change a particle width | `set width 25 0.00407` |
| `set BLOCK ID ID VALUE` | Change a matrix element in a 2D block | `set nmix 1 1 0.95` |
| `change model MODELNAME` | Switch to a different UFO model | `change model sm-no_b_mass` |
| `change model MODELNAME --modelname` | Switch model, keeping the original model's parameter names for mapping | `change model EFT_model --modelname` |
| `change process DEFINITION` | Reweight to a different (related) process | `change process p p > e+ e- j` |
| `change helicity False` | Sum over helicities instead of using stored helicity info | `change helicity False` |
| `change output 2.0` | Enable extended LHE output (required for mass reweighting) | `change output 2.0` |

The `set` commands inside the reweight card use the same BLOCK/ID syntax as in the param_card (not the `set run_card` / `set param_card` syntax used in launch dialogue scripts).

#### Mass Reweighting: `change output 2.0` Requirement

When the reweight card modifies **particle masses** (entries in the `MASS` block), the reweight module requires the extended LHE output format. This must be declared at the top of the reweight card with `change output 2.0` **before** any `launch` blocks:

```
# reweight_card.dat — mass reweighting example
change output 2.0

launch --rwgt_name=mH_126
  set mass 25 126.0
  set width 25 0.00407

launch --rwgt_name=mH_124
  set mass 25 124.0
  set width 25 0.00407
```

Without `change output 2.0`, MG5 raises a CRITICAL error:
```
CRITICAL: mass reweighting requires dedicated lhe output! Please include change output 2.0 in your reweight_card
```

The `change output 2.0` directive is only required when modifying masses. Reweighting that changes only couplings, Yukawas, widths, or other non-mass parameters does not require it.

#### Using Scan Syntax in Reweight Cards

The `set` command in the reweight card supports the **scan syntax** to generate multiple reweight points automatically:

```
# Scan over coupling values (no mass change — change output 2.0 not needed)
launch --rwgt_name=yt_scan
  set yukawa 6 scan:[165.0, 170.0, 172.0, 175.0, 180.0]
```

For mass scans, include `change output 2.0`:

```
# Scan over Higgs masses (mass change — change output 2.0 required)
change output 2.0

launch --rwgt_name=mH_scan
  set mass 25 scan:[120.0, 122.0, 124.0, 125.0, 126.0, 128.0, 130.0]
  set width 25 0.00407
```

This creates one reweight point per value, equivalent to writing multiple `launch` blocks. Multiple scanned parameters create a grid (all combinations).

**Details ->** [Parameter Scans](parameter-scans.md)

### What Can and Cannot Be Reweighted

The standalone reweight module recomputes the **matrix element** at each phase-space point with new parameters. It does NOT regenerate phase-space points or rerun the phase-space integration.

| Can Be Reweighted | Cannot Be Reweighted |
|---|---|
| Model parameters (couplings, masses, widths) | Generation-level cuts (the cuts applied during integration) |
| EFT Wilson coefficients / BSM couplings | Beam energy or beam type |
| Process definition (related processes with same initial/final states) | Functional form of the dynamical scale choice |
| Helicity treatment | Number of final-state particles |
| | Unrelated processes (different particle content) |

**Key points:**
- The original phase-space sampling must adequately cover the region relevant for the new parameters. If the new parameters create kinematic features not present in the original sample (e.g., a new resonance), the reweighted sample will be unreliable.
- For large parameter changes, validate the reweighted result against a dedicated generation.
- When reweighting masses, always include `change output 2.0` in the reweight card.
- Scale and PDF variations are handled by the separate `use_syst` systematics module (see above), not by the standalone reweight module.

### Output: Reweight Weights in the LHE File

Standalone reweight weights are stored in the same `<rwgt>` block as systematics weights, but use different ID conventions:

- **Standalone reweight weights**: IDs default to the format `rwgt_1`, `rwgt_2`, etc. (sequential numbering). If `--rwgt_name=NAME` is used, the ID is the specified `NAME`.
- **`use_syst` weights**: IDs are numeric, starting from 1 by default. The exact IDs depend on the number of scale/PDF variations and are documented in the LHE `<header>` block under the `<initrwgt>` section.

Both weight types appear together in each event's `<rwgt>` block. The `<initrwgt>` section in the LHE header defines the weight groups and maps IDs to their meaning.

**Details ->** [Output Formats & LHE](lhe-output-format.md)

### NLO Reweighting

The standalone reweight module works at NLO. Requirements and considerations:

- The process must have been generated at NLO (`[QCD]` or `[QED]` syntax in the process definition) using a loop-capable model (e.g., `loop_sm`).
- **`store_rwgt_info = True` must be set in the run_card before event generation.** This causes MadGraph to write counter-term and momentum information (`<mgrwgt>` blocks) into each LHE event, which the reweight module needs to recompute NLO matrix elements at full NLO accuracy. Without this setting, the reweight module falls back to LO-accuracy reweighting (with a warning message). When using the interactive launch menu with `reweight=ON`, `store_rwgt_info` is set automatically.
- NLO reweighting recomputes both virtual and real-emission matrix elements, so it is significantly slower than LO reweighting.
- The reweight card syntax is identical to the LO case.
- NLO reweighting supports changing model parameters (couplings, masses) but the same limitations on cuts and beam energy apply.
- For NLO+PS (matched) samples, the reweighting applies to the hard-event weights. Shower effects are not re-evaluated.

```
# NLO process with reweighting
import model loop_sm
generate p p > t t~ [QCD]
output my_nlo_ttbar
launch my_nlo_ttbar
  reweight=ON
  shower=PYTHIA8
  set run_card nevents 10000
  done
```

| Source | Method | Typical Size (LO) | Typical Size (NLO) |
|--------|--------|-------------------|---------------------|
| Scale (μ_R, μ_F) | 7-point envelope via `sys_scalefact` | ±30-50% | ±10-20% |
| PDF | Error set via `sys_pdf` | ±5-15% | ±3-10% |
| Matching/merging | Vary xqcut/qCut | ±5-20% | ±5-15% |
| Shower modeling | Compare Pythia8 vs Herwig | ±5-15% | ±5-10% |
| Model parameters | Vary BSM parameters | Process-dependent | Process-dependent |
