---
description: How the four captured filter fields constrain diagram enumeration in diagram_generation.py (drop vs mark-onshell-False).
---

# Filter enforcement in diagram generation

File: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` (v3.7.1). The four
Process fields captured by the parser (see parse-filter-operators) are consumed
here while building the amplitude. Three of the four DROP diagrams; the `$`
filter MARKS surviving propagators instead.

NOTE: the recursion/DiagramTag enumeration ALGORITHM itself is the
diagram-enumeration slice. This page is the parser-fields -> constraint mapping.

## Two-phase application order (`/` in-recursion vs s-channel three post-recursion)
The four operators do NOT fire at the same point of `generate_diagrams`:
- **`/` (forbidden_particles) is applied DURING `reduce_leglist`** (1014-1021):
  inside the per-candidate loop, a leg-vertex pairing is `continue`d (the whole
  branch pruned) if ANY merged vertex's outgoing leg
  `abs(vertex.get('legs')[-1].get('id'))` is in `forbidden_particles` (1017-1021).
  Because every internal propagator is the outgoing leg of some intermediate
  vertex during reduction, this prunes the particle off internal/t-channel lines
  AS the diagram is built — it shrinks the search space, it does not post-filter.
- **`> >`, `$$`, `$` are applied POST-recursion** on the completed diagram list,
  in this FIXED sequence: required_s_channels (715-736) -> forbidden_s_channels
  `$$` (742-776) -> forbidden_onsh_s_channels `$` (781-794). They run only on
  whatever survived reduction (and the `/` prune).
Probe recipe (v3.7.1, sm): `generate u u~ > e+ e-`, then `/ a`, then `$ z`;
count diagrams each (read fresh). Stable result: `/ a` PRUNES the photon
s-channel diagram (count drops); `$ z` KEEPS every diagram and marks
onshell=False on the s-channel leg of EACH diagram that carries the forbidden
propagator (count unchanged vs baseline). Confirms `/` drops, `$` keeps+marks.
Derivation rule for #marked legs: = #diagrams whose s-channel is the forbidden
particle (for this DY topology that is 1 — the lone Z s-channel; derive per
process, do not assume 1).

## decay-chain `lastvx=-2` is REQUIRED-only
The "exclude the artificial 1=1 decay vertex" adjustment (`lastvx=-2` when
`is_decay_proc`, 719-723) is applied ONLY in the required_s_channels block. The
`$$` block (742-776) and the `$` block (781-794) both walk `vertices[:-1]`
UNCONDITIONALLY (no `is_decay_proc` branch). So in a decay-chain process, `> >`
skips the last two vertices but `$$`/`$` skip only the last one.

## `$$` non-`ninitial==2` path is a `for...else` keep-rule (750-776)
For ninitial != 2 the diagram is KEPT (`newres.append`, 775) only if the vertex
loop completes WITHOUT `break` — i.e. no forbidden s-channel was hit. The `leg1`
tracking (755-769) inverts the lookup when leg 1 sits in the last vertex, to
avoid forbidding the INITIAL particle's own first s-channel. (ninitial==2 uses
the simple `any(... in forbidden_s_channels for vertex in vertices[:-1])`,
744-749.)

## Filters are carried VERBATIM to every expanded Process
`ProcessDefinition.get_process_with_legs` (base_objects.py:4120-4139) builds each
per-leg-content Process by copying all four filter fields straight from the
ProcessDefinition (4129-4132); the order-finder builds its candidate Processes
the same way (diagram_generation.py:2067-2080). So in a multiparticle process
(`define p = ...; generate p p > X $ z`) the SAME id-list applies to EVERY
expanded subprocess — there is NO per-combination remapping. Probe (v3.7.1, sm):
`define p = u u~ d d~ g; generate p p > e+ e- $ z` -> 2 subprocs, both carry
`forbidden_onsh_s_channels == (23,)`.

## Crossing-symmetry reuse is DISABLED for s-channel filters / decay chains
The fast "reuse a crossed amplitude by relabeling legs" path
(`success_procs`/`cross_amplitude`, 1857-1885) fires ONLY when `required_s_channels`,
`forbidden_onsh_s_channels` (`$`), `forbidden_s_channels` (`$$`),
`is_decay_chain` are ALL empty/false AND no `diagram_filter` (1857-1860). A
process bearing any of `$`/`$$`/`> >` (or a decay chain) is regenerated from
scratch, not reused. NOTE `forbidden_particles` (`/`) is NOT in this guard list —
a `/`-only process CAN still reuse crossings. (Separate from the `failed_procs`
cache at 1815, which is UNGUARDED in this main path — unlike the order-finder's
1815-analog at 2095 which exempts `$$`; see §"Filters are NOT part of process
identity" below.)

## The shared predicate: `get_s_channel_id` (base_objects.py:2435)
All THREE s-channel filters (`$`, `$$`, `> >`) match against
`vertex.get_s_channel_id(model, ninitial)` — the id of the vertex's last leg
"as an outgoing s-channel". Its semantics (2435-2468):
- Returns `0` for a t-channel leg (`state == False` with ninitial>=2, 2453-2456),
  for an identity/`id==0` vertex (2453-2456), and for a `loop_line` (2458-2460).
  So t-channel propagators can NEVER be filtered by `$`/`$$`/`> >` — these are
  s-channel-only operators by construction.
- It is SIGN-SENSITIVE. For ninitial>=2: if the leg `number > ninitial` it
  returns `leg.get('id')`; else (leg came from initial side) it returns the
  ANTI pdg (`get_anti_pdg_code()`, 2464-2468). For ninitial==1 it flips the
  sign for `state == False` legs (2443-2450).
- Because both the captured filter id (get_pdg_code, signed — see
  parse-filter-operators) and this predicate are signed and NO `abs()` is
  applied in the s-channel filter blocks (715-794), the SIGN must agree with
  the outgoing-s-channel direction. `$ w+` vetoes the W+ outgoing-direction
  propagator; `$ w-` the W- direction. Contrast `/` below, which uses `abs()`.

## `forbidden_particles` (`/`) — prune the branch by the INTERNAL propagator it creates
Lines 1016-1021 (inside `reduce_leglist` recursion): a candidate
leg-vertex pairing is skipped (`continue`) if any vertex's outgoing leg id
(`abs(vertex.get('legs')[-1].get('id'))`) is in `forbidden_particles`. The
`abs()` is at `:1018` (the field name `forbidden_particles` continues on `:1019`
— a citation of the abs as `:1019` is off by one; verify `:1018` in
3.7.1). Probe-anchored: `/ ta+` and `/ ta-` are equivalent and BOTH exclude
PDG ±15; `/ z ta+`, `/ ta+ ta- z`, `/ z ta+ ta-` all kill both τ charges; order
inside the `/` list is irrelevant; either τ charge alone suffices
(WW-mediated H→ττνν, `/ ta+ z` → 0 FFS4_3/GC_99 calls).

INTERNAL PROPAGATORS ONLY (corrects an earlier "internal or external" phrasing).
The tested leg is `vertex.get('legs')[-1]` — and that last leg is the FRESHLY
CREATED merged/outgoing leg, appended LAST in `merge_comb_legs`
(`diagram_generation.py:1218-1221`: `myleglist = LegList(list(entry))` then
`myleglist.append(myleg)`; `myleg` built by `get_combined_legs:1255-1262`). The
external legs being combined are the inputs (`legs[:-1]`), never the tested
`[-1]`. The overall process's external final-state legs enter as the initial
`curr_leglist` consumed by the recursion and are never the outgoing `[-1]` of a
propagator-creating merge (the closing `id=0` vertex via `can_combine_to_0:990-992`
uses `curr_leglist` directly, doesn't append). So `/` prunes branches by the
INTERNAL propagator they would build, NOT by external legs. Consequence: a final
state named in the process line is untouched — `generate ... h > ta+ vt ta- vt~
/ ta+ z` still has external τ⁺ν τ⁻ν̄; `/ ta+` forbids only an internal τ
propagator (e.g. the Yukawa-Hττ topology where H couples to a τ-line and a
daughter τ radiates W*→τν). `abs()` => particle and antiparticle both forbidden
REGARDLESS of sign captured at parse. NOTE the field is ALSO abs()-ed when
`set()` on the Process (base_objects.py:3106-3108) — stored ids already positive
by enforcement time; the abs() at 1018 is belt-and-braces. KEY asymmetry vs the
three s-channel filters: `/` is symmetric (abs), s-channel filters are signed
(no abs, match get_s_channel_id direction). Applies on ANY internal propagator
(s- AND t-channel — it is NOT s-channel-restricted, unlike `$`/`$$`/`> >`), but
NOT external legs.

## `required_s_channels` (`> >`) — keep only diagrams containing the propagator
Lines 710-736. List-of-lists semantics: outer list = OR, inner list = AND
(comment 710-714). For each `id_list`, keep diagrams where every `req_s_channel`
appears among `vertex.get_s_channel_id(model, ninitial)` over
`diagram.get('vertices')[:lastvx]`. `lastvx=-1` normally, `-2` for decay-chain
(skips the artificial 1=1 vertex, 719-723). Results unioned without dup (736).

## `forbidden_s_channels` (`$$`) — drop diagrams with the propagator as s-channel
Lines 742-776. Two code paths by `ninitial`:
- `ninitial == 2` (744-749): drop diagram if ANY non-final vertex
  (`vertices[:-1]`) has `get_s_channel_id` in `forbidden_s_channels`.
- else (750-776): walks vertices tracking leg 1 to avoid forbidding the
  initial-state particle's own first s-channel; more conservative.
Off-shell included: this removes the diagram topology entirely.

## `forbidden_onsh_s_channels` (`$`) — MARK propagator leg `onshell=False`
Lines 779-794. Does NOT drop the diagram. For every non-final vertex whose
`get_s_channel_id` is in `forbidden_onsh_s_channels`, the resulting (last) leg
is copied and `newleg.set('onshell', False)` (793). This is the SAME `onshell`
leg field that chain-decay sets to `True`.
- Early-out optimization (1857-1859): a fast path is taken only when
  required/forbidden_onsh/forbidden_s are all empty.
- Reset path (828-830): when gluing the final id=0 vertex for a non-decay-chain
  process, a leg with `onshell == False` is reset to `None` ONLY when it becomes
  the final-state leg (it is no longer an internal s-channel there).

## `onshell` leg field (base_objects.py)
`$MADGRAPH_INSTALL/madgraph/core/base_objects.py`:
- 2111-2112: comment "onshell: decaying leg (True), forbidden s-channel
  (False), none (None)"; default `self['onshell'] = None`.
- 2138-2140: validator requires bool/None.

## Downstream of `onshell=False`: gForceBW=2
`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py` `write_decayBW_file`
(5879-5899): `booldict = {None: "0", True: "1", False: "2"}` (5884); writes
`data gForceBW(<legnum>,<iconf>)/<code>/` per s-channel leg (5892-5894). So the
`$` filter's `onshell=False` becomes `gForceBW=2` in `decayBW.inc`.
(write_decayBW_file is the shared emission point with chain-decay; that slice
owns the True->1 case.)

## Runtime meaning of gForceBW=2 (boundary note)
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/myamp.f` `cut_bw` (function at
line 2): if a propagator is on-shell AND `gForceBW(i,iconfig).eq.2 .and.
sde_strat.eq.1` then `cut_bw=.true.; return` (142-144) — hard rejection of the
on-shell-forbidden channel. Detailed runtime/phase-space behaviour (sde_strat,
bwcutoff) is the bw-window / phase-space slices. We own that `2` is PRODUCED by
the `$` filter.

