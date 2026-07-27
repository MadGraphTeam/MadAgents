---
description: Amplitude.generate_diagrams recursive leg-reduction algorithm, post-filters (required/forbidden s-channels), and the decay-proc special case
---

# generate_diagrams algorithm (diagram_generation.py)

Cites: `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py` (v3.7.1).

## Entry: Amplitude.generate_diagrams (:520)
Docstring algorithm (:521-565), 8 steps. Signature `generate_diagrams(self, returndiag=False, diagram_filter=False)`. `returndiag=True` is used by `LoopAmplitude` — returns `(success, DiagramList)` instead of assigning `self['diagrams']`.

### Pre-checks (raise InvalidCmd, no diagrams) — three conservation gates (:587-633)
All three run on the ORIGINAL (un-flipped) `legs` BEFORE numbering/anti-PDG flipping, and BEFORE the "Trying <process>" log. On `returndiag=True` (loop path) they `return False, res` / `raise` instead of assigning + raising, so a loop amp fails the same checks (:590-594, :601-605, :627-633). The two `model.get(...)` asserts immediately above (:580-583, particles/interactions non-empty) precede them.

1. **Fermion parity** (:588-594): count legs whose particle `is_fermion()`; odd count → `InvalidCmd('The number of fermion is odd')` (:592). Pure parity on the leg multiset — no in/out distinction.
2. **In/out fermion balance, non-Majorana only** (:598-605): gated on `not model.get('got_majoranas')` — SKIPPED entirely for any model with a Majorana particle (e.g. SUSY neutralinos), because Majoranas break the incoming==outgoing fermion-count identity. `is_incoming_fermion` = fermion AND (initial-particle OR final-antiparticle); `is_outgoing_fermion` = fermion AND (initial-antiparticle OR final-particle) (`base_objects.py:2167-2188`). Mismatch → `InvalidCmd('The number of of incoming/outcoming fermions are different')` (:603) [sic, double "of" typo in source]. `got_majoranas` is lazy-computed via `check_majoranas()` on first `get` (`base_objects.py:1219-1221`).
3. **Conserved-charge gate** (:609-632): for each `charge` in `model.get('conserved_charge')`, sum the particle's `charge` attribute over all legs with a sign flip, reject if `abs(total) > 1e-10` → `InvalidCmd('No %s conservation for this process ' % charge)` (:629/:632). The sign predicate is `if (leg.get('id') != part['pdg_code']) != leg['state']: total -= value else: total += value` (:621-624) — i.e. subtract for (antiparticle XOR incoming), add otherwise, so an incoming particle and an outgoing antiparticle contribute with the SAME sign (net charge flow across the process boundary). Charge value lookup is defensive: tries `part.get(charge)`, then `getattr(part, charge)`, else `0` (:613-619).
   - **Where `conserved_charge` comes from (model-loading slice feeds this gate):** default is an empty `set()` (`base_objects.py:1092`), and diagram_generation.py:609 is the ONLY reader in `madgraph/core`. The ONLY setter is `models/import_ufo.py:636` `self.model.set('conserved_charge', self.conservecharge)`. `conservecharge` starts `{'charge'}` (import_ufo.py:513) plus every non-reserved numeric particle attribute (import_ufo.py:1316-1318), then DISCARDS any charge that some interaction violates (import_ufo.py:1865-1874, "The model has interaction violating the charge: %s"). So at generation time the set holds exactly the charges EVERY interaction conserves, and this gate enforces the whole process conserves them too. **Probe-confirmed (v3.7.1, `import model sm`):** the SM set is `['LeptonNumber', 'Y', 'charge']` — electric charge, hypercharge `Y`, AND LeptonNumber all survive the interaction-violation discard (the SM UFO declares all three as numeric particle properties). `got_majoranas` is `False` for SM, so gate #2 also fires. NOT a no-op for ordinary models (unlike the expansion-order ceiling) — every standard process is checked against all three.
   - **CAUTION — the InvalidCmd message is usually SWALLOWED, not shown.** For a normal `generate <proc>` (single process through `generate_multi_amplitudes`), a charge-violating process raises `InvalidCmd('No charge conservation...')` INSIDE this gate, but the multiprocess layer catches it into `failed_procs` and the user instead sees `NoDiagramException("No amplitudes generated from process ... Please enter a valid process")`. Probe-confirmed (v3.7.1): `generate e- e- > e- ve` (electric-charge-violating) raises NoDiagramException, NOT the charge message — the specific reason is lost. (This is the multi-error-swallow behavior in `multiprocess-crossing-mirror.md`: the single-error re-raise at :1908 only fires when exactly one crossing failed.) The `InvalidCmd('No ... conservation')` text is mostly an internal signal; expect users to report the generic "No amplitudes generated" instead.

