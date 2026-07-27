---
description: DR/DS (Diagram Removal / Subtraction) for resonant real-emission overlap (tt̄ vs tW) is NOT in stock FKS/NLO source — it is the MadSTR plugin (install-only). Stock FKS keeps all real diagrams; resonance handling is BW-window (myamp.f) not diagram-removal.
---

# DR/DS resonant-overlap handling — MadSTR plugin, not stock FKS

Warm-up scan (`/mg-study` diagram-filtering). v3.7.1. PLUGIN/ contains only
`__init__.py` — MadSTR ABSENT; plugin code not walkable here.

## The physics problem IS FKS-relevant (concept groundable)
At NLO, real-emission corrections to a process can contain doubly-resonant
sub-topologies that coincide with a distinct LO process (canonical: tW real
emission `p p > t W b` contains tt̄-like `t t̄` doubly-resonant diagrams,
overlapping tt̄ production). This overlap lives in the **real-emission amplitude**
— which is exactly what FKS `find_reals` / `FKSRealProcess` enumerate
(splittings-and-real-generation.md, fksrealprocess-and-real-amps.md). So the
overlap is a structure the FKS slice's real configs DO contain. But stock FKS has
NO mechanism to remove/subtract it.

## Stock FKS does NOT implement DR or DS — grep-absence
- `grep -rniE "diagram_removal|\bDR\b|\bDS\b|resonance|remove_diag|onshell_subtr|MadSTR|\bSTR\b"`
  over `$MADGRAPH_INSTALL/madgraph/fks/` (fks_base/fks_common/fks_helas_objects/
  fks_tag/sudakov.py) → only incidental `str(...)` casts and `splitting_type`.
  No DR/DS/resonance-subtraction code.
- FKS real enumeration keeps ALL diagrams of each real amplitude; the only
  resonance concept anywhere near real generation is the BW-cutoff *window*
  (`bwcutoff`, myamp.f — ma-bw-window slice), which is on-shell propagator
  clipping for phase-space integration, NOT diagram removal.
- NLO run_card template (`$MADGRAPH_INSTALL/Template/NLO/Cards/run_card.dat`):
  only `bwcutoff` "Determines which resonances are…" (line ~151). No `istr` /
  DR / DS knob. (`cluster.f` "Remove diagrams … resonance structure" at
  :355-371,661-713 is FKS *phase-space channel* clustering for scale-setting, a
  different mechanism — not tt̄/tW overlap removal.)

## MadSTR is an install-plugin TARGET only (external)
`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`:
- `:6484  install_plugin = ['maddm','maddump','MadSTR','cudacpp']`
- `:6503  'MadSTR':['arXiv:1612.00440']` (the install citation source records;
  the DR/DS method papers are Frixione et al.)
- `:6631-6633` aliases `madstr`/`madSTR` → `MadSTR`
- `:3004` MadSTR listed among installable plugins in do_install completion.
So stock MG5 knows how to *fetch/install* MadSTR (`install MadSTR`) but ships
none of its DR/DS code. Discovery via PLUGIN/ + `--mode=` belongs to
installation/interface slices (premise), not FKS.

## GAP (cannot source-verify here)
- DR = discard real diagrams with two resonant top propagators; DS = locally
  subtract on-shell tt̄ contribution keeping all diagrams: these are MadSTR
  algorithm claims. Plugin absent → external/unverified. Physics-spec level: send
  DR-vs-DS choice + tt̄/tW overlap physics to ma-physics; install to installation.

## Bottom line for a future dispatch
Stock MG5_aMC v3.7.1 CANNOT do DR/DS resonance-overlap treatment without the
MadSTR plugin. A tW / tt̄-overlap NLO request requires `install MadSTR` first;
the FKS slice alone provides the real amplitudes containing the overlap but no
removal/subtraction of it.