## Filters are NOT part of process identity (base_objects.py:3716-3795)
`Process.__eq__` (3787-3795) delegates to `compare_for_sort` ->
`list_for_sort` (3716-3729), which is ONLY
`[id, sorted(initial ids), sorted(final ids), sorted(decay-chain list_for_sorts)]`.
The four filter fields do NOT appear. So two Process objects that differ only by
a `/`/`$`/`$$`/`> >` filter compare EQUAL. Consequence for multiprocess
generation:
- The crossed-process failure cache (`failed_procs`) keys on `sorted_legs`
  alone (diagram_generation.py:1815, 2095). A process whose leg-content already
  failed is skipped without re-checking — EXCEPT the order-finder guards this
  with `and not process_definition.get('forbidden_s_channels')` (2095): a `$$`
  filter forces a re-check rather than trusting the leg-only cache, because the
  `$$` topology removal can change whether a same-legs process has any surviving
  diagram. (`$`, `/`, `> >` get no such exemption in that guard — only `$$`.)
- Practical reader caution: do not assume "same final state => same diagram
  count" across two `add process` lines that differ only in filters; identity
  ignores the filter, the amplitude does not.

## Serialization round-trip (`nice_string`, base_objects.py:3261-3279)
When a Process is printed back to a process line, `required_s_channels` is
rendered INLINE as the middle `> ... >` group, and the three trailing operators
are emitted in this fixed order: `$` (forbidden_onsh) at 3261-3265, then `$$`
(forbidden_s) at 3268-3272, then `/` (forbidden_particles) at 3275-3279. This is
a DIFFERENT order than parsing (parse strips `/` FIRST, then `$$`, then `$` —
see parse-filter-operators). The round-trip is still parse-stable because the
parser keys on the operator tokens, not their order. Probe-confirmed (v3.7.1,
sm): a Process with all four set prints
`u u~ > g > e- e+ $ z $$ h / a`. Other string forms
(`input_string`, `base_string`, `shell_string`) carry parallel blocks at
3363-3379, 3050-3070-region, and 4050-4066; `get_final_legs_with_decays`-style
dict export lists all four fields at 4129-4132.

