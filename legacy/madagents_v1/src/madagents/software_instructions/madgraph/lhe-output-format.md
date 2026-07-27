# 15 — Output Formats & LHE

MadGraph produces events in the Les Houches Event (LHE) format, an XML-based standard for parton-level Monte Carlo events. LHE file structure, event records, weight handling, and Python parsing.

## Contents

- [LHE File Location](#lhe-file-location)
- [LHE XML Structure](#lhe-xml-structure)
  - [The `<header>` Block](#the-header-block)
  - [The `<init>` Block](#the-init-block)
  - [The `<event>` Block](#the-event-block)
  - [SPINUP — Spin and Helicity Information](#spinup-spin-and-helicity-information)
  - [Tau Polarization and Parton Shower Decays](#tau-polarization-and-parton-shower-decays)
  - [Intermediate Particles](#intermediate-particles)
  - [Reweighting Weights](#reweighting-weights)
- [Weighted vs Unweighted Events](#weighted-vs-unweighted-events)
- [Parsing LHE Files with Python](#parsing-lhe-files-with-python)
  - [Extracting the Cross-Section](#extracting-the-cross-section)
  - [Counting Events and Extracting PDG IDs](#counting-events-and-extracting-pdg-ids)
  - [Computing Invariant Mass](#computing-invariant-mass)
- [Other Output Formats](#other-output-formats)

## LHE File Location

After a successful run:

- **LO (MadEvent)**: `<PROC_DIR>/Events/run_01/unweighted_events.lhe.gz`
- **NLO (aMC@NLO)**: `<PROC_DIR>/Events/run_01/events.lhe.gz`

The file is gzip-compressed. Use `gzip -d` to decompress, or read directly with Python's `gzip` module.

## LHE XML Structure

An LHE file has three main sections:

```xml
<LesHouchesEvents version="3.0">
<header>
  <!-- Run banner: all cards, MG5 version, process info -->
</header>
<init>
  <!-- Cross-section and process information -->
  2212  2212  6.500000e+03  6.500000e+03  ...
  5.044960e+02  1.234560e+00  1.000000e+00  1
</init>
<event>
  <!-- First event record -->
</event>
<event>
  <!-- Second event record -->
</event>
...
</LesHouchesEvents>
```

### The `<header>` Block

Contains the complete run configuration: run_card, param_card, model information, and MG5 version. Useful for reproducing the run.

### The `<init>` Block

Contains beam information and process cross-sections:

```
IDBMUP(1)  IDBMUP(2)  EBMUP(1)  EBMUP(2)  PDFGUP(1)  PDFGUP(2)  PDFSUP(1)  PDFSUP(2)  IDWTUP  NPRUP
XSECUP(1)  XERRUP(1)  XMAXUP(1)  LPRUP(1)
```

- `IDBMUP`: Beam particle PDG IDs (2212 = proton)
- `EBMUP`: Beam energies in GeV
- `XSECUP`: Cross-section in pb
- `XERRUP`: Cross-section uncertainty in pb
- `NPRUP`: Number of subprocesses

### The `<event>` Block

Each event contains a header line followed by one line per particle:

```
NUP  IDPRUP  XWGTUP  SCALUP  AQEDUP  AQCDUP
IDUP  ISTUP  MOTHUP(1)  MOTHUP(2)  ICOLUP(1)  ICOLUP(2)  PUP(1)  PUP(2)  PUP(3)  PUP(4)  PUP(5)  VTIMUP  SPINUP
```

**Event header fields:**
- `NUP`: Number of particles in the event
- `XWGTUP`: Event weight (normalization depends on `event_norm` setting — see below)
- `SCALUP`: Scale of the event in GeV

**Particle record columns:**

| Column | Name | Description |
|--------|------|-------------|
| 1 | IDUP | PDG particle ID |
| 2 | ISTUP | Status: -1 = incoming, 1 = final-state, 2 = intermediate |
| 3-4 | MOTHUP | Mother particle indices (1-indexed) |
| 5-6 | ICOLUP | Color flow tags |
| 7-10 | PUP(1-4) | 4-momentum: px, py, pz, E (GeV) |
| 11 | PUP(5) | Generated mass (GeV) |
| 12 | VTIMUP | Proper lifetime (mm/c) |
| 13 | SPINUP | Spin/helicity information (see below) |

### SPINUP — Spin and Helicity Information

The SPINUP column (column 13) encodes the spin state of each particle in the event:

| Value | Meaning |
|-------|---------|
| `+1.0` | Spin-up / positive helicity along the z-axis |
| `-1.0` | Spin-down / negative helicity along the z-axis |
| `0.0` | No spin information available (averaged over spins) |
| `9.0` | Spin information not meaningful (conventions vary by generator) |

By default, MadGraph sets SPINUP to `9.0` for most particles, indicating that spin information is not stored at the event level — the matrix element was evaluated summing/averaging over spins. When MadSpin is used for decays, it assigns physical spin states to the decayed particles, and the SPINUP values reflect the chosen helicity configuration for that event.

For polarized generation (e.g., `generate p p > w+{0} w-{T}`), the SPINUP values correspond to the selected polarization state of the specified particles.

### Tau Polarization and Parton Shower Decays

Tau polarization in the MadGraph → Pythia8 chain depends on whether MadSpin is used and whether taus are decayed at the MadGraph level or the shower level.

**How MadSpin sets SPINUP**: MadSpin computes the full production matrix element and selects a helicity configuration event-by-event via importance sampling. It assigns physical helicities (SPINUP = ±1) to **all** final-state particles — including taus that are not themselves being decayed. A tau that IS decayed by MadSpin becomes an intermediate particle (status=2, SPINUP=9.0) whose decay products carry physical helicities ±1.

**How Pythia8 reads SPINUP**: Pythia8's `TauDecays:mode` setting controls tau polarization:

| Mode | Behavior |
|------|----------|
| 0 | Isotropic decay (no polarization) |
| **1** (default) | **External (SPINUP) first; if SPINUP = 9.0, falls back to internal calculation** |
| 2 | Forced polarization via `TauDecays:tauPolarization` for taus from a specific mother |
| 3 | Forced polarization for all taus |
| 4 | Internal determination only (ignores SPINUP) |
| 5 | External (SPINUP) determination only |

In the default mode (1), Pythia8 checks the tau's SPINUP value. If it is ±1 (valid helicity), the external mechanism succeeds and that helicity is used directly. If it is 9.0 (no spin info), the external mechanism fails and Pythia8 falls back to computing the polarization internally from the mother/mediator particle identity and kinematics. After FSR creates copies of the tau with modified momentum, Pythia8 traces back to the original LHE-level tau via `iTopCopyId()` to recover the original SPINUP value.

**Standard workflows**:

1. **MadSpin decays the tau** (e.g., `set madspin_card decay ta+ > ...`): The tau becomes status=2 in the LHE file and Pythia8 does not re-decay it. Spin correlations from MadSpin are fully preserved. Set `15:mayDecay = no` in the pythia8_card to ensure Pythia8 does not interfere.

2. **MadSpin is active but does not decay the tau**: MadSpin still assigns SPINUP = ±1 to the final-state tau from the production ME. Pythia8's default mode reads this value and decays the tau with the correct helicity. Spin correlations are preserved.

3. **MadSpin is not used**: Taus have the MadGraph default SPINUP = 9.0. Pythia8's default mode falls back to its internal polarization calculation, which works correctly for standard SM production mechanisms (W → τν, Z → ττ, H → ττ). For BSM or non-standard production, the internal calculation may not cover the relevant matrix elements — in that case, use MadSpin to assign physical helicities.

**Status codes:**
- `-1`: Incoming particle (beam parton)
- `+1`: Outgoing (final-state) particle
- `+2`: Intermediate resonance (on-shell, appears when using decay chain syntax)

### Intermediate Particles

MG5 only writes intermediate particles (ISTUP = 2) to the LHE file when they are on-shell — i.e., their invariant mass falls within the Breit-Wigner window (M ± bwcutoff × Γ). For processes with multiple interfering diagrams (e.g., `e+ e- > mu+ mu-` via Z and γ), no unique intermediate particle exists, so none appears in the output. To force an intermediate particle in the output, use the on-shell decay chain syntax: `e+ e- > z, z > mu+ mu-`.

### Reweighting Weights

If systematics reweighting is enabled (`use_syst = True`), each event contains an `<rwgt>` block:

```xml
<event>
  ... (particle records) ...
  <rwgt>
    <wgt id='1001'> 1.0234e+02 </wgt>
    <wgt id='1002'> 1.1456e+02 </wgt>
    ...
  </rwgt>
</event>
```

The weight IDs map to specific scale/PDF combinations. See [Systematics & Reweighting](systematics-reweighting.md).

## Weighted vs Unweighted Events

- **Unweighted events** (default): All events carry equal weight. The weight normalization is controlled by the hidden `event_norm` parameter in the run_card:
  - `average` (default): XWGTUP = σ for each event, so the **average** of all weights equals the cross-section.
  - `sum`: XWGTUP = σ/N_events, so the **sum** of all weights equals the cross-section.
  - `unity`: XWGTUP = ±1.
  The cross-section is always available in the `<init>` block regardless of weight normalization.
- **Weighted events**: Events have varying weights. Produced when using biased event generation (`bias_module`) or during reweighting. Note: setting `nevents = 0` runs integration only and produces no event file. For physics analyses, each event must be filled into histograms with its weight.

If you see large weight variations (weights spanning many orders of magnitude), the integration grid may need more optimization, or generation cuts may be needed.

## Parsing LHE Files with Python

### Extracting the Cross-Section

```python
import gzip

def extract_cross_section(lhe_path):
    """Extract cross-section from the <init> block."""
    with gzip.open(lhe_path, 'rt') as f:
        in_init = False
        for line in f:
            if '<init>' in line:
                in_init = True
                next(f)  # skip beam info line
                continue
            if '</init>' in line:
                break
            if in_init:
                parts = line.split()
                xsec = float(parts[0])  # cross-section in pb
                xerr = float(parts[1])  # uncertainty in pb
                return xsec, xerr
    return None, None

xsec, xerr = extract_cross_section('unweighted_events.lhe.gz')
print(f"Cross-section: {xsec:.4f} ± {xerr:.4f} pb")
```

### Counting Events and Extracting PDG IDs

```python
import gzip

def parse_events(lhe_path):
    """Parse LHE events, extract final-state PDG IDs."""
    events = []
    with gzip.open(lhe_path, 'rt') as f:
        in_event = False
        current_event = []
        for line in f:
            if '<event>' in line:
                in_event = True
                current_event = []
                continue
            if '</event>' in line:
                in_event = False
                events.append(current_event)
                continue
            if in_event and not line.strip().startswith('<'):
                current_event.append(line.strip())

    # Extract final-state PDG IDs from each event
    for i, event_lines in enumerate(events):
        if not event_lines:
            continue
        # First line is the event header
        header = event_lines[0].split()
        n_particles = int(header[0])

        final_state = []
        for pline in event_lines[1:]:
            parts = pline.split()
            if len(parts) >= 13:
                pdg_id = int(parts[0])
                status = int(parts[1])
                if status == 1:  # final-state
                    final_state.append(pdg_id)

        if i == 0:
            print(f"Event 1 final-state PDGs: {final_state}")

    print(f"Total events: {len(events)}")
    return events

events = parse_events('unweighted_events.lhe.gz')
```

### Computing Invariant Mass

```python
import math
import gzip

def compute_mtt(lhe_path):
    """Compute the average invariant mass of tt̄ pairs."""
    masses = []
    with gzip.open(lhe_path, 'rt') as f:
        in_event = False
        particles = []
        for line in f:
            if '<event>' in line:
                in_event = True
                particles = []
                continue
            if '</event>' in line:
                in_event = False
                # Find top (6) and antitop (-6)
                top = None
                antitop = None
                for p in particles:
                    if p['pdg'] == 6 and p['status'] == 1:
                        top = p
                    elif p['pdg'] == -6 and p['status'] == 1:
                        antitop = p
                if top and antitop:
                    E = top['E'] + antitop['E']
                    px = top['px'] + antitop['px']
                    py = top['py'] + antitop['py']
                    pz = top['pz'] + antitop['pz']
                    m2 = E**2 - px**2 - py**2 - pz**2
                    masses.append(math.sqrt(max(0, m2)))
                continue
            if in_event and not line.strip().startswith('<'):
                parts = line.split()
                if len(parts) >= 13:
                    particles.append({
                        'pdg': int(parts[0]),
                        'status': int(parts[1]),
                        'px': float(parts[6]),
                        'py': float(parts[7]),
                        'pz': float(parts[8]),
                        'E': float(parts[9]),
                    })

    if masses:
        mean_mtt = sum(masses) / len(masses)
        print(f"Mean m(tt̄) = {mean_mtt:.1f} GeV ({len(masses)} events)")
        return mean_mtt
    return None

mean_mtt = compute_mtt('unweighted_events.lhe.gz')
```


## Other Output Formats

MG5 and its tool chain produce additional output formats beyond LHE:

- **HepMC** (`.hepmc.gz`): Written by Pythia8 after parton shower and hadronization. Contains the full particle-level event record including hadrons. Read by Delphes, MadAnalysis5, Rivet, and other analysis tools.
- **ROOT** (`.root`): Written by Delphes after detector simulation. Contains reconstructed objects (jets, leptons, photons, MET) in ROOT TTrees. Read by ROOT, PyROOT, uproot, or MadAnalysis5.

File locations: see [Scripted Execution](scripted-execution.md) for the output directory structure.
