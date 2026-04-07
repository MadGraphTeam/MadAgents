# 04 — Cards & Parameters

MadGraph uses configuration "cards" (plain-text files) to control physics parameters and run settings. After `output <PROC_DIR>`, cards are located in `<PROC_DIR>/Cards/`. They can be edited before `launch`, or modified during the launch dialogue using the `set` command.

## Contents

- [Overview of Cards](#overview-of-cards)
- [The `set` Command](#the-set-command)
- [Hidden Parameters and the `update` Command](#hidden-parameters-and-the-update-command)
  - [Revealing All Hidden Parameters: `update to_full`](#revealing-all-hidden-parameters-update-to_full)
  - [Revealing Specific Hidden run_card Blocks](#revealing-specific-hidden-run_card-blocks)
  - [param_card Maintenance Commands](#param_card-maintenance-commands)
  - [Setting Hidden Parameters Directly](#setting-hidden-parameters-directly)
- [param_card.dat — Physics Parameters](#param_carddat-physics-parameters)
  - [MASS Block — Particle Masses](#mass-block-particle-masses)
  - [DECAY Block — Particle Widths](#decay-block-particle-widths)
  - [SMINPUTS Block — SM Input Parameters](#sminputs-block-sm-input-parameters)
  - [Yukawa Block — Yukawa Couplings](#yukawa-block-yukawa-couplings)
  - [Dependent Parameters](#dependent-parameters)
- [run_card.dat — Run Configuration](#run_carddat-run-configuration)
  - [Beam Configuration](#beam-configuration)
  - [Event Generation](#event-generation)
  - [PDF Selection](#pdf-selection)
  - [Generation-Level Cuts](#generation-level-cuts)
  - [Scale Choices](#scale-choices)
  - [Systematics / Reweighting](#systematics-reweighting)
  - [Width Treatment](#width-treatment)
  - [Fixed-Target Configuration](#fixed-target-configuration)

## Overview of Cards

| Card | Purpose |
|------|---------|
| `param_card.dat` | Particle masses, widths, and coupling constants |
| `run_card.dat` | Collider setup, cuts, scales, integration settings |
| `pythia8_card.dat` | Pythia8 shower/hadronization settings |
| `delphes_card.dat` | Delphes detector simulation settings |
| `madspin_card.dat` | MadSpin decay configuration |
| `madanalysis5_card.dat` | MadAnalysis5 settings |
| `FKS_params.dat` | NLO-specific parameters (FKS subtraction) |

## The `set` Command

During the launch dialogue (in scripts), use `set` to modify card values without editing files directly:

```
set run_card ebeam1 6500
set param_card mass 6 172.5
set run_card nevents 10000
set pythia8_card JetMatching:qCut 30
```

Syntax: `set <card> <block_or_parameter> [index] <value>`

For the param_card, the block name and PDG ID (or parameter name) are needed. For the run_card, just the parameter name.

## Hidden Parameters and the `update` Command

MadGraph dynamically adjusts which run_card parameters are visible based on the current process. For example, jet cuts (`ptj`, `etaj`) are hidden when the process has no final-state jets, and matching parameters are hidden when matching is not enabled. Many advanced parameters (phase-space optimization, debugging, cluster tuning) are always hidden by default.

### Revealing All Hidden Parameters: `update to_full`

To reveal **every** possible run_card parameter at once, use `update to_full` at the card-editing prompt:

```
launch my_process
  update to_full
  set run_card ptj 30
  done
```

This expands the run_card to include all parameters, regardless of process relevance. It is the primary mechanism for accessing advanced or process-irrelevant settings.

### Revealing Specific Hidden run_card Blocks

Instead of revealing everything, you can reveal individual hidden blocks with `update <block_name>`:

| Command | Effect |
|---------|--------|
| `update to_full` | Reveals all hidden run_card parameters at once |
| `update beam_pol` | Reveals beam polarization settings (`polbeam1`, `polbeam2`) |
| `update ecut` | Reveals energy cuts in the partonic center-of-mass frame |
| `update ion_pdf` | Reveals ion PDF rescaling settings (heavy-ion collisions) |
| `update psoptim` | Reveals phase-space optimization settings (survey tuning, job splitting) |
| `update mlm` | Reveals MLM matching parameters |
| `update ckkw` | Reveals CKKW matching parameters |
| `update frame` | Reveals reference frame settings |
| `update syscalc` | Reveals systematics calculation parameters |

### param_card Maintenance Commands

The `update` command also has sub-commands that operate on the **param_card** (not the run_card). These do not reveal hidden blocks; they modify or reformat the param_card:

| Command | Effect |
|---------|--------|
| `update dependent` | Recalculates dependent parameters in the param_card (syncs alpha_s from PDF, recomputes model-dependent masses/widths). Does **not** reveal hidden parameters. |
| `update missing` | Adds missing blocks/parameters to the param_card with default values. Useful when an external spectrum file (e.g., SLHA) is incomplete. |
| `update to_slha1` | Converts param_card from SLHA2 to SLHA1 convention (beta). |
| `update to_slha2` | Converts param_card from SLHA1 to SLHA2 convention (beta). |

### Setting Hidden Parameters Directly

You do **not** need to reveal hidden parameters before modifying them. The `set` command works on any parameter, whether visible or hidden:

```
launch my_process
  set run_card ptj 30        # works even if ptj is hidden
  set run_card etaj 5.0
  done
```

This is the simplest approach in scripts when you know exactly which parameters to change.

**Key points:**
- The run_card is **process-aware** — it hides parameters irrelevant to the current process.
- Use `update to_full` to reveal all hidden parameters, or `update <block_name>` for specific blocks.
- The `set` command can modify any parameter regardless of visibility — you do not need to reveal parameters before setting them.
- `update dependent` and `update missing` operate on the param_card, not the run_card.

---

## param_card.dat — Physics Parameters

> **Default parameter values in MadGraph are software conventions, not physical constants.** They may differ from current PDG values or commonly used benchmarks (e.g., the default top mass is not necessarily the latest PDG world average). Defaults can also change between MG5 versions and model releases. Always verify defaults by inspecting the generated param_card (`<PROC_DIR>/Cards/param_card.dat`) and set critical values explicitly in your scripts.

The param_card follows the SLHA (SUSY Les Houches Accord) format. Key blocks:

### MASS Block — Particle Masses

```
BLOCK MASS
    5  4.700000e+00  # MB (b-quark mass)
    6  1.730000e+02  # MT (top quark mass)
   15  1.777000e+00  # MTA (tau mass)
   23  9.118800e+01  # MZ (Z boson mass)
   24  8.041900e+01  # MW (W boson mass — may be dependent)
   25  1.250000e+02  # MH (Higgs mass)
```

PDG IDs identify particles: 6 = top, 5 = bottom, 23 = Z, 24 = W, 25 = Higgs.

Setting a mass to zero makes the particle massless, which affects available diagrams and the flavor scheme.

**Script example — change top mass:**
```
set param_card mass 6 180.0
```

### DECAY Block — Particle Widths

```
DECAY   6  1.491500e+00  # WT (top width)
DECAY  23  2.441404e+00  # WZ (Z width)
DECAY  24  2.047600e+00  # WW (W width)
DECAY  25  6.382339e-03  # WH (Higgs width)
```

The width values must be consistent with the masses and couplings. Inconsistent widths cause problems with MadSpin (branching ratios > 1) and with the narrow-width approximation. Use [MadWidth](decays-and-madspin.md) (`compute_widths`) to calculate consistent widths.

Setting `DECAY X auto` tells MadGraph to compute the width automatically.

### SMINPUTS Block — SM Input Parameters

```
BLOCK SMINPUTS
    1  1.279000e+02  # aEWM1 (inverse EW coupling at MZ)
    2  1.166370e-05  # Gf (Fermi constant)
    3  1.184000e-01  # aS (strong coupling at MZ)
```

The default `sm` (and `loop_sm`) model uses the **alpha(MZ) electroweak input scheme**. The three EW inputs that determine `MW` are `aEWM1` (1/α at the Z pole, SMINPUTS entry 1), `Gf` (SMINPUTS entry 2), and `MZ` (from the MASS block, PDG 23). Note that entry 3 of SMINPUTS — `aS` — is the strong coupling constant; it is an independent QCD input and is *not* part of the EW input set. `MW` is an **internal (derived) parameter** computed from `aEWM1`, `Gf`, and `MZ` via the tree-level EW relation — it does not appear in the generated param_card and cannot be independently overridden.

The **Gmu scheme** — where `alpha_EW` is derived and `MW` is an independent input — is implemented in the separate model `loop_qcd_qed_sm_Gmu`. This model is not bundled with MG5 but is automatically downloaded from the MadGraph model database on first use: simply run `import model loop_qcd_qed_sm_Gmu` and MG5 will fetch it. See [03 — Models](models-and-restrictions.md) for details. Do not assume the default `sm` or `loop_sm` model uses the Gmu scheme.

### Yukawa Block — Yukawa Couplings

```
BLOCK YUKAWA
    5  4.700000e+00  # ymb
    6  1.730000e+02  # ymt
   15  1.777000e+00  # ymtau
```

### Dependent Parameters

Some parameters are computed from others (e.g., W mass in certain EW schemes). When modifying input parameters, you may see: `WARNING: Failed to update dependent parameter`. In scripts, respond with `update dependent` when prompted, or ensure dependent parameters are manually consistent. See [Troubleshooting](troubleshooting.md).

---

## run_card.dat — Run Configuration

The run_card controls collider setup, phase-space cuts, scale choices, and technical parameters.

### Beam Configuration

```
6500.0  = ebeam1    ! beam 1 energy in GeV (half of sqrt(s))
6500.0  = ebeam2    ! beam 2 energy in GeV
1       = lpp1      ! beam 1 type (0=no PDF, 1=proton, -1=antiproton)
1       = lpp2      ! beam 2 type
```

For pp collisions at 13 TeV: `ebeam1 = ebeam2 = 6500`. For e+e- at 91.2 GeV: `ebeam1 = ebeam2 = 45.6` with `lpp1 = lpp2 = 0`.

**Script example — set 13 TeV pp:**
```
set run_card ebeam1 6500
set run_card ebeam2 6500
```

### Event Generation

```
10000   = nevents       ! number of unweighted events
0       = iseed         ! random seed (0 = automatic)
```

Setting `nevents = 0` runs integration only (no event generation). The integration grids are computed but no LHE event file is produced.

### PDF Selection

```
230000  = lhaid    ! LHAPDF ID for the PDF set (only used when pdlabel=lhapdf)
```

The default PDF is the built-in `nn23lo1` set (LHAPDF equivalent ID: 247000), selected via `pdlabel = nn23lo1`. The `lhaid` parameter is only used when `pdlabel = lhapdf`; its default value of 230000 corresponds to NNPDF23_nlo_as_0119.

> **Note on built-in PDF labels:** MadGraph's built-in `pdlabel` shorthands cover only the NNPDF2.3 family (`nn23lo`, `nn23lo1`, `nn23nlo`). There are no built-in shorthands for NNPDF3.0, NNPDF3.1, CT18, MSHT20, or any other modern PDF set. Do not invent labels by analogy (e.g., `nn31nlo` does not exist and will fail). For any PDF set not listed above, use `pdlabel = lhapdf` with the numeric LHAPDF set ID via `lhaid`.

Common LHAPDF IDs:
- `262000` = NNPDF30_lo_as_0118 (LO)
- `263000` = NNPDF30_lo_as_0130 (LO, αs=0.130)
- `315000` = NNPDF31_lo_as_0118 (LO)
- `260000` = NNPDF30_nlo_as_0118 (NLO)
- `303400` = NNPDF31_nlo_as_0118 (NLO)
- `11000` = CT10nlo

> **Warning — NNPDF ID ordering is counterintuitive**: Within the NNPDF3.x family, the LO set IDs (262000, 263000) are numerically *higher* than the NLO ID (260000). This is the reverse of what one might expect from the name. Do not guess IDs by analogy or pattern within a PDF family. Always verify LHAPDF IDs against the official index before use: run `lhapdf list` or consult the [LHAPDF website](https://lhapdf.hepforge.org/pdfsets.html).

See [Installation](installation.md) for installing LHAPDF and PDF sets.

### Generation-Level Cuts

These cuts are applied during phase-space integration and directly affect the cross-section.

#### Standard Cuts (LO)

```
# Jet cuts
20.0    = ptj       ! minimum jet pT (GeV)
-1.0    = etaj      ! maximum jet |eta| (-1 = no cut)
0.4     = drjj      ! minimum deltaR(jet,jet)

# Lepton cuts
10.0    = ptl       ! minimum lepton pT
-1.0    = etal      ! maximum lepton |eta|
0.4     = drll      ! minimum deltaR(lep,lep)

# Photon cuts (simple)
20.0    = pta       ! minimum photon pT
-1.0    = etaa      ! maximum photon |eta|
```

#### Pair Invariant Mass Cuts

The parameter name for a dilepton (or more generally, lepton-pair) invariant mass cut **differs between LO and NLO run cards**. Using the wrong name silently has no effect.

| Context | Parameter | Applies to |
|---------|-----------|------------|
| **LO** run card | `mmll` | Same-flavor, opposite-sign lepton pairs (e.g. e⁺e⁻, μ⁺μ⁻) |
| **NLO** run card | `mll` | All opposite-sign lepton pairs |
| **NLO** run card | `mll_sf` | Same-flavor, opposite-sign lepton pairs only |

**LO example** (e.g. `p p > mu+ mu-`):
```
set run_card mmll 40    # correct LO parameter — minimum m(l+l-) in GeV
```

**NLO example** (e.g. `generate p p > mu+ mu- [QCD]`):
```
set run_card mll 40     # correct NLO parameter — minimum m(l+l-) in GeV
```

> **Warning**: Setting `mll` in an **LO** run card triggers a visible warning and the setting is discarded entirely: `WARNING: invalid set command run_card mll 40`. MadGraph also suggests the correct LO alternative (`mmll`, `mmllmax`). The cut is not applied. Always use `mmll` for LO generation.

Note: `mmll` applies only to **same-flavor** opposite-sign pairs. It does **not** cut on e⁺μ⁻ pairs. For different-flavor or more complex invariant mass cuts at LO, use the `mxx_min_pdg` syntax or a custom `dummy_cuts` function.

#### Photon Isolation (Frixione Smooth Cone)

When final-state photons are present, Frixione smooth-cone isolation (hep-ph/9801442) replaces simple photon cuts. Activated when `ptgmin > 0` (which disables `pta` and `draj`):

```
20.0    = ptgmin    ! Min photon pT (activates Frixione isolation)
0.4     = R0gamma   ! Isolation cone radius (hidden)
1.0     = xn        ! Cone exponent n (hidden)
1.0     = epsgamma  ! Epsilon_gamma parameter (hidden)
True    = isoEM     ! Isolate from EM energy too (hidden)
```

The isolation criterion requires that hadronic transverse energy within a cone of radius r around the photon satisfies:

$$E_T(r) \leq \epsilon_\gamma \, p_{T,\gamma} \left(\frac{1 - \cos r}{1 - \cos R_0}\right)^n$$

for all r < R0. This allows collinear radiation to vanish smoothly as r → 0, making the criterion infrared-safe at NLO.

When `isoEM = True` (default), the isolation applies to both hadronic **and** electromagnetic energy (other photons and leptons) within the cone. Set `isoEM = False` to isolate only from hadronic activity. At LO, these parameters are hidden; at NLO, `ptgmin`, `R0gamma`, `xn`, and `epsgamma` are visible in the run_card.

#### PDG-Based Cuts (Fine-Grained)

For per-particle cuts, use the `_min_pdg` / `_max_pdg` syntax:

```
{6: 500}   = pt_min_pdg     ! min pT for PDG ID 6 (top)
{11: 1000} = mxx_min_pdg    ! min invariant mass for pairs of PDG ID 11 (electrons)
{11: 1.0}  = eta_max_pdg    ! max |eta| for PDG ID 11
```

> **Warning**: Overly tight cuts can make the cross-section artificially small. See [Troubleshooting](troubleshooting.md) for diagnosing this.

#### Custom Cuts (`custom_fcts` / `dummy_fct.f`)

For cuts that cannot be expressed via the standard run_card parameters (e.g., flavor-dependent cuts, cuts on BSM particles, complex angular correlations), MadGraph supports user-defined Fortran cut functions.

**Method 1 — `custom_fcts` run_card parameter (MG5 v3.5.0+, recommended):**

```
set run_card custom_fcts ['/absolute/path/to/my_custom_cuts.f']
```

The file must define a `dummy_cuts` function. LO signature:

```fortran
logical function dummy_cuts(p)
implicit none
include 'nexternal.inc'
real*8 p(0:3, nexternal)
dummy_cuts = .true.
! Indices: 1,2 = initial state; 3..nexternal = final state
! Momenta are in the partonic center-of-mass frame (not lab frame)
return
end
```

NLO signature (different — includes particle identity):

```fortran
logical function dummy_cuts(p, istatus, ipdg)
implicit none
include 'nexternal.inc'
real*8 p(0:3, nexternal)
integer istatus(nexternal)  ! -1 = initial, 1 = final
integer ipdg(nexternal)     ! PDG codes
dummy_cuts = .true.
return
end
```

Custom run_card parameters can be added (e.g., `10.0 = min_newvar`) and accessed in Fortran via `include 'run.inc'`.

**Method 2 — Edit `SubProcesses/dummy_fct.f` directly** in the generated process directory. Works with all MG5 versions but does not survive process regeneration.

**Critical: `group_subprocesses` interaction.** MadGraph groups subprocesses sharing the same spin/color/mass structure to speed up integration. Grouped subprocesses share cut evaluations. If your custom cuts break flavor symmetry, beam symmetry, or identical-particle symmetry (e.g., different cuts for u- vs. d-initiated subprocesses, or asymmetric rapidity cuts), **the cross section will be silently wrong**. Fix: set `group_subprocesses False` **before** `generate`/`output` — it is a generation-time MG5 option, not a run_card parameter:

```
set group_subprocesses False
generate p p > mu+ mu- j
output my_process
launch my_process
  set run_card custom_fcts ['/path/to/cuts.f']
```

Standard run_card cuts adjust both the integrand and the phase-space integrator; custom cuts only modify the integrand, so tight custom cuts reduce integration efficiency.

| Aspect | Standard run_card cuts | Custom cuts (`custom_fcts` / `dummy_fct.f`) |
|--------|----------------------|---------------------------------------------|
| Phase-space integrator | Adjusted to match cuts | Not adjusted — tight cuts reduce efficiency |
| Subprocess grouping | Safe (respects symmetries) | May break symmetries — set `group_subprocesses False` if needed |
| NLO support | Full | Only IRC-safe cuts; NLO uses different function signature |

**Details ->** [Troubleshooting](troubleshooting.md)

#### Matching Cuts

```
1       = ickkw         ! matching scheme: 0=none, 1=MLM, 3=FxFx (NLO)
20.0    = xqcut         ! kt measure for matching (GeV) — MUST be nonzero for MLM
4       = maxjetflavor   ! max jet flavor for matching (4 or 5)
```

See [Matching & Merging](matching-and-merging.md) for proper setup.

### Scale Choices

```
-1      = dynamical_scale_choice   ! scale choice:
         !   -1 = CKKW back-clustering (default)
         !    0 = user-defined (requires custom hook)
         !    1 = sum of transverse energy
         !    2 = HT (sum of pT)
         !    3 = HT/2
         !    4 = center-of-mass energy
1.0     = scalefact     ! overall scale factor (multiplies chosen scale)
```

Fixed scale: set `dynamical_scale_choice` to a positive value or use `fixed_ren_scale` and `fixed_fac_scale`.

### Systematics / Reweighting

```
True    = use_syst            ! enable on-the-fly reweighting
0.5 1 2 = sys_scalefact       ! scale variation factors
         = sys_pdf             ! LHAPDF IDs for alternative PDFs
```

See [Systematics & Reweighting](systematics-reweighting.md) for full details.

### Width Treatment

```
1e-06   = small_width_treatment  ! threshold ratio Gamma/M below which
                                  ! MG5 uses a fake larger width
```

### Fixed-Target Configuration

MadGraph supports fixed-target kinematics by setting asymmetric beam energies, with the target particle's `ebeam` set to `0` (at rest). The key principle: `lpp` controls whether a beam uses PDFs (i.e., whether it is a composite hadron), while `ebeam` controls its energy. A proton target at rest still needs `lpp = 1` to use proton PDFs.

#### Proton Beam on Proton Target

For a proton beam hitting a stationary proton target (e.g., SPS fixed-target, SHiP-like):

```
import model sm
generate p p > mu+ mu-
output my_fixed_target
launch my_fixed_target
  set run_card lpp1 1          # beam proton (with PDF)
  set run_card lpp2 1          # target proton (with PDF — still a proton!)
  set run_card ebeam1 400.0    # beam energy in GeV
  set run_card ebeam2 0        # target at rest
  set no_parton_cut            # remove default cuts (critical at low sqrt(s))
  set run_card nevents 10000
  done
```

**Both beams keep `lpp = 1`** because both are protons with partonic content described by PDFs. Setting `lpp = 0` for the target would make it a bare parton (quark or gluon), not a proton.

**`set no_parton_cut` is essential** at fixed-target energies. The default generation-level cuts (e.g., `ptl = 10` GeV, `ptj = 20` GeV, `etal = 2.5`) are typically too aggressive for the low $\sqrt{s}$ of fixed-target collisions and will produce zero cross section. Use `set no_parton_cut` to remove all parton-level cuts, then apply physics cuts downstream.

#### Lepton/Neutrino Beam on Proton Target

For a lepton or neutrino beam hitting a stationary proton (e.g., neutrino DIS, MINERvA-like):

```
import model sm
generate ve p > e- j       # CC neutrino DIS
output nu_dis
launch nu_dis
  set run_card lpp1 0          # neutrino beam (no PDF)
  set run_card lpp2 1          # proton target (with PDF)
  set run_card ebeam1 100.0    # neutrino energy in GeV
  set run_card ebeam2 0        # target proton at rest
  set run_card polbeam1 -100   # left-handed neutrino
  set no_parton_cut            # remove default cuts
  set run_card nevents 10000
  done
```

Here `lpp1 = 0` because the neutrino is an elementary particle with no PDF, while `lpp2 = 1` because the proton target has partonic content.

#### `ebeam = 0` vs `ebeam = particle mass`

Setting `ebeam = 0` means the particle is at rest; MadGraph internally uses the particle's mass for the kinematics. Setting the rest mass explicitly (e.g., `ebeam2 = 0.938` for a proton) produces equivalent results. In older MG5 versions, `ebeam = 0` could cause crashes, but this is fixed in current versions. Use `ebeam = 0` as the simplest approach.

#### Center-of-Mass Energy

For a beam of energy $E$ hitting a target of mass $m$ at rest:

$$\sqrt{s} = \sqrt{2 E m + 2 m^2}$$

When $E \gg m$, this simplifies to $\sqrt{s} \approx \sqrt{2 E m}$. For example, a 400 GeV proton on a proton target: $\sqrt{s} \approx \sqrt{2 \times 400 \times 0.938} \approx 27.4$ GeV.

#### LHE Output Frame

LHE event momenta are written in the **lab frame** defined by the beam configuration. When one beam is at rest (`ebeam = 0`), the output is in the target rest frame — i.e., the natural lab frame of the fixed-target experiment. This is confirmed by the MadGraph developers: "If you set the 'ebeam' parameter corresponding to the proton to either the mass of the proton or zero then the output file will be in the frame where the proton is at rest."

#### Generation-Level Cuts and Reference Frames

MadGraph evaluates generation-level cuts in two different frames:

- **Rapidity/pseudorapidity cuts** (`etaj`, `etal`, `etaa`) are evaluated in the **lab frame** (the beam frame defined by the `ebeam` values).
- **Transverse momentum cuts** (`ptj`, `ptl`, `pta`) and **angular separation cuts** (`drjj`, `drll`, `draj`) are evaluated in the **partonic center-of-mass frame**.

In fixed-target kinematics, both types of cuts cause problems with default values:

- **Rapidity cuts**: In the lab frame, particles are boosted to very forward (large) rapidity. Default cuts like `etal = 2.5` reject most or all events.
- **pT cuts**: At low $\sqrt{s}$, the available pT in the partonic CM is limited. Default cuts like `ptj = 20` GeV or `ptl = 10` GeV may be kinematically impossible.

The simplest solution is `set no_parton_cut`, which removes all generation-level cuts. Apply detector-level angular and momentum cuts downstream (e.g., in Pythia8, Delphes, or analysis code).

#### Nuclear Targets

For a nuclear target (e.g., tungsten, lead), use the hidden ion parameters (revealed by `update ion_pdf`):

```
set run_card lpp2 1
set run_card ebeam2 0
set run_card nb_proton2 82      # e.g., lead-208
set run_card nb_neutron2 126
set run_card mass_ion2 195.08   # lead mass in GeV (MadGraph convention)
```

**MadGraph convention for `mass_ion`**: MadGraph computes ion mass as `A_amu × m_p`, where `A_amu` is the atomic mass in unified atomic mass units and `m_p ≈ 0.938` GeV. For lead-208, this gives `207.9766521 × 0.938 ≈ 195.08` GeV. This differs from the physical nuclear mass (~193.7 GeV, which accounts for binding energy). Use the MadGraph convention for consistency with MadGraph's built-in shortcuts like `set PbPb`.

**Shortcut for lead-lead**: Use `set PbPb` in the launch script to auto-populate `nb_proton`, `nb_neutron`, and `mass_ion` for both beams with lead-208 values (`mass_ion = 195.0821`, `nb_proton = 82`, `nb_neutron = 126`).

For a neutron target specifically:

```
set run_card nb_proton2 0
set run_card nb_neutron2 1
set run_card mass_ion2 0.93957
```

The ion mechanism performs PDF rescaling based on the nuclear composition (isospin weighting) but does **not** include nuclear modification factors (shadowing, EMC effect). For dedicated nuclear PDFs (e.g., nCTEQ15, EPPS21), install the appropriate LHAPDF set and specify its ID via `lhaid`.

**Key points:**
- A proton target at rest uses `lpp = 1` (with PDF) and `ebeam = 0`. Do **not** set `lpp = 0` for a proton target — that makes it a bare parton.
- A lepton/neutrino beam uses `lpp = 0` (no PDF).
- Use `set no_parton_cut` to remove generation-level cuts — default cuts produce zero cross section at typical fixed-target energies.
- Rapidity cuts (`etaj`, `etal`) are in the lab frame; pT cuts (`ptj`, `ptl`) are in the partonic CM frame.
- LHE output is in the lab frame (target rest frame when `ebeam = 0`).
- For nuclear targets, `mass_ion` follows MadGraph's convention (`A_amu × m_p`); use `set PbPb` for lead to auto-populate correct values.

**Details ->** [Lepton & Photon Colliders](lepton-photon-colliders.md) for other asymmetric beam setups (ep, eA)