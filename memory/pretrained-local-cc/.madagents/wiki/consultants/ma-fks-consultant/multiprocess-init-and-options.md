---
description: FKSMultiProcess options/defaults (OLP, ewsudakov, init_lep_split, nlo_mixed_expansion, ncores_for_proc_gen, loop_filter) and the __init__ born->real->virtual flow.
---

# FKSMultiProcess construction, options and defaults

`FKSMultiProcess` (`$MADGRAPH_INSTALL/madgraph/fks/fks_base.py:45`) extends
`diagram_generation.MultiProcess`.

## Defaults (default_setup, fks_base.py:50-62)
- `real_amplitudes` = empty AmplitudeList
- `pdgs` = []
- `born_processes` = empty FKSProcessList
- `ewsudakov` = False
- `OLP` = `'MadLoop'` (set only if absent), `ncores_for_proc_gen` = 0
- `loop_filter` = None

## Options consumed in __init__ (fks_base.py:125-192)
- `nlo_mixed_expansion` (`:133-137`) default **True**. Popped from options first.
  Controls loop-order determination in generate_virtuals.
- `OLP` (`:151-154`) default 'MadLoop'.
- `ewsudakov` (`:157-160`) default False.
- `init_lep_split` (`:163-166`) default False — controls lepton-initiated process
  inclusion.
- `ncores_for_proc_gen` (`:172-175`): 0 = old (serial) generation; >0 = that many
  cores; -1 = all cores. Selects async vs serial path.

## Construction flow
1. `super().__init__` generates the borns. `NoDiagramException` →
   `NoBornException` ("loop-induced … use virt= mode", `:181-188`).
2. Multiparticle warning (`:194-222`): if a born leg's multiparticle ids overlap
   soft particles but aren't exactly the full soft set, warns to consult appendix
   D of arXiv:1804.10017. Skipped for decay processes. **Trigger detail** (`:214-222`):
   per leg, fires iff `any(id in soft_particles)` AND `sorted(leg['ids']) != soft_particles`.
   `find_pert_particles_interactions(...)['soft_particles']` is returned already
   `sorted()` ascending (probed v3.7.1: QCD → `[-4,-3,-2,-1,1,2,3,4,21]` — light
   quarks + gluon, NO b/b̄/t since they are massive), so for a SINGLE perturbation
   order the comparison is a clean set-equality. **Consequence: the default `p`
   multiparticle (which includes `b,b̄`) can never equal the QCD soft set → this
   appendix-D warning effectively ALWAYS fires for `p` in QCD NLO** — it is
   informational, not an error, and not a sign of a malformed process.
   **Multi-pert quirk:** across >1 perturbation order, `soft_particles` is
   `.extend`-accumulated and NOT re-sorted (`:207-209`) — so the `:216` equality
   compares the sorted leg ids against a possibly-unsorted, possibly-duplicated
   concatenation, and a multiparticle that exactly matches the union still
   mis-compares as `!=` and warns. The `perturbation` list also accumulates across
   procdefs here and is reused later in the "no correction up to NLO" error string
   (`:293`).
3. Per-born-amplitude (`:234-261`): discards two-initial-lepton processes unless
   `init_lep_split` (`:236-242`); discards non-photon two-initial UPC processes
   (`:245-247`); builds `FKSProcess`, calls `generate_reals(combine=False)`, then
   `combine_real_amplitudes`.
4. Serial path only (`not ncores_for_proc_gen`, `:263-300`): `find_fks_j_from_i`
   per real; `generate_virtuals` if NLO_mode=='all'; validates NLO_mode in
   {all,real,LOonly}; raises `FKSProcessError` if zero real AND virtual diagrams
   and not LOonly (`:289-293`); logs the n-subprocess summary.
5. `has_isr` / `has_fsr` set from born processes (`:302-303`).

## generate_virtuals (fks_base.py:338)
Returns early if `OLP != 'MadLoop'` (loops generated at output stage by the OLP,
`:345-348`). If `nlo_mixed_expansion` False, computes per-coupling max loop orders
(`:350-358`). Per born: sets `perturbation_couplings = model['coupling_orders']`
when orders unspecified (`:373-374`); UPC virtual discard (`:379-383`); builds
`LoopAmplitude` with `loop_filter` (`:388-391`), swallowing `InvalidCmd`.

## FKSMultiProcess.add — merging two multiprocesses (fks_base.py:305-316)
`add(self, other)` extends `process_definitions`, `amplitudes`, `born_processes`,
`real_amplitudes`, `pdgs` (list-extend), and **ORs** `has_isr`/`has_fsr`/
`ewsudakov`. But it **OVERWRITES** `OLP` and `ncores_for_proc_gen` from `other`
(`:314-315`) — the merged value is the *latter* operand's, not OR/max. So combining
multiprocesses with different OLP or ncores settings silently takes the second's;
do not assume `add` preserves self's OLP/ncores.

## FKSProcess.__init__ asymmetries (fks_base.py:579-648)
- `self.isr`/`self.fsr` are **hard-coded False** here (`:632-633`, the real
  derivation is commented out `:630-631` "MZ to be fixed"). The operative
  has_isr/has_fsr come from the multiprocess level (`:302-303`), NOT from
  FKSProcess. Don't read FKSProcess.isr/fsr as meaningful.
- `self.perturbation` defaults `'QCD'` (`:597`). The **Process** start-branch
  re-derives it from `sorted(perturbation_couplings)[0]` (`:610-612`), but the
  **Amplitude** start-branch does NOT (`:617-622` sorts with the still-default
  `self.perturbation='QCD'`). An amplitude carrying e.g. QED-only perturbation
  could be sorted/processed as QCD — an asymmetry to watch when starting from an
  Amplitude rather than a Process.
- `find_reals` runs only when `NLO_mode != 'LOonly'` (`:642-643`); sudakov amps
  generated only if `ewsudakov` (`:647-648`).

## Cautions
- A process with neither real nor virtual NLO contributions (and not LOonly) hard
  errors at `:289`. LOonly is a "fake NLO" used in merged high-multiplicity samples.
- `FKSMultiProcess.add` overwrites OLP/ncores from the second operand (above).
- `FKSProcess.isr/fsr` are always False; use multiprocess has_isr/has_fsr instead.
- `nlo_mixed_expansion=True` (default) lets ALL coupling orders be perturbed in the
  loop when born `orders` are unset — relevant for EW/mixed corrections.
- The serial vs async (ncores) paths diverge substantially; virtual generation in
  async mode happens inside `async_generate_born`, not generate_virtuals.
