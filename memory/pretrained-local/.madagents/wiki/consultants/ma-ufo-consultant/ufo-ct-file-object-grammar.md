---
description: Object-level grammar of the AUTHORED CT/NLO files (CT_parameters.py CTParameter pole-dicts, CT_couplings.py CT Coupling two encodings, CT_vertices.py CTVertex 3-tuple coupling key + loop_particles groups + R2/UV/UVmass type, particle-attached counterterm/loop_particles) — the loop-UFO analogue of ufo-declaration-object-grammar.md. Anchored loop_sm.
---

# UFO CT/NLO file object grammar — what a loop-capable model author writes (v3.7.1)

The loop-UFO analogue of `ufo-declaration-object-grammar.md` (which is the TREE-file authored grammar). This page is the *static authored structure* of the NLO-only files: the attribute semantics and DSL syntax in `CT_parameters.py` / `CT_couplings.py` / `CT_vertices.py` and the particle-attached counterterm declarations — independent of how the loader transforms them (that is `ufo-ct-vertex-loading.md` + the loader-consumption section below, pointers only here). Anchor model: `$MADGRAPH_INSTALL/models/loop_sm/` (the canonical loop model, reliably shipped; it ships `CT_parameters.py`, which `SMEFTatNLO` does NOT). The SMEFTatNLO structural contrasts below are verifiable against `models/SMEFTatNLO/` when present, else the durable test fixture `tests/input_files/SMEFTatNLO_running/` (SMEFTatNLO is an oscillating EFT model — not always under `models/`). Base classes in each model's own `object_library.py` (loop_sm's at `object_library.py`).

## What a loop UFO carries BEYOND a tree UFO
A tree UFO = the required 6 files + optional orders/propagators/decays. A loop-capable UFO additionally ships, and the loader additionally consumes (only when `perturbation_couplings` is non-empty — see orders page):
- `CT_parameters.py` — `CTParameter` objects (Laurent-expanded renormalization constants). loop_sm ships them (count `CTParameter(` entries in the file); **SMEFTatNLO has NONE** (its CT poles live directly in dict-valued CT couplings instead) — the structural fact, not a count.
- `CT_couplings.py` — ordinary `Coupling` objects (R2/UV coupling values), but with two/three Laurent encodings (below). Count entries per file; some are dict-valued (`grep -c "value = {" <model>/CT_couplings.py`). SMEFTatNLO carries far more than loop_sm and is predominantly dict-valued.
- `CT_vertices.py` — `CTVertex` objects (the R2/UV/UVmass vertices). Count by `type=` tally per file (R2 / UV / UVmass), but note the naive `grep -oE "type = '...'"` over loop_sm double-counts a commented-out R2 block — count uncommented-only. SMEFTatNLO's UV vertices are auto-classified (see ct-vertex-loading page).
- `coupling_orders.py` with `perturbative_expansion>0` on some order AND an `object_library.py` `CouplingOrder.__init__` that STORES it (loop_sm `object_library.py:311` has `self.perturbative_expansion = perturbative_expansion`; sm does NOT — the tree/loop asymmetry, orders page). loop_sm: `QCD(hierarchy=1, expansion_order=-1, perturbative_expansion=1)`, `QED(...,perturbative_expansion=0)`.
- particle-attached `counterterm` / `loop_particles` declarations in `particles.py` (wavefunction renormalization — below). loop_sm is the ONLY bundled model that does this (`grep -l "counterterm\s*=" models/*/particles.py` = loop_sm only).

`SMEFTatNLO` is loop-capable WITHOUT `CT_parameters.py` and WITHOUT particle counterterms — so "loop UFO" does NOT imply all five extras. The minimal loop fingerprint is: `perturbative_expansion>0` stored + `CT_vertices.py` content. Everything else is optional within the NLO file set.

## 1. CTParameter (object_library.py:169-196) — a Laurent-expanded renormalization constant

`CTParameter(name, type, value, texname)` — NOTE the signature DIFFERS from `Parameter`:
- NO `nature` argument — the `__init__` FORCES `self.nature='internal'` (l.181). A CTParameter is never external (never read from a card).
- NO `lhablock`/`lhacode` — it has no LHA identity.
- `value` is a **Laurent-pole DICT** `{poleOrder: expr-string}`, keys ∈ {0 (finite), -1 (single pole), -2 (double pole)} — e.g. `RGR2 = CTParameter(value={0:'-(3.0/2.0)*G**4/(96.0*cmath.pi**2)'})` (R2, finite-only, `CT_parameters.py:17-20`); `G_UVg = CTParameter(value={-1:'-((G**2)/(2.0*48.0*cmath.pi**2))*11.0*CA'})` (UV, single-pole-only, `:39-42`); `G_UVc = CTParameter(value={-1:'...*4.0*TF', 0:'cond(MC,0.0,...*reglog(MC**2/MU_R**2))'})` (BOTH finite and single pole, `:49-54`). [`require_args` at l.171 LISTS `nature`, but the `__init__` signature `(name,type,value,texname)` at l.173 omits it — `nature` is forced `'internal'` at l.181, not passable.]
- Methods: `finite()` returns `self.value[0]` (→`'ZERO'` on KeyError, l.186-190); `pole(x)` returns `self.value[-x]` (→`'ZERO'` on KeyError, l.192-196). So `pole(1)=value[-1]` (single pole), `pole(2)=value[-2]` (double pole). The `-x` is the indexing convention, NOT the param-path's `pole_dict[-pole]` sign-flip (which is the loader's naming, expression page).

