# 02 — Process Syntax

This document covers the core MadGraph5 commands for defining processes and preparing them for event generation.

## Contents

- [Importing a Model](#importing-a-model)
- [Generating a Process](#generating-a-process)
- [Adding Processes](#adding-processes)
- [Multiparticle Labels](#multiparticle-labels)
  - [Defining Custom Multiparticle Labels](#defining-custom-multiparticle-labels)
  - [Viewing Labels](#viewing-labels)
- [Coupling Orders](#coupling-orders)
- [Squared Coupling Order Syntax](#squared-coupling-order-syntax)
- [Intermediate-Particle Operators — Requiring and Excluding Propagators](#intermediate-particle-operators-requiring-and-excluding-propagators)
  - [The `>` Operator — Requiring an S-Channel Particle](#the-operator-requiring-an-s-channel-particle)
  - [The `$`, `$$`, `/` Operators — Forbidding Propagators](#the-operators-forbidding-propagators)
- [The `@N` Tags for Matching](#the-n-tags-for-matching)
- [NLO Syntax](#nlo-syntax)
- [Decay Chain Syntax](#decay-chain-syntax)
  - [On-shell decay (comma syntax)](#on-shell-decay-comma-syntax)
  - [Nested decay chains — parentheses required](#nested-decay-chains-parentheses-required)
  - [S-channel requirement (> syntax)](#s-channel-requirement-syntax)
- [Excluding Particles](#excluding-particles)
- [Output — Creating the Process Directory](#output-creating-the-process-directory)
- [Launch — Starting Event Generation](#launch-starting-event-generation)
- [Inspection Commands](#inspection-commands)
- [Polarized Boson Syntax](#polarized-boson-syntax)
  - [Polarization Labels](#polarization-labels)
  - [Reference Frame](#reference-frame)
  - [Use Cases](#use-cases)
  - [Limitation: External Particles Only](#limitation-external-particles-only)
- [The `check` Command](#the-check-command)
- [Identical Particles and Symmetry Factors](#identical-particles-and-symmetry-factors)
  - [How It Works](#how-it-works)
  - [Decay Chains with Identical Particles](#decay-chains-with-identical-particles)
  - [Identical Particles in Production and Decay](#identical-particles-in-production-and-decay)

## Importing a Model

Every MG5 session begins by loading a physics model:

```
import model sm
```

This loads the Standard Model UFO directory. Other models include `loop_sm` (SM with loop capabilities for NLO), `heft` (SM with effective ggH vertex), `MSSM_SLHA2`, etc. See [Models](models-and-restrictions.md) for details.

To reset the session and load a different model:

```
import model sm-no_b_mass
```

The part after `-` specifies a restriction file (here, `restrict_no_b_mass.dat`), which sets the b-quark mass to zero (5-flavor scheme).

## Generating a Process

The `generate` command defines the hard process:

```
generate p p > t t~
```

**Syntax**: `generate <initial_state> > <final_state> [options]`

- Particles are separated by spaces.
- `>` separates initial-state from final-state particles.
- Antiparticles use the `~` suffix: `t~`, `u~`, `b~`.
- Charge is indicated with `+`/`-`: `e+`, `e-`, `mu+`, `mu-`, `w+`, `w-`.

More examples:

```
generate e+ e- > mu+ mu-
generate g g > h                  # requires heft model
generate p p > w+ z
generate p p > e+ e- j            # Drell-Yan + 1 jet
```

## Adding Processes

Use `add process` to include additional subprocesses in the same generation:

```
generate p p > t t~
add process p p > t t~ j
```

All processes added this way share the same output directory and are combined during event generation.

**Important**: Diagrams within a single `generate` command interfere coherently (amplitudes are summed before squaring). Different `generate`/`add process` commands are summed **incoherently** (cross-sections are added). For example:

```
generate p p > e+ e-              # includes Z/gamma interference (correct)
```

is NOT the same as:

```
generate p p > z > e+ e-          # Z-only (no interference)
add process p p > a > e+ e-       # gamma-only (no interference)
```

The second form loses the Z/gamma interference term entirely, producing a wrong invariant mass distribution. Always include all interfering topologies in a single `generate` command.

## Multiparticle Labels

MadGraph provides predefined multiparticle labels that group several particles under one symbol:

| Label | Particles (default SM) | Notes |
|-------|----------------------|-------|
| `p` | `g u c d s u~ c~ d~ s~` | Proton content (4-flavor, no b) |
| `j` | `g u c d s u~ c~ d~ s~` | Same as `p` — jet particles |
| `l+` | `e+ mu+` | Charged anti-leptons |
| `l-` | `e- mu-` | Charged leptons |
| `vl` | `ve vm vt` | Neutrinos |
| `vl~` | `ve~ vm~ vt~` | Anti-neutrinos |
| `all` | all particles in the model | |

In the default SM (with massive b-quark), `p` and `j` exclude b quarks (4-flavor scheme). When using `sm-no_b_mass`, b quarks are added to `p` and `j` (5-flavor scheme). See [PDFs and Scales](pdfs-and-scales.md) for more on flavor schemes.

### Defining Custom Multiparticle Labels

```
define leptons = e+ e- mu+ mu-
define quarks = u c d s b u~ c~ d~ s~ b~
generate p p > leptons leptons
```

Custom labels simplify complex process definitions and can be used anywhere a particle name is accepted.

### Viewing Labels

```
display multiparticles
```

This shows all currently defined multiparticle labels, including the defaults.

> **Note on zero-diagram filtering:** When MadGraph expands multiparticle labels it tries all combinations, but automatically drops any combination that yields zero Feynman diagrams in the loaded model. For example, `generate p p > l+ l-` in the SM produces only same-flavor dilepton pairs (e+e-, μ+μ-) because lepton-flavor-violating combinations (e+μ-, μ+e-) have no SM diagrams and are silently excluded. You do not need separate `add process` lines to avoid mixed-flavor states.

## Coupling Orders

Beyond basic `QCD=N` and `QED=N`:

```
generate p p > e+ e- j QED=2 QCD<=1   # exact QED order, max QCD order
generate p p > h j j QCD=0              # pure EW (VBF)
generate p p > h j j QCD=0 QED=4        # explicit both orders
```

For VBF Higgs isolation:

```
# EW only (includes VBF + VH with hadronic V decay)
generate p p > h j j QCD=0

# Pure VBF only (exclude VH)
generate p p > h j j $$ w+ w- z / a QCD=0
```

Note: `heft` model should NOT be used for VBF since it only provides the ggH effective vertex, not the VBF vertex.

## Squared Coupling Order Syntax

The `^2` suffix applies coupling constraints at the squared-amplitude level (|M|²) rather than the amplitude level. This enables selection of specific interference patterns:

```
generate p p > j j QED^2==2 QCD^2==2    # QED-QCD interference terms only
```

Supported operators are `==`, `<=`, and `>`:

```
generate p p > e+ e- j j QED^2==4 QCD^2==0    # pure EW squared terms
generate p p > e+ e- j j QED^2==2 QCD^2==2    # QCD-EW interference
generate p p > e+ e- j j QCD^2<=4              # all terms up to QCD^2=4
```

Without `^2`, coupling orders constrain amplitudes: `QCD=2` means amplitudes have at most 2 QCD vertices (2 powers of $g_s$). With `^2`, the constraint applies to the squared matrix element and counts powers of $g_s$ (NOT $\alpha_s$): `QCD^2==4` selects terms with 4 powers of $g_s$ in |M|² (= 2 powers of $\alpha_s$), e.g., from the product of an amplitude with QCD=2 and its conjugate with QCD=2, giving 2+2=4 $g_s$ powers total.

A negative value `COUP^2==-I` refers to the N^(-I+1)LO term in the expansion of that coupling order, which is useful for isolating specific perturbative contributions.

This syntax is essential for VBS (vector boson scattering) studies where QCD-EW interference terms must be isolated or excluded.

## Intermediate-Particle Operators — Requiring and Excluding Propagators

MadGraph provides four operators that control which intermediate particles (propagators) appear in Feynman diagrams. They are placed on the `generate` line after the final-state particles (for `$`, `$$`, `/`) or inline between `>` signs (for the s-channel require operator).

| Operator | Syntax | Effect | Channels affected |
|----------|--------|--------|-------------------|
| `>` (s-channel require) | `p p > z > e+ e-` | **Requires** the particle in the s-channel | s-channel only |
| `$` (soft s-channel forbid) | `p p > e+ e- $ z` | **Forbids on-shell** s-channel propagation; keeps off-shell tails | s-channel only |
| `$$` (hard s-channel forbid) | `p p > e+ e- $$ z` | **Removes all** s-channel diagrams with the particle (on-shell and off-shell) | s-channel only |
| `/` (full forbid) | `p p > e+ e- / h` | **Removes** the particle from all propagators | s-channel + t-channel |

### The `>` Operator — Requiring an S-Channel Particle

Placing a particle between two `>` signs requires it as an s-channel propagator:

```
generate p p > z > e+ e-
```

This selects only diagrams where the `e+ e-` pair is produced through an s-channel Z boson. The Z is **not** forced on-shell — off-shell (virtual) contributions are fully included. This is distinct from the decay-chain comma syntax, which forces the intermediate particle on-shell within a Breit-Wigner window.

**Key differences from decay-chain syntax**:

| Feature | S-channel require (`>`) | On-shell decay (`,`) |
|---------|------------------------|----------------------|
| Syntax | `p p > z > e+ e-` | `p p > z, z > e+ e-` |
| Off-shell contributions | Included (full propagator) | Excluded (Breit-Wigner window) |
| Cross-section | Full s-channel amplitude | Narrow-width approximation |
| Interference with non-resonant diagrams | **Not** included (only selected-particle diagrams) | **Not** included |
| Use case | Isolate s-channel topology, keep off-shell tails | Decay heavy on-shell resonances |

Because `>` excludes non-resonant diagrams, `p p > z > e+ e-` and `p p > e+ e-` give **different** results. The latter includes both Z and $\gamma$ exchange plus their interference. Use `>` only when you specifically want to isolate the s-channel resonance topology.

**Common applications**:

```
# Z-only Drell-Yan (no photon, no interference)
generate p p > z > e+ e-

# W-mediated single top (t-channel W excluded)
generate p p > w+ > t b~

# Isolate s-channel Z in e+e- collisions
generate e+ e- > z > mu+ mu-
```

**Details ->** [Decays & MadSpin](decays-and-madspin.md) for the full comparison between `>` and `,` syntax, and guidance on when to use each.

### The `$`, `$$`, `/` Operators — Forbidding Propagators

These three operators forbid particles from appearing as propagators. They differ in how aggressively they remove contributions:

- **`$ X`** — forbids X from going on-shell in the s-channel. Off-shell s-channel tails are kept. Useful for studying non-resonant backgrounds or interference effects away from a resonance pole.
- **`$$ X`** — removes all diagrams with X in the s-channel (on-shell and off-shell). More aggressive than `$`. T-channel diagrams with X are kept.
- **`/ X`** — removes X from both s-channel and t-channel propagators. The most restrictive operator.

List multiple particles after any operator, separated by spaces:

```
# VBF Higgs: no s-channel EW bosons, no photon exchange, pure EW
generate p p > h j j $$ w+ w- z / a QCD=0

# ttbar without Higgs or Z exchange anywhere
generate p p > t t~ / h z
```

**Gauge invariance warning**: Filtering diagrams with `$`, `$$`, `/`, or selecting subsets with `>` can break gauge invariance. Always verify with `check gauge <process>`.

**Details ->** [Diagram Filtering](diagram-filtering.md) for the full summary table, gauge invariance discussion, and examples of Z/γ separation.

By default, MadGraph minimizes the QED coupling order (QED has weight 2, QCD has weight 1 in the ordering algorithm).

You can explicitly constrain coupling orders on the `generate` line:

```
generate p p > e+ e- j QED=2 QCD<=1
```

- `QCD=N` means `QCD<=N` (maximum QCD coupling order is N).
- `QED=N` means `QED<=N` (maximum QED coupling order is N).
- The `==` operator requests exactly N: `QCD==2`.

**Warning**: When only one coupling order is specified, the other defaults to the model maximum (effectively infinity). For example, `QED=6` allows any QCD order — to isolate pure EW diagrams, constrain **both**:

```
generate p p > e+ e- j j QCD=0 QED=4     # pure EW only
```

This is important for isolating specific topologies. For example, to select only electroweak diagrams for VBF Higgs production:

```
generate p p > h j j QCD=0
```

See [Coupling Orders & Validation](coupling-orders-and-validation.md) for how automatic ordering works and its pitfalls.

## The `@N` Tags for Matching

When setting up MLM matching with multiple jet multiplicities, use `@N` tags to label each multiplicity:

```
generate p p > t t~ @0
add process p p > t t~ j @1
add process p p > t t~ j j @2
```

The `@N` tag tells MadGraph which jet multiplicity each subprocess belongs to, which is essential for the matching algorithm. See [Matching & Merging](matching-and-merging.md) for full details.

## NLO Syntax

For next-to-leading order computations, use square brackets:

```
generate p p > t t~ [QCD]
```

This requires a loop-capable model (`import model loop_sm`). The `[QCD]` indicates NLO QCD corrections. Other options:

```
generate p p > t t~ [QCD]           # full NLO QCD
generate p p > t t~ [virt=QCD]      # virtual corrections only
generate g g > z z [noborn=QCD]     # loop-induced (no Born amplitude)
```

**Note**: The comma-based decay chain syntax cannot be combined with the `[ ]` NLO syntax (e.g., `p p > t t~, t > w+ b [QCD]` will raise an error). For NLO production with decays, use the `>` s-channel syntax (e.g., `p p > t t~ > w+ b w- b~ [QCD]`) or MadSpin.

See [NLO Computations](nlo-computations.md) for details.

## Decay Chain Syntax

There are two ways to specify decays, with different physics implications:

### On-shell decay (comma syntax)
```
generate p p > t t~, t > w+ b, t~ > w- b~
```

The comma forces the intermediate particle to be **on-shell** within a Breit-Wigner window controlled by the `bwcutoff` parameter (default: 15 widths). Final-state cuts on decay products are disabled by default (`cut_decays = F` in the run_card).

### Nested decay chains — parentheses required

For multi-level cascades where decay products themselves decay, **parentheses are mandatory** to group each cascade branch:

```
generate p p > t t~, (t > w+ b, w+ > j j), (t~ > w- b~, w- > l- vl~)
```

Without parentheses, MadGraph cannot associate sub-decays (e.g. `w+ > j j`) with their parent decay chain. It silently discards them with a warning:

> *"Decay without corresponding particle in core process found... This warning usually means that you forgot parentheses in presence of subdecay"*

The result is fewer diagrams and incorrect physics — only the top-level decays (`t > w+ b`) are applied, while the W sub-decays are dropped entirely. This can produce orders-of-magnitude errors in cross-sections.

**Rule of thumb**: flat comma syntax (no parentheses) works only for single-level decays. As soon as a decay product itself decays, wrap the entire branch in parentheses.

### S-channel requirement (> syntax)
```
generate p p > w+ > e+ ve
```

The `>` through an intermediate particle requires it in the s-channel but does **not** force it on-shell — off-shell contributions are included.

These give **different cross-sections**. See [Decays & MadSpin](decays-and-madspin.md) for when to use each.

## Excluding Particles

Three operators control which particles appear as internal propagators:

```
generate p p > e+ e- / h          # exclude Higgs from ALL propagators (s+t channel)
generate p p > e+ e- $$ z         # remove all Z s-channel diagrams
generate p p > e+ e- $ z          # forbid on-shell Z in s-channel (keep off-shell)
```

- `/` removes the particle from both s-channel and t-channel propagators.
- `$$` removes all diagrams with the particle in the s-channel (both on-shell and off-shell contributions gone).
- `$` forbids the particle from going on-shell in the s-channel (off-shell contributions kept).

See [Diagram Filtering](diagram-filtering.md) for important caveats about gauge invariance when filtering diagrams.

## Output — Creating the Process Directory

After defining processes, create the process directory:

```
output my_process
```

This generates all Fortran code, creates the directory structure, and writes default configuration cards to `my_process/Cards/`. The directory name must not contain spaces.

If no name is given, MG5 uses a default name like `PROC_sm_0`.

## Launch — Starting Event Generation

After `output`, start the run:

```
launch my_process
```

Or simply `launch` to use the most recently created process directory. In a script, you must handle the launch dialogue — see [Scripted Execution](scripted-execution.md).

You can also launch an existing directory from a previous session:

```
launch my_process
```

Each launch creates a new run subdirectory (`run_01`, `run_02`, ...) under `my_process/Events/`.

To give a run a custom name:

```
launch my_process -n my_run_name
```

## Inspection Commands

After defining a process (before or after `output`):

```
display diagrams          # show Feynman diagrams (PostScript/browser)
display processes          # list all contributing subprocesses
display particles          # list all particles in the model
display interactions        # list all interaction vertices
display multiparticles      # list all multiparticle labels
display parameters          # list model parameters
display modellist           # list all available models
```

## Polarized Boson Syntax

Since MG5 v2.7.0, you can generate specific polarization states using curly braces:

```
generate e+ e- > w+{0} w-{T}          # longitudinal W+, transverse W-
generate p p > t{L} t~{R}             # left-handed top, right-handed antitop
generate p p > w+{0} w-{T}, w+ > e+ ve   # with decay chain
```

### Polarization Labels

| Label | Meaning | Applies to |
|-------|---------|------------|
| `{0}` | Longitudinal | Massive vector bosons (W, Z) |
| `{T}` | Transverse (sum of +/- helicities) | Massive vector bosons |
| `{L}` | Left-handed helicity | Fermions |
| `{R}` | Right-handed helicity | Fermions |

### Reference Frame

The polarization is defined in a reference frame controlled by the `me_frame` parameter in the run_card. The default is the partonic center-of-mass frame.

### Use Cases

- Studying the Goldstone boson equivalence theorem (longitudinal W/Z scattering)
- Measuring polarization fractions in top quark decays
- Testing anomalous couplings through polarization-dependent observables

### Limitation: External Particles Only

Polarization syntax applies to **external** (initial-state or final-state) particles only. It **cannot** restrict the polarization of intermediate particles in decay chains. The matrix element sums over all polarization states of the intermediate particle, and the physical polarization information is encoded in the angular distributions of the decay products.

```
generate e+ e- > w+{0} w-{T}              # OK: W+, W- are external final-state particles
generate p p > t{L} t~{R}                 # OK: t, t~ are external final-state particles
```

To study the polarization of an unstable particle, generate it as a **polarized final-state particle** and then decay it separately with MadSpin. For example, to study longitudinal W+ bosons from top decay:

```
# Step 1: Generate tops as external particles
generate p p > t t~
# Step 2: Use MadSpin to decay (spin correlations preserved, all W polarizations included)
# Step 3: Analyze angular distributions of W decay products to extract polarization fractions
```

MadSpin preserves the full spin correlation between production and decay, so the physical polarization information is encoded in the angular distributions of decay products — it does not need to be restricted at generation level.

## The `check` Command

Numerically verify that a process is correct:

```
check gauge p p > t t~         # verify gauge invariance (unitary vs Feynman gauge)
check lorentz p p > t t~       # verify Lorentz invariance
check permutation p p > t t~   # verify permutation symmetry
check full p p > t t~          # run all checks
```

This is especially important for BSM models or when using diagram filtering operators (`/`, `$`, `$$`), which can break gauge invariance if misused.

## Identical Particles and Symmetry Factors

When identical particles appear in the final state (e.g., `p p > z z`, `p p > j j j`), MadGraph automatically handles the combinatorial symmetry factors. During matrix element generation, MG5 identifies amplitudes that produce the same final-state configuration and combines them into a single matrix element with the appropriate symmetry factor. This avoids double-counting identical permutations.

### How It Works

MG5 uses `IdentifyMETag` to group amplitudes that differ only in the ordering of identical final-state particles. These amplitudes share the same squared matrix element and are combined during `generate_matrix_elements`, with a symmetry factor that accounts for the number of equivalent permutations.

For example, `p p > z z` has a symmetry factor of 1/2! = 1/2 because the two Z bosons are identical. The user does not need to apply any manual correction.

### Decay Chains with Identical Particles

A decay specification applies to **all** instances of the matching particle type in the final state. When the final state contains multiple identical particles and a decay is specified for that particle type, every instance is decayed. There is no mechanism to selectively decay only a subset of identical particles. See [Decays & MadSpin](decays-and-madspin.md) for full decay chain documentation.

### Identical Particles in Production and Decay

When using the reweight module (e.g., for parameter scans or PDF variations), identical particles that appear in both the production process and decay products require special treatment. The `identical_particle_in_prod_and_decay` option in the reweight interface controls this:

```
# In the reweight card or interface:
set identical_particle_in_prod_and_decay average   # default: average over assignments
set identical_particle_in_prod_and_decay max       # take the assignment with max weight
set identical_particle_in_prod_and_decay crash      # abort if ambiguity detected
```

This is relevant when, for instance, a process produces a b-quark in production and the decay also produces a b-quark, making it ambiguous which b-quark in the event corresponds to which role. The `average` option (default) averages over all possible assignments; `max` selects the highest-weight assignment.
