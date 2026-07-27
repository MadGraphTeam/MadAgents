# NLO Computations

NLO QCD corrections for arbitrary processes in MadGraph5_aMC@NLO.

## Contents

- [Requirements](#requirements)
- [Basic NLO Syntax](#basic-nlo-syntax)
- [NLO Syntax Variants](#nlo-syntax-variants)
  - [Loop-Induced Processes](#loop-induced-processes)
- [MC@NLO Matching](#mcnlo-matching)
- [Reducing Negative Weights](#reducing-negative-weights)
  - [Why MC@NLO Produces Negative Weights](#why-mcnlo-produces-negative-weights)
  - [MC@NLO-Delta Method](#mcnlo-delta-method)
  - [Folding Parameters](#folding-parameters)
  - [More Integration Points](#more-integration-points)
- [FKS_params.dat — Technical NLO Parameters](#fks_paramsdat-technical-nlo-parameters)
  - [Pole Cancellation Errors](#pole-cancellation-errors)
- [MadLoop and External One-Loop Providers (BLHA Interface)](#madloop-and-external-one-loop-providers-blha-interface)
  - [MadLoop — The Built-In One-Loop Provider](#madloop-the-built-in-one-loop-provider)
  - [The Binoth Les Houches Accord (BLHA)](#the-binoth-les-houches-accord-blha)
  - [Supported External OLPs](#supported-external-olps)
  - [Using GoSam as the OLP](#using-gosam-as-the-olp)
  - [Using Other OLPs via `[real=QCD]`](#using-other-olps-via-realqcd)
  - [When to Use an External OLP vs MadLoop](#when-to-use-an-external-olp-vs-madloop)
- [NLO Launch Flags](#nlo-launch-flags)
- [Version Differences: v2 vs v3](#version-differences-v2-vs-v3)
- [NLO + MadSpin + Shower + Delphes](#nlo-madspin-shower-delphes)
- [FxFx Merging at NLO](#fxfx-merging-at-nlo)
- [Process Overlap at NLO](#process-overlap-at-nlo)
  - [Internal Overlap (FKS Subtraction)](#internal-overlap-fks-subtraction)
  - [Physics-Level Process Overlap (Wt vs tt̄)](#physics-level-process-overlap-wt-vs-tt)
- [Electroweak NLO Corrections](#electroweak-nlo-corrections)
  - [Requirements](#requirements-1)
  - [NLO EW Syntax](#nlo-ew-syntax)
  - [The `nlo_mixed_expansion` Option](#the-nlo_mixed_expansion-option)
  - [Coupling Order Control](#coupling-order-control)
  - [Physics of EW Corrections](#physics-of-ew-corrections)
  - [Limitations](#limitations)

## Requirements

NLO computations require:
1. A **loop-capable model**: `import model loop_sm` is optional — MadGraph automatically loads `loop_sm` when the `[QCD]` syntax is used with the default `sm` model. However, explicitly importing `loop_sm` makes the model choice visible in the script and avoids the auto-upgrade info message.
2. The **`[QCD]`** syntax on the `generate` line
3. Optional but recommended: Pythia8 for MC@NLO matching to a parton shower

## Basic NLO Syntax

```
import model loop_sm
generate p p > t t~ [QCD]
output ttbar_NLO
launch ttbar_NLO
  shower=PYTHIA8
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

The `[QCD]` triggers computation of NLO QCD corrections: real emission diagrams, virtual (one-loop) diagrams, and the associated subtraction terms.

## NLO Syntax Variants

```
generate p p > t t~ [QCD]          # full NLO QCD (real + virtual + subtraction)
generate p p > t t~ [virt=QCD]     # virtual corrections only (one-loop amplitudes)
generate g g > z z [noborn=QCD]    # loop-induced process (no Born amplitude exists)
```

### Loop-Induced Processes

Some processes have no tree-level diagrams but proceed through loops at leading order (e.g., gg → ZZ, gg → HH). Use `[noborn=QCD]` to signal that the Born contribution is absent:

```
import model loop_sm
generate g g > z z [noborn=QCD]
```

If you try `generate g g > z z` without `[noborn=QCD]`, MG5 reports 0 diagrams because there is no tree-level amplitude.

**Warning**: MG5 does not validate that the Born amplitude truly vanishes when you use `[noborn=QCD]`. It trusts the user's assertion and skips the Born contribution. If the Born actually exists, the computation silently produces incomplete (wrong) results. Always verify independently that the process is genuinely loop-induced.

Loop-induced LO computations can receive very large higher-order corrections. For example, gg → H has a K-factor of ~2 from NLO QCD, making the LO cross-section a poor normalization. Use loop-induced LO for distribution shapes, but normalize to higher-order predictions (from dedicated codes or literature) when available.

## MC@NLO Matching

MG5_aMC@NLO uses the MC@NLO method to combine NLO calculations with a parton shower:

- Subtracts the shower approximation analytically from the NLO calculation.
- **Produces events with negative weights** — this is inherent to the method, not a bug.
- The negative weight fraction is typically 10-30% depending on the process.
- Note: LO event generation can also produce negative-weight events due to interference between diagrams of different topology or coupling order, though the fraction is typically much smaller than at NLO.
- Requires a parton shower (Pythia8) for physically meaningful predictions.

In the run_card:
```
PYTHIA8   = parton_shower      # shower program for MC@NLO matching
```

Note: POWHEG is a separate framework (POWHEG-BOX), not part of MG5_aMC@NLO.

## Reducing Negative Weights

Negative weight fractions reduce effective statistics: $N_{\text{eff}} = N \times (1 - 2f)^2$, where $f$ is the negative-weight fraction. At $f=30\%$, you need ~6× more events for equivalent statistical precision.

### Why MC@NLO Produces Negative Weights

The MC@NLO method decomposes the NLO cross section into two event types:

- **H-events** (Hard): $(n+1)$-body kinematics (real-emission topology). Weight = $d\sigma_{\text{real}} - d\sigma_{\text{MC}}$, where $d\sigma_{\text{MC}}$ is the parton shower's $\mathcal{O}(\alpha_s)$ emission approximation used as a local subtraction term.
- **S-events** (Standard): $n$-body kinematics (Born topology). Contain the Born, virtual, and integrated-subtraction contributions.

In soft/collinear regions, the shower approximation can locally exceed the NLO real-emission matrix element, making $d\sigma_{\text{real}} - d\sigma_{\text{MC}}$ negative for H-events. S-events can also carry negative weights when the virtual corrections are negative for certain Born configurations. This is inherent to the method and not a bug.

See Frederix, Frixione, Prestel, Torrielli, JHEP 07 (2020) 238 ([arXiv:2002.12716](https://arxiv.org/abs/2002.12716)) for a detailed classification of negative weight sources and the MC@NLO-Delta method for reducing them.

Strategies to mitigate:

### MC@NLO-Delta Method

`set run_card mcatnlo_delta True` — MC@NLO-Δ method, moderate CPU overhead (mitigated by pre-tabulated Sudakov factors), requires Pythia8 ≥ 8.309.

### Folding Parameters

The `folding` parameters in the run_card increase sampling points in the FKS subtraction, reducing the negative weight fraction at the cost of longer runtime:

```
set run_card folding 4 4 4
```

The three values control folding in different FKS subtraction variables (xi_i, y_ij, phi_i). Default is `1 1 1`. Each value must be 1, 2, 4, or 8. Increasing the values reduces negative weights at the cost of longer runtime (scales approximately linearly).

### More Integration Points

Better grid optimization reduces weight fluctuations:
- Increase the number of iterations/points for grid optimization.
- The first launch is slower (grid buildup), subsequent launches with the same process directory can reuse grids.

## FKS_params.dat — Technical NLO Parameters

Located in `<PROC_DIR>/Cards/FKS_params.dat`:

```
1d-5    = IRPoleCheckThreshold    ! IR pole cancellation threshold
1.0d-3  = PrecisionVirtualAtRunTime
```

### Pole Cancellation Errors

If you see `aMCatNLOError: Poles do not cancel`, the IR (infrared) subtraction terms and virtual corrections don't cancel to the expected precision. Common causes:

1. **VBF/VBS processes**: MG5 filters out certain pentagon diagrams containing non-QCD particles (W, Z, γ, H). These are UV-finite and typically contribute < 1% but cause the pole check to fail.

   **Fix**: Set `IRPoleCheckThreshold = -1.0d0` in FKS_params.dat to disable the check:
   ```
   set FKS_params IRPoleCheckThreshold -1.0d0
   ```

2. **Numerical instabilities**: Rare phase-space points with poor numerical precision. Increasing `PrecisionVirtualAtRunTime` triggers re-evaluation at higher precision for flagged points.

## MadLoop and External One-Loop Providers (BLHA Interface)

### MadLoop — The Built-In One-Loop Provider

MadLoop is the default one-loop provider (OLP) in MG5_aMC@NLO. It computes virtual (one-loop) amplitudes using integrand-reduction and tensor-integral-reduction methods.

**Default reduction tools** (statically linked — no user configuration needed):

| Tool | Method | Notes |
|------|--------|-------|
| **CutTools** | OPP integrand reduction | Required; always present |
| **IREGI** | Tensor integral reduction (TIR) | Required; always present |
| **Ninja** | OPP with Laurent expansion | Recommended; installed by default |

MadLoop implements a multi-tool stability rescue system: each phase-space point is first evaluated with one reduction tool in double precision. If numerical instability is detected, the point is re-evaluated with a different tool and/or in quadruple precision. Return codes indicate which tool and precision were used.

**Optional reduction libraries** (dynamically linked, must be installed separately):

| Library | Install command | Notes |
|---------|----------------|-------|
| COLLIER | `install collier` | Tensor reduction; alternative to IREGI |
| Golem95 | `install Golem95` | Tensor reduction (note: capital G is required) |
| PJFry++ | (manual) | Tensor reduction |
| Samurai | (manual) | OPP reduction |

Paths to optional libraries are set in `input/mg5_configuration.txt`:

```
# ninja = ./HEPTools/lib        # path to Ninja library (default)
# collier = ./HEPTools/lib       # path to COLLIER library
# golem = auto                   # path to Golem95 library (auto = auto-detect)
# samurai = None                 # path to Samurai library (None = disabled)
# pjfry = auto                   # path to PJFry++ library
```

The `output_dependencies` option controls how MadLoop's reduction libraries are bundled:

```
# output_dependencies = external          # links to MG5-wide libraries (default)
# output_dependencies = internal          # copies libraries into the output directory
# output_dependencies = environment_paths # searches PATH for libraries at runtime
```

### The Binoth Les Houches Accord (BLHA)

The BLHA is a standardized interface protocol between Monte Carlo event generators and one-loop providers. It allows MG5_aMC@NLO to delegate virtual amplitude computation to an external code instead of MadLoop.

**References:**
- BLHA1: Binoth et al., Comp. Phys. Comm. 181 (2010) 1612 ([arXiv:1001.1307](https://arxiv.org/abs/1001.1307))
- BLHA2: Alioli et al., Comp. Phys. Comm. 185 (2014) 560 ([arXiv:1308.3462](https://arxiv.org/abs/1308.3462))

The BLHA works in two phases:

1. **Order/Contract phase** (at code-generation time):
   - MG5 writes an **order file** (`OLE_order.lh`) specifying: subprocess list, coupling powers (QCD/QED), renormalization/regularization schemes, and a path to an SLHA parameter file (`ModelFile`) for masses, widths, and couplings.
   - The OLP reads the order file and produces a **contract file** (`OLE_order.olc`) confirming which subprocesses it can provide, assigning each an integer label.

2. **Runtime phase** (during integration/event generation):
   - `OLP_Start(contract_file, ierr)` — initializes the OLP, reads the contract. `ierr=1` on success.
   - `OLP_EvalSubProcess(label, momenta, mu_r, alpha_s, rval)` — evaluates the one-loop amplitude for subprocess `label` at the given phase-space point and renormalization scale `mu_r`, with strong coupling `alpha_s`. Returns a 4-element array: `rval(1)` = coefficient of double IR pole (1/epsilon²), `rval(2)` = coefficient of single IR pole (1/epsilon), `rval(3)` = finite part, `rval(4)` = Born |M|². Momenta are packed as 5-tuples (E, kx, ky, kz, M) per particle.

   This is the BLHA1 subroutine signature. BLHA2 introduces `OLP_EvalSubProcess2` which drops `alpha_s` from the argument list and adds a double-precision accuracy estimate. MG5_aMC@NLO uses the BLHA1 signature when interfacing external OLPs like GoSam.

**Note:** MG5's internal communication between MadFKS (real-emission/subtraction) and MadLoop uses a BLHA-inspired architecture — it shares the order/contract file mechanism and BinothLHA-named source files — but internally calls `sloopmatrix_thres()` rather than the standard BLHA subroutines.

### Supported External OLPs

| OLP | Method | Native MG5 support | Notes |
|-----|--------|-------------------|-------|
| **GoSam** | Algebraic code generation | Yes (`set OLP GoSam`) | Automated one-loop generator; uses reduction tools from GoSamContrib (Golem95, Samurai, and optionally Ninja) |
| **OpenLoops** | On-the-fly numerical recursion | Via `[real=QCD]` + manual interface | Fast for high-multiplicity processes |
| **RECOLA** | Recursive amplitude construction | Via `[real=QCD]` + manual interface | Uses COLLIER for reduction |

### Using GoSam as the OLP

GoSam has a native interface to MG5_aMC@NLO based on the BLHA1 standard. To use it:

**Option 1: Interactive command**
```
MG5_aMC> set OLP GoSam
```

**Option 2: Persistent configuration** in `input/mg5_configuration.txt`:
```
OLP = GoSam
```

With GoSam selected, `generate p p > e+ ve [QCD]` and `launch` will automatically:
1. Generate the BLHA order file (`OLE_order.lh`) with subprocess definitions.
2. Invoke GoSam to produce one-loop amplitudes and write the contract file (`OLE_order.olc`).
3. Use GoSam's loop amplitudes during integration and event generation.

GoSam-specific settings (loop particle content, model, number of active flavors) can be customized via a `gosam.rc` configuration file. Consult the GoSam documentation for details.

**Prerequisites:** GoSam and its dependencies (GoSamContrib, which includes Golem95 and Samurai) must be installed and accessible. GoSam generates Fortran code for the loop amplitudes, so the first run involves a code-generation step.

### Using Other OLPs via `[real=QCD]`

For OpenLoops, RECOLA, or other BLHA-compliant OLPs without a native MG5 interface, use the `[real=QCD]` syntax:

```
import model loop_sm
generate p p > t t~ [real=QCD]
output ttbar_real_only
```

The `[real=QCD]` directive generates only the real-emission diagrams and the associated phase-space integration infrastructure, but does **not** generate FKS subtraction terms or link MadLoop for virtual amplitudes. This is designed for interfacing external OLPs that provide their own subtraction and virtual corrections. The user must supply these missing components by interfacing their chosen OLP through the BinothLHA Fortran files in the output directory.

**Key syntax variants for separating NLO components** (see also NLO Syntax Variants above):

| Syntax | What is generated | Use case |
|--------|-------------------|----------|
| `[QCD]` | Full NLO: real + virtual + subtraction (MadLoop) | Standard NLO computation |
| `[real=QCD]` | Real-emission diagrams only (no FKS subtraction terms, no MadLoop virtuals) | Interface an external OLP that provides its own subtraction and virtuals |
| `[virt=QCD]` | Virtual (one-loop) corrections only | Standalone loop amplitude computation |

### When to Use an External OLP vs MadLoop

- **Cross-validation:** Using a different OLP provides an independent numerical check of virtual corrections, valuable for new or complex processes.
- **BSM models:** Some BSM models may be implemented in GoSam or RECOLA but not in MadLoop's UFO-based framework, or vice versa.
- **Performance:** For specific processes, external OLPs may be faster. OpenLoops' numerical recursion can be more efficient for high-multiplicity processes.
- **Default recommendation:** Use MadLoop (the default) unless you have a specific reason to use an external OLP. MadLoop is tightly integrated, requires no external dependencies beyond the statically linked reduction tools, and handles most SM and BSM processes.

## NLO Launch Flags

The `launch` command for NLO processes accepts several flags that control execution. These are particularly important for the [NLO gridpack workflow](scripted-execution.md#nlo-gridpack-workflow).

| Flag | Description |
|------|-------------|
| `--parton` | Stop after parton-level LHE event generation; skip parton shower. |
| `--nocompile` | Skip compilation; use pre-built executables. Use when launching from a pre-compiled process directory. |
| `--only_generation` | Skip MINT integration steps (steps 0 and 1); jump directly to event generation using existing grids. Requires that integration grids have been built by a prior run. |

These flags are passed on the `launch` command line:

```bash
./bin/aMCatNLO launch --parton --nocompile --only_generation
```

## Version Differences: v2 vs v3

MG5 v3 includes pentagon loops with non-colored particles (e.g., W/Z loops connecting quark lines) that were discarded in v2. This affects processes with t-channel vector bosons at LO:

- VBF Higgs production
- VBS (vector boson scattering)
- Single-top production

The `nlo_mixed_expansion` interface-level option controls this (see [detailed description below](#the-nlo_mixed_expansion-option)). It must be set before `generate`:

```
set nlo_mixed_expansion True      # include non-colored loops (v3 default)
set nlo_mixed_expansion False     # v2 behavior (discard non-colored loops)
```

For most processes the difference is negligible. For VBF/VBS it can be noticeable. The v3 behavior is more theoretically consistent.

## NLO + MadSpin + Shower + Delphes

Complete NLO workflow with all tools:

```
import model loop_sm
generate p p > t t~ [QCD]
output ttbar_NLO_full
launch ttbar_NLO_full
  shower=PYTHIA8
  madspin=ON
  detector=Delphes
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  set madspin_card decay t > w+ b, w+ > l+ vl
  set madspin_card decay t~ > w- b~, w- > l- vl~
  done
```

MadSpin handles decays between the fixed-order computation and the shower, preserving spin correlations. This is the recommended approach for NLO. Including decays directly in the NLO `generate` line (e.g., `p p > t t~ > w+ b w- b~ [QCD]`) does work for simple decay specifications using the `>` syntax, but MadSpin is preferred because:

- Complex multi-step decay cascades cause significant diagram-count growth, making computation very expensive. Simple two-body decays (e.g., `t > w+ b`) have only modest overhead (~25% more diagrams).
- MadSpin handles off-shell effects and non-resonant contributions more flexibly.
- MadSpin allows changing decay channels without regenerating the NLO process.

**Note**: The comma-based decay chain syntax (e.g., `p p > t t~, t > w+ b [QCD]`) is not supported at NLO and will produce an error. Use the `>` syntax or MadSpin for NLO decays.

## FxFx Merging at NLO

FxFx is the NLO extension of MLM matching. It merges NLO-accurate samples of different jet multiplicities. See [matching-and-merging.md](matching-and-merging.md) for full FxFx setup instructions.

FxFx requires `ickkw = 3` in the run_card and NLO process definitions with `[QCD]` and `@n` tags.

## Process Overlap at NLO

### Internal Overlap (FKS Subtraction)

At NLO, real-emission diagrams can produce topologies that overlap with different Born configurations. For example, in `p p > t t~ j [QCD]`, a real-emission diagram may produce a configuration where the extra jet is soft or collinear, overlapping with the Born process `p p > t t~`. MG5 handles this automatically via the FKS subtraction scheme: the `check_ij_confs()` and `find_reals_to_integrate()` routines identify overlapping configurations and assign each real-emission phase-space point to exactly one FKS partition, preventing double-counting.

**No user action is needed** for this internal overlap — FKS handles it correctly by construction.

### Physics-Level Process Overlap (Wt vs tt̄)

A different kind of overlap arises at the physics level. The classic example is **single-top Wt production** (`p p > t w-`) at NLO: its real-emission diagrams include `g b > t w- b̄`, which is also a leading-order diagram for **tt̄ production** (`p p > t t~, t~ > w- b~`). This is a physics ambiguity, not a technical subtraction issue.

MG5 does **not** provide built-in diagram removal (DR) or diagram subtraction (DS) schemes to handle this overlap. The standard approaches are:

1. **Inclusive approach**: Generate the full process including all diagrams. This is gauge-invariant but conflates Wt and tt̄.
2. **Invariant mass cuts**: Apply a veto on the invariant mass of the (W, b̄) system to exclude configurations near the top mass. This can be done at analysis level.
3. **External tools**: Dedicated Wt-channel generators implement DR/DS schemes. If precise Wt isolation is needed, consult the literature for the appropriate scheme.

For most analyses, the inclusive NLO calculation of `p p > t t~` supplemented by the inclusive single-top calculations is sufficient, provided the analysis selection avoids the overlap region.

## Electroweak NLO Corrections

MadGraph5_aMC@NLO supports automated computation of NLO electroweak (EW) corrections in addition to NLO QCD corrections. EW corrections are important at high energies where EW Sudakov logarithms can produce corrections of order 10% or more, comparable to residual QCD scale uncertainties.

### Requirements

NLO EW computations require:

1. A **loop-capable model with EW loops**: `loop_qcd_qed_sm` (not the standard `loop_sm` which only has QCD loops).
2. The appropriate bracket syntax on the `generate` line.
3. LHAPDF with a PDF set that includes a photon PDF (if real photon emission diagrams contribute).

**Important**: The `loop_qcd_qed_sm` model is not shipped with the default MG5 installation. It must be installed separately:

```
install loop_qcd_qed_sm
```

This model includes both QCD and QED loop amplitudes, UV counterterms, and R2 rational terms needed for NLO EW calculations.

Available restriction files for `loop_qcd_qed_sm`:
- `full`: No restrictions
- `no_widths`: Zero widths
- `with_b_mass`: Massive b-quark
- `with_b_mass_no_widths`: Massive b-quark with zero widths

A variant `loop_qcd_qed_sm_Gmu` uses the Gmu input scheme (Fermi constant as input instead of alpha_EW), with restrictions: `ckm`, `full`, `no_widths`.

### NLO EW Syntax

The bracket syntax for NLO corrections specifies which coupling types to include:

```
import model loop_qcd_qed_sm
generate p p > e+ e- [QCD]            # NLO QCD only (same as with loop_sm)
generate p p > e+ e- [QED]            # NLO EW only
generate p p > e+ e- [QCD QED]        # combined NLO QCD + NLO EW
```

The `[QCD QED]` syntax computes the full NLO corrections including both QCD and EW virtual loops, as well as real emission of gluons and photons.

### The `nlo_mixed_expansion` Option

`nlo_mixed_expansion` is an **MG5 interface-level option** (not a run_card parameter). It must be set via the `set` command **before** `generate` and `output`:

```
set nlo_mixed_expansion True      # default in MG5 v3
import model loop_qcd_qed_sm
generate p p > e+ e- [QCD QED]
output my_nlo_ew
```

It appears alongside other interface options such as `complex_mass_scheme` and `loop_optimized_output`. You can check its current value with `display options`.

| Value | Behavior |
|-------|----------|
| `True` (default) | Include contributions from all coupling-order combinations that contribute at the requested perturbative order (mixed QCD-EW terms included). |
| `False` | Include only the "pure" NLO QCD or NLO EW terms; mixed-order interference contributions are dropped. |

**Key points**:
- This is **not** a run_card parameter — do not look for it in `run_card.dat`. It is stored in the process metadata (banner) once the process is output.
- Setting it **after** `output` has no effect on an already-generated process directory.
- It is also relevant for pure QCD NLO computations where the Born process has mixed QCD-EW couplings (e.g., single-top production), as it controls whether pentagon loops with non-QCD particles are included.

### Coupling Order Control

For processes with multiple coupling types, the `QED` and `QCD` coupling order constraints control which Born-level diagrams are included:

```
generate p p > e+ e- QED=2 QCD=0 [QCD]     # Drell-Yan at NLO QCD (Born is pure EW)
generate p p > e+ e- j QED<=3 QCD<=1 [QCD]  # W/Z+jet at NLO QCD
```

The squared coupling order syntax (`QCD^2`, `QED^2`) can also be used to select specific interference patterns.

### Physics of EW Corrections

#### EW Sudakov Logarithms

EW corrections reach -10% to -30% at TeV-scale energies, suppressing high-pT tails. Particularly important for high-mass Drell-Yan, diboson at high pT, and any process with large momentum transfer.

#### Real Photon Emission

When photon-initiated processes contribute (e.g., γγ → l⁺l⁻), a PDF set with a photon component is required (e.g., NNPDF3.1luxQED).

### Limitations

1. **Model availability**: The `loop_qcd_qed_sm` model must be installed separately.
2. **Computational cost**: NLO EW computations are significantly slower than NLO QCD due to the larger number of diagrams and loop topologies.
3. **Shower matching**: MC@NLO matching for NLO EW corrections with QED showering requires careful treatment. Pythia8 supports QED showering, but the interface may need specific configuration.
4. **Photon PDFs**: For processes with real photon emission from the initial state, a PDF set including the photon PDF is required.
