# 28 — Standalone Matrix Element Output

Standalone matrix element output: Fortran/C++ code generation, directory structure, and external evaluation.

## Contents

- [Output Commands](#output-commands)
- [Directory Structure](#directory-structure)
  - [Fortran Standalone (`output standalone`)](#fortran-standalone-output-standalone)
  - [C++ Standalone (`output standalone_cpp`)](#c-standalone-output-standalone_cpp)
- [Compilation and Testing](#compilation-and-testing)
  - [Fortran](#fortran)
  - [C++](#c)
- [Key Subroutines and Functions](#key-subroutines-and-functions)
  - [Fortran Interface](#fortran-interface)
  - [What SMATRIX Returns](#what-smatrix-returns)
  - [C++ Interface](#c-interface)
- [Python Interface via f2py (matrix2py)](#python-interface-via-f2py-matrix2py)
  - [Prerequisites](#prerequisites)
  - [Single-Subprocess Library (matrix2py)](#single-subprocess-library-matrix2py)
  - [Multi-Process Library (all_matrix2py)](#multi-process-library-all_matrix2py)
- [Important Caveats](#important-caveats)
- [MadLoop Standalone (Loop Matrix Elements)](#madloop-standalone-loop-matrix-elements)
  - [Compilation and Testing](#compilation-and-testing)
  - [Function Signature](#function-signature)
- [Use Cases](#use-cases)

## Output Commands

MadGraph provides three output modes. The default (`output`) produces the full MadEvent directory for event generation. The standalone modes produce minimal packages for matrix element evaluation only:

| Command | Language | Description |
|---------|----------|-------------|
| `output <path>` | Fortran | Full MadEvent output (event generation, integration, LHE files) |
| `output standalone <path>` | Fortran | Minimal Fortran package for |M|² evaluation |
| `output standalone_cpp <path>` | C++ | Minimal C++ package for |M|² evaluation |

```
MG5_aMC> import model sm
MG5_aMC> generate p p > t t~
MG5_aMC> output standalone my_standalone
```

For C++:
```
MG5_aMC> output standalone_cpp my_standalone_cpp
```

## Directory Structure

### Fortran Standalone (`output standalone`)

```
my_standalone/
├── Cards/
│   └── param_card.dat            # Model parameters (masses, widths, couplings)
├── Source/
│   ├── MODEL/                    # UFO model Fortran code
│   ├── DHELAS/                   # HELAS library (helicity amplitude routines)
│   └── makefile
├── SubProcesses/
│   ├── P1_gg_ttx/                # Subprocess: g g → t t̄
│   │   ├── matrix.f              # Matrix element subroutine (SMATRIX)
│   │   ├── check_sa.f            # Example driver program
│   │   ├── nexternal.inc         # Number of external particles
│   │   ├── pmass.inc             # Particle masses
│   │   └── Makefile
│   ├── P2_uux_ttx/               # Subprocess: u ū → t t̄
│   │   ├── matrix.f
│   │   ├── check_sa.f
│   │   └── ...
│   └── ...                       # One directory per subprocess
└── lib/                          # Compiled libraries
```

Subprocess directories are named `P<N>_<name>` where `N` starts from 1. Each directory corresponds to a distinct initial-state parton combination (e.g., `gg`, `uux`, `ddx`). The process `p p > t t~` generates separate subprocess directories for each contributing partonic channel.

If you use `@N` tags in the `generate` command (e.g., `generate g g > z z @42`), the subprocess directory will be named accordingly (e.g., `P42_gg_zz`).

### C++ Standalone (`output standalone_cpp`)

```
my_standalone_cpp/
├── Cards/
│   └── param_card.dat
├── src/
│   ├── Parameters_sm.h / .cc     # Model parameters
│   ├── HelAmps_sm.h / .cc        # Helicity amplitude routines
│   ├── rambo.h / .cc             # RAMBO phase-space generator
│   └── Makefile
├── SubProcesses/
│   ├── P1_Sigma_sm_gg_ttx/
│   │   ├── CPPProcess.h / .cc    # Matrix element class
│   │   ├── check_sa.cpp          # Example driver program
│   │   └── Makefile
│   └── ...
└── lib/
```

C++ subprocess directories include a `Sigma_<model>` infix in the name (e.g., `P1_Sigma_sm_gg_ttx`).

## Compilation and Testing

### Fortran

```bash
# Compile and run the example driver for a specific subprocess
cd my_standalone/SubProcesses/P1_gg_ttx
make check
./check
```

The `make check` target compiles `check_sa.f` into the `check` executable. This evaluates |M|² at a RAMBO-generated random phase-space point and prints the result. Use it to verify the code compiles and runs correctly.

**Important:** Use `make check` explicitly — the default `make` target in the subprocess directory builds the f2py Python wrappers, not the check executable.

### C++

```bash
# First compile the source libraries
cd my_standalone_cpp/src
make

# Then compile and run the subprocess check
cd ../SubProcesses/P1_Sigma_sm_gg_ttx
make check
./check
```

## Key Subroutines and Functions

### Fortran Interface

The generated Fortran code provides these entry points in `matrix.f`:

| Entry Point | Type | Signature | Description |
|-------------|------|-----------|-------------|
| `SMATRIX` | Subroutine | `CALL SMATRIX(P, ANS)` | Returns |M|² summed over all helicities and colors, divided by the averaging/symmetry factor IDEN (see below). |
| `MATRIX` | Function | `MATRIX(P, NHEL, IC)` returns `REAL*8` | Returns |M|² for a specific helicity configuration `NHEL` and particle-flow array `IC`. Color-summed (via the color matrix CF) and divided by DENOM — but **not** divided by IDEN. |

**MATRIX function usage:**
```fortran
REAL*8 MATRIX
REAL*8 P(0:3, NEXTERNAL)
INTEGER NHEL(NEXTERNAL)   ! Helicity array: +1 or -1 per particle
INTEGER IC(NEXTERNAL)     ! Particle flow direction array (set all to 1 for standard evaluation)
REAL*8 result
result = MATRIX(P, NHEL, IC)
```

`MATRIX` is a **function** (not a subroutine) — you must assign its return value. The `IC` array controls the particle flow direction in HELAS wavefunction calls: each `IC(i)` multiplies the NSV (flow-direction) argument of the HELAS routine for particle `i` (e.g., `CALL VXXXXX(P(0,1),ZERO,NHEL(1),-1*IC(1),W(1,1))`). With `IC(i) = +1`, the standard initial/final-state assignment from the process definition is used. With `IC(i) = -1`, the flow is reversed (used internally for crossing symmetry). **For standalone usage, always set all IC entries to +1.**

**Momentum array format:**
```fortran
REAL*8 P(0:3, NEXTERNAL)
```
- First index: 4-momentum component — `P(0,i)` = E, `P(1,i)` = px, `P(2,i)` = py, `P(3,i)` = pz
- Second index: particle number (1 to NEXTERNAL), ordered as in the process definition
- Units: GeV
- Momenta must satisfy on-shell conditions and 4-momentum conservation

### What SMATRIX Returns

SMATRIX computes:

```
              1         1
SMATRIX  =  ---- × ---------- × sum_hel sum_{i,j} CF(j,i) * JAMP(j) * DCONJG(JAMP(i))
             IDEN     DENOM
```

where:

- **JAMP(i)** are the color-ordered partial amplitudes (color flows), each being a linear combination of Feynman diagram amplitudes.
- **CF(j,i)** is the color matrix encoding the interference between color flows `j` and `i`.
- **DENOM** is an `INTEGER` scalar — a common denominator factor that arises from expressing the color matrix CF in integer form. The actual color interference coefficient is `CF(j,i) / DENOM`. The value is determined by the color algebra (e.g., `DENOM = 3` for `g g > t t~`). DENOM is **not** related to initial-state color averaging. It divides the entire color-summed result as a single scalar: `MATRIX = MATRIX / DENOM`.
- **IDEN** is an `INTEGER` scalar — the combined averaging and symmetry factor that includes **all three** of the following:
  1. **Initial-state color averaging** (e.g., 1/(Nc² - 1) per gluon = 1/8, 1/Nc per quark = 1/3)
  2. **Initial-state helicity averaging** (e.g., 1/2 per massless fermion or gluon)
  3. **Identical-particle symmetry factor** for the final state (e.g., 1/2! for two identical gluons)

**Example IDEN values:**

| Process | Color avg | Helicity avg | Identical particle | IDEN |
|---------|-----------|-------------|-------------------|------|
| `g g > t t~` | 8 × 8 = 64 | 2 × 2 = 4 | 1 | 256 |
| `g g > g g` | 8 × 8 = 64 | 2 × 2 = 4 | 2 | 512 |
| `u u~ > t t~` | 3 × 3 = 9 | 2 × 2 = 4 | 1 | 36 |
| `e+ e- > t t~` | 1 × 1 = 1 | 2 × 2 = 4 | 1 | 4 |

You can verify IDEN for any process by inspecting the generated `matrix.f` file. IDEN is declared as `INTEGER IDEN` and initialized via a DATA statement — search for `DATA IDEN` near the top of the SMATRIX subroutine (e.g., `DATA IDEN/256/` for `g g > t t~`).

**Key point:** SMATRIX does **not** include the flux factor. For a 2 → N cross-section using the SMATRIX output:

$$\sigma = \frac{1}{2\hat{s}} \int \text{SMATRIX} \times d\Phi_N$$

where $2\hat{s}$ is the Møller flux factor for massless initial states ($2\hat{s} = 2 E_1 \cdot 2 E_2 \cdot |v_1 - v_2|$ in the center-of-mass frame). SMATRIX already includes the IDEN division, so no further averaging factors are needed.

### C++ Interface

The `CPPProcess` class in `CPPProcess.h` / `.cc` provides:

```cpp
#include "CPPProcess.h"
#include <vector>

CPPProcess process;
process.initProc("../../Cards/param_card.dat");

// Momenta: vector of double pointers, one per external particle
// Each pointer points to a 4-element array [E, px, py, pz]
int nexternal = process.nexternal;
std::vector<double*> momenta(nexternal);
for (int i = 0; i < nexternal; i++)
    momenta[i] = new double[4];  // [E, px, py, pz]

// ... fill momenta[i][0..3] for each particle ...

process.setMomenta(momenta);
process.sigmaKin();   // Evaluate matrix element

// Retrieve results
const double* matrix_elements = process.getMatrixElements();
double me2 = matrix_elements[0];  // |M|^2 for this subprocess

// Clean up
for (int i = 0; i < nexternal; i++)
    delete[] momenta[i];
```

**Key methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `initProc(param_card_path)` | `void initProc(string)` | Initialize model parameters from param_card |
| `setMomenta(momenta)` | `void setMomenta(vector<double*>&)` | Set external particle momenta |
| `sigmaKin()` | `void sigmaKin()` | Compute the matrix element |
| `getMatrixElements()` | `const double* getMatrixElements()` | Get pointer to computed |M|² values |
| `getMasses()` | `vector<double> getMasses()` | Get particle masses (for phase-space generation) |

**Important:** `setMomenta` takes a `vector<double*>&` (reference to a vector of double pointers), not a contiguous 2D array. See `check_sa.cpp` in the subprocess directory for a complete working example.

**Thread safety warning:** The default C++ standalone output uses a global static pointer for the model instance (`Parameters_sm` singleton), making it **not thread-safe**. If you need multithreaded evaluation, remove all `static` keywords from `CPPProcess.cc` and ensure each thread has its own `CPPProcess` instance.

## Python Interface via f2py (matrix2py)

The Fortran standalone code can be compiled into a Python-importable shared library using `f2py` (part of NumPy).

### Prerequisites

- `numpy` (provides `f2py`)
- `python-devel` / `python3-dev` system package (provides `Python.h`)
- A Fortran compiler (`gfortran`)

### Single-Subprocess Library (matrix2py)

```bash
cd my_standalone/SubProcesses/P1_gg_ttx
make matrix2py.so
```

This produces `matrix2py.so` (or `matrix2py.cpython-*.so`) importable from Python.

**Usage:**

```python
import matrix2py

# Step 1: Initialize model parameters (REQUIRED before any evaluation)
matrix2py.py_initialisemodel('../../Cards/param_card.dat')

# Step 2: Define momenta in (E, px, py, pz) format per particle
# Order must match the process definition: g g > t t~
# p[i] = [E, px, py, pz] for particle i
p = [[500.0,  0.0,   0.0,  500.0],    # incoming g
     [500.0,  0.0,   0.0, -500.0],    # incoming g
     [500.0,  110.9, 444.8, -199.6],   # outgoing t
     [500.0, -110.9, -444.8, 199.6]]   # outgoing t~

# Step 3: Transpose momenta (Fortran and Python use different array ordering)
def invert_momenta(p):
    """Transpose momenta from Python [particle][mu] to Fortran [mu][particle] order."""
    new_p = []
    for i in range(len(p[0])):
        new_p.append([0] * len(p))
    for i, onep in enumerate(p):
        for j, x in enumerate(onep):
            new_p[j][i] = x
    return new_p

P = invert_momenta(p)

# Step 4: Evaluate |M|^2
alphas = 0.118   # Strong coupling constant (you must supply this)
nhel = -1        # -1 = sum over all helicities; >= 0 selects a specific helicity
me2 = matrix2py.py_get_value(P, alphas, nhel)
print(f'|M|^2 = {me2}')
```

**Key functions in `matrix2py`:**

| Function | Call Syntax | Description |
|----------|-------------|-------------|
| `py_initialisemodel` | `matrix2py.py_initialisemodel('../../Cards/param_card.dat')` | Load model parameters. **Must be called once before any evaluation.** |
| `py_get_value` | `matrix2py.py_get_value(P, alphas, nhel)` → `float` | Evaluate |M|². `P` is the transposed momentum array, `alphas` is αs, `nhel = -1` sums over helicities. |

**Critical:** The momentum array must be transposed because Fortran uses column-major ordering while Python/C use row-major ordering. The `invert_momenta` function above handles this. Alternatively, use `numpy` with Fortran ordering:

```python
import numpy as np
p_array = np.array(p, dtype=np.float64, order='F')
```

### Multi-Process Library (all_matrix2py)

To combine all subprocesses into a single Python-accessible library, use the `--prefix=int` flag:

```
MG5_aMC> generate p p > t t~
MG5_aMC> output standalone my_dir --prefix=int
```

Compile:

```bash
cd my_dir/SubProcesses
make all_matrix2py.so
```

**Usage:**

```python
import all_matrix2py

# Initialize model
all_matrix2py.initialise('../Cards/param_card.dat')

# Define PDG codes for the external particles
pdgs = [21, 21, 6, -6]   # g g > t t~

# Process ID: use -1 for automatic selection, or the @N value if you used it
proc_id = -1

# Momenta in transposed format [mu][particle] (see invert_momenta above)
p = [[500.0, 0.0, 0.0, 500.0],
     [500.0, 0.0, 0.0, -500.0],
     [500.0, 110.9, 444.8, -199.6],
     [500.0, -110.9, -444.8, 199.6]]

def invert_momenta(p):
    new_p = []
    for i in range(len(p[0])):
        new_p.append([0] * len(p))
    for i, onep in enumerate(p):
        for j, x in enumerate(onep):
            new_p[j][i] = x
    return new_p

P = invert_momenta(p)

alphas = 0.118
scale2 = 0.0     # Renormalization scale squared (set 0 for tree-level)
nhel = -1        # -1 = sum over all helicities

me2 = all_matrix2py.smatrixhel(pdgs, proc_id, P, alphas, scale2, nhel)
print(f'|M|^2 = {me2}')
```

**Key function:**

| Function | Parameters | Description |
|----------|------------|-------------|
| `smatrixhel` | `(pdgs, proc_id, p, alphas, scale2, nhel)` | Evaluate |M|² for the subprocess matching the given PDG codes. `proc_id = -1` for automatic selection. |

The `all_matrix2py` library automatically routes to the correct subprocess based on the provided PDG codes. If multiple subprocesses share the same external particle content (distinguished by `@N` tags), use `proc_id` to select the correct one.

## Important Caveats

**No αs running:** The standalone output does **not** include a running coupling routine. You must supply the value of αs externally at the desired scale. If you have LHAPDF available, you can use its Python interface:

```python
import lhapdf
pdf = lhapdf.mkPDF('NNPDF23_lo_as_0130_qed', 0)
scale = 91.188  # e.g., the Z mass in GeV
alphas = pdf.alphasQ(scale)  # running alpha_s at the given scale
```

(LHAPDF may require setting `PYTHONPATH` to include the LHAPDF Python site-packages directory, and the PDF set must be installed.)

**No PDFs:** The standalone output does not include PDF evaluation. If you are computing a hadronic cross-section, you must supply parton distribution functions yourself (e.g., via LHAPDF).

**No run_card:** The `run_card.dat` is **not used** in standalone mode. Parameters set in the run_card (like `dynamical_scale_choice`) have no effect. All physics input comes from `param_card.dat` and the externally supplied αs value.

**Parameter initialization required:** You must call `py_initialisemodel()` (Python matrix2py) or `initialise()` (Python all_matrix2py) or the corresponding initialization routine (Fortran `check_sa.f` handles this) or `initProc()` (C++) before evaluating any matrix element. This reads the param_card and computes all model couplings.

**Momentum conventions:**
- 4-vector format: (E, px, py, pz) — energy first
- Units: GeV
- Particle ordering must match the process definition exactly
- Momenta must be on-shell and satisfy 4-momentum conservation
- For Fortran array: `P(0:3, NEXTERNAL)` where index 0 = energy

**Flux factor not included:** The returned value from SMATRIX does not include the flux factor. For a 2 → N cross-section:

$$\sigma = \frac{1}{2\hat{s}} \int \text{SMATRIX} \times d\Phi_N$$

SMATRIX already divides by IDEN (which includes color averaging, helicity averaging, and identical-particle symmetry), so no further averaging factors are needed beyond the flux factor.

## MadLoop Standalone (Loop Matrix Elements)

For one-loop virtual corrections, MadGraph produces a MadLoop standalone library:

```
MG5_aMC> generate g g > z z [virt=QCD] @42
MG5_aMC> output my_loop_standalone
```

The `output` step compiles all necessary code. No `launch` step is needed (or supported) for `[virt=QCD]` standalone output — the output is a standalone evaluator, not an event-generation directory.

### Compilation and Testing

```bash
# Navigate to the subprocess directory (note: @42 tag → P42)
cd my_loop_standalone/SubProcesses/P42_gg_zz
make check
./check
```

**Runtime note:** MadLoop links against external libraries (e.g., Ninja, CutTools). You may need to set `LD_LIBRARY_PATH` to include the HEPTools library directory (e.g., `export LD_LIBRARY_PATH=/path/to/MG5/HEPTools/lib:$LD_LIBRARY_PATH`) before running `./check`.

To build a static library:
```bash
cd my_loop_standalone/SubProcesses
make OLP_static    # produces lib/libMadLoop.a
```

### Function Signature

```fortran
CALL ML5_<ID>_SLOOPMATRIX(P, RESULT)
CALL ML5_<ID>_SLOOPMATRIXHEL_THRES(P, HEL_ID, RESULT, REQ_ACC, PREC_FOUND, RETURNCODE)
```

where `<ID>` corresponds to the `@N` tag used during process generation (e.g., `ML5_42_SLOOPMATRIX` for `@42`).

**Result array:** `REAL*8 RESULT(0:3, 0:N_COUPLING_ORDERS)`

| Index | Content |
|-------|---------|
| 0 | Born contribution |
| 1 | Virtual finite part |
| 2 | Single pole (1/ε) coefficient |
| 3 | Double pole (1/ε²) coefficient |

The second index `J` represents coupling order combinations (`J=0` is the sum of all contributions).

**Runtime requirement:** MadLoop needs access to `MadLoop5_resources/` at execution time. Either run from within the `SubProcesses` directory, create a symlink, or call `SETMADLOOPPATH(PATH)` before the first evaluation.

## Use Cases

- **Matrix Element Method (MEM):** Evaluate |M|² for observed events to discriminate signal from background.
- **Reweighting:** Reweight events from one parameter point to another by computing |M|² ratios.
- **Custom phase-space integration:** Build your own integrator over the matrix element.
- **Interfacing with external frameworks:** Export matrix elements to tools like MoMEMta, MadWeight, or custom analysis code.
- **Validation:** Compare MadGraph matrix elements against analytical calculations.
