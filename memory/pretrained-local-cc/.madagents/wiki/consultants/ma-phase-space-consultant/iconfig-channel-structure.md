---
description: How ICONFIG channels are built from diagrams — output-side find_symmetry grouping + 4-vertex config exclusion, configs.inc tables, survey-side gensym/symfact.dat, BW-subdivision dconfig code.
---

# ICONFIG channel structure (one channel per surviving diagram)

MadGraph integrates with single-diagram enhancement: each kept Feynman diagram becomes one
integration channel (ICONFIG). The channel structure is fixed at `output` time in
`configs.inc`, then symmetry-grouped at survey time by the `gensym` executable.

## NOT every diagram is a channel — the 4-vertex exclusion (output side)
"Kept diagram" is narrower than "Feynman diagram". The operative LO/MadEvent copy of
`write_configs_file_from_diagrams` is in class `ProcessExporterFortranME`
(`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:5415`; `ProcessExporterFortranMEGroup` does NOT
override it, so this copy serves both grouped and ungrouped output). It computes `minvert` = the
minimum `vertex_leg_numbers` over diagrams (export_v4.py:5438), then **skips** (`continue`, never
increments `nconfigs`) any diagram with a vertex above `minvert` (export_v4.py:5447-5451) —
comment there: "Only 3-vertices allowed in configs.inc". (The base-class copy at export_v4.py:2162
carries the same logic with the longer comment "…except for vertices which originate from a shrunk
loop"; the MadWeight copy is at 4037. There are THREE copies — cite the ME one for LO output.)
So diagrams containing a 4-point/contact vertex (4-gluon, HHHH, WWWW, ...) get **no MAPCONFIG entry /
no ICONFIG channel** — their amplitude still contributes to the matrix element, but they are not a
phase-space channel.
- Probe (`g g > g g`): `matrix1_orig.f` has `NGRAPHS=6` amplitudes, but
  `configs.inc` has `MAPCONFIG(0)/3/` — only the s/t/u-channel diagrams are channels; the 4-gluon
  contact diagram is excluded. **NGRAPHS (amplitudes) >= nconfigs (channels)** in general.
- Consequence: the diagram-number a config maps to (`MAPCONFIG(c)`) is NOT always `c` once contact
  diagrams are interleaved; read MAPCONFIG, don't assume identity.

## configs.inc — the per-channel propagator chain (static, written at output)
Read example `q q~ > z > z > l+ l-` (`<PROC_DIR>/.../P1_qq_z_z_ll/configs.inc`)
and WBF `q q > h q q` (`<PROC_DIR>/.../P1_qq_hqq/configs.inc`).
Per config `c`, indexed by negative propagator index `-i`:
- `MAPCONFIG(c)` — diagram number this config maps to. `MAPCONFIG(0)` = number of configs.
- `IFOREST(1:2,-i,c)` — the two daughters of intermediate propagator `-i` (negative = another
  intermediate, positive = external leg). Defines the decomposition tree.
- `SPROP(iproc,-i,c)` — s-channel propagator PDG of `-i` (per subprocess `iproc`, dim `maxsproc`).
  Nonzero only for s-channel branches; `0` for t-channel branches.
- `TPRID(-i,c)` — t-channel propagator PDG of `-i`. Nonzero only for t-channel branches; `0` for
  s-channel. (s and t are mutually exclusive per branch: WBF config 1 has TPRID=23/23/2, SPROP all 0;
  s-channel config 4 has TPRID=0, SPROP=23.)
- `TSTRATEGY(c)` — per-config t-channel handling strategy (1 or 2; see genps `one_tree` ping-pong).
- `FAKE_ID` — placeholder id emitted when a config has no real s-prop (DY example: `FAKE_ID/7/`).

## The syntax->channel seam — one config PER diagram via get_s_and_t_channels
The decay-chain syntax becomes integration channels at exactly one loop in
`write_configs_file_from_diagrams` (ProcessExporterFortranME, export_v4.py:5447 `for iconfig,
helas_diags in enumerate(configs)`). The chain has ALREADY been flattened upstream: a
`DecayChainAmplitude`'s production+decay diagrams are spliced into single combined diagrams by
`insert_decay_chains` (helas_objects.py:3940) BEFORE the writer runs — so by output time the writer
just sees ordinary flat diagrams; the chain resonances are interior propagators of each diagram.
(The splicing/flattening itself is the **helas/diagram-generation slice's** territory; my slice owns
from the flattened diagram onward.)
- Per kept diagram (after the 4-vertex `continue`, export_v4.py:5448-5451 — applies to chain diagrams
  identically), the writer calls `h.get('amplitudes')[0].get_s_and_t_channels(ninitial, model,
  new_pdg)` (export_v4.py:5462-5464). This walks the diagram tree from the final-state externals
  inward and splits its propagators into an **s-channel vertex list** (`schannels`) and a t-channel
  list. The chained resonances (t->bW, W->ev) are precisely the s-channel vertices in `schannels`;
  they become the SPROP/IFOREST rows of this config. So **one chain diagram -> one config**, and the
  chain's propagators -> that config's s-channel branches.
- Each s-channel vertex leg is built carrying `'onshell': mother.get('onshell')`
  (helas_objects.py:1966, in `HelasWavefunction.get_s_and_t_channels`). That onshell flag (True for a
  `>`-decayed leg, False for a `$`-forbidden leg, None otherwise) is what `write_decayBW_file` reads
  via `booldict` (export_v4.py:5884) into gForceBW (see gforcebw-cut_bw-onshell.md). So the full
  static pipeline is: `>`-syntax -> leg.onshell -> get_s_and_t_channels s-channel vertex leg ->
  {configs.inc SPROP row, decayBW.inc gForceBW=1}. The configs.inc resonance and its forced-BW flag
  are written from the SAME s-channel vertex in the SAME per-diagram pass.
- `s_and_t_channels.append([schannels-of-first-subproc, tchannels, tstrat])` (export_v4.py:5480-5481)
  is the SINGLE structure consumed by all three writers in this pass: configs.inc
  (write_configs_file_from_diagrams itself), props.inc (write_props_file, mass/width per propagator),
  decayBW.inc (write_decayBW_file, gForceBW per s-channel leg). The three runtime tables a channel is
  read from at integration are co-emitted from one per-diagram s/t decomposition.
- **The proof of co-emission is the CALLER seam, not the producer.** `write_configs_file` returns the
  one `s_and_t_channels` (export_v4.py:4453, ME `generate_subprocess_directory`), and the SAME variable
  is then handed to `write_decayBW_file` (export_v4.py:4475-4476) and `write_props_file`
  (export_v4.py:4519-4521) — plus `write_config_subproc_map_file` (4462-4463). One list, three writers,
  same `iconf` index. So SPROP[c] and gForceBW[c] are not merely "from the same logic" — they read the
  SAME `s_and_t_channels[c][0]` schannels list at the same index.
- **Same vertex, same leg — verified.** For an s-channel branch, configs.inc keys its SPROP row by
  `last_leg = vert.get('legs')[-1]` and carries that leg's `id` (the propagator PDG)
  (export_v4.py:5525,5533,5536-5538); decayBW.inc keys gForceBW by `leg = vertex.get('legs')[-1]` and
  carries that SAME leg's `onshell` flag through `booldict` (export_v4.py:5891,5894). SPROP and gForceBW
  for a branch are two attributes (`id`, `onshell`) of one `Leg` object — co-emitted, never reconciled
  across separate passes.

## symfact_orig.dat — symmetry grouping decided at OUTPUT (find_symmetry)
The `symmetry` array that becomes `symfact_orig.dat` is computed at `output` time by
`diagram_symmetry.find_symmetry(...)`
(`$MADGRAPH_INSTALL/madgraph/various/diagram_symmetry.py:70`), written by `write_symfact_file`
(the call site is `find_symmetry(matrix_element)` on the ungrouped ME path, export_v4.py:4525, and
`find_symmetry(subproc_group)` on the grouped path, export_v4.py:6468 — same function, two callers)
(`ProcessExporterFortranME`, export_v4.py:6149 — note it drops symmetry==0 entries via
`if s != 0`). Mechanism:
- Each config diagram gets a `DiagramTag` (diagram_symmetry.py:147); diagrams with **identical tags**
  are external-particle permutations of the same diagram (same topology) and form one class.
- The representative (first in its class, `idx2==0`) gets `symmetry[inum] = len(class)` (positive
  multiplicity, diagram_symmetry.py:165); every other member gets `symmetry[inum] = -<first diag #>`
  (negative pointer to the representative, line 167). This positive/negative convention is exactly the
  `use_config` semantics gensym later reads.
- Early-out: if `identical_particle_factor == 1` (no identical particles), all configs get `symmetry=1`
  — no grouping (diagram_symmetry.py:126-129). Example: `e+ e- > 3a` returns `[6,-1,-1,-1,-1,-1]`
  (docstring line 78) — config 1 is integrated with multiplicity 6, configs 2-6 are its mirrors.
- 4-vertex diagrams get `symmetry=0` here too (diagram_symmetry.py:118-123, 142-145), consistent with
  the configs.inc exclusion above.
So: the OUTPUT side (`find_symmetry`) DECIDES the grouping and writes `symfact_orig.dat`; the SURVEY
side (`gensym`) READS it and emits the integrated channel list. The two must agree.

## symfact.dat — symmetry grouping read at survey (gensym/symmetry.f)
The `gensym` executable is built from `$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_symmetry.f`
(`program symmetry` at madevent_symmetry.f:2, written into `<P>/symmetry.f` by `write_symmetry`,
`ProcessExporterFortranME`, export_v4.py:5989).
- It `open`s `symfact_orig.dat` (written by MG5 at output) into `use_config(j)`
  (madevent_symmetry.f:127-134; note the in-source comment at :125 misleadingly says "symfact.dat"
  but the actual `open(unit=25, file='symfact_orig.dat')` is at :127).
- `write_bash` (madevent_symmetry.f:141) loops configs; for `use_config(i)>0` it emits the config to
  stdout (the ICONFIG list gensym returns to gen_ximprove) and writes `symfact.dat` line
  `mapconfig(i)  use_config(i)`. `use_config(i)<=0` configs are symmetry-mirrors of another config and
  are NOT integrated separately (their line carries the negative pointer to the surviving config).
- `symfact.dat` line `1  1` (DY example) = config 1 integrated with multiplicity 1.

## BW subdivision — the dconfig fractional code
For configs with on-shell-conflicting BWs, gensym subdivides one ICONFIG into several
"sub-channels" distinguished by a fractional `dconfig` (e.g. `12.001`). Mechanism in
madevent_symmetry.f `write_bash`:
- `BW_Conflict` (line 286) flags propagators whose BWs conflict (can't all be on-shell at once).
- `bw_increment_array` / `enCode` (line 226,265) enumerate base-3 codes over the conflicting BWs;
  `ncode=int(dlog10(3d0)*(max_particles-3))+1` digits.
- Each non-failing code becomes a separate channel `dconfig=mapconfig(i)+icode/10**ncode`.
- `failConfig` (line 434) drops impossible BW combinations.
The fractional part is decoded back at integration by `get_user_params` in the driver
(`DeCode(jconfig,lbw(1),...)`, madevent_driver.f:347) into the `lbw` array consumed by myamp.

## gen_ximprove.gensym (python side)
`$MADGRAPH_INSTALL/madgraph/madevent/gen_ximprove.py:61` class `gensym`. `launch` (line 326)
compiles+runs the `gensym` Fortran exe per subprocess dir, captures stdout = whitespace channel list
(line 373 `jobs = stdout.split()`), and creates one survey job per channel. `gensym.combining_job`
(channels per ajob) starts at the **class default** registered at gen_ximprove.py:70 (read the
`combining_job` class attribute there) and is reassigned only in `gensym.__init__`:
- run_card `survey_nchannel_per_job` override (gen_ximprove.py:112-113): requires BOTH the value
  `!= 1` AND the key in `run_card.user_set` (i.e. the user actually set it). So the channels-per-job
  is run-card-tunable, not fixed at 2.
- `elif self.run_card['hard_survey'] > 1: self.combining_job = 1` (gen_ximprove.py:114-115). The `=1`
  override fires on **`hard_survey > 1`** — NOT on gridpack mode. (Earlier I mis-attributed line 115
  to gridpacks; the gate is `hard_survey`. Gridpack-specific `combining_job` handling lives in the
  *refine* subclasses `gen_ximprove*` at gen_ximprove.py:1860-1862, a different class, not `gensym`.)

## Cautions
- `SPROP` is dimensioned `(maxsproc, ...)`: a single config can carry different s-prop PDGs across
  subprocesses that share one symmetry channel — myamp picks the first nonzero `iproc`
  (myamp.f:108-113).
- `use_config<=0` channels never integrate; reading configs.inc alone overcounts channels — the
  real ICONFIG count comes from symfact.dat positive entries plus BW subdivisions.
