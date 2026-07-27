# Coupling Orders and Process Validation

This document covers automatic coupling order determination in MadGraph5 and the `check` command for validating process definitions.

## Contents

- [Process Validation: The `check` Command](#process-validation-the-check-command)
  - [Syntax](#syntax)
  - [Check Types](#check-types)
  - [Basic Examples](#basic-examples)
  - [How Each Check Works](#how-each-check-works)
  - [Pass/Fail Threshold Summary](#passfail-threshold-summary)
  - [Common Failure Causes and Remediation](#common-failure-causes-and-remediation)
- [Automatic Coupling Order](#automatic-coupling-order)
  - [Example: `p p > w+ b b~ j j`](#example-p-p--w-b-b-j-j)
  - [When Automatic Ordering Fails](#when-automatic-ordering-fails)
  - [When Automatic Ordering Drops Diagrams vs. Keeps All](#when-automatic-ordering-drops-diagrams-vs-keeps-all)
  - [When does WEIGHTED drop diagrams?](#when-does-weighted-drop-diagrams)
  - [Worked Example 1: Purely electroweak final state — no diagrams dropped](#worked-example-1-purely-electroweak-final-state--no-diagrams-dropped)
  - [Worked Example 2: Mixed QCD/EW final state — diagrams are dropped](#worked-example-2-mixed-qcdew-final-state--diagrams-are-dropped)
  - [Diagnostic checklist](#diagnostic-checklist)
  - [Common misconceptions](#common-misconceptions)

## Process Validation: The `check` Command

The `check` command validates process definitions and model implementations by testing fundamental physics properties (gauge invariance, Lorentz invariance, crossing symmetry). It is essential for validating custom UFO models from FeynRules and for verifying that diagram filtering preserves gauge invariance.

### Syntax

```
check <type> <process_definition> [options]
```

where `<type>` is one of the types listed below, and `<process_definition>` follows standard MG5 syntax (including `/`, `$`, `$$` filtering and coupling-order constraints).

### Check Types

| Type | What It Tests | Tree-level | Loop |
|------|--------------|------------|------|
| `full` | Runs **all four** checks: permutation, gauge, brs, lorentz | Yes | Yes |
| `gauge` | Compares |M|² in **unitary gauge** vs **Feynman gauge** | Yes | Yes (QCD-only NLO) |
| `brs` | Tests **Ward identities** by replacing ε_μ → p_μ for a massless gauge boson | Yes | Yes |
| `lorentz` | Compares |M|² across **four reference frames** (lab + 3 boosts) | Yes | Yes |
| `permutation` | Generates all particle orderings and compares matrix elements | Yes | Yes |
| `cms` | Validates **complex mass scheme** NLO implementation by scaling widths with λ | — | NLO only |
| `timing` | Benchmarks code execution time | — | Loop only |
| `stability` | Returns numerical stability statistics | — | Loop only |
| `profile` | Combined timing + stability (non-interactive) | — | Loop only |

**Important:** The only valid check type keywords are exactly those listed above. In particular, `lorentz_invariance` is **not** a valid alias for `lorentz` — using it causes MG5 to silently misparse the command (treating the unknown word as part of the process definition).

### Basic Examples

```
import model sm
# Run all tree-level checks on a process
check full p p > t t~

# Gauge invariance only
check gauge p p > e+ e-

# Lorentz invariance only
check lorentz p p > w+ w- h

# Ward identity (BRS) check — requires photon or gluon
check brs g g > t t~

# Permutation check
check permutation p p > e+ e- j

# Verify gauge invariance of a filtered process
check gauge p p > e+ e- $$ a
```

### How Each Check Works

#### Gauge Check

Computes |M|² at a random phase-space point in both **unitary gauge** and **Feynman gauge**. All particle widths are **automatically set to zero** during this check (finite widths break gauge invariance unless the complex mass scheme is used).

**Output columns:**

| Column | Meaning |
|--------|---------|
| Process | The process tested |
| Unitary | |M|² computed in unitary gauge |
| Feynman | |M|² computed in Feynman gauge |
| Relative diff | \|ME_F − ME_U\| / max(ME_F, ME_U) |
| Result | Passed / Failed |

Additional **JAMP** rows show individual color-flow amplitude contributions. Each JAMP should independently satisfy gauge invariance.

**Pass threshold:** Relative difference < 10⁻⁸ (same threshold for both tree-level and loop processes).

#### BRS (Ward Identity) Check

For one external massless gauge boson (photon or gluon), replaces the polarization vector ε_μ with the boson's 4-momentum p_μ. By the Ward identity, the resulting amplitude should vanish.

**Output columns:**

| Column | Meaning |
|--------|---------|
| Process | The process tested |
| Matrix | Standard |M|² value |
| BRS | |M|² with ε_μ → p_μ substitution |
| Ratio | BRS / Matrix |
| Result | Passed / Failed |

**Pass thresholds:**

| Process type | Threshold |
|---|---|
| Tree-level | Ratio < 10⁻¹⁰ |
| Loop | Ratio < 10⁻⁵ |

**Note:** If the process has no external massless gauge bosons (no photon or gluon), the BRS check prints `No ward identity` and skips — this is not a failure.

#### Lorentz Invariance Check

Computes |M|² (summed over helicities) in four reference frames: the lab frame and three Lorentz-boosted frames (boost β ≈ 0.5 along x, y, z axes). A Lorentz-invariant matrix element must give identical results in all frames.

**Output columns:**

| Column | Meaning |
|--------|---------|
| Process | The process tested |
| Min element | Smallest |M|² across the 4 frames |
| Max element | Largest |M|² across the 4 frames |
| Relative diff | (max − min) / max |
| Result | Passed / Failed |

**Pass thresholds:**

| Process type | Threshold |
|---|---|
| Tree-level | < 10⁻¹⁰ |
| Loop (rotations) | < 10⁻⁶ |
| Loop (boosts) | < 10⁻³ |

For loop processes, the Lorentz check uses **two separate thresholds**: a tighter threshold (10⁻⁶) for rotations and a more relaxed threshold (10⁻³) for boosts, because numerical loop integration introduces larger errors under Lorentz boosts than under rotations.

#### Permutation Check

Generates the process with all possible orderings of final-state particles (different diagram-building and HELAS call sequences) and compares the resulting matrix elements at the same phase-space point.

**Output columns:**

| Column | Meaning |
|--------|---------|
| Process | The process tested |
| Min element | Smallest |M|² across all orderings |
| Max element | Largest |M|² across all orderings |
| Relative diff | 2 × \|max − min\| / (\|max\| + \|min\|) |
| Result | Passed / Failed |

Note: the permutation check uses the **symmetrized relative difference** formula `2 × |max − min| / (|max| + |min|)`, not the simple `(max − min) / max` used by other checks.

**Pass thresholds:**

| Process type | Threshold |
|---|---|
| Tree-level | < 10⁻⁸ |
| Loop | < 10⁻⁵ |

#### CMS (Complex Mass Scheme) Check

Validates the NLO complex mass scheme implementation. Scales all widths by a parameter λ and checks that the difference between CMS and fixed-width results vanishes as λ → 0 with the expected power-law behavior.

```
check cms u d~ > e+ ve [virt=QCD]
check cms u d~ > e+ ve a [virt=QCD QED] --lambdaCMS=(1.0e-6,5)
```

Key options:

| Option | Default | Description |
|--------|---------|-------------|
| `--lambdaCMS=(min,N)` | `(1.0e-6,5)` | Tuple: minimum λ and points per decade (logarithmic spacing) |
| `--lambdaCMS=[list]` | — | Explicit list of λ values (must include 1.0); spaces must be escaped |
| `--offshellness=X` | `10.0` | Minimum off-shellness: resonance must satisfy p² > (X+1)M²; must be > −1 |
| `--cms=<orders>,<rules>` | auto | Coupling orders and parameter scaling rules (see below) |
| `--name=<name>` | auto | Base name for output/pickle files |
| `--seed=N` | `666` | Seed for kinematic configuration |
| `--tweak=<spec>` | — | Modify computational setup (e.g., `alltweaks` for comprehensive test) |
| `--analyze=f1.pkl,...` | — | Re-analyze previously generated results without recomputation |

The `--cms` option has two comma-separated parts: (1) coupling orders joined by `&` (e.g., `QED&QCD`), and (2) parameter scaling rules (e.g., `aewm1->10.0/lambdaCMS&as->0.1*lambdaCMS`).

The CMS check produces plots showing Δ vs λ (upper panel) and Δ/λ vs λ (lower panel). A successful check shows the Δ/λ curve flattening to a constant at small λ, confirming that the CMS–fixed-width difference vanishes at the expected rate.

### Pass/Fail Threshold Summary

| Check | Formula | Tree threshold | Loop threshold |
|-------|---------|---------------|----------------|
| Gauge | \|ME_F − ME_U\| / max(ME_F, ME_U) | < 10⁻⁸ | < 10⁻⁸ |
| BRS | BRS / Matrix | < 10⁻¹⁰ | < 10⁻⁵ |
| Lorentz | (max − min) / max | < 10⁻¹⁰ | Rotations: < 10⁻⁶, Boosts: < 10⁻³ |
| Permutation | 2\|max − min\| / (\|max\| + \|min\|) | < 10⁻⁸ | < 10⁻⁵ |
| CMS | Visual (Δ/λ → constant) | — | NLO only |

### Common Failure Causes and Remediation

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Gauge check fails | Diagram filtering broke gauge invariance | Remove or adjust `$`/`$$`/`/` filtering |
| Gauge check fails (custom model) | Incorrect UFO model (wrong vertices, missing diagrams) | Re-export from FeynRules; check vertex definitions |
| BRS prints `No ward identity` | No external photon or gluon in process | Not a failure — BRS only applies when massless gauge bosons are external |
| Lorentz check fails | Missing Feynman diagrams or incorrect model implementation | Check diagram filtering; re-validate UFO model |

## Automatic Coupling Order

When you don't specify coupling orders, MG5 automatically determines them by assigning weights to each coupling type:

- QCD coupling: weight 1
- QED coupling: weight 2

MG5 computes the total weight for each diagram and selects diagrams with the **lowest total weight** that gives a non-zero contribution. This means it minimizes the QED order.

### Example: `p p > w+ b b~ j j`

Without explicit orders, MG5 selects diagrams that minimize QED couplings. This may suppress relevant signal diagrams (e.g., diagrams with intermediate top quarks) in favor of pure QCD diagrams.

**Fix**: Explicitly specify coupling orders:

```
generate p p > w+ b b~ j j QCD=4 QED=1
```

### When Automatic Ordering Fails

The automatic ordering can give unexpected results when:
- Signal and background have different coupling structures
- You want specific topologies (e.g., VBF vs gluon fusion)
- Mixed QCD/EW processes where both contribute at similar orders

**Rule of thumb**: For simple processes (pure QCD or pure EW), automatic ordering works fine. For mixed processes, always specify coupling orders explicitly.

### When Automatic Ordering Drops Diagrams vs. Keeps All

### When does WEIGHTED drop diagrams?

WEIGHTED only drops diagrams when a process has **multiple coupling-order combinations** that produce valid topologies. If all diagrams share the same coupling orders, WEIGHTED keeps everything.

**Key rule**: Count the minimum number of QCD and QED vertices required by the final state. If the final state forces a unique coupling-order split, WEIGHTED is a no-op.

### Worked Example 1: Purely electroweak final state — no diagrams dropped

```
generate p p > mu+ mu- a
```

The final state (two charged leptons + photon) couples only via QED. Every tree-level diagram has exactly **QED=3, QCD=0** (WEIGHTED = 6). There is only one coupling-order combination, so WEIGHTED keeps all 32 diagrams:

```
generate p p > mu+ mu- a              # 32 diagrams, WEIGHTED<=6
generate p p > mu+ mu- a QED<=3       # 32 diagrams (identical)
generate p p > mu+ mu- a QED=99       # 32 diagrams (identical)
```

**How to recognize this case**: If every final-state particle couples only electromagnetically (leptons, photons) and the initial state is `p p`, then all diagrams share the same coupling orders and WEIGHTED changes nothing.

| Process | Coupling orders | Why uniform |
|---------|----------------|-------------|
| `p p > e+ e-` | QED=2, QCD=0 | Drell-Yan, purely EW final state |
| `p p > mu+ mu- a` | QED=3, QCD=0 | Leptons + photon, all EW |
| `e+ e- > mu+ mu-` | QED=2, QCD=0 | Leptonic initial and final state |

### Worked Example 2: Mixed QCD/EW final state — diagrams are dropped

```
generate p p > t t~
```

Top-quark pairs can be produced via **QCD** (g g → t t~ and q q~ → g → t t~, with QCD=2, WEIGHTED=2) and via **EW** (q q~ → Z/γ → t t~, with QED=2, WEIGHTED=4). The default `WEIGHTED<=2` keeps only the QCD diagrams (7 diagrams). With `WEIGHTED<=99`, all 15 diagrams are included. The 8 additional diagrams are the EW topologies.

To include EW contributions:

```
generate p p > t t~ QED=2 QCD=2    # include both QCD and EW diagrams
generate p p > t t~ WEIGHTED<=99    # equivalent: raise the WEIGHTED ceiling
```

| Process | Default WEIGHTED | What is dropped | Fix |
|---------|-----------------|-----------------|-----|
| `p p > t t~` | `<=2` (7 diag.) | EW diagrams q q~ → Z/γ → t t~ (8 diag.) | `WEIGHTED<=99` or `QED=2 QCD=2` |
| `p p > w+ b b~ j j` | Minimal | EW topologies (single-top, ttbar-mediated) | Increase `WEIGHTED` or set explicit orders |
| `p p > e+ e- j j` | Minimal | Subleading EW contributions | Set both `QCD` and `QED` explicitly |

### Diagnostic checklist

1. **Run with default orders** and note the diagram count and `WEIGHTED<=N` value in the output.
2. **Run with `WEIGHTED<=99`** (or `QED=99 QCD=99`) and compare diagram counts.
3. If the counts differ, WEIGHTED dropped diagrams. Decide whether the dropped diagrams matter for your physics.
4. Use `display processes` to inspect which subprocesses and coupling-order combinations are included.

### Common misconceptions

- **"I must always specify coupling orders to be safe."** — No. For processes where only one coupling-order combination exists (purely EW final states), the default is already complete.
- **"Specifying `QED=99` always adds more diagrams."** — No. It only adds diagrams if there are valid higher-QED topologies that WEIGHTED excluded. For `p p > mu+ mu- a`, `QED=99` gives the same 32 diagrams as the default.
- **"WEIGHTED drops diagrams for any process with photons."** — No. A photon in the final state does not automatically mean diagrams are dropped. What matters is whether the process admits multiple coupling-order splits.
- **"Pure QCD processes like `p p > t t~` are unaffected by WEIGHTED."** — No. While `p p > t t~` is predominantly QCD, the EW production diagrams (q q~ → Z/γ → t t~) exist at a higher WEIGHTED value and are dropped by default.
