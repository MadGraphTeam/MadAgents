---
description: run_onshell algorithm as the interface drives it — BR combinatorics, max-weight estimation, identical_particle effect site, fixed_order event-group handling end-to-end (interface_madspin.py)
---

# run_onshell — the onshell algorithm at the interface level

`run_onshell` at `$MADGRAPH_INSTALL/MadSpin/interface_madspin.py:1373`. The
`madspin-bridge-onshell-launch-io` page covers the **entry** I/O (input_format auto, count
which/how-many) and declared the decay-ME generation out of slice. This page caches the
**interface-driven onshell orchestration** that lives in interface_madspin.py (NOT decay.py):
the BR/cross bookkeeping, max-weight estimation, the matrix-element evaluation seam, and the
`fixed_order` handling. The actual ME *generation* class `decay_all_events_onshell`
(`MadSpin/decay.py:4196`, subclass of `decay_all_events` :1943) is out of slice.

## BR computation — combinatorial, NOT the bridge formula (:1462-1510)
Per to-decay PDG, branch on how `nb_needed` relates to `nb_event`:
- **one-per-event** (`nb_needed == nb_event`, :1472): generate `int(efficiency*nb_needed)+nevents_for_max`
  events `cumul=True`, get `pwidth`; `br *= pwidth/totwidth` (:1479). `efficiency` is a spin-dependent
  headroom factor — one value for spin-1, a larger one otherwise (:1464-1468 — read fresh) — over-generation
  headroom because not every generated decay passes.
- **integer-multiple** (`nb_needed % nb_event == 0`, `nb_mult = nb_needed//nb_event`, :1480-1501):
  - if `len(list_branches[name]) == nb_mult` (each copy its own branch): generate `nb_event`,
    `br *= pwidth/totwidth**nb_mult` then **`br *= math.factorial(nb_mult)`** (:1493-1494) — the
    factorial is the combinatorial multiplicity of assigning N identical decaying particles to N
    distinct branches.
  - else (one branch covers all copies, `cumul=True`): `br *= (pwidth/totwidth)**nb_mult` (:1501),
    no factorial.
- **else** (inconsistent counts, :1503-1508): `raise InvalidCmd("The onshell mode of MadSpin does
  not support event files where events do not *all* share the same set of final state particles
  to be decayed.")` — this is the ACTIVE (uncommented) onshell-mode limitation, distinct from the
  bridge-mode commented-out one (see bridge-onshell page :949).
- width clamp: `pwidth` above `totwidth` by more than a small tolerance -> `logger.warning("partial width
  larger than total width --from param_card--")`; a partial width within tolerance above total silently clamps
  `pwidth = totwidth` (:1475-1478 etc. — read the tolerance fresh). So a slightly-over partial width is tolerated and pinned to total.

After the loop: `self.branching_ratio = br`, `efficiency = 1`, `cross,error =
banner.get_cross()` then `cross *= br`, `error *= br` (:1510-1514). `banner.scale_init_cross(br)`
written into the output banner (:1533). This is the seam MadGraph consumes (cross/branching_ratio).

## max-weight estimation (get_maxwgt_for_onshell :1636)
- ms_dir cache: if `ms_dir/max_wgt` exists, read it back (:1642-1643); else compute and write it
  (:1687-1688). So a reused gridpack skips re-estimation.
- probes the first `nevents` events (`Nevents_for_max_weight`, local hardcoded fallback if 0, :1645-1647)
  with `max_weight_ps_point` PS points each (:1652-1664); per event takes the max over PS points.
- base estimate `factor*(ave+nb_sigma*std)` over all maxwgts (:1675), then re-tightened over the top
  N sorted maxwgts (:1678-1686) and bumped to `factor*all_maxwgt[1]` if the 2nd-largest
  exceeds the estimate. With default `nb_sigma=0` (sentinel), the estimate is `factor*ave` plus the top-tail
  guard — i.e. mean-driven, not tail-driven, unless nb_sigma is raised. (Read the factor, fallback, and top-N counts fresh at their lines.)
- `Nevents_for_max_weight` and `nb_sigma` are import-resolved sentinels (see staging page); here
  they drive how many probe events and how many sigma of headroom.

