---
description: Object-level grammar of the UFO declarations themselves (as authored, before the loader reads them) — Particle attribute semantics + .anti() mechanics, the Vertex color×lorentz→coupling sparse-dict, the Lorentz.structure DSL vocabulary/index convention, and the color-string DSL, with SM source examples.
---

# UFO declaration object grammar (v3.7.1) — what the model author writes

Complements `ufo-model-file-structure.md` (the class roster + require_args) and the loader-consumption pages (`ufo-vertex-to-interaction-conversion.md`, `ufo-loader-per-declaration-consumption.md`). This is the TREE-file authored grammar; its loop/NLO analogue (CTParameter / CT Coupling / CTVertex / particle-attached counterterm) is `ufo-ct-file-object-grammar.md`. THIS page is the *static authored structure*: the attribute semantics and DSL syntax in the `.py` files, independent of how the loader transforms them. Refs are `$MADGRAPH_INSTALL/models/sm/` unless noted. The base classes live in each model's own `object_library.py` (sm's at `object_library.py`).

## Particle — full attribute semantics (object_library.py:66-140)

Two attribute lists matter:
- `require_args` (l.69) = the 10 POSITIONAL fields: `pdg_code, name, antiname, spin, color, mass, width, texname, antitexname, charge`.
- `require_args_all` (l.71) = those 10 PLUS `line, propagating, goldstoneboson` — the three the `__init__` sets itself (l.73-91), not from `*args`.

`__init__` semantics:
- `charge` is cast `float(charge)` (l.77) — declared as a Python fraction `2/3` (file has `from __future__ import division`, l.6 of particles.py) and stored as a float.
- `self.selfconjugate = (name == antiname)` (l.87) — self-conjugacy is DERIVED from name==antiname, never declared. `a`,`Z`,`g`,`H`,`G0` are self-conjugate; `W+`(antiname `W-`), quarks, leptons are not.
- `self.line = self.find_line_type()` ALWAYS (l.88 `if 1:` — the `line=None` arg is dead, the passed `line` is ignored). The Feynman-diagram line style is computed from spin+color, never taken from the file.
- Every kwarg beyond the signature (e.g. `GhostNumber`, `LeptonNumber`, `Y` in sm) is set as an attribute via `UFOBaseClass.__init__`'s `**options` loop (l.25-26). These are arbitrary per-model quantum numbers — the loader reads only a subset (see "conserved charges" below); the rest ride along as inert attributes.

**spin = 2S+1 convention** (l.101-125, `find_line_type`): `1`=scalar (dashed), `2`=fermion (straight if not self-conj, else swavy/scurly), `3`=vector (wavy if colorless, curly if colored), `5`=spin-2 (double), `-1`=GHOST (dotted). So a ghost is identified by `spin == -1`, NOT by a flag.

**color = SU(3) rep with sign** (used in `find_line_type` + `.anti()`): `1`=singlet, `3`=triplet, `-3`=antitriplet, `8`=octet (sextets ±6 in other models). The SIGN distinguishes 3 from 3bar; `.anti()` flips it (below).

**mass / width = Parameter object REFERENCES, not values** (e.g. `mass = Param.MZ`, `width = Param.WZ`; massless uses the shared `Param.ZERO`). They're `import parameters as Param` references resolved at declaration. (How the loader stores these as the param NAME string — `ufo-width-declaration.md`.)

**goldstoneboson** (l.85, default `False`): explicitly `goldstoneboson = True` on `G0`/`G+` only (particles.py:315,330). Ghosts (`ghA`,`ghZ`,`ghWp`,`ghWm`,`ghG`) do NOT carry this flag — they are NOT Goldstones; they're identified by `spin = -1`. So the model has TWO distinct unphysical-field families, identified by two DIFFERENT mechanisms (Goldstone = the flag; ghost = spin −1). The loader drops both in unitary gauge but via separate tests.

**propagating** (l.84, default `True`): a particle with `propagating=False` has no kinetic/propagator term. sm declares none; used by some BSM models for auxiliary fields.

