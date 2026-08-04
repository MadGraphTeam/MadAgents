---
description: Gridpack refine execution — readonly (RO) cwd-redirection of all paths, nprocs MultiCore vs onecore path, check_events recursive resubmit with events.lhe.previous carry-over, and the self.gran granularity typo. v3.7.1.
---

# Gridpack refine execution (readonly / RO mode) (v3.7.1)

File: `$MADGRAPH_INSTALL/madgraph/madevent/gen_ximprove.py`, class `gen_ximprove_gridpack` (1826). Complements refine-gen-ximprove.md (class dispatch + stochastic `find_job_for_event`); this page is the **execution side**: how a gridpack actually runs its refine jobs, and the read-only relocation that lets a gridpack run from a deployed tarball without writing back into the install tree.

## Construction options (`__init__`, 1840-1862)
Reads from `opts`: `ngran` (granularity, default -1→1 at 1856-1857), `nprocs` (default 1), `readonly` (default False), `maxevts` (sets `max_request_event` only if `nprocs>1`, 1856). After super-init:
- `nprocs>1` → `self.combining_job = 0` (each channel its own script); else `sys.maxsize` (all channels one script, 1859-1862).
- Class constants (read at 1828-1833): a single min-iter, the gridpack max-iter + event caps, and `gen_events_security` set to **no over-generation** — effectively un-split (a very large request cap) unless `nprocs>1` overrides via `maxevts`.

### CAUTION — `self.gran` typo (1847) drops user granularity
```python
if 'ngran' in opts:
    self.gran = opts['ngran']   # writes self.gran, NOT self.ngran
```
Every consumer reads `self.ngran` (1856, 1886, 1888, 1910); `grep "self\.gran\b"` returns ONLY line 1847 — no reader exists, and the base/`v4`/`gen_ximprove` `__init__`s contain no `ngran` reference (it appears only inside this class, 1842-1910), so `super().__init__` cannot rescue it. `self.ngran` stays at its `-1`→`1` default (1856-1857). The user-requested granularity is silently ignored — granularity is always 1 in practice unless the caller sets `self.ngran` directly.

**Verified sibling dead-write** (same case-mismatch shape, distinct file): `combine_grid.py` defines `self.oneFail` (26) and the only reader is `self.oneFail` (377), but two write sites use lowercase `self.onefail` (combine_grid.py:73, gen_ximprove.py:708) which is never read — only combine_grid.py:80 writes the correct `oneFail`. So the "split job failed cuts" flag is set correctly only at one of its three write sites. Two confirmed case/spelling dead-writes in this slice: `self.gran` and `self.onefail`.

**`conservative_factor` is a dead parameter:** `combine_grid.py` has only three occurrences (signature defaults at 164 + 185, pass-through at 177); **no function body ever reads it**, and `write_associate_grid`'s `twgt = mean / 8.0 / nb_event` (219) is hardcoded `/8.0`. The call sites that pass `conservative_factor=5.0` (gen_ximprove.py:644), `=self.max_iter` (1759, 1774) hand an argument the callee discards — that is precisely a dead parameter, not evidence of use. It is a *different shape* from the case-mismatch dead-writes (`self.gran`/`self.onefail`) — here the spelling matches, the value simply isn't consumed — but it is equally inert. See combine-grid-vegas.md.

## Class dispatch (`__new__`, gen_ximprove 1006-1023)
`gen_ximprove(cmd, opt)` returns a `gen_ximprove_gridpack` when either (a) `cls.force_class=='gridpack'` (the gridpack subclass sets this as a **class attribute** in its own `__new__`, 1836-1838) or (b) `gen_ximprove.format_variable(cmd.run_card['gridpack'], bool)` is truthy (1018). Loop-induced and `job_strategy==2` route to `gen_ximprove_share` and pre-empt the gridpack branch order (1015-1020).

## readonly (RO) mode — every path redirected to cwd
The whole point of RO mode: run a deployed gridpack without writing into `$MADGRAPH_INSTALL/.../SubProcesses`. Two relocations:

1. **Script write location** (`get_job_for_event`, 1970): `write_dir = '.' if self.readonly else None`, passed to `create_ajob`. In `create_ajob` (1340-1342) a falsy `write_dir` defaults to `me_dir/SubProcesses`, but `'.'` is truthy → scripts written under `./<P_dir>` (cwd-relative, 1356). `info['base_directory']` is set to `<file_dir>/../../SubProcesses/<P_dir>/<directory>` (1956-1958) so the RO job can find the read-only grid template in the install tree while writing output locally.
2. **Job working directory** (1994, 2032, 2049): `pwd = pjoin(os.getcwd(), j['P_dir']) if self.readonly else pjoin(self.me_dir,'SubProcesses', j['P_dir'])`. The executable (`ajob1` / `script_name`) is chmod-`+x`'d and run with `cwd=pwd`.
3. **Combine location**: `write_dir = '.' if readonly else me_dir/SubProcesses` (2004); `combine_runs.CombineRuns(write_dir)` runs over the cwd-relative tree under the `if self.readonly` branch (2009-2012).

