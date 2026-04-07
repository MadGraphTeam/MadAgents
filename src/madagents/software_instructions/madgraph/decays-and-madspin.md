# 08 — Decays & MadSpin

MadGraph provides two approaches for handling particle decays: inline decay chain syntax in the `generate` command, and the external MadSpin tool. Both preserve spin correlations, but differ in flexibility, performance, and applicability.

## Contents

- [Decay Chain Syntax in `generate`](#decay-chain-syntax-in-generate)
  - [On-Shell Decay (Comma Syntax)](#on-shell-decay-comma-syntax)
  - [S-Channel Requirement (> Syntax)](#s-channel-requirement-syntax)
  - [Important: These Give Different Results](#important-these-give-different-results)
  - [Decay Specifications Apply to All Matching Particles](#decay-specifications-apply-to-all-matching-particles)
- [Why Production × BR Doesn't Match](#why-production-br-doesnt-match)
- [MadSpin](#madspin)
  - [Advantages of MadSpin](#advantages-of-madspin)
  - [MadSpin in Scripts](#madspin-in-scripts)
  - [Syntax Comparison: madspin_card vs Other Cards](#syntax-comparison-madspin_card-vs-other-cards)
  - [MadSpin Card Configuration](#madspin-card-configuration)
  - [Cascade Decays with Parentheses](#cascade-decays-with-parentheses)
  - [Common MadSpin Issues](#common-madspin-issues)
- [Multiparticle Labels in Decay Chains](#multiparticle-labels-in-decay-chains)
- [Production vs Decay Radiation](#production-vs-decay-radiation)
- [Choosing Between Generate-Level Decays and MadSpin](#choosing-between-generate-level-decays-and-madspin)
- [MadWidth (compute_widths)](#madwidth-compute_widths)
  - [The `compute_widths` Command](#the-compute_widths-command)
  - [Reading the Output](#reading-the-output)
  - [Why Consistent Widths Matter](#why-consistent-widths-matter)
  - [Fixing BR > 1 Errors](#fixing-br-1-errors)
  - [Model-Dependent Limitations: Loop-Induced Channels](#model-dependent-limitations-loop-induced-channels)
  - [BSM Models](#bsm-models)
  - [Auto-Width](#auto-width)
- [Decision Table: Which Decay Method to Use](#decision-table-which-decay-method-to-use)
- [Resonant Diagram Approximation](#resonant-diagram-approximation)
- [The `bwcutoff` Parameter](#the-bwcutoff-parameter)
- [The `cut_decays` Parameter](#the-cut_decays-parameter)

## Decay Chain Syntax in `generate`

### On-Shell Decay (Comma Syntax)

```
generate p p > t t~, t > w+ b, t~ > w- b~
```

The **comma** (`,`) forces the intermediate particle to be **on-shell** within a Breit-Wigner window. The comma separates production from decay, and the intermediate particle is required to have an invariant mass within:

```
M - bwcutoff × Γ  <  m_inv  <  M + bwcutoff × Γ
```

where `bwcutoff` (default 15) is set in the run_card.

Key properties:
- The intermediate particle appears in the LHE output.
- Final-state cuts on decay products are **disabled by default** (`cut_decays = F` in the run_card).
- The cross-section is computed via phase-space integration within the `bwcutoff` window (not the factorized σ × BR formula). It approximately equals σ(production) × BR(decay) when Γ/M is small, but MadGraph does not use this factorization internally.

### S-Channel Requirement (> Syntax)

```
generate p p > w+ > e+ ve
```

The `>` through an intermediate particle requires it in the **s-channel** but does **not** force it on-shell. Off-shell contributions are included. This gives a different (generally larger) cross-section than the comma syntax.

### Important: These Give Different Results

For the same physics, comma and `>` syntax produce different cross-sections:

```
generate p p > w+, w+ > e+ ve      # on-shell W+ (only resonant diagrams)
generate p p > w+ > e+ ve           # s-channel W+ required, off-shell included
generate p p > e+ ve                 # all diagrams, no W+ requirement
```

Each has a different cross-section. The choice depends on the physics question.

### Decay Specifications Apply to All Matching Particles

A decay specification applies to **every** particle of that type in the final state. If the final state contains multiple instances of the same particle, a single decay specification is sufficient to decay all of them. There is no syntax to decay only a subset of identical final-state particles while leaving others stable. This applies equally to both generate-level decay chains and MadSpin `decay` directives.

## Why Production × BR Doesn't Match

A common confusion: generating `p p > t t~` and comparing with `p p > t t~, t > w+ b, t~ > w- b~` expecting σ₁ × BR(t→Wb)² ≈ σ₂. The match is approximate but not exact, due to:

1. **Final-state cuts**: Different final-state particles mean different cuts apply. Disable with `cut_decays = F`.
2. **Width consistency**: The total width in the param_card must match the physical width. MG5 divides the phase-space integral by the total width.
3. **bwcutoff**: Restricts the off-shell range, introducing a small bias.
4. **Non-resonant diagrams**: The decay chain syntax keeps only resonant diagrams. The missing non-resonant contributions introduce errors of order Γ/M.
5. **Scale choices**: Dynamical scale choices can evaluate differently for different final states.
6. **NLO vs LO widths**: If the param_card width is from NLO but the matrix element is LO, there is a mismatch.

## MadSpin

MadSpin is an external tool that decays heavy resonances **after** event generation while preserving spin correlations. It operates between the hard-process generation and the parton shower.

### Advantages of MadSpin

- **Faster**: Decays are applied to already-generated events, avoiding the combinatorial explosion of including all decay products in the matrix element.
- **NLO compatible**: For NLO processes, including decays directly in the `generate` line is often not possible. MadSpin is the recommended approach.
- **Flexible**: Different decay channels can be specified without regenerating the hard process.

### MadSpin in Scripts

The madspin_card uses its own command language — it is **not** a parameter-value card like the run_card or param_card. You cannot use `set madspin_card decay ...` to add decay lines. Instead, use bare `decay` commands directly in the launch block.

> **Common mistake**: Writing `set madspin_card decay t > w+ b, w+ > l+ vl` in a launch block does NOT work. MadGraph will emit a warning (`Command set not allowed for modifying the madspin_card`) and MadSpin will fall back to the default madspin_card, which typically contains all-channel decays. Use bare `decay` commands instead (see below).

**Correct approach — bare `decay` commands in the launch block:**

```
import model sm
generate p p > t t~
output ttbar_madspin
launch ttbar_madspin
  madspin=ON
  shower=PYTHIA8
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  decay t > w+ b, w+ > l+ vl
  decay t~ > w- b~, w- > l- vl~
  done
```

Bare `decay` commands typed during the card-editing phase (between `launch` and `done`) are written directly into the madspin_card.dat. This is the simplest and recommended approach.

**Alternative — provide a custom madspin_card.dat file:**

For complex MadSpin configurations (custom spinmode, BW_cut, multiparticle definitions, etc.), create a `madspin_card.dat` file and provide its path in the launch block:

1. Create a `madspin_card.dat` file:

```
# madspin_card.dat
set spinmode onshell
set BW_cut 15

decay t > w+ b, w+ > l+ vl
decay t~ > w- b~, w- > l- vl~

launch
```

2. Reference it in the launch block:

```
launch ttbar_madspin
  madspin=ON
  shower=PYTHIA8
  /path/to/madspin_card.dat
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

MadGraph auto-detects the card type from the file content and copies it to the correct location.

### Syntax Comparison: madspin_card vs Other Cards

The `set <card> <param> <value>` syntax in a launch block is supported only for certain cards. The madspin_card is not one of them.

| Card | `set <card>` syntax in launch block | Notes |
|------|-------------------------------------|-------|
| `param_card` | `set param_card mass 6 172.5` | Full parameter-value support |
| `run_card` | `set run_card nevents 10000` | Full parameter-value support |
| `pythia8_card` | `set pythia8_card TimeShower:alphaSvalue 0.118` | Appends Pythia8 directives |
| `delphes_card` | `set delphes_card atlas` | **Presets only**: `default`, `atlas`, or `cms` — not arbitrary parameters |
| `madspin_card` | **Not supported** — use bare `decay` commands or provide file path | `decay t > w+ b, w+ > l+ vl` |

For all cards, you can alternatively provide a file path in the launch block; MadGraph auto-detects the card type.

**Details ->** [Cards and Parameters](cards-and-parameters.md)

### MadSpin Card Configuration

The `madspin_card.dat` contains MadSpin commands executed sequentially. Key directives:

```
# spinmode options:
#   madspin = full spin correlations and off-shell effects (default)
#   full    = alias for madspin (functionally identical)
#   onshell = full spin correlations, particle kept exactly on-shell (requires f2py)
#   none    = no spin correlations, no off-shell effects (supports 3-body decay, loop-induced)
set spinmode madspin
set BW_cut 15              # Breit-Wigner cutoff: on-shell window = mass ± BW_cut*width
                           # Default: -1 (inherit bwcutoff from run_card)

# Multiparticle labels (optional — built-in l+, l-, vl, vl~ are available)
define ell+ = e+ mu+
define ell- = e- mu-

# Decay specifications — bare 'decay' commands, one per line
decay t > w+ b, w+ > l+ vl
decay t~ > w- b~, w- > l- vl~

# 'launch' triggers MadSpin execution
launch
```

**Key points:**
- The `launch` at the end of the madspin_card.dat is required — it triggers the actual decay processing.
- The MadSpin parameter for the BW cutoff is `BW_cut` (not `bwcutoff` — that is the run_card parameter name). When `BW_cut` is set to `-1` (default), MadSpin inherits the value from the run_card's `bwcutoff`.
- The `spinmode` default is `madspin`. Valid values: `madspin`, `full`, `onshell`, `none`. The `full` and `madspin` modes are functionally identical.

| Mode | Spin correlations | Off-shell effects | Speed | Use when |
|------|-------------------|-------------------|-------|----------|
| `full` (default) | Yes | Yes | Slowest | Default choice; needed for precision |
| `onshell` | Yes | No | Faster | Narrow resonances where off-shell tails are irrelevant |
| `none` | No | No | Fastest | Phase-space decay; testing or when spin is unimportant |

> **Note on the MadSpin reweighting formula:** The formula $w = |\mathcal{M}_{\text{full}}|^2 / (|\mathcal{M}_{\text{prod}}|^2 \times \prod_i |\mathcal{M}_{\text{decay},i}|^2)$ commonly associated with MadSpin describes the `onshell` mode only. The default mode (`spinmode = madspin`/`full`) uses a different implementation with phase-space sampling (without decay matrix elements) and a simpler weight. Both modes produce identical spin-correlated distributions in the narrow-width limit.

**Details ->** [Scripted Execution](scripted-execution.md)

### Cascade Decays with Parentheses

For multi-step cascade decays, parentheses define the nesting hierarchy:

```
decay h2 > z h3 mu+ mu-, (h3 > z h1 j j, h1 > b b~)
```

**Without parentheses**, MadSpin may misinterpret the decay chain, causing orders-of-magnitude errors in the cross-section. Always use parentheses for cascades beyond simple two-body decays.

### Common MadSpin Issues

#### Branching Ratio > 1

```
WARNING: Branching ratio larger than one for particle 25 (Higgs)
```

This means the total width in the param_card is too small. MadSpin computes the partial width for the requested decay and divides by the stated total width. If the partial width exceeds the total width, BR > 1.

**Fix**: Use `compute_widths` to calculate consistent widths, or manually set the correct total width in the param_card. For the Higgs, the SM width is ~6.5×10⁻³ GeV. See the [MadWidth section](#madwidth-compute_widths) above.

#### Dependent Parameters Warning

```
WARNING: Failed to update dependent parameter
```

External programs (MadSpin, Pythia8) read the param_card and may get inconsistent values if dependent parameters aren't updated. Respond with `update dependent` when prompted, or ensure manual consistency.

## Multiparticle Labels in Decay Chains

Multiparticle labels in decay specifications are expanded via Cartesian product over all particles in the label. MG5 does **not** validate whether the resulting decay channels are physically allowed.

Example pitfall: Defining `define nu = vl vl~` (mixing neutrinos and antineutrinos) and then writing:

```
decay w+ > l+ nu
```

This expands to both `w+ > l+ vl` (physical: W+ → l+ ν) **and** `w+ > l+ vl~` (unphysical: W+ → l+ ν̄, violates charge conservation). MG5 silently skips unphysical channels that produce no diagrams or have no matching branching ratio, but this can cause confusing behavior: only a subset of the intended channels are generated.

**Best practice**: Use the built-in multiparticle labels (`vl`, `vl~`, `l+`, `l-`) in decay specifications. These are defined with correct particle/antiparticle content:

```
decay w+ > l+ vl       # correct: l+ vl = e+ ve, mu+ vm, ta+ vt
decay w- > l- vl~      # correct: l- vl~ = e- ve~, mu- vm~, ta- vt~
```

Do not define custom multiparticle labels that mix particles and antiparticles for use in decay chains.

## Production vs Decay Radiation

When generating a process with radiation alongside an unstable particle — e.g., `p p > t t~ a` — the matrix element includes photons from **all** sources: initial-state radiation, radiation off the top quarks, and radiation from the decay products (if decays are included). MG5 does not distinguish these contributions; the full matrix element handles them coherently.

However, double counting arises if you **also** decay the tops with MadSpin including photon radiation, or if you combine this sample with events from `p p > t t~` followed by showered decay radiation. To avoid this:

- Generate the full final state in one `generate` command when radiation matters (e.g., `p p > t t~ a, t > w+ b, t~ > w- b~`)
- Or generate `p p > t t~` with MadSpin for decays and rely on the parton shower for soft/collinear radiation — but do NOT add a separate `p p > t t~ a` sample

## Choosing Between Generate-Level Decays and MadSpin

| Criterion | Generate-level decay | MadSpin |
|-----------|---------------------|---------|
| Speed | Slower (full ME) | Faster (post-generation) |
| NLO processes | Not supported (comma syntax); works with `>` syntax | Recommended approach |
| Spin correlations | Full, exact | Full tree-level (via reweighting) |
| Off-shell effects | Included (with `>` syntax); BW window with comma syntax | Default mode: yes (BW sampling); onshell mode: no |
| Flexibility | Fixed at generation | Decay later, reuse events |
| Complex cascades | Limited | Better (with parentheses) |

**When to use which**:

- **LO production**: Prefer generate-level decay chains — they include full off-shell effects and exact spin correlations, and are simpler to set up.
- **NLO production**: The `>` syntax (e.g., `p p > t t~ > w+ b w- b~ [QCD]`) and MadSpin are both supported. The `>` syntax includes full off-shell effects but is computationally expensive for complex cascades. MadSpin is the practical default for most NLO workflows — it is faster, allows reuse of hard-process events with different decay channels, and preserves spin correlations at NWA-level accuracy. **Warning**: The comma-based decay chain syntax (e.g., `p p > t t~, t > w+ b [QCD]`) is not supported at NLO — MadGraph5_aMC@NLO raises an error when decay chains are combined with the `[ ]` NLO syntax.
- **Scalar particle decays** (e.g., H → WW* → 4f): Spin correlations between production and decay are absent for scalars. MadSpin's NWA limitation is less important here; the main concern is off-shell W* effects, which require generate-level treatment or dedicated tools.
- **Broad resonances** (Γ/M > 5-10%): Do not use decay chain syntax or MadSpin. Generate the full final state as a single process to capture off-shell and interference effects.

## MadWidth (compute_widths)

MadWidth computes particle decay widths and branching ratios within MadGraph5. By default, it calculates **tree-level (LO)** partial widths for all kinematically allowed decay channels of specified particles.

**NLO consistency note**: Since `compute_widths` and `DECAY X auto` produce LO widths by default, using them with NLO matrix elements introduces an O(alpha_s) mismatch. The sum of LO partial widths will not exactly match the NLO total width, creating a small systematic bias in the Breit-Wigner normalization and branching ratios. For most processes this is a sub-percent effect, but for precision studies, consider using widths from dedicated higher-order calculations.

### The `compute_widths` Command

```
import model sm
compute_widths t w+ w- z h
```

This computes the decay widths and branching ratios for the top quark, W+, W-, Z, and Higgs boson. The results are printed to the terminal and written to the param_card.

#### Script Usage

```
import model sm
compute_widths t w+ w- z h
generate p p > t t~
output my_process
launch my_process
  set run_card nevents 10000
  done
```

Run `compute_widths` **before** `output` to ensure the param_card in the output directory has consistent widths. Note: `compute_widths` does not require a generated process — it operates on the model alone. But `output` requires a prior `generate` command.

#### Specifying Options

```
compute_widths t --body_decay=2.0      # include 2-body decays only
compute_widths h --precision=0.01      # set precision threshold
compute_widths all                      # compute widths for all particles
```

### Reading the Output

The `compute_widths` command prints a table for each particle:

```
DECAY   6   1.4915e+00   # t : total width
#   BR          NDA   ID1   ID2
    1.000000    2     24     5     # W+ b
```

This shows:
- Total width of the top quark: ~1.49 GeV
- 100% branching ratio to W+b

### Why Consistent Widths Matter

Incorrect widths in the param_card cause: MadSpin BR > 1 errors (width too small) or underweighted events (width too large), incorrect Breit-Wigner resonance windows, and incorrect Breit-Wigner normalization.

### Fixing BR > 1 Errors

When MadSpin reports `Branching ratio larger than one for particle 25 (Higgs)`:

1. Check the DECAY block in the param_card:
   ```
   DECAY 25 1.0e-5    # Wrong! Too small
   ```

2. Fix by computing the correct width:
   ```
   compute_widths h
   ```

3. Or manually set the correct value:
   ```
   set param_card decay 25 6.478e-3
   ```

### Model-Dependent Limitations: Loop-Induced Channels

`compute_widths` computes partial widths using the **tree-level vertices available in the loaded model**. Decay channels that proceed through loop diagrams — and for which the model contains no tree-level effective vertex — are not included.

The most important SM example is the **Higgs boson** in the `sm` model:
- **Included** (tree-level vertices exist): H→bb̄, H→ττ, H→cc̄ (and other kinematically allowed fermionic channels)
- **Not included** (loop-induced, no tree-level vertex in `sm`): H→gg, H→γγ, H→Zγ

The missing channels mean the computed branching ratios and total width are incomplete. Additionally, the tree-level computation uses the b-quark pole mass for the Yukawa coupling, which significantly differs from the running mass used in state-of-the-art predictions. The net result is that `compute_widths` with the `sm` model gives a Higgs width that differs substantially from the physical SM value (~4.1×10⁻³ GeV from LHCHXSWG).

In the `heft` model, the effective Hgg vertex is present, so `compute_widths` with `heft` **will** include H→gg. However, `heft` does not include H→γγ.

**Practical guidance:**
- For the Higgs boson, set the total width manually from external calculations (e.g., LHCHXSWG predictions) rather than relying on `compute_widths`.
- For internal consistency (e.g., MadSpin using the same tree-level matrix elements), the `compute_widths` value can be used — but be aware it does not match the physical SM width.
- For BSM models, be aware that new particles may have significant loop-induced decay channels that `compute_widths` will miss if the model lacks the corresponding effective vertices.
- Running `compute_widths` remains the correct approach for most particles where tree-level channels dominate (top, W, Z, and most BSM particles).

### BSM Models

For BSM models, particle widths are generally not known a priori. Always run `compute_widths` for BSM particles:

```
import model 2HDM    # requires downloaded 2HDM UFO model
compute_widths h+ h- h2 h3 a0
```

This ensures:
- Consistent param_card values for MadSpin and event generation
- Correct branching ratios for decay chain specifications
- Proper Breit-Wigner resonance shapes

### Auto-Width

Setting `DECAY X auto` in the param_card (or via `set param_card decay X auto`) tells MG5 to compute the width automatically during event generation.

## Decision Table: Which Decay Method to Use

| Scenario | Recommended method |
|----------|--------------------|
| LO, narrow resonance, simple decay | Generate-level comma syntax |
| LO, need off-shell / interference | Full final-state generation (no decay chain) |
| NLO production, simple decay | Direct NLO `>` syntax (e.g., `p p > t t~ > w+ b w- b~ [QCD]`) or MadSpin (faster, flexible). **Comma syntax is not supported at NLO.** |
| NLO production, complex cascade | MadSpin (multi-step cascades cause significant diagram-count growth; simple two-body decays like t→Wb have only ~25% overhead) |
| Scalar decay (e.g., H -> WW*) | Generate-level for off-shell W*; MadSpin acceptable if off-shell effects are small |
| Broad resonance (Gamma/M > 5-10%) | Full matrix element -- do not use comma syntax or MadSpin |
| Reusing hard-process events with multiple decay channels | MadSpin (apply different decays without regenerating) |

## Resonant Diagram Approximation

Both comma syntax and MadSpin keep only resonant diagrams, discarding non-resonant contributions. This approximation is valid when Γ/M is small (the narrow-width regime) but MadGraph does not use the textbook NWA factorization (σ × BR) — it performs phase-space integration with Breit-Wigner propagators within the `bwcutoff` window. See [complex-mass-scheme.md](complex-mass-scheme.md) for NWA validity criteria and when to use the full off-shell matrix element.

## The `bwcutoff` Parameter

Controls the Breit-Wigner window for on-shell resonances:

```
15.0    = bwcutoff    ! in the run_card
```

An on-shell particle's invariant mass must satisfy |m - M| < bwcutoff × Γ. The default of 15 widths captures essentially the full resonance. Reduce for narrow cuts; increase for very broad resonances (but consider using the full matrix element instead).

## The `cut_decays` Parameter

Controls whether generation-level cuts apply to decay products:

```
False   = cut_decays    ! in the run_card
```

When `False` (default), cuts like `ptl` and `etal` do not apply to leptons from resonance decays. When `True`, all final-state cuts apply uniformly. This matters for cross-section comparisons between decayed and undecayed processes.
