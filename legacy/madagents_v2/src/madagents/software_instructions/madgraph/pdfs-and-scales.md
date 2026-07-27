# PDFs, Scales, and Alpha_s

PDF selection, LHAPDF configuration, scale choices ($\mu_R$, $\mu_F$), and their interplay with $\alpha_s$ running in MadGraph5.

## Contents

- [PDF Selection in the Run Card](#pdf-selection-in-the-run-card)
  - [Built-In PDF Sets (`pdlabel`)](#built-in-pdf-sets-pdlabel)
  - [Using LHAPDF (`pdlabel = lhapdf`)](#using-lhapdf-pdlabel--lhapdf)
  - [Other `pdlabel` Options](#other-pdlabel-options)
- [LO vs NLO PDF Consistency](#lo-vs-nlo-pdf-consistency)
- [Per-Beam PDF Configuration](#per-beam-pdf-configuration)
- [LHAPDF Configuration](#lhapdf-configuration)
- [Flavor Number Consistency](#flavor-number-consistency)
- [4-Flavor vs 5-Flavor Scheme](#4-flavor-vs-5-flavor-scheme)
  - [5-Flavor Scheme (Default)](#5-flavor-scheme-default)
  - [4-Flavor Scheme](#4-flavor-scheme)
  - [When to Use Each](#when-to-use-each)
  - [Consistency Checklist for 4F](#consistency-checklist-for-4f)
- [PDF Uncertainties](#pdf-uncertainties)
- [Common Issues](#common-issues)
- [Scale Parameters in the Run Card](#scale-parameters-in-the-run-card)
- [Fixed vs Dynamical Scales](#fixed-vs-dynamical-scales)
- [Dynamical Scale Options](#dynamical-scale-options)
  - [When to Use Each](#when-to-use-each-1)
- [The `scalefact` Multiplier](#the-scalefact-multiplier)
- [Separate Factorization Scales per Beam](#separate-factorization-scales-per-beam)
- [The `alpsfact` Parameter](#the-alpsfact-parameter)
- [Scale Variations for Uncertainty Estimation](#scale-variations-for-uncertainty-estimation)
- [NLO Scale Choices](#nlo-scale-choices)

## PDF Selection in the Run Card

Two parameters control the PDF:

```
nn23lo1   = pdlabel   ! PDF set
230000    = lhaid      ! if pdlabel=lhapdf, this is the LHAPDF set ID
```

### Built-In PDF Sets (`pdlabel`)

MG5 ships with several built-in PDF sets that require no external installation:

| `pdlabel` value | PDF set | LHAPDF ID | Order | Use case |
|-----------------|---------|-----------|-------|----------|
| `nn23lo1` | NNPDF2.3 LO (set 1) | 247000 | LO | Default for LO computations |
| `nn23lo` | NNPDF2.3 LO | 246800 | LO | Alternative LO set |
| `nn23nlo` | NNPDF2.3 NLO | 244800 | NLO | NLO computations (basic) |
| `cteq6l1` | CTEQ6L1 | — | LO | Legacy LO set |
| `cteq6_l` | CTEQ6L | — | LO | Legacy LO set |
| `cteq6_m` | CTEQ6M | — | NLO | Legacy NLO set |

These sets are compiled into MG5 and work without LHAPDF. However, they are older sets — for publication-quality results, use LHAPDF with a modern PDF set.

### Using LHAPDF (`pdlabel = lhapdf`)

For modern PDF sets (NNPDF3.1, NNPDF4.0, CT18, MSHT20, etc.), set:

```
lhapdf  = pdlabel
303400  = lhaid       ! LHAPDF set ID (e.g. NNPDF3.1 NLO)
```

This requires LHAPDF to be installed and configured. See [Installation & Setup](installation.md) for installing LHAPDF via `install lhapdf6`.

The `lhaid` value is the LHAPDF ID number. Each PDF set has a unique ID. To find IDs, consult the [LHAPDF website](https://lhapdf.hepforge.org/pdfsets.html) or run:

```
lhapdf list
```

> **Warning — always verify IDs from the official index**: LHAPDF IDs cannot be reliably guessed from set names or by analogy with other families. For example, within the NNPDF3.x family, the LO set IDs (262000 = `NNPDF30_lo_as_0118`, 263000 = `NNPDF30_lo_as_0130`) are numerically *higher* than the NLO ID (260000 = `NNPDF30_nlo_as_0118`) — the opposite of the natural ordering. Using a wrong ID silently runs with the wrong PDF order, producing inconsistent results. Always look up the exact ID in the official LHAPDF index before use.

### Other `pdlabel` Options

| `pdlabel` | Description |
|-----------|-------------|
| `none` | No PDF (equivalent to `lpp = 0`). Used for fixed-energy lepton beams. |
| `iww` | Improved Weizsaecker-Williams approximation for photon emission from leptons. |
| `eva` | Effective Vector boson Approximation (W/Z/photon from fermions). |
| `edff` | Electron fragmentation function. |
| `chff` | Charged hadron fragmentation function. |

For lepton colliders, additional lepton-beam PDF sets may be available depending on the MG5 version — see [Lepton & Photon Colliders](lepton-photon-colliders.md).

## LO vs NLO PDF Consistency

A critical requirement: **the PDF order should be at least as high as the perturbative order of the calculation** (e.g., NLO or NNLO PDFs for NLO calculations). Using an LO PDF for an NLO calculation is inconsistent and gives unreliable results, because the PDF encodes not only alpha_s running at the corresponding order but also scheme-dependent splitting functions and coefficient functions whose higher-order terms are designed to cancel against the NLO partonic cross-section. An order mismatch breaks this cancellation, spoiling the perturbative convergence.

| Calculation | Acceptable PDF |
|-------------|-------------|
| LO | LO PDF set |
| NLO | NLO or NNLO PDF set |

Using NNLO PDFs with NLO matrix elements is standard practice and recommended by the PDF4LHC working group. The reverse — using an LO PDF with an NLO calculation — is problematic because the LO alpha_s running is inconsistent with the NLO matrix element.

In practice:
- For LO: use `nn23lo1` (built-in) or an LO LHAPDF set
- For NLO: use `nn23nlo` (built-in) or an NLO LHAPDF set (recommended)

## Per-Beam PDF Configuration

MG5 supports different PDFs for each beam via hidden parameters:

```
lhapdf  = pdlabel1    ! PDF for beam 1
lhapdf  = pdlabel2    ! PDF for beam 2
```

These are hidden by default. When `pdlabel` is set, it applies to both beams. Per-beam PDFs are mainly relevant for asymmetric colliders (e.g., ep collisions where one beam is a proton and the other an electron).

## LHAPDF Configuration

The path to the LHAPDF installation is configured in `mg5_configuration.txt`:

```
lhapdf_py3 = /path/to/lhapdf-config
```

After installation, PDF sets must be downloaded. LHAPDF stores sets in a data directory (typically `share/LHAPDF/`). To install a new PDF set:

```bash
lhapdf install NNPDF31_nlo_as_0118
```

Or download manually from the LHAPDF website and place in the LHAPDF data directory.

## Flavor Number Consistency

The number of active quark flavors in the PDF must be consistent with the physics model:

- **5-flavor scheme** (default): b-quark is massless and appears in the proton PDF. Use `sm-no_b_mass` or set `maxjetflavor = 5`.
- **4-flavor scheme**: b-quark is massive and does NOT appear in the proton PDF. Use `sm` (default) and set `maxjetflavor = 4`. Must use a 4-flavor PDF set.

Inconsistency between the flavor scheme in the model and the PDF can lead to wrong results, particularly for processes with b-quarks in the initial state.

## 4-Flavor vs 5-Flavor Scheme

The flavor scheme determines whether the b-quark is treated as a massive parton or a massless constituent of the proton.

### 5-Flavor Scheme (Default)

```
import model sm-no_b_mass
```

- b-quark is massless
- b appears in the proton PDF and in `p`/`j` multiparticle labels
- Resums large logs of the form ln(Q²/m_b²) via the PDF evolution
- Appropriate for most processes at high Q²

### 4-Flavor Scheme

```
import model sm
define p = g u c d s u~ c~ d~ s~     # explicitly exclude b from proton
```

- b-quark is massive (mb ≈ 4.7 GeV)
- b does NOT appear in the proton PDF or in `p`/`j`
- Appropriate when b-quark mass effects matter

In addition to the model choice, set in the run_card:

```
set run_card maxjetflavor 4    # for 4F scheme
set run_card maxjetflavor 5    # for 5F scheme (default with sm-no_b_mass)
```

And use a consistent PDF set (4F PDF for 4F scheme, 5F PDF for 5F scheme).

### When to Use Each

| 4-Flavor Scheme | 5-Flavor Scheme |
|----------------|-----------------|
| bb̄H associated production | Inclusive Higgs production |
| Single-top tW-channel | Single-top t-channel |
| When m_b effects matter | High-Q² processes |
| Low b-quark pT | b-quarks in initial state |

### Consistency Checklist for 4F

1. `import model sm` (massive b)
2. Redefine `p` and `j` to exclude b: `define p = g u c d s u~ c~ d~ s~`
3. `set run_card maxjetflavor 4`
4. Use a 4-flavor PDF set (e.g., NNPDF31_lo_as_0118_nf4)

## PDF Uncertainties

PDF uncertainties are evaluated using the `use_syst` mechanism in the run card. When enabled, MG5 stores reweighting information for PDF error sets in the LHE file. See [Systematics & Reweighting](systematics-reweighting.md) for details.

## Common Issues

1. **"LHAPDF not found"**: The `lhapdf_py3` path in `mg5_configuration.txt` is not set or points to a missing installation. Install via `install lhapdf6` in the MG5 interactive prompt.

2. **"PDF set not found"**: The requested `lhaid` corresponds to a PDF set that is not installed in the LHAPDF data directory. Download the set with `lhapdf install <setname>`.

3. **Wrong alpha_s**: If your cross-section disagrees with expectations, check that the PDF order matches the calculation order. The PDF choice automatically determines alpha_s.

4. **Manually set alpha_s ignored**: For proton beams (`lpp=1`), the `aS(MZ)` value in param_card Block SMINPUTS is **overridden** by the alpha_s value fitted to the chosen PDF set. This is physically correct — the PDF was extracted with a specific alpha_s. To study alpha_s variations, use the systematics reweighting module (see [Systematics & Reweighting](systematics-reweighting.md)), not the param_card.

## Scale Parameters in the Run Card

```
False  = fixed_ren_scale       ! if True, use fixed renormalization scale
False  = fixed_fac_scale       ! if True, use fixed factorization scale
91.188 = scale                 ! fixed ren scale (GeV), used when fixed_ren_scale = True
91.188 = dsqrt_q2fact1         ! fixed fac scale for beam 1 (GeV)
91.188 = dsqrt_q2fact2         ! fixed fac scale for beam 2 (GeV)
-1     = dynamical_scale_choice ! dynamical scale selection
1.0    = scalefact             ! multiplicative factor applied to the chosen scale
```

## Fixed vs Dynamical Scales

- **Fixed scales** (`fixed_ren_scale = True`): mu_R and mu_F are set to the values of `scale` and `dsqrt_q2fact1`/`dsqrt_q2fact2` respectively, the same for every event.
- **Dynamical scales** (`fixed_ren_scale = False`, default): mu_R and mu_F are computed event-by-event based on the kinematics, using the `dynamical_scale_choice` option. This is the recommended approach for most processes.

When using dynamical scales, the `scale` and `dsqrt_q2fact` values are ignored.

## Dynamical Scale Options

The `dynamical_scale_choice` parameter selects the dynamical scale definition. The allowed values differ between LO and NLO:

- **LO allowed values**: -1, 0, 1, 2, 3, 4
- **NLO allowed values**: -2, -1, 0, 1, 2, 3, 10

| Value | Definition | Formula | LO | NLO |
|-------|-----------|---------|:--:|:---:|
| **-2** | Negative of HT (NLO only) | $-\sum \sqrt{m^2 + p_T^2}$ | — | Yes |
| **-1** | CKKW back-clustering (LO) / HT/2 (NLO) | **LO**: Clusters final-state particles following the Feynman diagram topology back to a 2->2 core process; uses the geometric mean of clustering $p_T$ values at selected vertices in the clustering tree. **NLO**: equivalent to HT/2 (choice 3) — CKKW clustering is not implemented in the NLO code. | Yes | Yes |
| **0** | User-defined | Requires editing `SubProcesses/setscales.f` in the process directory | Yes | Yes |
| **1** | Total transverse energy | sum of $E_T$ for all final-state particles | Yes | Yes |
| **2** | HT | sum of transverse mass $\sqrt{m^2 + p_T^2}$ for all final-state particles | Yes | Yes |
| **3** | HT/2 | Half the sum of transverse mass | Yes | Yes |
| **4** | sqrt(s-hat) | Partonic center-of-mass energy | Yes | — |
| **10** | Geometric mean of particle masses (NLO only) | $(\prod m_i)^{1/n}$ for massive final-state particles | — | Yes |

### When to Use Each

- **-1 (CKKW, default)**: Good general-purpose choice at LO. Follows the structure of the Feynman diagram, giving process-aware scales. Required when using MLM matching (`ickkw = 1`). At NLO, this choice falls back to HT/2 (same as choice 3) — CKKW clustering is only implemented in the LO code.
- **1 (total E_T)**: Similar to HT but uses transverse energy instead of transverse mass.
- **2 (HT)**: Common choice for multi-jet or heavy-particle production (e.g., tt-bar + jets). Reflects the overall hardness of the event.
- **3 (HT/2)**: Popular choice for top-quark pair production and multi-jet processes. Often gives better perturbative convergence than HT.
- **4 (sqrt(s-hat), LO only)**: Fixed for a given collider energy in 2->2 processes. Useful for inclusive cross-sections. Not available at NLO.
- **0 (user-defined)**: For custom scale definitions. Edit the file `<PROC_DIR>/SubProcesses/setscales.f` — the subroutine `set_ren_scale` receives the four-momenta of all particles and must return the scale value.

## The `scalefact` Multiplier

> **Note:** `scalefact` is available only at LO. At NLO, use `mur_over_ref` and `muf_over_ref` instead (see [NLO Scale Choices](#nlo-scale-choices) below).

The `scalefact` parameter multiplies the dynamical scale:

```
mu_R = scalefact * (dynamical scale)
```

Default is 1.0. Common use: set `scalefact = 0.5` to use HT/2 when `dynamical_scale_choice = 2`, which is equivalent to using `dynamical_scale_choice = 3`.

## Separate Factorization Scales per Beam

The factorization scales for the two beams can be set independently via the hidden parameters `fixed_fac_scale1` and `fixed_fac_scale2`:

```
False  = fixed_fac_scale1   ! factorization scale for beam 1
False  = fixed_fac_scale2   ! factorization scale for beam 2
```

This is rarely needed — the main use case is asymmetric colliders where the two beams have very different characteristics.

## The `alpsfact` Parameter

The hidden parameter `alpsfact` (default 1.0) is used in MLM matching to control the alpha_s reweighting at clustering vertices. It multiplies the scale used for alpha_s evaluation at each QCD vertex found by the clustering algorithm. This is only relevant when `ickkw = 1`. See [Matching & Merging](matching-and-merging.md).

## Scale Variations for Uncertainty Estimation

Scale variations are the primary method for estimating perturbative uncertainties. The standard procedure is the 7-point envelope: vary mu_R and mu_F independently by factors of 0.5 and 2 around the central scale, excluding the two extreme anti-correlated combinations (mu_R=0.5, mu_F=2) and (mu_R=2, mu_F=0.5).

This is done automatically via the systematics module:

```
True    = use_syst
systematics = systematics_program
['--mur=0.5,1,2', '--muf=0.5,1,2', '--pdf=errorset'] = systematics_arguments
```

See [Systematics & Reweighting](systematics-reweighting.md) for details.

## NLO Scale Choices

At NLO, the run card has additional scale-related parameters:

- `mur_over_ref` and `muf_over_ref`: Ratios of mu_R/mu_ref and mu_F/mu_ref for the central scale. These are the NLO equivalents of the LO `scalefact` parameter (which is not available at NLO).
- `reweight_scale`: Whether to include scale variation weights in the output.
- `rw_rscale` and `rw_fscale`: Lists of scale factors for reweighting (default: `[1.0, 2.0, 0.5]`).

As with the LO systematics module, the NLO `reweight_scale` mechanism computes all 3x3 = 9 combinations of the `rw_rscale` and `rw_fscale` factor lists. The 7-point envelope (excluding the two extreme anti-correlated variations) is obtained post-hoc at analysis time, not by filtering during event generation.