loop_sm `CT_parameters.py` tally (count `CTParameter(` entries; count those with a `-1` key vs a `-2` key): most carry a `-1` (single-pole) key and ZERO carry a `-2` (double pole) — the author guarantees single-pole-max at the CTParameter level too (consistent with the loader's `InvalidModel`-on-double-pole contract). The MECHANISM (no double poles), not the counts, is the durable fact. Values use loop-only functions `cond(M,a,b)` (mass-conditional: 0 if M==0 else b) and `reglog(x)` (regularized log), which the loop model's `function_library.py` extends `cmath` with.

## 2. CT Coupling (CT_couplings.py) — ordinary Coupling, TWO Laurent encodings

CT couplings are plain `Coupling(name, value, order)` (same class as tree couplings, object_library.py:234-263) — NO new class. But `value` is encoded one of two ways, and `Coupling.pole(x)` (l.250-263) handles both:
- **plain STRING** (R2, finite): `pole(0)` returns the string, `pole(x≠0)` returns `'ZERO'`. e.g. `R2_3Gq = Coupling(value='2.0*G**3/(48.0*cmath.pi**2)', order={'QCD':3})` (`CT_couplings.py:17-19`). The R2 finite piece.
- **STRING that REFERENCES a CTParameter**: still a string at author time, but the embedded CTParameter name carries the Laurent series — e.g. `GC_4GR2_Gluon_delta5 = Coupling(value='-4.0*complex(0,1)*RGR2*(2.0*lhv+5.0)', order={'QCD':4})` references `RGR2` (a CTParameter). The loader's `treat_couplings` (import_ufo.py:595-599) substitutes the CTParameter's poles to turn this into a dict (loader section below).
- **DICT value** `{-1:'...', 0:'...'}` directly: `pole(x)` returns `value[-x]` if present else `'ZERO'` (l.254-258). The Laurent series is inlined, no CTParameter reference. SMEFTatNLO uses THIS form predominantly because it ships no CT_parameters.py (most of its CT couplings are dict-valued) — but it is NOT SMEFTatNLO-only: **loop_sm ALSO has dict-valued CT couplings** (`grep -c "value = {" loop_sm/CT_couplings.py`), so a single loop UFO mixes all three encodings.

`Coupling.value()` (the METHOD, l.247-248) returns `self.pole(0)`. But note `self.value` (the ATTRIBUTE) is what's read in the dict/string branches — the method and attribute share the name; `pole(0)` reads the attribute. The `order` dict carries the QCD/QED/NP powers of the COUNTERTERM (e.g. R2_3Gq `{'QCD':3}` — the R2 of the ggg vertex is QCD^3), same as a tree coupling's order.

The `Coupling.__init__` ALSO accepts `loop_particles=None, counterterm=None` kwargs (object_library.py:240) and `require_args_all` includes them (l.238) — but no bundled CT_couplings.py uses them (`grep -c "counterterm\s*=\|loop_particles\s*=" loop_sm/CT_couplings.py` = 0). They're a forward-compat hook on the Coupling class.

## 3. CTVertex (object_library.py:217-230) — the R2/UV vertex with a 3-tuple coupling key

`CTVertex(name, particles, color, lorentz, couplings, type, loop_particles)` — `type` and `loop_particles` are POSITIONAL `require_args` (l.219), not optional kwargs (unlike the tree `Vertex` which has only the 5). Self-appends to `all_CTvertices` (l.230).

Canonical block (loop_sm `CT_vertices.py:21-28`, the ggg R2 vertex):
```
V_R23G = CTVertex(name='V_R23G',
   particles=[ P.G, P.G, P.G ],
   color=[ 'f(1,2,3)' ],                                    # color list (same DSL as tree)
   lorentz=[ L.VVV1 ],                                      # lorentz list (same DSL as tree)
   loop_particles=[ [[P.u],[P.d],[P.c],[P.s],[P.b],[P.t]],  # group 0: the quark loop (6 species)
                    [[P.G]] ],                              # group 1: the gluon loop
   couplings={ (0,0,0):C.R2_3Gq, (0,0,1):C.R2_3Gg },        # 3-TUPLE key
   type='R2' )
```

**The `couplings` key is a 3-tuple `(color_index, lorentz_index, loop_particle_group_index)`** — one MORE axis than the tree `Vertex`'s `(color_index, lorentz_index)` 2-tuple. The third index selects which `loop_particles` group the coupling belongs to. **PROOF the order is color-first (settled by the loader, not the authored symmetric `(0,0,k)` keys which can't discriminate):** at `import_ufo.py:1635` the loader does `new_couplings[key[2]][poleOrder][(key[0],key[1])] = newCoupling` — `key[2]` indexes the loop-particles slot (`new_couplings` sized `range(0,max(1,len(loop_particles)))`, l.1605-1606), and the reduced `(key[0],key[1])` is handed to the base `add_interaction`, which reads `interaction_info.lorentz[key[1]]` (l.1821 — so **key[1]=lorentz**) and `interaction_info.color` indexed by key[0] (l.1812). So **key[0]=color, key[1]=lorentz, key[2]=loop_group#** — identical color-first convention to the tree `Vertex` 2-tuple, plus the loop axis. So `(0,0,0)` = color0/lorentz0/quark-loop → `R2_3Gq` (quark-loop coupling), `(0,0,1)` = color0/lorentz0/gluon-loop → `R2_3Gg` (gluon-loop coupling): same color & lorentz structure, DIFFERENT loop content, DIFFERENT coupling. This is the structural reason R2/UV vertices fan out per loop-particle content.

