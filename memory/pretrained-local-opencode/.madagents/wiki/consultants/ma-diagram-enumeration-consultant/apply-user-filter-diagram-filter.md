---
description: --diagram_filter user-hook (apply_user_filter / remove_diag plugin) applied during LO enumeration; the legacy diag/vertex/leg fields it reads; Leg 'state' true=final/false=initial semantics and the authoritative t-channel test
---

# --diagram_filter user hook (apply_user_filter / remove_diag)

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py`, `.../core/base_objects.py`, `.../interface/madgraph_interface.py`, `.../loop/loop_diagram_generation.py` (v3.7.1). All facts below verified against source.

## Where the hook is applied
- Call gate inside `Amplitude.generate_diagrams`: `if diagram_filter: res = self.apply_user_filter(res)` at **diagram_generation.py:810-811** — runs AFTER `apply_squared_order_constraints` (:807-808), BEFORE the final id=0 vertex glue (:813-835). Order matters: filter sees post-squared-order diagrams, pre-glue.
- `apply_user_filter` def at **:904-935**. Body: `if True:` (:908) imports the user function via `misc.plugin_import('user_filter', <help-msg>, fcts=['remove_diag'])` (:909-911) — i.e. from `PLUGIN/user_filter.py`, function name `remove_diag`. The `else:` branch (:912-921) is a **dead** `if True:`-guarded example (T-channel-light-quark remover) — never reached.
- Loop over diagrams (:926-930): `model = self['process']['model']` (:925); `if remove_diag(diag, model): nb_removed += 1  else: res.append(diag)`. **`remove_diag` returning True DISCARDS the diagram; False KEEPS it** (kept only via the `else` append).
- **Plugin-import msg mismatch:** the help string advertises `remove_diag(ONEDIAG)` (one arg) but the actual call is two-arg `remove_diag(diag, model)` (:927) — a user filter may take `(diag, model=None)`.
- Warn `logger.warning('Diagram filter is ON and removed %s diagrams for this subprocess.' % nb_removed)` (:933) — fires ONLY when `nb_removed>0`.

## What turns it on — the `diagram_filter` flag (True/False)
`--diagram_filter` parsed in **`MadGraphCmd.do_add` (madgraph_interface.py:3247-3249)** → `MultiProcess(..., diagram_filter=True)` (:3371) → `generate_multi_amplitudes(..., diagram_filter=...)` (default False, :1669) → per-crossing `amplitude.generate_diagrams(diagram_filter=diagram_filter)` (:1892). Boolean only (`self['diagram_filter']` "only True/False so far", :1601).

## LO only — not for NLO (two independent guards)
1. `--diagram_filter` is parsed ONLY in the LO interface `MadGraphCmd.do_add`. The NLO interface `amcatnlo_interface.py` (`do_add` :452) has NO `diagram_filter` handling (grep of the whole file: empty). An NLO process (routed to aMC@NLO before `do_add`) never sets the flag → stays default False.
2. Structural backstop: `LoopAmplitude.generate_diagrams(loop_filter=None, diagram_filter=None)` (loop_diagram_generation.py:595) **overrides** the base method and NEVER calls `apply_user_filter` (only the born/loop generators + `loop_filter`). The `diagram_filter` kwarg is accepted purely for signature compatibility with the base-class call at :1892, and is ignored. So even if the flag reached a loop amp, no user filter would run.

## Applied to every subprocess incl. each decay
`DecayChainAmplitude.__init__` threads `diagram_filter` to:
- the CORE process amplitudes — `generate_multi_amplitudes(..., diagram_filter=diagram_filter)` (:1365) / `get_amplitude_from_proc(..., diagram_filter=diagram_filter)` (:1370).
- EACH decay chain — recursively `DecayChainAmplitude(process, ..., diagram_filter=diagram_filter)` (:1386-1389), one per entry in `argument.get('decay_chains')` (:1377).
So for `p p > z w- j j, z > l+ l-, w- > j j`, `remove_diag` is invoked independently on the production AND on each decay subprocess's diagram list (each subprocess runs its own `generate_diagrams`→`apply_user_filter`).

## Over-restrictive filter → NoDiagramException (with nuance)
If `apply_user_filter` empties `res`, `self['diagrams']=[]`. At the multiprocess layer (:1896-1904): `if amplitude.get('diagrams'):` is False → keep-branch skipped. Note `failed_crossing` was computed at :708 from `res` BEFORE the post-filters, so it is False (diagrams existed pre-filter) → `result=not failed_crossing=True` → `elif not result:` (:1902) is False → the emptied amp is NOT even appended to `failed_procs`; it is silently dropped. If ALL subprocesses end empty → `if not amplitudes:` (:1907) True → `NoDiagramException("No amplitudes generated from process %s. Please enter a valid process")` (:1911). `NoDiagramException(InvalidCmd)` (:40). The often-quoted "No amplitudes generated" is a truncation of that full message text.
- **Nuance:** a SINGLE member of a multiparticle expansion going all-empty is silently dropped (not in failed_procs, no warning beyond the :933 removal line); only the all-members-empty case raises. `len(failed_procs)` may be 0 in the all-filtered case, so the :1908 single-error re-raise won't fire → generic message.

## Legacy diag/vertex/leg fields the filter reads (one correction)
Against `base_objects.py` class defs (`Diagram` :2557, `Vertex` :2366, `Leg` :2091, defaults :2100-2114):
- `diag['vertices']` — list. ✓
- `vertex['id']` int; **id==0 = identity/fake final vertex** (source example :916 `if vertex['id']==0: #special final vertex: continue`). ✓. On "skip id in [0,-1]": id==0 confirmed; loop-related negative ids exist (id=-2 = shrunk loop, veto in multichannel :2770; id=-1 also loop bookkeeping) — the tree-level `remove_diag` example only skips id==0, so "[0,-1]" is a defensive superset, not fully needed at LO.
- `vertex['legs']` — list. ✓
- `leg['id']` PDG code. ✓ (default 0, :2103)
- `leg['number']` external leg number (min propagated inward). ✓ (:2104)
- `leg['state']` bool — **field semantics (often misread).** Source comment (:2105): `# state: True = final, False = initial`. The fundamental meaning is FINAL vs INITIAL, not "s-channel vs t-channel". The s/t reading is a *specialization for internal propagator legs* (see next section), not the field's definition. For an EXTERNAL leg, state just marks final-state vs initial-state particle.
- `diag.get('orders')` dict. ✓ (`get_order` reads `self['orders']`, :2678-2684)