## matrix-element evaluation & identical_particle_in_prod_and_decay (calculate_matrix_element :1727)
This is where `identical_particle_in_prod_and_decay` (default `'average'`) ACTUALLY takes effect —
the option page only lists allowed values; the effect is here:
- `get_all_momenta(orig_order)` can return >1 momentum assignment when production and decay share
  identical particles (:1744). The option decides how to combine the per-assignment MEs:
  - `'crash'` + >1 assignment -> `raise Exception("Ambiguous particle in production and decay...")`
    (:1745-1747).
  - `'average'` -> sum all, divide by count (:1755-1763).
  - `'max'` (the else/default-of-the-branch) -> keep the largest |ME| (:1758-1759).
  - `'first'` -> return the first assignment immediately (:1760-1761).
- weight ratio (get_onshell_evt_and_wgt :1695): returns `full_me/(production_me*decay_me)` (:1724) —
  the onshell spin-correlation weight is the full prod+decay ME over the product of factorized MEs.
  Caches `production.me_wgt` to avoid recompute (:1710-1714).
- **hardcoded sentinel (:1751-1752)**: if `event[0].color1 == <magic-tag> and event.aqcd == 0`, the f2py ME
  is called with a hardcoded `aqcd` and flag instead of the event's aqcd/scale. The magic color tag and the
  hardcoded aqcd are read fresh at :1751-1752; this is a narrow special-case in the ME call, easy to miss.

## fixed_order — onshell-ONLY event-group handling (:1410-1662, plus post_set :121)
`fixed_order` (default False, :72; "to activate fixed order handling of counter-event") is consumed
**only inside run_onshell and its helpers** — the none/madspin/full paths never read it. Confirmed:
every `fixed_order` touch in the interface is at :1410/1417/1530/1542/1553/1557/1662 (all run_onshell
scope). `post_fixed_order` (:121) emits two warnings on set: "Fix order madspin fails to have the
correct scale information. This can bias the results!" and "Not all functionalities of MadSpin handle
this mode correctly (only onshell mode so far)."
- input read with `orig_lhe.eventgroup = True` (:1410) — each LHE "event" is a GROUP (the real event
  plus NLO counter-events); the counting loop unwraps `event = event[0]` to count only the real event
  (:1417-1418).
- output also `eventgroup = True` (:1530-1531).
- per-event decay loop: `production, counterevt = production[0], production[1:]` (:1542-1543); decays
  are generated for the real event, then **re-attached to every counter-event** via
  `[evt.add_decays(decays) for evt in counterevt]` so the whole group shares the same decay kinematics
  (:1553-1554). Each member's weight (and parsed reweight wgts) scaled by `branching_ratio`
  (:1557-1563).

## Cautions
- The onshell limitation (:1508) is a HARD abort on heterogeneous final states — onshell needs every
  event to have the same set of decaying particles; mixed-final-state samples must use madspin/none.
- `generate_all_matrix_element` at **`interface_madspin.py:1803`** is DEAD CODE — no caller
  (grep-confirmed: the only `self.generate_all_matrix_element()` calls, decay.py:2052/2060, bind to the
  `decay_all_events` method, NOT this interface method), ends in a bare `raise Exception` at
  `interface_madspin.py:1844`; its decay-coupling default (`' QCD=99'` appended to a decay with no `=`,
  `interface_madspin.py:1816`) is a stale copy. The LIVE decay-coupling default is `decay.py:2857`
  (`decay_all_events.generate_all_matrix_element`, :2741) and its onshell override `decay.py:4280`
  (`decay_all_events_onshell.generate_all_matrix_element`, :4201). NOTE: there are THREE methods named
  `generate_all_matrix_element` — two LIVE (decay.py:2741 base + decay.py:4201 onshell override, both
  instantiated at interface_madspin.py:674/1518) and one DEAD (interface_madspin.py:1803). Always carry
  the FILE with the line number — a bare `:1803`/`:1816`/`:1844` resolves into unrelated decay.py code
  (`reorder_branch` / `modify_param_card`). Do not cite the interface dead copy as a live path.
- `fixed_order` warns it's only correct in onshell; setting it under any other spinmode silently has
  no effect (the option is simply never read there).

## Gaps
- `decay_all_events_onshell.compile()` / the ME library build, and decay-event sampling internals —
  MadSpin internals (decay.py), out of slice.
- Whether the spin-dependent efficiency headroom (:1464-1468) is ever insufficient (re-generation
  top-up at :1617-1629 handles StopIteration) is a runtime/statistics question — needs a probe.
