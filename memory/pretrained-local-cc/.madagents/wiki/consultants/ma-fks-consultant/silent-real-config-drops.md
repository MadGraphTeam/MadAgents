---
description: FKS real-config set shrinks at six pipeline stages, five invisible at default log level — the diagnostic for "an expected real subprocess/config is missing", plus the one DEBUG knob to observe all of them.
---

# Where FKS silently drops real-emission configs

The FKS real set is *enumerated* once (find_splittings/find_reals) and then
*pruned* repeatedly. A real subprocess or `(i,j)` config that you expect to see
can disappear at any of SIX later stages — and FIVE of them produce no
INFO/WARNING (sites 1–3 and 6 emit nothing; sites 4–5 emit DEBUG only). Sites 1–5
prune at real-config granularity; site 6 drops a whole born subprocess at the
ME-combination stage. This page is the single diagnostic for "my expected real
config/subprocess is not in the generated set"; the per-site mechanics live on
the instance pages cited below.

## The six shrink sites (all in `$MADGRAPH_INSTALL/madgraph/fks/`)

| # | Site | What drops | Log level | Page |
|---|------|-----------|-----------|------|
| 1 | `generate_reals` extra-cnt skip (`fks_base.py:804-811`) | real skipped to avoid double-counting a g/γ→qq̄ collinear cnt (cases a/c/d) | **none** (bare `continue`) | extra-counterterm-and-dedup |
| 2 | `generate_real_amplitudes` (`fks_base.py:651-669`) | real whose amplitude has zero diagrams at the requested orders | **none** | fksrealprocess-and-real-amps |
| 3 | `find_reals_to_integrate` (`fks_base.py:953-1024`) | double-counted soft/collinear real pruned when `remove=True` (default) | **none** (only sets `is_to_integrate=False`) | extra-counterterm-and-dedup |
| 4 | `check_ij_confs` (`fks_base.py:98-122`) | duplicate `(i,j)` config across reals sharing pdgs; then any real left with zero fks_infos | `logger.debug` only | extra-counterterm-and-dedup |
| 5 | `async_generate_real` (`fks_helas_objects.py:52`) | no-diagram real returns `[]` in the ncores path | `logger.debug` only | helas-async-generation |
| 6 | `generate_matrix_elements_fks` born-ME append guard (`fks_helas_objects.py:615-617`) | a born FKSHelasProcess whose `born_me` has no processes/diagrams is never appended (serial path) — drops the WHOLE born subprocess, not a real config | **none** (bare ValueError branch falls through) | helas-async-generation |

Sites 1–4 fire in the serial path; site 5 is the async equivalent of site 2.
Site 6 is at the Helas/ME-combination level (serial path), and drops at the
**born subprocess** granularity, not the real-config granularity of sites 1–5.
Sites 1–3 and 6 emit *nothing*; sites 4–5 emit DEBUG. None reaches default level.

## The one observation knob
All four serial sites (1–4) log (or would log) through the **`madgraph.fks_base`**
logger; site 5 through **`madgraph.fks_helas_objects`**. Sites 1–3 emit no record
at all, so raising the logger only surfaces sites 4–5. To see sites 1–3 you must
instrument the code or diff the real set before/after the stage.

```python
import logging
logging.getLogger('madgraph.fks_base').setLevel(logging.DEBUG)
logging.getLogger('madgraph.fks_helas_objects').setLevel(logging.DEBUG)
```

## Probe-verified (v3.7.1)
`generate u u~ > u u~ [QCD]` → real `u u~ > u u~ g` carries ij configs
`[(5,1),(5,2),(5,3),(5,4)]` (emitter i = gluon leg 5, recombining with each
colored leg). Injecting a duplicate of info `(5,1)` and calling
`mp.check_ij_confs()` emitted exactly one record:
`Duplicate FKS configuration found for Process: u u~ > u u~ g ... : ij = [5, 1]`
at level **DEBUG** (no INFO/WARNING), and removed the duplicate (5 infos → 4).
Confirms site 4 is real, DEBUG-only, and silent at default level. Standard
processes (`p p > t t~`, `g g > g g`, `u u~ > u u~`) produced NO duplicate at the
cross-real `check_ij_confs` stage — within-born duplicates are already removed by
site 3 (`find_reals_to_integrate`) before `check_ij_confs` runs, so site 4 mostly
fires only on multi-real pdg collisions.

## Distinct from enumeration *gates*
This page is about configs dropped AFTER they are built. The UPC / init-lepton /
2→1 / decay carve-outs in `find_reals` (`fks_base.py:910-929`) and the same-PDG /
UPC carve-outs in `find_splittings` are *enumeration gates* — they prevent the
config from being built in the first place, and a "missing config" there traces
to splittings-and-real-generation.md, not here. Also distinct: the
process-level discards (two-initial-lepton, non-photon UPC) at
`fks_base.py:236-247`, which DO log at INFO ("Discarding process…").

## Why this catches more than the instance pages
Each instance page documents its own site as a one-line caution. A debugging
question — "I expected real subprocess X / config (i,j) and it's gone" — needs
the asker to already know which of three pages owns the relevant site. This page
is the checklist: walk the six sites in pipeline order, and for the four that emit
nothing, diff the real set across the stage rather than trusting the log.