## t-channel identification
- **Authoritative test = `not leg.get('state')` (state==False), and the propagator leg = `vertex['legs'][-1]`** — straight from MG's own `Diagram.get_nb_t_channel` (base_objects.py:2742-2751): `for v in self['vertices'][:-1]: l = v.get('legs')[-1];  if not l.get('state'): nb_t+=1`. So both facts (last leg = propagator; state==False ⇒ t-channel) are exactly what MG uses. Also the id=0 glue treats `legs[-1]` as the propagator (:826-832).
- **Why `number<3` is INACCURATE:** `renumber_legs` sets the combined internal leg's state via `state_dict[min_number] = len([l for l in leg_list[:-1] if not l.get('state')]) != 1` (:2722-2723) — i.e. state=False (t-channel) ONLY when EXACTLY ONE initial-state leg is among the combined legs; combining BOTH initial legs (count 2 ≠ 1) gives state=True (s-channel). But its `number = min(combined numbers) = min(1,2) = 1 < 3`. So a genuine s-channel propagator built from both initial legs has number<3 yet state=True → the `number<3` heuristic misclassifies it as t-channel. The dead example in `apply_user_filter` (:918, `if vertex['legs'][-1]['number'] < 3: #this means T-channel`) itself embodies this inaccurate heuristic — MG's shipped example is itself the antipattern to avoid; a correct user filter should test `leg.get('state') == False`.

## Cross-refs
- Enumeration entry / post-filter ordering: `generate-diagrams-algorithm.md`.
- Multiprocess keep/drop/NoDiagramException + silent zero-member drop: `multiprocess-crossing-mirror.md`.
- Decay-chain construction (perturbed/one-incoming prohibitions, onshell flagging): `decay-chain-amplitude.md`.
- `onshell` tri-state (distinct field from `state`): `leg-onshell-lifecycle.md`.
