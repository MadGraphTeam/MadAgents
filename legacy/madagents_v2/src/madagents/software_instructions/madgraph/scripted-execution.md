# 05 — Scripted (Non-Interactive) Execution

Script-based execution is the recommended way to run MadGraph5 for reproducibility, automation, and batch processing. A script is a plain text file containing MG5 commands, one per line, executed with:

```
<MG5_DIR>/bin/mg5_aMC my_script.mg5
```

Each `mg5_aMC` invocation is an independent process — it does not retain state from prior sessions. Compilation checks run from scratch on each invocation. Within a single interactive session, subsequent `launch` calls to the same process directory may skip recompilation if the compiled code is already up to date, but a new invocation always starts fresh.

## Contents

- [Script Structure](#script-structure)
- [The Launch Dialogue in Scripts](#the-launch-dialogue-in-scripts)
  - [Enabling Optional Tools](#enabling-optional-tools)
- [Complete Script Examples](#complete-script-examples)
  - [Example 1: LO Cross-Section Calculation](#example-1-lo-cross-section-calculation)
  - [Example 2: LO Event Generation with Pythia8](#example-2-lo-event-generation-with-pythia8)
  - [Example 3: Full Chain — Pythia8 + Delphes](#example-3-full-chain-pythia8-delphes)
  - [Example 4: With MadSpin Decays](#example-4-with-madspin-decays)
  - [Example 5: NLO QCD Computation](#example-5-nlo-qcd-computation)
  - [Example 6: MLM Matched Samples](#example-6-mlm-matched-samples)
  - [Example 7: Parameter Scan (Multiple Launches)](#example-7-parameter-scan-multiple-launches)
  - [Example 8: Higgs via Gluon Fusion (heft Model)](#example-8-higgs-via-gluon-fusion-heft-model)
  - [Example 9: BSM Workflow — 2HDM Charged Higgs](#example-9-bsm-workflow-2hdm-charged-higgs)
  - [Example 10: Using compute_widths](#example-10-using-compute_widths)
  - [Example 11: Providing Pre-Edited Card Files](#example-11-providing-pre-edited-card-files)
- [Output Directory Structure](#output-directory-structure)
  - [Locating Key Output Files](#locating-key-output-files)
- [Tips for Robust Scripts](#tips-for-robust-scripts)
- [Gridpacks](#gridpacks)
  - [Creating a Gridpack](#creating-a-gridpack)
  - [Using a Gridpack](#using-a-gridpack)
  - [Workflow for Large-Scale Production](#workflow-for-large-scale-production)
  - [Seed Management](#seed-management)
  - [Limitations](#limitations)
  - [NLO Gridpack Workflow](#nlo-gridpack-workflow)
  - [Advanced: Modifying a Gridpack](#advanced-modifying-a-gridpack)
- [Run Card Quick Reference](#run-card-quick-reference)
- [Execution Mode](#execution-mode)
  - [Setting Execution Mode](#setting-execution-mode)
  - [Cluster Mode (run_mode = 1)](#cluster-mode-run_mode-1)
- [Common Pitfalls](#common-pitfalls)

## Script Structure

A typical script follows this pattern:

```
# 1. Load model
import model sm

# 2. Define process
generate p p > t t~

# 3. Create process directory
output my_ttbar

# 4. Launch event generation with settings
launch my_ttbar
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

Lines starting with `#` are comments and are ignored.

## The Launch Dialogue in Scripts

When `launch` runs, MadGraph enters a dialogue with two stages:

1. **Switches**: Enable/disable parton shower, detector simulation, MadSpin, analysis tools. In scripts, provide switch commands before `done`.
2. **Card editing**: Modify parameters with `set` commands. End with `done`.

In practice, for simple LO runs, a single `done` after `set` commands handles both stages. For runs with optional tools (Pythia8, Delphes, MadSpin), you may need to enable them explicitly.

**Note on `done` in script mode:** In script mode (`mg5_aMC script.mg5`), reaching end-of-file implicitly acts as `done` — the script does not hang if `done` is omitted. In interactive mode, omitting `done` leaves the prompt open.

### Enabling Optional Tools

In scripts, set switches by keyword assignment or numeric selection before the card-editing stage:

```
launch my_process
  shower=PYTHIA8
  detector=Delphes
  madspin=ON
  set run_card nevents 10000
  done
```

Or equivalently by answering the numbered menu:

```
launch my_process
  1           # toggle shower (ON)
  2           # toggle detector (ON)
  3           # toggle MadSpin (ON)
  done        # proceed to card editing
  set run_card nevents 10000
  done        # start the run
```

The exact numbering depends on what tools are installed and the MG5 version. Using keyword assignments (`shower=PYTHIA8`) is more portable.

---

## Complete Script Examples

### Example 1: LO Cross-Section Calculation

Compute the LO cross-section for e+e- → μ+μ- at √s = 91.2 GeV:

```
import model sm
generate e+ e- > mu+ mu-
output ee_mumu
launch ee_mumu
  set run_card ebeam1 45.6
  set run_card ebeam2 45.6
  set run_card lpp1 0
  set run_card lpp2 0
  set run_card nevents 10000
  done
```

Note: For e+e- collisions, set `lpp1 = lpp2 = 0` (no PDFs) and each beam energy is half the center-of-mass energy.

### Example 2: LO Event Generation with Pythia8

Generate pp → tt̄ events at 13 TeV with parton shower:

```
import model sm
generate p p > t t~
output ttbar_shower
launch ttbar_shower
  shower=PYTHIA8
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

### Example 3: Full Chain — Pythia8 + Delphes

Generate pp → tt̄ with shower and detector simulation:

```
import model sm
generate p p > t t~
output ttbar_full
launch ttbar_full
  shower=PYTHIA8
  detector=Delphes
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

The Delphes output (ROOT file) appears in `ttbar_full/Events/run_01/tag_1_delphes_events.root`.

### Example 4: With MadSpin Decays

Generate pp → tt̄ with spin-correlated top decays:

```
import model sm
generate p p > t t~
output ttbar_madspin
launch ttbar_madspin
  shower=PYTHIA8
  madspin=ON
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  set madspin_card decay t > w+ b, w+ > l+ vl
  set madspin_card decay t~ > w- b~, w- > l- vl~
  done
```

See [Decays & MadSpin](decays-and-madspin.md) for MadSpin configuration details.

### Example 5: NLO QCD Computation

Compute the NLO QCD cross-section for pp → tt̄:

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

Note: NLO requires `import model loop_sm` instead of `sm`. See [NLO Computations](nlo-computations.md).

### Example 6: MLM Matched Samples

Generate matched tt̄ + 0,1,2 jets:

```
import model sm
generate p p > t t~ @0
add process p p > t t~ j @1
add process p p > t t~ j j @2
output ttbar_matched
launch ttbar_matched
  shower=PYTHIA8
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 50000
  set run_card ickkw 1
  set run_card xqcut 20
  set run_card maxjetflavor 4
  set pythia8_card JetMatching:qCut 30
  set pythia8_card JetMatching:nJetMax 2
  done
```

See [Matching & Merging](matching-and-merging.md) for parameter tuning and validation.

### Example 7: Parameter Scan (Multiple Launches)

Run the same process with different parameter values:

```
import model sm
generate p p > t t~
output ttbar_scan

launch ttbar_scan
  set param_card mass 6 172.5
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done

launch ttbar_scan
  set param_card mass 6 180.0
  set run_card nevents 10000
  done

launch ttbar_scan
  set param_card mass 6 165.0
  set run_card nevents 10000
  done
```

Each `launch` creates a new run directory (`run_01`, `run_02`, `run_03`).

### Example 8: Higgs via Gluon Fusion (heft Model)

```
import model heft
generate g g > h
output ggH_heft
launch ggH_heft
  shower=PYTHIA8
  madspin=ON
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  set madspin_card decay h > b b~
  done
```

### Example 9: BSM Workflow — 2HDM Charged Higgs

Requires the 2HDM UFO model (download from FeynRules and place in `<MG5_DIR>/models/`).

```
import model 2HDM
display particles
generate p p > h+ h-
output charged_higgs
launch charged_higgs
  set param_card mass 37 300.0
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  done
```

### Example 10: Using compute_widths

```
import model sm
compute_widths t w+ w- z h
```

This prints widths and branching ratios to screen and can be used to update the param_card consistently. See [MadWidth](decays-and-madspin.md).

### Example 11: Providing Pre-Edited Card Files

Instead of using `set` commands, provide paths to pre-edited card files:

```
import model sm
generate p p > t t~
output ttbar_custom
launch ttbar_custom
  /path/to/my_run_card.dat
  /path/to/my_param_card.dat
  done
```

MadGraph auto-detects the card type from the file content and copies it to the correct location.

---

## Output Directory Structure

After a successful run, the output directory looks like:

```
my_process/
├── Cards/              # Configuration cards (param_card.dat, run_card.dat, ...)
├── Events/
│   ├── run_01/         # First run
│   │   ├── unweighted_events.lhe.gz          # Parton-level events (LO)
│   │   ├── events.lhe.gz                     # Parton-level events (NLO)
│   │   ├── tag_1_pythia8_events.hepmc.gz     # After Pythia8 (if enabled)
│   │   ├── tag_1_delphes_events.root         # After Delphes (if enabled)
│   │   ├── run_01_tag_1_banner.txt           # Run banner with all settings
│   │   └── ...
│   └── run_02/         # Second run (from subsequent launch)
│       └── ...
├── SubProcesses/       # Generated Fortran code
├── Source/              # Common source code
├── lib/                # Libraries
├── bin/                # Executables
└── HTML/               # Web-based results viewer
```

### Locating Key Output Files

| File | Location | When |
|------|----------|------|
| LHE events (LO) | `Events/run_XX/unweighted_events.lhe.gz` | LO (MadEvent) runs |
| LHE events (NLO) | `Events/run_XX/events.lhe.gz` | NLO (aMC@NLO) runs |
| Pythia8 output | `Events/run_XX/tag_1_pythia8_events.hepmc.gz` | When shower is enabled |
| Delphes output | `Events/run_XX/tag_1_delphes_events.root` | When Delphes is enabled |
| Run banner | `Events/run_XX/run_XX_tag_1_banner.txt` | Always |
| Cross-section | Printed to stdout; also in `Events/run_XX/run_XX_tag_1_banner.txt` | Always |

The exact paths are printed at the end of each `launch` in the terminal output.

---

## Tips for Robust Scripts

1. **Always specify beam energies explicitly** — don't rely on defaults, which may change between versions.
2. **Use `done` to advance through dialogue stages** — even if keeping all defaults.
3. **Use `set` for parameter changes** — this is more portable than editing card files.
4. **Comment your scripts** — lines starting with `#` are ignored.
5. **Set the random seed** for reproducible results: `set run_card iseed 42`.
6. **For e+e- collisions**, remember to set `lpp1 = lpp2 = 0`.
7. **Multiple launches reuse the output directory** — each creates a new `run_XX` subdirectory.

## Gridpacks

A gridpack is a self-contained tarball that packages the pre-compiled process code and optimized integration grids. It allows fast event generation on batch systems or computing clusters without needing a full MadGraph installation.

### Creating a Gridpack

Set `gridpack = True` in the run_card before launching:

```
import model sm
generate p p > z j
output zj_gridpack
launch zj_gridpack
  set run_card gridpack True
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  done
```

MG5 performs the full integration (optimizing the integration grids) and produces a tarball instead of generating events. The gridpack file is located in:

```
zj_gridpack/run_01_gridpack.tar.gz
```

### Using a Gridpack

The gridpack is portable — copy it to any machine (even without MG5 installed) and generate events:

```bash
tar xzf run_01_gridpack.tar.gz
cd madevent
./run.sh 10000 42        # <nevents> <seed>
```

Arguments:
- First argument: number of events to generate
- Second argument: random seed (use different seeds for independent samples)

The output LHE file appears in `Events/GridRun_XXXX/`.

### Workflow for Large-Scale Production

1. **On a local machine**: Create the gridpack (one-time, may take minutes to hours depending on the process).
2. **Copy to cluster**: Transfer the tarball to your batch system nodes.
3. **Submit jobs**: Each job untars and runs `./run.sh <nevents> <seed>` with a unique seed.
4. **Merge**: Combine the output LHE files from all jobs.

This parallelizes event generation efficiently since the expensive integration step is done once.

### Seed Management

Each cluster job must use a **different random seed** to produce independent event samples. Common approaches:

- Use the job array index as the seed: `./run.sh 10000 $SLURM_ARRAY_TASK_ID`
- Use a hash of the job ID
- Use sequential seeds: 1, 2, 3, ...

Using the same seed produces identical events — which is useful for debugging but not for production.

### Limitations

- **Fixed parameters**: The param_card and run_card are frozen at gridpack creation time. To change physics parameters (masses, couplings, beam energy), you must create a new gridpack.
- **No NLO via `gridpack=True`**: The standard `gridpack=True` mechanism does not support NLO processes. See [NLO Gridpack Workflow](#nlo-gridpack-workflow) below for the manual alternative.
- **No shower**: The gridpack produces parton-level LHE events only. Showering and detector simulation must be done separately on the output.
- **Disk space**: Each gridpack can be 100 MB to several GB depending on the process complexity.

### NLO Gridpack Workflow

The standard `gridpack=True` run_card option does not work for NLO processes. Instead, use a manual procedure that builds MINT integration grids and then generates events from them on batch nodes.

**Step 1: Generate the NLO process**

```
import model loop_sm
generate p p > t t~ [QCD]
output my_nlo_proc
```

**Step 2: Build MINT integration grids (integration-only run)**

Launch with `nevents=0` and a positive `req_acc` to run the integration phase without generating events:

```
launch my_nlo_proc
  set run_card nevents 0
  set run_card req_acc 0.01
  done
```

Setting `nevents=0` runs integration only. The `req_acc` parameter (requested accuracy, e.g., 0.01 for 1%) controls when the MINT integrator stops optimizing grids.

**Step 3: Package the process directory**

After integration completes, tar the entire process directory:

```bash
tar czf my_nlo_proc.tar.gz my_nlo_proc/
```

**Step 4: Generate events on batch nodes**

On each batch node, untar the process directory and launch event generation using the pre-built grids. Each job must have its own copy of the unpacked directory and a unique random seed:

```bash
tar xzf my_nlo_proc.tar.gz
cd my_nlo_proc
./bin/aMCatNLO launch --parton --nocompile --only_generation
  set run_card nevents 10000
  set run_card iseed $SLURM_ARRAY_TASK_ID
  done
```

The flags `--parton --nocompile --only_generation` skip compilation, skip MINT integration steps (0 and 1), and go directly to event generation using the existing grids. See [NLO Computations — NLO Launch Flags](nlo-computations.md#nlo-launch-flags) for flag details.

**Important**: Each batch job must operate on its own unpacked copy of the process directory — running multiple jobs in the same directory causes file conflicts.

### Advanced: Modifying a Gridpack

For minor run_card changes (cuts, number of events), you can modify the cards inside the untarred gridpack before running:

```bash
tar xzf run_01_gridpack.tar.gz
cd madevent
# Edit Cards/run_card.dat
./run.sh 10000 42
```

However, changes to the physics model or process require regenerating the gridpack from scratch.

## Run Card Quick Reference

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `ebeam1/2` | 6500 | Beam energies in GeV (half of sqrt(s)) |
| `lpp1/2` | 1 | Beam type: 0=no PDF, 1=proton, -1=antiproton |
| `nevents` | 10000 | Number of unweighted events |
| `iseed` | 0 | Random seed (0=automatic) |
| `pdlabel` / `lhaid` | nn23lo1 / 230000 | PDF label (default: nn23lo1, built-in) and LHAPDF set ID (only used when pdlabel=lhapdf) |
| `dynamical_scale_choice` | -1 | Scale definition (see Scales below) |
| `scalefact` | 1.0 | Multiplier on the chosen scale |
| `ickkw` / `xqcut` | 0 / 0 | Matching scheme and kt cut (GeV) |
| `use_syst` | True | Enable on-the-fly reweighting |

Generation-level cuts: `ptj`, `ptl`, `pta`, `etaj`, `etal`, `drjj`, `drll`. Per-particle cuts via `pt_min_pdg`, `mxx_min_pdg`, `eta_max_pdg` with dict syntax `{PDG: value}`.

## Execution Mode

These are **MadEvent configuration options** (set in `input/mg5_configuration.txt` or via `set` at the MG5 prompt), not run_card parameters. They control how integration and event generation are parallelized.

| Option | Default | Values | Purpose |
|--------|---------|--------|---------|
| `run_mode` | **2** (multicore) | 0=sequential, 1=cluster, 2=multicore | Parallelization mode for integration/event generation |
| `nb_core` | None (auto-detect) | Integer or None | Number of CPU cores for multicore mode; None = use all available cores |

**Important:** `run_mode` and `nb_core` are MadEvent/configuration options. They must be set **before** any `launch` command — either in `input/mg5_configuration.txt`, or via `set` at the MG5 prompt before `launch`. They **cannot** be set inside a launch block (MG5 will issue `WARNING: invalid set command` if you try).

### Setting Execution Mode

In `input/mg5_configuration.txt` (persistent across sessions):

```
run_mode = 2
nb_core = 4
```

Or at the MG5 prompt or in a script, **before** the `launch` command:

```
set run_mode 2
set nb_core 4
launch my_proc
  set run_card nevents 10000
  done
```

### Cluster Mode (run_mode = 1)

For cluster submission, set `cluster_type` (condor, sge, slurm, lsf, pbs) and optional queue/walltime settings in `mg5_configuration.txt`.

**Key points:**
- `run_mode` and `nb_core` **cannot** be set inside a `launch` block — only before `launch` or in `mg5_configuration.txt`.
- Default is `run_mode = 2` (multicore) with auto-detected core count (`nb_core = None`).

## Common Pitfalls

- **Missing `done`**: The script hangs waiting for input. Always end the launch block with `done`.
- **Wrong beam type**: Forgetting `lpp1 = lpp2 = 0` for e+e- collisions uses proton PDFs and gives wrong results.
- **NLO with wrong model**: Using `import model sm` with `[QCD]` triggers an auto-upgrade to `loop_sm` (with an info message). This works — `import model loop_sm` is optional since MG5 handles the upgrade automatically — but explicitly importing `loop_sm` makes the model choice visible.
- **Matching without `@N` tags**: Using `ickkw=1` without explicit `@N` multiplicity tags is discouraged — MadGraph auto-assigns them, but explicit tags improve clarity and reduce the risk of misconfiguration.