### Setup
- `overall_orders` is min'd into `orders` (:571-577).
- Logs `"Trying <process>"` (:636) unless returndiag.
- Legs numbered 1..n if number==0 (:639-644). Incoming legs flipped to anti-PDG so all outgoing (:658-660).
- `max_multi_to1 = max len of ref_dict_to1 keys` (:664).

### Recursion: reduce_leglist (:959)
Recursive N→N-1 leg reduction. At each level:
- `can_combine_to_0(ref_dict_to0, is_decay_proc)` → emit final n→0 vertex if coupling orders allow (:983-997).
- stop at 2 legs (:1000).
- `combine_legs` (:1090) builds all valid groupings via `ref_dict_to1`; `merge_comb_legs` (:1165) replaces each group with new particle(s), number = min(group numbers).
- `forbidden_particles`: skip any combination producing a forbidden internal line (:1017-1021).
- coupling orders pruned via `reduce_orders` (skip if any order<0) (:1024-1030).

### Decay-process special case (ninitial==1) (:674-695)
`is_decay_proc = process.get_ninitial() == 1`. Builds a custom `ref_dict_to0` that only lets the initial leg combine as the n→0 identity, and sets `leglist[0].from_group=None` so it combines LAST. This yields A=A as the artificial final vertex — required for using the result as a decay-chain leg. Docstring "SPECIAL CASE" (:556-559).

## Post-generation filters (operate on `res`)
- **required_s_channels** (:715-736): keep diagrams where all required s-channel ids of any one id-list are present (lists are OR, elements AND). Excludes last vertex (n→0); for decay procs excludes last TWO (:723, artificial 1=1 vertex).
- **forbidden_s_channels** (:742-776): drop diagrams containing a forbidden s-channel propagator. ninitial==2 simple path (:744); ninitial!=2 has a directional walk to avoid forbidding the initial particle (:750-776).
- **forbidden_onsh_s_channels** (:781-794): mark matching s-channel legs `onshell=False` to forbid on-shell generation (does not drop the diagram).
- `diagram.calculate_orders(model)` for each (:797).
- **squared-order constraints** via `apply_squared_order_constraints` (:856) — only if `not returndiag and len(res)>0` (:807). Skipped for NLO returndiag path because interferences span beyond these diagrams. Mechanism (:856-902): (1) `constrained_orders` (the `==`/`>` forms) filtered first via `filter_constrained_orders` (:864-865); (2) positive squared-order constraints applied in a `while` loop via `apply_positive_sq_orders` until the diagram count stops shrinking (:870-881) — iterated because filtering one order can re-open filtering on another (relevant for `==`); a count INCREASE raises `MadGraph5Error('Inconsistency in ...')` (:877-879); (3) at most ONE negative squared-order constraint via `apply_negative_sq_order` (:885-892), and it MUTATES `self['process']['squared_orders'][neg_order]` to the computed positive target (:897) so downstream/output never sees a negative value; >1 negative → `InvalidCmd('At most one negative squared order constraint can be specified')` (:898-900).
- **diagram_filter** — call gate `if diagram_filter: res = self.apply_user_filter(res)` at **:810-811** (AFTER squared-order, BEFORE the id=0 glue); def `apply_user_filter` at :904. Full detail + the `remove_diag`/state/t-channel semantics in the dedicated page `apply-user-filter-diagram-filter.md`. Warns "Diagram filter is ON and removed %s diagrams for this subprocess." (:933) only when something was removed.

## Final id=0 vertex glue (:813-835)
If NOT `is_decay_chain`: the trailing id==0 vertex is glued into the next-to-last vertex (replaces an incoming leg with the outgoing one). Decay-chain processes deliberately keep the artificial final vertex.

## Tail
- `trim_diagrams(diaglist=res)` (:841) dedups legs/vertices in memory (no decay flagging here — decay_ids empty).
- process legs sorted by the lowest perturbation coupling (default 'QCD') (:844-847).
- returns `not failed_crossing` (True if generation succeeded before s-channel filtering) (:852).

## Cautions
- `failed_crossing` is computed from `res` BEFORE the required/forbidden s-channel filters (:708). A process can return `True` (crossing succeeded) yet end with zero diagrams after s-channel filtering — callers in `generate_multi_amplitudes` distinguish via `amplitude.get('diagrams')` truthiness (:1897).
- squared-order filtering is SKIPPED on the returndiag (loop) path (:807) — do not assume the constraint was applied for NLO.
- The "fermion number" / charge pre-checks raise before logging diagram counts; a bad process fails fast here, not in the recursion.
- `apply_squared_order_constraints` has a SIDE EFFECT: a negative squared-order constraint is replaced in-place by its resolved positive target on `process['squared_orders']` (:897). After diagram generation the process no longer carries the user's negative value — downstream code and output read the resolved positive number. Don't read `process['squared_orders']` post-generation and assume it equals the user's input when a negative constraint was given.
