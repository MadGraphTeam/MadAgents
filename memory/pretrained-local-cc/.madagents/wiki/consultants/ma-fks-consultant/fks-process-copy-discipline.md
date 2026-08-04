---
description: FKS process-cloning invariant — shallow-copy the Process then rebuild its legs separately; never copy.deepcopy a whole process (reorders legs / breaks amp refs).
---

# FKS process-copy discipline

Whenever FKS code needs a modified clone of a `Process` (to change leg ids,
orders, or squared_orders before re-amplitude-ing), the invariant is:

> `copy.copy` the process (shallow), then rebuild `process['legs']`
> *separately* as a fresh leg list. **Never `copy.deepcopy` the whole
> process** — that reorders the legs and breaks amplitude/diagram references.

This is a structural code-construction invariant, not a runtime prediction.
It fires at every FKS site that clones a process, including any new site —
not just the three below.

## Source sites (v3.7.1)
- `generate_virtuals` (`$MADGRAPH_INSTALL/madgraph/fks/fks_base.py:362,377`):
  `myproc = copy.copy(born.born_amp['process'])` then
  `myproc['legs'] = fks_common.to_legs(copy.copy(myproc['legs']))`.
- `generate_reals` cnt_process
  (`$MADGRAPH_INSTALL/madgraph/fks/fks_base.py:758-759`):
  `cnt_process = copy.copy(born_proc)` then
  `cnt_process['legs'] = copy.deepcopy(born_proc['legs'])`, then
  `to_fks_legs(...)`. The legs ARE deep-copied — but on their own, after the
  shallow process copy, never as part of the process.
- `sudakov.py` (`:151-155`, repeated `:189-192,218-221,260,305`): the rule is
  literally commented `# MZ: NEVER deepcopy a process!!!`; pattern is
  `born_proc = copy.copy(...process)` then
  `born_proc['legs'] = MG.LegList(copy.deepcopy(...process['legs']))`. Note
  sudakov rebuilds as a *plain* `MG.LegList`, not `FKSLegList`, to avoid leg
  reordering on assignment.

## Related but distinct: shallow-copy-for-safe-mutation
`check_ij_confs` (`fks_base.py:103,105`) wraps the *iterated* lists in
`copy.copy` (`for real in copy.copy(born.real_amps)`,
`for info in copy.copy(real.fks_infos)`) so it can `.remove()` from the
originals mid-loop. That is the standard "copy the list you mutate while
iterating" idiom — same `copy.copy`, different purpose (loop safety, not
process cloning). Don't conflate.

## Caution
- If you author or edit any FKS routine that clones a process, follow the
  shallow-process / separate-legs idiom. A `copy.deepcopy(process)` will pass
  tests on trivial topologies and silently corrupt leg ordering on others.
- Instance detail lives on ew-sudakov.md (sudakov NEVER-deepcopy caution) and
  extra-counterterm-and-dedup.md (generate_reals cnt_process). Those pages are
  kept; this page is the cross-file principle.
