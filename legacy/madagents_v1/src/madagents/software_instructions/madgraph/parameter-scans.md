# 21 — Parameter Scans

MadGraph has a built-in mechanism for scanning over parameter values in both the run card and the param card. This generates multiple runs automatically, each with different parameter values, and produces a summary table of cross-sections.

## Contents

- [Run Card Scans (`scan:` Syntax)](#run-card-scans-scan-syntax)
  - [Multi-Parameter Scans](#multi-parameter-scans)
  - [Correlated Scans](#correlated-scans)
- [Param Card Scans](#param-card-scans)
- [Complete Example](#complete-example)
- [Output and Summary](#output-and-summary)
- [Practical Tips](#practical-tips)
- [Known Issue: Thread Leak with Sequential `launch` Commands](#known-issue-thread-leak-with-sequential-launch-commands)
  - [Symptom](#symptom)
  - [Root Cause](#root-cause)
  - [Solutions (in order of preference)](#solutions-in-order-of-preference)
  - [Example: Converting Sequential Launches to `scan:` Syntax](#example-converting-sequential-launches-to-scan-syntax)
  - [Pipeline Robustness](#pipeline-robustness)
  - [HPC Considerations](#hpc-considerations)

## Run Card Scans (`scan:` Syntax)

To scan over a run card parameter, replace its value with the `scan:` keyword followed by a Python list expression:

```
scan:[6500, 7000, 7500]  = ebeam1  ! scan beam energy
```

MG5 evaluates the expression after `scan:` using Python's `eval()`, so any valid Python expression that produces a list is accepted:

```
scan:[100, 200, 300, 500, 1000]  = ebeam1           ! explicit list
scan:range(1000, 10001, 1000)    = ebeam1            ! range from 1000 to 10000 in steps of 1000
scan:[10**i for i in range(2,5)] = nevents           ! list comprehension: [100, 1000, 10000]
```

### Multi-Parameter Scans

Multiple parameters can be scanned simultaneously. MG5 takes the **Cartesian product** of all scan values, generating one run for each combination:

```
scan:[6500, 7000]  = ebeam1   ! 2 values
scan:[170, 172.5, 175]  = ... ! 3 values in param_card
```

This produces 2 x 3 = 6 runs.

### Correlated Scans

To scan multiple parameters **together** (same index varies simultaneously, not as a Cartesian product), use the same scan ID number:

```
scan1:[6500, 7000]  = ebeam1   ! scan group 1
scan1:[6500, 7000]  = ebeam2   ! scan group 1 (same index)
```

Parameters with the same scan ID number are iterated in lockstep. Parameters with different scan IDs (or no ID) form independent dimensions of the Cartesian product.

## Param Card Scans

The same `scan:` syntax works in the param_card. To scan over a physics parameter (e.g., the top mass):

```
BLOCK MASS
  6  scan:[170.0, 172.5, 175.0]  # top mass scan
```

Note: Run card scans and param card scans cannot be used simultaneously in the same launch. MG5 will raise an error if `scan` is present in both cards.

## Complete Example

A script scanning the top mass:

```
import model sm
generate p p > t t~
output ttbar_scan
launch ttbar_scan
  set run_card ebeam1 6500
  set run_card ebeam2 6500
  set run_card nevents 10000
  set param_card mass 6 scan:[170.0, 172.5, 175.0]
  done
```

This generates three separate runs, one for each top mass value. Each run appears as a separate subdirectory under `Events/` (e.g., `run_01`, `run_01_scan_02`, `run_01_scan_03`).

## Output and Summary

After a scan completes, MG5 produces a summary table showing the cross-section for each parameter point. The table is stored in the `Events/` directory and lists:

- Run name
- Parameter values for that scan point
- Cross-section and error

Each scan point also gets a `params.dat` file in its event directory recording the parameter values used.

## Practical Tips

1. **Seed management**: Each scan point uses a different random seed automatically.
2. **Grid reuse**: Subsequent scan points can benefit from integration grids optimized by earlier points, making scans faster than running each point independently.
3. **Number of events**: The `nevents` setting applies to each scan point individually.
4. **Cross-section only**: If you only want cross-sections (no events), combine with the `done` mechanism and check the summary table.

## Known Issue: Thread Leak with Sequential `launch` Commands

### Symptom

When a MadGraph script issues many sequential `launch` commands (typically more than ~25–50, depending on `nb_core` and system thread limits), the process crashes with:

```
RuntimeError: can't start new thread
```

or:

```
thread.error: can't start new thread
```

The error usually originates in `cluster.py` or `madevent_interface.py` when MadGraph tries to spawn a new daemon thread.

### Root Cause

In multicore mode (`run_mode = 2`, the default), each `launch` creates a `MultiCore` thread pool for parallel integration. These threads are **not joined or terminated** after the run completes. Across many sequential launches in the same `mg5_aMC` process, threads accumulate until the system's per-process or per-user thread limit (`ulimit -u`) is exhausted.

This is tracked in Launchpad bugs [#1784866](https://bugs.launchpad.net/mg5amcnlo/+bug/1784866) and [#1979966](https://bugs.launchpad.net/mg5amcnlo/+bug/1979966).

### Solutions (in order of preference)

| Solution | Details |
|---|---|
| **Upgrade MadGraph** | The thread leak was fixed in **v2.9.13** (LTS) and **v3.4.2** (feature branch). |
| **Use `scan:` syntax** | Replace repeated `launch` commands with a single launch using `scan:` syntax (see above). This avoids per-launch thread overhead entirely and is the recommended approach for parameter sweeps. |
| **Separate processes** | Run each parameter point as a separate `mg5_aMC` invocation (e.g., via a bash loop). Each process gets a fresh thread pool. |
| **Reduce `nb_core`** | Set `nb_core` to a small value (e.g., 1 or 2) via `set nb_core 1` before `launch`, or in `mg5_configuration.txt`. This is a **configuration option**, not a run_card parameter. |
| **Set `run_mode = 0`** | Forces sequential (single-core) mode, eliminating multithreading entirely. Set via `set run_mode 0` before `launch`, or in `mg5_configuration.txt`. Slowest option but avoids the leak completely. |

### Example: Converting Sequential Launches to `scan:` Syntax

**Problematic** — many sequential `launch` calls (will crash after ~25–50 launches):

```
import model sm
generate p p > t t~
output ttbar_points

launch ttbar_points
  set param_card mass 6 170.0
  done

launch ttbar_points
  set param_card mass 6 172.5
  done

launch ttbar_points
  set param_card mass 6 175.0
  done
# ... repeated for many more points
```

**Recommended** — single launch with `scan:` syntax:

```
import model sm
generate p p > t t~
output ttbar_scan
launch ttbar_scan
  set param_card mass 6 scan:[170.0, 172.5, 175.0]
  done
```

For correlated multi-parameter scans, use numbered scan labels to iterate parameters in lockstep:

```
launch my_output
  set param_card mass 9000006 scan1:[500, 750, 1000, 1500]
  set param_card decay 9000006 scan1:[50, 75, 100, 150]
  done
```

### Pipeline Robustness

When running parameter scans in automated pipelines, set `crash_on_error` to ensure MadGraph returns a non-zero exit code on failure:

```
set crash_on_error True
launch my_output
  ...
```

This is a MG5 interface option set via `set` before `launch` (not a run_card parameter). Without it, MadGraph may silently continue or exit with code 0 even after a thread-related crash, making failures hard to detect in batch systems (SLURM, HTCondor, PBS).

### HPC Considerations

On HPC systems with strict per-user thread/process limits, the thread leak manifests sooner. The `scan:` syntax or separate-process approach is strongly recommended for large parameter sweeps on clusters.

**Details ->** [Troubleshooting](troubleshooting.md) | [Scripted Execution](scripted-execution.md)