`launch()` passes `main_dir=pjoin(cmd.me_dir,'SubProcesses')` to `collect_result` with the in-source comment "main_dir is for gridpack readonly mode" (1076-1077) — `collect_result`/`Combine_results` accept an explicit base so the survey results can be read from one tree while refine writes another.

## nprocs path — local parallel execution (1973-2007)
Gridpack runs jobs **locally**, not via the cluster layer:
- `nprocs==1`: each `j` run with `cluster.onecore.launch_and_wait(exe, cwd=pwd, packet_member=j['packet'])` (2001); dedup by `P_dir` so one script per P-dir (combining_job=sys.maxsize batched all channels), with a "Working on job N of M" status every 5th P-dir (1990-1991).
- `nprocs>1`: builds `cluster.MultiCore(nb_core=self.nprocs)` (1974), submits every job via `cluster_submit` (2003), then `nprocs_cluster.wait(me_dir, gridpack_wait_monitoring)` (2006-2007). `gridpack_wait_monitoring` logs Idle/Running/Done counts (1976-1980).

## check_events — recursive resubmit with `.previous` carry-over (2015-2061)
After the first generation + `CombineRuns`, verifies each refined channel reached its target:
1. Re-reads `<Sdir>/<P>/G<G>/results.dat` into a fresh `sum_html.OneResult` (2027-2028).
2. If `new_results.get('nunwgt') < requested_events` (2031): the channel under-produced.
   - `events.lhe` is renamed to **`events.lhe.previous`** (`files.mv`, 2038) — the already-generated events are preserved, not discarded.
   - `requested_event` is **reduced by the events already produced** (`-= new_results.get('nunwgt')`, 2034) so the resubmit only makes up the shortfall.
   - `precision -= -1*requested_event/axsec` (2035), `offset += 1` (2036) — distinct seed so the resubmit isn't a duplicate.
3. For the new job set: re-`create_ajob`, run `ajob1` locally (onecore), then **`files.put_at_end(events.lhe, events.lhe.previous)`** (2059) appends the prior events to the new file, and **recurse** `check_events(...)` (2061) until every channel meets `requested_event`.

So gridpack guarantees the exact requested event count per channel by an unbounded local resubmit loop, accumulating across passes via `.previous` concatenation. This is the gridpack analogue of the share-variant carry-over (refine-gen-ximprove.md), but driven by a hard count check rather than a stop-test, and with `gen_events_security` set to no over-generation (no padding).

### CAUTION — `precision -= -1*requested_event/axsec` (2035)
After `requested_event` was just decremented (2034), this line subtracts a negative (so adds magnitude) to `precision`. `precision` for gridpack event-mode is the negative event-target encoding; the resubmit's `precision` field is recomputed from the *reduced* shortfall. Read it as "new precision target = remaining events / axsec," not a precision (relative-error) value — the sign convention is event-count mode (refine-gen-ximprove.md: negative precision ⇒ event-count target).

## Stochastic channel selection (recap, full detail in refine-gen-ximprove.md)
`find_job_for_event` (1864): per channel `R=random.random()`; skip if `goal_lum*axsec < R*ngran` (1886); else `gscalefact[tag]=max(1, 1/(goal_lum*axsec/ngran))` (1888). With `ngran` stuck at 1 (typo above), the skip threshold is `R` itself — channels with `goal_lum*axsec ≥ R` are refined. So the count of refined channels is RNG-driven and depends on `ngran` *only if the typo is bypassed*.

## Cautions summary
- `self.gran` (1847) vs `self.ngran` everywhere else — user `ngran` opt is silently dropped; granularity effectively 1.
- RO mode redirects script-write, job-cwd, and combine to `os.getcwd()`; the install-tree `SubProcesses` is read-only source of the grid template (`base_directory`). Confusing two trees (read vs write) mis-locates `results.dat`/`events.lhe`.
- Gridpack runs jobs via `cluster.onecore`/`MultiCore`, NOT the configured cluster — long gridpack generation is local-CPU-bound regardless of cluster settings.
- `gen_events_security` set to no over-generation; the exact count is met by the `check_events` resubmit loop, which can recurse many times for a hard-to-fill channel.
- `combine_runs.CombineRuns(write_dir)` is invoked with the RO write_dir; it re-unweights to a common max-weight (combine_runs.py copy_events, see iteration-combination-and-results.md) over the cwd-relative tree.