## Cautions
- `$` (onsh) and `$$` differ fundamentally: `$$` removes the topology; `$` keeps
  it and only vetoes the on-shell region at integration. A user wanting the
  diagram gone entirely needs `$$`, not `$`.
- SILENT-FAIL TRAP (e.g. pure-γ Drell-Yan `q q~ > a > l+ l-` / "Z s-channel
  forbidden"): writing `$ z` does NOT remove the Z diagram — the `$` block
  (781-794) only marks one leg `onshell=False` and KEEPS the diagram, so at LO
  this leaves a HYBRID γ+Z amplitude, not the pure-γ piece. The byte-identical
  γ-only LO ME is produced by `$$ z` (drop topology), `/ z` (drop particle
  everywhere — LO-equivalent here since Z appears only on the single s-channel),
  or `a > l+ l-` (require γ s-channel). The TELL is the diagram count (read
  fresh; recipe `generate q q~ > l+ l-` then each variant): baseline = γ+Z;
  `$$ z`/`/ z`/`a > l+ l-` collapse to γ-only (count drops); `$ z` leaves the
  count EQUAL to baseline -> the Z diagram was kept, `$` did NOT forbid it.
  What the kept-Z propagator computes under `$` (Breit-Wigner principal-value /
  P1D routine / BWCUTOFF control) is bw-window/aloha — this slice owns only that
  `$` swaps the propagator treatment rather than removing the diagram.
  Z/γ SEPARATION (probe recipe v3.7.1 sm: `generate u u~ > e+ e-`, then `$$ a`,
  then `$$ z`; count fresh): base = γ+Z; `$$ a` = Z-only (photon s-channel
  dropped); `$$ z` = γ-only. Each single-`$$` here drops one diagram because DY
  has exactly one γ and one Z s-channel; in general `$$ X` drops ALL diagrams
  whose s-channel is X (derive the count per topology, not "one"). The two
  `$$` singles do NOT sum to the full ME — the γ–Z interference term lives only
  in the full (unfiltered) amplitude and is lost by either drop.
- `$` KEEPS-vs `$$` DROPS, count-confirmed on a top resonance (probe recipe
  v3.7.1 sm: `generate p p > w+ w- b b~`, then `$ t t~`, then `$$ t t~`; compare
  per-subprocess diagram counts fresh): `$ t t~` retains MORE diagrams than
  `$$ t t~` in every subprocess (gg and each qq̄) — `$` keeps the s-channel-tt̄
  topologies and only marks their propagator legs onshell=False, `$$` removes
  them. This is the canonical semi-off-shell-top use case for `$`.
- The `gForceBW=2` rejection is gated on `sde_strat.eq.1` (142). Whether that
  branch is active for a given process is a phase-space/integration question
  (not this slice).
- `$`/`$$`/`> >` are S-CHANNEL ONLY: `get_s_channel_id` returns 0 for t-channel,
  identity, and loop legs (base_objects.py:2453-2460), so a t-channel exchange
  cannot be forbidden/required by these. To exclude a particle from a t-channel
  leg, use `/` (it filters any INTERNAL propagator, s- AND t-channel — but never
  an external leg). Conversely `/` cannot target only the s-channel — it removes
  the particle from every internal line.
- PARTIAL-FILTER-LEAK TRAP (topology-gate diagnostic; sibling to the `$ z`
  silent-fail above): when MORE THAN ONE internal propagator mediates an
  unwanted topology, forbidding only one leaks the rest. WW-mediated-only
  H→ττνν (`generate p p > h j j QCD=0, h > ta+ vt ta- vt~ / ...`). Two internal
  propagators carry non-WW H-decay topologies — `z` (PDG 23: H→Z*Z*→ττνν) and a
  τ propagator (PDG 15: Yukawa-Hττ where H couples to a τ-line via FFS4_3/GC_99
  and a daughter τ radiates W*→τν). `/ z` ALONE is INSUFFICIENT: it kills H→Z*Z*
  but leaves the Yukawa+W hybrids. Recipe (counts read fresh; these were
  anchored runtime observations, not re-probed here — HYPOTHESIS until
  re-probed): compare the surviving FFS4_3/GC_99 (Hττ Yukawa) call count under
  `/ z` vs the fully unfiltered form — `/ z` leaves a NONZERO Yukawa-call count
  (hybrids survive); only `/ ta+ z` (forbid BOTH) drives it to 0 (fully gated).
  The TELL is the FFS4_3/GC_99 vertex-call count, NOT just the diagram count
  (count the `/ ta+ z` 4-body form `P1_qq_hqq_h_tapvltamvl` and the explicit
  WW-chain form fresh — they are NOT diagram-count-equal, being different
  process specs). Rule of thumb when gating a final state to one
  mediator: enumerate EVERY internal propagator that can reach that final state
  and forbid them all; a single-particle `/` is a partial gate that silently
  leaks. (FFS4_3-call count is a diagram-enumeration fingerprint; this slice owns
  that `/` is the gate and which propagators it must list.)
- Sign matters for s-channel filters but not for `/`. A user forbidding "the W
  propagator" generically must consider both `$ w+` and `$ w-` (or use the
  particle that maps to the relevant outgoing direction); `/ w+` already covers
  both signs via abs().
