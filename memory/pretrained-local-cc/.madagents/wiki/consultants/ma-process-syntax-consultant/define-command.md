---
description: do_define parse path — separate from do_add; = / | normalisation, check_define validation (label cannot be a particle name), extract_particle_ids resolution, optimize_order sorting, removal via "/".
---

# define command (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `def do_define` at **3527**. Separate parser path from `do_add`/`extract_process`.

## Flow
- 3530 `avoid_history_duplicate('define %s' % line, ['define'])`.
- 3531 if no model, auto `do_import('model sm')`.
- 3534 lowercases line if `not model['case_sensitive']`.
- 3538-3540 normalisation: replaces `=`→` = `, `|`→` | `, `/`→` / ` (NOTE: only these three, NOT the `> , $ [ ]` set that extract_process's spacing regex handles).
- 3541 `args = split_arg(line)`; 3543 `check_define(args)`.
- 3545 `label = args[0]`.
- 3547-3553 **removal syntax**: `args.index('/')` → everything after `/` becomes `remove_ids`, truncate args before it.
- 3555-3557 `pdg_list = extract_particle_ids(args[1:])`; `remove_list = extract_particle_ids(remove_ids)`; subtract.
- 3559 `optimize_order(pdg_list)`; 3560 `self._multiparticles[label] = pdg_list`.

## check_define (932)
- `<2` args → `InvalidCmd('"define" command requires at least two arguments')`.
- `args[1]=='='` → deletes it (so `define p = ...` and `define p ...` both work); then re-checks `<2`.
- any remaining `'='` in args → `InvalidCmd('... requires symbols "=" at the second position')`.
- 951 auto-imports sm if no model.
- **956 label collision**: if `model['particles'].find_name(args[0])` → `InvalidCmd("label %s is a particle name in this model")`. A multiparticle name may not shadow a model particle name.

## extract_particle_ids (5591)
Shared with the `/`/`$`/`> >` filters and required-s-channels in extract_process. Handles `|` as or-multiparticle separator (builds list-of-id-lists; used for `Z/gamma`-style required s-channels). `get_copy` per name; digit→int; unknown→`InvalidCmd("No particle %s in model")`. `crash_on_duplication=True` (only required-s-channels) raises `InvalidCmd('Particle can not be duplicate')`.

## optimize_order (5643)
Stable sort of pdg_list by: pdg<0 last, fermion, color (desc), mass!=zero — groups similar particles. Probe (v3.7.1): `define myq = u d s` → `Defined multiparticle myq = u d s`.

## Default multiparticles
`p j l+ l- vl vl~ all` are NOT created by the parser — they are populated by the model loader at import (out of this slice). Probe shows them already defined after `import model sm`.

## No sub-keywords — `args[0]` is always a literal label (MadDM correction)
Core `do_define` has NO keyword dispatch on the first token. **3545 `label = args[0]`** takes the first token *verbatim* as the multiparticle name; everything after (`args[1:]`) is a particle-id list resolved by `extract_particle_ids`. So in core MG5:
- `define darkmatter ~xd` → tries to create a multiparticle **literally named `darkmatter`** containing `~xd`. `darkmatter`/`coannihilator` are NOT recognized as anything special — they are just labels. (check_define 955 only forbids a label that collides with a model *particle* name; `darkmatter` is not an SM particle so no collision.)
- `~xd` / `~xr` are resolved as particle names via `extract_particle_ids` → if the loaded model does not declare them, `InvalidCmd("No particle ~xd in model")` (5591-region resolution). In plain `sm` these are unknown → hard error at parse.
- No semantic "DM candidate selection" happens in core — that is a **MadDM plugin extension** (plugin overrides/adds a `do_define`/`do_define_darkmatter` handler; plugin source ABSENT here = GAP). The durable correction: `define darkmatter …` / `define coannihilator …` are MadDM plugin syntax, NOT core process-syntax. Core `define <label> <particles>` only ever creates a user multiparticle in `self._multiparticles[label]`.
