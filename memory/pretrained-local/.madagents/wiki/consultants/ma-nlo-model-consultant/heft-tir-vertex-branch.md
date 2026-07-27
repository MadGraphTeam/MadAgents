---
description: How MadLoop/TIR detects HEFT-style effective vertices per loop group (HAS_AN_HEFT_VERTEX) and routes CutTools-limited loops; the structural rule defining a HEFT vertex.
---

# HEFT-style effective vertices at NLO (TIR branch)

(v3.7.1.) The loop reduction has special handling for Higgs-effective vertices so CutTools
limitations are correctly enforced per loop group.

## The flag (`$MADGRAPH_INSTALL/.../template_files/loop_optimized/TIR_interface.inc:475`)
```
LOGICAL HAS_AN_HEFT_VERTEX(NLOOPGROUPS)
%(has_HEFT_list)s
```
Used at 514 (QP branch) and 531 (DP branch):
`CALL DETECT_LOOPLIB(LIBNUM,NLOOPLINE,RANK,complex_mass,HAS_AN_HEFT_VERTEX(loop_ID),
MAX_SPIN_CONNECTED_TO_LOOP,LPASS)`. The per-loop-group HEFT flag is an input to the
reduction-library selection: a loop containing an HEFT vertex constrains which library
(CutTools vs TIR libs) may reduce it. `LPASS=.FALSE.` advances to the next library.

## Where has_HEFT_list is computed (`$MADGRAPH_INSTALL/madgraph/loop/loop_exporters.py:2229-2260`)
At output time, per loop group `i`:
```
for lamp in loop_amp_list:
    final_lwf = lamp.get_final_loop_wavefunction()
    while final_lwf is not None:
        scalars = #(mothers with spin==1 and mass!='ZERO')
        vectors = #(mothers with spin==3 and mass=='ZERO')
        if scalars>=1 and vectors>=1 and scalars+vectors==len(mothers):
            has_HEFT_vertex[i] = True; break
        final_lwf = final_lwf.get_loop_mother()
```
Emitted as Fortran `DATA (HAS_AN_HEFT_VERTEX(I),...) /.TRUE.,.FALSE.,.../` in chunks of 9.

## The HEFT-vertex definition (load-bearing rule, comment at 2237-2239)
"any vertex built up from ONLY massless vectors (spin 3, mass ZERO) and massive scalars
(spin 1, mass != ZERO), with at least one of each." The massive-scalar requirement is
deliberate: it removes the gluon-ghost false positive (ghosts are massless scalars).
Examples: ggH (hgg), and by extension hγγ effective vertices.

## Caution
- The detection is purely structural (spin + mass of the wavefunction mothers), not a
  model-declared "this is HEFT" flag. A model that gives its effective scalar a ZERO mass
  would NOT trigger the HEFT branch (and a massless-scalar+massless-vector vertex is
  treated like the ghost case). Watch this if reasoning about non-Higgs effective vertices.
