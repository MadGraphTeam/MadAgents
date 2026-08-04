---
description: The s-vs-t classification of a branch is one fact (first daughter is an incoming leg) re-derived at every PS stage — configs.inc SPROP/TPRID, set_peaks tsgn, map_invarients tchannel/nb_tchannel, one_tree ns/nt — letting you predict mapping + var-count + itmax bump for ANY config from one read.
---

# The s/t-channel classification invariant

Across the whole LO phase-space path the question "is propagator branch `-i` of `iconfig`
s-channel or t-channel?" is answered by ONE structural fact and re-derived independently at every
stage that needs it. Knowing this lets you read a single config and predict, for ANY process the
instance pages never named, which branches get BW vs t-channel mappings, how many integration
variables the channel has, and whether the driver's `itmax+=2` bump fires.

## The single fact
A branch is **t-channel iff its first daughter is an incoming leg**:
`iforest(1,-i,iconfig)` equals `1` (or `2` when `nincoming==2`). Otherwise it is **s-channel**.
In the static configs.inc tables this surfaces as a strict dichotomy, **mutually exclusive per
branch**:
- `SPROP(iproc,-i,c) != 0`  <=>  s-channel branch (the PDG of the s-channel propagator).
- `TPRID(-i,c) != 0`        <=>  t-channel branch (the PDG of the t-channel propagator).
Never both, never neither on a real propagator branch.
Probe `q q~ > t t~` (`<PROC_DIR>/.../P1_qq_ttx/configs.inc`, MAPCONFIG(0)=4): configs 1/2/3
are s-channel `SPROP=22/21/23, TPRID=0`; config 4 is t-channel `TPRID(-1,4)=24, TPRID(-2,4)=5,
SPROP=0,0,0` on both branches. Exactly one of {SPROP,TPRID} nonzero per branch.

## Re-derived at four stages — same concept, NOT a byte-identical predicate
1. **Table build (output)** — configs.inc SPROP/TPRID written by `write_configs_file_from_diagrams`
   (`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:5415`, ME class). This is the source of truth the
   other three read via common `/to_sprop/` and `/to_forest/`.
2. **Variable mapping (set_peaks)** — `tsgn` decides BW (s) vs `setgrid` offset (t). A 3-line block
   `if (iforest(1,i,iconfig) .eq. 1.or.iforest(1,i,iconfig) .eq. 2) then / tsgn=-1d0 / endif`
   (`$MADGRAPH_INSTALL/Template/LO/SubProcesses/myamp.f:377-379`; note `tsgn` is *sticky* — once -1 it
   stays for later propagators). See propagator-mappings-gen_s-transpole.md.
3. **Invariant counting (map_invarients)** — counts `nb_tchannel` (simple `nconfigs==1` path) via an
   `ns_channel` walk `do while((iforest(1,-ns_channel,mincfig).ne.1.and..ne.2).and.ns_channel.lt.nbranch)`
   then `nb_tchannel=nbranch-ns_channel-1` (`$MADGRAPH_INSTALL/Template/LO/Source/invarients.f:239-243`).
   The multi-config path's `tchannel`-flag + cos-theta-slot allocation uses the *guarded* predicate
   `if (iforest(1,-j,iconfig).eq.1 .or. (nincoming.eq.2 .and. iforest(1,-j,iconfig).eq.2))`
   (invarients.f:252) but does NOT compute nb_tchannel. `nb_tchannel` drives the driver's `itmax+=2`
   bump. See genps-momentum-generation.md.
4. **Momentum generation (one_tree)** — walks `itree` until the incoming leg `iopposite` (keyed on
   `tstrategy` sign, NOT a bare iforest test), giving `ns_channel`/`nt_channel=nbranch-ns_channel-1`
   (`$MADGRAPH_INSTALL/Template/LO/SubProcesses/genps.f:784-795`). See genps-momentum-generation.md.

### The predicate is NOT identical everywhere — the trap
- **cut_bw** (myamp.f:117) and **map_invarients** (invarients.f:252) GUARD the `.eq.2` with
  `nincoming.eq.2`.
- **set_peaks** (myamp.f:377) does NOT guard `.eq.2`. Harmless in practice (a 1->n decay,
  nincoming==1, has no t-channels and leg 2 is final-state), but the predicates are not byte-identical
  — do not assume "the same line everywhere".
- **one_tree** uses `iopposite` (from `tstrategy`), a different mechanism that achieves the same s/t
  split. So the INVARIANT is conceptual (first daughter = incoming leg => t-channel), not a single
  shared line of code.

## What you can predict from one configs.inc read
- Which branches get a BW mapping (SPROP!=0, width>0) vs a t-channel `1/sqrt` / offset grid
  (TPRID!=0) — without re-reading set_peaks.
- The integration-variable count: on the multi-config path each t-channel branch adds a cos-theta slot
  `minvar(nbranch-1+2*j,...)` (invarients.f:255-258); the last pure-s invariant is dropped for 2->n
  (`minvar(nbranch-1)=0`, invarients.f:264). (The simple `nconfigs==1` job uses `minvar(j)=j` over the
  full maxdim range, line 231-233, so the cos-theta vars are already in that flat range.)
- Whether `itmax = itmax+2` fires: count TPRID!=0 branches; >1 => bump (driver.f:196), because the
  standard per-channel job runs `nconfigs==1` and that is the only map_invarients path computing
  nb_tchannel (see genps-momentum-generation.md).

## Boundary
- This page owns the *classification* and where it is read. The *mapping math* per class is
  propagator-mappings-gen_s-transpole.md; the *event-level gating* (gForceBW/cut_bw/OnBW) is
  gforcebw-cut_bw-onshell.md; the *VEGAS point/iteration budget* is the numerical/VEGAS slice.
- SPROP is dimensioned `(maxsproc,...)`: one symmetry-grouped config can carry different s-PDGs
  across subprocesses; myamp picks the first nonzero iproc (myamp.f:108-113). The s/t dichotomy still
  holds per (branch), just read across the iproc axis for the PDG.
