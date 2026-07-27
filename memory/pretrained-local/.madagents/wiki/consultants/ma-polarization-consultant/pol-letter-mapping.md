---
description: Polarization {…} letter/number-to-helicity mapping in extract_process, the spin-gating per letter, and the 2s+1 spin convention used to gate them
---

# Polarization letter mapping (`extract_process`)

Source: `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, polarization
block at lines 5082-5190 (v3.7.1). Spin is the **2s+1 convention**
(`base_objects.py:285` prints `'spin(2s+1 format)'`; `is_boson` def at
`base_objects.py:511`, `is_fermion` returns `spin%2==0` at 509 — so boson =
`spin%2==1`). So: spin==1 scalar, spin==2 fermion, spin==3 vector (spin-1),
spin==5 spin-2.

## Parse entry (5082-5109)
- `'{' in part_name` triggers: `part_name, pol = part_name.split('{',1)` then
  `pol, rest = pol.split('}',1)` (5083-5084).
- Spin AND mass read from the particle: `spin = ...get_particle(no_dup_name).get('spin')`
  and `mass = ...get('mass')` (5089-5090). Leading-digit duplication prefixes are
  stripped by retrying with `no_dup_name[1:]` (5103-5104).
- Multiparticle: `spins`/`mass` become **sets** over members (5094-5095). If
  `len(spins) > 1` → `InvalidCmd('Can not use polarised on multi-particles for
  multi-particles with various spin')` (5097-5098). Otherwise single spin popped.
- After `}`, `rest` (the part of the *token* after `}`) must be empty or →
  `InvalidCmd('A space is required after the "}" symbol to separate particles')`
  (5108-5109). The guard is `if rest:` — truthy for ANY non-empty string. Because
  tokens are already whitespace-split by `split_arg` (each `part_name` is one
  whitespace-delimited token), `rest` never contains whitespace; so anything glued
  after the brace raises. **Probe (v3.7.1):** `e+ e- > Z{T}Z` → that error (the
  glued `Z` becomes `rest`); `e+ e- > Z{T}x mu-` → same error. Contrast `Z{T} Z`
  (spaced) which passes this gate and instead dies at the ambiguous-mix gate. Same
  visual pair, two different gates — see `pol-validation-pipeline.md`.

## Letter loop (5111-5190)
Iterates chars of `pol`; `,` separators consumed (5112); `ignore` flag skips the
digit already consumed by a `+N`/`-N`. Mapping (all spin-1-only letters raise the
quoted `InvalidCmd` for any other spin):

| token | spin gate | appends | note |
|-------|-----------|---------|------|
| `T`/`t` | spin==3 only | `[1,-1]` | transverse = sum of hel ±1 (5115-5119) |
| `L`/`l` | any spin | `[-1]` | if spin==3 emits warning "interpreted as left (-1); for longitudinal (0) please use 0" (5120-5123) |
| `R`/`r` | any spin | `[1]` | right-handed (5124-5125) |
| `A`/`a` | spin==3 only | `[99]` | auxiliary (5126-5130) |
| `G`/`g` | spin==3 only | `[4]` | metric (5131-5135) |
| `H`/`h` | spin==3 only | `[5]` | Theta (5136-5140) |
| `Q`/`q` | spin==3 only | `[6]` | qq = longitudinal − Theta (5141-5145) |
| `W`/`w` | spin==3 only | `[7]` | Ward-protected full prop (5146-5150) |
| `S`/`s` | spin==3 only | `[9]` | scalar = aux + width (5151-5155) |
| `+` then digit | — | `+int(d)`, `abs>3`→raise "polarization are between -3 and 3" | sets `ignore` (5157-5163) |
| `+` alone | — | `[1]` | (5164-5165) |
| `-` then digit | — | `-int(d)`, `abs>3`→raise | sets `ignore` (5166-5172) |
| `-` alone | — | `[-1]` | (5173-5174) |
| `0` | see below | `[0]` | longitudinal (5175-5183) |
| other digit | — | `int(p)`, `abs>3`→raise | (5184-5188) |
| anything else | — | — | `InvalidCmd('Invalid Polarization')` (5189-5190) |

## `0` (longitudinal) — spin/mass dependent (5175-5183)
- spin in [1,2] (scalar/fermion) → `InvalidCmd('"0" (longitudinal) polarizations
  are not supported for scalars/fermions.')` (5176-5177).
- spin in [3,5] AND massless (`mass == "ZERO"` or `"ZERO" in mass` for the
  multiparticle set) → `logger.info('"0" ... detected for massless boson.')`, still
  appends `[0]`; comment: "those mode will be bypass at generation time / important
  to keep it here in presence of multi-particles" (5178-5181).
- else → `[0]` (5182-5183).

## Caution
- `L` for a spin-1 particle is **left-handed (-1)**, NOT longitudinal — common
  user trap; longitudinal must be requested with `0`. Warning is emitted but the
  value is still `[-1]`.
- `L`/`R` are **NOT spin-gated** (5120-5125): both branch on "any spin" and append
  `[-1]`/`[1]`. A doc/label table calling `{L}`/`{R}` "fermion (left/right-handed)"
  polarizations is an oversimplification — they apply to spin-1 vectors too (`L` on a
  vector = left helicity −1 with the warning, `R` = right helicity +1). Only the
  transverse/exotic letters (`T A G H Q W S`) are spin==3-only; `0` is spin/mass-gated
  (rejected for scalars/fermions). So the real spin partition is: `L R` universal,
  `T/A/G/H/Q/W/S` vector-only, `0` boson-only.
- **Version provenance (v2.7.0 claim) — UNGROUNDED here.** A "polarization syntax
  available since v2.7.0" claim cannot be settled from this source tree (no changelog
  marker in the parser). Treat as an unverified version claim, not a cached fact.
- `0` on a massless vector is accepted at parse time (emits the `logger.info`) but the
  helicity-0 mode is **stripped at diagram-generation time** — the bypass site is in
  `diagram_generation.py` (~1750-1794), NOT the mc-integration slice. If `0` was the leg's
  ONLY polarization, stripping empties the list and the whole process is dropped →
  `NoDiagramException` (not a polarization error). See `pol-generation-expansion.md`.
  What the *surviving* codes do at integration is the mc-integration slice's territory.
- The resulting `polarization` list is attached to the (Multi)Leg dict
  (`'polarization': polarization`, 5233-5240); how it's consumed downstream
  (HELAS/amplitude) is out of this slice.
- `polarization = []` is (re)initialised per token at 5081 (right after
  `mylegids = []`), so the list does NOT accumulate across legs — each
  whitespace-separated particle gets its own freshly-parsed polarization.

## Digit-duplication prefix + polarization (`2Z{T}` → two identical legs)
For a token like `2Z{T}`: the `{` branch reads spin/mass via `no_dup_name` (which
strips the leading digit, 5103-5104) but leaves `part_name` = `2Z`. After the letter
loop, the duplicate-handling block (5193-5224) sees `part_name[0].isdigit()` →
`duplicate, part_name = int('2'), 'Z'` → builds `duplicate` legs, **each carrying the
same parsed `polarization` list**. **Probe (v3.7.1):** `generate e+ e- > 2Z{T}` →
`e+ e- > z{T} z{T}`, "1 processes with 2 diagrams", no error — because the two legs
have *identical* polarization, so the ambiguous-mix gate (`check_polarization`) sees
"already present → no issue" and the symmetry factor treats them as identical (1/2!).
Contrast `Z{T} Z` (one polarized, one not) which IS ambiguous. See
`pol-symmetry-factor.md` for the identical-leg-key mechanism.
