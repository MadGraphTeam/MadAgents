---
description: How extract_process parses the four diagram-filter operators (/, $, $$, > >) and which Process field each captures.
---

# Filter-operator parsing in `extract_process`

File: `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, inside
`extract_process` (MG5_aMC v3.7.1). Parsing happens AFTER coupling-order
extraction and AFTER `line = line.lower()` (5002-5004) when the model is not
case-sensitive.

## Order of operations (sequential, mutating `line`)
The operators are stripped off `line` left-to-right in this fixed order; each
match removes its captured text from `line` so the next regex sees a shorter
line:

1. **`/` forbidden particles** (5006-5019)
   - `slash = line.find("/")`, `dollar = line.find("$")` (5007-5008).
   - Only fires if `slash > 0` (5010).
   - If a `$` appears AFTER the `/` (`dollar > slash`), uses the `$`-aware
     variant `r"^(.+)\s*/\s*(.+\s*)(\$.*)$"` (5012) so the trailing `$...`
     stays out of `forbidden_particles`; group(3) is re-appended to `line`
     (5018-5019). Otherwise plain `r"^(.+)\s*/\s*(.+\s*)$"` (5014).
   - Capture: `forbidden_particles = group(2)` (5016); `line = group(1)` (5017).

2. **`$$` forbidden s-channels** (5021-5026)
   - `r"^(.+)\s*\$\s*\$\s*(.+)\s*$"` (5022). Capture: `forbidden_schannels =
     group(2)` (5025).

3. **`$` forbidden ON-SHELL s-channels** (5028-5033)
   - `r"^(.+)\s*\$\s*(.+)\s*$"` (5029). Capture: `forbidden_onsh_schannels =
     group(2)` (5032).
   - `$$` is matched BEFORE `$`, so a `$$` line is consumed by step 2 and never
     reaches this regex. A single `$` is captured here.

4. **`> >` required s-channels** (5035-5041)
   - `re.match("^(.+?)>(.+?)>(.+)$", line)` (5036) — a plain (non-raw) string
     literal in source, not `r"..."`; inconsequential as the pattern has no
     backslashes. Non-greedy first two groups: middle
     group(2) is the required-s-channel text. The line is REBUILT removing the
     inner `>`: `line = group(1) + ">" + group(3)` (5040-5041).

## From strings to PDG-id lists (5298-5327)
`extract_particle_ids(<captured string>)` (def at 5591) converts each captured
name string into PDG ids:
- `forbidden_particle_ids` (5299), `forbidden_onsh_schannel_ids` (5306),
  `forbidden_schannel_ids` (5308), `required_schannel_ids` (5320,
  `crash_on_duplication=True`).
- `|` in the string is an OR-multiparticle -> list-of-lists (5607-5613,
  comment 5592-5596). For `/`, `$`, `$$` an or-multiparticle is REJECTED
  (`InvalidCmd "... can be used only for required s-channels"`, 5301-5317).
  Only `> >` accepts the OR form.
- `required_schannel_ids` is wrapped to list-of-lists if not already
  (5325-5327): different lists = OR, elements within a list = AND
  (consumed at diagram_generation.py:710-714).

## Multi-particle per operator is a SPACE-separated AND-list
`extract_particle_ids` (5599-5617) loops over `split_arg(args)` and appends
EACH space-separated `part_name`'s id. With no `|` present, every id lands in
one sublist -> after flatten a FLAT list. So `$$ w+ w- z / a` parses to
`forbidden_s_channels=[24,-24,23]` and `forbidden_particles=[22]` (each operator
carries its own multi-particle list). Semantics of that flat list: for `/`,`$`,
`$$` every listed particle is INDEPENDENTLY forbidden (AND — all removed);
`/ ta+ ta- z` kills τ⁺, τ⁻ AND Z (see diagram-filter-enforcement). Only `> >`
reads `|` as OR (list-of-lists). Plain space separation needs no `|`; the
`args.replace("|"," | ")` NO-OP (return discarded) only bites the OR form.
Multiparticle labels (`p`,`j`,`l+`) also expand here (5609-5610). Source-walked
(v3.7.1); the space-separated flat-list is a source read, the specific tuple
values are HYPOTHESIS until probed.

## Capture is SIGNED PDG (get_pdg_code, 5606)
`extract_particle_ids` resolves each name via
`self._curr_model['particles'].get_copy(part_name).get_pdg_code()` (5604-5606),
which is the SIGNED pdg of the particle AS NAMED. So the captured id keeps the
sign of the named particle:
- `$ w+` -> `forbidden_onsh_s_channels=[24]`; `$ w-` -> `[-24]` (distinct).
- `/ mu+` -> `forbidden_particles=[13]` (signed at capture).
Numeric literals are accepted too (5614-5615: `isdigit()` or leading `-` +
digits), so `$ 24` and `$ -24` work directly.
This signedness MATTERS for the s-channel filters (`$`,`$$`,`> >`) because
enforcement matches `get_s_channel_id` (also signed, no abs) — see
diagram-filter-enforcement. For `/` the sign is erased at enforcement by
`abs()` (diagram_generation.py:1018), so `/ mu+` and `/ mu-` are equivalent.
Probe-confirmed (v3.7.1, sm): `$ w+`->[24], `$ w-`->[-24], `/ mu+`->[13].

## OR-list `|` quirks (only `> >`)
- The middle group of `> A | B >` is the OR-list. Correct form is
  `p p > z | a > e+ e-` -> `required_s_channels=[[23],[22]]` (Z OR photon).
  Probe-confirmed (v3.7.1, sm).
- WATCH the non-greedy regex: in `p p > e+ e- > z | a` the `z | a` lands in
  group(3) = the FINAL STATE (not the required s-channel), and then errors
  ("No particle | in model") because `|` is not valid in a final-state list.
  The OR-list must sit BETWEEN the two `>`.
- `|` must be SPACE-SEPARATED. `extract_particle_ids` line 5599
  `args.replace("|", " | ")` is a NO-OP (return value discarded, not
  reassigned), so the auto-spacing never happens; `split_arg('z|a')` keeps
  `z|a` as one token -> "No particle z|a in model". `split_arg('z | a')` ->
  `['z','|','a']` works. Probe-confirmed (v3.7.1, sm).

## Stored on the ProcessDefinition (5336-5352)
- `'forbidden_particles': forbidden_particle_ids`
- `'forbidden_onsh_s_channels': forbidden_onsh_schannel_ids`  (the `$` field)
- `'forbidden_s_channels': forbidden_schannel_ids`            (the `$$` field)
- `'required_s_channels': required_schannel_ids`              (the `> >` field)

## `Process.set()` re-normalizes the fields (base_objects.py:3103-3118)
The signed/raw ids stored at parse get re-normalized whenever they are `set()`
on a `Process` (and on `ProcessDefinition`, which subclasses it). Two overrides:
- **`forbidden_particles` is abs()-ed AT SET** (3106-3110): `value = [abs(i)
  for i in value]`. So the sign captured by `get_pdg_code` (signed) is ALREADY
  erased here, BEFORE enforcement — not only at the `abs()` in
  diagram_generation.py:1018. Probe (v3.7.1, sm): `set('forbidden_particles',
  [-13]) -> [13]`. Practical upshot unchanged (`/ mu+`==`/ mu-`), but the sign
  dies at the field, not at the recursion.
- **`required_s_channels` auto-wraps to list-of-lists AT SET** (3112-3116): a
  flat list `[23]` becomes `[[23]]`. This is a SECOND wrap, independent of the
  parser's wrap (5325-5327) — a Process built programmatically with a flat list
  still gets wrapped. Probe: `set('required_s_channels', [23]) -> [[23]]`.

## Field validators (base_objects.py:3042-3070, the `filter` method)
`Process.filter` (the value-validator, distinct from a diagram filter) enforces
STRUCTURE on each field when set:
- `required_s_channels` (3042-3052): must be list-OF-lists of nonzero ints
  (`i == 0` rejected: "Not valid PDG code 0 for s-channel particle").
- `forbidden_onsh_s_channels` / `forbidden_s_channels` (3054-3061): must be a
  FLAT list of nonzero ints. A nested/OR list is rejected here even if it
  somehow bypassed the parser's OR-rejection. Probe: `set('forbidden_onsh_
  s_channels', [[24]]) -> PhysicsObjectError "is not a valid list of integers"`.
  This is the structural backstop confirming `$`/`$$` are single-particle-only.
- `forbidden_particles` (3063-3070): must be a flat list of POSITIVE ints
  (`i <= 0` rejected). Consistent with the abs() at set. (Minor source bug: the
  `i <= 0` message at 3070 uses `%` with `str(value)` but no `%s` placeholder,
  so it raises a `TypeError` on the format rather than the intended
  PhysicsObjectError — cosmetic, the field is already abs()-ed so `i<=0` only
  triggers on a literal 0.)

## Probe-confirmed capture (v3.7.1, model sm)
`extract_process` on these lines yields (PYTHONPATH=$MADGRAPH_INSTALL):
- `p p > t t~ / g`           -> forbidden_particles=[21]
- `p p > e+ e- $ z`          -> forbidden_onsh_s_channels=[23]
- `p p > e+ e- $$ z`         -> forbidden_s_channels=[23]
- `p p > t t~ > w+ w- b b~`  -> required_s_channels=[[6, -6]]
- `p p > e+ e- / a $ z`      -> forbidden_particles=[22], forbidden_onsh_s_channels=[23]

## Secondary parse: `split_process_line` (5466-5512) — MadSpin/reweight
A SEPARATE static helper, NOT the diagram-generation `extract_process` path.
Used by `reweight_interface.py` (215, 1188) to split a procline into
`(core_process, options)`. It strips `[...]` NLO tags (5477-5481) and `@num`
(5486-5489), then finds the option-string start by scanning for the FIRST
order `name=N` (5494-5498), `/` (5501-5502), or `$` (5503-5504) and cutting
there (`line[:pos]`, `line[pos:]`, 5506-5511). It does NOT distinguish
`$$`/`$`/`> >`; it only needs the earliest `/`-or-`$` to know where filters/
options begin. So for those tools the filter operators act merely as
"options-start" markers, not as four separate captures. (The main diagram
path's per-operator capture is the block at 5006-5041 above.)

## Source quirk: leaked `part_name` in OR-rejection message
The OR-rejection `InvalidCmd` for `/`,`$`,`$$` (5304/5312/5316) interpolates
`% part_name`, but `part_name` is NOT a local here — it leaks from an earlier
loop, so the error names the WRONG particle. Probe (v3.7.1, sm):
`p p > e+ e- $ z | a` -> "Multiparticle e- is or-multiparticle which can be
used only for required s-channels" (names `e-`, not the offending `z|a`).
Cosmetic only; the rejection itself is correct.

## `/` capture is independent of what PRECEDES the `/`
The `/` step is a pure string op on `line`: `slash = line.find("/")` then the
regex splits at the first `/`, taking group(2) (post-`/` text) into
`forbidden_particles` and group(1) (pre-`/` text) back into `line` (5007-5017).
It never inspects or resolves the pre-`/` tokens — those stay in `line` for the
downstream `>`/final-state parsing. So a plugin-wrapped `generate` whose head
tokens are NOT ordinary particles (e.g. MadDM `generate relic_density / z`,
where `relic_density` is a MadDM observable keyword the plugin preprocesses)
still parses `/ z` identically: `forbidden_particles=[23]`. The `/`-operator
semantics do not depend on the preceding tokens' meaning. (What `relic_density`
expands to is MadDM-plugin territory — GAP; plugin not installed. Only the core
`/ z` capture is grounded here.)

## Cautions
- `$` vs `$$` is decided purely by regex precedence (step 2 before step 3).
  A typo like `e+ e- $z` (no space) still matches because `\s*` allows zero
  whitespace; the name "z" must still resolve in the model.
- `slash > 0` (strict) means a `/` at position 0 is ignored — but a process
  line never legitimately starts with `/`.
- These are PARSER-level captures. What they then constrain in diagram
  enumeration is on page diagram-filter-enforcement.
