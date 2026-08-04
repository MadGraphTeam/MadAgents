---
description: FKSDiagramTag + link_rb_configs born<->real configuration linking, find_fks_j_from_i, and the fks_tag.py MultiTagLeg/TagLeg tagged-final-state objects.
---

# Born-real config linking and tagged-particle legs

## FKSDiagramTag (fks_common.py:40)
Subclass of `diagram_generation.DiagramTag` whose `link_from_leg` returns
`[((id, number), number)]` — the leg `number` is excluded from tag *comparison*
but retained to extract leg permutations between born and real (`:44-50`).

## link_rb_configs (fks_common.py:66)
For each born diagram (configuration), finds the real configuration with the
ij → i j splitting. Builds `shift_dict` mapping real leg positions to born leg
positions accounting for the inserted i and removed-then-reinserted ij (`:79-89`).
Restricts to "born-level" diagrams via `minvert` (smallest max-vertex-size) so
only 3-point-function configs are used (`:91-105`). Called from
`FKSProcess.link_born_reals` (`fks_base.py:847`) — but only when EVERY splitting
type is `['QCD']`; otherwise it logs at **INFO** (`'link_born_real: skipping
because not all splittings are QCD'`, `:856`) and returns early. The gate scans
ALL fks_infos on ALL reals (`:853-857`) — a SINGLE non-`['QCD']` splitting anywhere
disables rb_links for the **whole born process**, not just that real. So rb_links
are strictly QCD-only and all-or-nothing per born.

## find_fks_j_from_i (fks_base.py:469)
Per real, builds `fks_j_from_i[i] = [j...]`: for each final-state i and each other
leg j and each perturbation order, uses `combine_ij` to form the underlying born,
sorts, and checks the born pdgs are in `born_pdg_list`. Records valid j's. This
identifies which collinear partner j each emitter i can recombine with.

## combine_ij (fks_common.py:459)
Inverse of split: checks if FKS legs i,j combine to ij. Requires
`i.id in soft_particles`, `j.id in pert_particles`, i final-state, and a
`not_double_counting` condition (j not a massless vector unless i is too / j
initial, plus the particle-antiparticle ordering rule, `:469-478`). Returns the
combined leg(s) as FKS legs.

## Tagged particles (fks_tag.py)
`MultiTagLeg(MG.MultiLeg)` (`:25`) and `TagLeg(MG.Leg)` (`:54`) each add a single
boolean key `is_tagged` (default False) for semi-inclusive / UPC analyses. The
`is_tagged` flag is read throughout find_splittings/find_reals/generate_virtuals
to apply the same-PDG and UPC carve-outs.

## Cautions
- rb_links exist only for purely-QCD splittings; mixed/EW reals get no rb_links,
  which downstream (FKS exporter) must handle.
- `link_rb_configs` raises `FKSProcessError` if real has != born+1 legs (`:76-77`).