**`loop_particles`** is a list of "loop groups"; each group is a list of "loop-particle sets" (lists of `Particle` refs), so the type is list-of-list-of-list. The third coupling-key index `key[2]` indexes the OUTER list (the groups). A group with multiple sets (e.g. the quark group `[[P.u],[P.d],...]`, 6 singleton sets) means "sum over these loop contents at the same coupling key" — they share one coupling. A 2-particle set `[[P.G,P.c]]` (loop_sm `V_UVcMass:646`) means a loop containing BOTH the gluon and the c-quark. (Some authored decls use pdg INTEGERS instead of Particle refs — loop_sm `particles.py:319 b.loop_particles=[[[5,21]]]` uses 5,21; the loader handles both — comment import_ufo.py:1357-1362.)

**`type`** ∈ the author's vocabulary: `'R2'`, `'UV'`, `'UVmass'` (loop_sm uses these three). The loader ALSO accepts `'UVloop'`/`'UVtree'` and auto-classifies a bare `'UV'` by particle content (ct-vertex-loading page #2). loop_sm authors plain `'UV'` and `'UVmass'` explicitly; the bare `'UV'`→`UVloop`/`UVmass` split happens at load.

UV example (loop_sm `:567-574`, `V_UV1eps3G`): `loop_particles=[[[P.u],[P.d],[P.s]],[[P.c]],[[P.b]],[[P.t]],[[P.G]]]` (5 groups: light-quark / c / b / t / gluon), `couplings={(0,0,0):C.UV_3Gq,(0,0,1):C.UV_3Gc,(0,0,2):C.UV_3Gb,(0,0,3):C.UV_3Gt,(0,0,4):C.UV_3Gg}` — five `(0,0,k)` keys, one per loop group. UVmass example (`:643-649`, `V_UVcMass`): `particles=[P.c__tilde__, P.c]` (2 same-flavor → mass renorm), `color=['Identity(1,2)']`, `lorentz=[L.R2_QQ_2]`, `loop_particles=[[[P.G,P.c]]]`, `couplings={(0,0,0):C.UV_cMass}`, `type='UVmass'`.

A commented-out 4-gluon R2 block (`:40-58`) shows the full density: a 6-color × 3-lorentz × 2-loop-group grid with ~36 keys — illustrating how large the 3-tuple key set gets for high-point R2 vertices.

## 4. Particle-attached counterterm / loop_particles (particles.py) — wavefunction renormalization

The `Particle.__init__` carries `loop_particles=None, counterterm=None` kwargs (object_library.py:77), and `.anti()` deliberately does NOT copy them (comment l.128: "We do not copy the UV wavefunction renormalization as it is defined for the particle only") — so a wavefunction CT is particle-specific, never inherited by the antiparticle.

