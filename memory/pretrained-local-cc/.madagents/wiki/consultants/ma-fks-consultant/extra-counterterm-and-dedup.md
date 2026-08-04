---
description: generate_reals extra-counterterm (g/a->qqbar) handling, find_reals_to_integrate double-count removal, check_ij_confs silent dedup.
---

# Extra counterterms, double-counting removal, and ij dedup

## generate_reals extra-counterterm logic (fks_base.py:689-845)
For each real built by `find_reals`, before keeping it the code handles the
tricky case where an extra "mother" (e.g. g→qq̄ vs γ→qq̄) could give the same
real-emission final state, to avoid double-counting the collinear singularity.

- `has_coll_sing_born` (`:729-736`): true if the born at
  `squared_orders[pert] - 2` still has diagrams (collinear singularity subtracted
  by this dir's born). If `squared_orders[pert] < 2`, false.
- At most ONE extra mother allowed — else `FKSProcessError` (`:745-747`).
- `has_coll_sing_cnt` (`:750-782`): generates the counterterm process replacing
  the splitting mother with `mom_cnt`, checks its amplitude exists with current
  squared orders, then whether at `cnt_ord - 2` it still has diagrams.
- Four cases a)–d) documented at `:784-801`. Decision:
  - skip if `mom_cnt and mom_cnt < ij_id` and (both-or-neither coll sing) (`:804-807`);
  - skip case c): `has_coll_sing_cnt and not has_coll_sing_born` (`:810-811`).
  - otherwise keep the `FKSRealProcess`; if `has_coll_sing_cnt`, store the cnt
    amplitude in `extra_cnt_amp_list` and record `extra_cnt_index`,
    append cnt pdgs to `underlying_born` and `cnt_ord` to `splitting_type`
    (`:822-837`).

`extra_cnt_index` defaults to -1 (no extra counterterm) in FKSRealProcess
(`fks_base.py:434`).

## find_reals_to_integrate (fks_base.py:953)
Pairwise comparison of real_amps to set `is_to_integrate=False` on duplicates
(double-counted soft/collinear configs). Must run BEFORE combining processes
(raises if a real already has >1 fks_info, `:966-968`).
- Final-final (`j_m,j_n > nincoming`): requires same mother id `ij_id`, matching
  (i,j) ids (either order); then keeps one by i/j/ij ordering and the
  particle=anti-particle test (`:976-1009`). For g/a→ffx (non-self-conjugate
  daughters) keeps the **lowest ij** (`:998-1004`).
- Initial-state (`j_m <= nincoming`, `j_n==j_m`): keeps lower-i config (`:1011-1017`).
- If `remove_reals` (default True), non-integrate reals are pruned (`:1018-1023`).

## check_ij_confs (fks_base.py:98) — SILENT dedup
Runs at the FKSMultiProcess level. Builds `ijconfs_dict` keyed by space-joined
real pdgs; if an `[i,j]` config already seen for those pdgs, **removes that
fks_info** with only a `logger.debug` (`:109-112`). If a real loses all its
fks_infos it is removed from the born, again only `logger.debug` (`:119-122`).
No INFO/WARNING — duplicates vanish silently.

## Cautions
- check_ij_confs dedup is invisible at default log level — a config you expect may
  be silently dropped across reals sharing the same pdgs. Raise logger
  `madgraph.fks_base` to DEBUG to observe.
- The extra-cnt double-counting decision depends on `squared_orders`; a process
  with insufficient squared orders (`< 2` in the pert coupling) takes the
  `has_coll_sing_born=False` branch and may drop the collinear counterterm.