- GAUGE-INVARIANCE HAZARD (boundary caution). A gauge-invariant tree amplitude
  is a SUM over diagrams whose unphysical (longitudinal / gauge-dependent) pieces
  cancel among each other. All four operators alter that set: `/`, `$$`, `> >`
  DROP diagrams (1014-1021 / 742-776 / 710-736); `$` swaps a propagator's
  on-shell treatment (781-794). Removing or re-treating a proper subset can leave
  the Ward-identity cancellation incomplete -> the result becomes gauge-dependent.
  This is source-visible only as the diagram-removal MECHANISM (my slice); MG5
  emits NO warning that a filter broke gauge invariance — it is a silent physics
  consequence. The remedy the docs point to, `check gauge`, is a real command
  (`do_check` madgraph_interface.py:4065; gauge branch invokes
  `process_checks.check_gauge` at :4622; def process_checks.py:3060. The earlier
  :1643 `if args[0] in ['gauge']` and :3000 help-list are only arg-validation/help,
  NOT the execution point) but is
  owned by the process-syntax slice, and WHETHER a given filter actually breaks
  gauge invariance is a physics judgment (physics slice). I own only: the filters
  do modify the diagram set, so the hazard is real; routing the gauge test and
  the physics verdict is elsewhere. Most acute for `/`/`$$` on a massive-vector
  s-channel where the removed diagram carried a gauge-cancelling piece (e.g.
  forbidding one of γ/Z in a Drell-Yan-like set). INFERRED (mechanism cited;
  gauge-breaking is a physics inference, not a source guard).
- `apply_user_filter` (810-811, the `--diagram_filter` Python-callable option)
  is a DISTINCT user filter, not one of the four `/$$$>>` operators — out of
  this slice (diagram-enumeration / output options).
