# Diagram Filtering and Resonance Separation

This document covers MadGraph5 diagram filtering operators (`/`, `$`, `$$`), gauge invariance considerations, the `bwcutoff` parameter, resonant vs non-resonant separation strategies, and the diagram filter plugin.

## Contents

- [Diagram Filtering: `/`, `$`, `$$`](#diagram-filtering)
  - [`/` — Remove from All Propagators](#remove-from-all-propagators)
  - [`$$` — Remove from S-Channel Only](#remove-from-s-channel-only)
  - [`$` — Forbid On-Shell S-Channel](#forbid-on-shell-s-channel)
  - [Summary Table](#summary-table)
  - [Example: Z/γ Separation](#example-zγ-separation)
- [Gauge Invariance and Diagram Filtering](#gauge-invariance-and-diagram-filtering)
  - [1. Breaking Gauge Invariance](#1-breaking-gauge-invariance)
  - [2. Missing Interference](#2-missing-interference)
  - [Gauge Invariance of Diagram Filtering: Scalars vs Gauge Bosons](#gauge-invariance-of-diagram-filtering-scalars-vs-gauge-bosons)
  - [Signal/Background/Interference Separation via Squared Coupling Orders](#signalbackgroundinterference-separation-via-squared-coupling-orders)
  - [Commands from the Official Wiki](#commands-from-the-official-wiki)
  - [Alternative: Diagram Exclusion with `/h`](#alternative-diagram-exclusion-with-h)
  - [Summary: Signal/Background Separation Methods](#summary-signalbackground-separation-methods)
- [The `bwcutoff` Parameter and On-Shell/Off-Shell Boundaries](#the-bwcutoff-parameter-and-on-shelloff-shell-boundaries)
  - [Definition and Default](#definition-and-default)
  - [When `bwcutoff` Affects the Cross Section](#when-bwcutoff-affects-the-cross-section)
  - [How `bwcutoff` Interacts with Each Operator](#how-bwcutoff-interacts-with-each-operator)
  - [Practical Guidance](#practical-guidance)
- [Resonant vs Non-Resonant Separation Strategies](#resonant-vs-non-resonant-separation-strategies)
  - [Approach 1: Decay Chain (Narrow-Width Approximation)](#approach-1-decay-chain-narrow-width-approximation)
  - [Approach 2: Full Matrix Element](#approach-2-full-matrix-element)
  - [Approach 3: `$` Operator (Off-Shell Complement)](#approach-3-operator-off-shell-complement)
  - [Approach 4: `$$` Operator (Diagram Removal)](#approach-4-operator-diagram-removal)
  - [Approach 5: DR/DS Schemes at NLO (MadSTR Plugin)](#approach-5-drds-schemes-at-nlo-madstr-plugin)
  - [Summary: Choosing the Right Approach](#summary-choosing-the-right-approach)
- [Diagram Filter Plugin (`--diagram_filter`)](#diagram-filter-plugin---diagram_filter)
  - [Setup](#setup)
  - [Decay Chains](#decay-chains)
  - [Diagram Data Structure (Legacy API)](#diagram-data-structure-legacy-api)
  - [Diagram Data Structure (Drawing API)](#diagram-data-structure-drawing-api)
  - [Examples](#examples)
  - [Filter by Coupling Orders](#filter-by-coupling-orders)
  - [Remove T-Channel Quarks (Legacy API)](#remove-t-channel-quarks-legacy-api)
  - [Remove 4-Point Contact Interactions (Drawing API)](#remove-4-point-contact-interactions-drawing-api)
  - [Production-Only Filter (Skip Decay Chain Diagrams)](#production-only-filter-skip-decay-chain-diagrams)
  - [When to Use the Diagram Filter vs Built-In Operators](#when-to-use-the-diagram-filter-vs-built-in-operators)
  - [Known Issues (Historical)](#known-issues-historical)

## Diagram Filtering: `/`, `$`, `$$`

Three operators control which intermediate particles appear in Feynman diagrams:

### `/` — Remove from All Propagators

```
generate p p > e+ e- / h
```

Removes **all** diagrams containing the Higgs as an internal line, in both s-channel and t-channel. This is the most aggressive exclusion.

### `$$` — Remove from S-Channel Only

```
generate p p > e+ e- $$ z
```

Removes **all** diagrams with Z in the **s-channel**, regardless of whether the propagator is on-shell or off-shell. T-channel Z propagators (if any) are kept. Useful for separating production topologies.

### `$` — Forbid On-Shell S-Channel

```
generate p p > e+ e- $ z
```

Keeps all diagrams but **forbids the Z from going on-shell** in the s-channel — i.e., the Z invariant mass must be outside the Breit-Wigner window (M ± bwcutoff × Γ). Off-shell s-channel contributions are retained. Useful for studying off-shell tails.

Note: `$` is less aggressive than `$$`. With `$$`, the diagrams are removed entirely. With `$`, the diagrams remain but only their off-shell contributions survive.

### Summary Table

| Operator | S-channel diagrams | T-channel diagrams | Off-shell s-channel | On-shell s-channel |
|----------|-------------------|-------------------|--------------------|--------------------|
| `/ X` | Removed | Removed | Removed | Removed |
| `$$ X` | Removed | Kept | Removed | Removed |
| `$ X` | Kept | Kept | Kept | Forbidden |

### Example: Z/γ Separation

```
generate p p > e+ e-             # full process (Z + γ + interference)
generate p p > e+ e- $$ a        # Z-only diagrams (no s-channel photon)
generate p p > e+ e- $$ z        # γ-only diagrams (no s-channel Z)
```

**Warning**: The Z-only and γ-only cross-sections do **not** sum to the full cross-section. The missing piece is the Z/γ **interference term**, which is constructive below the Z pole and destructive above it. This separation is not physically meaningful — see Gauge Invariance below.

## Gauge Invariance and Diagram Filtering

When using `/`, `$`, or `$$` to select diagram subsets, two critical dangers arise:

### 1. Breaking Gauge Invariance

Each diagram subset must be independently gauge invariant. If not, the matrix element calculation gives gauge-dependent (unphysical) results. For example, separating Z and γ diagrams individually is gauge invariant (each is a complete gauge-invariant subset). But more complex filterings may break gauge invariance.

**Always verify** with the `check` command:

```
generate p p > e+ e- $$ a
check gauge p p > e+ e- $$ a
```

If the check fails, the diagram subset is not gauge invariant and the results are unreliable.

### 2. Missing Interference

Even when each subset is gauge invariant, splitting a process into subsets loses the interference between subsets. The interference contribution can increase or decrease the cross-section — it is not always positive.

**Bottom line**: Diagram filtering is a useful tool for understanding topologies, but the filtered cross-sections are not directly interpretable as physical contributions. Use the full (unfiltered) process for physics predictions.

### Gauge Invariance of Diagram Filtering: Scalars vs Gauge Bosons

The gauge-invariance risk of diagram filtering depends critically on **what particle is being excluded**:

| Particle type | Example | Gauge invariant to exclude? | Reason |
|---|---|---|---|
| **Gauge bosons** (W, Z, γ, g) | `$$ z`, `/ a` | **Depends on process** | Gauge boson propagators can participate in gauge cancellations between diagrams. Excluding them is safe when the subsets are separately gauge invariant (e.g., Z and γ in Drell-Yan are separate gauge-invariant subsets), but unsafe when diagrams with different gauge bosons cancel against each other (e.g., W/Z in some multi-boson processes). See the existing "Gauge Invariance and Diagram Filtering" section above for specific safe/unsafe cases. |
| **Scalar singlets** (Higgs) | `$$ h`, `/ h` | **Yes** | The Higgs boson is a physical scalar and a gauge singlet. Its propagator is independent of the gauge-fixing parameter (ξ) in R_ξ gauges. Diagrams with and without a Higgs propagator form separately gauge-invariant subsets. |

**Key point:** Using `/ h` or `$$ h` to exclude Higgs-mediated diagrams does **not** break gauge invariance. This is a fundamental difference from excluding gauge bosons whose propagators depend on the gauge parameter.

However, diagram exclusion still has a physical limitation: the **interference term** between Higgs-mediated and non-Higgs diagrams is lost. For processes where signal–background interference is large (e.g., gg → ZZ near and above the Higgs mass), this missing interference can shift the cross section by O(10%) or more in the high-mass tail. The issue is not gauge dependence but an incomplete physics description.

### Signal/Background/Interference Separation via Squared Coupling Orders

For processes like gg → ZZ or gg → WW, the cleanest way to isolate signal, background, and interference is through **squared coupling-order constraints** in a modified model. The official MadGraph wiki provides `loop_sm_modif`, a modified version of `loop_sm` where the Higgs–gauge-boson couplings (HWW, HZZ) are assigned a custom coupling order `NP` instead of the default `QED`.

**What NP tags:** In `loop_sm_modif`, the `NP` coupling order tags the **Higgs–gauge-boson vertices** (HWW and HZZ couplings, i.e., GC_31 and GC_32 in the UFO). Yukawa couplings (yb, yt, etc.) remain tagged with `QED`, unchanged from the standard `loop_sm`. The `NP` order therefore counts the number of HVV vertices in the amplitude.

**Setup:** Download `loop_sm_modif.tar.gz` from the [MadGraph Offshell_interference_effects wiki page](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/Offshell_interference_effects) and extract it into your models directory.

#### Commands from the Official Wiki

The MadGraph wiki shows the following syntax for gg → ZZ (4-lepton final state):

```
import model loop_sm_modif

# Signal only (Higgs-mediated squared, triangle²):
generate g g > e+ e- mu+ mu- / e+ e- mu+ mu- [QCD] NP^2==2

# Interference only (triangle × box):
generate g g > e+ e- mu+ mu- / e+ e- mu+ mu- [QCD] NP^2==1

# Background only (box², no Higgs):
generate g g > e+ e- mu+ mu- / e+ e- mu+ mu- [QCD] NP=0

# Total (signal + background + interference):
generate g g > e+ e- mu+ mu- / e+ e- mu+ mu- [QCD] NP=1
```

**Important version caveat:** The `==` squared-order constraint (e.g., `NP^2==2`) may fail in some MadGraph versions with the error *"The squared-order constraints passed are not <=. Other kind of squared-order constraints are not supported at NLO"*. This is because loop-induced processes with `[QCD]` use the NLO framework internally. If `==` fails, use `<=` constraints with subtraction:

```
import model loop_sm_modif

# Background only (no Higgs vertices):
generate g g > e+ e- mu+ mu- / e+ e- mu+ mu- [QCD] NP=0
# → σ_bkg

# Background + interference (up to 1 HVV vertex in |M|²):
generate g g > e+ e- mu+ mu- / e+ e- mu+ mu- [QCD] NP^2<=1
# → σ_bkg + σ_int

# Full (all contributions):
generate g g > e+ e- mu+ mu- / e+ e- mu+ mu- [QCD] NP^2<=2
# → σ_bkg + σ_int + σ_sig
```

Then extract each piece by subtraction: σ_int = σ(NP^2<=1) − σ(NP=0), and σ_sig = σ(NP^2<=2) − σ(NP^2<=1).

**Important:** The standard `loop_sm` model does **not** define the `NP` coupling order — it only has `QCD` and `QED`. You must use `loop_sm_modif` (or create your own modification). Using an undefined coupling order with `loop_sm` will produce an error.

The `/ e+ e- mu+ mu-` in the commands above excludes diagrams with these leptons as internal lines, which is standard for this process to avoid double-counting.

#### Alternative: Diagram Exclusion with `/h`

```
import model loop_sm
# Background only (box diagrams) — gauge invariant:
generate g g > z z / h [noborn=QCD]

# Full process (signal + background + interference):
generate g g > z z [noborn=QCD]
```

The background-only result is gauge invariant (Higgs is a scalar singlet). Interference is obtained by subtraction: σ_int = σ_full − σ_signal − σ_bkg, requiring three separate runs.

#### Summary: Signal/Background Separation Methods

| Method | Gauge invariant? | Captures interference? | Complexity |
|---|---|---|---|
| `/ h` or `$$ h` (exclude Higgs) | Yes (Higgs is scalar singlet) | No — must subtract to get interference | 3 runs needed |
| Squared coupling orders (`NP` in `loop_sm_modif`) | Yes | Yes — each piece isolated | 1 run per piece |
| Full process (no filtering) | Yes | Yes — all included automatically | 1 run, no separation |

## The `bwcutoff` Parameter and On-Shell/Off-Shell Boundaries

The `bwcutoff` parameter in the run_card defines the boundary between "on-shell" and "off-shell" for s-channel resonances. It is central to how decay chains and the `$` operator behave.

### Definition and Default

| Property | Value |
|----------|-------|
| Location | `run_card.dat` |
| Default | `15` |
| Meaning | A resonance is on-shell if its invariant mass satisfies |m − M| < bwcutoff × Γ |

The on-shell window is **M ± bwcutoff × Γ**, where M is the pole mass and Γ is the total width of the particle.

### When `bwcutoff` Affects the Cross Section

`bwcutoff` does **not** affect the cross section of full (non-decay-chain) processes. For full processes like `p p > w+ w- b b~`, MadGraph integrates over all phase space — the `bwcutoff` value only controls which internal propagators are written with status code 2 (intermediate resonance) in the LHE event file.

`bwcutoff` **does** affect the cross section in exactly two cases:

| Syntax | How bwcutoff affects it |
|--------|------------------------|
| Decay chains: `p p > t t~, t > w+ b, t~ > w- b~` | Intermediate particles are **required** to be on-shell (within M ± bwcutoff × Γ). Smaller bwcutoff → narrower integration window → smaller cross section. |
| `$` operator: `p p > w+ w- b b~ $ t t~` | Intermediate particles are **forbidden** from being on-shell (within M ± bwcutoff × Γ). Smaller bwcutoff → narrower exclusion window → larger cross section. |

These two cases are **complementary**: decay chains integrate only inside the on-shell window, while `$` integrates only outside it.

### How `bwcutoff` Interacts with Each Operator

The `$`, `$$`, and `/` operators differ fundamentally in whether they use `bwcutoff` (see the **Summary Table** above for the full operator comparison):

- **`$` (forbid on-shell)**: Uses `bwcutoff`. Keeps all diagrams but applies a phase-space cut — events where the s-channel invariant mass falls inside M ± bwcutoff × Γ are rejected.
- **`$$` (remove s-channel diagrams)**: Does **not** use `bwcutoff`. Removes all diagrams containing the specified s-channel particle entirely.
- **`/` (remove particle everywhere)**: Does **not** use `bwcutoff`. Removes all diagrams containing the specified particle in any role.

### Practical Guidance

- For most analyses, the default `bwcutoff = 15` is appropriate. At 15 widths from the pole, the Breit-Wigner propagator suppression is approximately 1/900 relative to the peak, making the excluded tails negligible.
- Increasing `bwcutoff` in decay chains captures more off-shell tails but moves further from the narrow-width approximation where decay chains are valid.
- The `$` operator with `bwcutoff` provides an approximate separation of resonant vs non-resonant contributions, but this separation is gauge-dependent (see below).

**Details →** [Cards & Parameters](cards-and-parameters.md) for other run_card settings.

## Resonant vs Non-Resonant Separation Strategies

A common task is separating resonant contributions (e.g., on-shell top pair production) from non-resonant contributions (e.g., single-top or continuum W⁺W⁻bb̄). MadGraph offers several approaches, each with trade-offs.

### Approach 1: Decay Chain (Narrow-Width Approximation)

```
generate p p > t t~, t > w+ b, t~ > w- b~
```

- Includes **only** doubly-resonant diagrams (both t and t̄ on-shell).
- Valid in the narrow-width limit (Γ_t/m_t ≈ 0.8%). Corrections are O(Γ/M).
- `bwcutoff` controls how far off-shell the intermediate tops can be.
- Spin correlations between production and decay are preserved.
- Computationally efficient.

**Details →** [Decays & MadSpin](decays-and-madspin.md) for full decay chain syntax including nested decays and parenthesized final states.

### Approach 2: Full Matrix Element

```
generate p p > w+ w- b b~
```

- Includes **all** diagrams: doubly-resonant (tt̄), singly-resonant (single-top-like), non-resonant, and all interferences.
- Gauge invariant. This is the most complete LO calculation.
- `bwcutoff` does not affect the cross section (only the LHE event record).
- More expensive computationally.

### Approach 3: `$` Operator (Off-Shell Complement)

```
generate p p > w+ w- b b~ $ t t~
```

- Keeps all diagrams but **forbids** t and t̄ from being on-shell in the s-channel.
- The exclusion window is M ± bwcutoff × Γ — events where an s-channel top would be inside this window are rejected.
- This is the **approximate complement** of the decay chain: decay chain covers the on-shell region, `$` covers the off-shell region.

**Key points:**
- The `$` approach is only approximately gauge invariant. Diagrams with forced s-channel propagators are not gauge invariant far from the Breit-Wigner peak.
- You **cannot** simply add the decay-chain cross section and the `$`-filtered cross section to recover the full result, because interference between resonant and non-resonant diagrams is lost.
- For physics predictions, always use the full matrix element (Approach 2). Use Approaches 1 and 3 only for understanding the anatomy of contributions.

### Approach 4: `$$` Operator (Diagram Removal)

```
generate p p > w+ w- b b~ $$ t t~
```

- **Removes** all diagrams with s-channel t or t̄ entirely. No phase-space cut — the diagrams simply do not exist.
- The remaining diagrams may or may not be gauge invariant. Always verify with `check gauge`.
- Unlike `$`, this does not depend on `bwcutoff`.

### Approach 5: DR/DS Schemes at NLO (MadSTR Plugin)

At NLO, the overlap between processes like tt̄ production and tW single-top production becomes a formal problem: real-emission corrections to tW include doubly-resonant tt̄-like diagrams. Two schemes handle this:

| Scheme | Method | Description |
|--------|--------|-------------|
| **Diagram Removal (DR)** | Remove doubly-resonant diagrams | All real-emission diagrams containing two resonant top propagators are discarded. Simple but introduces a scheme dependence. |
| **Diagram Subtraction (DS)** | Subtract on-shell limit | The on-shell tt̄ contribution is subtracted locally in phase space, keeping all diagrams. More theoretically consistent but computationally involved. |

These schemes are implemented in the **MadSTR plugin** (arXiv:1907.04898). Install from GitHub (`https://github.com/mg5amcnlo/MadSTR`) by copying the inner `MadSTR/` directory into `<MG5_DIR>/PLUGIN/MadSTR`, then launch MadGraph with `--mode=MadSTR`.

> **Version compatibility:** MadSTR requires MG5_aMC@NLO v2.9.0 or later. It has been validated through v3.5.2 and declares support up to v3.6.x (as specified in `__init__.py`: `maximal_mg5amcnlo_version = (3,6,1000)`). For MG5 v3.7.0+, manual editing of the plugin's `__init__.py` (raising `maximal_mg5amcnlo_version`) or `os_wrapper_fks.inc` may be required — check the GitHub repository for updates.

The DR/DS difference provides a systematic uncertainty estimate for the overlap treatment.

### Summary: Choosing the Right Approach

| Goal | Recommended approach |
|------|---------------------|
| Full physics prediction at LO | `p p > w+ w- b b~` (full ME) |
| Efficient on-shell tt̄ generation | Decay chain: `p p > t t~, t > ...` |
| Understanding non-resonant size | Compare full ME to decay chain |
| NLO tt̄ with tW overlap handled | MadSTR plugin (DR/DS) |
| Isolating non-resonant contributions (approximate) | `$ t t~` with appropriate `bwcutoff` |
| Publication result | Full ME or NLO with MadSTR |

## Diagram Filter Plugin (`--diagram_filter`)

The `--diagram_filter` flag activates a user-defined Python function that selectively removes individual Feynman diagrams during process generation. This provides finer-grained control than the built-in `/`, `$`, `$$` operators or coupling-order constraints.

**Warnings:**
- This feature works at **leading order only**. It is not available for NLO processes.
- Removing diagrams can break **gauge invariance**. The MadGraph FAQ states: *"Be carefull about gauge invariance (a non gauge invariant subset will also break lorentz invariance)"* ([FAQ-General-15](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/FAQ-General-15)). The lead developer describes this mechanism as *"not a real plugin [but] a (extremelly dangerous) hack"* ([Launchpad Q&A #701855](https://answers.launchpad.net/mg5amcnlo/+question/701855)). Always validate filtered results with `check gauge` and `check lorentz`.
- The filter is applied to **all subprocesses**, including decay chains. See the "Decay Chains" subsection below.

### Setup

1. Create the file `PLUGIN/user_filter.py` in the MadGraph installation directory.
2. Define a function `remove_diag(diag, model)` that returns `True` to **discard** a diagram or `False` to **keep** it.
3. Append `--diagram_filter` to the `generate` or `add process` command.

```
generate p p > w+ w+ j j --diagram_filter
add process p p > w+ w- j j --diagram_filter
```

The `--diagram_filter` flag must appear **at the very end** of the complete process definition (after any decay chains, coupling-order constraints, and `@N` tags). Placing it within the process definition causes a *"No particle --diagram_filter in model"* error ([Launchpad Q&A #696554](https://answers.launchpad.net/mg5amcnlo/+question/696554)).

```
# CORRECT — flag at the very end after decay chains and tags:
generate p p > z w- j j QCD=99, z > l+ l-, w- > j j @0 --diagram_filter

# WRONG — flag placed before the decay chain:
generate p p > z w- j j --diagram_filter, z > l+ l-, w- > j j
```

MadGraph prints a warning showing how many diagrams were removed per subprocess:
```
WARNING: Diagram filter is ON and removed N diagrams for this subprocess.
```

### Decay Chains

When `--diagram_filter` is used with decay chains (comma syntax), the filter function is called for **every subprocess** — both the production process and each decay chain. For example, with `generate p p > z w- j j, z > l+ l-, w- > j j --diagram_filter`, the `remove_diag` function is called separately for the `p p > z w- j j` production, the `z > l+ l-` decay, and the `w- > j j` decay.

To apply different logic to production vs decay diagrams, inspect the diagram structure inside `remove_diag`. For instance, check the number of initial-state legs or use `len(draw.initial_vertex)` in the drawing API to distinguish production diagrams (2 initial-state particles) from decay diagrams (1 initial-state particle).

**Caution:** A filter that is too restrictive can remove ALL diagrams from a decay subprocess, causing a `NoDiagramException: No amplitudes generated` error.

### Diagram Data Structure (Legacy API)

The `diag` argument is a `Diagram` object containing a list of vertices. Each vertex represents a Feynman diagram vertex and has the following structure:

| Attribute | Type | Description |
|-----------|------|-------------|
| `diag['vertices']` | list | All vertices in the diagram |
| `vertex['id']` | int | Vertex interaction ID; **`0` = identity vertex** (always skip vertices with `id` in `[0, -1]`) |
| `vertex['legs']` | list | Particles (legs) attached to this vertex |
| `leg['id']` | int | PDG code of the particle (e.g., 21 = gluon, 24 = W⁺, 6 = top) |
| `leg['number']` | int | Leg number in the DAG |
| `leg['state']` | bool | `True` for s-channel / final-state propagators, **`False` for t-channel propagators** |
| `diag.get('orders')` | dict | Coupling orders for this diagram (e.g., `{'QCD': 2, 'QED': 2}`) |

**T-channel identification:** The authoritative way to identify t-channel propagators is `leg.get('state') == False`. Do **not** rely on `leg['number'] < 3` — while this heuristic appears in some MadGraph examples, it is inaccurate because s-channel propagators formed by combining both initial-state legs also get `number < 3`.

**Propagator convention:** In each vertex, `vertex['legs'][-1]` (the last leg) is the propagator connecting this vertex to the rest of the diagram.

### Diagram Data Structure (Drawing API)

For more complex filtering, convert the DAG to a full graph representation using the drawing module. The following code runs inside `PLUGIN/user_filter.py` within the MadGraph environment (not standalone):

```
# Inside PLUGIN/user_filter.py — requires the MadGraph environment
import madgraph.core.drawing as drawing

def remove_diag(diag, model):
    draw = drawing.FeynmanDiagram(diag, model)
    draw.load_diagram()
    draw.define_level()
    # Now use draw.vertexList, draw.lineList, draw.initial_vertex
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `draw.vertexList` | list | All vertices in the diagram |
| `draw.initial_vertex` | list | External particle vertices |
| `draw.lineList` | list | All particles: initial states, final states, and propagators |
| `vertex.lines` | list | `FeynmanLine` objects connected to this vertex |
| `vertex.level` | int | Hierarchy level (`0` = initial state) |
| `line.id` | int | PDG code |
| `line.begin` | vertex | Starting vertex of the line |
| `line.end` | vertex | Ending vertex of the line |
| `line.number` | int | Original DAG leg number |

### Examples

All examples below are meant to be placed in `PLUGIN/user_filter.py`. They define the `remove_diag` function that MadGraph calls during process generation.

#### Filter by Coupling Orders

```python
def remove_diag(diag, model):
    """Keep only diagrams with exactly QCD=2."""
    if diag.get('orders').get('QCD', 0) != 2:
        return True
    return False
```

#### Remove T-Channel Quarks (Legacy API)

```python
def remove_diag(diag, model=None):
    """Remove all diagrams with a quark in the t-channel."""
    for vertex in diag['vertices']:
        if vertex['id'] in [0, -1]:    # skip identity/sewing vertices
            continue
        propagator = vertex['legs'][-1]
        if not propagator.get('state'):   # t-channel propagator (state == False)
            if abs(propagator['id']) in [1,2,3,4,5]:  # quark PDG codes
                return True
    return False
```

#### Remove 4-Point Contact Interactions (Drawing API)

```
# Inside PLUGIN/user_filter.py — requires the MadGraph environment
import madgraph.core.drawing as drawing

def remove_diag(diag, model):
    """Remove diagrams containing 4-point vertices."""
    draw = drawing.FeynmanDiagram(diag, model)
    draw.load_diagram()
    for v in draw.vertexList:
        if len(v.lines) > 3:
            return True
    return False
```

#### Production-Only Filter (Skip Decay Chain Diagrams)

```
# Inside PLUGIN/user_filter.py — requires the MadGraph environment
import madgraph.core.drawing as drawing

def remove_diag(diag, model):
    """Apply filter only to production diagrams (2 initial-state particles).
    Decay chain diagrams (1 initial-state particle) are kept unconditionally."""
    draw = drawing.FeynmanDiagram(diag, model)
    draw.load_diagram()
    draw.define_level()
    if len(draw.initial_vertex) < 2:
        return False  # this is a decay subprocess — keep it
    # Apply your production filter logic here
    for v in draw.vertexList:
        if len(v.lines) > 3:
            return True
    return False
```

### When to Use the Diagram Filter vs Built-In Operators

| Goal | Best approach |
|------|---------------|
| Remove all diagrams with a specific s-channel particle | `$$` operator |
| Remove all diagrams with a specific particle anywhere | `/` operator |
| Forbid on-shell s-channel resonance only | `$` operator |
| Restrict to pure EW or pure QCD diagrams | Coupling-order constraints (e.g., `QCD=0`) |
| Filter by specific propagator type in specific channel | `--diagram_filter` |
| Remove specific vertex topologies (e.g., 4-point) | `--diagram_filter` |
| Filter based on diagram-level coupling-order combinations | `--diagram_filter` |

### Known Issues (Historical)

The following bugs have been fixed in past MadGraph releases. They are listed here for users on older versions.

- **Crossed diagrams not filtered ([Bug #1820040](https://bugs.launchpad.net/mg5amcnlo/+bug/1820040)):** In MadGraph v2.6.5 and earlier, diagrams reused via crossing symmetry bypassed the filter. Fixed in June 2019.
- **MadSpin crash with `--diagram_filter` ([Bug #1659128](https://bugs.launchpad.net/mg5amcnlo/+bug/1659128)):** MadSpin could crash with *"InvalidCmd: No particle ... in model"* when used on outputs produced with `--diagram_filter`. Fixed in March 2017. Additionally, the lead developer warns that *"a lot of extension (like MadSpin/…) will not work any longer"* when diagram filtering is used ([Q&A #626578](https://answers.launchpad.net/mg5amcnlo/+question/626578)). Test carefully before large production runs.
- **`ValueError: level must be >= 0` ([Q&A #695863](https://answers.launchpad.net/mg5amcnlo/+question/695863)):** Affected v2.8.2 due to a bug in the plugin import mechanism (`misc.py`). Fixed in v2.9.3 (revision 304).
