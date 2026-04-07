# 03 — Models

Built-in models, restriction files, BSM UFO model installation, and EW scheme selection.

## Contents

- [Loading a Model](#loading-a-model)
- [Built-In Models](#built-in-models)
  - [Electroweak Input Schemes in Built-In Models](#electroweak-input-schemes-in-built-in-models)
- [Restriction Files](#restriction-files)
  - [Why Restriction Files Matter](#why-restriction-files-matter)
  - [Mass vs. Yukawa Coupling in Restriction Files](#mass-vs-yukawa-coupling-in-restriction-files)
  - [What `sm-no_b_mass` Actually Does](#what-sm-no_b_mass-actually-does)
  - [Custom Restriction File for bbH in the 5-Flavor Scheme](#custom-restriction-file-for-bbh-in-the-5-flavor-scheme)
  - [Restriction File Values and Diagram Selection](#restriction-file-values-and-diagram-selection)
- [Exploring a Model](#exploring-a-model)
- [BSM Workflow](#bsm-workflow)
  - [Using an External BSM Model](#using-an-external-bsm-model)
  - [Using an External UFO Model](#using-an-external-ufo-model)
  - [Z' Resonance Search Example](#z-resonance-search-example)
- [The heft Model](#the-heft-model)
  - [Effective Vertices in the `heft` Model](#effective-vertices-in-the-heft-model)
  - [Higgs Pair Production (`g g > h h`) — HEFT Limitations](#higgs-pair-production-g-g-h-h-heft-limitations)
  - [Correct Approach: Loop-Induced `g g > h h`](#correct-approach-loop-induced-g-g-h-h)
  - [Internal vs. External Parameters](#internal-vs-external-parameters)
  - [Higgs Trilinear Coupling in `loop_sm` — A Common Pitfall](#higgs-trilinear-coupling-in-loop_sm-a-common-pitfall)
  - [Studying Modified Trilinear Couplings in `g g > h h`](#studying-modified-trilinear-couplings-in-g-g-h-h)
- [Merging Models with `add model`](#merging-models-with-add-model)
  - [Syntax](#syntax)
  - [What the Merge Does](#what-the-merge-does)
  - [The `hgg_plugin` — Built-In Effective ggH Plugin](#the-hgg_plugin-built-in-effective-ggh-plugin)
  - [Practical Workflow — Gluon-Fusion Higgs + Decay in a BSM Model](#practical-workflow-gluon-fusion-higgs-decay-in-a-bsm-model)
  - [Caveats](#caveats)
- [The loop_sm Model](#the-loop_sm-model)
- [FeynRules Integration](#feynrules-integration)
- [Model Verification](#model-verification)

## Loading a Model

```
import model sm
```

This loads the Standard Model. The `import model` command resets the session: any previously defined processes are cleared.

## Built-In Models

MG5 ships with several UFO model directories:

| Model | Description | Use Case |
|-------|-------------|----------|
| `sm` | Standard Model (4-flavor, massive b) | Default for most LO computations |
| `sm-no_b_mass` | SM with massless b-quark (5-flavor) | When b is in the proton/jet definition |
| `loop_sm` | SM with loop amplitudes | Required for NLO computations (`[QCD]`) |
| `heft` | SM + effective ggH vertex | Fast Higgs via gluon fusion (valid for mH << 2mt) |
| `MSSM_SLHA2` | Minimal Supersymmetric SM (SLHA2 format) | SUSY studies |

Models like `2HDM` (Two-Higgs-Doublet Model) and `EWdim6` (dimension-6 EFT) are **not** shipped with MG5 — download them from the [FeynRules model database](https://feynrules.irmp.ucl.ac.be/wiki/ModelDatabaseMainPage) and place in `<MG5_DIR>/models/`.

### Electroweak Input Schemes in Built-In Models

The EW input scheme determines which parameters are independent inputs and which are derived:

| Model | EW scheme | Primary EW inputs | Derived from inputs |
|-------|-----------|-------------------|---------------------|
| `sm`, `loop_sm` | **alpha(MZ)** | `aEWM1` (= 1/α at M_Z), `Gf`, `MZ` | `MW` (computed via tree-level EW relation from aEWM1, Gf, MZ) |
| `loop_qcd_qed_sm_Gmu` | **Gmu** | `Gf`, `MZ`, `MW` | `aEWM1` (= 1/α, derived from G_F, M_Z, M_W) |

The `loop_qcd_qed_sm_Gmu` model is **not bundled** with MG5, but it is automatically downloaded from the MadGraph model database on first use — simply run `import model loop_qcd_qed_sm_Gmu` and MG5 will fetch and install it.

**Key point**: In the default `sm` model, `MW` is an **internal (derived) parameter** — it is not written to the generated param_card and cannot be independently overridden. Setting `MW` directly has no effect; MadGraph computes it from `aEWM1`, `Gf`, and `MZ` (the third EW input comes from the MASS block, not SMINPUTS). To treat `MW` as an independent input, use `loop_qcd_qed_sm_Gmu` or a custom model. See [Cards & Parameters](cards-and-parameters.md#sminputs-block--sm-input-parameters) for details.

## Restriction Files

Restriction files set specific parameters to zero or fixed values, enabling MG5 to simplify the computation (e.g., subprocess grouping for massless quarks).

```
import model sm-no_b_mass
```

The part after `-` corresponds to a file `restrict_no_b_mass.dat` inside the model's UFO directory. The default restriction file (`restrict_default.dat`) is loaded automatically when no restriction is specified:

```
import model sm          # loads restrict_default.dat
import model sm-full     # loads restrict_full.dat (no simplifications)
```

### Why Restriction Files Matter

### Mass vs. Yukawa Coupling in Restriction Files

In the SM UFO model, particle masses and Yukawa couplings are **independent parameters**. The b-quark has two relevant entries:

| Block | ID | Parameter | Meaning |
|-------|----|-----------|---------|
| `MASS` | 5 | `MB` | b-quark pole mass (kinematics, phase space, PDFs) |
| `YUKAWA` | 5 | `ymb` | b-quark Yukawa coupling (Hbb vertex strength) |

Setting `MB = 0` makes the b-quark massless for kinematics (enabling it to appear as a parton in 5-flavor PDFs and in multiparticle labels like `p` and `j`). Setting `ymb = 0` removes the Hbb interaction vertex entirely.

### What `sm-no_b_mass` Actually Does

The restriction file `restrict_no_b_mass.dat` sets **both** `MB = 0` **and** `ymb = 0`. This means:

- The b-quark is massless (included in `p` and `j` definitions).
- The Hbb Yukawa vertex is **removed** — any diagram that requires a Higgs–b-quark Yukawa coupling will not be generated.

```
# Inside restrict_no_b_mass.dat:
Block MASS
  5  0.000000e+00   # MB  (massless b)
Block YUKAWA
  5  0.000000e+00   # ymb (Hbb Yukawa vertex removed!)
```

This is correct for processes where the b-quark appears only as a light parton (e.g., `p p > t t~` in the 5-flavor scheme) but **wrong** for any process that relies on the Hbb Yukawa coupling.

**Important subtlety**: Setting `ymb = 0` only removes diagrams mediated by the Hbb Yukawa vertex. Processes like `p p > h b b~` may still produce diagrams through other vertices (e.g., Higgs-strahlung topologies via `Z* > b b~`). This can be misleading — the process generates diagrams, but the Yukawa-mediated contribution (typically the dominant one for bbH studies) is absent. To verify which diagrams remain, use `display diagrams` after process generation.

The cleanest test for whether the Yukawa vertex is present is `b b~ > h`, which proceeds **only** through the Hbb Yukawa coupling. With `sm-no_b_mass`, this produces zero diagrams:

```
import model sm-no_b_mass
generate b b~ > h
# Result: 0 diagrams — the Yukawa vertex is absent
```

### Custom Restriction File for bbH in the 5-Flavor Scheme

To study Higgs production via b-quark Yukawa couplings in the 5-flavor scheme, create a custom restriction file that keeps `MB = 0` but retains a nonzero `ymb`:

1. Copy the default restriction file:
   ```bash
   cp <MG5_DIR>/models/sm/restrict_no_b_mass.dat <MG5_DIR>/models/sm/restrict_no_b_mass_Hbb.dat
   ```

2. Edit `restrict_no_b_mass_Hbb.dat` — set `ymb` to a nonzero value while keeping `MB = 0`:
   ```
   Block MASS
     5  0.000000e+00   # MB  (massless b for 5FS kinematics)
   Block YUKAWA
     5  4.700000e+00   # ymb (nonzero to preserve Hbb vertex)
   ```

3. Load the custom restriction:
   ```
   import model sm-no_b_mass_Hbb
   generate b b~ > h
   # Now produces diagrams via the Yukawa vertex
   ```

**Key points:**
- `sm-no_b_mass` removes **both** `MB` and `ymb`. Do not use it for processes requiring the Hbb Yukawa vertex.
- For bbH in the 5FS, always create a custom restriction with `MB = 0`, `ymb ≠ 0`.
- The same principle applies to other quarks: setting a quark mass to zero in a restriction file typically also zeros its Yukawa coupling. Always check both `MASS` and `YUKAWA` blocks.
- The `ymb` value can be changed later via the param_card at launch time — but **only** if it was nonzero in the restriction file. If the restriction file set `ymb = 0`, the Hbb vertex is permanently removed from the model at `import model` time and cannot be restored by changing the param_card.
- The default SM restriction file (`restrict_default.dat`) sets `ymb = 4.7 GeV`, matching the pole mass `MB = 4.7 GeV`. When creating a custom restriction for 5FS bbH, a common choice is to keep `ymb = 4.7` (the default) or set it to the running b-quark mass (~4.18 GeV). What matters at the restriction-file stage is that `ymb` is **nonzero** so the Hbb vertex is not removed from the model.
- Alternatively, use `sm` (4-flavor scheme with massive b) for bbH if 5FS is not required — the Hbb vertex is present by default.

Without a restriction file that sets light quark masses to zero, MG5 cannot group subprocesses for different quark flavors together. This dramatically increases computation time. If a FeynRules-generated model runs much slower than the built-in SM for the same process, the likely cause is that light quarks have nonzero masses in the model. The fix is to create a restriction file setting `MU`, `MD`, `MS`, `MC` to zero.

To create a restriction file:
1. Copy `restrict_default.dat` to `restrict_MYNAME.dat` inside the model directory.
2. Set the desired masses/parameters to zero.
3. Load with `import model MYMODEL-MYNAME`.

### Restriction File Values and Diagram Selection

MG5 uses restriction file parameter values not only to remove vertices (when parameters are zero) but also to optimize the model's internal coupling structure. This optimization can have unintended consequences for models with many free parameters, particularly EFT models:

- **Parameters set to zero**: All vertices depending on these parameters are removed. This is the intended behavior for disabling operators.
- **Parameters set to identical non-zero values**: MG5 may identify these as equal and merge the corresponding couplings, silently producing incorrect results when the parameters are later set to different values in the param_card.
- **Parameters set to 1.0**: This value can trigger additional coupling simplifications in MG5's optimization.

**Important**: The restriction file determines the model structure (which diagrams and coupling associations exist) at `import model` time. Parameter values set in the param_card at `launch` time only change numerical values — they cannot restore diagrams that were removed or couplings that were merged by the restriction file optimization.

**Fix for EFT models**: Set all active parameters (Wilson coefficients you intend to vary) in the restriction file to **random, mutually distinct, non-zero values different from 1**:

```
# WRONG — all Wilson coefficients set to the same value
Block SMEFT
  1  1.000000e+00   # cG
  2  1.000000e+00   # cW
  3  1.000000e+00   # cH

# CORRECT — random distinct values
Block SMEFT
  1  1.234567e-01   # cG
  2  7.890123e-02   # cW
  3  4.567890e-01   # cH
```

Parameters for operators you want to disable should be set to exactly zero.

## Exploring a Model

After loading a model, inspect its content:

```
display particles         # list all particles with PDG IDs, masses, spins
display interactions       # list all interaction vertices
display multiparticles     # list predefined multiparticle labels
display parameters         # list all parameters and their values
display modellist          # list all available model directories
```

Use `display particles` to find particle names for your process. Particle names vary between models — the top quark is `t` in the SM but might have a different name in a BSM model.

## BSM Workflow

### Using an External BSM Model

Example: charged Higgs production in the Two-Higgs-Doublet Model (download the 2HDM UFO from FeynRules and place in `<MG5_DIR>/models/`):

```
import model 2HDM
display particles            # find the charged Higgs name (h+ or hp)
generate p p > h+ h-
output charged_higgs
launch charged_higgs
  set param_card mass 37 300.0    # set charged Higgs mass (PDG 37)
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

After setting masses, use [MadWidth](decays-and-madspin.md) to compute consistent widths:

```
import model 2HDM
compute_widths h+ h- h2 h3
```

### Using an External UFO Model

1. Download the UFO model directory (e.g., from the FeynRules model database or generate with FeynRules/SARAH).
2. Place the directory inside `<MG5_DIR>/models/`.
3. Load it:

```
import model MY_BSM_MODEL
```

Or provide the full path:

```
import model /path/to/MY_BSM_MODEL
```

### Z' Resonance Search Example

For a heavy Z' boson decaying to dimuons:

```
import model Zprime_UFO         # or whatever the model is named
display particles                # find the Z' particle name
generate p p > zp, zp > mu+ mu-
output zprime_search
launch zprime_search
  set param_card mass 9900032 2000.0    # Z' mass = 2 TeV (PDG ID varies by model)
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

Physics considerations for resonance searches:
- Use decay chain syntax (`,`) for on-shell production.
- Use `compute_widths` to calculate the Z' width consistently from its couplings.
- Apply generation cuts on the dimuon invariant mass to focus on the signal region.
- A narrow resonance (Γ/M < 3%) gives a clean peak; wide resonances need larger `bwcutoff`.

## The heft Model

The `heft` (Higgs Effective Field Theory) model integrates out the top-quark loop and adds effective vertices to the SM, enabling tree-level computation of gluon-fusion Higgs production:

```
import model heft
generate g g > h
```

Without `heft`, `g g > h` has zero tree-level diagrams in the SM because it proceeds through a top-quark loop. Alternative approaches:
- `heft`: Fast, valid for mH << 2mt. Does NOT include the VBF vertex — do not use for `p p > h j j` VBF studies.
- `loop_sm` with `[QCD]`: Full loop computation, slower but more accurate for high-pT Higgs or near the 2mt threshold.

### Effective Vertices in the `heft` Model

The `heft` model implements the following effective vertices (and **only** these):

| Vertex | Particles | Origin |
|--------|-----------|--------|
| `g g h` | 2 gluons + 1 Higgs | Dimension-5 operator from integrating out the top loop |
| `g g g h` | 3 gluons + 1 Higgs | Expansion of the same operator (via auxiliary tensor particle) |
| `g g g g h` | 4 gluons + 1 Higgs | Expansion of the same operator (via auxiliary tensor particle) |
| `h a a` | Higgs + 2 photons | Effective H→γγ coupling |

**There is no `g g h h` (ggHH) contact vertex.** The MadGraph HEFT model only implements single-Higgs effective couplings to gluons. The double-Higgs effective couplings exist in the HELAS library but are **not included** in the `heft` UFO model.

### Higgs Pair Production (`g g > h h`) — HEFT Limitations

In the full SM, `g g > h h` at one loop receives two contributions:
1. **Triangle diagrams**: `g g → H* → h h` (top loop produces an off-shell Higgs, which splits via the trilinear `HHH` coupling).
2. **Box diagrams**: `g g → h h` (top quarks circulate in a box with two Higgs legs attached).

These two contributions interfere destructively, and the box diagrams dominate at high $m_{HH}$.

In the `heft` model, `g g > h h` produces **exactly 1 diagram** — the triangle topology only:

```
import model heft
generate g g > h h
# INFO: Process has 1 diagrams
# This is ONLY the triangle: g g -> H* -> h h (via ggH vertex + HHH coupling)
# The box contribution is MISSING
```

This means:
- The `heft` model captures **only the triangle diagram** for di-Higgs production.
- The box diagram contribution (dominant at high $m_{HH}$) is **completely absent** — there is no `g g h h` vertex to produce it.
- The total cross section and all differential distributions (especially $m_{HH}$) are **wrong** when using `heft` for `g g > h h`.
- Do **not** use `heft` for Higgs pair production studies.

### Correct Approach: Loop-Induced `g g > h h`

For Higgs pair production with full top-mass dependence (both triangle and box diagrams), use the `loop_sm` model with loop-induced syntax:

```
import model loop_sm
generate g g > h h [noborn=QCD]
output gg_hh_loop
launch
```

The `[noborn=QCD]` flag is required because this is a loop-induced process (no tree-level Born contribution exists). This computes the exact one-loop matrix elements with full top-mass dependence, giving correct results across the entire $m_{HH}$ range.

**Key points for loop-induced `g g > h h`:**
- Computationally expensive — each phase-space point requires numerical evaluation of one-loop integrals.
- MadSpin is not compatible with loop-induced mode. For Higgs decays, use the parton shower or `set spinmode none` in MadSpin (acceptable for scalar Higgs since there are no spin correlations).
- True NLO for `g g > h h` requires two-loop virtual corrections, which are not available in MadGraph.

**Details ->** [NLO Plugins and Loop-Induced Processes](nlo-plugins-and-loops.md) for loop-induced process syntax and options.

### Internal vs. External Parameters

UFO models distinguish between **external** and **internal** parameters:

| Type | Definition | Settable via param_card? | Example |
|------|-----------|--------------------------|--------|
| **External** | Independent inputs read from the param_card at launch time | Yes | `MH` (Higgs mass), `MT` (top mass), `aS` (strong coupling) |
| **Internal** | Derived from external parameters via formulas in `parameters.py` | No — computed automatically | `lam` (Higgs quartic), `GF`-derived quantities, `sqrt2` |

Internal parameters **cannot be independently modified** through the param_card. Changing them requires either:
1. Changing the external parameters they depend on (which affects other physics), or
2. Modifying the model's `parameters.py` to promote them to external parameters.

This distinction is critical for the **Higgs trilinear self-coupling** in `gg → h h` studies.

### Higgs Trilinear Coupling in `loop_sm` — A Common Pitfall

In the standard `loop_sm` model, the Higgs self-coupling is an **internal parameter** derived from the Higgs mass:

```python
# In loop_sm/parameters.py:
lam = MH**2 / (2. * v**2)       # Higgs quartic coupling (internal)
# The triple-Higgs vertex coupling GC_30 is proportional to lam * v
```

This means:
- **You cannot independently set the trilinear coupling** `λ_HHH` in the param_card when using the standard `loop_sm` model.
- Setting `MH = 0` to force `lam = 0` would break the physics entirely.
- The `set param_card` command at launch time can only modify external parameters — it has no effect on internal ones like `lam`.

**Do not claim** that setting `λ_HHH = 0` in the param_card of the standard `loop_sm` is a valid method to isolate box diagrams in `g g > h h`. The trilinear coupling is not an independent parameter in this model.

### Studying Modified Trilinear Couplings in `g g > h h`

To vary the Higgs trilinear coupling independently of the Higgs mass, use one of these approaches:

#### Approach 1: Dedicated Higgs Pair Production Model (Recommended)

The MadGraph wiki provides dedicated models for `g g > h h` with explicit BSM coupling modifiers as **external parameters**:

| Parameter | Meaning | SM Value |
|-----------|---------|----------|
| `ctr` | Scaling factor for the SM Higgs trilinear coupling (`λ_HHH → ctr × λ_HHH`) | 1 |
| `cy` | Scaling factor for the top Yukawa coupling (`y_t → cy × y_t`) | 1 |
| `c2` | Coefficient of the `t t h h` contact interaction (absent in SM) | 0 |

These models are available from the [MadGraph Higgs Pair Production wiki page](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/HiggsPairProduction). Download the appropriate model package and place it in `<MG5_DIR>/models/`.

With such a model, isolating triangle vs. box contributions is straightforward:

```
# Triangle-only: set ctr to SM value, set cy=0 to remove box diagrams
# (cy=0 also removes the triangle's top-loop, so this needs care)

# Box-only: set ctr=0 to remove the trilinear vertex → no triangle diagrams
set param_card ctr 0.0

# Scan over trilinear coupling values:
set param_card ctr 2.0    # doubled trilinear coupling
```

**Key points:**
- Setting `ctr = 0` eliminates all triangle diagrams, leaving only box contributions.
- Setting `c2 = 0` recovers the SM (no anomalous `tthh` contact interaction).
- The cross section has the form $\sigma(\text{ctr}) = A \cdot \text{ctr}^2 + B \cdot \text{ctr} + C$, where $A$ is the $|\text{triangle}|^2$ contribution, $B$ is the triangle–box interference, and $C = |\text{box}|^2$ is the box-only contribution (independent of `ctr`). This makes the $\sigma(\text{ctr})$ dependence non-trivial — it is not a simple rescaling.

#### Approach 2: Modify the `loop_sm` UFO Manually

If a dedicated model is not available, you can promote the trilinear coupling to an external parameter:

1. Copy the `loop_sm` directory to a new model (e.g., `loop_sm_kl`).
2. In `parameters.py`, add a new external parameter `kl` (in a custom SLHA block, e.g., `BSMINPUTS`).
3. Modify the trilinear coupling definition to multiply by `kl`:
   ```python
   # Original: lam = MH**2 / (2. * v**2)
   # Modified: effective trilinear = kl * (original)
   # Multiply the relevant GC_XX coupling by kl
   ```
4. Delete `restrict_*.dat` files and any `decays.py` in the copied model directory.
5. Load the modified model and set `kl` in the param_card:
   ```
   import model loop_sm_kl
   generate g g > h h [noborn=QCD]
   output gg_hh_kl
   launch
     set param_card bsminputs 1 0.0    # kl=0 → box only
   ```

#### Approach 3: Reweighting

Generate SM `g g > h h` events with `loop_sm`, then use MadGraph's reweighting module (`change model` in the reweight card) to reweight events to different trilinear coupling values. This requires a model with the trilinear coupling as an external parameter for the reweighting step. See [Systematics & Reweighting](systematics-reweighting.md).

**Key points:**
- The standard `loop_sm` model does **not** allow independent variation of the Higgs trilinear coupling.
- Always check whether a coupling is internal or external before attempting to modify it via the param_card. Use `display parameters` after `import model` — internal parameters are listed separately from external ones.
- For `g g > h h` studies with modified couplings, use a dedicated model with explicit scaling parameters (`ctr`, `cy`, `c2`).

## Merging Models with `add model`

The `add model` command merges a second UFO model (the "plugin") into the currently loaded model (the "base"), creating a combined model that contains the particles, parameters, and interactions from both.

### Syntax

```
import model BASE_MODEL
add model PLUGIN_MODEL [--recreate] [--output=DIRNAME]
```

| Option | Effect |
|--------|--------|
| (none) | Creates a merged model directory `BASE__PLUGIN` inside `<MG5_DIR>/models/`. If this directory already exists, it is reused without re-merging. |
| `--recreate` | Forces re-creation of the merged model even if `BASE__PLUGIN` already exists. **Use this after modifying either model.** |
| `--output=DIRNAME` | Sets a custom name for the merged model directory instead of the default `BASE__PLUGIN`. |

### What the Merge Does

The merged model contains the **union** of all content from both models, with the following conflict resolution rules:

| Element | Merge Rule |
|---------|------------|
| **Particles** | Matched by PDG code. If both models define the same particle, properties are unified. If one model has the mass set to zero and the other nonzero, the **nonzero mass wins**. |
| **External parameters** | Parameters with the same SLHA block and ID are assumed to represent the same physical quantity and merged into one: the plugin parameter is renamed to match the base parameter's name. **No value comparison is performed** — the user must ensure consistency in the param_card. Parameters with identical names but different block/ID are renamed with a suffix (`__1`). |
| **Internal parameters** | Merged; naming conflicts are resolved by renaming the plugin's version. |
| **Coupling orders** | New coupling orders from the plugin are added. For coupling orders defined in both models, **both** the `hierarchy` and the `expansion_order` take the **minimum** of the two values. This can suppress plugin vertices in diagram generation (see caveats). |
| **Interactions / vertices** | All interactions from both models are included. **Exact duplicates** (matching particles, Lorentz structures, color structures, and couplings) **are detected and skipped**. However, near-duplicate interactions (same external particles but different coupling constants or Lorentz structures) are both kept — this can produce double-counting and incorrect cross sections. |
| **Lorentz structures** | Merged; naming conflicts resolved by renaming. |

### The `hgg_plugin` — Built-In Effective ggH Plugin

MG5 ships with `hgg_plugin` in `<MG5_DIR>/models/hgg_plugin/`. It adds effective Higgs–gluon and Higgs–photon vertices to any model, enabling tree-level gluon-fusion Higgs production without the `heft` model. This is useful when you need the effective ggH vertex combined with a BSM model that is not based on `heft`.

The plugin introduces two coupling orders:

| Coupling Order | Meaning | Vertices |
|----------------|---------|----------|
| `HIG` | Effective Higgs–gluon coupling (from integrating out the top loop) | g g H, g g g H, g g g g H |
| `HIW` | Effective Higgs–photon coupling (H→γγ via W loop) | H γ γ |

### Practical Workflow — Gluon-Fusion Higgs + Decay in a BSM Model

```
# 1. Load the base model with its restriction
import model MY_BSM-my_restriction

# 2. Merge the plugin (force fresh merge)
add model hgg_plugin --recreate

# 3. Inspect the merged model
display particles
display interactions
display coupling_order

# 4. Generate gg > H using only the effective ggH vertex
#    Coupling order constraints on the generate line are essential —
#    without them, MG5 may include unwanted diagrams or fail to find
#    the effective vertex due to automatic coupling order weight thresholds.
generate g g > h HIG=1 HIW=0 QED=0 QCD=0
output ggH_bsm
launch
```

**Coupling order constraints in decay chains** apply independently per core process and per decay. If the decay involves a coupling order (e.g., a Yukawa coupling requiring QED≥1), you must allow it in the decay specification:

```
generate g g > h HIG=1 HIW=0 QED=0 QCD=0, h > mu+ mu-
```

Here the decay `h > mu+ mu-` is unconstrained (default coupling orders apply), so the QED=1 Yukawa vertex is found. To add explicit constraints on the decay, ensure you permit the required orders:

```
generate g g > h HIG=1 HIW=0 QED=0 QCD=0, (h > mu+ mu- QED=1 HIG=0 HIW=0)
```

### Caveats

- **No physics validation**: MG5 performs a purely technical merge. It does not check gauge invariance, unitarity, or other physics consistency of the combined model.
- **Plugin restriction files are ignored**: Only the base model's restriction file (specified via `import model BASE-RESTRICTION`) is applied. Any `restrict_*.dat` in the plugin directory has no effect.
- **Near-duplicate interactions**: Exact duplicate interactions (same particles, Lorentz structures, color structures, couplings) are detected and skipped. But if both models define the same physical vertex with different coupling names or Lorentz structures, both copies are kept, producing incorrect cross sections. Verify with `display interactions` after merging.
- **Coupling order hierarchy conflicts**: When both models define the same coupling order, both `hierarchy` and `expansion_order` take the **minimum** of the two values. This can suppress plugin vertices in automatic diagram generation. Fix: explicitly specify high coupling order limits on the `generate` line (e.g., `QED=99`).
- **Cached/stale merged models**: MG5 caches merged models as `.pkl` files. If you modify either model's Python source files after merging, the cached version may be stale. Use `--recreate` to force a fresh merge, or delete all `.pkl` files in the merged model directory.
- **Loop models as plugins are not supported**: You cannot use a loop-level UFO model (like `loop_sm`) as the plugin in `add model`.
- **Parameter block conflicts**: Parameters in non-standard SLHA blocks may have different physical meanings across models despite sharing the same block name. Inspect the merged `param_card.dat` carefully.

**Key points:**
- Always use `--recreate` after modifying either model to avoid stale caches.
- Always specify coupling order constraints on the `generate` line to select the desired vertices.
- Use `display interactions` after the merge to verify that expected vertices are present and no near-duplicates exist.
- For complex BSM + effective-vertex combinations, consider implementing the effective vertex directly in the FeynRules Lagrangian and generating a single unified UFO model — this avoids all merge pitfalls.

## The loop_sm Model

Required for NLO computations:

```
import model loop_sm
generate p p > t t~ [QCD]
```

The `loop_sm` model contains the loop amplitude information (UV counterterms, R2 rational terms) needed for NLO calculations. Using `import model sm` with `[QCD]` syntax triggers an automatic upgrade to `loop_sm` (MG5 prints an info message and loads `loop_sm`), so the process generation succeeds. Explicitly importing `loop_sm` is optional but makes the model choice visible. See [NLO Computations](nlo-computations.md).

## FeynRules Integration

FeynRules is a Mathematica package that generates UFO models from a Lagrangian. The workflow:

1. Define the Lagrangian in FeynRules.
2. Export as a UFO model.
3. Place the UFO directory in `<MG5_DIR>/models/`.
4. Create a restriction file for performance (set light quark masses to zero).
5. Load with `import model`.

Common issue: FeynRules models include massive light quarks by default, which prevents subprocess grouping and makes generation slow. Always create a restriction file.

## Model Verification

After loading a BSM model, verify it with:

```
import model MY_MODEL
generate p p > t t~
check gauge p p > t t~     # verify gauge invariance
check full p p > t t~       # run all checks
```

This is essential for custom UFO models to catch bugs in the model implementation.
