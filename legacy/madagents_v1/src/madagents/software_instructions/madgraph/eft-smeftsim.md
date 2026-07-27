# 26 — EFT Models and SMEFTsim

This document covers how to use EFT (Effective Field Theory) models in MadGraph5, with a focus on the SMEFTsim package. It covers model installation, coupling order syntax for separating SM/interference/BSM-squared contributions, param_card structure, restriction file pitfalls, and complete worked examples.

## Contents

- [Available EFT Models](#available-eft-models)
- [Installing EFT Models](#installing-eft-models)
  - [Auto-download via `import model`](#auto-download-via-import-model)
  - [Manual installation](#manual-installation)
  - [SMEFTsim Model Variants](#smeftsim-model-variants)
- [SMEFTsim Restriction Files](#smeftsim-restriction-files)
  - [Custom restriction files](#custom-restriction-files)
- [Coupling Orders in SMEFTsim](#coupling-orders-in-smeftsim)
  - [How `NPprop=0` Works](#how-npprop0-works)
  - [Relationship Between NP, QED, and QCD](#relationship-between-np-qed-and-qcd)
- [Separating SM, Interference, and BSM-Squared](#separating-sm-interference-and-bsm-squared)
  - [Complete Example: $pp \to t\bar{t}$ with SMEFTsim](#complete-example-pp-to-tbart-with-smeftsim)
- [Wilson Coefficient Naming](#wilson-coefficient-naming)
  - [Chromomagnetic dipole operator ($\mathcal{O}_{uG}$) example](#chromomagnetic-dipole-operator-mathcalo_ug-example)
  - [Common operators for top studies (in `top` / `topU3l` variants)](#common-operators-for-top-studies-in-top-topu3l-variants)
  - [Mapping between SMEFTsim and SMEFTatNLO](#mapping-between-smeftsim-and-smeftatnlo)
- [Setting Wilson Coefficients](#setting-wilson-coefficients)
- [Common Pitfalls](#common-pitfalls)
- [SMEFTatNLO: NLO QCD Corrections for SMEFT](#smeftatnlo-nlo-qcd-corrections-for-smeft)
  - [SMEFTatNLO vs SMEFTsim: Key Differences](#smeftatnlo-vs-smeftsim-key-differences)
  - [SMEFTatNLO Restriction Cards](#smeftatnlo-restriction-cards)
  - [Separating SM, Interference, and BSM-Squared in SMEFTatNLO](#separating-sm-interference-and-bsm-squared-in-smeftatnlo)
  - [Complete NLO Example: $pp \to t\bar{t}$ with SMEFTatNLO](#complete-nlo-example-pp-to-tbart-with-smeftatnlo)
  - [SMEFTatNLO Wilson Coefficient Naming](#smeftatnlo-wilson-coefficient-naming)
  - [SMEFTatNLO Practical Notes](#smeftatnlo-practical-notes)

## Available EFT Models

Several EFT UFO models are commonly used with MadGraph5:

| Model | Basis | Coupling Order | Typical Use |
|-------|-------|---------------|-------------|
| `SMEFTsim` | Warsaw (complete dim-6) | `NP` | General SMEFT studies (LO) |
| `SMEFTatNLO` | Warsaw (subset) | `NP` | NLO QCD EFT with top/Higgs/EW |
| `dim6top` | Warsaw (top sector) | `DIM6` | Top-quark EFT studies (NLO QCD) |
| `EWdim6` | dim-6 EW operators | varies | Anomalous gauge couplings |

**None of these models ship with MadGraph5** — they must be obtained separately.

## Installing EFT Models

### Auto-download via `import model`

MadGraph maintains a database of UFO models hosted on the FeynRules wiki. Any UFO model posted there is automatically detected and made available for download. To use this:

```
import model SMEFTsim_U35_MwScheme_UFO
```

MadGraph will download the tarball from the FeynRules database and install it into `<MG5_DIR>/models/`. This works for models registered on the FeynRules wiki, including SMEFTsim.

### Manual installation

If auto-download fails (e.g., network issues, model not in database), install manually:

```bash
cd <MG5_DIR>/models/
# Download from the SMEFTsim GitHub: https://github.com/SMEFTsim/SMEFTsim
# Or from FeynRules: https://feynrules.irmp.ucl.ac.be/wiki/SMEFT
# Extract the UFO directory into <MG5_DIR>/models/
```

**Important**: Do not overwrite `models/__init__.py` when extracting.

### SMEFTsim Model Variants

SMEFTsim provides 10 model variants combining 5 flavor assumptions and 2 electroweak input schemes.

**Flavor assumptions:**

| Flavor | Symmetry | Description |
|--------|----------|-------------|
| `U35` | U(3)⁵ | Minimal flavor violation, fewest parameters. Flavor-universal Wilson coefficients. |
| `MFV` | Linear MFV | Minimal Flavor Violation |
| `top` | U(2)³ quark, U(1)³ lepton | For top physics. Third-generation quarks distinguished. |
| `topU3l` | U(2)³ quark, U(3)² lepton | For top physics with simplified lepton sector. |
| `general` | None | Full flavor structure — most parameters. |

**EW input schemes:**

| Scheme | Input Parameters |
|--------|------------------|
| `MwScheme` | ($M_W$, $M_Z$, $G_F$) |
| `alphaScheme` | ($\alpha_{EW}$, $M_Z$, $G_F$) |

The model directory name follows: `SMEFTsim_<flavor>_<scheme>_UFO`.

**Choosing a flavor variant**: For top quark studies (e.g., $pp \to t\bar{t}$), use `top` or `topU3l`. For Higgs or electroweak studies, `U35` is common. The `general` variant has the most parameters but is slowest.

## SMEFTsim Restriction Files

Each SMEFTsim UFO model ships with two restriction files:

| Restriction | File | Wilson coefficients | Light quark masses |
|-------------|------|--------------------|-----------|
| `massless` | `restrict_massless.dat` | Set to **random distinct nonzero** values | Set to zero |
| `SMlimit_massless` | `restrict_SMlimit_massless.dat` | Set to **zero** (SM limit) | Set to zero |

**Critical distinction**:

- **`-massless`**: Wilson coefficients are nonzero → all EFT vertices are present → the `NP` coupling order is available on the `generate` line. **Use this restriction for EFT studies.**
- **`-SMlimit_massless`**: All Wilson coefficients are zero → all EFT vertices are **removed** from the model → the `NP` coupling order is **not valid**. Using `NP==1` on the `generate` line produces the error: `model order NP not valid for this model`. This restriction is only useful as a starting template for a custom restriction.

```
# CORRECT — use the massless restriction (NP coupling order preserved)
import model SMEFTsim_U35_MwScheme_UFO-massless
generate p p > t t~ NP==1
# Works: NP coupling order is defined

# WRONG — SMlimit_massless removes all EFT vertices
import model SMEFTsim_U35_MwScheme_UFO-SMlimit_massless
generate p p > t t~ NP==1
# ERROR: model order NP not valid for this model
```

### Custom restriction files

To create a custom restriction that activates only specific Wilson coefficients:

1. Copy `restrict_SMlimit_massless.dat` to a new file, e.g., `restrict_mytop.dat`.
2. Set the Wilson coefficients you need to **random distinct nonzero values** (not all the same, not 1.0, not special values like `9.999e-01` or `1e-99`). Good choices: `0.327`, `0.891`, `0.542`, etc.
3. Leave all other Wilson coefficients at exactly `0`.
4. Load the custom restriction: `import model SMEFTsim_U35_MwScheme_UFO-mytop`

**Why random distinct values?** MadGraph uses restriction file values to determine which vertices to keep. If values match certain patterns (all equal, equal to 1, or near-zero), safety checks may incorrectly remove diagrams.

## Coupling Orders in SMEFTsim

SMEFTsim defines several coupling orders beyond the standard `QCD` and `QED`:

| Coupling Order | Meaning | `expansion_order` | Effect |
|---------------|---------|-------------------|--------|
| `NP` | Total new physics order (counts dim-6 operator insertions per amplitude) | 99 | No automatic constraint |
| `NPprop` | NP insertions in propagator corrections only | **0** | **Automatically excluded** unless explicitly requested |
| `NPcpv` | CP-violating NP interactions | 99 | No automatic constraint |
| `NPshifts` | Idle in v3.0+ (parameter shifts absorbed) | 99 | No automatic constraint |
| `SMHLOOP` | SM radiative Higgs couplings (hgg, hγγ, hZγ) | 99 | No automatic constraint |
| `NP<name>` | Per-operator coupling order (e.g., `NPcuG`, `NPcHG`) | 99 | No automatic constraint |

### How `NPprop=0` Works

`NPprop` has `expansion_order = 0` in the UFO model. This means MadGraph automatically excludes all propagator-correction vertices (linearized SMEFT corrections to W/Z/H/top propagators) unless you explicitly request them:

```
# Default behavior: NPprop contributions excluded (expansion_order=0)
generate p p > t t~ NP==1
# Only contact-interaction EFT diagrams

# Explicitly include propagator corrections:
generate p p > t t~ NP==1 NPprop<=2
```

### Relationship Between NP, QED, and QCD

The vast majority of EFT vertices in SMEFTsim carry both an `NP` order and a `QED` order (because dim-6 operators typically involve electroweak couplings). However, a small number of EFT vertices have `QED=0`:

- **Propagator corrections** (`NPprop` vertices): Some carry `QED=0`.
- **Higgs-gluon operators** (`cHG`, `cHGtil`): The $\mathcal{O}_{HG} = H^\dagger H \, G_{\mu\nu}^a G^{a\mu\nu}$ operator modifies the H-g-g vertex, which is a pure QCD+NP interaction with no electroweak coupling.
- **Higgs self-coupling** (`cH`): The $\mathcal{O}_H = (H^\dagger H)^3$ operator modifies the Higgs self-interaction without involving gauge couplings.

**Practical consequence**: Do not rely on `QED` order alone to separate SM from EFT contributions. Always use `NP` and `NP^2` for this purpose.

Some EFT operators (notably the chromomagnetic operator $\mathcal{O}_{uG}$) allow gluon emission that is not proportional to $\alpha_s$. This means diagrams with external gluons can appear even when `QCD=0` is specified. Use `NP` constraints instead of `QCD`/`QED` to control EFT contributions.

## Separating SM, Interference, and BSM-Squared

For EFT studies, the cross-section decomposes as:
$$\sigma = \sigma_{\text{SM}} + \sigma_{\text{int}} \cdot C_i / \Lambda^2 + \sigma_{\text{BSM}^2} \cdot C_i^2 / \Lambda^4$$

Use `NP^2` (squared coupling order) to isolate each piece:

| Component | Syntax | Physical Meaning |
|-----------|--------|------------------|
| SM only | `NP^2==0` | Pure SM (no EFT operators) |
| SM + interference | `NP<=1 NP^2==2` | Linear EFT: SM × EFT interference |
| BSM-squared only | `NP^2==4` | Quadratic EFT: EFT × EFT |
| SM + interference + BSM² | `NP<=2` | Full dim-6 contribution |

### Complete Example: $pp \to t\bar{t}$ with SMEFTsim

Using the `top` flavor variant (recommended for top studies):

```
# === SM-only contribution ===
import model SMEFTsim_top_MwScheme_UFO-massless
generate p p > t t~ NP^2==0 SMHLOOP=0
output tt_SM
launch tt_SM
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done

# === Interference (linear EFT) ===
import model SMEFTsim_top_MwScheme_UFO-massless
generate p p > t t~ NP==1 NP^2==2 SMHLOOP=0
output tt_interference
launch tt_interference
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  set param_card SMEFT 15 1.0    # ctGRe (chromomagnetic dipole)
  done

# === BSM-squared (quadratic EFT) ===
import model SMEFTsim_top_MwScheme_UFO-massless
generate p p > t t~ NP^2==4 SMHLOOP=0
output tt_bsm2
launch tt_bsm2
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  set param_card SMEFT 15 1.0    # ctGRe
  done
```

**Key points:**
- `NP^2==0`: Selects only diagrams with zero NP insertions in |M|² → pure SM.
- `NP==1 NP^2==2`: Amplitudes have exactly one NP insertion, and |M|² has two NP powers (SM amplitude × EFT amplitude) → interference only.
- `NP^2==4`: Two NP powers in each amplitude → BSM-squared only.
- `SMHLOOP=0`: Excludes SM loop-induced Higgs couplings (hgg, hγγ) to avoid double-counting with explicit EFT operators like `cHG`.

## Wilson Coefficient Naming

Wilson coefficient names in the param_card depend on the **flavor variant**. The same physical operator has different names across variants:

### Chromomagnetic dipole operator ($\mathcal{O}_{uG}$) example

| Flavor variant | param_card name | Block | Notes |
|---------------|----------------|-------|-------|
| `U35` | `cuGRe`, `cuGIm` | `SMEFT`, `SMEFTcpv` | Flavor-universal: applies to all up-type quarks |
| `top` / `topU3l` | `ctGRe`, `ctGIm` | `SMEFT`, `SMEFTcpv` | Third-generation specific |
| `general` | `cuG1x3Re` (etc.) | `SMEFT`, `SMEFTcpv` | Full flavor indices |

### Common operators for top studies (in `top` / `topU3l` variants)

| Operator | Real part | Imaginary part | Description |
|----------|-----------|---------------|-------------|
| $\mathcal{O}_{tG}$ | `ctGRe` | `ctGIm` | Chromomagnetic dipole |
| $\mathcal{O}_{tW}$ | `ctWRe` | `ctWIm` | Weak dipole |
| $\mathcal{O}_{tB}$ | `ctBRe` | `ctBIm` | Hypercharge dipole |
| $\mathcal{O}_{Hq}^{(1)}$ | `cHQ1` | — | Higgs-quark current (singlet) |
| $\mathcal{O}_{Hq}^{(3)}$ | `cHQ3` | — | Higgs-quark current (triplet) |
| $\mathcal{O}_{Ht}$ | `cHt` | `cHtbRe` | Higgs-top current |
| $\mathcal{O}_{tH}$ | `ctHRe` | `ctHIm` | Top Yukawa correction |

### Mapping between SMEFTsim and SMEFTatNLO

SMEFTatNLO uses different names for the same operators:

| SMEFTsim (`top`) | SMEFTatNLO | Warsaw notation |
|-------------------|------------|----------------|
| `ctGRe` | `ctG` | $\mathcal{O}_{tG}$ |
| `cHGRe` | `cpG` | $\mathcal{O}_{HG}$ |
| `ctHRe` | `ctp` | $\mathcal{O}_{tH}$ |

**Important**: SMEFTsim v3 uses the `Re`/`Im` suffix convention. Earlier versions (v2) used `Abs`/`Ph` (absolute value / phase). Always check which version you are using.

To discover parameter names for a specific model variant, use:

```
import model SMEFTsim_top_MwScheme_UFO-massless
display parameters
```

Or inspect the param_card directly: `<MG5_DIR>/models/SMEFTsim_top_MwScheme_UFO/restrict_massless.dat`.

## Setting Wilson Coefficients

Wilson coefficients are set via the param_card. In SMEFTsim, they appear in two blocks:

- **`SMEFT`** — CP-even (real parts)
- **`SMEFTcpv`** — CP-odd (imaginary parts)

Set coefficients in a launch script:

```
launch my_output
  set param_card SMEFT 15 1.0      # ctGRe = 1.0 (in top variant)
  set param_card SMEFTcpv 15 0.0   # ctGIm = 0.0
  done
```

Or edit the param_card directly and modify the relevant block entries.

**Reminder**: The restriction file determines which operators are **present** in the model. If a Wilson coefficient is zero in the restriction file, the corresponding vertex is removed and cannot be restored by setting a nonzero value in the param_card.

## Common Pitfalls

1. **Wrong restriction file**: Using `-SMlimit_massless` instead of `-massless` removes all EFT vertices. Error: `model order NP not valid for this model`.

2. **Wrong parameter name**: Wilson coefficient names depend on the flavor variant. `ctGRe` is valid in the `top` variant but not in `U35` (use `cuGRe` instead).

3. **Missing `SMHLOOP=0`**: Without this, SM loop-induced Higgs couplings (hgg, hγγ, hZγ) are included, which can double-count contributions from EFT operators like `cHG`.

4. **Relying on QED/QCD to separate EFT**: A few EFT operators (chromomagnetic dipole, Higgs-gluon operators) allow gluon emission not proportional to $\alpha_s$. Use `NP` and `NP^2` instead of `QCD`/`QED` for EFT separation.

5. **Identical restriction values**: Setting all active Wilson coefficients to the same value (e.g., all `1.0`) can cause MadGraph to merge couplings, producing silently wrong results. Use random distinct values.

6. **NPprop not included**: Propagator corrections are excluded by default (`NPprop` has `expansion_order=0`). If you need them, add `NPprop<=2` to the generate line.

## SMEFTatNLO: NLO QCD Corrections for SMEFT

SMEFTatNLO is a dedicated UFO model supporting automated NLO QCD corrections for a broad set of dimension-6 SMEFT operators. It includes UV counterterms and R2 rational terms required for one-loop renormalization.

**Reference**: Degrande et al., *Automated one-loop computations in the SMEFT*, [arXiv:2008.11743](https://arxiv.org/abs/2008.11743), Phys. Rev. D 103, 096024 (2021). Model available from [FeynRules](https://feynrules.irmp.ucl.ac.be/wiki/SMEFTatNLO).

### SMEFTatNLO vs SMEFTsim: Key Differences

| Property | SMEFTsim | SMEFTatNLO |
|----------|----------|------------|
| Accuracy | LO only | NLO QCD |
| **NP order per EFT vertex** | **NP = 1** | **NP = 2** |
| Flavor symmetry | 5 variants (U35, MFV, top, topU3l, general) | Fixed: U(2)_q × U(2)_u × U(3)_d × [U(1)_l × U(1)_e]³ |
| EW input scheme | MwScheme or alphaScheme | Fixed: ($G_F$, $M_Z$, $M_W$) |
| Operator naming | `ctGRe` / `ctGIm` (v3) | `ctG` (real, no Re/Im suffix) |
| Restriction for EFT studies | `-massless` | `-NLO` (NLO) or `-LO` (LO) |
| Default (no restriction) | Includes all vertices | **Pure SM only** — all EFT vertices removed |
| Wilson coefficient block | `SMEFT` / `SMEFTcpv` | `DIM6` (use `display parameters` to verify) |

> **Critical: NP order per vertex** — In SMEFTsim, each EFT vertex carries `NP=1`. In SMEFTatNLO, each EFT vertex carries `NP=2`. This means coupling-order syntax for separating SM/interference/BSM² is **different** between the two models. Commands written for SMEFTsim (e.g., `NP<=1 NP^2==2`) generate **zero amplitudes** in SMEFTatNLO.

### SMEFTatNLO Restriction Cards

| Restriction | Import syntax | Effect |
|-------------|--------------|--------|
| (none) | `import model SMEFTatNLO` | Pure SM — all EFT vertices removed |
| `-NLO` | `import model SMEFTatNLO-NLO` | EFT vertices active, NLO counterterms included |
| `-LO` | `import model SMEFTatNLO-LO` | EFT vertices active, LO only |
| `-NLO_no4q` | `import model SMEFTatNLO-NLO_no4q` | NLO with four-quark operators excluded (for MG5 v2.X compatibility) |

**Always use `-NLO` for NLO computations and `-LO` for LO computations.** Importing without a restriction loads pure SM with no EFT vertices.

> **Note on `-NLO_no4q`**: The restriction file is `restrict_NLO_no4q.dat`. The FeynRules wiki may show `SMEFTatNLO-no4q`, but on current installations the correct import is `SMEFTatNLO-NLO_no4q`. Using `-no4q` alone fails because `restrict_no4q.dat` does not exist, and even if it did, the `-NLO` part is required to activate EFT vertices.

### Separating SM, Interference, and BSM-Squared in SMEFTatNLO

Because SMEFTatNLO assigns `NP=2` per EFT vertex (not `NP=1`), the coupling-order syntax is different from SMEFTsim. **Do not use the SMEFTsim separation table for SMEFTatNLO.**

#### At LO (SMEFTatNLO-LO)

At LO, both `NP^2==` (equality) and `NP^2<=` (inequality) are supported:

| Component | SMEFTatNLO syntax | Notes |
|-----------|-------------------|-------|
| SM only | `NP^2==0` | No EFT insertions |
| Interference only | `NP<=2 NP^2==2` | Note: `NP<=2`, **not** `NP<=1` |
| SM + interference | `NP<=2 NP^2<=2` | Includes NP^2=0 (SM) and NP^2=2 (int) |
| BSM-squared only | `NP^2==4` | EFT × EFT |
| Full | `NP<=2` | All contributions |

```
# CORRECT — SMEFTatNLO LO interference
import model SMEFTatNLO-LO
generate p p > t t~ QCD=2 QED=0 NP<=2 NP^2==2

# WRONG — NP<=1 excludes all EFT amplitudes (vertices carry NP=2)
import model SMEFTatNLO-LO
generate p p > t t~ QCD=2 QED=0 NP<=1 NP^2==2
# Result: No amplitudes generated
```

#### At NLO — Only `NP^2<=` Is Supported

**At NLO (with `[QCD]`), MadGraph only supports `<=` for squared coupling order constraints.** Using `==` produces:

```
The squared-order constraints passed are not <=.
Other kind of squared-order constraints are not supported at NLO.
```

This is a fundamental limitation of the aMC@NLO framework — it applies to **all** NLO processes, not just SMEFTatNLO.

**Consequence**: You cannot directly isolate the interference (`NP^2==2`) or BSM-squared (`NP^2==4`) at NLO in a single `generate` command. Use inclusive `<=` constraints and obtain individual components by **subtraction**.

#### NLO Separation by Subtraction

Generate three separate processes and subtract cross-sections:

| Run | `generate` command | Contains |
|-----|-------------------|----------|
| A | `p p > t t~ QCD=2 QED=0 NP=0 [QCD]` | SM only |
| B | `p p > t t~ QCD=2 QED=0 NP<=2 NP^2<=2 [QCD]` | SM + interference |
| C | `p p > t t~ QCD=2 QED=0 NP<=2 [QCD]` | SM + interference + BSM² |

Then:
- **SM at NLO** = Run A
- **Interference at NLO** = Run B − Run A
- **BSM-squared at NLO** = Run C − Run B

### Complete NLO Example: $pp \to t\bar{t}$ with SMEFTatNLO

```
# === Run A: Pure SM at NLO ===
import model SMEFTatNLO-NLO
generate p p > t t~ QCD=2 QED=0 NP=0 [QCD]
output tt_SM_NLO
launch tt_SM_NLO
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 50000
  done

# === Run B: SM + interference at NLO ===
import model SMEFTatNLO-NLO
generate p p > t t~ QCD=2 QED=0 NP<=2 NP^2<=2 [QCD]
output tt_SM_int_NLO
launch tt_SM_int_NLO
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 50000
  set ctG 1.0
  done

# === Run C: Full (SM + int + quad) at NLO ===
import model SMEFTatNLO-NLO
generate p p > t t~ QCD=2 QED=0 NP<=2 [QCD]
output tt_full_NLO
launch tt_full_NLO
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 50000
  set ctG 1.0
  done
```

**Key points:**
- `NP=0` in Run A excludes all EFT vertices → pure SM.
- `NP<=2 NP^2<=2` in Run B includes SM (NP=0) and EFT (NP=2) amplitudes, but only |M|² terms with NP² ≤ 2 → excludes BSM² (NP²=4).
- `NP<=2` in Run C includes all contributions.
- Interference = σ(B) − σ(A); BSM-squared = σ(C) − σ(B).

### SMEFTatNLO Wilson Coefficient Naming

| SMEFTatNLO | SMEFTsim (`top`) | Operator |
|------------|-----------------|----------|
| `ctG` | `ctGRe` | Chromomagnetic dipole $\mathcal{O}_{tG}$ |
| `cpG` | `cHGRe` | Higgs-gluon $\mathcal{O}_{HG}$ |
| `ctp` | `ctHRe` | Top Yukawa correction $\mathcal{O}_{tH}$ |
| `ctW` | `ctWRe` | Weak dipole $\mathcal{O}_{tW}$ |
| `ctZ` | — | $Z$-dipole (linear combination) |
| `cQq83` | — | Four-quark operator |
| `cQq13` | — | Four-quark operator |

**Normalization**: The chromomagnetic dipole in SMEFTatNLO includes an explicit factor of $g_s$: $c_{tG}^{\text{LHC-TOPWG}} = g_s \cdot c_{tG}^{\text{SMEFTatNLO}}$. Consult the `definitions.pdf` available from the [FeynRules SMEFTatNLO wiki page](https://feynrules.irmp.ucl.ac.be/wiki/SMEFTatNLO) for all normalizations (this file is not included in the UFO model directory).

To discover parameter names and block structure for your specific version:

```
import model SMEFTatNLO-NLO
display parameters
```

### SMEFTatNLO Practical Notes

1. **MG5 version requirement**: MG5 v3.1.X or later is required for four-quark operators at NLO and for `cpG`. On MG5 v2.X, use `import model SMEFTatNLO-NLO_no4q` to exclude four-quark operators.

2. **Wilson coefficient scale**: The EFT cutoff scale `Lambda` (Block `DIM6`, lhacode `[1]`) defaults to 1000 GeV. The EFT renormalization scale `mueft` (Block `Renor`) defaults to 91.18 GeV (≈ $M_Z$), distinct from $\mu_R$/$\mu_F$. No RG evolution is performed. Do not confuse the two: `Lambda` is the $1/\Lambda^2$ suppression scale, while `mueft` is the scale at which Wilson coefficients are defined.

3. **Interference numerical challenges**: Interference contributions obtained by subtraction can suffer from large cancellations when the interference is much smaller than σ_SM. Compare `sde_strategy 1` and `sde_strategy 2`; increase `nevents` significantly.

4. **MadSpin limitation**: MadSpin does **not** support squared coupling order constraints. Using `NP^2<=2` with MadSpin decay chains produces: `Decay processes cannot specify squared orders constraints`. Decay heavy particles via Pythia8 or use MadGraph decay chain syntax at generation time.

5. **Scalar/tensor QQℓℓ operators**: The coefficients `ctlT3` and `cblS3` (Block `DIM64F2L`) have active vertices for third-generation quarks and leptons at LO but break the model's flavor symmetry assumption and are **not available for NLO computations** — use only with `-LO`. The coefficient `ctlS3` is entirely inert: it appears in the parameter card but has no couplings and no vertices at any order, so setting it has no effect on any amplitude.

6. **Excluded operators**: The triple-gluon operator ($\mathcal{O}_G$, coefficient `cG`), four-lepton vertices, and top-quark flavor-changing interactions are not available at any order.

7. **Reweighting for parameter scans**: Use `reweight_card.dat` for efficient scans over Wilson coefficients. Note that `NP^2==` syntax **does** work inside `change process` in the reweight card (reweighting operates at LO-reweighted level):

```
# In reweight_card.dat:
change process p p > t t~ QCD=2 QED=0 NP^2==2
launch --rwgt_name=int_ctG
  set ctG 1.0
```
