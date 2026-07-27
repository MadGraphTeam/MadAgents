---
description: has_born=False (loop-induced) as the single master switch rerouting MadLoop at every layer — generation, order guessing, color, runtime init (MG5_aMC v3.7.1)
---

# Loop-induced and the `has_born` master switch

Loop-induced = a process whose born amplitude is empty, so the virtual is squared against ITSELF. The single carrier of this state is the process key `has_born` (`LoopAmplitude['has_born']`, default True at `$MADGRAPH_INSTALL/madgraph/loop/loop_diagram_generation.py:69`). `LoopInducedMultiProcess.get_amplitude_from_proc` sets it False (`:1794`). It is also re-derived from emptiness at generation time: `:658-660` `has_born = born_diagrams!=[]` (born requested but none generated ⇒ becomes loop-induced).

This one flag reroutes behavior at every layer of the subtree. The instance pages document each thread in operational detail; this page is the cross-axis map so a future-me on any one page sees the parallel reroutes.

## The reroutes (False ⇒ loop-induced path)

1. **Diagram generation** — born generation skipped (`:635` guarded by has_born); `set_Born_CT` (UVtree + wavefunction renorm) skipped entirely (`:764` guard) — loop-induced has NO UVtree/WF-renorm CTs, only R2/UVmass/UVloop from `set_LoopCT_vertices`. See ./loop-diagram-generation.md, ./counterterm-structure.md.
2. **Order guessing** — the normal born-derived WEIGHTED bound is replaced by the no-born formula `squared_orders['WEIGHTED'] = 2*(loop min WEIGHTED + max(pert wgts) - min(pert wgts))` (`:776-783`, fires only when not has_born and no user orders). See ./loop-order-guessing.md.
3. **Loop color basis** — `compute_loop_nc=True` (independent closed-loop Nc-power tracking, the expensive double `full_simplify`) is used only for the loop-induced + MadEvent path; otherwise `loop_Nc_power=None`. The flag lives on `LoopColorBasis` (loop_color_amp.py :41); its True-value is threaded in by the loop-induced MadEvent export (`compute_color_flows=True`, `SubProc_prefix='PV'` at `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:9995-10004`). See ./loop-color-basis.md.
4. **Runtime init / stability** — loop-induced subprocess dirs carry the `PV` prefix and have `loop_matrix.f` but NO `born_matrix.f`. `run_initialization` keys on the ABSENCE of `born_matrix.f` (`$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py:7489`) to bump the init PS-point attempt counts higher than the has-born defaults (read both the default attempts :7451 and the loop-induced bump :7489-7493) because the zero-contribution reference scale is dynamic. `StabilityCheckDriver_loop_induced.f` hard-zeroes BORN/1EPS/2EPS and reports `FIN=MATELEM(1,0)` unnormalized (no born to divide by). See ./madloop-init-and-stability.md.
5. **Reduction-library default — STANDALONE-ONLY** — `LoopProcessExporterFortranSA.finalize` (`$MADGRAPH_INSTALL/madgraph/loop/loop_exporters.py:261-274`) forces `MLReductionLib`→a Collier-first chain + `COLLIERComputeUVpoles/IRpoles`→`.FALSE.` when `has_loop_induced` (read the forced value at loop_exporters.py:264). BUT this fires ONLY for `output standalone`. The MadEvent loop-induced path (`LoopInducedExporterME.finalize` :3131) does NOT call super().finalize(), so a MadEvent `output` keeps the Ninja-first MadLoopParams.dat default (probe-confirmed: `g g > z [noborn=QCD]` kept the commented default chain, UVpoles `.TRUE.`). Do NOT claim Collier-first for the MadEvent loop-induced path. See ./madloop-params-runtime-knobs.md.

## Probe-confirmed (v3.7.1)

`generate g g > z [noborn=QCD]; output` ⇒ subprocess dir `PV0_0_1_gg_z`, proc_prefix `ML5_0_0_1_`, contains `loop_matrix.f`, NO `born_matrix.f`. This is exactly the artifact state the `:7489` init bump keys on. Confirms the runtime reroute trigger.

## Mixing loop-induced + has-born is rejected — but the raise is in the INTERFACE layer, not the loop layer

`create_loop_induced` (`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:5357`, the handler for `add process ... [noborn=...]`) carries the cross-subprocess guard, NOT loop_diagram_generation. Two checks:
- **Pre-gen** (`:5408-5410`): `if self._curr_amps and (not isinstance(self._curr_amps[0], LoopAmplitude) or self._curr_amps[0]['has_born']): raise InvalidCmd("Can not mix loop induced process with not loop induced process")`. Fires when a `[noborn]` process is added onto existing amps that are either non-loop or has-born loop amps. One-directional (keys off the FIRST existing amp).
- **Post-gen** (`:5443-5444`): after `LoopInducedMultiProcess` generation, `if amp['has_born']: raise Exception` — a bare sanity assertion that a `[noborn]` process really produced no Born (has_born re-derived from emptiness at loop_diagram_generation.py:658-660).

So MG5 does detect a loop-induced/non-loop-induced mix and raise, but the owner is the process-syntax/`do_add` interface layer (madgraph_interface.create_loop_induced), not the loop amplitude/multiprocess classes. `LoopMultiProcess`/`LoopInducedMultiProcess` (loop_diagram_generation.py:1774/:1787) themselves carry NO mixing check.

## Squared-order constraints on loop-induced (has_born=False)
`check_squared_orders` (loop_diagram_generation.py:1636) handles squared orders for BOTH cases. For loop-induced it filters Loop*Loop, "completely analogous to the tree level case" (`:1695-1698`). Constraint TYPE (`==`/`<=`/`>`) is read from `self['process'].get('sqorders_types')` (`:1650`) — populated upstream by the coupling-order/process-syntax parser from `^2==N` etc. Positive vs negative constraints split at `:816-819`; positive iterated to fixpoint (`:820-824`), the single negative one resolved once (`:826-835`, `apply_negative_sq_order`). Actual filtering delegates to `base_objects.DiagramList.apply_positive_sq_orders`/`apply_negative_sq_order` (shared with tree). NOTE: `==`/`>` rejection at NLO `[QCD]` is amcatnlo_interface.py:542 (nlo-syntax's slice), a PARSE-layer gate upstream of this loop machinery — not enforced here.

## Trap

`madevent_interface.py:7532` `is_loop_induced = os.path.exists(...'born_matrix.f')` is BACKWARDS-named (True when born_matrix.f EXISTS, i.e. the has-born case) AND dead — assigned, never read. Do NOT read effective loop-induced sense off `:7532`; the live branch is the `:7489 not os.path.isfile(...)` one. Verified by grep: `:7532` is the only occurrence of the variable.

## Boundary

This page owns the flag's meaning and its generation/order/color/init consequences. The export-layer machinery that consumes it (`export_v4.py` `PV`-dir layout, born/real/virtual subdir structure) is nlo-export's slice — cited above only as the boundary where `compute_loop_nc=True` is injected.
