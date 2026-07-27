---
description: The "effectively single-core" predicate (run_mode==0 OR (run_mode==2 AND nb_core==1)) gates four distinct do_pythia8 behaviors — parallelization-skip, Main:numberOfEvents, log xsec retrieval, DJR retrieval — and is written four times, once in a precedence-broken form. The rule for any "does X happen on a parallel PY8 run?" question.
---

# PY8 single-core predicate: what changes when the shower parallelizes

## Principle
Whether `do_pythia8` runs PY8 directly (single process) or splits the LHE file into
parallel jobs is decided by one predicate:

```
run_mode==0  OR  (run_mode==2 AND nb_core==1)
```

(`run_mode` is `self.options['run_mode']`: 0=single, 1=cluster, 2=multicore. The
predicate is "multicore-but-one-core OR explicitly single".) This **same predicate**
gates four distinct behaviors. To answer any "does behavior X happen on a parallel
(multi-core) PY8 run?" question, do NOT reason from X's purpose — check whether X's
code site sits inside a single-core-gated branch. If it does, X is single-core-only and
the parallel path either skips it, warns, or substitutes the parallel-aggregation path.

The four gated sites (all `madevent_interface.py`):
1. **Parallelization-skip** (`:4800`): `run_mode==0 or (run_mode==2 and nb_core==1)`
   => `self.cluster=None`, run the wrapper directly via `misc.call`; else split into N jobs.
   This is the canonical, correctly-written form. (Quirk: the `:4807` `run_mode==2 and
   nb_core>1` sub-branch inside it is dead — the outer gate already excluded that case.)
2. **`Main:numberOfEvents`** (`:4683`): set to `run_card['nevents']` — but written in a
   **precedence-broken** form (see CAUTION). On a true parallel run it is NOT set here;
   it is instead set per-split in the parallelization block (`PY8Card_<i>` force, see
   do-pythia8-handoff.md "Per-split renormalization").
3. **Log xsec retrieval** (`:5172`): `parse_PY8_log_file` runs only if single-core; the
   parallel branch logs `'Pythia8 cross-section could not be retreived... set nb_core to 1'`
   and leaves sigma_m/Nacc/Ntry as None (so `cross_pythia` is not stored from the log).
4. **DJR retrieval** (`:5205`): `extract_cross_sections_from_DJR` runs only if single-core;
   the parallel branch warns and sets `cross_sections={}` (so no `cross_pythia8` from this
   site).

On a parallel run, the merged numbers for #3/#4 instead come from the **per-split
aggregation** that ran earlier (`:4980-5052`, see py8-result-extraction.md): per-split logs
summed/averaged, per-split DJRs summed with quadrature errors. So the result IS retrieved on
a parallel run — just by a different code path, and the single-core retrieval blocks at
`:5172`/`:5205` are correctly skipped to avoid double-reading.

## CAUTION: the `:4683` form is the lone deviant
`:4683` reads `not use_mg5amc_py8_interface and run_mode==0 or (run_mode==2 and nb_core==1)`.
Python precedence (`not`>`and`>`or`) parses this as
`((not old_iface) AND run_mode==0) OR (run_mode==2 AND nb_core==1)` — NOT the clean
single-core predicate the other three sites use. Consequence: for the **old interface with
run_mode==0**, this guard is False (any nb_core), so `Main:numberOfEvents` is NOT set here;
it falls back to the `setup_Pythia8RunAndCard:4316-4317` default (sets to nevents only if
currently 0/-1). A user `Main:numberOfEvents` in pythia8_card.dat therefore survives on the
old-interface single-core path but is overwritten on main164. The other three sites
(`:4800`/`:5172`/`:5205`) are the canonical form and have no such interface dependence.

## Cases this catches beyond the per-facet pages
do-pythia8-handoff.md documents the `:4683` numberOfEvents caution and the parallelization
block in isolation; py8-result-extraction.md documents the `:5172`/`:5205` retrieval warnings
and the `:4980-5052` aggregation in isolation. Neither states that **one predicate governs all
four sites**, nor that the retrieval-skip is not a failure but a deliberate hand-off to the
aggregation path, nor that `:4683` is the single precedence-broken instance. The principle:
any "does X happen when PY8 parallelizes?" question is answered by locating X's gate, not by
reasoning about X — and the answer for retrieval is "yes, via aggregation," not "no."

Boundary: governs only `do_pythia8`'s LO control flow (in slice). PY8's own internal
threading/`Parallelism` is out of slice. NLO+PS (run_mcatnlo) uses a different driver.

## Instances this lifts from
do-pythia8-handoff.md (Run modes / parallelization; line-4683 CAUTION);
py8-result-extraction.md (Parallel-run aggregation; the `:5172`/`:5205` retrieval gates).
Verified v3.7.1 by source-walk of the four sites (`:4683`, `:4800`, `:5172`, `:5205`) and the
aggregation block `:4980-5052`.
