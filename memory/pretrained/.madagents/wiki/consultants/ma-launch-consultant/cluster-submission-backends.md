---
description: cluster.py — Cluster base + MultiCore thread-queue backend (worker/queue/GPU dispatch, packet chaining, fail-fast), from_name scheduler registry + PBS specifics, multiple_try retry, configure_run_mode instantiation (run_mode 0 = MultiCore(1), plugin fallback), need_transfer/submit2 staging, wait/control, modify_interface hook.
---

# Cluster submission (cluster.py)

Cites: `$MADGRAPH_INSTALL/madgraph/various/cluster.py` (v3.7.1).

## Backend registry (2508-2513)
`from_name = {'condor':CondorCluster, 'pbs':PBSCluster, 'sge':SGECluster, 'lsf':LSFCluster, 'ge':GECluster, 'slurm':SLURMCluster, 'htcaas':HTCaaSCluster, 'htcaas2':HTCaaS2Cluster}`. `onecore = MultiCore(1)` (2512) is a singleton thread for simple bash jobs. `MultiCore` (641) is the local multi-thread backend (not in `from_name`; selected by run_mode==2).

## run_mode vs cluster_type
- `run_mode`: 0=single, 1=cluster, 2=multicore (set via config `run_mode` or launch flags `--cluster` / `--nb_core=N` / `--multicore`). Mapping confirmed by MELauncher/generate_events (launch-entrypoints page).
- `cluster_type` (config key) selects which `from_name` backend is used when run_mode==1.

## configure_run_mode — where run_mode becomes a live `self.cluster` (common_run_interface.py:3671-3713)
The actual instantiation link. `configure_run_mode(run_mode)` sets `self.cluster_mode = run_mode` and `self.options['run_mode'] = run_mode`, then builds `self.cluster`:
- **run_mode 0 or 2** (3687-3692): `self.cluster = cluster.MultiCore(**self.options)` with `nb_core` forced to 1 for mode 0 (3683) or to `multiprocessing.cpu_count()` for mode 2 when `nb_core` is unset (3679-3680). So **single-core (run_mode 0) is `MultiCore` with one core, NOT a distinct backend** — there is no separate serial cluster class. Reused if an existing `MultiCore` already has the right `nb_core`.
- **run_mode 1** (3695-3713): `cluster_name = options['cluster_type']`; if in `from_name`, `self.cluster = from_name[cluster_name](**opt)` (prints `using cluster: <name>`). Else tries a **plugin cluster**: `misc.from_plugin_import(plugin_path, 'new_cluster', cluster_name)` (3706-3708) — a plugin can register a `new_cluster` dict keyed by name. If neither resolves, raises `InvalidCmd("<name> is not recognized as a supported cluster format.")`.

Called from launch-flag handlers (`--cluster`/`--multicore`/`--nb_core`, common_run 855-874), from `switch_mode` run_mode/nb_core changes (3656), and at 4154. `self.cluster_mode` (used by `monitor`/`launch_job` to decide submit-vs-run) is exactly this `run_mode` int.
- Config keys (`$MADGRAPH_INSTALL/input/mg5_configuration.txt`): `cluster_type`, `cluster_queue`, `cluster_size`, `cluster_walltime` (minutes for slurm, seconds for condor), `cluster_temp_path`, `cluster_local_path`, `cluster_status_update`, `cluster_nb_retry`, `cluster_retry_wait`, `cluster_requirement`, `cluster_vacatetime`, `enforce_shared_disk` (Condor only), `nb_core` (MultiCore). Defaults for these are registered in `Cluster.__init__` (cluster.py:99-134) — read fresh there.

## Cluster base class (93-615)
- `__init__` (99-134): registers defaults for `cluster_queue`, `temp_dir`, `cluster_status_update` (a (long,short) tuple), `nb_retry`, `cluster_retry_wait` — read the literals at the coordinate.
- `submit` (136): abstract — each backend overrides.
- `submit2` (143, `@store_input()`): "NO SHARE DISK" path. If no `temp_dir` or no input/output files, falls back to plain `submit` (157-166). Else writes a wrapper bash script that copies `input_files` to `$temp_dir/run$JOBID`, runs the program there, copies `output_files` back (174-213).
- `cluster_submit` (217): wraps submit2 + packet bookkeeping (do not override except DAG).
- `control` (242): abstract `(idle, run, finish, fail)` per backend.
- `wait` (298-393): **base scheduler-polling loop** (used by the real-scheduler backends, NOT MultiCore — MultiCore overrides wait, see below). Adaptive cadence between the `cluster_status_update` short and long intervals (the (long,short) tuple from `__init__`, cluster.py:99-134); switches to long mode after a `change_at` iteration count when idle<run; ctrl-C forces an update. Raises `ClusterManagmentError` on any `fail` (340).
- `launch_and_wait` (530-597): submit one job, poll `control_one_job` until not R/I, with check_termination/resubmit logic; optional stderr->stdout merge.
- `modify_interface(run_interface)` (608-615): **base is a no-op (returns)**. Backends (e.g. Condor) override to mutate run_card/options at treatcards time. Called from `do_treatcards` and `configure_directory`.

## need_transfer (84-91)
Returns False unless `run_mode==1` OR `cluster_temp_path` is set. Controls whether input files (e.g. MadLoop5_resources tarball) are compressed/staged. So a multicore (run_mode==2) run with no temp path does NOT stage/transfer.