### .anti() — how an antiparticle is built (l.127-140)
There is NO separate `Particle(...)` declaration for most antiparticles. The file does `W__minus__ = W__plus__.anti()`, `u__tilde__ = u.anti()`, etc. (particles.py:52,82,...). `.anti()`:
- raises `Exception('%s has no anti particle.')` if `selfconjugate` (l.128-129) — you cannot call `.anti()` on `a`/`Z`/`g`/`H`/`G0`.
- builds `outdic`: for every attribute in `self.__dict__` NOT in `require_args_all`, store the NEGATED value `-v` (l.130-133). PROBE-CONFIRMED (loaded sm, `ve.__dict__`): the negated set is `{GhostNumber, LeptonNumber, Y, selfconjugate}` — note `selfconjugate` IS in the negated dict (it is in `__dict__` but NOT in `require_args_all`), so `outdic['selfconjugate'] = -False = 0`. That negated `selfconjugate` is passed into the new `Particle(...)` via `**outdic` but is then HARMLESSLY OVERWRITTEN by `__init__`'s `self.selfconjugate = (name==antiname)` (l.87) — so the negation is inert. The physically meaningful negations are the extra per-model quantum numbers (`GhostNumber`, `LeptonNumber`, `Y`): a neutrino `ve` has `LeptonNumber=1` → `ve~` gets `LeptonNumber=-1`. (`line`/`propagating`/`goldstoneboson` are in `require_args_all` and so are NOT negated — copied straight.)
- color flips ONLY for non-{1,8}: `color in [1,8] → unchanged`, else `-color` (l.134-137). Triplet 3 → antitriplet −3; octet 8 → 8 (gluon's anti is itself in color); singlet stays 1.
- returns a NEW `Particle(-pdg, antiname, name, spin, newcolor, mass, width, antitexname, texname, -charge, line, propagating, goldstoneboson, **outdic)` (l.139-140) — pdg, charge negated; name↔antiname and texname↔antitexname swapped; mass/width/spin/propagating/goldstoneboson COPIED unchanged. This new object self-appends to `all_particles` like any other.

Consequence: `all_particles` contains BOTH the particle and its `.anti()` as full independent entries (sm: explicit `Particle(...)` decls plus one `.anti()` per non-self-conjugate — count `Particle(` vs `.anti()` in `particles.py`; see structure page). The loader later collapses each ±pdg pair into one MG5 particle with an `is_part`/`self_antipart` flag (consumption slice).

## Vertex — the color×lorentz→coupling sparse map (object_library.py:168-181, sm/vertices.py)

`Vertex(name, particles, color, lorentz, couplings)`:
- `particles` = an ORDERED list of `Particle` refs (e.g. `[P.d__tilde__, P.d, P.g]`). Order is load-bearing: the Lorentz/color index `n` refers to the n-th particle here (1-based).
- `color` = a LIST of color-structure STRINGS (one per independent color tensor). Single-structure vertices use `['1']` (color singlet) or `['T(3,2,1)']` / `['f(1,2,3)']`.
- `lorentz` = a LIST of `Lorentz` refs (one per independent Lorentz tensor).
- `couplings` = a DICT keyed `(color_index, lorentz_index) → Coupling ref`. The key indexes into the `color` list × `lorentz` list grids (both 0-based).

**The map is a SPARSE dict over the color×lorentz grid, not a dense matrix.** Canonical multi-structure example, the 4-gluon vertex (vertices.py:228-232):
```
V_37 = Vertex(particles=[g,g,g,g],
   color=['f(-1,1,2)*f(3,4,-1)','f(-1,1,3)*f(2,4,-1)','f(-1,1,4)*f(2,3,-1)'],  # 3 color structures
   lorentz=[L.VVVV1, L.VVVV3, L.VVVV4],                                          # 3 lorentz structures
   couplings={(1,1):C.GC_12,(0,0):C.GC_12,(2,2):C.GC_12})                        # only the DIAGONAL 3 keys
```
There are 3×3=9 possible (color,lorentz) cells but only the 3 diagonal cells `(0,0),(1,1),(2,2)` are populated — each pairing color-structure k with lorentz-structure k, all carrying the SAME coupling `GC_12`. The off-diagonal cells are absent (zero). So a multi-term vertex declares its color-lorentz pairing by WHICH dict keys exist, and the same `Coupling` may appear in several cells. A single-term vertex is just `{(0,0): C.GC_n}`.

## Coupling — value string + order dict (object_library.py:185-194, sm/couplings.py)
`Coupling(name, value, order)`. `value` is a Python EXPRESSION STRING evaluated later (e.g. `GC_1: '-(ee*complex(0,1))/3.'`, `GC_12: 'complex(0,1)*G**2'`). `order` is a dict of coupling-order powers (`GC_1: {'QED':1}`, `GC_12: {'QCD':2}`). The order dict is what makes a coupling carry QCD²/QED¹ weight; transitively a vertex's order is its couplings' orders (see `ufo-coupling-orders-and-propagators.md`).

## Parameter — external (number+LHA) vs internal (expr string) (object_library.py:146-164, sm/parameters.py)
`Parameter(name, nature, type, value, texname, lhablock=None, lhacode=None)`. `nature ∈ {'external','internal'}`, `type ∈ {'real','complex'}`.
- **external** (`aEWM1`, parameters.py:21-27): `value` is a NUMERIC LITERAL (`132.50698`) and `lhablock`+`lhacode` are REQUIRED — `__init__` raises `Exception('Need LHA information for external parameter ...')` if either is None for an external (l.161-162). The lhablock/lhacode = where the param reads from the param_card (`SMINPUTS [1]`). These are the model's free inputs.
- **internal** (`ee`, parameters.py:301-305): `value` is an EXPRESSION STRING in terms of other params (`'2*cmath.sqrt(aEW)*cmath.sqrt(cmath.pi)'`); no LHA info. Derived at compute time.
- `ZERO` (parameters.py:14-18): internal, `value = '0.0'` — the single shared hard-zero referenced by every massless `mass`/`width` (the `Param.ZERO` in particles.py).
So external/internal is the declaration-time split between "read from card" and "compute from formula"; `value`'s TYPE (number vs string) follows the nature. (Loader handling of the value strings — shortening/dependency classification — is `ufo-expression-shortening-and-event-dependence.md`.)

**EW input scheme is encoded HERE, not chosen by a flag.** In `sm/parameters.py` the external EW inputs are `aEWM1` (:21, `SMINPUTS[1]`), `Gf` (:29), `MZ` (:125) — plus `aS`(:37), `MT`(:141), `MH`(:157). **`MW` is INTERNAL** (`sm/parameters.py:295`, nature='internal') — derived, not a free input; so sm is the Gμ/α(MZ)/MZ scheme with MW computed. Which parameters are external IS the scheme; changing scheme means a different UFO, not a switch. Concrete internal-derived anchors: `loop_sm` `lam = MH**2/(2.*v**2)` (nature='internal', `loop_sm/parameters.py:379-383`); `ee`, `sw`, `cw`, `v` all internal. `cmath.sqrt(2)` is inlined into value strings (e.g. Yukawas `(ymb*cmath.sqrt(2))/v`), not a standalone Parameter.

## Lorentz.structure — the DSL vocabulary and index convention (object_library.py:200-209, sm/lorentz.py)

`Lorentz(name, spins, structure)`:
- `spins` = list of 2S+1 spins, one per particle, SAME ORDER as the vertex's `particles` (e.g. `FFV1: spins=[2,2,3]` = fermion,fermion,vector).
- `structure` = a tensor EXPRESSION STRING in a fixed DSL. The loader copies it RAW onto the MG5 Lorentz object (`ufo-loader-per-declaration-consumption.md`: lorentz is COPY-RAW); it is EVALUATED by ALOHA (`$MADGRAPH_INSTALL/aloha/aloha_object.py`), never by the loader.

**Index convention**: a positive integer `n` in a structure/color string = the n-th particle in the vertex `particles` list (1-based). A NEGATIVE integer = a contracted (summed) internal index. Example `FFV2: 'Gamma(3,2,-1)*ProjM(-1,1)'` — Lorentz index 3 (the vector, particle 3), spinor indices on particles 2 and 1, with `-1` the summed spinor index between Gamma and the chiral projector.

**DSL vocabulary** (tokens present across all bundled models, via `grep models/*/lorentz.py`; class defs in `aloha/aloha_object.py`):
- `P(mu, i)` — momentum of particle i, Lorentz index mu (l.62). By far the commonest token (~2025 uses).
- `Gamma(mu, i, j)` — Dirac gamma matrix, vector index mu, spinor rows i (out) j (in) (l.716). `FFV1: 'Gamma(3,2,1)'`.
- `Gamma5(i, j)` — γ⁵ (l.857; present 63× across models).
- `Metric(mu, nu)` — g^{μν} (l.1015). `VVS1: 'Metric(1,2)'`.
- `ProjM(i, j)` (l.1103) / `ProjP(i, j)` (l.1132) — chiral projectors (1∓γ⁵)/2. `FFS1: 'ProjM(2,1)'`.
- `Identity(i, j)` — δ in spinor/color space (l.1046; used 67× in lorentz; ALSO a color-string token but resolved differently, see below).
- `Epsilon(a,b,c,d)` — Levi-Civita ε^{μνρσ} (l.985, 119× across models).
- `Sigma(mu, nu, i, j)` — σ^{μν} = (i/2)[γ^μ,γ^ν] (l.829). DEFINED in ALOHA but UNUSED in any bundled model's lorentz.py (grep = 0). An author CAN use it; the SM/bundled set doesn't.
Operators are plain Python: `+ - *` and numeric coefficients/`/2.` (e.g. `VVVV5: 'Metric(1,4)*Metric(2,3) - (Metric(1,3)*Metric(2,4))/2. - (Metric(1,2)*Metric(3,4))/2.'`). A structure can be a sum of terms; each term is a product of DSL tensors with numeric coefficients. `structure='external'` (the class default, l.204) or `'1'` marks a structureless/scalar contact term (e.g. `SSS1`,`SSSS1`,`UUS1` use `'1'`).

SM's `Lorentz` objects (lorentz.py, names like UUS1/FFV1..5/VVVV1..5 — count entries in the file) form the full tensor basis the SM Feynman rules need.

## Color-string DSL — the color tensors (sm/vertices.py `color=[...]`, eval'd against `madgraph/core/color_algebra.py`)

The `color` strings are evaluated by the LOADER's `treat_color` against the color-algebra classes (`import_ufo.py:1812`; classes at `color_algebra.py`) — distinct from the Lorentz DSL (which ALOHA owns). Author-level vocabulary seen in sm:
- `'1'` — color singlet (the commonest; all colorless vertices).
- `T(a, i, j)` — fundamental generator (T^a)_{ij}, octet index a, triplet indices i,j (`color_algebra.py:212`). `V_74: 'T(3,2,1)'` (gluon=particle3, quarks 2,1).
- `f(a, b, c)` — SU(3) structure constant f^{abc} (l.304). `V_36 (ggg): 'f(1,2,3)'`.
- `d(a, b, c)` — symmetric d^{abc} (l.338, subclass of f).
- Products with summed negative indices: `V_37 (gggg): 'f(-1,1,2)*f(3,4,-1)'` — `-1` is the summed adjoint index between the two structure constants.
- `Identity(i, j)` — color δ (used heavily: `V_n: 'Identity(1,2)'`, sm vertices.py:434). SPECIAL CASE: there is NO `Identity` class in `color_algebra.py` (grep=0). The loader's `treat_color` string-matches it (`_pat_id` regex, import_ufo.py:1944) and REWRITES it by the particles' color rep into a real color-algebra class: triplet → `color.T(...)`, octet → `color.Tr(...)` (×2 factor), sextet → `color.T6(...)` (import_ufo.py:1982-2015); a same-rep pair raises `InvalidModel`. So `Identity` is the ONE color token that is loader-special-cased pre-eval rather than an eval'd `color.` class name.
Also available (other models): `Tr(...)` (trace, l.94), `Epsilon`/`EpsilonBar` (l.359/519, color-triplet ε_{ijk}), `T6`/`K6`/`K6Bar` (sextet, l.684+). Same index convention as Lorentz: positive = n-th particle, negative = summed.

## CouplingOrder — the order-weight declaration (object_library.py:234-243, sm/coupling_orders.py)
`CouplingOrder(name, expansion_order, hierarchy, perturbative_expansion=0)`. SM declares exactly two: `QCD(expansion_order=99, hierarchy=1)`, `QED(expansion_order=99, hierarchy=2)`. `hierarchy` ranks orders for WEIGHTED counting (lower = "more fundamental"); `expansion_order=99` = no per-process cap; `perturbative_expansion>0` flags a loop/perturbed order. NOTE the sm object_library ACCEPTS but does not STORE `perturbative_expansion` (the tree/loop asymmetry — full treatment in `ufo-coupling-orders-and-propagators.md`).

## Cautions (source-visible, declaration-level)
- `selfconjugate`, `line`, and the antiparticle are all DERIVED at construction, never authored: don't expect to find a `selfconjugate=` or an explicit antiparticle `Particle(...)` for `W-`/`u~` in the file — they come from `name==antiname` and `.anti()`.
- A ghost is `spin = -1`, a Goldstone is `goldstoneboson = True` — two DIFFERENT identifications. Don't infer ghost-ness from the Goldstone flag or vice versa.
- `mass`/`width` are Parameter REFERENCES, not numbers; massless particles share the single `Param.ZERO` object. Reading `particle.mass` gives a Parameter, not a float.
- `couplings` is a SPARSE dict keyed `(color_idx, lorentz_idx)` — absent keys are zero, and one coupling can fill several cells (the 4-gluon diagonal). Don't read it as a dense color×lorentz matrix.
- The Lorentz `structure` and color strings use the SAME 1-based-particle / negative-summed index convention but are evaluated by DIFFERENT engines (ALOHA for Lorentz, color_algebra for color). `Identity(i,j)` is a token in BOTH DSLs — but ASYMMETRICALLY resolved: Lorentz `Identity` IS an ALOHA class (`aloha_object.py:1046`, spinor/color δ); color `Identity` is NOT a `color_algebra` class — the loader's `treat_color` special-cases it (regex `_pat_id`, import_ufo.py:1944) and rewrites it to `color.T`/`Tr`/`T6` by rep. Don't assume color-`Identity` is an eval'd `color.Identity`; it has no class.
- `Sigma` (σ^{μν}) is in ALOHA's vocabulary but no bundled model uses it; a structure string is only as valid as ALOHA's evaluator — an unknown token surfaces at ALOHA time, not loader time.
