# 16 — Troubleshooting

This document provides a systematic approach to diagnosing common MadGraph5 errors, unexpected results, and performance issues.

## Contents

- [Diagnostic Approach](#diagnostic-approach)
- ["0 Diagrams" / "No Amplitudes Generated"](#0-diagrams-no-amplitudes-generated)
  - [Decision Tree](#decision-tree)
- [Cross-Section Too Small](#cross-section-too-small)
  - [Symptom: Cross-section is orders of magnitude below expectations.](#symptom-cross-section-is-orders-of-magnitude-below-expectations)
- [Cross-Section Too Large](#cross-section-too-large)
  - [Symptom: Cross-section seems unphysically large.](#symptom-cross-section-seems-unphysically-large)
- [Event Generation Issues](#event-generation-issues)
  - [Too Few Events Generated](#too-few-events-generated)
  - ["No Events Passed the Matching"](#no-events-passed-the-matching)
- ["fail to reach target" (Insufficient Events Generated)](#fail-to-reach-target-insufficient-events-generated)
  - [Common Causes](#common-causes)
- [Nearly Massless Final-State Particles](#nearly-massless-final-state-particles)
  - [Symptoms](#symptoms)
  - [Diagnosis Checklist](#diagnosis-checklist)
  - [Fixes (in order of preference)](#fixes-in-order-of-preference)
  - [Key Points](#key-points)
- [Floating-Point Exceptions (SIGFPE)](#floating-point-exceptions-sigfpe)
  - [Common Causes](#common-causes)
- ["failed to reduce to color indices"](#failed-to-reduce-to-color-indices)
  - [Common Causes](#common-causes)
- [NLO Errors](#nlo-errors)
  - ["Poles Do Not Cancel"](#poles-do-not-cancel)
  - ["Cannot Find the Model" for NLO](#cannot-find-the-model-for-nlo)
  - [Large Negative Weights](#large-negative-weights)
  - [Version Differences (v2 vs v3)](#version-differences-v2-vs-v3)
- [Width and Decay Issues](#width-and-decay-issues)
  - [MadSpin: "Branching Ratio Larger Than One"](#madspin-branching-ratio-larger-than-one)
  - [Cascade Decay Cross-Section Wrong by Orders of Magnitude](#cascade-decay-cross-section-wrong-by-orders-of-magnitude)
  - [Dependent Parameters Warning](#dependent-parameters-warning)
  - [Small Width Treatment](#small-width-treatment)
- [Compilation Errors](#compilation-errors)
  - [Fortran Line Length Errors](#fortran-line-length-errors)
- [Performance Issues](#performance-issues)
  - [Slow Event Generation with Custom Models](#slow-event-generation-with-custom-models)
- [Cross-Section Physics](#cross-section-physics)
  - [W+/W- Asymmetry](#ww-asymmetry)
  - [Energy Dependence](#energy-dependence)
  - [VBF Isolation](#vbf-isolation)

## Diagnostic Approach

When something goes wrong, follow this order:

1. **Read the error message** — MG5 error messages are usually informative.
2. **Check the log files** — `<PROC_DIR>/Events/run_XX/` contains detailed logs.
3. **Verify the model** — is the correct model loaded? (`display particles`)
4. **Check the cards** — are param_card and run_card consistent?
5. **Simplify** — reproduce with a minimal process before debugging the complex one.

---

## "0 Diagrams" / "No Amplitudes Generated"

The `generate` command finds no valid Feynman diagrams for the requested process.

### Decision Tree

1. **Conservation law violation**: Check that the process conserves electric charge, color, lepton number, and baryon number.
   - Example: `e+ e- > g g` — electrons don't carry color, so no QCD vertex exists at tree level. Use `e+ e- > u u~` instead.

2. **Wrong model**: The model doesn't contain the needed interactions.
   - Example: `g g > h` in the SM — this is loop-induced, no tree-level diagrams exist. Use `import model heft` for the effective vertex, or `loop_sm` with `[noborn=QCD]`.
   - Example: `p p > h z` — double-check the model is loaded (`import model sm`). Verify the particle name with `display particles`.

3. **Overly restrictive coupling orders**: Explicit `QCD=0` or `QED=0` may eliminate all diagrams.

4. **Diagram filtering**: Using `/`, `$`, or `$$` may remove all contributing diagrams.

**Diagnostic commands**:
```
display particles          # verify particle names and properties
display interactions        # verify available vertices
check gauge <process>       # test if the (filtered) process is gauge invariant
```

## Cross-Section Too Small

### Symptom: Cross-section is orders of magnitude below expectations.

**Common causes:**

1. **Overly tight generation cuts**: Check `pt_min_pdg`, `mxx_min_pdg`, `eta_max_pdg` in the run_card.
   - Example: `pt_min_pdg = {11: 500}` requires electron pT > 500 GeV — this kills the Z peak for Drell-Yan.
   - Example: `mxx_min_pdg = {11: 1000}` requires m(e+e-) > 1 TeV.
   - Also check: `ptj`, `ptl`, `pta`, `etaj`, `etal`, `etaa`, `drjj`, `drll`.
   - **Fix**: Relax or remove generation-level cuts.

2. **Wrong beam energy**: Check `ebeam1`, `ebeam2` — are they in GeV? Is each beam half the desired √s?

3. **Wrong beam type**: For e+e- collisions, `lpp1 = lpp2 = 0` (no PDFs). Using proton PDFs for e+e- gives wrong results.

4. **Phase space suppression**: Heavy particles near the kinematic threshold have small cross-sections. Verify that 2×m_particle < √s.

## Cross-Section Too Large

### Symptom: Cross-section seems unphysically large.

**Common causes:**

1. **QCD process**: bb̄ production at the LHC has σ ≈ 500 μb — this is physical, not an error. QCD processes are proportional to α_s², which is much larger than α_EW. The cross-section hierarchy at the LHC:
   - Total inelastic: ~80 mb
   - bb̄: ~0.5 mb
   - tt̄: ~0.5 nb (500 pb)
   - WW: ~65 pb
   - ZH: ~1 pb

2. **Missing cuts**: Some processes (like `p p > j j`) have QCD divergences that require generation-level cuts (ptj > 0) to regulate.

3. **Matching misconfiguration**: Pre-shower cross-sections with MLM matching are not physical — they don't include Sudakov suppression. Use the post-shower cross-section.

## Event Generation Issues

### Too Few Events Generated

**Symptoms**: Requested 50,000 events but got ~1,000.

**Common causes:**

1. **xqcut = 0 with matching (ickkw = 1)**: Without a generation-level kt cut, soft/collinear divergences make unweighting extremely inefficient. **Fix**: Set `xqcut` to an appropriate value (15-30 GeV).

2. **Very tight cuts**: Phase space is too restricted for efficient event generation.

3. **Heavy particles near threshold**: Close to the kinematic limit, the integration efficiency is low. Increase `npoints_FO` or relax mass requirements.

### Very Low Matching Efficiency

**Symptoms**: Very few or no events survive matching vetoes.

**Common causes:**

1. **Single multiplicity with ickkw = 1**: Only generated one multiplicity but enabled matching. The matching procedure adds overhead and can reduce efficiency through parton-jet matching failures, even though single-multiplicity samples run in inclusive mode (no hard-jet veto). **Fix**: Set `ickkw = 0` or add more multiplicities.

2. **qCut too large**: If `JetMatching:qCut` is much larger than `xqcut`, most events are rejected. **Fix**: Use `qCut ≈ 1.2-1.5 × xqcut`.

3. **Missing @N tags**: While MadGraph auto-assigns process numbers when `@N` tags are omitted, explicitly labeling subprocesses is recommended for clarity:
   ```
   # RECOMMENDED
   generate p p > t t~ @0
   add process p p > t t~ j @1
   ```

## "fail to reach target" (Insufficient Events Generated)

```
INFO: fail to reach target 60000
```

MadEvent completed the cross-section integration (survey + refine) successfully, but the **unweighting** step could not produce enough unweighted events to meet the `nevents` target. The reported cross-section may still be valid; only the event count is low.

### Common Causes

1. **Missing or too-loose generation cuts**: Collinear/IR singularities make unweighting extremely inefficient. Example: setting `draj = 0.0` removes the photon-jet collinear cut, producing a singularity that prevents efficient unweighting.
   - **Fix**: Set physically sensible non-zero values for `ptj`, `ptl`, `drjj`, `draj`, etc.

2. **Phase-space topology with low unweighting efficiency**: Processes with many diagrams or interference-dominated topologies can have poor phase-space mapping. The MadEvent multi-channel integrator may not efficiently sample all regions.
   - **Fix**: Try `sde_strategy = 2` in the run_card (the newer multi-channel integration strategy, which can improve unweighting efficiency for processes with many diagrams).
   - Alternative: Try a different random seed (`iseed` in run_card) — this error can exhibit high seed sensitivity.

3. **Zero or inconsistent particle widths**: Setting the width of a particle to zero in the param_card when it should be able to decay creates a mathematical singularity. Events generated under these conditions are unreliable.
   - **Fix**: Use `compute_widths <particle>` or `DECAY <particle> auto` in the param_card.

4. **Very large event samples (LO only)**: Per-channel event limits can prevent reaching high `nevents` targets.
   - **Fix**: Use `multi_run N` (from the MadEvent interface: `launch <PROC_DIR> -i`, then `multi_run N`) to split into N independent runs, each generating `nevents/N` events. This is available for LO event generation only.

**Note**: The cross-section value in the results summary can still be valid even when the event count is far below target. Check `crossx.html` to compare integration channel luminosities.

---

## Nearly Massless Final-State Particles

BSM models sometimes introduce very light particles (e.g., dark photons, axion-like particles, light scalars) with masses far below the other particles in the process. When such a particle couples to heavier final-state particles (e.g., a 1 MeV dark photon coupling to muons), it behaves as effectively massless and produces **soft and collinear singularities** in the matrix element — analogous to real photon emission in QED.

**This is NOT a narrow-resonance or unweighting-efficiency problem.** It is a fundamentally different issue: the matrix element diverges when the light particle becomes soft (low energy) or collinear with another final-state particle. Decay-chain syntax (`p p > mu+ mu- (zp > ...)`) does not help because the light particle is a direct final-state object, not an intermediate s-channel resonance.

### Symptoms

| Symptom | Explanation |
|---------|-------------|
| "fail to reach target" with very few events generated (e.g., 25 out of 10,000) | Integrator spends most time in singular phase-space regions with near-zero unweighting efficiency |
| Very slow event generation despite finite cross-section | Matrix element is sharply peaked in soft/collinear regions; acceptance rate for unweighted events is extremely low |
| Cross-section appears large or unstable across runs | Soft/collinear divergences inflate the integral; results depend sensitively on seed and sampling |

### Diagnosis Checklist

1. Is there a final-state BSM particle with mass ≪ the other final-state particles?
2. Does this particle couple to one or more of the other final-state particles?
3. If both answers are yes, soft/collinear singularities are the likely cause.

### Fixes (in order of preference)

**1. Apply a pT cut on the light particle using `pt_min_pdg`:**

The `pt_min_pdg` run_card parameter applies a minimum-pT generation cut to any particle identified by PDG code. This regulates the soft singularity.

```
set run_card pt_min_pdg {9000005: 5.0}   # min pT = 5 GeV for PDG 9000005 (example dark photon)
```

**2. Apply a deltaR separation cut via custom cuts:**

The pT cut alone does not fully regulate the collinear singularity. A deltaR separation between the light particle and the particles it couples to is needed. This requires a custom-cuts Fortran function because the standard run_card `drXX` parameters only apply to SM-classified particles (jets, leptons, photons).

Create a Fortran file defining a `dummy_cuts` function and register it via:

```
set run_card custom_fcts ['/absolute/path/to/my_custom_cuts.f']
```

See [Cards & Parameters — Custom Cuts](cards-and-parameters.md) for the `dummy_cuts` function signature and details.

**Important:** If your custom cut breaks flavor or beam symmetries, you must disable subprocess grouping by setting `group_subprocesses` to `False` **before** the `generate` command — it is a generation-time MG5 option, not a run_card parameter:

```
set group_subprocesses False
generate p p > mu+ mu- zp
output my_process
```

**3. Combine both cuts for best results:**

Use `pt_min_pdg` to regulate the soft region and a custom deltaR cut to regulate the collinear region. Together these remove the singular phase-space corners while keeping the physically interesting region.

**4. Additional measures for marginal cases:**

- `set run_card sde_strategy 2` — alternative phase-space integration strategy that can improve efficiency for processes where the standard strategy underperforms. Note: `sde_strategy 2` has no effect when `group_subprocesses` is `False`.
- Use the `bias_module` to enhance the physically relevant region while keeping correct weighted distributions.

### Key Points

- **Nearly massless final-state particles cause soft/collinear divergences** — a distinct problem from narrow-resonance unweighting inefficiency or `small_width_treatment`.
- **Decay-chain syntax does not help**: the light particle is a final-state object, not an s-channel propagator.
- **Generation-level cuts are mandatory**: without pT and/or deltaR cuts, the integrator cannot efficiently sample the phase space.
- **Standard run_card `drXX`/`ptX` cuts only apply to SM-classified particles** (jets, leptons, photons). For BSM particles, use `pt_min_pdg` (by PDG code) and `custom_fcts` for angular separation cuts.
- **`group_subprocesses` is a generation-time option**, not a run_card parameter. Set it with `set group_subprocesses False` before `generate`/`output`, not during `launch`.

---

## Floating-Point Exceptions (SIGFPE)

```
Program received signal SIGFPE: Floating-point exception - erroneous arithmetic operation.
```

### Common Causes

1. **Loop-reduction library numerical issues (NLO)**: The loop integral reduction libraries (COLLIER, CutTools, IREGI) can produce intermediate floating-point exceptions (`IEEE_DIVIDE_BY_ZERO`, `IEEE_INVALID_FLAG`) during NLO calculations. These are normally handled internally but become fatal when strict compiler flags trap them.
   - **Fix**: Remove strict FPE-trapping flags (e.g., `-ffpe-trap=invalid,zero`) from `Source/make_opts`.
   - Alternative: Unlink COLLIER if debugging suggests it is the source.

2. **Phase-space integration grid degradation**: When upstream numerical failures corrupt the integration grid normalization, the `DiscreteSampler` module encounters a division by zero.
   - **Fix**: Try `sde_strategy = 1` in the run_card (reverts to the older integration strategy).
   - Alternative: Recompile all dependencies (CutTools, IREGI, COLLIER) with the same compiler.

3. **Kinematic edge cases**: Extreme configurations such as boosting heavy quarks into frames where the quark mass exceeds the parent hadron mass can trigger divisions by zero in Lorentz boost routines.
   - **Fix**: Use appropriate flavor schemes (e.g., 5-flavor scheme with massless b-quarks via a restriction file) instead of keeping all quark masses non-zero.

4. **Compiler-specific issues**: Different gfortran versions handle IEEE floating-point edge cases differently. A process that runs fine with one compiler version may crash with another.
   - **Fix**: Upgrade MadGraph to the latest stable release. Recompile all dependencies with the same compiler version.

SIGFPE errors are more common in **NLO and loop-induced processes** (which invoke loop integral reduction) and in **BSM models** with unusual parameter points.

---

## "failed to reduce to color indices"

```
MadEventError : Error: failed to reduce to color indices: 0 1
```

MadGraph could not assign valid color flow indices (ICOLUP in the LHE event record) to a generated event. The leading-color approximation algorithm failed to map the selected Feynman diagram to a consistent color flow.

### Common Causes

1. **MadGraph version bugs**: This error has been fixed multiple times across MadGraph releases. Older versions have known bugs in the color flow assignment code.
   - **Fix**: Upgrade to the latest stable MadGraph release.

2. **Subprocess grouping conflicts**: The `group_subprocesses` setting can trigger this error in some processes.
   - **Fix**: Try toggling `set group_subprocesses False` (or `True`).

3. **MLM matching interaction**: With `ickkw = 1` (MLM matching), the color flow selection may conflict with the diagram configuration variable in some versions.
   - **Fix**: Upgrade to the latest stable version.

---

## NLO Errors

### "Poles Do Not Cancel"

```
aMCatNLOError: Poles do not cancel, run cannot continue
```

When IR poles don't cancel, MG5 aborts with this error. The cause is **always** a mismatch between the real and virtual contributions — never a PDF choice or parameter card issue (IR poles are properties of the matrix elements and subtraction scheme, not of PDFs).

**Important NLO syntax note:** The `$` (single dollar) syntax for excluding intermediate particles is **not valid at NLO**. MG5 will reject it with: `$ syntax not valid for aMC@NLO. $$ syntax is on the other hand a valid syntax.` Only the `$$` syntax (excluding s-channel propagators) is available for NLO processes.

#### Cause 1: Resonant Contributions in Real-Emission Diagrams (5-Flavor Scheme)

This is a **well-known cause** for processes involving electroweak bosons at NLO QCD. In the 5-flavor scheme (5FS), the b-quark is a massless parton in the proton. Real-emission diagrams with b-quark initial states can then contain **on-shell top-quark propagators** that are absent at Born level. These resonant contributions have IR singularities not matched by the virtual corrections, causing pole cancellation to fail.

**Affected processes** (examples, not exhaustive):

| Process | Resonant channel in real emission |
|---------|----------------------------------|
| `p p > w+ w- [QCD]` | `b g > w+ w- b` via on-shell `t` (`b g > t w-`, `t > w+ b`) |
| `p p > w+ w- h [QCD]` | Same mechanism — resonant top in b-initiated real emission |

The underlying problem: the FKS subtraction scheme assumes that real-emission singularities arise from soft/collinear limits of Born-level topologies. When a new resonance (e.g., an on-shell top quark) appears only in the real-emission diagrams, the subtraction terms constructed from the Born do not match, and pole cancellation fails.

**Fix — switch to the 4-flavor scheme (recommended by MG5 developers):**

Removing the b-quark from the proton definition eliminates the b-initiated channels that produce the resonant top quarks. This is the solution recommended by Olivier Mattelaer (MG5 lead developer).

```
import model loop_sm
# Define proton and jets WITHOUT b-quarks
define p = g u c d s u~ c~ d~ s~
define j = g u c d s u~ c~ d~ s~
generate p p > w+ w- [QCD]
output pp_ww_NLO_4FS
launch pp_ww_NLO_4FS
  shower=PYTHIA8
  set run_card maxjetflavor 4
  set run_card lhaid <4-flavor PDF set ID>   # e.g., NNPDF31_nlo_as_0118_nf_4
  done
```

**Key requirements for a consistent 4FS setup:**
- Redefine `p` and `j` multiparticle labels to exclude `b` and `b~` **before** `generate`.
- Set `maxjetflavor = 4` in the run_card.
- Use a **4-flavor PDF set** (the PDF must be fitted with `nf=4` active flavors). Using a 5-flavor PDF with `maxjetflavor = 4` is inconsistent.
- Use a **diagonal CKM matrix** (recommended by MG5 developers for this specific fix) to prevent any residual top-quark contributions via off-diagonal CKM elements.
- The b-quark mass remains non-zero in the param_card (it enters the matrix element).

**Important clarifications:**
- This error is **not caused by PDF choice** (LO vs NLO PDFs). IR poles are properties of the matrix elements and subtraction scheme. Using NLO PDFs does not fix pole cancellation.
- The `$$` syntax cannot solve this problem either — while `$$` is valid at NLO, it excludes s-channel propagators, and this does not properly resolve the FKS subtraction mismatch caused by the resonant real-emission contributions. The 4FS is the correct approach.
- The `complex_mass_scheme` does not resolve this issue — it addresses finite-width effects, not the appearance of new resonant channels.
- Setting `IRPoleCheckThreshold = -1.0d0` merely disables the check; it does not fix the underlying mismatch. In this case, the NLO corrections will be abnormally large and unphysical.

**Note:** For a related but distinct problem — NLO processes where real-emission diagrams overlap with a *different* physical process (e.g., Wt vs tt̄) — see Cause 4 below, where `$$` *is* an appropriate tool.

#### Cause 2: Discarded Non-QCD Loop Diagrams (VBF/VBS/Single-Top)

When computing `[QCD]` corrections, MG5 filters out loop diagrams that are not pure QCD perturbations — specifically, pentagon diagrams containing non-QCD particles (W, Z, γ, H) in the loop. During process generation, MG5 prints:

```
WARNING: Some loop diagrams contributing to this process are discarded
because they are not pure QCD-perturbation.
```

These pentagon diagrams are UV-finite and IR-finite, and typically contribute < 1% to the cross-section. However, their absence causes the formal pole check to fail because the bookkeeping of IR poles becomes incomplete.

This primarily affects:
- VBF Higgs production (`p p > h j j QCD=0 [QCD]`)
- Vector boson scattering (VBS)
- Single-top t-channel production

**Fix**: Disable the pole check by setting `IRPoleCheckThreshold = -1.0d0` in `Cards/FKS_params.dat`:

```
set FKS_params IRPoleCheckThreshold -1.0d0
```

This is safe when the discarded diagrams are genuinely negligible. The calculation proceeds and produces correct results to the stated accuracy.

**MG5 v3 vs v2**: MG5 v3 includes these pentagon contributions by default (controlled by the `nlo_mixed_expansion` interface-level option, set to `True` by default), which can eliminate this specific pole cancellation failure. See [NLO Computations — Version Differences](nlo-computations.md).

#### Cause 3: Numerical Instabilities

Rare phase-space points with poor numerical precision in the loop integral reduction (CutTools, COLLIER, IREGI) can cause pole cancellation to fail at isolated points.

**Fix**: Increase `PrecisionVirtualAtRunTime` in `Cards/FKS_params.dat` to trigger re-evaluation at higher precision for flagged points. If only a few points fail, this is harmless.

#### Cause 4: Resonance Overlap at NLO (Wt vs tt̄)

A related but distinct issue arises when real-emission diagrams at NLO overlap with a different physical process. The classic example is **single-top Wt production** (`p p > t w- [QCD]`): the real-emission diagram `g b > t w- b̄` is also a Born diagram for `p p > t t~`. This creates both a physics ambiguity and potential numerical problems.

Unlike Cause 1 (where the resonant channel is entirely absent at Born level), here the overlap is between two well-defined physical processes at the same perturbative order. The `$$` syntax *is* appropriate in this context because it cleanly removes a separable set of s-channel propagators.

Options:

1. **`$$` syntax at NLO**: For specific cases, exclude s-channel propagators to separate overlapping processes. For example, for t-channel single-top production:
   ```
   generate p p > t b~ j $$ w+ w- [QCD]
   ```
   This excludes diagrams with s-channel W propagators, separating t-channel from s-channel single-top. (Recommended by R. Frederix on the MG5 Launchpad.)

2. **MadSTR plugin**: Implements Diagram Removal (DR), Diagram Subtraction (DS), and on-shell subtraction for NLO processes with resonance overlap. Invoke with `./bin/mg5_aMC --mode=MadSTR`. See [arXiv:1907.04898](https://arxiv.org/abs/1907.04898). **Version compatibility**: MadSTR was originally developed for MG5 v2.9.x. A fix for MG5 v3.x compatibility has been pushed to the MadSTR repository (as of 2025), but users should verify with the latest plugin version.

3. **Inclusive approach**: Generate the full process and handle overlap at analysis level with invariant-mass vetoes.

#### Diagnostic Summary

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `p p > w+ w- [QCD]` in 5FS fails | Resonant top in b-initiated real emission (Cause 1) | Switch to 4FS with diagonal CKM |
| VBF/VBS process fails; "loop diagrams discarded" warning | Discarded non-QCD pentagons (Cause 2) | `IRPoleCheckThreshold = -1.0d0` |
| Isolated failures in long runs | Numerical precision (Cause 3) | Increase `PrecisionVirtualAtRunTime` |
| Wt-like process with tt̄ overlap | Resonance overlap (Cause 4) | MadSTR plugin or `$$` syntax |

### "Cannot Find the Model" for NLO

NLO requires `import model loop_sm`, not `import model sm`. The loop-capable model contains UV counterterms and rational R2 terms needed for one-loop calculations.

### Large Negative Weights

MC@NLO events can have negative weights (10-30% is typical). To reduce:
- Increase `folding` parameters: `set run_card folding 4 4 1` (allowed values per variable: 1, 2, 4, or 8).
- Consider POWHEG matching if available.
- Increase statistics to compensate for the effective statistics loss.

### Version Differences (v2 vs v3)

MG5 v3 includes pentagon loops with non-colored particles that v2 discarded. This affects VBF, VBS, and single-top processes. Control with the `nlo_mixed_expansion` interface-level option (not a run_card parameter — must be set before `generate`).

## Width and Decay Issues

### MadSpin: "Branching Ratio Larger Than One"

The total width in the param_card is too small for the requested decay. MadSpin computes the partial width and divides by the stated total width.

**Fix**: Run `compute_widths <particle>` to calculate the correct width, or manually set the DECAY value in the param_card. See [MadWidth](decays-and-madspin.md).

### Cascade Decay Cross-Section Wrong by Orders of Magnitude

In MadSpin, cascade decays require parentheses to define the nesting hierarchy:

```
# WRONG — misinterpreted nesting
decay h2 > z h3 mu+ mu-, h3 > z h1 j j, h1 > b b~

# CORRECT — explicit nesting with parentheses
decay h2 > z h3 mu+ mu-, (h3 > z h1 j j, h1 > b b~)
```

### Dependent Parameters Warning

```
WARNING: Failed to update dependent parameter
```

MG5 couldn't recalculate parameters that depend on other parameters (e.g., W mass in certain EW schemes). **Fix**: Respond with `update dependent` when prompted, or manually ensure param_card consistency.

### Small Width Treatment

For BSM particles with very small widths (Γ/M < 10⁻⁶), MG5 replaces the width with a "fake" larger width (default: 10⁻⁶ × M) to avoid numerical precision issues. The cross-section is rescaled correctly, but the Breit-Wigner shape is artificially broadened.

**Fix**: Set `small_width_treatment` in the run_card to a smaller value (e.g., `1e-12`) if you need the correct Breit-Wigner shape for very narrow resonances.

## Compilation Errors

### Fortran Line Length Errors

```
Error: Line truncated [in matrix_optim.f]
```

This occurs with complex BSM models (SMEFT, models with many couplings) when the helicity recycling optimization generates Fortran CALL statements exceeding the 132-character line limit.

**Fix**: Set `hel_recycling = False` in the run_card. This avoids the issue at the cost of slower code. Alternatively, update to MG5 v2.9.14+ or v3.4.2+ which patch this.

## Performance Issues

### Slow Event Generation with Custom Models

FeynRules-generated models often include massive light quarks (u, d, s, c), preventing MG5 from grouping subprocesses by flavor symmetry. This can make generation 10-100× slower.

**Fix**: Create a restriction file that sets light quark masses to zero, then load with `import model MYMODEL-massless`. See [Models](models-and-restrictions.md).

## Cross-Section Physics

Diagnostic benchmarks: at the LHC, σ(W+)/σ(W-) ≈ 1.3-1.4 (u/d PDF asymmetry). Cross-sections for heavy particles scale steeply with √s (e.g., σ(tt̄) at 13 TeV is ~4-5× larger than at 7 TeV).

### VBF Isolation

`p p > h j j` mixes gluon-fusion + jets and VBF diagrams. To isolate VBF, use `QCD=0` (see [Coupling Orders & Validation](coupling-orders-and-validation.md)) and diagram filtering (see [Diagram Filtering](diagram-filtering.md)). Do NOT use the `heft` model for VBF.
