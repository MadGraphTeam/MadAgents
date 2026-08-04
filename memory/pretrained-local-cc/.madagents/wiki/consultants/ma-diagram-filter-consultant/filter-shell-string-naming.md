---
description: Which filter operators appear in the subprocess directory name (shell_string) — `/` -> `_no_X`, `> >` -> `_Z_` between sides; `$`/`$$` are INVISIBLE (same dir name as unfiltered). Probe-confirmed.
---

# Filters in the subprocess directory name (`shell_string`)

File: `$MADGRAPH_INSTALL/madgraph/core/base_objects.py` `Process.shell_string`
(v3.7.1, def at 3433). This is the function that builds the SUBPROCESS DIRECTORY
NAME (the `P<id>_...` folder under `SubProcesses/`) and the matrix-element shell
tag. Distinct from `nice_string`/`input_string`/`base_string` (the process-line
serializations covered in diagram-filter-enforcement §"Serialization round-trip").

## Signature & defaults (3433-3438)
```
def shell_string(self, schannel=True, forbid=True, main=True, pdg_order=False,
                 print_id = True):
    """Returns process as string ... including process number,
    intermediate s-channels and forbidden particles ..."""
```
Both `schannel` and `forbid` default True. So by default the directory name
DOES encode `> >` and `/`.

## `> >` required_s_channels -> inserted between initial and final (3460-3466)
At the `>`-separator (where prevleg is initial and leg is final), if
`required_s_channels` is set and `schannel`, the required propagator name(s) are
inserted, OR-lists joined by `_or_`:
```
3462   mystr += "_or_".join(["".join([... req_id name ...
                              for req_id in id_list])
                            for id_list in self['required_s_channels']])
```
So `u u~ > z > e+ e-` -> `..._z_...`; `> z | a >` -> `..._z_or_a_...`.

## `/` forbidden_particles -> `_no_<part>` suffix (3484-3488)
After the legs, if `forbidden_particles` and `forbid`:
```
3484   if self['forbidden_particles'] and forbid:
3485       mystr = mystr + '_no_'
3486       for forb_id in self['forbidden_particles']:
3487           ... + forbpart.get_name()
```
So `/ a` -> `..._no_a`; `/ a z` -> `..._no_az`.

## `$` and `$$` are INVISIBLE in shell_string
There is NO `forbidden_onsh_s_channels` or `forbidden_s_channels` block anywhere
in `shell_string` (3433-3516). The blocks that DO render `$`/`$$` (the
`$`/`$$` trailing operators) live only in the process-LINE serializations:
`nice_string` (3261-3279), `input_string` (3363-3379), the dict export
(4050-4066). None of those feed the directory name.

Consequence: two processes differing ONLY by a `$` or `$$` filter get the SAME
subprocess directory name; two differing by `/` or `> >` get DIFFERENT names.

## Probe-confirmed (v3.7.1, sm)
`generate ...; amp.get('process').shell_string()`:
- `u u~ > e+ e-`        -> `1_uux_epem`
- `u u~ > e+ e- $ z`    -> `1_uux_epem`        (IDENTICAL — `$` invisible)
- `u u~ > e+ e- / a`    -> `1_uux_epem_no_a`   (`_no_a` suffix)
- `u u~ > z > e+ e-`    -> `1_uux_z_epem`       (`z` between sides)

## Cautions
- A user auditing "which P-directory is my `$`-filtered process?" cannot
  distinguish it by folder name from the unfiltered process — the `$`/`$$`
  effect shows only in `decayBW.inc` (gForceBW, see schannel-config-carrier-and-
  sprop) and the ME Fortran (P1D/BWCUTOFF, see dollar-filter-helas-realization).
- Because `$`/`$$` don't change the shell name but DO change the amplitude,
  re-`output`ing a `$`-added process over an existing same-legs directory could
  collide on the name — the differing content is the only tell. (Output/dir-
  collision handling is the code-output slice; we own only that the NAME is the
  same.)
- `pdg_order=True` (3445-3450) sorts final legs by pid for the name but does NOT
  change which filters appear; the `$`/`$$` invisibility is independent of it.
