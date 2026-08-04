---
description: FKSRealProcess fields and the fks_infos config record (the per-config dict the NLO exporter consumes); generate_real_amplitudes dedup and combine_real_amplitudes merge-by-pdgs.
---

# FKSRealProcess and the fks_infos config record

The FKSRealProcess is the per-real data product; its `fks_infos` list is the
record the NLO exporter ultimately consumes (flattened by
`FKSHelasProcess.get_fks_info_list`, see helas-async-generation.md).

## FKSRealProcess.__init__ (fks_base.py:404-460)
Built once per (real-emission leglist, ij splitting). On construction it scans
the leglist for the `fks=='i'` and `fks=='j'` legs and appends ONE dict to
`self.fks_infos` (`:411-434`):

```
{'i': i_fks,                  # leg number of the radiated parton
 'j': j_fks,                  # leg number of the collinear partner / emitter
 'ij': ij,                    # leg number of the combined (born) parton
 'ij_id': ij_id,              # pdg id of the combined parton
 'underlying_born': born_pdgs,# pdg list of the underlying born
 'splitting_type': splitting_type,   # list of pert orders, e.g. ['QCD']
 'need_color_links': ...,     # i is a gluon (see below)
 'need_charge_links': ...,    # i is a photon
 'extra_cnt_index': -1}       # -1 = no extra counterterm (set later)
```

`need_color_links`/`need_charge_links` are computed inline (`:416-423`): both
require i `massless` AND `spin==3` AND `self_antipart`; then `color==8` → color
links (gluon), `color==1` → charge links (photon). This is the per-config flag
the exporter reads to decide color- vs charge-correlated borns (matches
color-links.md need_*_links).

Other instance fields (`:436-460`):
- `self.process` = `copy.copy(born_proc)` with `perturbation_couplings` extended
  by each `splitting_type` order and `orders` copied from the born (kept so the
  squared_orders drive the amplitude, comment `:442`).
- `self.pdgs` = `array.array('i', ...)` of leg ids (the dedup key everywhere).
- `self.colors`, `self.particle_tags`, and `self.charges` (charges are real only
  when `perturbation_couplings != ['QCD']`, else a list of 0.0, `:449-452`).
- `self.amplitude` empty Amplitude, `self.is_to_integrate=True`,
  `self.is_nbody_only=False`, `self.fks_j_from_i={}`, `self.missing_borns=[]`.

`generate_real_amplitude` (`:463-466`) just wraps `Amplitude(self.process)`.

`get_leg_i`/`get_leg_j` (`:498-512`) return the i/j legs but **raise if
`len(fks_infos)>1`** — i.e. only valid BEFORE combine; after combine a real holds
several configs and there is no single i/j.

## generate_real_amplitudes (fks_base.py:651-669)
Generates each real amp once, reusing across reals via shared `(pdg_list,
real_amp_list)` accumulators keyed by `amp.pdgs`. **Reals whose amplitude has no
diagrams are dropped** from `self.real_amps` (`:662-669`) — a real that looks
kinematically valid but yields zero diagrams at the requested orders silently
disappears here.

## combine_real_amplitudes (fks_base.py:673-686)
Merges reals with identical `pdgs` into one FKSRealProcess, concatenating their
`fks_infos` lists. After this a single real carries MULTIPLE fks configs (which is
why `get_leg_i`/`get_leg_j` then refuse). Called with `combine=True` (the
multiprocess `__init__` calls `generate_reals(combine=False)` then
`combine_real_amplitudes` separately, fks_base.py:255-257).

## Cautions
- `extra_cnt_index` starts -1 and is only rewritten by the generate_reals
  extra-counterterm branch (see extra-counterterm-and-dedup.md). A real with no
  g/γ→qq̄ ambiguity keeps -1.
- The no-diagram drop in `generate_real_amplitudes` is silent (no warning) — a
  missing real subprocess can trace to here when orders/squared_orders exclude
  its diagrams.
- `pdgs` (the array of leg ids) is THE identity key for reals across
  combine_real_amplitudes, find_reals_to_integrate, check_ij_confs, and the async
  temp-file reload. Two distinct splittings reaching the same final-state pdgs
  collapse into one real with two fks_infos.