loop_sm attaches them POST-construction (NOT as constructor kwargs), in a "Wavefunction renormalization" block (`particles.py:317-329`):
```
b.loop_particles = [[[5,21]]]                                 # b-quark + gluon loop (pdg 5,21)
b.counterterm  = {(1,0,0):CTParam.bWcft_UV.value}             # 3-tuple key → CTParameter's .value (Laurent dict)
...
G.loop_particles = [[[4]],[[5]],[[6]]]                        # gluon: 3 loop groups (c/b/t)
G.counterterm  = {(1,0,0):CTParam.GWcft_UV_c.value,(1,0,1):CTParam.GWcft_UV_b.value,(1,0,2):CTParam.GWcft_UV_t.value}
```
- `counterterm` is a DICT keyed by a 3-tuple `(?, ?, loop_group#)` → a CTParameter's `.value` (the raw Laurent DICT, accessed as the `.value` ATTRIBUTE — `bWcft_UV.value` is `{-1:'cond(MB,...)',0:'cond(MB,...)'}`, `CT_parameters.py:95-99`). The gluon's three keys `(1,0,0)/(1,0,1)/(1,0,2)` differ only in the loop-group index, one per c/b/t loop.
- `loop_particles` here uses pdg INTEGERS (`[[[5,21]]]`), parallel to the CTVertex `loop_particles` but particle-attached.
- The first key index `(1,...)` is the coupling-ORDER count (here QCD=1 — a one-loop QCD wavefunction CT); the loader one-loop-checks it (loader section).

The wavefunction-renormalization CTParameters themselves are ordinary CTParameters with both `-1` and `0` poles: `GWcft_UV_c/_b/_t` at `CT_parameters.py:67/74/81`, `cWcft_UV/bWcft_UV/tWcft_UV` at `:88/95/102` (the `b` block is `:95-99`). So a particle CT references a CTParameter exactly like a CT coupling can.

## Loader consumption (pointers — full detail on ct-vertex-loading page + this section)
The AUTHORED grammar above is transformed by the loader ONLY for `perturbation_couplings` models:
- **CTVertex** → `add_CTinteraction` (import_ufo.py:1556+): 3-axis split (order × loop_particles × pole) → base interactions with R2/UV/UVmass/`*1eps` type labels. `ufo-ct-vertex-loading.md`.
- **CTParameter referenced in a CT coupling string** → `treat_couplings` (import_ufo.py:595-599): substitutes the CTParameter's poles, turning `value='2*RGR2'` into a dict `{-1:'2*RGR2_1EPS_', 0:'2*RGR2_FIN_'}` (comment l.587-594). The `_FIN_`/`_1EPS_` UPPERCASE suffixes come from `pole_dict={-2:'2EPS',-1:'1EPS',0:'FIN'}` (l.60) — distinct from the coupling-path lowercase `_1eps` (expression page). A name-conflict check at l.549-556 raises `InvalidModel` if a suffixed CTparam name collides with an existing param.
- **particle.counterterm** → consumed in `add_particle` (import_ufo.py:1342-1379), GATED on `self.perturbation_couplings and counterterms!={}` (l.1342, else the particle is appended unchanged). It (a) one-loop-checks each key — exactly one order index ==1 and none >1 (l.1354-1355); (b) SYNTHESIZES a new `Coupling` named `UVWfct_<particlename>_<loop#>` with `value=counterterm` (the Laurent dict) and `order={ordername:2}`, popped onto `self.wavefunction_CT_couplings` (l.1373-1377); (c) rewrites the particle's `counterterm` attr to `('ORDERNAME',((pdg_tuple),)):{laurent_order:CTCouplingName}` form (l.1368-1370, l.1379). So a particle-attached wavefunction CT becomes a synthesized `UVWfct_*` coupling + a reshaped attribute — created at load, present in NO `.py` file.

## Cautions (source-visible, declaration-level)
- **"loop UFO" ≠ "has CT_parameters.py".** SMEFTatNLO is loop-capable with NO `CT_parameters.py` (poles inlined as dict-valued CT couplings) and NO particle counterterms. loop_sm has both. Don't assume a CT_parameters.py exists for every NLO model; the `__init__.py` import of it is try/except-guarded and silently passes if absent.
- **The CTVertex `couplings` key is a 3-TUPLE** `(color, lorentz, loop_group#)`, not the tree 2-tuple. Reading it as `(color, lorentz)` drops the loop-content axis and mis-pairs couplings.
- **CTParameter `value` is always a DICT** (Laurent), never a bare string — opposite of a CT Coupling whose `value` may be a string. And CTParameter is forced `internal`, never external: it has no LHA identity and is never a param_card entry.
- **A particle's `counterterm`/`loop_particles` are NOT copied to its antiparticle** (`.anti()` comment, object_library.py:128). A wavefunction CT is declared on the particle only.
- **No `-2` (double-pole) keys** in any loop_sm CTParameter or CT coupling value, consistent with the loader's hard `InvalidModel`-on-double-pole contract. A genuine double pole in an authored CT value HARD-FAILS at load (ct-vertex-loading page), it does not warn.
- The R2/UV PHYSICS (which renormalization scheme, what the R2 rational terms mean) and HOW MadLoop consumes the resulting interactions are **nlo-model / madloop slice** — this page stops at the authored object grammar + loader transform locus.