## MultiCore internals (641-966) — the local thread-queue backend (THE default for most launches)
`MultiCore` is NOT in `from_name`; it is the run_mode 0/2 backend (and `onecore = MultiCore(1)` singleton). It overrides `submit`, `wait`, `remove`, `launch_and_wait` — its `wait` is a thread-queue loop, NOT the base Cluster.wait scheduler-polling loop.
- **nb_core resolution** (662-667): from `opt['nb_core']`, else `args[0]` if int, else 1.
- **Worker/queue model** (699-787): `start_demon` spawns daemon threads up to `nb_core`; each `worker` pulls `(tag, exe, arg, opt)` off `self.queue`, runs it (subprocess for a str exe, or calls the Python fct directly if not a str — note: in-process fct calls are single-threaded, NO parallelism, 752-756), pushes the tag onto `self.done`.
- **Fail-fast** (746-751): a subprocess returncode NOT in `[0, 143, -15]` (143/-15 = SIGTERM, treated as clean) sets `stoprequest` and calls `self.remove(fail_msg)` — "Stop all computation". One failed job aborts the whole MultiCore batch; the error surfaces from `wait` (928-935 raises `self.fail_msg`).
- **`__debug__` re-raise** (773-774): under non-`-O` Python a worker exception is re-raised with traceback inside the worker; under `-O` it is swallowed to a warning. (`-O`/`__debug__` cross-slice seam.)
- **GPU dispatch** (682-697, 699-711): reads `MG5_GPU_VISIBLE_DEVICES` (must be a 2-element comma list giving get_var,set_var) else falls back to `NVIDIA/CUDA`, `ROCR/HIP` `_VISIBLE_DEVICES`; logs "Found N GPUs". `start_demon` round-robins GPUs across workers: `this_gpu_idx = len(self.demons) % gpus_count`, sets the per-worker env `set_var` to one device. So MultiCore is GPU-aware and pins one GPU per worker thread cyclically.
- **wait loop** (851-966): computes `Idle = queue.qsize()`, `Done = nb_done + done.qsize()`, `Running = max(0, submitted.qsize() - Idle - Done)` (887-889) — counts, not a scheduler query. Wakeup is lock-based (`self.lock.wait(300)`, a worker `lock.set()` releases the main thread) with a `time.sleep` fallback ramping `min(sleep+2, 180)`s (914-924). On exit resets all queues unless `keep_thread`.
- **Packet mechanism** (617 `class Packet`; wait 868-881): jobs can be grouped into a packet via `id_to_packet`; when the last job of a packet finishes (`packet.remove_one()==0`), `wait` submits the packet's follow-up `fct` (`self.submit(packet.fct, packet.args)`). This is how survey/refine chain a post-packet function (e.g. combine-an-iteration) after a group of channel jobs completes — the chaining is in the local backend, not the flow command.
- `launch_and_wait` (815-822): MultiCore-specific — just `misc.call` (blocking), bypassing the queue.

## multiple_try retry decorator (cluster.py:50 = misc.multiple_try, misc.py:452)
Every scheduler backend's `submit`/`control`/`control_one_job` is `@multiple_try()`-decorated. `multiple_try(nb_try=<n>, sleep=<s>)` (defaults at misc.py:452 — read fresh): retries `nb_try` times with **linear backoff** `sleep*(i+1)` between tries; re-raises `KeyboardInterrupt` immediately; logs "Start waiting for update" once. Final failure raises `my_error.__class__('[Fail N times] ...')` — except under `-O` (`if __debug__: raise` followed by the wrapped raise) the bare `raise` with no active exception is itself buggy. So a flaky scheduler is retried a bounded number of times before the job is declared failed.

## PBSCluster specifics (1351-1496) — representative scheduler backend
- Class attrs: `maximum_submited_jobs` (value at cluster.py:52 — read fresh); status tags `idle=['Q']`, `running=['T','E','R']`, `complete=['C']`; `job_id='PBS_JOBID'`.
- `submit` (1363): if `len(submitted_ids) > maximum_submited_jobs`, BLOCKS in `wait` until slots free (1369-1371) — a built-in submission throttle. Builds `qsub -o <stdout> -N <jobname> -e <stderr> -V [-q <queue>]` (queue only if `cluster_queue` set and != 'None'); pipes a `cd <cwd>; ./<prog> <args>` script to qsub stdin; parses the numeric job id from `output.split('.')[0]`; raises `ClusterManagmentError` if non-digit or returncode!=0.
- `control_one_job` (1419): `qstat <id>`; "cannot connect"/"cannot read reply" -> `ClusterManagmentError('server disconnected')`; "Unknown" -> 'F'; maps status field [4] via idle/running tags. (Other backends differ in qsub/qstat flags + tag sets; the shape is the same.)

## Cautions
- `cluster_walltime` units differ by backend (minutes for slurm, seconds for condor; comment says unsupported for others — config line 136).
- Base `modify_interface` is a no-op; any run_card auto-adjustment "by the cluster" comes from a backend override, not the base.
- `submit2` only does file-staging when `temp_dir` is set AND input/output files are passed; otherwise it silently degrades to `submit` (shared-disk assumption).
- `enforce_shared_disk` is documented as Condor-only.
