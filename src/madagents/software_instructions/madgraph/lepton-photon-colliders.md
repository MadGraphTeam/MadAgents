# 22 — Lepton and Photon Collider Configuration

MadGraph supports a variety of beam types beyond proton-proton collisions, including electron-positron, muon, photon, and asymmetric (e.g., ep) colliders. The beam type is configured via the `lpp` parameters in the run card.

## Contents

- [Beam Type (`lpp`)](#beam-type-lpp)
  - [Valid `lpp` Values](#valid-lpp-values)
- [Electron-Positron Colliders](#electron-positron-colliders)
  - [Basic e+e- Setup (No ISR)](#basic-ee-setup-no-isr)
  - [e+e- with ISR Structure Functions](#ee-with-isr-structure-functions)
- [Muon Colliders](#muon-colliders)
- [Photon-Initiated Processes (EPA)](#photon-initiated-processes-epa)
  - [Photon-Photon Fusion](#photon-photon-fusion)
  - [Photon-Proton (ep-like at LHC)](#photon-proton-ep-like-at-lhc)
- [Asymmetric Colliders (ep)](#asymmetric-colliders-ep)
- [Beam Polarization](#beam-polarization)
- [Heavy Ion Collisions](#heavy-ion-collisions)
- [NLO Limitations for Non-Standard Beam Configurations](#nlo-limitations-for-non-standard-beam-configurations)
  - [Configurations Blocked at NLO (DIS Error)](#configurations-blocked-at-nlo-dis-error)
  - [Configurations That Pass the DIS Check at NLO](#configurations-that-pass-the-dis-check-at-nlo)
  - [Example: DIS at LO (Correct)](#example-dis-at-lo-correct)
  - [Example: DIS at NLO (Will Fail)](#example-dis-at-nlo-will-fail)

## Beam Type (`lpp`)

```
1   = lpp1   ! beam 1 type
1   = lpp2   ! beam 2 type
```

### Valid `lpp` Values

| `lpp` | Beam type | Description |
|-------|-----------|-------------|
| **0** | No PDF (fixed energy) | Lepton beam at fixed energy. Use for e+e- or mu+mu- without ISR structure functions. |
| **1** | Proton | Proton beam with PDF (default). |
| **-1** | Antiproton | Antiproton beam with PDF. |
| **2** | Elastic photon from proton | Equivalent Photon Approximation (EPA): photon emitted quasi-elastically from a proton. |
| **-2** | Elastic photon from antiproton | EPA from an antiproton. |
| **3** | Electron (with ISR) | Electron beam with ISR structure functions from the PDF framework. |
| **-3** | Positron (with ISR) | Positron beam with ISR structure functions. |
| **4** | Muon (with ISR) | Muon beam with ISR structure functions. |
| **-4** | Antimuon (with ISR) | Antimuon beam with ISR structure functions. |
| **9** | Plugin mode | Custom beam definition via a plugin module. |

## Electron-Positron Colliders

### Basic e+e- Setup (No ISR)

For a simple fixed-energy electron-positron collider:

```
import model sm
generate e+ e- > mu+ mu-
output ee_mumu
launch ee_mumu
  set run_card lpp1 0
  set run_card lpp2 0
  set run_card ebeam1 125.0    ! 250 GeV center-of-mass
  set run_card ebeam2 125.0
  set run_card pdlabel none
  done
```

With `lpp = 0`, the beams have fixed energy (no PDF, no ISR). The `pdlabel` should be set to `none`.

### e+e- with ISR Structure Functions

For more realistic lepton collider simulations including initial-state radiation:

```
set run_card lpp1 -3    ! positron with ISR
set run_card lpp2 3     ! electron with ISR
set run_card ebeam1 125.0
set run_card ebeam2 125.0
```

With `lpp = +/-3`, MG5 applies electron/positron PDF-like structure functions that account for ISR photon emission, giving a more realistic beam energy spectrum.

## Muon Colliders

For muon collider simulations:

```
set run_card lpp1 -4    ! antimuon with ISR
set run_card lpp2 4     ! muon with ISR
set run_card ebeam1 5000.0    ! 10 TeV center-of-mass
set run_card ebeam2 5000.0
```

## Photon-Initiated Processes (EPA)

The Equivalent Photon Approximation allows simulation of photon-photon or photon-proton processes at hadron colliders:

### Photon-Photon Fusion

```
import model sm
generate a a > w+ w-
output aa_ww
launch aa_ww
  set run_card lpp1 2     ! elastic photon from proton
  set run_card lpp2 2     ! elastic photon from proton
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  done
```

### Photon-Proton (ep-like at LHC)

```
set run_card lpp1 1     ! proton
set run_card lpp2 2     ! elastic photon from proton
```

## Asymmetric Colliders (ep)

For electron-proton collisions (like HERA or the EIC):

```
set run_card lpp1 0     ! electron (fixed energy, no PDF)
set run_card lpp2 1     ! proton (with PDF)
set run_card ebeam1 27.5    ! electron energy
set run_card ebeam2 920     ! proton energy
set run_card pdlabel none   ! (will be overridden by lpp2=1 for beam 2)
```

For per-beam PDF control, use the hidden parameters `pdlabel1` and `pdlabel2`.

## Beam Polarization

Beam polarization is controlled by `polbeam1` and `polbeam2` (hidden parameters, revealed by `update beam_pol`):

```
set run_card polbeam1 -80.0   ! 80% left-handed beam 1
set run_card polbeam2  30.0   ! 30% right-handed beam 2
```

The value ranges from **-100** (fully left-handed) to **+100** (fully right-handed). Zero means unpolarized.

**Important**: Beam polarization is only meaningful for `lpp = 0` (fixed-energy lepton beams). It does not apply to proton beams (`lpp = 1`).

Use cases:
- ILC-like scenarios: e+e- with polarized beams (e.g., `polbeam1 = -80`, `polbeam2 = +30`)
- Testing specific helicity configurations at lepton colliders

## Heavy Ion Collisions

MG5 supports heavy ion beams via hidden parameters (revealed by `update ion_pdf`):

```
set run_card nb_proton1 82    ! number of protons (e.g., lead: 82)
set run_card nb_neutron1 126  ! number of neutrons (lead: 126)
```

This is relevant for ultra-peripheral collisions (UPC) and photon-photon processes in heavy-ion physics.

## NLO Limitations for Non-Standard Beam Configurations

At NLO, MadGraph5_aMC@NLO blocks any beam configuration that pairs a **proton beam (`lpp=1`)** with a non-proton/antiproton beam. The run_card validation check (in `banner.py`) raises an `InvalidRunCard` error whenever:
1. At least one beam is not a proton or antiproton (`abs(lpp) != 1`), **AND**
2. At least one beam is specifically a proton (`lpp == 1`).

This means lepton-proton, EPA photon-proton, and dressed lepton-proton configurations are all blocked at NLO.

### Configurations Blocked at NLO (DIS Error)

| Configuration | Beam settings | Error |
|---------------|---------------|-------|
| Lepton-proton (DIS) | `lpp1=0, lpp2=1` | `InvalidRunCard: Process like Deep Inelastic scattering not supported at NLO accuracy.` |
| Proton-lepton (DIS) | `lpp1=1, lpp2=0` | Same |
| EPA photon-proton | `lpp1=2, lpp2=1` | Same |
| Proton-EPA photon | `lpp1=1, lpp2=2` | Same |
| Dressed lepton-proton | `lpp1=±3, lpp2=1` (or `±4`) | Same |
| Proton-dressed lepton | `lpp1=1, lpp2=±3` (or `±4`) | Same |

### Configurations That Pass the DIS Check at NLO

| Configuration | Beam settings | Notes |
|---------------|---------------|-------|
| Proton-proton | `lpp1=1, lpp2=1` | Standard hadron collider |
| Proton-antiproton | `lpp1=1, lpp2=-1` | Tevatron-like |
| Antiproton-proton | `lpp1=-1, lpp2=1` | Tevatron-like |
| Lepton-lepton | `lpp1=0, lpp2=0` | No PDFs |
| Dressed lepton-lepton | `lpp1=±3, lpp2=±3` (or `±4`) | With lepton ISR PDFs |
| EPA photon-EPA photon | `lpp1=2, lpp2=2` | Passes DIS check (may fail later for other reasons) |
| Lepton-EPA photon | `lpp1=0, lpp2=2` | Passes DIS check (may fail later for other reasons) |
| Lepton-antiproton | `lpp1=0, lpp2=-1` | Passes DIS check (antiproton is `lpp=-1`, not `lpp=1`) |

> **Note:** Passing the DIS check does not guarantee that NLO generation will succeed end-to-end. Some configurations (e.g., EPA-EPA at NLO) may pass run_card validation but fail during integration for other reasons.

**Key points:**
- The error is raised at **launch time** (run_card validation), not at process generation. The `generate` and `output` steps succeed; the failure occurs when `launch` validates the run_card.
- LO generation works for **all** beam configurations. Only NLO (`[QCD]`, `[QED]`) triggers the DIS restriction.
- The restriction specifically checks for `lpp == 1` (proton), not `lpp == -1` (antiproton). This means lepton-antiproton (`lpp1=0, lpp2=-1`) is **not** blocked by this check, even though it is also an asymmetric lepton-hadron configuration.
- For DIS-like processes (e.g., `e- p > e- j`), generate at **LO** and shower with Pythia8. Expect significant event rejection rates from Pythia8 due to the asymmetric beam configuration.

### Example: DIS at LO (Correct)

```
import model sm
generate e- p > e- j
output ep_DIS
launch ep_DIS
  set run_card lpp1 0
  set run_card lpp2 1
  set run_card ebeam1 18.0
  set run_card ebeam2 275.0
  done
```

### Example: DIS at NLO (Will Fail)

```
import model loop_sm
generate e- p > e- j [QCD]
output ep_DIS_NLO
launch ep_DIS_NLO       # ERROR: InvalidRunCard
  set run_card lpp1 0
  set run_card lpp2 1
  set run_card ebeam1 18.0
  set run_card ebeam2 275.0
  done
```

This produces: `InvalidRunCard: Process like Deep Inelastic scattering not supported at NLO accuracy.`

See also: [NLO Computations](nlo-computations.md) — general NLO requirements and pitfalls
