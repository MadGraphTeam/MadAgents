---
description: FKSHelasRealProcess __init__ three ME-provision modes and the __eq__ (ignores fks_infos/charges + per-info ij_id/underlying_born) that drives within-born real dedup and add_process 1-to-1 real matching.
---

# FKSHelasRealProcess: construction modes and equality

`FKSHelasRealProcess` (`$MADGRAPH_INSTALL/madgraph/fks/fks_helas_objects.py:941`)
is the Helas-ME wrapper around an `FKSRealProcess` (the amplitude-level object on
fksrealprocess-and-real-amps.md). Its `__eq__` is the predicate behind two
combination operations:
- within-born real dedup in `FKSHelasProcess.__init__`
  (`self.real_processes.index(fksreal_me)`, `:708,722`);
- the 1-to-1 real correspondence in `FKSHelasProcess.add_process`
  (`self.real_processes.index(oth_real)`, see helas-async-generation.md
  add_process section) — a miss there RAISES.

## __init__ — three ME-provision modes (:955-1004)
Copies `colors`, `particle_tags`, `charges`, `fks_infos`, `is_to_integrate` off
the `fksrealproc`, then provides `self.matrix_element` by one of three branches on
the type/contents of `real_me_list`:
1. **list, old NLO mode** (`:976-978`): `real_me_list` is a list 1-1 with
   `real_amp_list`; picks `real_me_list[real_amp_list.index(fksrealproc.amplitude)]`
   and **deepcopies** it (and its `processes`). Requires
   `len(real_me_list)==len(real_amp_list)` else `FKSProcessError` (`:972-975`).
2. **single HelasMatrixElement, new (multicore) NLO mode** (`:980-986`): asserts
   `fksrealproc.process in real_me_list['processes']` (consistency check, raises
   AssertionError on mismatch) and uses the ME directly (no copy).
3. **generate-fresh fallback** (`:988-1002`): if a (list, amp_list) pair is given,
   same index-and-deepcopy as mode 1; else builds a fresh
   `HelasMatrixElement(fksrealproc.amplitude)` and its color basis/matrix inline
   (INFO "generating matrix element...").
Finally `self.fks_j_from_i = fksrealproc.fks_j_from_i` (`:1004`).

## __eq__ — equality up to PDG-level relabeling (:1010-1030)
Two-stage compare, deliberately ignoring the identity-bearing fields so that two
reals with the same TOPOLOGY but different PDG ids/underlying borns are "equal"
(this is what lets c c~ > t t~ g and u u~ > t t~ g reals share one
FKSHelasRealProcess and merge their process lists):

1. **Top-level dict compare, skipping `fks_infos` and `charges`** (`:1014-1016`):
   every other instance attribute (`matrix_element`, `colors`, `particle_tags`,
   `is_to_integrate`, `fks_j_from_i`, `isfinite`) must be equal. (`charges` skipped
   because charges differ across same-topology flavor reals; `fks_infos` handled
   separately below.)
2. **fks_infos compare, per-info skipping `ij_id` and `underlying_born`**
   (`:1019-1029`): same number of infos; for each info, same `len(underlying_born)`
   and equal on every key EXCEPT `ij_id` and `underlying_born`. So `i`, `j`, `ij`,
   `splitting_type`, `need_color_links`, `need_charge_links`, `extra_cnt_index`
   must match, but the actual mother pdg (`ij_id`) and born pdg list
   (`underlying_born`) may differ.

`__ne__` (`:1033-1036`) negates.

## Why this matters / cautions
- The equality is **looser than pdg-identity**: it is the leg-structure +
  ij-config-shape match, NOT the flavor match. This is the mechanism by which the
  serial `generate_matrix_elements_fks`/`add_process` and the async finalize fold
  flavor-equivalent real subprocesses together (and why `add_process` can then
  extend the merged real's process pdg lists).
- `matrix_element` being in the top-level compare means two reals are equal only
  if their Helas MEs are equal (HelasMatrixElement.`__eq__`) — same diagram
  structure — AND their fks-config shapes line up. A real that fails the ME compare
  never reaches the fks_infos stage.
- The `assert fksrealproc.process in real_me_list['processes']` (mode 2) is the
  new-mode consistency guard; an AssertionError here means the pre-generated real
  ME handed in does not contain the expected process (mismatch between the async
  real-amp generation and the born-side reload).
- A bad pairing of `real_me_list`/`real_amp_list` lengths (mode 1/3) is a hard
  `FKSProcessError` ("not same number of amplitudes and matrix elements") — the
  1-1 correspondence is assumed, not searched.
