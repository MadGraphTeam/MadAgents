---
description: Fermion-flow-clash handling for Majorana particles — check_and_fix_fermion_flow / check_majorana_and_flip_flow recursion, the flip-flow vs flip-sign rule, and calculate_fermionfactor / sign_flips_to_order.
---

# Fermion-flow clash (Majorana) and fermion factor

Cites `$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (v3.7.1).

## When a clash occurs
A fermion-flow clash = N(incoming) != N(outgoing) among the fermion mothers of a wf/amplitude. Arises when a Majorana particle flips fermion flow (docstring @1163-1190). `fermionflow` property is +/-1 (bosons always +1); -1 only set on a clash @612-614.

## set_state_and_particle @1123
Before clash check: sets `leg_state=False` (t-channel) iff exactly one initial-state mother. Boson → state 'intermediate'. Fermion → copies fermion mother's state; self_antipart copies with_flow state/is_part; non-self-antipart copies state+fermionflow and flips state+fermionflow if is_part/incoming mismatch @1156-1160.

## check_and_fix_fermion_flow @1163 (HelasWavefunction)
Sorts mothers by pdg (`sort_by_pdg_codes` with anti-pdg) then delegates to `HelasWavefunctionList.check_and_fix_fermion_flow` @2301, which calls the recursion. Also invoked on the amplitude's mothers in generate_helas_diagrams @3785.

## check_majorana_and_flip_flow @1207 (recursive)
Walks down the fermion line to the outermost Majorana, then back up:
- `found_majorana` becomes True at the first self_antipart wf @1231-1232.
- At an external leg (no mothers) @1240: `flip_flow = found_majorana` (non-self-antipart) or `flip_sign = found_majorana` (self-antipart); `force_flip_flow` overrides.
- Up the tree: compare `new_mother.get_with_flow('state')` vs self's. **flip_sign** iff state differs AND self is self_antipart (Majorana) — flips `state` and `is_part` @1358-1362 (keeps id*flow). **flip_flow** iff state differs AND NOT self_antipart — flips `fermionflow` sign @1354-1356.
- Rule (docstring @1213-1219): flip fermionflow only AFTER the last Majorana; before it, flip particle identity + state instead. This keeps the Helas calls marking *where* the clash physically happens (the outermost Majorana).
- When a flip is needed and the wf already exists in `wavefunctions`, a `copy.copy` is made with a new number and inserted respecting mother-before-daughter ordering @1280-1348; an existing matching copy is reused and wf_number decremented @1363-1378.

## Fermion factor — calculate_fermionfactor @2907 (HelasAmplitude)
- Picks fermion vs boson mothers; `fermion_numbers = [f.get_fermion_order()]` (recursive line tracing @1419).
- Tree level (@2991-2996): pairs fermion lines as [NI,NO,...].
- `fermion_factor = sign_flips_to_order(fermion_number_list)` @3022 — bubble-sort parity, (-1)^nflips @3027-3043.
- Loop level adds `ghost_factor` (anticommuting ghost loop = -1) and `fermion_loop_factor` (closed fermion loop = -1) @2926-2990 — loop is madloop slice's domain but the factor lives here.
- Result: `self['fermionfactor'] = fermion_factor * ghost_factor * fermion_loop_factor` @3024.

## Octet/scalar Majorana coupling sign
`set_octet_majorana_coupling_sign` @1106, `set_scalar_coupling_sign` @1089 adjust coupling sign for special Majorana cases.

## Conjugate index — the `C<i>` ALOHA tag (distinct from the flip-flow recursion above)
A SEPARATE Majorana mechanism: which fermion line of a vertex needs the charge-conjugated (hermitian) ALOHA routine. This is the `conjugate_indices` property, the source of the `C1`/`C2` tags in ALOHA routine names.
- `conjugate_indices` is a stored prop, default **`None`** (wf @646, amp @2614). The enhanced `get()` accessor **lazily computes and caches** it on first access: `if name=='conjugate_indices' and self[name]==None: self['conjugate_indices']=self.get_conjugate_index()` (wf @851-853, amp @2787-2789).
- `get_conjugate_index()` (wf @2144 / amp @3152) returns `tuple(sorted(indices))` of fermion-LINE indices (1-based, one per fermion pair) needing conjugation. **The early-return guards DIFFER between the two variants** (verified v3.7.1): the amp (@3155-3157) early-returns `()` simply when no mother has `fermionflow<0` or `is_majorana()`; the wf (@2147-2151) ANDs that with a second conjunct `(not interaction_id or self.fermionflow >= 0)` — so a wf with its OWN negative `fermionflow` and a non-zero `interaction_id` does NOT early-return even with no Majorana/neg-flow mother (the wf carries its own fermion line, the amp does not). Otherwise: sort mothers by interaction pdg order (`sort_by_pdg_codes`), take fermions, then `indices = fermions.majorana_conjugates()` PLUS any line whose pair has a member with `fermionflow<0` (@2172-2175 / @3168-3171). The wf variant also inserts a state-flipped copy of `self` into the fermion list at `self_index` first (@2160-2166) — the amp variant does not (amp has no own fermion line).
- `majorana_conjugates()` @2468 (HelasWavefunctionList): empty unless ≥2 Majoranas @2476. For each fermion PAIR `(self[i],self[i+1])`, appends a conjugate iff both are Majorana with DIFFERENT pdg AND I/O order is wrong (`self[i]` spin-state>0 i.e. incoming, `self[i+1]`<0 i.e. outgoing) @2483-2490. Comment @2472-2474: "crucial if the Lorentz structure depends on the direction of the Majorana particles, as in MSSM with goldstinos."
- **Two readers, two freshness levels (mutation-lifecycle trap):** `needs_hermitian_conjugate()` @1468/@2865 reads the STORED `self.get('conjugate_indices')` (triggers the lazy cache, then frozen); `get_aloha_info()` @1861/@3055 calls the LIVE `get_conjugate_index()` and builds `tags=['C%i'%w for w in ...]`. `get_call_key` @1742-1743 appends `conjugate_indices` to the call key ONLY when `needs_hermitian_conjugate()`. So if a wf is mutated (flow flip, decay insert) AFTER the stored value cached, the two can diverge — another instance of the helas-me-mutation-lifecycle principle, this time on a per-wf lazy cache.
- **Divergence probe-DEMONSTRATED** (MSSM_SLHA2, `u u > ul ul` gluino-prop wf): after poisoning the STORED slot to `()` (`wf['conjugate_indices']=()` raw-dict write), `needs_hermitian_conjugate()` returns `False` (reads stored) while `get_aloha_info()` STILL emits `(('FFS1',),('C1',),1)` (recomputes live) — and consequently `get_call_key` DROPS the conjugate entry while ALOHA generation (via `get_used_lorentz`→`get_aloha_info`) STILL generates the `C1` routine. The two code paths provably read different sources; this is not merely theoretical.

**Probe-verified** (MSSM_SLHA2, parse-time API): `u u > ul ul` (t-channel gluino exchange) gives the gluino-propagator wf `fermionflow=1` but `conjugate_indices=(1,)` and `get_aloha_info()=(('FFS1',),('C1',),1)` — i.e. the `C1` conjugate ALOHA tag fires on a POSITIVE-flow Majorana propagator (driven by the I/O ordering branch, not by negative flow), and one external wf carries `fermionflow=-1`. By contrast `u u~ > go go` (different topology) gives NO conjugate index and NO negative flow — the conjugate tag is topology-dependent, not merely "process contains a Majorana."

## Caution
- The clash logic mutates and inserts wavefunctions mid-generation and renumbers later wfs; downstream code that cached wf numbers before this runs is wrong. The recursion also touches `number_to_wavefunctions` dicts to keep replacements consistent @1382-1398.
