---
description: The four diagram-filter operators (/, $, $$, > >) differ along a VISIBILITY axis — which build artifact each surfaces in. Answers "from artifact X, which operators are detectable?" Probe-confirmed.
---

# Filter-operator visibility matrix

A deeper cut across the four per-artifact pages (parse-filter-operators,
diagram-filter-enforcement, dollar-filter-helas-realization,
schannel-config-carrier-and-sprop, filter-shell-string-naming). The unifying
principle: the four operators differ not only in WHAT they constrain but in
WHICH BUILD ARTIFACT each one is visible in. This page answers the inverse
("audit-direction") question those pages each answer only for one artifact:
**given artifact X, which of the four filters can I detect from it?**

## The matrix (v3.7.1, probe-confirmed; source per cell below)

| operator | diagram effect | process-LINE (`nice_string`) | dir-name (`shell_string`) | ME-code Fortran | config arrays |
|----------|----------------|------------------------------|---------------------------|-----------------|---------------|
| `/`  forbidden particles | DROP (prune in recursion) | visible `/ a` | **visible** `_no_a` | n/a (diagram gone) | n/a |
| `$$` forbidden s-channel | DROP (remove topology) | visible `$$ z` | INVISIBLE | n/a (diagram gone) | n/a |
| `$`  forbidden onsh s-ch | KEEP + mark onshell=False | visible `$ z` | INVISIBLE | **P1D + BWCUTOFF** | **gForceBW=2** |
| `> >` required s-channel | KEEP-ONLY matching | rendered inline `> z >` | **visible** `_z_` | n/a | (s-chan present) |

## The non-obvious inversion this catches
The intuition "a filter that changes the directory name is the heavy one" is
BACKWARDS. `$` is the MOST invisible at the name level — `u u~ > e+ e- $ z` gets
the SAME dir name as the unfiltered process (`1_uux_epem`) — yet the MOST
invasive at the code level: it is the ONLY operator that rewrites the generated
matrix-element Fortran (P1D routine + extra BWCUTOFF arg) AND the ONLY one that
writes a config-array value (gForceBW=2). The two DROP operators (`/`, `$$`)
leave no ME-code/config trace at all (the diagram they target is gone), so there
is nothing downstream to mark. `$$` is doubly invisible: invisible in the dir
name AND leaves no downstream marker — only the process-line and the diagram
count reveal it.

## Audit-direction lookup (what each artifact tells you)
- **Only the process line / `nice_string`:** all four are visible (the only
  artifact that shows every operator). Order emitted: `$` then `$$` then `/`,
  `> >` inline (diagram-filter-enforcement §round-trip).
- **Only the subprocess dir name:** you see `/` (`_no_X`) and `> >` (`_Z_`);
  you CANNOT distinguish a `$`- or `$$`-filtered process from the unfiltered one
  (filter-shell-string-naming).
- **Only the diagram count:** `/`, `$$`, `> >` change it (they drop/keep-only);
  `$` does NOT (it keeps all diagrams, marks one leg) — a `$`-filtered process
  has the SAME diagram count as unfiltered.
- **Only the ME Fortran (`matrix1.f`):** ONLY `$` is detectable (P1D/BWCUTOFF on
  the marked propagator call). `/`/`$$`/`> >` left no code marker.
- **Only `decayBW.inc`:** ONLY `$` is detectable (gForceBW=2). Note `sprop` in
  configs.inc is NEVER zeroed by any filter — do not infer a filter from sprop.

## Source per cell (all v3.7.1)
- Parse (which field each captures): `madgraph_interface.py` 5007-5041
  (parse-filter-operators).
- Diagram effect: `diagram_generation.py` — `/` prune 1014-1021; `> >` keep-only
  710-736; `$$` drop 742-776; `$` mark onshell=False 781-794
  (diagram-filter-enforcement).
- `nice_string` renders all four: `base_objects.py` 3158+ (probe:
  `u u~ > e+ e- $ z` -> `... $ z`; `$$ z`; `/ a`; `> z >`).
- `shell_string` renders only `/` (3484-3488) and `> >` (3460-3466); no
  `$`/`$$` block in 3433-3515 (filter-shell-string-naming).
- ME-code P1D/BWCUTOFF for `$`: `helas_objects.py` 1597-1600 (BWCUTOFF arg),
  1898-1899 (P1D tag) (dollar-filter-helas-realization).
- gForceBW=2 for `$`: `export_v4.py` write_decayBW_file 5884-5894; sprop never
  zeroed 2256 (schannel-config-carrier-and-sprop).

## Probe-confirmed (v3.7.1, sm)
`generate <line>; amp.get('process')` (shell/nice strings are stable outputs;
read diagram counts fresh — the stable claim is `$` = baseline, the other three
reduce):
- `u u~ > e+ e-`        -> shell `1_uux_epem`                     (baseline count)
- `u u~ > e+ e- $ z`    -> shell `1_uux_epem`,      nice `... $ z`  (count = baseline)
- `u u~ > e+ e- $$ z`   -> shell `1_uux_epem`,      nice `... $$ z` (count < baseline)
- `u u~ > e+ e- / a`    -> shell `1_uux_epem_no_a`, nice `... / a`  (count < baseline)
- `u u~ > z > e+ e-`    -> shell `1_uux_z_epem`,    nice `> z >`    (count < baseline)
Plus (dollar-filter-helas-realization / schannel-config-carrier probes):
`$ z` output -> matrix1_orig.f carries `FFV2_5P1D_3(...,BWCUTOFF,...)`,
decayBW.inc `DATA GFORCEBW(-1,2)/2/`.

## Boundary
This is the audit-direction synthesis; each cell's mechanism lives on its own
page. What the P1D routine COMPUTES is the aloha/helas-routine slice; the
bwcutoff WINDOW and gForceBW=2 runtime enforcement is bw-window/phase-space.
We own which-artifact-shows-which-operator.
